"""When a caller's turn starts and ends.

Start: speech over Kenji only interrupts when it is more than aizuchi. Pipecat's word-count
strategy splits on spaces, which Japanese does not have, so the domain's BackchannelClassifier
decides instead, with the current node's policy.

End: the speech service proposes where a turn ends, and a phrase left hanging on a particle is
held open a little longer before Kenji answers it.
"""

import asyncio
import time
from collections.abc import Callable
from typing import Any

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    FunctionCallsStartedFrame,
    InterimTranscriptionFrame,
    LLMFullResponseEndFrame,
    LLMTextFrame,
    ProposedUserStartedSpeakingFrame,
    TranscriptionFrame,
    VADUserStartedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.turns.types import ProcessFrameResult
from pipecat.turns.user_start import BaseUserTurnStartStrategy
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy

from kenji.domain.turn import (
    UNFINISHED_PHRASE_GRACE_SECS,
    BackchannelClassifier,
    TurnDecision,
    TurnPolicy,
    TurnVerdict,
    sounds_unfinished,
)

type DecisionListener = Callable[[str, TurnDecision, float], None]
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


class UnfinishedPhraseHold(ExternalUserTurnStopStrategy):  # type: ignore[no-untyped-call]
    """Ends the turn where the speech service proposes, unless the words stop mid-phrase.

    「生年月日は、」 followed by a breath is not a finished turn. It is held open for a grace
    period: if the caller carries on, their words join the same turn; if not, it closes.
    """

    def __init__(
        self,
        *,
        grace_secs: float = UNFINISHED_PHRASE_GRACE_SECS,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._grace_secs = grace_secs
        self._heard = ""
        self._hold: asyncio.Task[None] | None = None

    async def handle_user_turn_started(self) -> None:
        await super().handle_user_turn_started()  # type: ignore[no-untyped-call]
        self._start_listening_afresh()

    async def handle_user_turn_stopped(self) -> None:
        await super().handle_user_turn_stopped()  # type: ignore[no-untyped-call]
        self._start_listening_afresh()

    async def process_frame(self, frame: Frame) -> ProcessFrameResult:
        if isinstance(frame, TranscriptionFrame):
            self._heard += frame.text
        elif isinstance(frame, _SPEECH_RESUMED):
            self._release_hold()
        result: ProcessFrameResult = await super().process_frame(frame)
        return result

    async def trigger_user_turn_stopped(
        self, *, enable_user_speaking_frames: bool | None = None
    ) -> None:
        if self._hold is not None:
            return
        if sounds_unfinished(self._heard):
            self._hold = self.create_task(
                self._close_after_grace(enable_user_speaking_frames), f"{self}::hold"
            )
            return
        await super().trigger_user_turn_stopped(
            enable_user_speaking_frames=enable_user_speaking_frames
        )

    async def _close_after_grace(self, enable_user_speaking_frames: bool | None) -> None:
        await asyncio.sleep(self._grace_secs)
        self._hold = None
        await super().trigger_user_turn_stopped(
            enable_user_speaking_frames=enable_user_speaking_frames
        )

    def _start_listening_afresh(self) -> None:
        self._release_hold()
        self._heard = ""

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
