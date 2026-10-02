from datetime import date

import pytest

from kenji.domain.account import Account, AccountLocked, AccountSummary, summarize_account
from kenji.domain.dates import parse_japanese_date
from kenji.domain.eras import ERAS
from kenji.domain.identity import (
    DebtorIdentity,
    IdentityClaim,
    IdentityGate,
    IdentityStatus,
    attempt_verification,
    normalize_name,
)

YUKI = DebtorIdentity(
    family_name_kana="さとう",
    given_name_kana="ゆうき",
    written_name="佐藤ゆうき",
    date_of_birth=date(1990, 7, 14),
)
ACCOUNT = Account(
    account_suffix="7731",
    balance_yen=35_000,
    overdue_since=date(2026, 9, 30),
    debtor=YUKI,
)
RIGHT_BIRTHDAY = date(1990, 7, 14)
WRONG_BIRTHDAY = date(1991, 7, 14)


def test_balance_is_locked_before_identity_is_verified() -> None:
    assert summarize_account(ACCOUNT, IdentityGate()) == AccountLocked()


def test_balance_is_revealed_after_identity_is_verified() -> None:
    gate = attempt_verification(IdentityGate(), IdentityClaim("サトウユウキ", RIGHT_BIRTHDAY), YUKI)

    assert summarize_account(ACCOUNT, gate) == AccountSummary("7731", 35_000, date(2026, 9, 30))


@pytest.mark.parametrize(
    "spoken_name",
    [
        "佐藤ゆうき",
        "佐藤 ゆうき",
        "サトウ　ユウキ",
        "さとうゆうき",
        "ユウキサトウ",
        "佐藤ゆうきです",
        "さとうゆうき様",
    ],
)
def test_name_variants_verify(spoken_name: str) -> None:
    gate = attempt_verification(IdentityGate(), IdentityClaim(spoken_name, RIGHT_BIRTHDAY), YUKI)

    assert gate.status is IdentityStatus.VERIFIED


def test_wrong_birthday_does_not_verify() -> None:
    gate = attempt_verification(IdentityGate(), IdentityClaim("さとうゆうき", WRONG_BIRTHDAY), YUKI)

    assert gate.status is IdentityStatus.UNVERIFIED
    assert gate.failed_attempts == 1


def test_gate_locks_after_max_failed_attempts() -> None:
    gate = IdentityGate()
    for _ in range(gate.max_attempts):
        gate = attempt_verification(gate, IdentityClaim("すずきはなこ", RIGHT_BIRTHDAY), YUKI)

    assert gate.status is IdentityStatus.LOCKED


def test_locked_gate_stays_locked_even_for_the_right_claim() -> None:
    locked = IdentityGate(status=IdentityStatus.LOCKED, failed_attempts=3)

    after = attempt_verification(locked, IdentityClaim("さとうゆうき", RIGHT_BIRTHDAY), YUKI)

    assert after == locked
    assert summarize_account(ACCOUNT, after) == AccountLocked()


def test_normalize_name_drops_spacing_punctuation_and_honorifics() -> None:
    assert normalize_name(" サトウ・ユウキ さん ") == "さとうゆうき"


@pytest.mark.parametrize(
    "text",
    ["1990-07-14", "1990/7/14", "1990年7月14日", "平成2年7月14日", "平成２年 ７月１４日"],
)
def test_birth_dates_parse_from_western_and_era_formats(text: str) -> None:
    assert parse_japanese_date(text) == RIGHT_BIRTHDAY


def test_first_year_of_an_era_parses() -> None:
    assert parse_japanese_date("令和元年5月1日") == date(2019, 5, 1)


@pytest.mark.parametrize("text", ["七月十四日", "1990-13-01", "平成0年1月1日"])
def test_unparseable_dates_are_rejected(text: str) -> None:
    with pytest.raises(ValueError, match=r"unrecognised date|must be in|positive"):
        parse_japanese_date(text)


def test_era_rejects_non_positive_year() -> None:
    with pytest.raises(ValueError, match="positive"):
        ERAS["平成"].to_western_year(0)
