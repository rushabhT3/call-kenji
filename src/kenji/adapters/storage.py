"""Files on disk: per-call events and audit chain (text only, never audio), contacts, usage.

Layout under DATA_DIR:
    calls/<date>/<call_id>/events.jsonl   live-page events with their offset into the call
    calls/<date>/<call_id>/audit.jsonl    hash-chained audit records
    contacts.json                         stop-contact requests
    usage/<date>-<pool>.json              daily guardrail counters per transport
"""

import asyncio
import json
import shutil
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import TextIO

from loguru import logger
from pydantic import BaseModel, Field, TypeAdapter

from kenji.app.events import CallEvent
from kenji.domain.audit import AuditEntry, AuditRecord, append_entry, record_from_json
from kenji.domain.contact import ContactPreferences, StopContactRequest, record_stop_contact
from kenji.domain.guardrails import UsageToday
from kenji.domain.retention import is_expired

_EVENT = TypeAdapter[CallEvent](CallEvent)


class _LineFiles:
    """Appends lines from one background thread and keeps each file open until the call ends.

    The call's audio runs on the event loop, so no write may block it. On the Cloud Storage
    volume every open-append-close re-uploads the whole object, so each file is opened once
    and uploaded once, when it is closed.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._files: dict[str, TextIO] = {}
        self._writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="call-record")

    def append(self, name: str, line: str) -> None:
        self._writer.submit(self._write, name, line).add_done_callback(self._report_failure)

    async def close(self) -> None:
        await asyncio.wrap_future(self._writer.submit(self._close_all))
        self._writer.shutdown()

    def _write(self, name: str, line: str) -> None:
        file = self._files.get(name)
        if file is None:
            self._directory.mkdir(parents=True, exist_ok=True)
            file = self._files[name] = (self._directory / name).open("a", encoding="utf-8")
        file.write(line + "\n")

    def _close_all(self) -> None:
        for file in self._files.values():
            file.close()
        self._files.clear()

    def _report_failure(self, done: Future[None]) -> None:
        error = done.exception()
        if error is not None:
            logger.error(
                "could not write a call record line",
                directory=str(self._directory),
                error=str(error),
            )


class CallRecord:
    """Writes one call's events and audit chain as JSON lines."""

    def __init__(self, data_dir: Path, call_date: date, call_id: str) -> None:
        self._files = _LineFiles(data_dir / "calls" / call_date.isoformat() / call_id)
        self._last: AuditRecord | None = None
        self._records: list[AuditRecord] = []
        self._opened_at = time.monotonic()

    def publish(self, event: CallEvent) -> None:
        offset_ms = round((time.monotonic() - self._opened_at) * 1000)
        line = json.dumps(
            {"offset_ms": offset_ms, "event": _EVENT.dump_python(event, mode="json")},
            ensure_ascii=False,
        )
        self._files.append("events.jsonl", line)

    def append(self, entry: AuditEntry) -> AuditRecord:
        record = append_entry(self._last, entry)
        line = json.dumps(record.to_json(), ensure_ascii=False, sort_keys=True)
        self._files.append("audit.jsonl", line)
        self._last = record
        self._records.append(record)
        return record

    def records(self) -> list[AuditRecord]:
        return list(self._records)

    async def close(self) -> None:
        await self._files.close()


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
    """Stop-contact requests, read from disk once and saved off the event loop.

    The server runs as a single instance, so memory is the source of truth while it runs.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._preferences = self._load()
        self._writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="contacts")
        self._last_save: Future[None] | None = None

    def preferences(self) -> ContactPreferences:
        return self._preferences

    def record(self, request: StopContactRequest) -> None:
        self._preferences = record_stop_contact(self._preferences, request)
        self._last_save = self._writer.submit(self._save, self._preferences)
        self._last_save.add_done_callback(self._report_failure)

    def wait_for_save(self) -> None:
        if self._last_save is not None:
            self._last_save.result()

    def _load(self) -> ContactPreferences:
        if not self._path.exists():
            return ContactPreferences()
        stopped = json.loads(self._path.read_text(encoding="utf-8"))["stopped_callers"]
        return ContactPreferences(stopped_callers=frozenset(stopped))

    def _save(self, preferences: ContactPreferences) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"stopped_callers": sorted(preferences.stopped_callers)}
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _report_failure(self, done: Future[None]) -> None:
        error = done.exception()
        if error is not None:
            logger.error("could not save a stop-contact request", error=str(error))


class _DailyUsage(BaseModel):
    seconds: int = 0
    calls: dict[str, int] = Field(default_factory=dict)


class JsonUsageLedger:
    """Daily counters for the budget guardrails, one small JSON file per Japan-time day.

    Safe to call from worker threads: each read-modify-write holds a lock.
    """

    def __init__(self, usage_dir: Path) -> None:
        self._usage_dir = usage_dir
        self._lock = threading.Lock()

    def usage_today(self, pool: str, caller_ref: str, day: date) -> UsageToday:
        usage = self._read(pool, day)
        return UsageToday(
            seconds_used=usage.seconds, calls_by_this_caller=usage.calls.get(caller_ref, 0)
        )

    def record_call(self, pool: str, caller_ref: str, day: date) -> None:
        with self._lock:
            usage = self._read(pool, day)
            usage.calls[caller_ref] = usage.calls.get(caller_ref, 0) + 1
            self._write(pool, day, usage)

    def record_seconds(self, pool: str, day: date, seconds: int) -> None:
        with self._lock:
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
