"""Text helpers that the transcript and the turn classifier rely on."""

import pytest

from kenji.domain.text import without_repeated_sentence_ends, without_stray_latin_words


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


@pytest.mark.parametrize(
    ("raw", "clean"),
    [
        (
            "お名前の読み Frieden確認のため、もう一度だけお聞かせいただけますでしょうか。",
            "お名前の読み確認のため、もう一度だけお聞かせいただけますでしょうか。",
        ),
        ("みなとのAIアシスタント、ケンジです。", "みなとのAIアシスタント、ケンジです。"),
        ("毎月6,000円です。", "毎月6,000円です。"),
    ],
)
def test_a_stray_latin_word_is_dropped_but_ai_is_kept(raw: str, clean: str) -> None:
    assert without_stray_latin_words(raw) == clean
