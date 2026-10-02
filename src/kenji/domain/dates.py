"""Parse the date formats a Japanese caller or a model may produce."""

import re
from datetime import date

from kenji.domain.eras import ERA_NAME_PATTERN, ERAS, parse_era_year
from kenji.domain.text import ascii_digits

_WESTERN_DATE = re.compile(r"(\d{4})(?:-|/|年)(\d{1,2})(?:-|/|月)(\d{1,2})日?")
_ERA_DATE = re.compile(rf"({ERA_NAME_PATTERN})(元|\d{{1,2}})年(\d{{1,2}})月(\d{{1,2}})日")


def parse_japanese_date(text: str) -> date:
    compact = re.sub(r"\s+", "", ascii_digits(text))
    if western := _WESTERN_DATE.fullmatch(compact):
        year, month, day = (int(part) for part in western.groups())
        return date(year, month, day)
    if era_date := _ERA_DATE.fullmatch(compact):
        era_name, era_year, era_month, era_day = era_date.groups()
        western_year = ERAS[era_name].to_western_year(parse_era_year(era_year))
        return date(western_year, int(era_month), int(era_day))
    raise ValueError(f"unrecognised date: {text!r}")
