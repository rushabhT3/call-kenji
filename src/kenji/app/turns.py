"""Turn start strategy: speech over Kenji only interrupts when it is more than aizuchi.

Pipecat's word-count strategy splits on spaces, which Japanese does not have, so this
strategy asks the domain's BackchannelClassifier instead, with the current node's policy.
"""

import time
from collections.abc import Callable

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    InterimTranscriptionFrame,
    TranscriptionFrame,
    VADUserStartedSpeakingFrame,
)
from pipecat.turns.types import ProcessFrameResult
from pipecat.turns.user_start import BaseUserTurnStartStrategy

from kenji.domain.turn import BackchannelClassifier, TurnDecision, TurnPolicy, TurnVerdict

type DecisionListener = Callable[[str, TurnDecision, float], None]


def _monotonic_ms() -> float:
    return time.monotonic() * 1000.0


class BackchannelTurnStartStrategy(BaseUserTurnStartStrategy):  # type: ignore[no-untyped-call]
    def __init__(
        self,
        classifier: BackchannelClassifier,
        policy: Callable[[], TurnPolicy],
        on_decision: DecisionListener,
        clock_ms: Callable[[], float] = _monotonic_ms,
    ) -> None:
        super().__init__()
        self._classifier = classifier
        self._policy = policy
        self._on_decision = on_decision
        self._clock_ms = clock_ms
        self._is_bot_speaking = False
        self._overlap_started_ms: float | None = None

    async def handle_user_turn_started(self) -> None:
        self._is_bot_speaking = False
        self._overlap_started_ms = None

    async def process_frame(self, frame: Frame) -> ProcessFrameResult:
        if isinstance(frame, BotStartedSpeakingFrame):
            self._is_bot_speaking = True
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._is_bot_speaking = False
        elif isinstance(frame, VADUserStartedSpeakingFrame):
            return await self._on_voice(frame)
        elif isinstance(frame, (InterimTranscriptionFrame, TranscriptionFrame)):
            return await self._on_text(frame.text, is_final=isinstance(frame, TranscriptionFrame))
        return ProcessFrameResult.CONTINUE

    async def _on_voice(self, _frame: VADUserStartedSpeakingFrame) -> ProcessFrameResult:
        if not self._is_bot_speaking:
            await self.trigger_user_turn_started()
            return ProcessFrameResult.STOP
        self._overlap_started_ms = self._clock_ms()
        return ProcessFrameResult.CONTINUE

    async def _on_text(self, text: str, *, is_final: bool) -> ProcessFrameResult:
        if not self._is_bot_speaking:
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
