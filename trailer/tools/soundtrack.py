"""Compose the trailer's soundtrack, locked to src/timeline.json, and cut the dialogue clips.

Everything is synthesised here: drone, clock ticks, heartbeat, braams, whooshes, hits, a string
ostinato, the riser, the final impact and the sparkles. The dialogue is Kenji's and the caller's
real voices from the recorded demo call. The music ducks under every line.

    uv run --with scipy python trailer/tools/soundtrack.py
"""

import json
import wave
from pathlib import Path

import numpy as np
from scipy import signal
from voice_segments import CALL_AUDIO, decode

ROOT = Path(__file__).resolve().parents[1]
TIMELINE = json.loads((ROOT / "src" / "timeline.json").read_text(encoding="utf-8"))
PUBLIC = ROOT / "public"
RATE = 48_000
DURATION = TIMELINE["durationSecs"]
RNG = np.random.default_rng(7)

D1, D2, F2, A2, D3, F3, A3, C4, D4, FS3 = 36.71, 73.42, 87.31, 110.0, 146.83, 174.61, 220.0, 261.63, 293.66, 185.0


def seconds(count: float) -> np.ndarray:
    return np.arange(int(count * RATE)) / RATE


def lowpass(x: np.ndarray, cutoff: float, order: int = 4) -> np.ndarray:
    return signal.sosfilt(signal.butter(order, cutoff, "low", fs=RATE, output="sos"), x, axis=0)


def highpass(x: np.ndarray, cutoff: float, order: int = 4) -> np.ndarray:
    return signal.sosfilt(signal.butter(order, cutoff, "high", fs=RATE, output="sos"), x, axis=0)


def bandpass(x: np.ndarray, low: float, high: float) -> np.ndarray:
    return signal.sosfilt(signal.butter(2, [low, high], "band", fs=RATE, output="sos"), x, axis=0)


def saw(freq: float | np.ndarray, length: float, detune: float = 0.0) -> np.ndarray:
    t = seconds(length)
    phase = np.cumsum(np.broadcast_to(freq * (1 + detune), t.shape)) / RATE
    return signal.sawtooth(2 * np.pi * phase)


def sine(freq: float | np.ndarray, length: float) -> np.ndarray:
    t = seconds(length)
    phase = np.cumsum(np.broadcast_to(freq, t.shape)) / RATE
    return np.sin(2 * np.pi * phase)


def noise(length: float) -> np.ndarray:
    return RNG.standard_normal(int(length * RATE))


def decay(length: float, time_constant: float, attack: float = 0.004) -> np.ndarray:
    t = seconds(length)
    return np.minimum(t / attack, 1.0) * np.exp(-t / time_constant)


def stereo(x: np.ndarray, pan: float = 0.0) -> np.ndarray:
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * left, x * right], axis=1) * np.sqrt(2)


def reverb(x: np.ndarray, length: float, mix: float, darkness: float = 5000.0) -> np.ndarray:
    tail = seconds(length)
    impulse = np.stack([noise(length), noise(length)], axis=1) * np.exp(-tail / (length / 5))[:, None]
    impulse = lowpass(impulse, darkness)
    impulse /= np.abs(impulse).sum(axis=0).max() / 6
    wet = np.stack([signal.fftconvolve(x[:, side], impulse[:, side]) for side in (0, 1)], axis=1)
    dry = np.vstack([x, np.zeros((len(wet) - len(x), 2))])
    return dry * (1 - mix) + wet * mix


class Mix:
    def __init__(self) -> None:
        self.bed = np.zeros((int((DURATION + 6) * RATE), 2))
        self.voice = np.zeros_like(self.bed)

    def add(self, sound: np.ndarray, at: float, gain: float = 1.0, *, into: str = "bed") -> None:
        track = self.bed if into == "bed" else self.voice
        start = int(at * RATE)
        end = min(start + len(sound), len(track))
        track[start:end] += sound[: end - start] * gain


def braam(length: float = 3.6) -> np.ndarray:
    tone = sum(saw(f, length, d) for f, d in [(D2, 0), (D2, 0.004), (A2, -0.003), (D3, 0.002), (F3, -0.002)])
    tone = np.tanh(2.5 * tone / 3)
    bright, dark = lowpass(tone, 2600), lowpass(tone, 420)
    t = seconds(length)
    opening = np.clip(1 - t / 0.5, 0, 1)
    body = (bright * opening + dark * (1 - opening)) * decay(length, 1.4, 0.03)
    sub = sine(D1, length) * decay(length, 1.8, 0.02) * 0.9
    return reverb(stereo(body * 0.7 + sub), 3.0, 0.35, 2500)


def boom(length: float = 2.5, start: float = 120.0, end: float = 32.0) -> np.ndarray:
    t = seconds(length)
    sweep = end + (start - end) * np.exp(-t / 0.18)
    body = sine(sweep, length) * decay(length, 0.7, 0.003)
    thump = lowpass(noise(length), 180) * decay(length, 0.12) * 0.6
    return reverb(stereo(body + thump), 2.5, 0.25, 1500)


def hit(length: float = 1.2) -> np.ndarray:
    t = seconds(length)
    kick = sine(45 + 120 * np.exp(-t / 0.03), length) * decay(length, 0.22)
    crack = highpass(noise(length), 1800) * decay(length, 0.06) * 0.5
    return reverb(stereo(kick + crack), 1.2, 0.2, 6000)


def whoosh(length: float = 0.75, rising: bool = True) -> np.ndarray:
    raw = noise(length)
    blocks = 24
    edges = np.linspace(0, len(raw), blocks + 1, dtype=int)
    centres = np.geomspace(300, 4200, blocks) if rising else np.geomspace(4200, 300, blocks)
    swept = np.concatenate(
        [bandpass(raw[a:b], c * 0.6, min(c * 1.6, 20_000)) for a, b, c in zip(edges[:-1], edges[1:], centres)]
    )
    shape = np.sin(np.linspace(0, np.pi, len(swept))) ** 2
    out = swept * shape * 2.2
    pan = np.linspace(-0.7, 0.7, len(out))
    return np.stack([out * np.cos((pan + 1) * np.pi / 4), out * np.sin((pan + 1) * np.pi / 4)], axis=1) * 1.4


def tick(high: bool) -> np.ndarray:
    length = 0.25
    click = sine(2600 if high else 1900, length) * decay(length, 0.012, 0.0005)
    click += highpass(noise(length), 4000) * decay(length, 0.004, 0.0002) * 0.6
    return reverb(stereo(click * 0.5), 0.6, 0.25)


def heartbeat() -> np.ndarray:
    length = 0.6
    t = seconds(length)
    beat = sine(52 + 20 * np.exp(-t / 0.02), length) * decay(length, 0.09)
    second = np.zeros_like(beat)
    offset = int(0.22 * RATE)
    second[offset:] = beat[: len(beat) - offset] * 0.6
    return stereo(lowpass(beat + second, 220))


def pluck(freq: float, length: float = 0.22) -> np.ndarray:
    tone = saw(freq, length) + saw(freq, length, 0.006) * 0.7 + saw(freq * 2, length) * 0.3
    return lowpass(tone, 2200) * decay(length, 0.07, 0.002)


def ostinato(start: float, end: float, step_start: float, step_end: float, mix: Mix, gain: float) -> None:
    pattern = [D3, D3, D3, F3, D3, D3, D3, A3, D3, D3, D3, C4, D3, D3, A3, F3]
    at, index = start, 0
    while at < end:
        progress = (at - start) / (end - start)
        accent = 1.3 if index % 4 == 0 else 0.85
        level = gain * (0.45 + 0.55 * progress) * accent
        mix.add(stereo(pluck(pattern[index % len(pattern)]), 0.3 if index % 2 else -0.3), at, level)
        if index % 4 == 0:
            mix.add(boom(0.5, 90, 45), at, level * 0.5)
        at += step_start + (step_end - step_start) * progress
        index += 1


def riser(length: float) -> np.ndarray:
    t = seconds(length)
    progress = t / length
    tone = sum(sine(80 * 2 ** (k + 3.2 * progress), length) for k in range(3)) / 3
    air = bandpass(noise(length), 800, 9000)
    shape = progress**2.2
    return reverb(stereo((tone * 0.6 + air * 0.5) * shape), 1.5, 0.3)


def snare_roll(start: float, end: float, mix: Mix) -> None:
    at = start
    while at < end:
        progress = (at - start) / (end - start)
        length = 0.15
        snare = highpass(noise(length), 900) * decay(length, 0.04)
        mix.add(stereo(snare, RNG.uniform(-0.3, 0.3)), at, 0.14 + 0.32 * progress**2)
        at += 0.25 * (1 - progress) + 0.035


def sparkles(length: float) -> np.ndarray:
    out = np.zeros(int(length * RATE))
    for _ in range(46):
        at = int(RNG.uniform(0, length - 0.4) * RATE)
        ping = sine(RNG.uniform(2800, 7400), 0.4) * decay(0.4, RNG.uniform(0.03, 0.12), 0.001)
        out[at : at + len(ping)] += ping * RNG.uniform(0.2, 0.5)
    return reverb(stereo(out * 0.5), 1.8, 0.45, 9000)


def pad(chord: list[float], length: float) -> np.ndarray:
    tone = sum(saw(f, length, d) for f in chord for d in (-0.003, 0.003))
    tone = lowpass(tone / len(chord), 1300)
    t = seconds(length)
    shape = np.minimum(t / 1.5, 1) * np.minimum((length - t) / 2.5, 1)
    return reverb(stereo(tone * shape), 3.0, 0.4, 3000)


def drone(length: float) -> np.ndarray:
    t = seconds(length)
    tone = sum(saw(f, length, d) for f, d in [(D2, 0.0), (D2, 0.003), (A2, -0.002)]) / 3
    tone = lowpass(tone, 320) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t))
    sub = sine(D1, length) * 0.6
    air = bandpass(noise(length), 2200, 4200) * 0.05
    return stereo(tone + sub + air)


def place_voice(mix: Mix, audio: np.ndarray) -> list[tuple[float, float]]:
    spans = []
    for line in TIMELINE["voice"].values():
        clip = audio[int(line["from"] * RATE) : int(line["to"] * RATE)].astype(np.float64)
        fade = int(0.02 * RATE)
        clip[:fade] *= np.linspace(0, 1, fade)
        clip[-fade:] *= np.linspace(1, 0, fade)
        clip = highpass(clip, 90) / np.abs(clip).max() * 0.85
        write_wav(PUBLIC / line["file"], np.stack([clip, clip], axis=1))
        mix.add(reverb(stereo(clip), 0.9, 0.1, 7000), line["at"], 1.0, into="voice")
        spans.append((line["at"], line["at"] + len(clip) / RATE))
    return spans


def duck(length: int, spans: list[tuple[float, float]]) -> np.ndarray:
    gain = np.ones(length)
    ramp = int(0.18 * RATE)
    for begin, end in spans:
        a, b = int(begin * RATE) - ramp, int(end * RATE) + ramp
        gain[a + ramp : b - ramp] = np.minimum(gain[a + ramp : b - ramp], 0.28)
        gain[a : a + ramp] = np.minimum(gain[a : a + ramp], np.linspace(1, 0.28, ramp))
        gain[b - ramp : b] = np.minimum(gain[b - ramp : b], np.linspace(0.28, 1, ramp))
    return gain


def silence(mix: Mix) -> None:
    for begin, end in TIMELINE["silences"]:
        a, b = int(begin * RATE), int(end * RATE)
        mix.bed[a:b] = 0.0


def score(mix: Mix) -> None:
    scenes, montage = TIMELINE["scenes"], TIMELINE["montage"]
    opening = drone(scenes["flipbook"][0])
    swell = np.minimum(seconds(len(opening) / RATE) / 3.0, 1.0)[:, None]
    mix.add(opening * swell, 0, 0.32)
    for index, at in enumerate(TIMELINE["ticks"]):
        mix.add(tick(index % 2 == 0), at, 0.5 + 0.06 * index)
    for beat in np.arange(13.9, 19.0, 0.85):
        mix.add(heartbeat(), beat, 0.55 + 0.08 * (beat - 13.9))
    for at in TIMELINE["braams"]:
        mix.add(braam(), at, 0.85)
    for at in TIMELINE["whooshes"]:
        mix.add(whoosh(), at - 0.35, 0.5)
    for at in TIMELINE["hits"]:
        mix.add(hit(), at, 0.7)
    for at in TIMELINE["slams"]:
        mix.add(braam(2.6), at, 0.9)
        mix.add(boom(), at, 0.9)
    mix.add(boom(1.8), montage["slowModel"], 0.5)
    ostinato(montage["turn"], scenes["refusal"][0], 0.125, 0.11, mix, 0.5)
    for beat in np.arange(40.2, 50.2, 1.0):
        mix.add(heartbeat(), beat, 0.5)
    flip = TIMELINE["flipbook"]
    ostinato(flip["start"], flip["end"], 0.1, 0.05, mix, 0.42)
    snare_roll(flip["start"], flip["end"], mix)
    mix.add(riser(flip["end"] - flip["start"]), flip["start"], 0.5)
    silence(mix)
    impact = TIMELINE["impact"]
    mix.add(braam(4.5), impact, 1.0)
    mix.add(boom(3.5, 95, 28), impact, 1.0)
    mix.add(reverb(stereo(highpass(noise(2.5), 3000) * decay(2.5, 0.5)), 3.0, 0.4), impact, 0.35)
    mix.add(sparkles(2.6), impact + 0.08, 0.8)
    mix.add(pad([D3, FS3, A3, D4], 15.5), impact + 0.3, 0.28)
    mix.add(hit(), scenes["endCard"][0] + 0.4, 0.5)


def compress(x: np.ndarray, threshold: float = 0.55, window: float = 0.03) -> np.ndarray:
    """A smooth peak compressor, so dense passages sit below the ceiling AAC would overshoot."""
    level = np.abs(x).max(axis=1)
    kernel = np.ones(int(window * RATE)) / int(window * RATE)
    envelope = np.maximum(signal.fftconvolve(level, kernel, mode="same"), 1e-6)
    gain = np.minimum(1.0, (threshold / envelope) ** 0.6)
    gain = signal.fftconvolve(gain, kernel, mode="same")
    return x * gain[:, None]


def master(mix: Mix, spans: list[tuple[float, float]]) -> np.ndarray:
    bed = mix.bed * duck(len(mix.bed), spans)[:, None]
    out = bed + mix.voice
    out = out[: int(DURATION * RATE)]
    fade = int(2.0 * RATE)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out = compress(out / np.abs(out).max())
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    return out / np.abs(out).max() * 0.9


def write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(pcm.tobytes())


if __name__ == "__main__":
    call = decode(CALL_AUDIO)
    mix = Mix()
    spans = place_voice(mix, call)
    score(mix)
    final = master(mix, spans)
    write_wav(PUBLIC / "audio" / "soundtrack.wav", final)
    rms = np.sqrt((final**2).mean())
    print(f"soundtrack: {len(final) / RATE:.1f}s, peak {np.abs(final).max():.2f}, rms {20 * np.log10(rms):.1f} dBFS")
