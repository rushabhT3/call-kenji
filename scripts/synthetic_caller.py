"""A synthetic caller for Kenji: a Cartesia voice speaking over a real WebRTC connection.

It hears Kenji's audio, follows the private viewer feed, and can tell when Kenji has finished
a turn. Used by scripts/voice_check.py.
"""

import asyncio
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

import httpx
import numpy as np
import websockets
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioFrame

from kenji.adapters.content import load_script
from kenji.config import Settings

CALLER_VOICE_ID = "498e7f37-7fa3-4e2c-b8e2-8b6e9276f956"  # Aiko: a Japanese voice unlike Kenji's
CARTESIA_VERSION = "2026-03-01"
SAMPLE_RATE = 48_000
FRAME_SAMPLES = SAMPLE_RATE // 50
FRAME_BYTES = FRAME_SAMPLES * 2
VOICE_RMS = 300.0
NEW_UTTERANCE_GAP_SECS = 0.6
KENJI_DONE_SILENCE_SECS = 4.0  # Muse pauses 3-6 s mid-answer while a tool runs
CALL_TIMEOUT_SECS = 240.0
POLL_SECS = 0.05


class CallerMicrophone(MediaStreamTrack):
    """Plays queued speech in real time, and silence in between, like a phone held to a mouth."""

    kind = "audio"

    def __init__(self) -> None:
        super().__init__()
        self._pending = bytearray()
        self._samples_sent = 0
        self._started_at: float | None = None
        self.stopped_speaking_at = 0.0
        self.sent = bytearray()

    @property
    def started_at(self) -> float | None:
        """When the first frame left, on the monotonic clock: where `sent` begins."""
        return self._started_at

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
        padded = chunk.ljust(FRAME_BYTES, b"\0")
        self.sent.extend(padded)
        frame = AudioFrame(format="s16", layout="mono", samples=FRAME_SAMPLES)
        frame.planes[0].update(padded)
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
    """What the caller hears: when Kenji starts and stops making sound, and the sound itself."""

    last_voice_at: float = 0.0
    onsets: list[float] = field(default_factory=list)
    heard: list[tuple[int, np.ndarray]] = field(default_factory=list)
    first_heard_at: float | None = None
    first_pts: int | None = None

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

    def _keep(self, frame: AudioFrame) -> None:
        """Keep the audio at its place in the stream, as mono 16-bit samples."""
        channels = len(frame.layout.channels)
        mono = frame.to_ndarray().reshape(-1, channels).mean(axis=1).astype(np.int16)
        pts = frame.pts if frame.pts is not None else sum(len(kept) for _, kept in self.heard)
        if self.first_pts is None:
            self.first_pts, self.first_heard_at = pts, time.monotonic()
        self.heard.append((pts - self.first_pts, mono))

    def _hear(self, frame: AudioFrame) -> None:
        self._keep(frame)
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
    arrived_at: list[float] = field(default_factory=list)

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

    def kenji_answers(self, acknowledgement: str) -> int:
        """Kenji's lines so far, leaving out the instant 「はい、」 that precedes a model answer."""
        return sum(1 for line in self.kenji_lines() if line != acknowledgement)

    def kenji_lines(self) -> list[str]:
        lines = self.of_type("transcript")
        return [
            str(line["ja"]) for line in lines if line["speaker"] == "kenji" and line["is_final"]
        ]


class CallerVoice:
    """Speaks the caller's lines with Cartesia, once per distinct line."""

    def __init__(self, settings: Settings, http: httpx.AsyncClient) -> None:
        self._api_key = settings.cartesia_api_key.get_secret_value()
        script = load_script(settings.content_dir / "script_ja.yaml")
        self.acknowledgement = script.lines.acknowledgement.ja
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
    acknowledgement: str = ""

    def kenji_has_finished(self, since: float) -> bool:
        has_spoken = self.kenji.last_voice_at > since
        quiet_for = time.monotonic() - self.kenji.last_voice_at
        return has_spoken and quiet_for >= KENJI_DONE_SILENCE_SECS

    async def say(self, pcm: bytes) -> float:
        self.microphone.say(pcm)
        await until(lambda: not self.microphone.is_speaking, CALL_TIMEOUT_SECS)
        return self.microphone.stopped_speaking_at

    def note_reply_time(self, stopped_at: float) -> None:
        onset = self.kenji.first_onset_after(stopped_at)
        if onset is not None:
            self.mouth_to_ear_ms.append((onset - stopped_at) * 1000)


async def until(condition: Callable[[], bool], timeout_secs: float) -> bool:
    deadline = time.monotonic() + timeout_secs
    while not condition():
        if time.monotonic() > deadline:
            return False
        await asyncio.sleep(POLL_SECS)
    return True


async def follow_feed(base: str, feed: ViewerFeed, ready: asyncio.Event) -> None:
    async with websockets.connect(f"ws://{base}/ws/viewer") as socket_:
        async for raw in socket_:
            message = json.loads(raw)
            if message.get("type") == "viewer_ready":
                feed.viewer_id = message["viewer_id"]
                ready.set()
            else:
                feed.events.append(message)
                feed.arrived_at.append(time.monotonic())


async def dial(base: str, feed: ViewerFeed, http: httpx.AsyncClient) -> LiveCall:
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
