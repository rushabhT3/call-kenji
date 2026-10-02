import json
from datetime import date, datetime
from pathlib import Path

from loguru import logger

from kenji.adapters.storage import (
    CallRecord,
    JsonContactStore,
    JsonUsageLedger,
    purge_expired_calls,
    read_audit,
)
from kenji.app.events import FlowNodeEntered
from kenji.domain.audit import AuditEntry, verify_chain
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.contact import StopContactRequest

TODAY = date(2026, 10, 2)


async def test_call_record_writes_text_only_and_a_verifiable_chain(tmp_path: Path) -> None:
    record = CallRecord(tmp_path, TODAY, "call-1")
    record.publish(FlowNodeEntered(node="greeting"))
    for kind in ("call_started", "identity_checked"):
        record.append(AuditEntry(kind=kind, recorded_at="2026-10-02T15:00:00+09:00", payload={}))
    await record.close()

    call_dir = tmp_path / "calls" / "2026-10-02" / "call-1"
    assert sorted(path.name for path in call_dir.iterdir()) == ["audit.jsonl", "events.jsonl"]
    line = json.loads((call_dir / "events.jsonl").read_text(encoding="utf-8"))
    assert line["event"] == {"type": "flow_node", "node": "greeting"}
    assert line["offset_ms"] >= 0
    assert verify_chain(read_audit(call_dir / "audit.jsonl")).is_valid


async def test_call_record_keeps_event_order_across_many_writes(tmp_path: Path) -> None:
    record = CallRecord(tmp_path, TODAY, "call-1")
    nodes = [f"node-{index}" for index in range(200)]
    for node in nodes:
        record.publish(FlowNodeEntered(node=node))
    await record.close()

    events_path = tmp_path / "calls" / "2026-10-02" / "call-1" / "events.jsonl"
    lines = events_path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["event"]["node"] for line in lines] == nodes


async def test_call_record_that_cannot_write_logs_and_keeps_the_call_going(
    tmp_path: Path,
) -> None:
    (tmp_path / "calls").write_text("a file where the calls directory should be", encoding="utf-8")
    record = CallRecord(tmp_path, TODAY, "call-1")
    messages: list[str] = []
    sink = logger.add(lambda message: messages.append(str(message)), level="ERROR")
    try:
        record.publish(FlowNodeEntered(node="greeting"))
        await record.close()
    finally:
        logger.remove(sink)

    assert any("could not write a call record line" in message for message in messages)


def test_purge_deletes_days_older_than_retention(tmp_path: Path) -> None:
    for day in ("2026-08-31", "2026-09-02", "2026-10-01"):
        (tmp_path / "calls" / day / "call").mkdir(parents=True)

    removed = purge_expired_calls(tmp_path, TODAY, retention_days=30)

    assert [path.name for path in removed] == ["2026-08-31"]
    assert sorted(path.name for path in (tmp_path / "calls").iterdir()) == [
        "2026-09-02",
        "2026-10-01",
    ]


def test_purge_with_no_calls_yet(tmp_path: Path) -> None:
    assert purge_expired_calls(tmp_path, TODAY, retention_days=30) == []


def test_usage_ledger_counts_per_pool_and_caller(tmp_path: Path) -> None:
    ledger = JsonUsageLedger(tmp_path)
    ledger.record_call("phone", "caller-a", TODAY)
    ledger.record_call("phone", "caller-a", TODAY)
    ledger.record_seconds("phone", TODAY, 125)

    phone = ledger.usage_today("phone", "caller-a", TODAY)
    browser = ledger.usage_today("browser", "caller-a", TODAY)

    assert (phone.seconds_used, phone.calls_by_this_caller) == (125, 2)
    assert (browser.seconds_used, browser.calls_by_this_caller) == (0, 0)


def test_contact_store_persists_stop_requests(tmp_path: Path) -> None:
    path = tmp_path / "contacts.json"
    requested_at = datetime(2026, 10, 2, 15, 0, tzinfo=JAPAN_STANDARD_TIME)
    JsonContactStore(path).record(StopContactRequest("caller-a", requested_at))

    assert JsonContactStore(path).preferences().stopped_callers == frozenset({"caller-a"})
