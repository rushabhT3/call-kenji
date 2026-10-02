from datetime import UTC, datetime

import pytest

from kenji.domain.calling_hours import JAPAN_STANDARD_TIME, is_within_calling_hours, to_japan_time


def _jst(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 2, hour, minute, tzinfo=JAPAN_STANDARD_TIME)


def test_call_at_21_10_japan_time_is_refused() -> None:
    assert not is_within_calling_hours(_jst(21, 10))


@pytest.mark.parametrize(("hour", "minute"), [(8, 0), (12, 30), (20, 59)])
def test_calls_inside_the_window_are_allowed(hour: int, minute: int) -> None:
    assert is_within_calling_hours(_jst(hour, minute))


@pytest.mark.parametrize(("hour", "minute"), [(7, 59), (21, 0), (23, 30), (0, 0)])
def test_calls_outside_the_window_are_refused(hour: int, minute: int) -> None:
    assert not is_within_calling_hours(_jst(hour, minute))


def test_window_is_evaluated_in_japan_time_whatever_the_input_zone() -> None:
    twelve_ten_utc = datetime(2026, 10, 2, 12, 10, tzinfo=UTC)

    assert to_japan_time(twelve_ten_utc).hour == 21
    assert not is_within_calling_hours(twelve_ten_utc)


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        is_within_calling_hours(datetime(2026, 10, 2, 12, 0))  # noqa: DTZ001
