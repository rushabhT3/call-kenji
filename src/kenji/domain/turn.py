"""Decide if speech over Kenji is aizuchi or an interruption, and if a quiet caller has finished."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from kenji.domain.text import count_spoken_characters, spoken_characters, to_hiragana

DEFAULT_AIZUCHI = (
    "はい",
    "ええ",
    "うん",
    "そうですね",
    "なるほど",
    "そうですか",
    "そう",
    "はあ",
    "ああ",
)
DEFAULT_URGENT_PHRASES = (
    "待って",
    "まって",
    "ちょっと",
    "すみません",
    "すいません",
    "違います",
    "ちがいます",
    "違う",
    "ちがう",
    "いいえ",
    "そうじゃなく",
    "そうではなく",
    "すとっぷ",
    "やめて",
    "止めて",
    "もう一度",
    "もういちど",
    "変え",
    "変更",
    "訂正",
)
DEFAULT_HALF_SCORE_CHARACTERS = 4
_ELONGATION_MARKS = str.maketrans("", "", "ー〜～")
# Japanese marks a finished turn at its very end (です, ます, か). Speech that stops on a topic or
# case particle, a pause comma or a filler is still mid-sentence. Conjunctive endings such as
# けど, から and ので are left out on purpose: callers often end a turn on them and imply the rest.
UNFINISHED_ENDINGS = (
    "、",
    "は",
    "を",
    "が",
    "に",
    "で",
    "へ",
    "と",
    "も",
    "えっと",
    "あの",
    "その",
)
FINISHED_DESPITE_ENDING = ("こんにちは", "こんばんは", "ですが", "ますが", "ので", "んで")
UNFINISHED_PHRASE_GRACE_SECS = 2.0
# Smart Turn itself ends a turn it hears as unfinished after 3 s of silence. By the time the
# speech service proposes the end, a good part of that silence has usually passed.
STILL_TALKING_GRACE_SECS = 1.5
# Above this, a reading of the caller's voice says they have finished, as Smart Turn's own does.
FINISHED_ABOVE = 0.5
_CLOSING_MARKS = "。．. "


class TurnVerdict(StrEnum):
    BACKCHANNEL = "backchannel"
    INTERRUPTION = "interruption"


class TurnEndWait(StrEnum):
    """Why Kenji waited to answer after the speech service said the caller had finished."""

    NONE = "none"
    UNFINISHED_PHRASE = "unfinished_phrase"
    STILL_TALKING = "still_talking"
    CALLER_HOLD = "caller_hold"


@dataclass(frozen=True, slots=True)
class TurnEndGrace:
    """How long Kenji waits for more from a caller who has not finished, before answering."""

    unfinished_phrase_secs: float = UNFINISHED_PHRASE_GRACE_SECS
    still_talking_secs: float = STILL_TALKING_GRACE_SECS

    def secs(self, wait: TurnEndWait) -> float:
        if wait is TurnEndWait.UNFINISHED_PHRASE:
            return self.unfinished_phrase_secs
        if wait is TurnEndWait.STILL_TALKING:
            return self.still_talking_secs
        return 0.0


@dataclass(frozen=True, slots=True)
class TurnPolicy:
    min_interruption_score: float

    def __post_init__(self) -> None:
        if not 0.0 < self.min_interruption_score <= 1.0:
            raise ValueError(f"threshold must be in (0, 1], got {self.min_interruption_score}")


@dataclass(frozen=True, slots=True)
class TurnDecision:
    characters: int
    score: float
    verdict: TurnVerdict


class BackchannelClassifier(Protocol):
    def classify(self, utterance: str, policy: TurnPolicy) -> TurnDecision: ...


def decide(utterance: str, score: float, policy: TurnPolicy) -> TurnDecision:
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"score must be in [0, 1], got {score}")
    verdict = (
        TurnVerdict.INTERRUPTION
        if score >= policy.min_interruption_score
        else TurnVerdict.BACKCHANNEL
    )
    return TurnDecision(characters=count_spoken_characters(utterance), score=score, verdict=verdict)


def _normalize(utterance: str) -> str:
    return spoken_characters(to_hiragana(utterance).translate(_ELONGATION_MARKS))


def sounds_unfinished(transcript: str) -> bool:
    """Whether a caller who has gone quiet stopped mid-sentence, as in 「生年月日は、」."""
    # The speech service closes every finalised segment with 。, even mid-sentence.
    words = transcript.strip().rstrip(_CLOSING_MARKS)
    if not words or words.endswith(FINISHED_DESPITE_ENDING):
        return False
    return words.endswith(UNFINISHED_ENDINGS)


def turn_end_wait(transcript: str, finished_probability: float | None) -> TurnEndWait:
    """Whether to wait for more from a caller the speech service says has finished.

    The words come first: a phrase left on a particle is unfinished however it sounds. Otherwise
    the reading of the voice decides, and with no reading the speech service is taken at its word.
    """
    if finished_probability is not None and not 0.0 <= finished_probability <= 1.0:
        raise ValueError(f"probability must be in [0, 1], got {finished_probability}")
    if sounds_unfinished(transcript):
        return TurnEndWait.UNFINISHED_PHRASE
    if finished_probability is None or finished_probability > FINISHED_ABOVE:
        return TurnEndWait.NONE
    return TurnEndWait.STILL_TALKING


def is_composed_of(text: str, words: frozenset[str]) -> bool:
    reachable = {0}
    for end in range(1, len(text) + 1):
        if any(start in reachable and text[start:end] in words for start in range(end)):
            reachable.add(end)
    return bool(text) and len(text) in reachable


class LexiconBackchannelClassifier:
    def __init__(
        self,
        aizuchi: tuple[str, ...] = DEFAULT_AIZUCHI,
        urgent_phrases: tuple[str, ...] = DEFAULT_URGENT_PHRASES,
        half_score_characters: int = DEFAULT_HALF_SCORE_CHARACTERS,
    ) -> None:
        if half_score_characters <= 0:
            raise ValueError("half_score_characters must be positive")
        self._aizuchi = frozenset(_normalize(word) for word in aizuchi)
        self._urgent_phrases = tuple(_normalize(phrase) for phrase in urgent_phrases)
        self._half_score_characters = half_score_characters

    def classify(self, utterance: str, policy: TurnPolicy) -> TurnDecision:
        return decide(utterance, self._score(_normalize(utterance)), policy)

    def _score(self, normalized: str) -> float:
        if not normalized or is_composed_of(normalized, self._aizuchi):
            return 0.0
        if any(phrase in normalized for phrase in self._urgent_phrases):
            return 1.0
        characters = len(normalized)
        return characters / (characters + self._half_score_characters)
