"""Append-only audit chain: each record seals SHA-256(previous hash + record)."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

type JsonValue = str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None

GENESIS_HASH = "0" * 64


@dataclass(frozen=True, slots=True)
class AuditEntry:
    kind: str
    recorded_at: str
    payload: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class AuditRecord:
    sequence: int
    entry: AuditEntry
    previous_hash: str
    hash: str

    def body(self) -> dict[str, JsonValue]:
        return _body(self.sequence, self.entry)

    def to_json(self) -> dict[str, JsonValue]:
        return {**self.body(), "previous_hash": self.previous_hash, "hash": self.hash}


@dataclass(frozen=True, slots=True)
class ChainVerification:
    is_valid: bool
    first_invalid_sequence: int | None = None


def _body(sequence: int, entry: AuditEntry) -> dict[str, JsonValue]:
    return {
        "sequence": sequence,
        "kind": entry.kind,
        "recorded_at": entry.recorded_at,
        "payload": dict(entry.payload),
    }


def canonical_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def seal(previous_hash: str, body: dict[str, JsonValue]) -> str:
    return hashlib.sha256((previous_hash + canonical_json(body)).encode("utf-8")).hexdigest()


def append_entry(previous: AuditRecord | None, entry: AuditEntry) -> AuditRecord:
    sequence = 0 if previous is None else previous.sequence + 1
    previous_hash = GENESIS_HASH if previous is None else previous.hash
    return AuditRecord(
        sequence=sequence,
        entry=entry,
        previous_hash=previous_hash,
        hash=seal(previous_hash, _body(sequence, entry)),
    )


def record_from_json(raw: Mapping[str, JsonValue]) -> AuditRecord:
    sequence, payload = raw["sequence"], raw["payload"]
    if not isinstance(sequence, int) or not isinstance(payload, dict):
        raise ValueError(f"malformed audit record: {raw!r}")
    return AuditRecord(
        sequence=sequence,
        entry=AuditEntry(
            kind=str(raw["kind"]), recorded_at=str(raw["recorded_at"]), payload=payload
        ),
        previous_hash=str(raw["previous_hash"]),
        hash=str(raw["hash"]),
    )


def chain_head(records: Sequence[AuditRecord]) -> str:
    return records[-1].hash if records else GENESIS_HASH


def verify_chain(
    records: Sequence[AuditRecord], expected_head: str | None = None
) -> ChainVerification:
    expected_previous = GENESIS_HASH
    for expected_sequence, record in enumerate(records):
        is_linked = (
            record.sequence == expected_sequence and record.previous_hash == expected_previous
        )
        if not is_linked or seal(record.previous_hash, record.body()) != record.hash:
            return ChainVerification(is_valid=False, first_invalid_sequence=expected_sequence)
        expected_previous = record.hash
    if expected_head is not None and expected_previous != expected_head:
        return ChainVerification(is_valid=False, first_invalid_sequence=len(records))
    return ChainVerification(is_valid=True)
