from pathlib import Path

import pytest
from pydantic import ValidationError

from kenji.config import Settings
from kenji.server import load_settings

REQUIRED_KEYS = {
    "LLM_API_KEY": "sk-test",
    "SONIOX_API_KEY": "soniox-test",
    "CARTESIA_API_KEY": "cartesia-test",
}


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for key in REQUIRED_KEYS:
        monkeypatch.delenv(key, raising=False)


def _set(monkeypatch: pytest.MonkeyPatch, values: dict[str, str]) -> None:
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_missing_api_key_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {"LLM_API_KEY": "sk-test", "SONIOX_API_KEY": "soniox-test"})

    with pytest.raises(ValidationError, match="cartesia_api_key"):
        Settings()


def test_required_keys_are_enough(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, REQUIRED_KEYS)

    settings = Settings()

    assert settings.max_call_seconds == 300
    assert not settings.is_phone_enabled


def test_hearing_how_callers_sound_is_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, REQUIRED_KEYS)
    monkeypatch.delenv("CALLER_EMOTION_MODEL_DIR", raising=False)

    assert Settings().caller_emotion_model_dir is None


def test_the_emotion_model_dir_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, "CALLER_EMOTION_MODEL_DIR": "models/sense-voice"})

    assert Settings().caller_emotion_model_dir == Path("models/sense-voice")


def test_onnx_classifier_needs_a_model_path(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, "BACKCHANNEL_CLASSIFIER": "onnx"})

    with pytest.raises(ValidationError, match="BACKCHANNEL_ONNX_PATH"):
        Settings()


def test_twilio_settings_must_be_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, "TWILIO_ACCOUNT_SID": "AC123"})

    with pytest.raises(ValidationError, match="must be set together"):
        Settings()


def test_complete_twilio_settings_enable_the_phone_line(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(
        monkeypatch,
        {
            **REQUIRED_KEYS,
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token",
            "PUBLIC_BASE_URL": "https://kenji.example",
        },
    )

    assert Settings().is_phone_enabled


PHONE_LINE = {
    "TWILIO_ACCOUNT_SID": "AC123",
    "TWILIO_AUTH_TOKEN": "token",
    "PUBLIC_BASE_URL": "https://kenji.example",
}
SOFTPHONE = {
    "TWILIO_API_KEY_SID": "SK123",
    "TWILIO_API_KEY_SECRET": "secret",
    "TWILIO_TWIML_APP_SID": "AP123",
}


def test_softphone_settings_must_be_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, **PHONE_LINE, "TWILIO_API_KEY_SID": "SK123"})

    with pytest.raises(ValidationError, match="TWILIO_TWIML_APP_SID must be set together"):
        Settings()


def test_the_softphone_needs_the_phone_line(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, **SOFTPHONE})

    with pytest.raises(ValidationError, match="TWILIO_ACCOUNT_SID is needed"):
        Settings()


def test_complete_softphone_settings_are_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, **PHONE_LINE, **SOFTPHONE})

    assert Settings().twilio_twiml_app_sid == "AP123"


def test_guardrails_must_be_positive(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, "MAX_CALL_SECONDS": "0"})

    with pytest.raises(ValidationError, match="max_call_seconds"):
        Settings()


def test_empty_keys_fail_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {**REQUIRED_KEYS, "LLM_API_KEY": "  "})

    with pytest.raises(ValidationError, match="must not be empty"):
        Settings()


def test_startup_errors_never_echo_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    _set(monkeypatch, {"LLM_API_KEY": "sk-do-not-print-me"})

    with pytest.raises(SystemExit) as stopped:
        load_settings()

    message = str(stopped.value)
    assert "SONIOX_API_KEY" in message
    assert "do-not-print-me" not in message
