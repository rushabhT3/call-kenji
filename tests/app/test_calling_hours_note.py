"""The X-ray's calling-hours check teaches the rule at the hour the caller rang."""

from datetime import UTC, datetime

from kenji.app.session import calling_hours_note
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME

NIGHT_NOTE = "03:12 in Tokyo. Kenji would never ring a debtor now; you rang him, so he answers."


def _tokyo(hour: int, minute: int) -> datetime:
    return datetime(2026, 10, 3, hour, minute, tzinfo=JAPAN_STANDARD_TIME)


def test_a_call_by_day_falls_inside_the_window() -> None:
    assert calling_hours_note(_tokyo(15, 4)) == "15:04 in Tokyo, inside 08:00–21:00."


def test_a_call_at_night_is_answered_though_kenji_would_never_ring_then() -> None:
    assert calling_hours_note(_tokyo(3, 12)) == NIGHT_NOTE


def test_the_hour_is_read_in_tokyo_whatever_zone_the_server_keeps() -> None:
    assert calling_hours_note(datetime(2026, 10, 2, 18, 12, tzinfo=UTC)) == NIGHT_NOTE
