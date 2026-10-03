from dataclasses import astuple, replace
from datetime import date, datetime

import pytest

from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.compliance import CallFacts, CheckStatus, assess_compliance
from kenji.domain.contact import (
    ContactPreferences,
    StopContactRequest,
    may_contact,
    record_stop_contact,
)
from kenji.domain.identity import IdentityStatus
from kenji.domain.outcome import CallOutcome, PaymentPromise, follow_up_sms_allowed
from kenji.domain.terms import Negotiation, PaymentProposal, check_terms

AFTERNOON = datetime(2026, 10, 2, 15, 0, tzinfo=JAPAN_STANDARD_TIME)
LATE_NIGHT = datetime(2026, 10, 2, 21, 10, tzinfo=JAPAN_STANDARD_TIME)
NEGOTIATION = Negotiation(balance_yen=35_000, today=date(2026, 10, 2))


FRESH_CALL = CallFacts(
    started_at=AFTERNOON,
    is_inbound=True,
    identity_status=IdentityStatus.UNVERIFIED,
    latest_offer_accepted=None,
    ai_disclosed=False,
    recording_notice_given=False,
)


def test_fresh_call_in_hours_passes_hours_and_waits_on_the_rest() -> None:
    report = assess_compliance(FRESH_CALL)

    assert report.calling_hours is CheckStatus.PASSED
    assert {
        report.identity_gate,
        report.offer_within_terms,
        report.ai_disclosure,
        report.recording_notice,
    } == {CheckStatus.PENDING}


def test_completed_call_passes_every_check() -> None:
    report = assess_compliance(
        replace(
            FRESH_CALL,
            identity_status=IdentityStatus.VERIFIED,
            latest_offer_accepted=True,
            ai_disclosed=True,
            recording_notice_given=True,
        )
    )

    assert set(astuple(report)) == {CheckStatus.PASSED}


def test_a_call_the_caller_made_passes_calling_hours_at_any_hour() -> None:
    report = assess_compliance(replace(FRESH_CALL, started_at=LATE_NIGHT))

    assert report.calling_hours is CheckStatus.PASSED


@pytest.mark.parametrize(
    ("started_at", "status"), [(AFTERNOON, CheckStatus.PASSED), (LATE_NIGHT, CheckStatus.BLOCKED)]
)
def test_ringing_a_debtor_is_only_allowed_inside_calling_hours(
    started_at: datetime, status: CheckStatus
) -> None:
    report = assess_compliance(replace(FRESH_CALL, started_at=started_at, is_inbound=False))

    assert report.calling_hours is status


def test_guardrails_that_fire_are_shown_as_blocked() -> None:
    report = assess_compliance(
        replace(
            FRESH_CALL,
            started_at=LATE_NIGHT,
            is_inbound=False,
            identity_status=IdentityStatus.LOCKED_OUT,
            latest_offer_accepted=False,
        )
    )

    assert report.calling_hours is CheckStatus.BLOCKED
    assert report.identity_gate is CheckStatus.BLOCKED
    assert report.offer_within_terms is CheckStatus.BLOCKED


def test_stop_contact_is_recorded_per_caller() -> None:
    preferences = record_stop_contact(
        ContactPreferences(), StopContactRequest(caller_ref="caller-1", requested_at=AFTERNOON)
    )

    assert not may_contact(preferences, "caller-1")
    assert may_contact(preferences, "caller-2")


@pytest.mark.parametrize(
    ("outcome", "may_contact_caller", "allowed"),
    [
        (CallOutcome.PROMISE_TO_PAY, True, True),
        (CallOutcome.HUMAN_HANDOFF, True, True),
        (CallOutcome.PROMISE_TO_PAY, False, False),
        (CallOutcome.CALLBACK_REQUESTED, True, False),
        (CallOutcome.STOP_CONTACT, True, False),
    ],
)
def test_follow_up_sms_only_after_promise_or_handoff_to_a_contactable_caller(
    outcome: CallOutcome, may_contact_caller: bool, allowed: bool
) -> None:
    assert follow_up_sms_allowed(outcome, may_contact_caller) is allowed


def test_promise_outside_terms_cannot_be_recorded() -> None:
    rejected = check_terms(PaymentProposal(3_000, date(2026, 10, 27)), NEGOTIATION)

    with pytest.raises(ValueError, match="outside terms"):
        PaymentPromise(decision=rejected, promised_at=AFTERNOON)


def test_promise_inside_terms_is_recorded() -> None:
    accepted = check_terms(PaymentProposal(6_000, date(2026, 10, 27)), NEGOTIATION)

    assert PaymentPromise(decision=accepted, promised_at=AFTERNOON).decision.is_accepted
