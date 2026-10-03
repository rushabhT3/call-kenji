"""SenseVoice's tags become the tones Kenji knows; the real model runs only where it was fetched."""

import os
from pathlib import Path

import pytest
from pydantic import SecretStr

from kenji.adapters.sense_voice import (
    SenseVoiceEmotionClassifier,
    has_sense_voice_model,
    tone_from_tags,
)
from kenji.app.ports import CallerTone, TurnAudio
from kenji.config import Settings
from kenji.container import build_emotion_classifier

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.environ.get("CALLER_EMOTION_MODEL_DIR") or ROOT / "models" / "sense-voice")
ONE_SECOND_OF_SILENCE = TurnAudio(pcm=bytes(32_000), sample_rate=16_000)


@pytest.mark.parametrize(
    ("emotion", "event", "tone"),
    [
        ("<|ANGRY|>", "<|Speech|>", CallerTone(emotion="angry")),
        ("<|SAD|>", "<|Cry|>", CallerTone(emotion="sad", sounds=("crying",))),
        ("<|NEUTRAL|>", "<|Laughter|>", CallerTone(emotion="neutral", sounds=("laughter",))),
        ("<|EMO_UNKNOWN|>", "<|Cough|>", CallerTone(emotion="unknown", sounds=("coughing",))),
        ("<|OTHER|>", "<|BGM|>", CallerTone(emotion="unknown")),
    ],
)
def test_sense_voice_tags_become_a_tone(emotion: str, event: str, tone: CallerTone) -> None:
    assert tone_from_tags(emotion, event) == tone


def test_a_missing_model_fails_at_startup(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        SenseVoiceEmotionClassifier(tmp_path)


@pytest.mark.skipif(
    not has_sense_voice_model(MODEL_DIR), reason="run scripts/fetch_emotion_model.py first"
)
def test_the_configured_model_hears_silence_as_no_clear_emotion(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key=SecretStr("dummy-llm-key"),
        soniox_api_key=SecretStr("dummy-soniox-key"),
        cartesia_api_key=SecretStr("dummy-cartesia-key"),
        data_dir=tmp_path,
        caller_emotion_model_dir=MODEL_DIR,
    )

    classifier = build_emotion_classifier(settings)

    assert isinstance(classifier, SenseVoiceEmotionClassifier)
    assert classifier.classify(ONE_SECOND_OF_SILENCE) == CallerTone(emotion="unknown")
