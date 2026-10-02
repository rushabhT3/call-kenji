from datetime import datetime

import pytest

from kenji.app.session import CallContext, CallSession
from kenji.app.tools import CallTools, NodeName
from kenji.domain.account import Account
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.identity import DebtorIdentity
from kenji.domain.outcome import CallOutcome
from kenji.domain.terms import Negotiation
from tests.conversation.harness import FixedClock, MemoryContacts, MemoryRecorder

NOW = datetime(2026, 10, 2, 15, 0, tzinfo=JAPAN_STANDARD_TIME)
YUKI = DebtorIdentity(
    family_name_kana="さとう",
    given_name_kana="ゆうき",
    written_name="佐藤ゆうき",
    family_name_written="佐藤",
    family_name_latin="Sato",
    date_of_birth=datetime(1990, 7, 14, tzinfo=JAPAN_STANDARD_TIME).date(),
)
ACCOUNT = Account("7731", 35_000, NOW.date().replace(day=30, month=9), YUKI)


@pytest.fixture
def recorder() -> MemoryRecorder:
    return MemoryRecorder()


@pytest.fixture
def session(recorder: MemoryRecorder) -> CallSession:
    context = CallContext(
        call_id="call-1",
        transport="browser",
        caller_ref="caller-1",
        started_at=NOW,
        account=ACCOUNT,
        negotiation=Negotiation(balance_yen=35_000, today=NOW.date()),
    )
    return CallSession(context, recorder, recorder, FixedClock(NOW))


@pytest.fixture
def tools(session: CallSession) -> CallTools:
    return CallTools(session, MemoryContacts())


def _verify(tools: CallTools) -> None:
    tools.verify_identity("サトウユウキ", "1990-07-14")


def test_account_summary_is_locked_before_verification(tools: CallTools) -> None:
    assert tools.get_account_summary().result == {"status": "LOCKED"}


def test_account_summary_after_verification(tools: CallTools) -> None:
    _verify(tools)

    assert tools.get_account_summary().result["balance_yen"] == 35_000


def test_verification_moves_to_the_balance(tools: CallTools) -> None:
    outcome = tools.verify_identity("サトウユウキ", "平成2年7月14日")

    assert outcome.next_node is NodeName.STATE_BALANCE


def test_three_mismatches_lock_out_and_end(tools: CallTools, session: CallSession) -> None:
    outcomes = [tools.verify_identity("スズキハナコ", "1990-07-14") for _ in range(3)]

    assert outcomes[0].result == {"status": "mismatch", "attempts_left": 2}
    assert outcomes[-1].next_node is NodeName.IDENTITY_LOCKED
    assert session.outcome is CallOutcome.IDENTITY_NOT_VERIFIED


def test_unreadable_birth_date_is_an_error_not_a_failed_attempt(tools: CallTools) -> None:
    assert "error" in tools.verify_identity("サトウユウキ", "そのうち").result


def test_3000_yen_is_rejected_with_a_counter_offer(tools: CallTools) -> None:
    _verify(tools)

    result = tools.check_terms(3000, None).result

    assert result["accepted"] is False
    assert result["smallest_acceptable_monthly_yen"] == 6_000


@pytest.mark.parametrize("amount", ["6,000", "6000円", 6000])
def test_amounts_are_parsed_at_the_boundary(tools: CallTools, amount: object) -> None:
    assert tools.check_terms(amount, "2026-10-27").result["accepted"] is True


@pytest.mark.parametrize("amount", [None, "たくさん", -5])
def test_unusable_amounts_are_errors(tools: CallTools, amount: object) -> None:
    assert "error" in tools.check_terms(amount, None).result


def test_promise_needs_a_confirmed_plan(tools: CallTools) -> None:
    _verify(tools)
    tools.confirm_plan(3000, None)

    assert "error" in tools.record_promise().result


def test_confirmed_plan_is_promised_and_closes(tools: CallTools, session: CallSession) -> None:
    _verify(tools)
    assert tools.confirm_plan(6000, None).next_node is NodeName.READ_BACK

    outcome = tools.record_promise()

    assert outcome.next_node is NodeName.CLOSE
    assert session.outcome is CallOutcome.PROMISE_TO_PAY


def test_stop_contact_is_stored_and_audited(session: CallSession, recorder: MemoryRecorder) -> None:
    contacts = MemoryContacts()

    CallTools(session, contacts).record_stop_contact()

    assert "caller-1" in contacts.preferences().stopped_callers
    assert "stop_contact_recorded" in [record.entry.kind for record in recorder.records()]


def test_first_outcome_wins(tools: CallTools, session: CallSession) -> None:
    tools.third_party_answered()
    tools.end_without_agreement("終了")

    assert session.outcome is CallOutcome.CALLBACK_REQUESTED
