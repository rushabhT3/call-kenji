"""Turn an accepted payment plan into the exact words Kenji reads back and the SMS preview."""

from datetime import date

from kenji.app.script import Line
from kenji.domain.terms import TermsDecision

_MONTH_ABBREVIATIONS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


def format_yen(amount_yen: int) -> str:
    return f"{amount_yen:,}"


def format_date_ja(day: date) -> str:
    return f"{day.month}月{day.day}日"


def format_date_en(day: date) -> str:
    return f"{day.day} {_MONTH_ABBREVIATIONS[day.month - 1]}"


def agreement_fields(decision: TermsDecision) -> dict[str, str]:
    if not decision.is_accepted:
        raise ValueError(f"no agreement to describe: {decision.violations}")
    schedule = decision.schedule
    first, final = schedule[0], schedule[-1]
    return {
        "first_due": format_date_ja(first.due_on),
        "first_due_en": format_date_en(first.due_on),
        "monthly_yen": format_yen(first.amount_yen),
        "installments": str(len(schedule)),
        "final_yen": format_yen(final.amount_yen),
        "total_yen": format_yen(sum(installment.amount_yen for installment in schedule)),
    }


def describe_agreement(template: Line, decision: TermsDecision) -> Line:
    return template.fill(agreement_fields(decision))
