import pytest

from kenji.domain.kana import (
    MAX_READABLE_NUMBER,
    day_count_to_kana,
    day_of_month_to_kana,
    month_to_kana,
    number_to_kana,
    to_speech_kana,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3万5千円", "さんまんごせんえん"),
        ("35,000円", "さんまんごせんえん"),
        ("¥35,000", "さんまんごせんえん"),
        ("1,500万円", "いっせんごひゃくまんえん"),
        ("8000円", "はっせんえん"),
        ("６，０００円", "ろくせんえん"),
    ],
)
def test_amounts_are_read_as_kana(text: str, expected: str) -> None:
    assert to_speech_kana(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("10月27日", "じゅうがつにじゅうしちにち"),
        ("9月30日", "くがつさんじゅうにち"),
        ("11月1日", "じゅういちがつついたち"),
        ("4月14日", "しがつじゅうよっか"),
        ("2026年10月27日", "にせんにじゅうろくねんじゅうがつにじゅうしちにち"),
        ("平成2年7月14日", "へいせいにねんしちがつじゅうよっか"),
        ("平成元年1月8日", "へいせいがんねんいちがつようか"),
        ("令和4年", "れいわよねん"),
        ("12月", "じゅうにがつ"),
    ],
)
def test_dates_are_read_as_kana(text: str, expected: str) -> None:
    assert to_speech_kana(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("毎月6,000円を6回払いで", "毎月ろくせんえんをろっかいばらいで"),
        ("2回", "にかい"),
        ("6か月", "ろっかげつ"),
        ("10ヶ月", "じゅっかげつ"),
        ("45日以内", "よんじゅうごにち以内"),
        ("1日", "いちにち"),
        ("午前8時から午後9時まで", "ごぜんはちじからごごくじまで"),
        ("14時", "じゅうよじ"),
        ("口座番号の末尾は7731です", "口座番号の末尾はなな、なな、さん、いちです"),
    ],
)
def test_counts_times_and_account_digits_are_read_as_kana(text: str, expected: str) -> None:
    assert to_speech_kana(text) == expected


@pytest.mark.parametrize(
    "text",
    ["2時間", "13月", "お電話ありがとうございます。", "12345"],
)
def test_text_without_a_safe_reading_is_left_unchanged(text: str) -> None:
    assert to_speech_kana(text) == text


def test_amount_too_large_to_read_is_left_unchanged() -> None:
    text = f"{MAX_READABLE_NUMBER + 1}円"

    assert to_speech_kana(text) == text


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "ぜろ"),
        (1, "いち"),
        (10, "じゅう"),
        (300, "さんびゃく"),
        (600, "ろっぴゃく"),
        (1000, "せん"),
        (3000, "さんぜん"),
        (5834, "ごせんはっぴゃくさんじゅうよん"),
        (10_000, "いちまん"),
        (10_000_000, "いっせんまん"),
        (100_000_000, "いちおく"),
    ],
)
def test_number_to_kana(value: int, expected: str) -> None:
    assert number_to_kana(value) == expected


@pytest.mark.parametrize("value", [-1, MAX_READABLE_NUMBER + 1])
def test_number_to_kana_rejects_unreadable_values(value: int) -> None:
    with pytest.raises(ValueError, match="cannot read"):
        number_to_kana(value)


def test_month_to_kana_rejects_month_out_of_range() -> None:
    with pytest.raises(ValueError, match="not a month"):
        month_to_kana(0)


def test_day_of_month_to_kana_rejects_day_out_of_range() -> None:
    with pytest.raises(ValueError, match="not a day of month"):
        day_of_month_to_kana(32)


@pytest.mark.parametrize(
    ("days", "expected"),
    [(14, "じゅうよっか"), (34, "さんじゅうよっか"), (60, "ろくじゅうにち")],
)
def test_day_count_to_kana(days: int, expected: str) -> None:
    assert day_count_to_kana(days) == expected
