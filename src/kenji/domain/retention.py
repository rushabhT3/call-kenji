"""Call transcripts and events are kept for 30 days, then deleted."""

from datetime import date, timedelta

RETENTION_DAYS = 30


def is_expired(recorded_on: date, today: date, retention_days: int = RETENTION_DAYS) -> bool:
    if retention_days <= 0:
        raise ValueError(f"retention must be positive, got {retention_days}")
    return recorded_on < today - timedelta(days=retention_days)
