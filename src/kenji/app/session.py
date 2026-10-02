"""One call's state, changed only through the domain rules and audited as it changes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from kenji.app.events import (
    CallEnded,
    ComplianceUpdated,
    FlowNodeEntered,
    HandoffRecorded,
)
from kenji.app.ports import AuditLog, Clock, EventSink
from kenji.domain.account import Account, AccountLocked, AccountSummary, summarize_account
from kenji.domain.audit import AuditEntry, JsonValue
from kenji.domain.compliance import CallFacts, ComplianceReport, assess_compliance
from kenji.domain.contact import StopContactRequest
from kenji.domain.identity import IdentityClaim, IdentityGate, IdentityStatus, attempt_verification
from kenji.domain.outcome import CallOutcome, HandoffRecord, PaymentPromise
from kenji.domain.terms import Negotiation, PaymentProposal, TermsDecision, check_terms


class NoConfirmedPlanError(Exception):
    """record_promise was called before an in-terms plan was confirmed."""


@dataclass(frozen=True, slots=True)
class CallContext:
    call_id: str
    transport: Literal["phone", "browser"]
    caller_ref: str
    started_at: datetime
    account: Account
    negotiation: Negotiation


class CallSession:
    def __init__(
        self, context: CallContext, sink: EventSink, audit: AuditLog, clock: Clock
    ) -> None:
        self.context = context
        self._sink = sink
        self._audit = audit
        self._clock = clock
        self._gate = IdentityGate()
        self._latest_offer_accepted: bool | None = None
        self._confirmed_plan: TermsDecision | None = None
        self._promise: PaymentPromise | None = None
        self._is_disclosure_given = False
        self._node = ""
        self._outcome: CallOutcome | None = None
        self._compliance: ComplianceReport | None = None

    @property
    def node(self) -> str:
        return self._node

    @property
    def negotiation(self) -> Negotiation:
        return self.context.negotiation

    def stop_contact_request(self) -> StopContactRequest:
        request = StopContactRequest(
            caller_ref=self.context.caller_ref, requested_at=self._clock.now()
        )
        self._audit_entry("stop_contact_recorded", {"caller_ref": request.caller_ref})
        return request

    @property
    def identity_status(self) -> IdentityStatus:
        return self._gate.status

    @property
    def confirmed_plan(self) -> TermsDecision | None:
        return self._confirmed_plan

    @property
    def promise(self) -> PaymentPromise | None:
        return self._promise

    @property
    def outcome(self) -> CallOutcome | None:
        return self._outcome

    def enter_node(self, node: str) -> None:
        self._node = node
        self._sink.publish(FlowNodeEntered(node=node))
        self._audit_entry("node_entered", {"node": node})

    def mark_disclosure_given(self) -> None:
        self._is_disclosure_given = True
        self._audit_entry("disclosure_given", {"ai": True, "demo": True, "transcript_notice": True})
        self.publish_compliance()

    def verify_identity(self, claim: IdentityClaim) -> IdentityGate:
        self._gate = attempt_verification(self._gate, claim, self.context.account.debtor)
        self._audit_entry(
            "identity_checked",
            {"status": self._gate.status.value, "failed_attempts": self._gate.failed_attempts},
        )
        self.publish_compliance()
        return self._gate

    def account_summary(self) -> AccountSummary | AccountLocked:
        summary = summarize_account(self.context.account, self._gate)
        self._audit_entry(
            "account_summary_requested", {"locked": isinstance(summary, AccountLocked)}
        )
        return summary

    def check_terms(self, proposal: PaymentProposal) -> TermsDecision:
        decision = check_terms(proposal, self.context.negotiation)
        self._latest_offer_accepted = decision.is_accepted
        self._audit_entry("terms_checked", _decision_payload(decision))
        self.publish_compliance()
        return decision

    def confirm_plan(self, proposal: PaymentProposal) -> TermsDecision:
        decision = self.check_terms(proposal)
        if decision.is_accepted:
            self._confirmed_plan = decision
        return decision

    def record_promise(self) -> PaymentPromise:
        if self._confirmed_plan is None:
            raise NoConfirmedPlanError("no in-terms plan has been confirmed")
        self._promise = PaymentPromise(decision=self._confirmed_plan, promised_at=self._clock.now())
        self._audit_entry("promise_recorded", _decision_payload(self._confirmed_plan))
        return self._promise

    def request_handoff(self, reason: str, summary: str) -> HandoffRecord:
        record = HandoffRecord(
            reason=reason,
            summary=summary,
            identity_status=self._gate.status,
            requested_at=self._clock.now(),
        )
        self._audit_entry("handoff_requested", {"reason": reason, "summary": summary})
        self._sink.publish(
            HandoffRecorded(
                reason=reason,
                summary=summary,
                identity_status=record.identity_status,
                node=self._node,
                requested_at=record.requested_at,
            )
        )
        return record

    def conclude(self, outcome: CallOutcome) -> None:
        if self._outcome is None:
            self._outcome = outcome
            self._audit_entry("outcome_decided", {"outcome": outcome.value})

    def finish(self) -> CallOutcome:
        outcome = self._outcome or (
            CallOutcome.NO_AGREEMENT
            if self._gate.is_verified
            else CallOutcome.IDENTITY_NOT_VERIFIED
        )
        self._audit_entry("call_ended", {"outcome": outcome.value})
        self._sink.publish(CallEnded(outcome=outcome, ended_at=self._clock.now()))
        return outcome

    def record(self, kind: str, payload: dict[str, JsonValue]) -> None:
        self._audit_entry(kind, payload)

    def _audit_entry(self, kind: str, payload: dict[str, JsonValue]) -> None:
        self._audit.append(
            AuditEntry(kind=kind, recorded_at=self._clock.now().isoformat(), payload=payload)
        )

    def publish_compliance(self) -> None:
        report = assess_compliance(
            CallFacts(
                started_at=self.context.started_at,
                identity_status=self._gate.status,
                latest_offer_accepted=self._latest_offer_accepted,
                ai_disclosed=self._is_disclosure_given,
                recording_notice_given=self._is_disclosure_given,
            )
        )
        if report != self._compliance:
            self._compliance = report
            self._sink.publish(_compliance_event(report))


def _compliance_event(report: ComplianceReport) -> ComplianceUpdated:
    return ComplianceUpdated(
        calling_hours=report.calling_hours,
        identity_gate=report.identity_gate,
        offer_within_terms=report.offer_within_terms,
        ai_disclosure=report.ai_disclosure,
        recording_notice=report.recording_notice,
    )


def _decision_payload(decision: TermsDecision) -> dict[str, JsonValue]:
    return {
        "monthly_yen": decision.proposal.monthly_yen,
        "first_payment_on": decision.proposal.first_payment_on.isoformat(),
        "installments": len(decision.schedule),
        "accepted": decision.is_accepted,
        "violations": [violation.value for violation in decision.violations],
    }
