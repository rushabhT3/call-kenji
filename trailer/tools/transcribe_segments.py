"""Transcribe chosen stretches of the demo call with SenseVoice, to find each line's exact span."""

import sys
from pathlib import Path

import numpy as np
import sherpa_onnx
from voice_segments import CALL_AUDIO, RATE, decode

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "models" / "sense-voice"

recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
    model=str(MODEL / "model.int8.onnx"),
    tokens=str(MODEL / "tokens.txt"),
    num_threads=2,
    language="ja",
)
audio = decode(CALL_AUDIO)
for span in sys.argv[1:]:
    begin, end = (float(part) for part in span.split(":"))
    stream = recognizer.create_stream()
    stream.accept_waveform(RATE, audio[int(begin * RATE) : int(end * RATE)].astype(np.float32))
    recognizer.decode_stream(stream)
    print(f"{begin:7.2f}-{end:7.2f}  {stream.result.text}")
