"""Budget guardrails: which calls may start, and how long each may run.

Every call is one the caller made, so it is answered at any hour: the calling-hours window limits
a lender ringing a debtor, not a debtor ringing Kenji.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from kenji.domain.calling_hours import to_japan_time


class Refusal(StrEnum):
    DAILY_MINUTES_USED_UP = "daily_minutes_used_up"
    CALLER_DAILY_LIMIT = "caller_daily_limit"


@dataclass(frozen=True, slots=True)
class CallLimits:
    max_call_seconds: int = 300
    daily_seconds: int = 3_600
    calls_per_caller_per_day: int = 10

    def __post_init__(self) -> None:
        if min(self.max_call_seconds, self.daily_seconds, self.calls_per_caller_per_day) <= 0:
            raise ValueError(f"call limits must be positive: {self}")


@dataclass(frozen=True, slots=True)
class UsageToday:
    seconds_used: int
    calls_by_this_caller: int


@dataclass(frozen=True, slots=True)
class Admission:
    refusal: Refusal | None
    call_seconds_allowed: int

    @property
    def is_admitted(self) -> bool:
        return self.refusal is None


def usage_day(moment: datetime) -> date:
    return to_japan_time(moment).date()


def admit_call(usage: UsageToday, limits: CallLimits) -> Admission:
    refusal = _refusal(usage, limits)
    if refusal is not None:
        return Admission(refusal=refusal, call_seconds_allowed=0)
    seconds_left_today = limits.daily_seconds - usage.seconds_used
    return Admission(
        refusal=None, call_seconds_allowed=min(limits.max_call_seconds, seconds_left_today)
    )


def _refusal(usage: UsageToday, limits: CallLimits) -> Refusal | None:
    if usage.seconds_used >= limits.daily_seconds:
        return Refusal.DAILY_MINUTES_USED_UP
    if usage.calls_by_this_caller >= limits.calls_per_caller_per_day:
        return Refusal.CALLER_DAILY_LIMIT
    return None
