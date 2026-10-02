"""The backchannel strategy inside Pipecat's real user aggregator."""

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    Frame,
    InterimTranscriptionFrame,
    InterruptionFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    VADUserStartedSpeakingFrame,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMUserAggregator,
    LLMUserAggregatorParams,
)
from pipecat.tests.utils import SleepFrame, run_test
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.utils.time import time_now_iso8601

from kenji.app.turns import BackchannelTurnStartStrategy
from kenji.domain.turn import LexiconBackchannelClassifier, TurnDecision, TurnPolicy, TurnVerdict

READ_BACK = TurnPolicy(min_interruption_score=0.85)


def _text(text: str, *, final: bool) -> Frame:
    kind = TranscriptionFrame if final else InterimTranscriptionFrame
    return kind(text=text, user_id="caller", timestamp=time_now_iso8601())


async def _speak_over_kenji(utterance: str) -> tuple[list[str], list[TurnDecision], str]:
    decisions: list[TurnDecision] = []
    clock = iter(range(0, 10_000, 250))
    strategy = BackchannelTurnStartStrategy(
        classifier=LexiconBackchannelClassifier(),
        policy=lambda: READ_BACK,
        on_decision=lambda _text, decision, _overlap: decisions.append(decision),
        clock_ms=lambda: float(next(clock)),
    )
    aggregator = LLMUserAggregator(
        LLMContext(),
        params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                start=[strategy], stop=[ExternalUserTurnStopStrategy(timeout=0.05)]
            )
        ),
    )
    downstream, _ = await run_test(
        aggregator,
        frames_to_send=[
            BotStartedSpeakingFrame(),
            VADUserStartedSpeakingFrame(),
            _text(utterance, final=False),
            SleepFrame(sleep=0.2),
            _text(utterance, final=True),
            SleepFrame(sleep=0.2),
        ],
    )
    return (
        [type(frame).__name__ for frame in downstream],
        decisions,
        aggregator.aggregation_string(),
    )


async def test_hai_while_reading_terms_does_not_interrupt() -> None:
    frames, decisions, aggregation = await _speak_over_kenji("はい")

    assert InterruptionFrame.__name__ not in frames
    assert [decision.verdict for decision in decisions] == [TurnVerdict.BACKCHANNEL]
    assert aggregation == ""


async def test_chotto_matte_kudasai_stops_kenji() -> None:
    frames, decisions, _ = await _speak_over_kenji("ちょっと待ってください")

    assert InterruptionFrame.__name__ in frames
    assert UserStartedSpeakingFrame.__name__ in frames
    assert decisions[0].verdict is TurnVerdict.INTERRUPTION
