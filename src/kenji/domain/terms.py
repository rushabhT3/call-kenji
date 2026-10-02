"""Repayment terms Kenji may agree to, and the schedule an accepted offer produces."""

import calendar
import math
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

COUNTER_OFFER_STEP_YEN = 1_000
DEFAULT_FIRST_PAYMENT_AFTER_DAYS = 14
SUGGESTED_PLAN_COUNT = 3


@dataclass(frozen=True, slots=True)
class RepaymentTerms:
    minimum_monthly_yen: int = 5_000
    maximum_installments: int = 6
    first_payment_within_days: int = 45


@dataclass(frozen=True, slots=True)
class Negotiation:
    balance_yen: int
    today: date
    terms: RepaymentTerms = RepaymentTerms()

    def __post_init__(self) -> None:
        if self.balance_yen <= 0:
            raise ValueError(f"balance must be positive, got {self.balance_yen}")


@dataclass(frozen=True, slots=True)
class PaymentProposal:
    monthly_yen: int
    first_payment_on: date

    def __post_init__(self) -> None:
        if self.monthly_yen <= 0:
            raise ValueError(f"monthly amount must be positive, got {self.monthly_yen}")


class TermsViolation(StrEnum):
    BELOW_MINIMUM_MONTHLY = "below_minimum_monthly"
    TOO_MANY_INSTALLMENTS = "too_many_installments"
    FIRST_PAYMENT_IN_PAST = "first_payment_in_past"
    FIRST_PAYMENT_TOO_LATE = "first_payment_too_late"


@dataclass(frozen=True, slots=True)
class Installment:
    due_on: date
    amount_yen: int


@dataclass(frozen=True, slots=True)
class TermsDecision:
    proposal: PaymentProposal
    schedule: tuple[Installment, ...]
    violations: tuple[TermsViolation, ...]

    @property
    def is_accepted(self) -> bool:
        return not self.violations


def check_terms(proposal: PaymentProposal, negotiation: Negotiation) -> TermsDecision:
    schedule = build_schedule(proposal, negotiation.balance_yen)
    return TermsDecision(
        proposal=proposal,
        schedule=schedule,
        violations=_violations(proposal, len(schedule), negotiation),
    )


def _violations(
    proposal: PaymentProposal, installment_count: int, negotiation: Negotiation
) -> tuple[TermsViolation, ...]:
    terms = negotiation.terms
    latest_first_payment = latest_first_payment_date(negotiation)
    paying_in_full = proposal.monthly_yen >= negotiation.balance_yen
    checks = (
        (
            not paying_in_full and proposal.monthly_yen < terms.minimum_monthly_yen,
            TermsViolation.BELOW_MINIMUM_MONTHLY,
        ),
        (installment_count > terms.maximum_installments, TermsViolation.TOO_MANY_INSTALLMENTS),
        (proposal.first_payment_on < negotiation.today, TermsViolation.FIRST_PAYMENT_IN_PAST),
        (proposal.first_payment_on > latest_first_payment, TermsViolation.FIRST_PAYMENT_TOO_LATE),
    )
    return tuple(violation for failed, violation in checks if failed)


def build_schedule(proposal: PaymentProposal, balance_yen: int) -> tuple[Installment, ...]:
    monthly = min(proposal.monthly_yen, balance_yen)
    count = math.ceil(balance_yen / monthly)
    final_amount = balance_yen - monthly * (count - 1)
    amounts = [monthly] * (count - 1) + [final_amount]
    return tuple(
        Installment(due_on=add_months(proposal.first_payment_on, index), amount_yen=amount)
        for index, amount in enumerate(amounts)
    )


def add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year, month = start.year + month_index // 12, month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def smallest_acceptable_monthly(negotiation: Negotiation) -> int:
    terms = negotiation.terms
    floor = max(
        terms.minimum_monthly_yen,
        math.ceil(negotiation.balance_yen / terms.maximum_installments),
    )
    rounded = math.ceil(floor / COUNTER_OFFER_STEP_YEN) * COUNTER_OFFER_STEP_YEN
    return min(rounded, negotiation.balance_yen)


def suggested_plans(negotiation: Negotiation) -> tuple[TermsDecision, ...]:
    """The smallest acceptable monthly amount and the next steps up, each one inside the terms."""
    first_payment_on = default_first_payment_date(negotiation)
    smallest = smallest_acceptable_monthly(negotiation)
    steps = range(smallest, negotiation.balance_yen + 1, COUNTER_OFFER_STEP_YEN)
    decisions = (
        check_terms(PaymentProposal(monthly, first_payment_on), negotiation) for monthly in steps
    )
    accepted = [decision for decision in decisions if decision.is_accepted]
    return tuple(accepted[:SUGGESTED_PLAN_COUNT])


def default_first_payment_date(negotiation: Negotiation) -> date:
    return negotiation.today + timedelta(days=DEFAULT_FIRST_PAYMENT_AFTER_DAYS)


def latest_first_payment_date(negotiation: Negotiation) -> date:
    return negotiation.today + timedelta(days=negotiation.terms.first_payment_within_days)
