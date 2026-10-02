"""Character-level helpers for Japanese text, which has no word spaces."""

import re
import unicodedata

_KATAKANA_FIRST = ord("ァ")
_KATAKANA_LAST = ord("ヶ")
_KATAKANA_TO_HIRAGANA_OFFSET = ord("ァ") - ord("ぁ")
_FULLWIDTH_TO_ASCII = str.maketrans("０１２３４５６７８９，￥／－", "0123456789,¥/-")
_REPEATED_SENTENCE_END = re.compile(r"([。！？])\1+")
# Kenji speaks Japanese only; the model now and then slips a Latin word into a sentence.
_STRAY_LATIN_WORD = re.compile(r"\s*(?<![A-Za-z])(?!AI(?![A-Za-z]))[A-Za-z]{2,}(?![A-Za-z])\s*")


def to_hiragana(text: str) -> str:
    return "".join(_katakana_char_to_hiragana(char) for char in text)


def _katakana_char_to_hiragana(char: str) -> str:
    code = ord(char)
    if _KATAKANA_FIRST <= code <= _KATAKANA_LAST:
        return chr(code - _KATAKANA_TO_HIRAGANA_OFFSET)
    return char


def is_spoken_character(char: str) -> bool:
    return unicodedata.category(char)[0] in {"L", "N"}


def spoken_characters(text: str) -> str:
    return "".join(char for char in text if is_spoken_character(char))


def count_spoken_characters(text: str) -> int:
    return len(spoken_characters(text))


def ascii_digits(text: str) -> str:
    return text.translate(_FULLWIDTH_TO_ASCII)


def without_repeated_sentence_ends(text: str) -> str:
    return _REPEATED_SENTENCE_END.sub(r"\1", text)


def without_stray_latin_words(text: str) -> str:
    return _STRAY_LATIN_WORD.sub("", text)
