"""What each tool the talker can call does, independent of the conversation framework."""

from dataclasses import dataclass
from enum import StrEnum

from kenji.app.ports import ContactStore
from kenji.app.session import CallSession, NoConfirmedPlanError
from kenji.domain.account import AccountLocked
from kenji.domain.audit import JsonValue
from kenji.domain.dates import parse_japanese_date
from kenji.domain.identity import IdentityClaim, IdentityStatus
from kenji.domain.outcome import CallOutcome
from kenji.domain.terms import (
    PaymentProposal,
    TermsDecision,
    default_first_payment_date,
    latest_first_payment_date,
    smallest_acceptable_monthly,
)


class NodeName(StrEnum):
    GREETING = "greeting"
    VERIFY_IDENTITY = "verify_identity"
    STATE_BALANCE = "state_balance"
    LISTEN = "listen"
    NEGOTIATE = "negotiate"
    READ_BACK = "read_back"
    CLOSE = "close"
    THIRD_PARTY = "third_party"
    HUMAN_HANDOFF = "human_handoff"
    STOP_CONTACT = "stop_contact"
    IDENTITY_LOCKED = "identity_locked"


@dataclass(frozen=True, slots=True)
class ToolOutcome:
    result: dict[str, JsonValue]
    next_node: NodeName | None = None


def _error(message: str) -> ToolOutcome:
    return ToolOutcome(result={"error": message})


class CallTools:
    def __init__(self, session: CallSession, contacts: ContactStore) -> None:
        self._session = session
        self._contacts = contacts

    def verify_identity(self, name_kana: str, date_of_birth: str) -> ToolOutcome:
        try:
            claim = IdentityClaim(
                spoken_name=name_kana, date_of_birth=parse_japanese_date(date_of_birth)
            )
        except ValueError:
            return _error("date_of_birth must be a real date such as 1990-07-14")
        gate = self._session.verify_identity(claim)
        if gate.status is IdentityStatus.VERIFIED:
            return ToolOutcome(result={"status": "verified"}, next_node=NodeName.STATE_BALANCE)
        if gate.status is IdentityStatus.LOCKED_OUT:
            self._session.conclude(CallOutcome.IDENTITY_NOT_VERIFIED)
            return ToolOutcome(result={"status": "locked_out"}, next_node=NodeName.IDENTITY_LOCKED)
        attempts_left = gate.max_attempts - gate.failed_attempts
        next_node = (
            None if self._session.node == NodeName.VERIFY_IDENTITY else NodeName.VERIFY_IDENTITY
        )
        return ToolOutcome(
            result={"status": "mismatch", "attempts_left": attempts_left}, next_node=next_node
        )

    def get_account_summary(self) -> ToolOutcome:
        summary = self._session.account_summary()
        if isinstance(summary, AccountLocked):
            return ToolOutcome(result={"status": summary.status})
        return ToolOutcome(
            result={
                "account_suffix": summary.account_suffix,
                "balance_yen": summary.balance_yen,
                "overdue_since": summary.overdue_since.isoformat(),
            }
        )

    def check_terms(self, monthly_yen: object, first_payment_date: str | None) -> ToolOutcome:
        proposal = self._proposal(monthly_yen, first_payment_date)
        if isinstance(proposal, ToolOutcome):
            return proposal
        decision = self._session.check_terms(proposal)
        next_node = None if self._session.node == NodeName.NEGOTIATE else NodeName.NEGOTIATE
        return ToolOutcome(result=self._terms_result(decision), next_node=next_node)

    def confirm_plan(self, monthly_yen: object, first_payment_date: str | None) -> ToolOutcome:
        proposal = self._proposal(monthly_yen, first_payment_date)
        if isinstance(proposal, ToolOutcome):
            return proposal
        decision = self._session.confirm_plan(proposal)
        next_node = NodeName.READ_BACK if decision.is_accepted else None
        return ToolOutcome(result=self._terms_result(decision), next_node=next_node)

    def record_promise(self) -> ToolOutcome:
        try:
            self._session.record_promise()
        except NoConfirmedPlanError:
            return _error("confirm an in-terms plan with confirm_plan before recording a promise")
        self._session.conclude(CallOutcome.PROMISE_TO_PAY)
        return ToolOutcome(result={"status": "recorded"}, next_node=NodeName.CLOSE)

    def request_human(self, reason: str, summary: str) -> ToolOutcome:
        self._session.request_handoff(reason=reason, summary=summary)
        self._session.conclude(CallOutcome.HUMAN_HANDOFF)
        return ToolOutcome(result={"status": "handoff_recorded"}, next_node=NodeName.HUMAN_HANDOFF)

    def record_stop_contact(self) -> ToolOutcome:
        self._contacts.record(self._session.stop_contact_request())
        self._session.conclude(CallOutcome.STOP_CONTACT)
        return ToolOutcome(
            result={"status": "stop_contact_recorded"}, next_node=NodeName.STOP_CONTACT
        )

    def third_party_answered(self) -> ToolOutcome:
        self._session.conclude(CallOutcome.CALLBACK_REQUESTED)
        return ToolOutcome(result={"status": "callback_requested"}, next_node=NodeName.THIRD_PARTY)

    def end_without_agreement(self, reason: str) -> ToolOutcome:
        self._session.record("ended_without_agreement", {"reason": reason})
        self._session.conclude(CallOutcome.NO_AGREEMENT)
        return ToolOutcome(result={"status": "closing"}, next_node=NodeName.CLOSE)

    def _proposal(
        self, monthly_yen: object, first_payment_date: str | None
    ) -> PaymentProposal | ToolOutcome:
        negotiation = self._session.negotiation
        try:
            first_payment_on = (
                parse_japanese_date(first_payment_date)
                if first_payment_date
                else default_first_payment_date(negotiation)
            )
            amount = int(str(monthly_yen).replace(",", "").replace("円", ""))
            return PaymentProposal(monthly_yen=amount, first_payment_on=first_payment_on)
        except (TypeError, ValueError):
            return _error("monthly_yen must be a positive integer and the date YYYY-MM-DD")

    def _terms_result(self, decision: TermsDecision) -> dict[str, JsonValue]:
        negotiation = self._session.negotiation
        schedule = decision.schedule
        return {
            "accepted": decision.is_accepted,
            "violations": [violation.value for violation in decision.violations],
            "monthly_yen": schedule[0].amount_yen,
            "installments": len(schedule),
            "final_yen": schedule[-1].amount_yen,
            "first_payment_date": schedule[0].due_on.isoformat(),
            "smallest_acceptable_monthly_yen": smallest_acceptable_monthly(negotiation),
            "latest_first_payment_date": latest_first_payment_date(negotiation).isoformat(),
        }
