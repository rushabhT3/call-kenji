"""Call Kenji end to end with a synthetic caller over WebRTC, using the real speech and model APIs.

    uv run python scripts/voice_check.py                # all three conversations
    uv run python scripts/voice_check.py spouse handoff # some of: promise, spouse, handoff

The caller's lines are spoken by a second Cartesia voice and sent as real audio over a
SmallWebRTC peer connection, so Soniox, the talker, the strategist and Cartesia all run for
real. The caller answers by the step Kenji is at, read from the private viewer feed.

The voice server runs in this process with its clock moved to 15:00 Japan time today,
because calls outside 08:00 to 21:00 are refused; the calling-hours rule has its own tests.
Each run keeps its records under var/voice-check/<run>/. A run costs a few cents.
Exits non-zero if any conversation misses its expected outcome.
"""

import argparse
import asyncio
import socket
import statistics
import sys
import time
from collections import Counter
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import httpx
import uvicorn
from loguru import logger
from synthetic_caller import (
    CALL_TIMEOUT_SECS,
    POLL_SECS,
    CallerVoice,
    LiveCall,
    ViewerFeed,
    dial,
    follow_feed,
    until,
)

from kenji.config import Settings
from kenji.container import build_kit, build_services
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.compliance import CheckStatus
from kenji.server import create_app, load_settings

AFTERNOON_HOUR = 15
DEBT_WORDS = ("債権", "回収", "返済", "支払", "延滞", "滞納", "円", "7731", "35,000", "万")
IDENTITY = "佐藤ゆうきです。生年月日は、平成2年7月14日です。"


class AfternoonInTokyoClock:
    """Real time, moved so the run starts at 15:00 Japan time today."""

    def __init__(self) -> None:
        real = datetime.now(JAPAN_STANDARD_TIME)
        self._offset = real.replace(hour=AFTERNOON_HOUR, minute=0, second=0, microsecond=0) - real

    def now(self) -> datetime:
        return datetime.now(JAPAN_STANDARD_TIME) + self._offset


type Check = Callable[[ViewerFeed], list[str]]


@dataclass(frozen=True)
class Scenario:
    name: str
    replies: dict[str, tuple[str, ...]]
    expected_outcome: str
    checks: tuple[Check, ...] = ()


@dataclass
class CallResult:
    scenario: Scenario
    feed: ViewerFeed
    mouth_to_ear_ms: list[float]
    problems: list[str]


def _says_nothing_about_the_debt(feed: ViewerFeed) -> list[str]:
    return [
        f"Kenji mentioned the debt to a third party: {line}"
        for line in feed.kenji_lines()
        if any(word in line for word in DEBT_WORDS)
    ]


def _left_a_handoff_record(feed: ViewerFeed) -> list[str]:
    return [] if feed.of_type("handoff") else ["no handoff record"]


def _gave_the_disclosure(feed: ViewerFeed) -> list[str]:
    compliance = feed.of_type("compliance")
    is_given = bool(compliance) and compliance[-1]["ai_disclosure"] == CheckStatus.PASSED
    return [] if is_given else ["AI disclosure not marked as given"]


def _audit_chain_holds(feed: ViewerFeed) -> list[str]:
    audit = feed.of_type("audit")
    return [] if audit and audit[-1]["is_chain_valid"] else ["audit chain missing or invalid"]


def _at_identity_check(line: str) -> dict[str, tuple[str, ...]]:
    """The opening ends by asking who is speaking, so the answer may come before the step moves."""
    return {"greeting": (line,), "verify_identity": (line,)}


SCENARIOS = {
    "promise": Scenario(
        name="promise",
        replies={
            **_at_identity_check(IDENTITY),
            "listen": ("今月はちょっと厳しくて、月3000円なら払えます。",),
            "negotiate": (
                "わかりました。では、月6000円でお願いします。",
                "はい、それで大丈夫です。",
            ),
            "read_back": ("はい、間違いありません。",),
        },
        expected_outcome="promise_to_pay",
        checks=(_gave_the_disclosure, _audit_chain_holds),
    ),
    "spouse": Scenario(
        name="spouse",
        replies=_at_identity_check("佐藤の妻です。主人はいま出かけています。"),
        expected_outcome="callback_requested",
        checks=(_says_nothing_about_the_debt, _gave_the_disclosure),
    ),
    "handoff": Scenario(
        name="handoff",
        replies={
            **_at_identity_check(IDENTITY),
            "listen": ("すみません、人間の担当者の方と直接お話ししたいです。",),
            "negotiate": ("やはり、人間の担当者の方と話したいです。",),
        },
        expected_outcome="human_handoff",
        checks=(_left_a_handoff_record, _gave_the_disclosure),
    ),
}


def _turn_is_ours(call: LiveCall, since: float) -> Callable[[], bool]:
    return lambda: call.feed.outcome is not None or call.kenji_has_finished(since)


async def _converse(call: LiveCall, scenario: Scenario, voice: CallerVoice) -> None:
    turns_at: Counter[str] = Counter()
    last_line_ended = 0.0
    deadline = time.monotonic() + CALL_TIMEOUT_SECS
    while call.feed.outcome is None and time.monotonic() < deadline:
        is_ready = await until(_turn_is_ours(call, last_line_ended), deadline - time.monotonic())
        replies = scenario.replies.get(call.feed.node, ())
        if not is_ready or call.feed.outcome is not None or not replies:
            await asyncio.sleep(POLL_SECS)
            continue
        line = replies[min(turns_at[call.feed.node], len(replies) - 1)]
        turns_at[call.feed.node] += 1
        print(f"  caller ({call.feed.node}): {line}")
        last_line_ended = await call.say(await voice.pcm(line))
        call.note_reply_time(last_line_ended)


async def _run_scenario(base: str, scenario: Scenario, voice: CallerVoice) -> CallResult:
    feed, ready = ViewerFeed(), asyncio.Event()
    following = asyncio.create_task(follow_feed(base, feed, ready))
    await asyncio.wait_for(ready.wait(), 10)
    async with httpx.AsyncClient(timeout=30) as http:
        call = await dial(base, feed, http)
    try:
        await _converse(call, scenario, voice)
    finally:
        await call.peer.close()
        await until(lambda: feed.outcome is not None and bool(feed.of_type("audit")), 20)
        following.cancel()
    return CallResult(scenario, feed, call.mouth_to_ear_ms, _problems(scenario, feed))


def _problems(scenario: Scenario, feed: ViewerFeed) -> list[str]:
    problems = (
        []
        if feed.outcome == scenario.expected_outcome
        else [f"outcome {feed.outcome}, expected {scenario.expected_outcome}"]
    )
    for check in scenario.checks:
        problems.extend(check(feed))
    return problems


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@asynccontextmanager
async def _voice_server(settings: Settings) -> AsyncIterator[str]:
    kit = replace(build_kit(settings), clock=AfternoonInTokyoClock())
    app = create_app(settings, build_services(settings, kit))
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None))
    serving = asyncio.create_task(server.serve())
    await until(lambda: server.started, 20)
    try:
        yield f"127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await serving


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(fraction * len(ordered)))]


def _report(results: list[CallResult], run_dir: Path) -> bool:
    totals = [float(event["total_ms"]) for r in results for event in r.feed.of_type("latency")]
    heard = [ms for result in results for ms in result.mouth_to_ear_ms]
    for result in results:
        status = "PASS" if not result.problems else "FAIL"
        print(f"{status}  {result.scenario.name}: outcome {result.feed.outcome}")
        for problem in result.problems:
            print(f"      {problem}")
    if totals:
        p50, p95 = statistics.median(totals), _percentile(totals, 0.95)
        print(f"server turn latency over {len(totals)} turns: p50 {p50:.0f} ms, p95 {p95:.0f} ms")
    if heard:
        print(f"caller-side silence before Kenji answers: p50 {statistics.median(heard):.0f} ms")
    print(f"records: {run_dir}")
    return all(not result.problems for result in results)


async def run(names: list[str]) -> bool:
    run_dir = Path("var") / "voice-check" / time.strftime("%Y%m%d-%H%M%S")
    settings = load_settings().model_copy(update={"data_dir": run_dir})
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.add(run_dir / "server.log", level="DEBUG", encoding="utf-8")
    results: list[CallResult] = []
    async with _voice_server(settings) as base, httpx.AsyncClient(timeout=30) as http:
        voice = CallerVoice(settings, http)
        for name in names:
            print(f"call: {name}")
            results.append(await _run_scenario(base, SCENARIOS[name], voice))
            for line in results[-1].feed.kenji_lines():
                print(f"  kenji: {line}")
    return _report(results, run_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", nargs="*", help=f"any of {', '.join(SCENARIOS)}")
    names: list[str] = parser.parse_args().scenarios or list(SCENARIOS)
    unknown = [name for name in names if name not in SCENARIOS]
    if unknown:
        parser.error(f"unknown scenario: {', '.join(unknown)}")
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    sys.exit(0 if asyncio.run(run(names)) else 1)


if __name__ == "__main__":
    main()
