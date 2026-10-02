"""Stop-contact requests: once recorded, no follow-up contact may be made."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class StopContactRequest:
    caller_ref: str
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class ContactPreferences:
    stopped_callers: frozenset[str] = frozenset()


def record_stop_contact(
    preferences: ContactPreferences, request: StopContactRequest
) -> ContactPreferences:
    return ContactPreferences(stopped_callers=preferences.stopped_callers | {request.caller_ref})


def may_contact(preferences: ContactPreferences, caller_ref: str) -> bool:
    return caller_ref not in preferences.stopped_callers
