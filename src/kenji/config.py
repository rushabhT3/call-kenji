"""Typed configuration. Startup fails at once if a required key is missing or inconsistent."""

from pathlib import Path
from typing import Literal, Self

from pydantic import Field, FilePath, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LanguageModelSettings(BaseSettings):
    """Any OpenAI-compatible chat-completions provider; an unset base URL means OpenAI."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_api_key: SecretStr
    talker_provider: Literal["openai"] = "openai"
    llm_base_url: str | None = None
    llm_reasoning_effort: Literal["none", "minimal", "low", "medium", "high"] | None = "none"
    llm_temperature: float | None = None
    talker_model: str = "gpt-6-luna"
    strategist_model: str = "gpt-6-luna"
    translator_model: str = "gpt-6-luna"

    @field_validator("llm_api_key")
    @classmethod
    def _require_llm_key(cls, value: SecretStr) -> SecretStr:
        return _non_empty(value)


def _non_empty(value: SecretStr) -> SecretStr:
    if not value.get_secret_value().strip():
        raise ValueError("must not be empty")
    return value


class Settings(LanguageModelSettings):
    soniox_api_key: SecretStr
    cartesia_api_key: SecretStr
    soniox_model: str = "stt-rt-v5"
    cartesia_model: str = "sonic-3.6"
    cartesia_voice_id: str = "aa3ccc4a-cfd8-405c-acf5-1873a527b006"

    backchannel_classifier: Literal["lexicon", "onnx"] = "lexicon"
    backchannel_onnx_path: FilePath | None = None

    cloudflare_turn_key_id: str | None = None
    cloudflare_turn_api_token: SecretStr | None = None

    twilio_account_sid: str | None = None
    twilio_auth_token: SecretStr | None = None
    public_base_url: str | None = None
    twilio_api_key_sid: str | None = None
    twilio_api_key_secret: SecretStr | None = None
    twilio_twiml_app_sid: str | None = None
    proxy_shared_secret: SecretStr | None = None

    max_call_seconds: int = Field(default=300, gt=0)
    daily_phone_seconds: int = Field(default=3_600, gt=0)
    daily_browser_seconds: int = Field(default=3_600, gt=0)
    calls_per_caller_per_day: int = Field(default=3, gt=0)
    retention_days: int = Field(default=30, gt=0)

    data_dir: Path = Path("var")
    content_dir: Path = Path("content")
    stun_url: str = "stun:stun.l.google.com:19302"
    enable_dev_client: bool = False
    host: str = "127.0.0.1"
    port: int = 7860
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    otel_exporter_otlp_endpoint: str | None = None

    @field_validator("soniox_api_key", "cartesia_api_key")
    @classmethod
    def _require_speech_keys(cls, value: SecretStr) -> SecretStr:
        return _non_empty(value)

    @model_validator(mode="after")
    def _require_consistent_options(self) -> Self:
        if self.backchannel_classifier == "onnx" and self.backchannel_onnx_path is None:
            raise ValueError("BACKCHANNEL_ONNX_PATH is required when BACKCHANNEL_CLASSIFIER=onnx")
        turn_parts = (self.cloudflare_turn_key_id, self.cloudflare_turn_api_token)
        if any(turn_parts) and not all(turn_parts):
            raise ValueError(
                "CLOUDFLARE_TURN_KEY_ID and CLOUDFLARE_TURN_API_TOKEN must be set together"
            )
        twilio_parts = (self.twilio_account_sid, self.twilio_auth_token, self.public_base_url)
        if any(twilio_parts) and not all(twilio_parts):
            raise ValueError(
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and PUBLIC_BASE_URL must be set together"
            )
        return self

    @model_validator(mode="after")
    def _require_complete_softphone(self) -> Self:
        softphone_parts = (
            self.twilio_api_key_sid,
            self.twilio_api_key_secret,
            self.twilio_twiml_app_sid,
        )
        if any(softphone_parts) and not all(softphone_parts):
            raise ValueError(
                "TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET and TWILIO_TWIML_APP_SID must be set"
                " together"
            )
        if any(softphone_parts) and not self.is_phone_enabled:
            raise ValueError("the softphone calls the phone line, so TWILIO_ACCOUNT_SID is needed")
        return self

    @property
    def is_phone_enabled(self) -> bool:
        return self.twilio_account_sid is not None
