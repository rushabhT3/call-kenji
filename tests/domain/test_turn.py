import pytest

from kenji.domain.turn import (
    STILL_TALKING_GRACE_SECS,
    UNFINISHED_PHRASE_GRACE_SECS,
    LexiconBackchannelClassifier,
    TurnEndGrace,
    TurnEndWait,
    TurnPolicy,
    TurnVerdict,
    decide,
    is_composed_of,
    sounds_unfinished,
    turn_end_wait,
)

READING_TERMS = TurnPolicy(min_interruption_score=0.85)
CONVERSING = TurnPolicy(min_interruption_score=0.5)


@pytest.fixture
def classifier() -> LexiconBackchannelClassifier:
    return LexiconBackchannelClassifier()


def test_hai_is_ignored_while_reading_terms(classifier: LexiconBackchannelClassifier) -> None:
    decision = classifier.classify("はい", READING_TERMS)

    assert decision.verdict is TurnVerdict.BACKCHANNEL
    assert decision.score == 0.0


def test_chotto_matte_kudasai_stops_the_agent(classifier: LexiconBackchannelClassifier) -> None:
    decision = classifier.classify("ちょっと待ってください", READING_TERMS)

    assert decision.verdict is TurnVerdict.INTERRUPTION
    assert decision.score == 1.0


@pytest.mark.parametrize(
    "utterance", ["はいはい", "うーん", "ええ、そうですね", "ナルホド", "はーい。"]
)
def test_strings_of_aizuchi_are_backchannel(
    classifier: LexiconBackchannelClassifier, utterance: str
) -> None:
    assert classifier.classify(utterance, CONVERSING).verdict is TurnVerdict.BACKCHANNEL


def test_characters_are_counted_without_splitting_on_spaces(
    classifier: LexiconBackchannelClassifier,
) -> None:
    decision = classifier.classify("今月 は 無理 です", CONVERSING)

    assert decision.characters == 7


def test_same_speech_interrupts_a_lenient_node_but_not_a_strict_one(
    classifier: LexiconBackchannelClassifier,
) -> None:
    utterance = "今月は無理です"

    assert classifier.classify(utterance, CONVERSING).verdict is TurnVerdict.INTERRUPTION
    assert classifier.classify(utterance, READING_TERMS).verdict is TurnVerdict.BACKCHANNEL


def test_silence_is_backchannel(classifier: LexiconBackchannelClassifier) -> None:
    decision = classifier.classify("、。 ", CONVERSING)

    assert decision.verdict is TurnVerdict.BACKCHANNEL
    assert decision.characters == 0


def test_classifier_rejects_non_positive_half_score() -> None:
    with pytest.raises(ValueError, match="half_score_characters"):
        LexiconBackchannelClassifier(half_score_characters=0)


@pytest.mark.parametrize("threshold", [0.0, 1.5])
def test_policy_rejects_threshold_outside_unit_interval(threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold"):
        TurnPolicy(min_interruption_score=threshold)


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_decide_rejects_score_outside_unit_interval(score: float) -> None:
    with pytest.raises(ValueError, match="score"):
        decide("はい", score, CONVERSING)


def test_is_composed_of_requires_full_coverage() -> None:
    words = frozenset({"はい", "ええ"})

    assert is_composed_of("はいええ", words)
    assert not is_composed_of("はいえ", words)
    assert not is_composed_of("", words)


@pytest.mark.parametrize("confirmation", ["間違いありません", "大丈夫です", "それで結構です"])
def test_confirmations_over_the_read_back_do_not_interrupt(
    classifier: LexiconBackchannelClassifier, confirmation: str
) -> None:
    assert classifier.classify(confirmation, READING_TERMS).verdict is TurnVerdict.BACKCHANNEL


@pytest.mark.parametrize(
    "correction",
    [
        "違います",
        "そうじゃなくて",
        "いいえ、10日です",
        "すみません、金額が違います",
        "日付を変えたいです",
        "もう一度お願いします",
        "金額を変更できますか",
    ],
)
def test_corrections_over_the_read_back_interrupt(
    classifier: LexiconBackchannelClassifier, correction: str
) -> None:
    assert classifier.classify(correction, READING_TERMS).verdict is TurnVerdict.INTERRUPTION


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。生年月日は。",
        "金額は、",
        "毎月の支払いを",
        "えっと",
        "今月はちょっと",
        "それで",
    ],
)
def test_speech_that_stops_on_a_particle_or_filler_is_unfinished(speech: str) -> None:
    assert sounds_unfinished(speech)


@pytest.mark.parametrize(
    "speech",
    [
        "佐藤ゆうきです。",
        "平成2年7月14日です。",
        "6000円でお願いします。",
        "どうなるんですか？",
        "こんにちは。",
        "今月は厳しいので。",
        "払いたいのですが",
        "",
    ],
)
def test_speech_that_ends_like_a_turn_is_finished(speech: str) -> None:
    assert not sounds_unfinished(speech)


def test_a_caller_who_sounds_finished_is_answered_at_once() -> None:
    assert turn_end_wait("佐藤ゆうきです。", finished_probability=0.91) is TurnEndWait.NONE


def test_a_caller_whose_voice_is_still_going_is_waited_for() -> None:
    wait = turn_end_wait("お支払いは来月の。", finished_probability=0.23)

    assert wait is TurnEndWait.STILL_TALKING


def test_words_left_on_a_particle_are_waited_for_however_they_sound() -> None:
    wait = turn_end_wait("生年月日は。", finished_probability=0.97)

    assert wait is TurnEndWait.UNFINISHED_PHRASE


def test_with_no_reading_of_the_voice_the_speech_service_is_trusted() -> None:
    assert turn_end_wait("佐藤ゆうきです。", finished_probability=None) is TurnEndWait.NONE


def test_an_even_reading_of_the_voice_is_not_taken_as_finished() -> None:
    assert turn_end_wait("来月の。", finished_probability=0.5) is TurnEndWait.STILL_TALKING


@pytest.mark.parametrize("probability", [-0.1, 1.1])
def test_turn_end_wait_rejects_probability_outside_unit_interval(probability: float) -> None:
    with pytest.raises(ValueError, match="probability"):
        turn_end_wait("はい。", probability)


def test_each_wait_has_its_own_grace() -> None:
    grace = TurnEndGrace()

    assert grace.secs(TurnEndWait.UNFINISHED_PHRASE) == UNFINISHED_PHRASE_GRACE_SECS
    assert grace.secs(TurnEndWait.STILL_TALKING) == STILL_TALKING_GRACE_SECS
    assert grace.secs(TurnEndWait.NONE) == 0.0
