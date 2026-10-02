"""Read the few things a caller says that Kenji can act on without a language model.

Every reader is deliberately narrow: it answers only when the words leave no doubt and returns
None or False otherwise, which hands the turn to the model. A wrong answer here would verify the
wrong caller or record a promise nobody made, while None only costs a little time.
"""

import re
from datetime import date

from kenji.domain.dates import parse_japanese_date
from kenji.domain.eras import ERA_NAME_PATTERN
from kenji.domain.identity import DebtorIdentity
from kenji.domain.text import ascii_digits, spoken_characters, to_hiragana
from kenji.domain.turn import is_composed_of

# A plain yes is matched against whole phrases, never a deny-list: any word outside these, even a
# polite one such as でも or なら, may attach a condition, so the turn goes to the model instead.
AGREEMENT_PHRASES = (
    "はい",
    "ええ",
    "うん",
    "はいはい",
    "それで",
    "その内容で",
    "そのないようで",
    "お願いします",
    "おねがいします",
    "よろしくお願いします",
    "大丈夫です",
    "だいじょうぶです",
    "間違いありません",
    "まちがいありません",
    "間違いないです",
    "それで結構です",
    "問題ありません",
    "了解です",
    "了解しました",
    "承知しました",
    "わかりました",
    "分かりました",
)
MAX_AGREEMENT_CHARACTERS = 20
# Words that put the speaker beside the account holder rather than in their place.
SOMEONE_ELSE = (
    "妻",
    "夫",
    "主人",
    "家族",
    "母",
    "父",
    "娘",
    "息子",
    "兄",
    "弟",
    "姉",
    "妹",
    "代理",
    "本人ではな",
    "本人じゃな",
)
# Totals and lump sums are a different offer from a monthly amount, so they go to the model.
TOTAL_WORDS = ("合計", "全額", "一括", "全部で", "総額")
# Timing the rules cannot turn into a date. An offer that names one goes to the model.
RELATIVE_TIMING = (
    "来週",
    "再来週",
    "来月",
    "月末",
    "週末",
    "明日",
    "明後日",
    "あさって",
    "給料日",
    "日後",
    "週間後",
    "か月後",
    "ヶ月後",
)
_HONORIFICS = ("", "さん", "さま", "様")
_QUESTION_MARKS = ("?", "？")
_ELONGATION_MARKS = str.maketrans("", "", "ー〜～")
_KANJI_DIGITS = {
    "〇": 0,
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_KANJI_TEN = "十"
_DIGIT_BY_DIGIT_LENGTHS = (1, 4)
_KANJI_NUMBER = re.compile(rf"([{''.join(_KANJI_DIGITS)}{_KANJI_TEN}]+)(?=[年月日千万円])")
_ERA_DATE = re.compile(rf"(?:{ERA_NAME_PATTERN})(?:元|\d{{1,2}})年\d{{1,2}}月\d{{1,2}}日")
_WESTERN_DATE = re.compile(
    r"(?<!\d)\d{4}(?:年\d{1,2}月\d{1,2}日|/\d{1,2}/\d{1,2}|-\d{1,2}-\d{1,2})(?!\d)"
)
_MONTH_DAY = re.compile(r"(?<!\d)(\d{1,2})月(\d{1,2})日")
_YEN = re.compile(r"(?<![\d,])(?:(\d+)万)?(?:(\d+)千)?(\d{1,3}(?:,\d{3})+|\d+)?円")
_THOUSAND = 1_000
_TEN_THOUSAND = 10_000
_TEN = 10

type DateSpan = tuple[int, int, date]


def find_birth_date(text: str) -> date | None:
    """The one date of birth in what the caller said, or None if there is not exactly one."""
    compact = _compact(text)
    if compact is None:
        return None
    full_dates = _full_dates(compact)
    if not full_dates or _stray_month_days(compact, full_dates):
        return None
    return _only({found for _, _, found in full_dates})


def find_month_day(text: str, today: date) -> date | None:
    """The one payment date the caller named, taking a month and day as the next one to come."""
    compact = _compact(text)
    if compact is None:
        return None
    full_dates = _full_dates(compact)
    if full_dates is None:
        return None
    month_days = _stray_month_days(compact, full_dates)
    if full_dates and month_days:
        return None
    if full_dates:
        return _only({found for _, _, found in full_dates})
    pair = _only({(int(month), int(day)) for month, day in month_days})
    return None if pair is None else _next_occurrence(pair, today)


def find_monthly_yen(text: str) -> int | None:
    """The one monthly amount the caller offered, in yen, or None if anything is unclear."""
    compact = _compact(text)
    if compact is None or any(word in compact for word in TOTAL_WORDS):
        return None
    amounts = {_yen_amount(match) for match in _YEN.finditer(compact) if match.group(0) != "円"}
    if None in amounts:
        return None
    amount = _only(amounts)
    return amount if amount else None


def mentions_relative_timing(text: str) -> bool:
    return any(word in text for word in RELATIVE_TIMING)


def names_the_debtor(text: str, identity: DebtorIdentity) -> bool:
    """Whether the caller gave the account holder's full name as their own."""
    if any(word in text for word in SOMEONE_ELSE):
        return False
    spoken = spoken_characters(to_hiragana(text)).lower()
    names = identity.accepted_names()
    if any(name + honorific + "の" in spoken for name in names for honorific in _HONORIFICS):
        return False
    return any(name in spoken for name in names)


def is_plain_agreement(text: str) -> bool:
    """Whether the caller said an unconditional yes and nothing else."""
    if any(mark in text for mark in _QUESTION_MARKS):
        return False
    spoken = _agreement_form(text)
    if not spoken or len(spoken) > MAX_AGREEMENT_CHARACTERS:
        return False
    return is_composed_of(
        spoken, frozenset(_agreement_form(phrase) for phrase in AGREEMENT_PHRASES)
    )


def _read_kanji_number(numeral: str) -> int | None:
    """A kanji number up to 99 (十四, 二十, 七) or a year digit by digit (一九九〇); else None.

    Two or three digits read one by one (二二) are not how a number is said, so they are refused.
    """
    if numeral.count(_KANJI_TEN) > 1:
        return None
    if _KANJI_TEN not in numeral:
        if len(numeral) not in _DIGIT_BY_DIGIT_LENGTHS:
            return None
        return int("".join(str(_KANJI_DIGITS[char]) for char in numeral))
    tens, units = numeral.split(_KANJI_TEN)
    tens_value = 1 if not tens else _single_digit(tens)
    units_value = 0 if not units else _single_digit(units)
    if tens_value is None or units_value is None:
        return None
    return tens_value * _TEN + units_value


def _single_digit(numeral: str) -> int | None:
    value = _KANJI_DIGITS.get(numeral) if len(numeral) == 1 else None
    return None if value is None or value == 0 else value


def _compact(text: str) -> str | None:
    """Half-width digits, no spaces, kanji numbers read; None if a kanji number is unreadable."""
    compact = re.sub(r"\s+", "", ascii_digits(text))
    unreadable = False

    def to_digits(match: re.Match[str]) -> str:
        nonlocal unreadable
        value = _read_kanji_number(match.group(1))
        unreadable = unreadable or value is None
        return str(value)

    converted = _KANJI_NUMBER.sub(to_digits, compact)
    return None if unreadable else converted


def _full_dates(compact: str) -> list[DateSpan] | None:
    """Dates with a year, era or western; None if any of them is not a real date."""
    spans: list[DateSpan] = []
    for pattern in (_ERA_DATE, _WESTERN_DATE):
        for match in pattern.finditer(compact):
            try:
                spans.append((match.start(), match.end(), parse_japanese_date(match.group(0))))
            except ValueError:
                return None
    return spans


def _stray_month_days(compact: str, full_dates: list[DateSpan] | None) -> list[tuple[str, str]]:
    """Month-and-day mentions that are not part of a dated year, such as a correction."""
    covered = full_dates or []
    return [
        (match.group(1), match.group(2))
        for match in _MONTH_DAY.finditer(compact)
        if not any(start <= match.start() < end for start, end, _ in covered)
    ]


def _next_occurrence(month_day: tuple[int, int], today: date) -> date | None:
    month, day = month_day
    try:
        this_year = date(today.year, month, day)
        return this_year if this_year >= today else date(today.year + 1, month, day)
    except ValueError:
        return None


def _yen_amount(match: re.Match[str]) -> int | None:
    man, sen, rest = match.groups()
    rest_value = int(rest.replace(",", "")) if rest else 0
    if sen:
        sen_value = int(sen)
        if sen_value >= _TEN or rest_value >= _THOUSAND:
            return None
        rest_value += sen_value * _THOUSAND
    if man:
        if rest_value >= _TEN_THOUSAND:
            return None
        rest_value += int(man) * _TEN_THOUSAND
    return rest_value


def _agreement_form(text: str) -> str:
    return spoken_characters(to_hiragana(text).translate(_ELONGATION_MARKS))


def _only[T](values: set[T]) -> T | None:
    return next(iter(values)) if len(values) == 1 else None
