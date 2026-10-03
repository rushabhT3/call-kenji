"""Load the script and the fictional personas from YAML, failing fast on anything missing."""

from datetime import date
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from kenji.app.personas import PersonaCatalog
from kenji.app.script import Script
from kenji.app.tools import NodeName
from kenji.domain.account import Account
from kenji.domain.dates import parse_japanese_date
from kenji.domain.identity import DebtorIdentity


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_script(path: Path) -> Script:
    return Script.model_validate(_read_yaml(path))


class _File(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _DebtorFile(_File):
    family_name_kana: str
    given_name_kana: str
    written_name: str
    family_name_written: str
    family_name_latin: str
    date_of_birth: date


class _InBothLanguages(_File):
    en: str
    ja: str


class _PhraseFile(_File):
    id: str
    steps: list[NodeName]
    label: str
    ja: str
    en: str


class _PersonaFile(_File):
    id: str
    debtor: _DebtorFile
    name_en: str
    birth_date_ja: str
    account_suffix: str
    balance_yen: int
    overdue_since: date
    situation: _InBothLanguages
    mood: _InBothLanguages
    phrases: list[_PhraseFile]

    @model_validator(mode="after")
    def _birth_date_ja_is_the_date_of_birth(self) -> Self:
        if parse_japanese_date(self.birth_date_ja) != self.debtor.date_of_birth:
            raise ValueError(f"persona {self.id!r}: birth_date_ja is not its date_of_birth")
        return self


class _PersonasFile(_File):
    default: str
    personas: list[_PersonaFile]

    @model_validator(mode="after")
    def _ids_are_unique(self) -> Self:
        ids = [persona.id for persona in self.personas]
        if len(set(ids)) != len(ids):
            raise ValueError(f"persona ids must be unique, got {ids}")
        return self


def _account(persona: _PersonaFile) -> Account:
    return Account(
        account_suffix=persona.account_suffix,
        balance_yen=persona.balance_yen,
        overdue_since=persona.overdue_since,
        debtor=DebtorIdentity(**persona.debtor.model_dump()),
    )


def load_personas(path: Path) -> PersonaCatalog:
    raw = _PersonasFile.model_validate(_read_yaml(path))
    return PersonaCatalog(
        default_id=raw.default,
        accounts={persona.id: _account(persona) for persona in raw.personas},
    )
