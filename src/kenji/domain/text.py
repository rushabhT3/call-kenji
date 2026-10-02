"""Character-level helpers for Japanese text, which has no word spaces."""

import unicodedata

_KATAKANA_FIRST = ord("ァ")
_KATAKANA_LAST = ord("ヶ")
_KATAKANA_TO_HIRAGANA_OFFSET = ord("ァ") - ord("ぁ")
_FULLWIDTH_TO_ASCII = str.maketrans("０１２３４５６７８９，￥／－", "0123456789,¥/-")


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
