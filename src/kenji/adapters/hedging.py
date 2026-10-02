"""Hedged streams: if an answer is slow to start, ask again and keep whichever starts first.

Only the winner is ever read, so a duplicate request can never produce a second reply or a
second tool call. Every loser is cancelled and closed.
"""

import asyncio
import inspect
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from loguru import logger

type StreamStarter[T] = Callable[[], Awaitable[AsyncIterable[T]]]


@dataclass(frozen=True, slots=True)
class _Opened[T]:
    stream: AsyncIterable[T]
    items: AsyncIterator[T]
    first: tuple[T] | tuple[()]

    async def close(self) -> None:
        await _call_if_present(self.items, "aclose")
        if not await _call_if_present(self.stream, "close"):
            await _call_if_present(self.stream, "aclose")


async def _call_if_present(target: object, method: str) -> bool:
    closer = getattr(target, method, None)
    if closer is None:
        return False
    result = closer()
    if inspect.isawaitable(result):
        await result
    return True


async def _open[T](start: StreamStarter[T]) -> _Opened[T]:
    stream = await start()
    items = aiter(stream)
    try:
        first: tuple[T] | tuple[()] = (await anext(items),)
    except StopAsyncIteration:
        first = ()
    except BaseException:
        await _Opened(stream, items, ()).close()
        raise
    return _Opened(stream, items, first)


class HedgedStream[T]:
    """The winning stream, with the first item it was raced on replayed ahead of the rest."""

    def __init__(self, opened: _Opened[T]) -> None:
        self._opened = opened

    def __aiter__(self) -> AsyncIterator[T]:
        return self._items()

    async def _items(self) -> AsyncIterator[T]:
        for item in self._opened.first:
            yield item
        async for item in self._opened.items:
            yield item

    async def close(self) -> None:
        await self._opened.close()


async def _first_success[T](attempts: list[asyncio.Task[_Opened[T]]]) -> _Opened[T]:
    """The earliest attempt to start, or the earliest failure if every attempt fails."""
    pending = set(attempts)
    failures: list[BaseException] = []
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        settled = [task for task in attempts if task in done]
        winners = [task.result() for task in settled if task.exception() is None]
        failures.extend(error for task in settled if (error := task.exception()) is not None)
        if winners:
            for loser in winners[1:]:
                await loser.close()
            return winners[0]
    raise failures[0]


async def _cancel_unfinished[T](attempts: list[asyncio.Task[_Opened[T]]]) -> None:
    unfinished = [task for task in attempts if not task.done()]
    for task in unfinished:
        task.cancel()
    for outcome in await asyncio.gather(*unfinished, return_exceptions=True):
        if isinstance(outcome, _Opened):
            await outcome.close()


async def first_to_start[T](start: StreamStarter[T], hedge_after_secs: float) -> HedgedStream[T]:
    """Start a stream; if its first item is late, race a second identical one against it.

    A first stream that fails before the hedge fires fails the call at once. Once two are
    racing, a failure in one leaves the other to win, and only both failing raises.
    """
    attempts = [asyncio.create_task(_open(start))]
    try:
        done, _ = await asyncio.wait(attempts, timeout=hedge_after_secs)
        if done:
            return HedgedStream(attempts[0].result())
        logger.info("model slow to start answering; racing a second request")
        attempts.append(asyncio.create_task(_open(start)))
        return HedgedStream(await _first_success(attempts))
    finally:
        await _cancel_unfinished(attempts)
