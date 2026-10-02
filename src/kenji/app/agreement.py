"""Turn an accepted payment plan into the exact words Kenji reads back and the SMS preview."""

from datetime import date

from kenji.app.script import Line, Lines, SmsTemplates
from kenji.domain.account import AccountSummary
from kenji.domain.identity import DebtorIdentity
from kenji.domain.terms import TermsDecision

_MONTH_ABBREVIATIONS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)  # fmt: skip


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
        "regular_installments": str(len(schedule) - 1),
        "final_yen": format_yen(final.amount_yen),
        "total_yen": format_yen(sum(installment.amount_yen for installment in schedule)),
    }


def describe_plan_en(decision: TermsDecision) -> str:
    schedule = decision.schedule
    first, final = schedule[0], schedule[-1]
    start = format_date_en(first.due_on)
    if len(schedule) == 1:
        return f"¥{format_yen(final.amount_yen)} in one payment on {start}"
    if final.amount_yen == first.amount_yen:
        return f"¥{format_yen(first.amount_yen)} × {len(schedule)} from {start}"
    regular = f"¥{format_yen(first.amount_yen)} × {len(schedule) - 1}"
    last = f"¥{format_yen(final.amount_yen)}"
    return f"{regular} then {last} from {start} ({len(schedule)} payments)"


def describe_read_back(lines: Lines, decision: TermsDecision) -> Line:
    schedule = decision.schedule
    if len(schedule) == 1:
        template = lines.read_back_single
    elif schedule[-1].amount_yen == schedule[0].amount_yen:
        template = lines.read_back_even
    else:
        template = lines.read_back
    return template.fill(agreement_fields(decision))


def honorific_fields(debtor: DebtorIdentity) -> dict[str, str]:
    return {
        "honorific_ja": f"{debtor.family_name_written}様",
        "honorific_en": f"{debtor.family_name_latin}-sama",
    }


def describe_promise_sms(
    sms: SmsTemplates, decision: TermsDecision, debtor: DebtorIdentity
) -> Line:
    template = sms.promise_single if len(decision.schedule) == 1 else sms.promise
    return template.fill(agreement_fields(decision) | honorific_fields(debtor))


def describe_handoff_sms(sms: SmsTemplates, debtor: DebtorIdentity) -> Line:
    return sms.handoff.fill(honorific_fields(debtor))


def describe_balance(lines: Lines, summary: AccountSummary) -> Line:
    return lines.balance_statement.fill(
        {
            "account_suffix": summary.account_suffix,
            "overdue_since": format_date_ja(summary.overdue_since),
            "overdue_since_en": format_date_en(summary.overdue_since),
            "balance_yen": format_yen(summary.balance_yen),
        }
    )
