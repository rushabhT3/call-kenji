"""A call plays one of the fictional personas, and the rules understand every persona's lines."""

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import yaml

from kenji.adapters.content import load_personas
from kenji.app.personas import PersonaCatalog
from kenji.domain.account import Account
from kenji.domain.identity import DebtorIdentity
from kenji.domain.terms import (
    Negotiation,
    PaymentProposal,
    check_terms,
    default_first_payment_date,
)
from kenji.domain.understanding import (
    find_birth_date,
    find_monthly_yen,
    names_the_debtor,
    only_identity_words,
)

PERSONAS_FILE = Path(__file__).resolve().parents[2] / "content" / "personas.yaml"
TODAY = date(2026, 10, 2)
RAW_PERSONAS: list[dict[str, Any]] = yaml.safe_load(PERSONAS_FILE.read_text(encoding="utf-8"))[
    "personas"
]
PERSONA_IDS = [persona["id"] for persona in RAW_PERSONAS]
LINES = {
    persona["id"]: {phrase["id"]: phrase["ja"] for phrase in persona["phrases"]}
    for persona in RAW_PERSONAS
}
YUKI = DebtorIdentity("さとう", "ゆうき", "佐藤ゆうき", "佐藤", "Sato", date(1990, 7, 14))
CATALOG = PersonaCatalog(
    default_id="sato",
    accounts={
        "sato": Account("7731", 35_000, date(2026, 9, 30), YUKI),
        "tanaka": Account("4410", 52_000, date(2026, 8, 31), YUKI),
    },
)


@pytest.fixture(scope="module")
def personas() -> PersonaCatalog:
    return load_personas(PERSONAS_FILE)


def test_a_known_persona_is_played() -> None:
    assert CATALOG.resolve("tanaka") == "tanaka"
    assert CATALOG.account_for("tanaka").account_suffix == "4410"


@pytest.mark.parametrize("persona_id", [None, "nobody", ""])
def test_a_missing_or_unknown_persona_plays_the_default(persona_id: str | None) -> None:
    assert CATALOG.resolve(persona_id) == "sato"
    assert CATALOG.account_for(persona_id).account_suffix == "7731"


def test_a_catalog_without_its_default_persona_is_refused() -> None:
    with pytest.raises(ValueError, match="nobody"):
        PersonaCatalog(default_id="nobody", accounts=CATALOG.accounts)


def test_all_five_personas_load_with_sato_as_the_default(personas: PersonaCatalog) -> None:
    assert personas.default_id == "sato"
    assert list(personas.accounts) == ["sato", "tanaka", "suzuki", "ito", "yamamoto"]
    tanaka = personas.account_for("tanaka")
    assert tanaka.debtor.written_name == "田中けんた"
    assert tanaka.debtor.date_of_birth == date(1985, 3, 2)
    assert (tanaka.account_suffix, tanaka.balance_yen) == ("4410", 52_000)


type FileEdit = Callable[[dict[str, Any]], object]


@pytest.mark.parametrize(
    ("edit", "complaint"),
    [
        (lambda raw: raw["personas"][0].update(nickname="ゆう"), "nickname"),
        (lambda raw: raw["personas"][1].pop("mood"), "mood"),
        (lambda raw: raw["personas"][1]["phrases"][0].pop("en"), r"phrases\.0\.en"),
        (lambda raw: raw["personas"][1].update(birth_date_ja="昭和60年3月12日"), "birth_date_ja"),
        (lambda raw: raw["personas"][2]["phrases"][0].update(steps=["greet"]), "steps"),
        (lambda raw: raw["personas"][1].update(id="sato"), "unique"),
        (lambda raw: raw.update(default="nobody"), "nobody"),
    ],
)
def test_a_broken_personas_file_fails_at_startup(
    tmp_path: Path, edit: FileEdit, complaint: str
) -> None:
    raw = yaml.safe_load(PERSONAS_FILE.read_text(encoding="utf-8"))
    edit(raw)
    broken = tmp_path / "personas.yaml"
    broken.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ValueError, match=complaint):
        load_personas(broken)


@pytest.mark.parametrize("persona_id", PERSONA_IDS)
def test_each_personas_identity_line_is_verified_by_the_rules(
    personas: PersonaCatalog, persona_id: str
) -> None:
    debtor = personas.account_for(persona_id).debtor
    line = LINES[persona_id]["identity"]

    assert find_birth_date(line) == debtor.date_of_birth
    assert names_the_debtor(line, debtor)
    assert only_identity_words(line, debtor)


@pytest.mark.parametrize("persona_id", PERSONA_IDS)
def test_each_personas_wrong_birthday_and_family_lines_verify_nobody(
    personas: PersonaCatalog, persona_id: str
) -> None:
    debtor = personas.account_for(persona_id).debtor
    lines = LINES[persona_id]

    assert find_birth_date(lines["wrong_birthday"]) not in {None, debtor.date_of_birth}
    assert not names_the_debtor(lines["family"], debtor)


def _within_terms(line: str, account: Account) -> bool:
    negotiation = Negotiation(balance_yen=account.balance_yen, today=TODAY)
    monthly_yen = find_monthly_yen(line)
    assert monthly_yen is not None, line
    proposal = PaymentProposal(monthly_yen, default_first_payment_date(negotiation))
    return check_terms(proposal, negotiation).is_accepted


@pytest.mark.parametrize("persona_id", PERSONA_IDS)
def test_each_personas_offers_fall_on_the_side_of_the_terms_their_labels_promise(
    personas: PersonaCatalog, persona_id: str
) -> None:
    account = personas.account_for(persona_id)

    assert _within_terms(LINES[persona_id]["accept"], account)
    assert not _within_terms(LINES[persona_id]["too_little"], account)
