from datetime import date

import pytest

from kenji.domain.terms import (
    Installment,
    Negotiation,
    PaymentProposal,
    TermsViolation,
    add_months,
    check_terms,
    default_first_payment_date,
    latest_first_payment_date,
    smallest_acceptable_monthly,
    suggested_plans,
)

TODAY = date(2026, 10, 2)
NEGOTIATION = Negotiation(balance_yen=35_000, today=TODAY)
NEXT_MONTH = date(2026, 10, 27)


def test_3000_yen_a_month_is_rejected() -> None:
    decision = check_terms(PaymentProposal(3_000, NEXT_MONTH), NEGOTIATION)

    assert not decision.is_accepted
    assert decision.violations == (
        TermsViolation.BELOW_MINIMUM_MONTHLY,
        TermsViolation.TOO_MANY_INSTALLMENTS,
    )


def test_5000_yen_a_month_needs_seven_payments_and_is_rejected() -> None:
    decision = check_terms(PaymentProposal(5_000, NEXT_MONTH), NEGOTIATION)

    assert decision.violations == (TermsViolation.TOO_MANY_INSTALLMENTS,)


def test_6000_yen_a_month_is_accepted_with_a_smaller_final_payment() -> None:
    decision = check_terms(PaymentProposal(6_000, NEXT_MONTH), NEGOTIATION)

    assert decision.is_accepted
    assert [installment.amount_yen for installment in decision.schedule] == [6_000] * 5 + [5_000]
    assert decision.schedule[-1].due_on == date(2027, 3, 27)


def test_paying_more_than_the_balance_is_a_single_full_payment() -> None:
    decision = check_terms(PaymentProposal(40_000, NEXT_MONTH), NEGOTIATION)

    assert decision.is_accepted
    assert decision.schedule == (Installment(due_on=NEXT_MONTH, amount_yen=35_000),)


def test_full_payment_below_monthly_minimum_is_accepted() -> None:
    small_debt = Negotiation(balance_yen=3_000, today=TODAY)

    assert check_terms(PaymentProposal(3_000, NEXT_MONTH), small_debt).is_accepted


@pytest.mark.parametrize(
    ("first_payment_on", "violation"),
    [
        (date(2026, 10, 1), TermsViolation.FIRST_PAYMENT_IN_PAST),
        (date(2026, 11, 17), TermsViolation.FIRST_PAYMENT_TOO_LATE),
    ],
)
def test_first_payment_must_fall_within_45_days(
    first_payment_on: date, violation: TermsViolation
) -> None:
    decision = check_terms(PaymentProposal(6_000, first_payment_on), NEGOTIATION)

    assert decision.violations == (violation,)


def test_first_payment_on_day_45_is_accepted() -> None:
    assert check_terms(PaymentProposal(6_000, date(2026, 11, 16)), NEGOTIATION).is_accepted


def test_smallest_acceptable_monthly_is_rounded_up_to_a_speakable_amount() -> None:
    assert smallest_acceptable_monthly(NEGOTIATION) == 6_000


def test_smallest_acceptable_monthly_never_exceeds_the_balance() -> None:
    assert smallest_acceptable_monthly(Negotiation(balance_yen=4_500, today=TODAY)) == 4_500


def test_add_months_clamps_to_month_end() -> None:
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 11, 30), 3) == date(2027, 2, 28)


def test_non_positive_amounts_are_rejected() -> None:
    with pytest.raises(ValueError, match="monthly amount"):
        PaymentProposal(0, NEXT_MONTH)
    with pytest.raises(ValueError, match="balance"):
        Negotiation(balance_yen=0, today=TODAY)


def test_default_first_payment_is_two_weeks_out_and_inside_terms() -> None:
    first_payment = default_first_payment_date(NEGOTIATION)

    assert first_payment == date(2026, 10, 16)
    assert first_payment <= latest_first_payment_date(NEGOTIATION)


def test_suggested_plans_start_at_the_smallest_acceptable_amount_and_all_pass() -> None:
    negotiation = Negotiation(balance_yen=35_000, today=date(2026, 10, 2))

    plans = suggested_plans(negotiation)

    assert [plan.proposal.monthly_yen for plan in plans] == [6_000, 7_000, 8_000]
    assert all(plan.is_accepted for plan in plans)
    assert all(sum(i.amount_yen for i in plan.schedule) == 35_000 for plan in plans)
    assert {plan.proposal.first_payment_on for plan in plans} == {date(2026, 10, 16)}


def test_a_balance_at_the_minimum_suggests_one_full_payment() -> None:
    plans = suggested_plans(Negotiation(balance_yen=5_000, today=date(2026, 10, 2)))

    assert [len(plan.schedule) for plan in plans] == [1]
