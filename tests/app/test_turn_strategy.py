"""The turn strategies inside Pipecat's real user aggregator."""

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    Frame,
    InterimTranscriptionFrame,
    InterruptionFrame,
    LLMFullResponseEndFrame,
    ProposedUserStartedSpeakingFrame,
    ProposedUserStoppedSpeakingFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
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

from kenji.app.turns import (
    AnswerWatch,
    BackchannelTurnStartStrategy,
    Floor,
    UnfinishedPhraseHold,
)
from kenji.domain.turn import LexiconBackchannelClassifier, TurnDecision, TurnPolicy, TurnVerdict

READ_BACK = TurnPolicy(min_interruption_score=0.85)
CONVERSING = TurnPolicy(min_interruption_score=0.5)
GRACE_SECS = 0.4


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


async def _caller_speaks(*frames: Frame) -> tuple[list[str], list[str]]:
    context = LLMContext()
    start = BackchannelTurnStartStrategy(
        classifier=LexiconBackchannelClassifier(),
        policy=lambda: CONVERSING,
        on_decision=lambda *_: None,
    )
    stop = UnfinishedPhraseHold(timeout=0.05, grace_secs=GRACE_SECS)
    aggregator = LLMUserAggregator(
        context,
        params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(start=[start], stop=[stop])
        ),
    )
    downstream, _ = await run_test(
        aggregator,
        frames_to_send=[VADUserStartedSpeakingFrame(), ProposedUserStartedSpeakingFrame(), *frames],
    )
    messages = [message for message in context.get_messages() if isinstance(message, dict)]
    turns = [str(message.get("content")) for message in messages if message.get("role") == "user"]
    return [type(frame).__name__ for frame in downstream], turns


async def test_a_finished_sentence_ends_the_turn_where_the_service_proposes() -> None:
    frames, turns = await _caller_speaks(
        _text("佐藤ゆうきです。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=0.2),
    )

    assert turns == ["佐藤ゆうきです。"]
    assert frames.count(UserStoppedSpeakingFrame.__name__) == 1


async def test_a_phrase_left_on_a_particle_is_held_open() -> None:
    frames, _ = await _caller_speaks(
        _text("生年月日は。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=GRACE_SECS / 2),
    )

    assert UserStoppedSpeakingFrame.__name__ not in frames


async def test_a_held_phrase_closes_when_the_caller_stays_quiet() -> None:
    _, turns = await _caller_speaks(
        _text("生年月日は。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=GRACE_SECS + 0.3),
    )

    assert turns == ["生年月日は。"]


async def test_speech_after_the_pause_joins_the_same_turn() -> None:
    frames, turns = await _caller_speaks(
        _text("佐藤ゆうきです。生年月日は。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=GRACE_SECS / 2),
        ProposedUserStartedSpeakingFrame(),
        _text("平成2年", final=False),
        SleepFrame(sleep=GRACE_SECS + 0.2),
        _text("平成2年7月14日です。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=0.2),
    )

    assert frames.count(UserStoppedSpeakingFrame.__name__) == 1
    assert len(turns) == 1
    assert "生年月日は" in turns[0]
    assert "平成2年7月14日です" in turns[0]


async def _speak_while_kenji_holds_the_floor(utterance: str) -> tuple[list[str], Floor]:
    floor = Floor()
    floor.hold()
    strategy = BackchannelTurnStartStrategy(
        classifier=LexiconBackchannelClassifier(),
        policy=lambda: READ_BACK,
        on_decision=lambda *_: None,
        floor=floor,
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
            VADUserStartedSpeakingFrame(),
            _text(utterance, final=True),
            SleepFrame(sleep=0.2),
        ],
    )
    return [type(frame).__name__ for frame in downstream], floor


async def test_aizuchi_after_kenjis_acknowledgement_does_not_take_the_turn() -> None:
    frames, floor = await _speak_while_kenji_holds_the_floor("はい")

    assert UserStartedSpeakingFrame.__name__ not in frames
    assert floor.is_held


async def test_a_real_interruption_after_the_acknowledgement_takes_the_turn() -> None:
    frames, floor = await _speak_while_kenji_holds_the_floor("ちょっと待ってください")

    assert UserStartedSpeakingFrame.__name__ in frames
    assert not floor.is_held


def test_the_floor_is_kept_through_the_gap_and_released_when_the_answer_starts() -> None:
    floor = Floor()
    floor.hold()

    floor.kenji_started_speaking()
    assert floor.is_held
    floor.kenji_stopped_speaking()
    assert floor.is_held
    floor.kenji_started_speaking()
    assert not floor.is_held


def test_speech_unrelated_to_a_held_floor_changes_nothing() -> None:
    floor = Floor()

    floor.kenji_stopped_speaking()
    floor.kenji_started_speaking()

    assert not floor.is_held


def test_the_floor_is_released_when_kenji_stops_after_the_model_has_answered() -> None:
    floor = Floor()
    floor.hold()

    floor.answer_ready()
    assert floor.is_held
    floor.kenji_stopped_speaking()
    assert not floor.is_held


def test_an_answer_with_no_floor_held_is_ignored() -> None:
    floor = Floor()

    floor.answer_ready()
    floor.hold()
    floor.kenji_stopped_speaking()

    assert floor.is_held


async def test_the_answer_watch_marks_the_end_of_the_models_answer() -> None:
    floor = Floor()
    floor.hold()

    await run_test(AnswerWatch(floor), frames_to_send=[LLMFullResponseEndFrame()])
    floor.kenji_stopped_speaking()

    assert not floor.is_held
