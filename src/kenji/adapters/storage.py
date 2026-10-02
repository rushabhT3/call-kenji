"""Files on disk: per-call events and audit chain (text only, never audio), contacts, usage.

Layout under DATA_DIR:
    calls/<date>/<call_id>/events.jsonl   live-page events
    calls/<date>/<call_id>/audit.jsonl    hash-chained audit records
    contacts.json                         stop-contact requests
    usage/<date>-<pool>.json              daily guardrail counters per transport
"""

import json
import shutil
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field, TypeAdapter

from kenji.app.events import CallEvent
from kenji.domain.audit import AuditEntry, AuditRecord, append_entry, record_from_json
from kenji.domain.contact import ContactPreferences, StopContactRequest, record_stop_contact
from kenji.domain.guardrails import UsageToday
from kenji.domain.retention import is_expired

_EVENT = TypeAdapter[CallEvent](CallEvent)


def _append_line(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(text + "\n")


class CallRecord:
    """Writes one call's events and audit chain as JSON lines."""

    def __init__(self, data_dir: Path, call_date: date, call_id: str) -> None:
        self._directory = data_dir / "calls" / call_date.isoformat() / call_id
        self._last: AuditRecord | None = None
        self._records: list[AuditRecord] = []

    def publish(self, event: CallEvent) -> None:
        _append_line(self._directory / "events.jsonl", _EVENT.dump_json(event).decode("utf-8"))

    def append(self, entry: AuditEntry) -> AuditRecord:
        record = append_entry(self._last, entry)
        line = json.dumps(record.to_json(), ensure_ascii=False, sort_keys=True)
        _append_line(self._directory / "audit.jsonl", line)
        self._last = record
        self._records.append(record)
        return record

    def records(self) -> list[AuditRecord]:
        return list(self._records)


def read_audit(path: Path) -> list[AuditRecord]:
    with path.open(encoding="utf-8") as file:
        return [record_from_json(json.loads(line)) for line in file if line.strip()]


def purge_expired_calls(data_dir: Path, today: date, retention_days: int) -> list[Path]:
    calls_dir = data_dir / "calls"
    if not calls_dir.exists():
        return []
    expired = [
        day_dir
        for day_dir in calls_dir.iterdir()
        if day_dir.is_dir() and is_expired(date.fromisoformat(day_dir.name), today, retention_days)
    ]
    for day_dir in expired:
        shutil.rmtree(day_dir)
    return expired


class JsonContactStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def preferences(self) -> ContactPreferences:
        if not self._path.exists():
            return ContactPreferences()
        stopped = json.loads(self._path.read_text(encoding="utf-8"))["stopped_callers"]
        return ContactPreferences(stopped_callers=frozenset(stopped))

    def record(self, request: StopContactRequest) -> None:
        updated = record_stop_contact(self.preferences(), request)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"stopped_callers": sorted(updated.stopped_callers)}
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class _DailyUsage(BaseModel):
    seconds: int = 0
    calls: dict[str, int] = Field(default_factory=dict)


class JsonUsageLedger:
    """Daily counters for the budget guardrails, one small JSON file per Japan-time day."""

    def __init__(self, usage_dir: Path) -> None:
        self._usage_dir = usage_dir

    def usage_today(self, pool: str, caller_ref: str, day: date) -> UsageToday:
        usage = self._read(pool, day)
        return UsageToday(
            seconds_used=usage.seconds, calls_by_this_caller=usage.calls.get(caller_ref, 0)
        )

    def record_call(self, pool: str, caller_ref: str, day: date) -> None:
        usage = self._read(pool, day)
        usage.calls[caller_ref] = usage.calls.get(caller_ref, 0) + 1
        self._write(pool, day, usage)

    def record_seconds(self, pool: str, day: date, seconds: int) -> None:
        usage = self._read(pool, day)
        usage.seconds += seconds
        self._write(pool, day, usage)

    def _path(self, pool: str, day: date) -> Path:
        return self._usage_dir / f"{day.isoformat()}-{pool}.json"

    def _read(self, pool: str, day: date) -> _DailyUsage:
        path = self._path(pool, day)
        if not path.exists():
            return _DailyUsage()
        return _DailyUsage.model_validate_json(path.read_text(encoding="utf-8"))

    def _write(self, pool: str, day: date, usage: _DailyUsage) -> None:
        self._usage_dir.mkdir(parents=True, exist_ok=True)
        self._path(pool, day).write_text(usage.model_dump_json(indent=2), encoding="utf-8")
