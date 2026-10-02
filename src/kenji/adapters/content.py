"""Load the script and the fictional account from YAML, failing fast on anything missing."""

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from kenji.app.script import Script
from kenji.domain.account import Account
from kenji.domain.identity import DebtorIdentity


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_script(path: Path) -> Script:
    return Script.model_validate(_read_yaml(path))


class _DebtorFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family_name_kana: str
    given_name_kana: str
    written_name: str
    family_name_written: str
    family_name_latin: str
    date_of_birth: date


class _AccountFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    debtor: _DebtorFile
    account_suffix: str
    balance_yen: int
    overdue_since: date


def load_account(path: Path) -> Account:
    raw = _AccountFile.model_validate(_read_yaml(path))
    return Account(
        account_suffix=raw.account_suffix,
        balance_yen=raw.balance_yen,
        overdue_since=raw.overdue_since,
        debtor=DebtorIdentity(**raw.debtor.model_dump()),
    )
