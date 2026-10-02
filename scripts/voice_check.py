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
import json
import socket
import statistics
import sys
import time
from collections import Counter
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import uvicorn
import websockets
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioFrame
from loguru import logger

from kenji.config import Settings
from kenji.container import build_kit, build_services
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.compliance import CheckStatus
from kenji.server import create_app, load_settings

CALLER_VOICE_ID = "498e7f37-7fa3-4e2c-b8e2-8b6e9276f956"  # Aiko: a Japanese voice unlike Kenji's
CARTESIA_VERSION = "2026-03-01"
SAMPLE_RATE = 48_000
FRAME_SAMPLES = SAMPLE_RATE // 50
FRAME_BYTES = FRAME_SAMPLES * 2
VOICE_RMS = 300.0
NEW_UTTERANCE_GAP_SECS = 0.6
KENJI_DONE_SILENCE_SECS = 2.5
CALL_TIMEOUT_SECS = 240.0
POLL_SECS = 0.05
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


class CallerMicrophone(MediaStreamTrack):
    """Plays queued speech in real time, and silence in between, like a phone held to a mouth."""

    kind = "audio"

    def __init__(self) -> None:
        super().__init__()
        self._pending = bytearray()
        self._samples_sent = 0
        self._started_at: float | None = None
        self.stopped_speaking_at = 0.0

    def say(self, pcm: bytes) -> None:
        self._pending.extend(pcm)

    @property
    def is_speaking(self) -> bool:
        return bool(self._pending)

    async def recv(self) -> AudioFrame:
        await self._wait_for_frame_time()
        chunk = bytes(self._pending[:FRAME_BYTES])
        del self._pending[:FRAME_BYTES]
        if chunk and not self._pending:
            self.stopped_speaking_at = time.monotonic()
        frame = AudioFrame(format="s16", layout="mono", samples=FRAME_SAMPLES)
        frame.planes[0].update(chunk.ljust(FRAME_BYTES, b"\0"))
        frame.sample_rate = SAMPLE_RATE
        frame.pts = self._samples_sent
        frame.time_base = Fraction(1, SAMPLE_RATE)
        self._samples_sent += FRAME_SAMPLES
        return frame

    async def _wait_for_frame_time(self) -> None:
        if self._started_at is None:
            self._started_at = time.monotonic()
        due = self._started_at + self._samples_sent / SAMPLE_RATE
        await asyncio.sleep(max(0.0, due - time.monotonic()))


@dataclass
class KenjiVoice:
    """What the caller hears: when Kenji starts and stops making sound."""

    last_voice_at: float = 0.0
    onsets: list[float] = field(default_factory=list)

    async def listen(self, track: MediaStreamTrack) -> None:
        while True:
            try:
                frame = await track.recv()
            except MediaStreamError:
                return
            if isinstance(frame, AudioFrame):
                self._hear(frame)

    def first_onset_after(self, moment: float) -> float | None:
        return next((onset for onset in self.onsets if onset > moment), None)

    def _hear(self, frame: AudioFrame) -> None:
        samples = frame.to_ndarray().astype(np.float64)
        if float(np.sqrt(np.mean(np.square(samples)))) < VOICE_RMS:
            return
        now = time.monotonic()
        if now - self.last_voice_at > NEW_UTTERANCE_GAP_SECS:
            self.onsets.append(now)
        self.last_voice_at = now


@dataclass
class ViewerFeed:
    """The private live feed the page would show, read as plain events."""

    viewer_id: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)

    def of_type(self, kind: str) -> list[dict[str, Any]]:
        return [event for event in self.events if event.get("type") == kind]

    @property
    def node(self) -> str:
        nodes = self.of_type("flow_node")
        return str(nodes[-1]["node"]) if nodes else ""

    @property
    def outcome(self) -> str | None:
        ended = self.of_type("call_ended")
        return str(ended[-1]["outcome"]) if ended else None

    def kenji_lines(self) -> list[str]:
        lines = self.of_type("transcript")
        return [
            str(line["ja"]) for line in lines if line["speaker"] == "kenji" and line["is_final"]
        ]


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


class CallerVoice:
    """Speaks the caller's lines with Cartesia, once per distinct line."""

    def __init__(self, settings: Settings, http: httpx.AsyncClient) -> None:
        self._api_key = settings.cartesia_api_key.get_secret_value()
        self._model = settings.cartesia_model
        self._http = http
        self._spoken: dict[str, bytes] = {}

    async def pcm(self, line: str) -> bytes:
        if line not in self._spoken:
            self._spoken[line] = await self._synthesize(line)
        return self._spoken[line]

    async def _synthesize(self, line: str) -> bytes:
        response = await self._http.post(
            "https://api.cartesia.ai/tts/bytes",
            headers={"X-API-Key": self._api_key, "Cartesia-Version": CARTESIA_VERSION},
            json={
                "model_id": self._model,
                "transcript": line,
                "voice": {"mode": "id", "id": CALLER_VOICE_ID},
                "language": "ja",
                "output_format": {
                    "container": "raw",
                    "encoding": "pcm_s16le",
                    "sample_rate": SAMPLE_RATE,
                },
            },
        )
        response.raise_for_status()
        return response.content


@dataclass
class LiveCall:
    microphone: CallerMicrophone
    kenji: KenjiVoice
    feed: ViewerFeed
    peer: RTCPeerConnection
    mouth_to_ear_ms: list[float] = field(default_factory=list)

    def kenji_has_finished(self, since: float) -> bool:
        has_spoken = self.kenji.first_onset_after(since) is not None
        quiet_for = time.monotonic() - self.kenji.last_voice_at
        return has_spoken and quiet_for >= KENJI_DONE_SILENCE_SECS

    async def say(self, pcm: bytes) -> float:
        self.microphone.say(pcm)
        await _until(lambda: not self.microphone.is_speaking, CALL_TIMEOUT_SECS)
        return self.microphone.stopped_speaking_at

    def note_reply_time(self, stopped_at: float) -> None:
        onset = self.kenji.first_onset_after(stopped_at)
        if onset is not None:
            self.mouth_to_ear_ms.append((onset - stopped_at) * 1000)


async def _until(condition: Callable[[], bool], timeout_secs: float) -> bool:
    deadline = time.monotonic() + timeout_secs
    while not condition():
        if time.monotonic() > deadline:
            return False
        await asyncio.sleep(POLL_SECS)
    return True


async def _follow_feed(base: str, feed: ViewerFeed, ready: asyncio.Event) -> None:
    async with websockets.connect(f"ws://{base}/ws/viewer") as socket_:
        async for raw in socket_:
            message = json.loads(raw)
            if message.get("type") == "viewer_ready":
                feed.viewer_id = message["viewer_id"]
                ready.set()
            else:
                feed.events.append(message)


async def _dial(base: str, feed: ViewerFeed, http: httpx.AsyncClient) -> LiveCall:
    peer = RTCPeerConnection()
    microphone, kenji = CallerMicrophone(), KenjiVoice()
    peer.addTrack(microphone)
    peer.createDataChannel("chat")
    listeners: list[asyncio.Task[None]] = []

    @peer.on("track")
    def on_track(track: MediaStreamTrack) -> None:
        if track.kind == "audio":
            listeners.append(asyncio.create_task(kenji.listen(track)))

    await peer.setLocalDescription(await peer.createOffer())
    offer = peer.localDescription
    body = {"sdp": offer.sdp, "type": offer.type, "requestData": {"viewer_id": feed.viewer_id}}
    answer = (await http.post(f"http://{base}/api/offer", json=body)).raise_for_status().json()
    await peer.setRemoteDescription(RTCSessionDescription(sdp=answer["sdp"], type=answer["type"]))
    return LiveCall(microphone, kenji, feed, peer)


def _turn_is_ours(call: LiveCall, since: float) -> Callable[[], bool]:
    return lambda: call.feed.outcome is not None or call.kenji_has_finished(since)


async def _converse(call: LiveCall, scenario: Scenario, voice: CallerVoice) -> None:
    turns_at: Counter[str] = Counter()
    last_line_ended = 0.0
    deadline = time.monotonic() + CALL_TIMEOUT_SECS
    while call.feed.outcome is None and time.monotonic() < deadline:
        is_ready = await _until(_turn_is_ours(call, last_line_ended), deadline - time.monotonic())
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
    following = asyncio.create_task(_follow_feed(base, feed, ready))
    await asyncio.wait_for(ready.wait(), 10)
    async with httpx.AsyncClient(timeout=30) as http:
        call = await _dial(base, feed, http)
    try:
        await _converse(call, scenario, voice)
    finally:
        await call.peer.close()
        await _until(lambda: feed.outcome is not None and bool(feed.of_type("audit")), 20)
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
    await _until(lambda: server.started, 20)
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
