"""Text helpers that the transcript and the turn classifier rely on."""

import pytest

from kenji.domain.text import without_repeated_sentence_ends


@pytest.mark.parametrize(
    ("raw", "tidy"),
    [
        ("おっしゃらないでください。。", "おっしゃらないでください。"),
        ("よろしいでしょうか？？", "よろしいでしょうか？"),
        ("はい。承知しました。", "はい。承知しました。"),
    ],
)
def test_a_repeated_sentence_end_is_kept_once(raw: str, tidy: str) -> None:
    assert without_repeated_sentence_ends(raw) == tidy
