"""Print the speech segments in the recorded demo call, to cut trailer dialogue from it."""

from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CALL_AUDIO = ROOT / "web" / "public" / "demo" / "call.m4a"
RATE = 48_000
FRAME_SECS = 0.02
SILENCE_DB = -42.0
MIN_GAP_SECS = 0.22


def decode(path: Path) -> np.ndarray:
    resampler = av.AudioResampler(format="flt", layout="mono", rate=RATE)
    chunks: list[np.ndarray] = []
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks)


def segments(samples: np.ndarray) -> list[tuple[float, float]]:
    hop = int(RATE * FRAME_SECS)
    frames = samples[: len(samples) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((frames**2).mean(axis=1)) + 1e-9)
    voiced = db > SILENCE_DB
    spans: list[tuple[float, float]] = []
    start = None
    gap = 0
    for index, is_voiced in enumerate(voiced):
        if is_voiced:
            start = index if start is None else start
            gap = 0
        elif start is not None:
            gap += 1
            if gap * FRAME_SECS >= MIN_GAP_SECS:
                spans.append((start * FRAME_SECS, (index - gap + 1) * FRAME_SECS))
                start, gap = None, 0
    return spans


if __name__ == "__main__":
    audio = decode(CALL_AUDIO)
    print(f"duration {len(audio) / RATE:.2f}s peak {np.abs(audio).max():.3f}")
    for begin, end in segments(audio):
        print(f"{begin:7.2f} - {end:7.2f}  ({end - begin:5.2f}s)")
