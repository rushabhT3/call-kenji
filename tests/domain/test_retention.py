from datetime import date

import pytest

from kenji.domain.retention import RETENTION_DAYS, is_expired

TODAY = date(2026, 10, 2)


def test_records_are_kept_for_thirty_days() -> None:
    assert RETENTION_DAYS == 30
    assert not is_expired(date(2026, 9, 2), TODAY)


def test_records_older_than_thirty_days_expire() -> None:
    assert is_expired(date(2026, 9, 1), TODAY)


def test_retention_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        is_expired(TODAY, TODAY, retention_days=0)
