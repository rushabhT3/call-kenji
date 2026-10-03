"""When a caller's turn starts and ends.

Start: speech over Kenji only interrupts when it is more than aizuchi. Pipecat's word-count
strategy splits on spaces, which Japanese does not have, so the domain's BackchannelClassifier
decides instead, with the current node's policy.

End: the speech service proposes where a turn ends, and Smart Turn v3 gives a second opinion from
the sound of the caller's voice. A phrase left hanging on a particle, or a pause Smart Turn hears
as mid-sentence, is held open a little longer before Kenji answers it. A caller who presses Hold
keeps the turn open for as long as they like, and hands it over by pressing Done.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from pipecat.audio.turn.base_turn_analyzer import BaseTurnAnalyzer
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    FunctionCallsStartedFrame,
    InputAudioRawFrame,
    InterimTranscriptionFrame,
    LLMFullResponseEndFrame,
    LLMTextFrame,
    ProposedUserStartedSpeakingFrame,
    TranscriptionFrame,
    VADUserStartedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.metrics.metrics import TurnMetricsData
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor, FrameProcessorSetup
from pipecat.turns.types import ProcessFrameResult
from pipecat.turns.user_start import BaseUserTurnStartStrategy
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy

from kenji.app.events import TurnEndJudged
from kenji.domain.turn import (
    BackchannelClassifier,
    TurnDecision,
    TurnEndGrace,
    TurnEndWait,
    TurnPolicy,
    TurnVerdict,
    turn_end_wait,
)

type DecisionListener = Callable[[str, TurnDecision, float], None]
type TurnEndListener = Callable[[TurnEndJudged], None]
_SPEECH_RESUMED = (
    VADUserStartedSpeakingFrame,
    ProposedUserStartedSpeakingFrame,
    InterimTranscriptionFrame,
)


def _monotonic_ms() -> float:
    return time.monotonic() * 1000.0


class Floor:
    """Kenji keeps the floor while silent between his 「はい、」 and the answer that follows it.

    Speech in that gap is judged as speech over Kenji: aizuchi does not cancel the answer on its
    way, and a bare はい cannot be taken as agreement to something he has not yet said.
    """

    def __init__(self) -> None:
        self._is_held = False
        self._acknowledgement_played = False
        self._model_answered = False
        self._answer_ready = False

    @property
    def is_held(self) -> bool:
        return self._is_held

    @property
    def is_awaiting_model(self) -> bool:
        """Kenji holds the floor and the model has not yet said or done anything."""
        return self._is_held and not self._model_answered

    def hold(self) -> None:
        self._is_held = True
        self._acknowledgement_played = False
        self._model_answered = False
        self._answer_ready = False

    def release(self) -> None:
        self._is_held = False

    def model_answered(self) -> None:
        if self._is_held:
            self._model_answered = True

    def answer_ready(self) -> None:
        if self._model_answered:
            self._answer_ready = True

    def kenji_stopped_speaking(self) -> None:
        if self._answer_ready:
            self.release()
        elif self._is_held:
            self._acknowledgement_played = True

    def kenji_started_speaking(self) -> None:
        """Kenji's answer has begun, so the ordinary rules for speech over him take over."""
        if self._acknowledgement_played and self._model_answered:
            self.release()


class BackchannelTurnStartStrategy(BaseUserTurnStartStrategy):  # type: ignore[no-untyped-call]
    def __init__(
        self,
        classifier: BackchannelClassifier,
        policy: Callable[[], TurnPolicy],
        on_decision: DecisionListener,
        clock_ms: Callable[[], float] = _monotonic_ms,
        floor: Floor | None = None,
    ) -> None:
        super().__init__()
        self._classifier = classifier
        self._policy = policy
        self._on_decision = on_decision
        self._clock_ms = clock_ms
        self._floor = floor or Floor()
        self._is_bot_speaking = False
        self._overlap_started_ms: float | None = None

    async def handle_user_turn_started(self) -> None:
        self._is_bot_speaking = False
        self._overlap_started_ms = None
        self._floor.release()

    async def process_frame(self, frame: Frame) -> ProcessFrameResult:
        if isinstance(frame, BotStartedSpeakingFrame):
            self._is_bot_speaking = True
            self._floor.kenji_started_speaking()
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._is_bot_speaking = False
            self._floor.kenji_stopped_speaking()
        elif isinstance(frame, VADUserStartedSpeakingFrame):
            return await self._on_voice(frame)
        elif isinstance(frame, (InterimTranscriptionFrame, TranscriptionFrame)):
            return await self._on_text(frame.text, is_final=isinstance(frame, TranscriptionFrame))
        return ProcessFrameResult.CONTINUE

    def _kenji_has_floor(self) -> bool:
        return self._is_bot_speaking or self._floor.is_held

    async def _on_voice(self, _frame: VADUserStartedSpeakingFrame) -> ProcessFrameResult:
        if not self._kenji_has_floor():
            await self.trigger_user_turn_started()
            return ProcessFrameResult.STOP
        self._overlap_started_ms = self._clock_ms()
        return ProcessFrameResult.CONTINUE

    async def _on_text(self, text: str, *, is_final: bool) -> ProcessFrameResult:
        if not self._kenji_has_floor():
            await self.trigger_user_turn_started()
            return ProcessFrameResult.STOP
        decision = self._classifier.classify(text, self._policy())
        if decision.verdict is TurnVerdict.INTERRUPTION:
            self._report(text, decision)
            await self.trigger_user_turn_started()
            return ProcessFrameResult.STOP
        if is_final:
            self._report(text, decision)
            self._overlap_started_ms = None
            await self.trigger_reset_aggregation()  # type: ignore[no-untyped-call]
        return ProcessFrameResult.CONTINUE

    def _report(self, text: str, decision: TurnDecision) -> None:
        started = self._overlap_started_ms
        overlap_ms = 0.0 if started is None else max(0.0, self._clock_ms() - started)
        self._on_decision(text, decision, overlap_ms)


class CallerHold:
    """The caller asked Kenji to wait: however long they pause, their turn stays open."""

    def __init__(self) -> None:
        self._is_on = False
        self._listeners: list[Callable[[], Awaitable[None]]] = []

    @property
    def is_on(self) -> bool:
        return self._is_on

    def when_released(self, listener: Callable[[], Awaitable[None]]) -> None:
        self._listeners.append(listener)

    def put_on(self) -> None:
        self._is_on = True

    async def release(self) -> None:
        if not self._is_on:
            return
        self._is_on = False
        for listener in self._listeners:
            await listener()


class SmartTurnOpinion:
    """Smart Turn v3's reading of the caller's voice: had they finished when they paused?

    Each pause is judged as the VAD hears it, as Pipecat's own Smart Turn strategy does, so the
    reading is usually ready by the time the speech service proposes that the turn has ended.
    Pauses are only judged in the caller's own turn; while Kenji talks the model would only cost
    time.
    """

    def __init__(self, analyzer: BaseTurnAnalyzer) -> None:
        self._analyzer = analyzer
        self._is_speaking = False
        self._is_pause_judged = False
        self._finished_probability: float | None = None

    @property
    def finished_probability(self) -> float | None:
        """How likely the caller had finished at their latest pause; None with no reading."""
        return self._finished_probability

    async def judge_latest_pause(self) -> float | None:
        """The reading of the latest pause, judged now if the VAD has not heard the pause yet."""
        if not self._is_pause_judged:
            await self._judge()
        return self._finished_probability

    async def hear(self, frame: Frame, *, is_callers_turn: bool) -> None:
        if isinstance(frame, InputAudioRawFrame):
            self._take_in(frame)
        elif isinstance(frame, VADUserStartedSpeakingFrame):
            self._is_speaking = True
            self._forget_the_reading()
            self._analyzer.update_vad_start_secs(frame.start_secs)
        elif isinstance(frame, VADUserStoppedSpeakingFrame):
            self._is_speaking = False
            if is_callers_turn:
                await self._judge()

    def forget(self) -> None:
        self._forget_the_reading()
        self._analyzer.clear()  # type: ignore[no-untyped-call]

    async def close(self) -> None:
        await self._analyzer.cleanup()  # type: ignore[no-untyped-call]

    def _take_in(self, frame: InputAudioRawFrame) -> None:
        # Told the rate the audio really has, Smart Turn resamples it to the 16 kHz it was trained
        # on, so a phone call's audio is never read at the wrong speed.
        if self._analyzer.sample_rate != frame.sample_rate:
            self._analyzer.set_sample_rate(frame.sample_rate)
        self._analyzer.append_audio(frame.audio, self._is_speaking)

    def _forget_the_reading(self) -> None:
        self._is_pause_judged = False
        self._finished_probability = None

    async def _judge(self) -> None:
        self._finished_probability = await self._read_the_voice()
        self._is_pause_judged = True

    async def _read_the_voice(self) -> float | None:
        if not self._analyzer.speech_triggered:
            return None
        try:
            _, metrics = await self._analyzer.analyze_end_of_turn()
        except Exception:
            logger.exception("Smart Turn could not judge a pause; the speech service decides alone")
            return None
        return metrics.probability if isinstance(metrics, TurnMetricsData) else None


class UnfinishedPhraseHold(ExternalUserTurnStopStrategy):  # type: ignore[no-untyped-call]
    """Ends the turn where the speech service proposes, unless the caller sounds unfinished.

    「生年月日は、」 followed by a breath is not a finished turn, and nor is 「お支払いは来月の」
    when Smart Turn hears the voice still going. Either is held open for a grace period: if the
    caller carries on, their words join the same turn; if not, it closes. A pause Smart Turn hears
    as the end of the turn closes at once, with no grace period added.
    """

    def __init__(
        self,
        *,
        grace: TurnEndGrace | None = None,
        caller_hold: CallerHold | None = None,
        smart_turn: Callable[[], BaseTurnAnalyzer] | None = None,
        on_turn_end: TurnEndListener | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._grace = grace or TurnEndGrace()
        self._load_smart_turn = smart_turn
        self._smart_turn: SmartTurnOpinion | None = None
        self._on_turn_end = on_turn_end
        self._heard = ""
        self._is_callers_turn = False
        self._proposed_at_ms = 0.0
        self._ended_for: TurnEndWait | None = None
        self._hold: asyncio.Task[None] | None = None
        self._caller_hold = caller_hold
        self._closes_when_done: tuple[bool | None] | None = None
        if caller_hold is not None:
            caller_hold.when_released(self._close_after_done)

    async def setup(self, setup: FrameProcessorSetup) -> None:  # type: ignore[override]
        await super().setup(setup)
        if self._load_smart_turn is not None and self._smart_turn is None:
            # Loading the model takes a moment; off the event loop, other calls keep their audio.
            analyzer = await asyncio.to_thread(self._load_smart_turn)
            self._smart_turn = SmartTurnOpinion(analyzer)

    async def cleanup(self) -> None:
        await super().cleanup()  # type: ignore[no-untyped-call]
        if self._smart_turn is not None:
            await self._smart_turn.close()

    async def handle_user_turn_started(self) -> None:
        await super().handle_user_turn_started()  # type: ignore[no-untyped-call]
        self._start_listening_afresh()
        self._is_callers_turn = True

    async def handle_user_turn_stopped(self) -> None:
        await super().handle_user_turn_stopped()  # type: ignore[no-untyped-call]
        self._report_turn_end()
        self._start_listening_afresh()
        self._is_callers_turn = False
        if self._smart_turn is not None:
            self._smart_turn.forget()

    async def process_frame(self, frame: Frame) -> ProcessFrameResult:
        if isinstance(frame, TranscriptionFrame):
            self._heard += frame.text
        elif isinstance(frame, _SPEECH_RESUMED):
            self._release_hold()
        if self._smart_turn is not None:
            await self._smart_turn.hear(frame, is_callers_turn=self._is_callers_turn)
        result: ProcessFrameResult = await super().process_frame(frame)
        return result

    async def trigger_user_turn_stopped(
        self, *, enable_user_speaking_frames: bool | None = None
    ) -> None:
        if self._hold is not None or self._closes_when_done is not None:
            return
        self._proposed_at_ms = _monotonic_ms()
        self._hold = self.create_task(
            self._close_when_finished(enable_user_speaking_frames), f"{self}::hold"
        )

    async def _close_when_finished(self, enable_user_speaking_frames: bool | None) -> None:
        """Ends the turn, after a grace period if the caller does not sound finished."""
        wait = turn_end_wait(self._heard, await self._reading_of_the_voice())
        if wait is not TurnEndWait.NONE and not self._is_on_hold():
            await asyncio.sleep(self._grace.secs(wait))
        self._hold = None
        await self._close(enable_user_speaking_frames, wait)

    async def _close(self, enable_user_speaking_frames: bool | None, wait: TurnEndWait) -> None:
        if self._is_on_hold():
            self._closes_when_done = (enable_user_speaking_frames,)
            return
        await self._end_turn(enable_user_speaking_frames, wait)

    async def _close_after_done(self) -> None:
        """The caller pressed Done: a turn that would have ended while on hold ends now."""
        pending, self._closes_when_done = self._closes_when_done, None
        if pending is not None:
            await self._end_turn(pending[0], TurnEndWait.CALLER_HOLD)

    async def _end_turn(self, enable_user_speaking_frames: bool | None, wait: TurnEndWait) -> None:
        self._ended_for = wait
        await super().trigger_user_turn_stopped(
            enable_user_speaking_frames=enable_user_speaking_frames
        )

    def _report_turn_end(self) -> None:
        """Says why Kenji answered when he did. A turn the watchdog closed has nothing to say."""
        if self._on_turn_end is None or self._ended_for is None:
            return
        self._on_turn_end(
            TurnEndJudged(
                finished_probability=self._reported_reading(),
                waited_for=self._ended_for,
                waited_ms=max(0.0, _monotonic_ms() - self._proposed_at_ms),
            )
        )

    async def _reading_of_the_voice(self) -> float | None:
        return None if self._smart_turn is None else await self._smart_turn.judge_latest_pause()

    def _reported_reading(self) -> float | None:
        return None if self._smart_turn is None else self._smart_turn.finished_probability

    def _is_on_hold(self) -> bool:
        return self._caller_hold is not None and self._caller_hold.is_on

    def _start_listening_afresh(self) -> None:
        self._release_hold()
        self._heard = ""
        self._closes_when_done = None
        self._ended_for = None

    def _release_hold(self) -> None:
        if self._hold is not None:
            self._hold.cancel()
            self._hold = None


class AnswerWatch(FrameProcessor):
    """Sits after the model and tells the floor when it has answered and when it has finished.

    Only words or a tool call count as an answer: an empty completion leaves the floor
    awaiting the model, which is how the answer guard notices it.
    """

    def __init__(self, floor: Floor) -> None:
        super().__init__()
        self._floor = floor

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, FunctionCallsStartedFrame) or (
            isinstance(frame, LLMTextFrame) and frame.text.strip()
        ):
            self._floor.model_answered()
        elif isinstance(frame, LLMFullResponseEndFrame):
            self._floor.answer_ready()
        await self.push_frame(frame, direction)
