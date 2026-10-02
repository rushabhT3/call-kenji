"""The overdue account and the only view of it a caller may receive."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from kenji.domain.identity import DebtorIdentity, IdentityGate


@dataclass(frozen=True, slots=True)
class Account:
    account_suffix: str
    balance_yen: int
    overdue_since: date
    debtor: DebtorIdentity


@dataclass(frozen=True, slots=True)
class AccountSummary:
    account_suffix: str
    balance_yen: int
    overdue_since: date


@dataclass(frozen=True, slots=True)
class AccountLocked:
    status: Literal["LOCKED"] = "LOCKED"


def summarize_account(account: Account, gate: IdentityGate) -> AccountSummary | AccountLocked:
    if not gate.is_verified:
        return AccountLocked()
    return AccountSummary(
        account_suffix=account.account_suffix,
        balance_yen=account.balance_yen,
        overdue_since=account.overdue_since,
    )
