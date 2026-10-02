import pytest

from kenji.domain.turn import (
    LexiconBackchannelClassifier,
    TurnPolicy,
    TurnVerdict,
    decide,
    is_composed_of,
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
