from dataclasses import replace

import pytest

from kenji.domain.audit import (
    GENESIS_HASH,
    AuditEntry,
    AuditRecord,
    append_entry,
    chain_head,
    record_from_json,
    verify_chain,
)


def _chain(length: int) -> list[AuditRecord]:
    records: list[AuditRecord] = []
    for index in range(length):
        entry = AuditEntry(
            kind="turn",
            recorded_at=f"2026-10-02T10:00:0{index}+09:00",
            payload={"text": f"発話{index}", "score": 0.5},
        )
        records.append(append_entry(records[-1] if records else None, entry))
    return records


def test_untouched_chain_verifies() -> None:
    records = _chain(3)

    assert records[0].previous_hash == GENESIS_HASH
    assert verify_chain(records).is_valid


def test_edited_audit_record_fails_verify() -> None:
    records = _chain(3)
    edited_entry = replace(records[1].entry, payload={"text": "改ざん", "score": 0.5})
    records[1] = replace(records[1], entry=edited_entry)

    verification = verify_chain(records)

    assert not verification.is_valid
    assert verification.first_invalid_sequence == 1


def test_removed_record_fails_verify() -> None:
    records = _chain(3)
    del records[1]

    assert verify_chain(records).first_invalid_sequence == 1


def test_deleting_the_last_record_is_caught_with_the_published_head() -> None:
    records = _chain(3)
    published_head = chain_head(records)

    verification = verify_chain(records[:-1], expected_head=published_head)

    assert not verification.is_valid
    assert verification.first_invalid_sequence == 2


def test_intact_chain_matches_its_published_head() -> None:
    records = _chain(2)

    assert verify_chain(records, expected_head=chain_head(records)).is_valid
    assert chain_head([]) == GENESIS_HASH


def test_json_round_trip_preserves_the_chain() -> None:
    records = _chain(2)

    restored = [record_from_json(record.to_json()) for record in records]

    assert restored == records
    assert verify_chain(restored).is_valid


def test_malformed_json_record_is_rejected() -> None:
    raw = _chain(1)[0].to_json()
    raw["payload"] = "not an object"

    with pytest.raises(ValueError, match="malformed"):
        record_from_json(raw)
