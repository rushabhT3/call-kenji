from datetime import UTC, date, datetime

import pytest

from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.guardrails import (
    CallLimits,
    Refusal,
    UsageToday,
    admit_call,
    usage_day,
)

AFTERNOON = datetime(2026, 10, 2, 15, 0, tzinfo=JAPAN_STANDARD_TIME)
LIMITS = CallLimits()
FRESH_DAY = UsageToday(seconds_used=0, calls_by_this_caller=0)


def test_first_call_of_the_day_gets_the_full_five_minutes() -> None:
    admission = admit_call(AFTERNOON, FRESH_DAY, LIMITS)

    assert admission.is_admitted
    assert admission.call_seconds_allowed == 300


def test_call_is_shortened_to_what_is_left_of_the_daily_pool() -> None:
    admission = admit_call(
        AFTERNOON, UsageToday(seconds_used=3_480, calls_by_this_caller=0), LIMITS
    )

    assert admission.call_seconds_allowed == 120


@pytest.mark.parametrize(
    ("at", "usage", "refusal"),
    [
        (
            datetime(2026, 10, 2, 21, 10, tzinfo=JAPAN_STANDARD_TIME),
            FRESH_DAY,
            Refusal.OUTSIDE_CALLING_HOURS,
        ),
        (
            AFTERNOON,
            UsageToday(seconds_used=3_600, calls_by_this_caller=0),
            Refusal.DAILY_MINUTES_USED_UP,
        ),
        (AFTERNOON, UsageToday(seconds_used=0, calls_by_this_caller=3), Refusal.CALLER_DAILY_LIMIT),
    ],
)
def test_calls_are_refused_when_a_guardrail_is_hit(
    at: datetime, usage: UsageToday, refusal: Refusal
) -> None:
    admission = admit_call(at, usage, LIMITS)

    assert not admission.is_admitted
    assert admission.refusal is refusal
    assert admission.call_seconds_allowed == 0


def test_usage_day_rolls_over_at_midnight_japan_time() -> None:
    assert usage_day(datetime(2026, 10, 2, 15, 30, tzinfo=UTC)) == date(2026, 10, 3)


def test_limits_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        CallLimits(max_call_seconds=0)
