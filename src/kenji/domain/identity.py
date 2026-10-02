"""Identity gate: nothing about the account is disclosed until the debtor is verified."""

from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum

from kenji.domain.text import spoken_characters, to_hiragana

_HONORIFIC_SUFFIXES = ("です", "さま", "さん", "様")
DEFAULT_MAX_ATTEMPTS = 3


@dataclass(frozen=True, slots=True)
class DebtorIdentity:
    family_name_kana: str
    given_name_kana: str
    written_name: str
    family_name_written: str
    family_name_latin: str
    date_of_birth: date

    def accepted_names(self) -> frozenset[str]:
        return frozenset(
            normalize_name(name)
            for name in (
                self.family_name_kana + self.given_name_kana,
                self.given_name_kana + self.family_name_kana,
                self.written_name,
            )
        )


@dataclass(frozen=True, slots=True)
class IdentityClaim:
    spoken_name: str
    date_of_birth: date


class IdentityStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    LOCKED_OUT = "locked_out"


@dataclass(frozen=True, slots=True)
class IdentityGate:
    status: IdentityStatus = IdentityStatus.UNVERIFIED
    failed_attempts: int = 0
    max_attempts: int = DEFAULT_MAX_ATTEMPTS

    @property
    def is_verified(self) -> bool:
        return self.status is IdentityStatus.VERIFIED


def normalize_name(name: str) -> str:
    normalized = spoken_characters(to_hiragana(name)).lower()
    for suffix in _HONORIFIC_SUFFIXES:
        normalized = normalized.removesuffix(suffix)
    return normalized


def claim_matches(claim: IdentityClaim, identity: DebtorIdentity) -> bool:
    return (
        claim.date_of_birth == identity.date_of_birth
        and normalize_name(claim.spoken_name) in identity.accepted_names()
    )


def attempt_verification(
    gate: IdentityGate, claim: IdentityClaim, identity: DebtorIdentity
) -> IdentityGate:
    if gate.status is not IdentityStatus.UNVERIFIED:
        return gate
    if claim_matches(claim, identity):
        return replace(gate, status=IdentityStatus.VERIFIED)
    failed_attempts = gate.failed_attempts + 1
    status = (
        IdentityStatus.LOCKED_OUT
        if failed_attempts >= gate.max_attempts
        else IdentityStatus.UNVERIFIED
    )
    return replace(gate, status=status, failed_attempts=failed_attempts)
