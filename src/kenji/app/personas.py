"""The fictional debtors a caller can play, and the one a call plays when none is chosen."""

from collections.abc import Mapping
from dataclasses import dataclass

from kenji.domain.account import Account


@dataclass(frozen=True, slots=True)
class PersonaCatalog:
    default_id: str
    accounts: Mapping[str, Account]

    def __post_init__(self) -> None:
        if self.default_id not in self.accounts:
            raise ValueError(f"the default persona {self.default_id!r} is not in the catalog")

    def resolve(self, persona_id: str | None) -> str:
        """The persona a call plays: the one asked for if it exists, otherwise the default."""
        if persona_id is None or persona_id not in self.accounts:
            return self.default_id
        return persona_id

    def account_for(self, persona_id: str | None) -> Account:
        return self.accounts[self.resolve(persona_id)]
