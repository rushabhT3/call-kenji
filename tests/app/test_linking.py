from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest

from kenji.app.linking import CODE_TTL, MAX_FAILED_ATTEMPTS_PER_CALL, LinkRegistry, random_code


class StepClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 2, 6, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


def _codes(*codes: str) -> Iterator[str]:
    yield from codes


@pytest.fixture
def clock() -> StepClock:
    return StepClock()


def test_code_links_the_call_to_the_tab_that_showed_it(clock: StepClock) -> None:
    registry = LinkRegistry(clock)
    code_a = registry.issue("tab-a")
    registry.issue("tab-b")

    assert registry.redeem("call-1", code_a) == "tab-a"


def test_code_is_single_use(clock: StepClock) -> None:
    registry = LinkRegistry(clock)
    code = registry.issue("tab-a")
    registry.redeem("call-1", code)

    assert registry.redeem("call-2", code) is None


def test_code_expires(clock: StepClock) -> None:
    registry = LinkRegistry(clock)
    code = registry.issue("tab-a")
    clock.advance(CODE_TTL + timedelta(seconds=1))

    assert registry.redeem("call-1", code) is None


def test_call_is_locked_out_after_repeated_wrong_codes(clock: StepClock) -> None:
    codes = _codes("1111", "2222")
    registry = LinkRegistry(clock, code_source=lambda: next(codes))
    registry.issue("tab-a")
    real_code = registry.issue("tab-b")
    for _ in range(MAX_FAILED_ATTEMPTS_PER_CALL):
        registry.redeem("call-1", "9999")

    assert registry.redeem("call-1", real_code) is None
    assert registry.redeem("call-2", real_code) == "tab-b"


def test_a_renewed_code_leaves_the_previous_one_working_until_it_expires(
    clock: StepClock,
) -> None:
    codes = _codes("1111", "2222")
    registry = LinkRegistry(clock, code_source=lambda: next(codes))
    first = registry.issue("tab-a")
    clock.advance(CODE_TTL / 2)
    registry.issue("tab-a")

    assert registry.redeem("call-1", first) == "tab-a"


def test_linking_a_tab_retires_its_other_codes(clock: StepClock) -> None:
    codes = _codes("1111", "2222")
    registry = LinkRegistry(clock, code_source=lambda: next(codes))
    first = registry.issue("tab-a")
    second = registry.issue("tab-a")
    registry.redeem("call-1", second)

    assert registry.redeem("call-2", first) is None


def test_codes_never_collide_with_a_pending_code(clock: StepClock) -> None:
    codes = _codes("1234", "1234", "5678")
    registry = LinkRegistry(clock, code_source=lambda: next(codes))

    assert {registry.issue("tab-a"), registry.issue("tab-b")} == {"1234", "5678"}


def test_random_code_is_four_digits() -> None:
    code = random_code()

    assert len(code) == 4
    assert code.isdigit()
