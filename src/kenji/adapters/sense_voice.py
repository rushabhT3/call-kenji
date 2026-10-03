"""SenseVoice-Small through sherpa-onnx hears how a caller's turn sounds, from its audio alone.

SenseVoice tags each utterance with a language, an emotion and one audio event. The emotion is
kept, and the events that say something about the caller: laughter, crying, a cough, a sneeze.
Background music or noise says nothing about them, and silence is often heard as music.

The int8 model (scripts/fetch_emotion_model.py) is 228 MB on disk and about 300 MB in memory, and
classifies a few seconds of speech in a few hundred milliseconds on two CPU threads.
"""

from pathlib import Path

import numpy as np
import sherpa_onnx

from kenji.app.events import CallerEmotion, CallerSound
from kenji.app.ports import CallerTone, TurnAudio

MODEL_FILE = "model.int8.onnx"
TOKENS_FILE = "tokens.txt"
_THREADS = 2
_PCM_SCALE = 32_768.0
_EMOTIONS: dict[str, CallerEmotion] = {
    "<|NEUTRAL|>": "neutral",
    "<|HAPPY|>": "happy",
    "<|SAD|>": "sad",
    "<|ANGRY|>": "angry",
    "<|FEARFUL|>": "fearful",
    "<|DISGUSTED|>": "disgusted",
    "<|SURPRISED|>": "surprised",
}
_SOUNDS: dict[str, CallerSound] = {
    "<|Laughter|>": "laughter",
    "<|Cry|>": "crying",
    "<|Cough|>": "coughing",
    "<|Sneeze|>": "sneezing",
}


def has_sense_voice_model(model_dir: Path) -> bool:
    return all((model_dir / name).is_file() for name in (MODEL_FILE, TOKENS_FILE))


def tone_from_tags(emotion: str, event: str) -> CallerTone:
    sound = _SOUNDS.get(event)
    return CallerTone(emotion=_EMOTIONS.get(emotion, "unknown"), sounds=(sound,) if sound else ())


class SenseVoiceEmotionClassifier:
    def __init__(self, model_dir: Path) -> None:
        if not has_sense_voice_model(model_dir):
            raise FileNotFoundError(f"SenseVoice model not found in {model_dir}")
        self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=str(model_dir / MODEL_FILE),
            tokens=str(model_dir / TOKENS_FILE),
            num_threads=_THREADS,
            language="ja",
        )

    def classify(self, audio: TurnAudio) -> CallerTone:
        stream = self._recognizer.create_stream()
        samples = np.frombuffer(audio.pcm, dtype=np.int16).astype(np.float32) / _PCM_SCALE
        stream.accept_waveform(audio.sample_rate, samples)
        self._recognizer.decode_stream(stream)
        result = stream.result
        return tone_from_tags(result.emotion, result.event)
