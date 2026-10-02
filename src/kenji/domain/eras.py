"""Japanese imperial eras used in spoken and written dates of birth."""

from dataclasses import dataclass

FIRST_YEAR_MARKER = "元"


@dataclass(frozen=True, slots=True)
class Era:
    name: str
    reading: str
    first_western_year: int

    def to_western_year(self, era_year: int) -> int:
        if era_year < 1:
            raise ValueError(f"era year must be positive, got {era_year}")
        return self.first_western_year + era_year - 1


ERAS: dict[str, Era] = {
    era.name: era
    for era in (
        Era(name="昭和", reading="しょうわ", first_western_year=1926),
        Era(name="平成", reading="へいせい", first_western_year=1989),
        Era(name="令和", reading="れいわ", first_western_year=2019),
    )
}

ERA_NAME_PATTERN = "|".join(ERAS)


def parse_era_year(token: str) -> int:
    return 1 if token == FIRST_YEAR_MARKER else int(token)
