"""Swap the rendered trailer's audio for the mastered soundtrack, re-encoded with headroom.

AAC overshoots a full-scale master, so the soundtrack is encoded at a lower peak and the result is
decoded again to prove it no longer clips. The video stream is copied untouched.

    uv run python trailer/tools/remux_audio.py <rendered.mp4> <soundtrack.wav> <out.mp4>
"""

import sys
import wave
from fractions import Fraction

import av
import numpy as np

TARGET_PEAK = 0.92
FRAME_SAMPLES = 1024


def read_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path) as file:
        rate = file.getframerate()
        samples = np.frombuffer(file.readframes(file.getnframes()), "<i2").reshape(-1, 2).astype(np.float32) / 32768
    return samples / np.abs(samples).max() * TARGET_PEAK, rate


def encode_audio(stream: av.audio.stream.AudioStream, samples: np.ndarray, rate: int) -> list[av.Packet]:
    packets: list[av.Packet] = []
    for start in range(0, len(samples), FRAME_SAMPLES):
        chunk = np.ascontiguousarray(samples[start : start + FRAME_SAMPLES].T)
        frame = av.AudioFrame.from_ndarray(chunk, format="fltp", layout="stereo")
        frame.sample_rate = rate
        frame.pts = start
        frame.time_base = Fraction(1, rate)
        packets.extend(stream.encode(frame))
    packets.extend(stream.encode(None))
    return packets


def remux(rendered: str, soundtrack: str, target: str) -> None:
    samples, rate = read_wav(soundtrack)
    with av.open(rendered) as source, av.open(target, "w", options={"movflags": "+faststart"}) as output:
        video_in = source.streams.video[0]
        video_out = output.add_stream_from_template(video_in)
        audio_out = output.add_stream("aac", rate=rate, layout="stereo")
        audio_out.bit_rate = 192_000
        audio_packets = encode_audio(audio_out, samples, rate)
        video_packets = [packet for packet in source.demux(video_in) if packet.dts is not None]
        timed = [(float(p.dts * video_in.time_base), p, video_out) for p in video_packets]
        timed += [(float(p.dts * p.time_base), p, audio_out) for p in audio_packets if p.dts is not None]
        for _, packet, stream in sorted(timed, key=lambda item: item[0]):
            packet.stream = stream
            output.mux(packet)


def peak_of(path: str) -> float:
    with av.open(path) as container:
        return max(float(np.abs(frame.to_ndarray()).max()) for frame in container.decode(audio=0))


if __name__ == "__main__":
    rendered, soundtrack, target = sys.argv[1:4]
    remux(rendered, soundtrack, target)
    print(f"decoded peak after AAC: {peak_of(target):.3f}")
