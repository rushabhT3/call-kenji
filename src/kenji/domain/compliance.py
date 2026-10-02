"""The compliance view of a call: which safeguards have held so far."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from kenji.domain.calling_hours import is_within_calling_hours
from kenji.domain.identity import IdentityStatus


class CheckStatus(StrEnum):
    PASSED = "pass"
    BLOCKED = "blocked"
    PENDING = "pending"


@dataclass(frozen=True, slots=True)
class CallFacts:
    started_at: datetime
    identity_status: IdentityStatus
    latest_offer_accepted: bool | None
    ai_disclosed: bool
    recording_notice_given: bool


@dataclass(frozen=True, slots=True)
class ComplianceReport:
    calling_hours: CheckStatus
    identity_gate: CheckStatus
    offer_within_terms: CheckStatus
    ai_disclosure: CheckStatus
    recording_notice: CheckStatus


_IDENTITY_CHECK = {
    IdentityStatus.VERIFIED: CheckStatus.PASSED,
    IdentityStatus.LOCKED: CheckStatus.BLOCKED,
    IdentityStatus.UNVERIFIED: CheckStatus.PENDING,
}

_OFFER_CHECK = {True: CheckStatus.PASSED, False: CheckStatus.BLOCKED, None: CheckStatus.PENDING}


def _given(is_given: bool) -> CheckStatus:
    return CheckStatus.PASSED if is_given else CheckStatus.PENDING


def assess_compliance(facts: CallFacts) -> ComplianceReport:
    return ComplianceReport(
        calling_hours=(
            CheckStatus.PASSED if is_within_calling_hours(facts.started_at) else CheckStatus.BLOCKED
        ),
        identity_gate=_IDENTITY_CHECK[facts.identity_status],
        offer_within_terms=_OFFER_CHECK[facts.latest_offer_accepted],
        ai_disclosure=_given(facts.ai_disclosed),
        recording_notice=_given(facts.recording_notice_given),
    )
