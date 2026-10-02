"""How a call ended, and the records an ending leaves behind."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from kenji.domain.identity import IdentityStatus
from kenji.domain.terms import TermsDecision


class CallOutcome(StrEnum):
    PROMISE_TO_PAY = "promise_to_pay"
    HUMAN_HANDOFF = "human_handoff"
    STOP_CONTACT = "stop_contact"
    CALLBACK_REQUESTED = "callback_requested"
    IDENTITY_NOT_VERIFIED = "identity_not_verified"
    OUTSIDE_CALLING_HOURS = "outside_calling_hours"
    DAILY_LIMIT_REACHED = "daily_limit_reached"
    NO_AGREEMENT = "no_agreement"


_OUTCOMES_WITH_FOLLOW_UP_SMS = frozenset({CallOutcome.PROMISE_TO_PAY, CallOutcome.HUMAN_HANDOFF})


@dataclass(frozen=True, slots=True)
class PaymentPromise:
    decision: TermsDecision
    promised_at: datetime

    def __post_init__(self) -> None:
        if not self.decision.is_accepted:
            raise ValueError(f"cannot promise an offer outside terms: {self.decision.violations}")


@dataclass(frozen=True, slots=True)
class HandoffRecord:
    reason: str
    summary: str
    identity_status: IdentityStatus
    requested_at: datetime


def follow_up_sms_allowed(outcome: CallOutcome, may_contact_caller: bool) -> bool:
    return may_contact_caller and outcome in _OUTCOMES_WITH_FOLLOW_UP_SMS
