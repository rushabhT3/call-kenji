"""Rewrite amounts, dates and counts as kana so speech synthesis reads them correctly."""

import re
from collections.abc import Callable

from kenji.domain.eras import ERA_NAME_PATTERN, ERAS, FIRST_YEAR_MARKER
from kenji.domain.text import ascii_digits

_DIGITS = ("ぜろ", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう")
_THOUSANDS = {1: "せん", 3: "さんぜん", 8: "はっせん"}
_HUNDREDS = {1: "ひゃく", 3: "さんびゃく", 6: "ろっぴゃく", 8: "はっぴゃく"}
_GROUP_UNITS = ("", "まん", "おく")
_GROUP_SIZE = 10_000
MAX_READABLE_NUMBER = _GROUP_SIZE ** len(_GROUP_UNITS) - 1
_MULTIPLIERS = {"": 1, "百": 100, "千": 1_000, "万": 10_000, "億": 100_000_000}

_MONTHS = (
    "いち",
    "に",
    "さん",
    "し",
    "ご",
    "ろく",
    "しち",
    "はち",
    "く",
    "じゅう",
    "じゅういち",
    "じゅうに",
)
MAX_DAY_OF_MONTH = 31
_YOKKA_DIGIT = 4
_DAYS_OF_MONTH = {
    1: "ついたち", 2: "ふつか", 3: "みっか", 4: "よっか", 5: "いつか", 6: "むいか",
    7: "なのか", 8: "ようか", 9: "ここのか", 10: "とおか", 14: "じゅうよっか",
    17: "じゅうしちにち", 19: "じゅうくにち", 20: "はつか", 24: "にじゅうよっか",
    27: "にじゅうしちにち", 29: "にじゅうくにち",
}  # fmt: skip
_SOKUON_ENDINGS = (
    ("いち", "いっ"),
    ("ろく", "ろっ"),
    ("はち", "はっ"),
    ("じゅう", "じゅっ"),
    ("ひゃく", "ひゃっ"),
)
_HOUR_ENDINGS = (("よん", "よ"), ("なな", "しち"), ("きゅう", "く"))
_HALF_DAY = {"午前": "ごぜん", "午後": "ごご"}

_NUMBER = r"\d{1,3}(?:,\d{3})+|\d+"
_COMPOUND_NUMBER = rf"(?:(?:{_NUMBER})[億万千百])+(?:{_NUMBER})?|{_NUMBER}"


def number_to_kana(value: int) -> str:
    if not 0 <= value <= MAX_READABLE_NUMBER:
        raise ValueError(f"cannot read {value} as kana")
    if value == 0:
        return _DIGITS[0]
    groups = (value // _GROUP_SIZE**index % _GROUP_SIZE for index in range(len(_GROUP_UNITS)))
    parts = [
        _group_to_kana(group, is_higher_group=index > 0) + _GROUP_UNITS[index]
        for index, group in enumerate(groups)
        if group
    ]
    return "".join(reversed(parts))


def _group_to_kana(group: int, *, is_higher_group: bool) -> str:
    thousands, hundreds, tens, ones = group // 1000, group // 100 % 10, group // 10 % 10, group % 10
    thousands_kana = "いっせん" if thousands == 1 and is_higher_group else _THOUSANDS.get(thousands)
    return "".join(
        (
            thousands_kana or _place(thousands, "せん"),
            _HUNDREDS.get(hundreds) or _place(hundreds, "ひゃく"),
            "じゅう" if tens == 1 else _place(tens, "じゅう"),
            _DIGITS[ones] if ones else "",
        )
    )


def _place(digit: int, unit: str) -> str:
    return _DIGITS[digit] + unit if digit else ""


def _replace_ending(reading: str, endings: tuple[tuple[str, str], ...]) -> str:
    for ending, replacement in endings:
        if reading.endswith(ending):
            return reading.removesuffix(ending) + replacement
    return reading


def counter_prefix(value: int) -> str:
    return _replace_ending(number_to_kana(value), _SOKUON_ENDINGS)


def hour_to_kana(hour: int) -> str:
    return _replace_ending(number_to_kana(hour), _HOUR_ENDINGS) + "じ"


def year_to_kana(year: int) -> str:
    return _replace_ending(number_to_kana(year), (("よん", "よ"),)) + "ねん"


def month_to_kana(month: int) -> str:
    if not 1 <= month <= len(_MONTHS):
        raise ValueError(f"not a month: {month}")
    return _MONTHS[month - 1] + "がつ"


def day_of_month_to_kana(day: int) -> str:
    if not 1 <= day <= MAX_DAY_OF_MONTH:
        raise ValueError(f"not a day of month: {day}")
    return _DAYS_OF_MONTH.get(day) or number_to_kana(day) + "にち"


def day_count_to_kana(days: int) -> str:
    if days == 1:
        return "いちにち"
    if days <= MAX_DAY_OF_MONTH:
        return day_of_month_to_kana(days)
    if days % 10 == _YOKKA_DIGIT:
        return number_to_kana(days - _YOKKA_DIGIT) + "よっか"
    return number_to_kana(days) + "にち"


def parse_amount(text: str) -> int:
    pieces = re.findall(rf"({_NUMBER})([億万千百]?)", text)
    return sum(int(number.replace(",", "")) * _MULTIPLIERS[unit] for number, unit in pieces)


def yen_to_kana(amount: int) -> str:
    return number_to_kana(amount) + "えん"


def digits_to_kana(digits: str) -> str:
    return "、".join(_DIGITS[int(digit)] for digit in digits)


def _era_date(match: re.Match[str]) -> str:
    era_name, era_year = match.groups()
    year = "がんねん" if era_year == FIRST_YEAR_MARKER else year_to_kana(int(era_year))
    return ERAS[era_name].reading + year


def _time(match: re.Match[str]) -> str:
    half_day, hour = match.groups()
    return _HALF_DAY.get(half_day or "", "") + hour_to_kana(int(hour))


def _month_and_day(match: re.Match[str]) -> str:
    return month_to_kana(int(match[1])) + day_of_month_to_kana(int(match[2]))


def _account_digits(match: re.Match[str]) -> str:
    return "末尾" + match[1] + digits_to_kana(match[2])


type _Rewrite = tuple[re.Pattern[str], Callable[[re.Match[str]], str]]

_NOT_MID_NUMBER = r"(?<![\d,])"

_REWRITES: tuple[_Rewrite, ...] = (
    (re.compile(rf"({ERA_NAME_PATTERN})(元|\d{{1,2}})年"), _era_date),
    (re.compile(rf"{_NOT_MID_NUMBER}(\d{{1,4}})年"), lambda m: year_to_kana(int(m[1]))),
    (re.compile(rf"{_NOT_MID_NUMBER}(\d{{1,2}})月(\d{{1,2}})日"), _month_and_day),
    (re.compile(rf"{_NOT_MID_NUMBER}(\d{{1,2}})月"), lambda m: month_to_kana(int(m[1]))),
    (
        re.compile(rf"{_NOT_MID_NUMBER}(\d+)(?:か|ヶ|ケ|カ|箇)月"),
        lambda m: counter_prefix(int(m[1])) + "かげつ",
    ),
    (
        re.compile(rf"毎月{_NOT_MID_NUMBER}(\d{{1,2}})日"),
        lambda m: "毎月" + day_of_month_to_kana(int(m[1])),
    ),
    (re.compile(rf"{_NOT_MID_NUMBER}(\d+)日後"), lambda m: day_count_to_kana(int(m[1])) + "ご"),
    (re.compile(rf"{_NOT_MID_NUMBER}(\d+)日"), lambda m: day_count_to_kana(int(m[1]))),
    (re.compile(rf"(午前|午後)?{_NOT_MID_NUMBER}(\d{{1,2}})時(?!間)"), _time),
    (
        re.compile(rf"{_NOT_MID_NUMBER}(\d+)回払い"),
        lambda m: counter_prefix(int(m[1])) + "かいばらい",
    ),
    (re.compile(rf"{_NOT_MID_NUMBER}(\d+)回"), lambda m: counter_prefix(int(m[1])) + "かい"),
    (re.compile(rf"¥\s?({_NUMBER})円?"), lambda m: yen_to_kana(parse_amount(m[1]))),
    (
        re.compile(rf"{_NOT_MID_NUMBER}({_COMPOUND_NUMBER})円"),
        lambda m: yen_to_kana(parse_amount(m[1])),
    ),
    (re.compile(r"末尾([はがの]?)(\d+)"), _account_digits),
)


def _safely(rewrite: Callable[[re.Match[str]], str]) -> Callable[[re.Match[str]], str]:
    def apply(match: re.Match[str]) -> str:
        try:
            return rewrite(match)
        except ValueError:
            return match[0]

    return apply


def to_speech_kana(text: str) -> str:
    rewritten = ascii_digits(text)
    for pattern, rewrite in _REWRITES:
        rewritten = pattern.sub(_safely(rewrite), rewritten)
    return rewritten
