"""A slow first answer is raced against a second request; only the winner is ever read."""

import asyncio
from collections.abc import AsyncIterator

import pytest

from kenji.adapters.hedging import first_to_start
from kenji.adapters.openai_models import ChatEndpoint, HedgedOpenAILLMService, OpenAITalker

HEDGE_AFTER_SECS = 0.05
SLOW_SECS = 0.4


class FakeStream:
    """A stream we own: waits, then yields its items or fails, and records being closed."""

    def __init__(
        self, items: list[str], first_delay: float = 0.0, error: Exception | None = None
    ) -> None:
        self._items = items
        self._first_delay = first_delay
        self._error = error
        self.is_closed = False

    def __aiter__(self) -> AsyncIterator[str]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[str]:
        await asyncio.sleep(self._first_delay)
        if self._error is not None:
            raise self._error
        for item in self._items:
            yield item

    async def close(self) -> None:
        self.is_closed = True


class Starter:
    """Hands out prepared streams in order and counts how many requests were made."""

    def __init__(self, *streams: FakeStream) -> None:
        self._streams = list(streams)
        self.requests = 0

    async def __call__(self) -> FakeStream:
        stream = self._streams[self.requests]
        self.requests += 1
        return stream


async def _read(starter: Starter) -> list[str]:
    hedged = await first_to_start(starter, HEDGE_AFTER_SECS)
    return [item async for item in hedged]


async def test_a_fast_first_answer_never_starts_a_second_request() -> None:
    starter = Starter(FakeStream(["a", "b"]), FakeStream(["x"]))

    assert await _read(starter) == ["a", "b"]
    assert starter.requests == 1


async def test_a_slow_first_answer_loses_to_a_faster_second_one() -> None:
    slow, fast = FakeStream(["slow"], first_delay=SLOW_SECS), FakeStream(["fast-1", "fast-2"])
    starter = Starter(slow, fast)

    assert await _read(starter) == ["fast-1", "fast-2"]
    assert starter.requests == 2
    assert slow.is_closed


async def test_a_first_answer_that_fails_at_once_fails_the_call() -> None:
    starter = Starter(FakeStream([], error=RuntimeError("bad request")), FakeStream(["x"]))

    with pytest.raises(RuntimeError, match="bad request"):
        await _read(starter)
    assert starter.requests == 1


async def test_when_one_racer_fails_the_other_still_answers() -> None:
    slow = FakeStream(["slow-but-fine"], first_delay=SLOW_SECS)
    starter = Starter(slow, FakeStream([], error=RuntimeError("second failed")))

    assert await _read(starter) == ["slow-but-fine"]
    assert starter.requests == 2


async def test_when_both_racers_fail_the_earliest_failure_is_raised() -> None:
    first = FakeStream([], first_delay=SLOW_SECS, error=RuntimeError("first failed"))
    starter = Starter(first, FakeStream([], error=RuntimeError("second failed")))

    with pytest.raises(RuntimeError, match="second failed"):
        await _read(starter)


async def test_closing_the_hedged_stream_closes_the_winner() -> None:
    winner = FakeStream(["a"])
    hedged = await first_to_start(Starter(winner), HEDGE_AFTER_SECS)

    await hedged.close()

    assert winner.is_closed


async def test_an_empty_answer_reads_as_empty() -> None:
    assert await _read(Starter(FakeStream([]))) == []


def test_the_talker_hedges_its_requests() -> None:
    endpoint = ChatEndpoint(api_key="dummy", base_url=None, reasoning_effort=None, temperature=None)

    talker = OpenAITalker(endpoint, "test-model").create("You are Kenji.")

    assert isinstance(talker, HedgedOpenAILLMService)
