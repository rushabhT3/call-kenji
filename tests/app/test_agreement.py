"""Plans described in English for the strategist, in each of their three shapes."""

from datetime import date

from kenji.app.agreement import describe_plan_en
from kenji.domain.terms import Negotiation, PaymentProposal, check_terms

NEGOTIATION = Negotiation(balance_yen=35_000, today=date(2026, 10, 2))
FIRST_PAYMENT = date(2026, 10, 16)


def _plan(monthly_yen: int) -> str:
    return describe_plan_en(check_terms(PaymentProposal(monthly_yen, FIRST_PAYMENT), NEGOTIATION))


def test_a_plan_with_a_smaller_last_payment_says_so() -> None:
    assert _plan(6_000) == "¥6,000 × 5 then ¥5,000 from 16 Oct (6 payments)"


def test_an_even_plan_is_one_amount_times_the_count() -> None:
    assert _plan(7_000) == "¥7,000 × 5 from 16 Oct"


def test_paying_in_full_is_one_payment() -> None:
    assert _plan(35_000) == "¥35,000 in one payment on 16 Oct"
