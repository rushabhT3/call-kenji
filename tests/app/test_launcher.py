"""The guardrails at the door: who gets a call, and the polite line for who does not."""

import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from typing import cast

from kenji.app.events import CallEnded, CallStarted, TranscriptLine
from kenji.app.hub import EventHub
from kenji.app.launcher import CallAccounting, CallLauncher, CallRequest, CallRouting
from kenji.app.linking import LinkRegistry
from kenji.app.ports import CallRecorder
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.guardrails import CallLimits, UsageToday
from kenji.domain.outcome import CallOutcome
from tests.conversation.harness import (
    FixedClock,
    MemoryRecorder,
    TextTransport,
    build_text_kit,
)

LIMITS = CallLimits(max_call_seconds=300, daily_seconds=3_600, calls_per_caller_per_day=3)


class MemoryUsage:
    def __init__(self, calls_by_caller: int = 0) -> None:
        self.calls = calls_by_caller
        self.seconds: list[int] = []

    def usage_today(self, pool: str, caller_ref: str, day: date) -> UsageToday:  # noqa: ARG002
        return UsageToday(seconds_used=sum(self.seconds), calls_by_this_caller=self.calls)

    def record_call(self, pool: str, caller_ref: str, day: date) -> None:  # noqa: ARG002
        self.calls += 1

    def record_seconds(self, pool: str, day: date, seconds: int) -> None:  # noqa: ARG002
        self.seconds.append(seconds)


LATE = datetime(2026, 10, 2, 21, 10, tzinfo=JAPAN_STANDARD_TIME)


@dataclass(frozen=True)
class LauncherUnderTest:
    launcher: CallLauncher
    recorder: MemoryRecorder
    hub: EventHub


def launcher_for(clock: FixedClock, usage: MemoryUsage) -> LauncherUnderTest:
    text = build_text_kit([], clock)
    recorder, hub = MemoryRecorder(), EventHub()

    def make_recorder(_call_id: str, _day: date) -> CallRecorder:
        return recorder

    launcher = CallLauncher(
        text.kit,
        CallRouting(hub=hub, links=LinkRegistry(text.kit.clock)),
        CallAccounting(usage, make_recorder, {"phone": LIMITS, "browser": LIMITS}),
    )
    return LauncherUnderTest(launcher, recorder, hub)


async def _connected_call(launcher: CallLauncher, request: CallRequest) -> CallOutcome:
    transport = TextTransport()
    task = asyncio.create_task(launcher.run(transport, request))
    await asyncio.sleep(0.2)
    await transport.connect()
    await asyncio.sleep(0.5)
    await transport.disconnect()
    return await asyncio.wait_for(task, 8)


async def _refused_call(
    clock: FixedClock, usage: MemoryUsage
) -> tuple[CallOutcome, MemoryRecorder]:
    under_test = launcher_for(clock, usage)
    transport = TextTransport()
    task = asyncio.create_task(under_test.launcher.run(transport, CallRequest("phone", "caller-a")))
    await asyncio.sleep(0.2)
    await transport.connect()
    return await asyncio.wait_for(task, 8), under_test.recorder


async def test_call_at_21_10_japan_time_is_refused_politely() -> None:
    outcome, recorder = await _refused_call(FixedClock(LATE), MemoryUsage())

    assert outcome is CallOutcome.OUTSIDE_CALLING_HOURS
    line = cast(TranscriptLine, recorder.of_type("transcript")[0])
    assert "受付時間外" in line.ja
    assert cast(CallEnded, recorder.of_type("call_ended")[0]).outcome is outcome
    assert [record.entry.kind for record in recorder.records()] == ["call_refused"]


async def test_fourth_call_of_the_day_from_one_caller_is_refused() -> None:
    usage = MemoryUsage(calls_by_caller=3)

    outcome, recorder = await _refused_call(FixedClock(), usage)

    assert outcome is CallOutcome.DAILY_LIMIT_REACHED
    assert "上限" in cast(TranscriptLine, recorder.of_type("transcript")[0]).ja
    assert usage.calls == 3


async def test_admitted_call_is_counted_shown_to_its_tab_and_then_forgotten() -> None:
    usage = MemoryUsage()
    under_test = launcher_for(FixedClock(), usage)
    tab = under_test.hub.subscribe("tab")

    outcome = await _connected_call(
        under_test.launcher, CallRequest("browser", "caller-a", viewer_id="tab")
    )

    assert outcome is CallOutcome.IDENTITY_NOT_VERIFIED
    assert (usage.calls, usage.seconds) == (1, [0])
    assert under_test.recorder.is_closed
    assert not tab.empty()
    call_id = cast(CallStarted, under_test.recorder.of_type("call_started")[0]).call_id
    late_tab = under_test.hub.subscribe("late-tab")
    assert under_test.hub.link(call_id, "late-tab")
    assert late_tab.empty()


async def test_late_phone_call_is_refused_before_it_is_answered() -> None:
    under_test = launcher_for(FixedClock(LATE), MemoryUsage())

    line = await under_test.launcher.screen(CallRequest("phone", "caller-a", call_id="CA1"))

    assert line is not None
    assert "受付時間外" in line.ja
    recorder = under_test.recorder
    assert [record.entry.kind for record in recorder.records()] == ["call_refused"]
    ended = cast(CallEnded, recorder.of_type("call_ended")[0])
    assert ended.outcome is CallOutcome.OUTSIDE_CALLING_HOURS
    assert recorder.is_closed


async def test_phone_call_inside_the_limits_is_answered_without_a_record_yet() -> None:
    usage = MemoryUsage()
    under_test = launcher_for(FixedClock(), usage)

    line = await under_test.launcher.screen(CallRequest("phone", "caller-a", call_id="CA1"))

    assert line is None
    assert under_test.recorder.events == []
    assert usage.calls == 0
