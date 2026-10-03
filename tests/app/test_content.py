from dataclasses import fields
from datetime import date
from pathlib import Path

import pytest

from kenji.adapters.content import load_personas, load_script
from kenji.app.agreement import (
    describe_balance,
    describe_handoff_sms,
    describe_promise_sms,
    describe_read_back,
)
from kenji.app.personas import PersonaCatalog
from kenji.app.script import Script
from kenji.domain.account import Account, AccountSummary
from kenji.domain.terms import Negotiation, PaymentProposal, check_terms
from kenji.domain.turn import LexiconBackchannelClassifier, TurnVerdict

CONTENT = Path(__file__).resolve().parents[2] / "content"


@pytest.fixture(scope="module")
def script() -> Script:
    return load_script(CONTENT / "script_ja.yaml")


@pytest.fixture(scope="module")
def personas() -> PersonaCatalog:
    return load_personas(CONTENT / "personas.yaml")


@pytest.fixture(scope="module")
def account(personas: PersonaCatalog) -> Account:
    return personas.account_for(None)


def test_the_default_persona_is_the_fictional_debtor(account: Account) -> None:
    assert account.debtor.written_name == "佐藤ゆうき"
    assert account.debtor.date_of_birth == date(1990, 7, 14)
    assert (account.account_suffix, account.balance_yen) == ("7731", 35_000)


def test_japanese_lines_have_no_spaces_after_loading(script: Script) -> None:
    for line in vars(script.lines).values():
        assert " " not in line.ja


def test_every_template_fills(script: Script, account: Account) -> None:
    negotiation = Negotiation(balance_yen=account.balance_yen, today=date(2026, 10, 2))
    plan = check_terms(PaymentProposal(6_000, date(2026, 10, 27)), negotiation)
    lump_sum = check_terms(PaymentProposal(35_000, date(2026, 10, 27)), negotiation)
    even = check_terms(PaymentProposal(7_000, date(2026, 10, 27)), negotiation)
    summary = AccountSummary(account.account_suffix, account.balance_yen, account.overdue_since)

    filled = [
        describe_read_back(script.lines, plan),
        describe_read_back(script.lines, lump_sum),
        describe_balance(script.lines, summary),
        describe_promise_sms(script.sms, plan, account.debtor),
        describe_promise_sms(script.sms, lump_sum, account.debtor),
        describe_handoff_sms(script.sms, account.debtor),
        describe_read_back(script.lines, even),
    ]

    assert all("{" not in line.ja and "{" not in line.en for line in filled)
    assert "毎月6,000円を5回、そのあと最終回に5,000円で、全6回" in filled[0].ja
    assert "毎月7,000円を5回で、合計35,000円" in filled[-1].ja
    assert "35,000円を一括" in filled[1].ja
    assert filled[3].ja.startswith("【みなと債権回収】佐藤様")


def test_neutral_lines_never_name_the_debt(script: Script) -> None:
    lines = script.lines
    neutral = [
        lines.greeting,
        lines.link_prompt,
        lines.ask_identity,
        lines.third_party_callback,
        lines.identity_locked,
    ]
    for line in neutral:
        for word in ("債権", "回収", "返済", "支払", "延滞", "滞納", "円"):
            assert word not in line.ja


def test_read_back_is_the_strictest_node(script: Script) -> None:
    thresholds = {
        name: getattr(script.nodes, name).min_interruption_score
        for name in type(script.nodes).model_fields
    }
    read_back = thresholds.pop("read_back")

    assert all(read_back > other for other in thresholds.values())


@pytest.mark.parametrize(
    ("utterance", "verdict"),
    [("はい", TurnVerdict.BACKCHANNEL), ("ちょっと待ってください", TurnVerdict.INTERRUPTION)],
)
def test_required_turn_cases_hold_with_the_configured_read_back_policy(
    script: Script, utterance: str, verdict: TurnVerdict
) -> None:
    policy = script.nodes.read_back.turn_policy

    assert LexiconBackchannelClassifier().classify(utterance, policy).verdict is verdict


def test_every_tool_documents_exactly_its_parameters(script: Script) -> None:
    expected = {
        "verify_identity": {"name_kana", "date_of_birth"},
        "check_terms": {"monthly_yen", "first_payment_date"},
        "confirm_plan": {"monthly_yen", "first_payment_date"},
        "request_human": {"reason", "summary"},
        "end_without_agreement": {"reason"},
    }
    for name in type(script.tools).model_fields:
        assert set(getattr(script.tools, name).parameters) == expected.get(name, set())


def test_debtor_identity_fields_all_come_from_the_persona_file(personas: PersonaCatalog) -> None:
    for account in personas.accounts.values():
        assert all(getattr(account.debtor, field.name) for field in fields(account.debtor))
