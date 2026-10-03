"""The turn strategies inside Pipecat's real user aggregator."""

import asyncio
from collections.abc import Callable

from pipecat.audio.turn.base_turn_analyzer import (
    BaseTurnAnalyzer,
    BaseTurnParams,
    EndOfTurnState,
)
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    Frame,
    InputAudioRawFrame,
    InterimTranscriptionFrame,
    InterruptionFrame,
    LLMFullResponseEndFrame,
    LLMTextFrame,
    ProposedUserStartedSpeakingFrame,
    ProposedUserStoppedSpeakingFrame,
    TranscriptionFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    VADUserStartedSpeakingFrame,
    VADUserStoppedSpeakingFrame,
)
from pipecat.metrics.metrics import MetricsData, TurnMetricsData
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMUserAggregator,
    LLMUserAggregatorParams,
)
from pipecat.tests.utils import SleepFrame, run_test
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.utils.time import time_now_iso8601

from kenji.app.events import TurnEndJudged
from kenji.app.turns import (
    AnswerWatch,
    BackchannelTurnStartStrategy,
    CallerHold,
    Floor,
    TurnEndListener,
    UnfinishedPhraseHold,
)
from kenji.domain.turn import (
    LexiconBackchannelClassifier,
    TurnDecision,
    TurnEndGrace,
    TurnEndWait,
    TurnPolicy,
    TurnVerdict,
)

READ_BACK = TurnPolicy(min_interruption_score=0.85)
CONVERSING = TurnPolicy(min_interruption_score=0.5)
GRACE_SECS = 0.4
GRACE = TurnEndGrace(unfinished_phrase_secs=GRACE_SECS, still_talking_secs=GRACE_SECS)
PHONE_RATE = 8_000
PIPELINE_RATE = 16_000
# Windows' monotonic clock ticks every 15.6 ms, so a measured wait can fall a tick short.
CLOCK_TICK_MS = 16


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


class FakeSmartTurn(BaseTurnAnalyzer):
    """Hears audio as Smart Turn does and reads every pause the same way."""

    def __init__(self, finished_probability: float) -> None:
        super().__init__()
        self._finished_probability = finished_probability
        self._has_heard_speech = False
        self.pauses_judged = 0

    @property
    def speech_triggered(self) -> bool:
        return self._has_heard_speech

    @property
    def params(self) -> BaseTurnParams:
        return BaseTurnParams()

    def append_audio(self, buffer: bytes, is_speech: bool) -> EndOfTurnState:  # noqa: ARG002
        self._has_heard_speech = self._has_heard_speech or is_speech
        return EndOfTurnState.INCOMPLETE

    async def analyze_end_of_turn(self) -> tuple[EndOfTurnState, MetricsData | None]:
        self.pauses_judged += 1
        is_complete = self._finished_probability > 0.5
        state = EndOfTurnState.COMPLETE if is_complete else EndOfTurnState.INCOMPLETE
        reading = TurnMetricsData(
            processor="fake",
            is_complete=is_complete,
            probability=self._finished_probability,
            e2e_processing_time_ms=1.0,
        )
        return state, reading

    def clear(self) -> None:
        self._has_heard_speech = False


class BrokenSmartTurn(FakeSmartTurn):
    async def analyze_end_of_turn(self) -> tuple[EndOfTurnState, MetricsData | None]:
        raise RuntimeError("the model could not run")


def _loads(analyzer: BaseTurnAnalyzer) -> Callable[[], BaseTurnAnalyzer]:
    return lambda: analyzer


def _audio(sample_rate: int = PIPELINE_RATE) -> Frame:
    twenty_ms_of_silence = bytes(sample_rate // 50 * 2)
    return InputAudioRawFrame(audio=twenty_ms_of_silence, sample_rate=sample_rate, num_channels=1)


def _pause_after(text: str) -> list[Frame]:
    """The caller speaks, goes quiet, and the speech service proposes that the turn is over."""
    return [
        _audio(),
        VADUserStoppedSpeakingFrame(),
        _text(text, final=True),
        ProposedUserStoppedSpeakingFrame(),
    ]


async def _caller_speaks(
    *frames: Frame,
    caller_hold: CallerHold | None = None,
    smart_turn: BaseTurnAnalyzer | None = None,
    on_turn_end: TurnEndListener | None = None,
) -> tuple[list[str], list[str]]:
    context = LLMContext()
    start = BackchannelTurnStartStrategy(
        classifier=LexiconBackchannelClassifier(),
        policy=lambda: CONVERSING,
        on_decision=lambda *_: None,
    )
    stop = UnfinishedPhraseHold(
        timeout=0.05,
        grace=GRACE,
        caller_hold=caller_hold,
        smart_turn=None if smart_turn is None else _loads(smart_turn),
        on_turn_end=on_turn_end,
    )
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
    floor.model_answered()
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

    floor.model_answered()
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

    await run_test(
        AnswerWatch(floor),
        frames_to_send=[LLMTextFrame("承知いたしました。"), LLMFullResponseEndFrame()],
    )
    floor.kenji_stopped_speaking()

    assert not floor.is_held


def test_an_empty_answer_or_kenjis_own_holding_line_does_not_release_the_floor() -> None:
    floor = Floor()
    floor.hold()

    floor.kenji_started_speaking()
    floor.kenji_stopped_speaking()
    floor.answer_ready()
    floor.kenji_started_speaking()
    floor.kenji_stopped_speaking()

    assert floor.is_held
    assert floor.is_awaiting_model


async def test_blank_model_text_is_not_an_answer() -> None:
    floor = Floor()
    floor.hold()

    await run_test(
        AnswerWatch(floor), frames_to_send=[LLMTextFrame("  "), LLMFullResponseEndFrame()]
    )

    assert floor.is_awaiting_model


async def _press_done_after(caller_hold: CallerHold, secs: float) -> None:
    await asyncio.sleep(secs)
    await caller_hold.release()


async def test_a_caller_on_hold_keeps_the_turn_however_long_they_pause() -> None:
    caller_hold = CallerHold()
    caller_hold.put_on()

    frames, _ = await _caller_speaks(
        _text("佐藤ゆうきです。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=GRACE_SECS + 0.3),
        caller_hold=caller_hold,
    )

    assert UserStoppedSpeakingFrame.__name__ not in frames


async def test_pressing_done_hands_the_held_turn_to_kenji_at_once() -> None:
    caller_hold = CallerHold()
    caller_hold.put_on()
    done = asyncio.create_task(_press_done_after(caller_hold, 0.3))

    frames, turns = await _caller_speaks(
        _text("佐藤ゆうきです。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=0.6),
        caller_hold=caller_hold,
    )
    await done

    assert frames.count(UserStoppedSpeakingFrame.__name__) == 1
    assert turns == ["佐藤ゆうきです。"]


async def test_pressing_done_before_the_caller_has_finished_leaves_the_turn_open() -> None:
    caller_hold = CallerHold()
    caller_hold.put_on()
    await caller_hold.release()

    frames, _ = await _caller_speaks(_text("佐藤", final=False), SleepFrame(sleep=0.2))

    assert UserStoppedSpeakingFrame.__name__ not in frames


async def _press_hold_after(caller_hold: CallerHold, secs: float) -> None:
    await asyncio.sleep(secs)
    caller_hold.put_on()


async def test_pressing_hold_while_kenji_waits_keeps_the_turn_open() -> None:
    caller_hold = CallerHold()
    pressed = asyncio.create_task(_press_hold_after(caller_hold, GRACE_SECS / 2))

    frames, _ = await _caller_speaks(
        _text("生年月日は。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=GRACE_SECS + 0.3),
        caller_hold=caller_hold,
    )
    await pressed

    assert UserStoppedSpeakingFrame.__name__ not in frames


async def test_a_pause_smart_turn_hears_as_the_end_is_answered_at_once() -> None:
    ends: list[TurnEndJudged] = []

    _, turns = await _caller_speaks(
        *_pause_after("佐藤ゆうきです。"),
        SleepFrame(sleep=GRACE_SECS / 2),
        smart_turn=FakeSmartTurn(0.91),
        on_turn_end=ends.append,
    )

    assert turns == ["佐藤ゆうきです。"]
    assert [(end.waited_for, end.finished_probability) for end in ends] == [
        (TurnEndWait.NONE, 0.91)
    ]


async def test_a_pause_smart_turn_hears_mid_sentence_is_held_open() -> None:
    frames, _ = await _caller_speaks(
        *_pause_after("お支払いは来月の。"),
        SleepFrame(sleep=GRACE_SECS / 2),
        smart_turn=FakeSmartTurn(0.23),
    )

    assert UserStoppedSpeakingFrame.__name__ not in frames


async def test_a_turn_held_for_smart_turn_closes_when_the_caller_stays_quiet() -> None:
    ends: list[TurnEndJudged] = []

    _, turns = await _caller_speaks(
        *_pause_after("お支払いは来月の。"),
        SleepFrame(sleep=GRACE_SECS + 0.3),
        smart_turn=FakeSmartTurn(0.23),
        on_turn_end=ends.append,
    )

    assert turns == ["お支払いは来月の。"]
    assert ends[0].waited_for is TurnEndWait.STILL_TALKING
    assert ends[0].waited_ms >= GRACE_SECS * 1000 - CLOCK_TICK_MS


async def test_words_left_on_a_particle_are_held_however_finished_they_sound() -> None:
    ends: list[TurnEndJudged] = []

    frames, _ = await _caller_speaks(
        *_pause_after("生年月日は。"),
        SleepFrame(sleep=GRACE_SECS / 2),
        smart_turn=FakeSmartTurn(0.95),
        on_turn_end=ends.append,
    )

    assert UserStoppedSpeakingFrame.__name__ not in frames
    assert ends == []


async def test_the_hold_button_wins_over_a_pause_smart_turn_hears_as_the_end() -> None:
    caller_hold = CallerHold()
    caller_hold.put_on()
    done = asyncio.create_task(_press_done_after(caller_hold, 0.4))
    ends: list[TurnEndJudged] = []

    frames, _ = await _caller_speaks(
        *_pause_after("佐藤ゆうきです。"),
        SleepFrame(sleep=0.7),
        caller_hold=caller_hold,
        smart_turn=FakeSmartTurn(0.95),
        on_turn_end=ends.append,
    )
    await done

    assert frames.count(UserStoppedSpeakingFrame.__name__) == 1
    assert [end.waited_for for end in ends] == [TurnEndWait.CALLER_HOLD]


async def test_with_no_pause_to_judge_the_speech_service_decides_alone() -> None:
    ends: list[TurnEndJudged] = []

    _, turns = await _caller_speaks(
        _text("佐藤ゆうきです。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=0.2),
        smart_turn=FakeSmartTurn(0.1),
        on_turn_end=ends.append,
    )

    assert turns == ["佐藤ゆうきです。"]
    assert [end.finished_probability for end in ends] == [None]


async def test_smart_turn_is_asked_when_the_speech_service_beats_the_vad_to_the_pause() -> None:
    smart_turn = FakeSmartTurn(0.23)

    frames, _ = await _caller_speaks(
        _audio(),
        _text("お支払いは来月の。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=GRACE_SECS / 2),
        smart_turn=smart_turn,
    )

    assert UserStoppedSpeakingFrame.__name__ not in frames
    assert smart_turn.pauses_judged == 1


async def test_a_pause_with_no_speech_heard_before_it_is_not_judged() -> None:
    smart_turn = FakeSmartTurn(0.1)
    ends: list[TurnEndJudged] = []

    await _caller_speaks(
        VADUserStoppedSpeakingFrame(),
        _text("佐藤ゆうきです。", final=True),
        ProposedUserStoppedSpeakingFrame(),
        SleepFrame(sleep=0.2),
        smart_turn=smart_turn,
        on_turn_end=ends.append,
    )

    assert smart_turn.pauses_judged == 0
    assert [end.waited_for for end in ends] == [TurnEndWait.NONE]


async def test_a_reading_that_fails_leaves_the_speech_service_to_decide() -> None:
    ends: list[TurnEndJudged] = []

    _, turns = await _caller_speaks(
        *_pause_after("佐藤ゆうきです。"),
        SleepFrame(sleep=0.2),
        smart_turn=BrokenSmartTurn(0.1),
        on_turn_end=ends.append,
    )

    assert turns == ["佐藤ゆうきです。"]
    assert [end.finished_probability for end in ends] == [None]


async def test_smart_turn_is_told_the_rate_the_audio_really_has() -> None:
    smart_turn = FakeSmartTurn(0.9)

    await _caller_speaks(
        _audio(sample_rate=PHONE_RATE), SleepFrame(sleep=0.1), smart_turn=smart_turn
    )

    assert smart_turn.sample_rate == PHONE_RATE


async def test_pauses_while_kenji_talks_are_not_judged() -> None:
    smart_turn = FakeSmartTurn(0.9)

    await _caller_speaks(
        *_pause_after("佐藤ゆうきです。"),
        SleepFrame(sleep=0.2),
        BotStartedSpeakingFrame(),
        VADUserStartedSpeakingFrame(),
        _audio(),
        VADUserStoppedSpeakingFrame(),
        SleepFrame(sleep=0.1),
        smart_turn=smart_turn,
    )

    assert smart_turn.pauses_judged == 1
