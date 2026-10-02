"""Write a voice-check call as the page's demo replay: its events and both sides of its audio.

The caller is a synthetic Cartesia voice, so nobody's voice is kept. Calls to the live
server never keep audio; this is a development script run on one machine.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import av
import numpy as np
from synthetic_caller import SAMPLE_RATE, CallerMicrophone, KenjiVoice, ViewerFeed

ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = ROOT / "web" / "public" / "demo"
AUDIO_NAME = "call.m4a"
AUDIO_BIT_RATE = 40_000
FRAME_SAMPLES = SAMPLE_RATE // 50
TAIL_SECS = 1.0


@dataclass(frozen=True)
class CallAudio:
    microphone: CallerMicrophone
    kenji: KenjiVoice


def _timeline(feed: ViewerFeed) -> tuple[float, list[dict[str, Any]]]:
    """The events from the call's start, timed from when the page heard it had started."""
    start = next(i for i, event in enumerate(feed.events) if event.get("type") == "call_started")
    started_at = feed.arrived_at[start]
    timed = zip(feed.events[start:], feed.arrived_at[start:], strict=True)
    events = [{"offset_ms": round((at - started_at) * 1000), "event": event} for event, at in timed]
    return started_at, events


def _add(mix: np.ndarray, samples: np.ndarray, start: int) -> None:
    if start < 0:
        samples, start = samples[-start:], 0
    end = min(len(mix), start + len(samples))
    if end > start:
        mix[start:end] += samples[: end - start]


def _mixed(audio: CallAudio, started_at: float, length_secs: float) -> np.ndarray:
    """Both sides on one track, each sample at its moment on the call's clock."""
    mix = np.zeros(int((length_secs + TAIL_SECS) * SAMPLE_RATE), dtype=np.int32)
    microphone, kenji = audio.microphone, audio.kenji
    if microphone.started_at is not None:
        caller = np.frombuffer(bytes(microphone.sent), dtype=np.int16)
        _add(mix, caller, round((microphone.started_at - started_at) * SAMPLE_RATE))
    if kenji.first_heard_at is not None:
        first = round((kenji.first_heard_at - started_at) * SAMPLE_RATE)
        for position, samples in kenji.heard:
            _add(mix, samples, first + position)
    return np.clip(mix, -32768, 32767).astype(np.int16)


def _encode(samples: np.ndarray, path: Path) -> None:
    container = av.open(str(path), mode="w", format="mp4")
    stream = container.add_stream("aac", rate=SAMPLE_RATE, layout="mono")
    stream.bit_rate = AUDIO_BIT_RATE
    for start in range(0, len(samples), FRAME_SAMPLES):
        chunk = samples[start : start + FRAME_SAMPLES].reshape(1, -1)
        frame = av.AudioFrame.from_ndarray(chunk, format="s16", layout="mono")
        frame.sample_rate = SAMPLE_RATE
        for packet in stream.encode(frame):
            container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()


def write_demo_recording(feed: ViewerFeed, audio: CallAudio) -> Path:
    started_at, events = _timeline(feed)
    length_secs = events[-1]["offset_ms"] / 1000
    _encode(_mixed(audio, started_at, length_secs), DEMO_DIR / AUDIO_NAME)
    recording = {
        "source": "voice check: Kenji and a synthetic Cartesia caller over WebRTC",
        "recorded_on": datetime.now().astimezone().date().isoformat(),
        "audio": AUDIO_NAME,
        "events": events,
    }
    path = DEMO_DIR / "call.json"
    path.write_text(json.dumps(recording, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path
