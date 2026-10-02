"""Typed configuration. Startup fails at once if a required key is missing or inconsistent."""

from pathlib import Path
from typing import Literal, Self

from pydantic import Field, FilePath, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: SecretStr
    soniox_api_key: SecretStr
    cartesia_api_key: SecretStr

    talker_provider: Literal["openai"] = "openai"
    talker_model: str = "gpt-6-luna"
    talker_base_url: str | None = None
    strategist_model: str = "gpt-6-luna"
    translator_model: str = "gpt-6-luna"
    soniox_model: str = "stt-rt-v5"
    cartesia_model: str = "sonic-3.6"
    cartesia_voice_id: str = "aa3ccc4a-cfd8-405c-acf5-1873a527b006"

    backchannel_classifier: Literal["lexicon", "onnx"] = "lexicon"
    backchannel_onnx_path: FilePath | None = None

    twilio_account_sid: str | None = None
    twilio_auth_token: SecretStr | None = None
    public_base_url: str | None = None

    max_call_seconds: int = Field(default=300, gt=0)
    daily_phone_seconds: int = Field(default=3_600, gt=0)
    daily_browser_seconds: int = Field(default=3_600, gt=0)
    calls_per_caller_per_day: int = Field(default=3, gt=0)
    retention_days: int = Field(default=30, gt=0)

    data_dir: Path = Path("var")
    content_path: Path = Path("content/script_ja.yaml")
    host: str = "127.0.0.1"
    port: int = 7860
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    otel_exporter_otlp_endpoint: str | None = None

    @model_validator(mode="after")
    def _require_consistent_options(self) -> Self:
        if self.backchannel_classifier == "onnx" and self.backchannel_onnx_path is None:
            raise ValueError("BACKCHANNEL_ONNX_PATH is required when BACKCHANNEL_CLASSIFIER=onnx")
        twilio_parts = (self.twilio_account_sid, self.twilio_auth_token, self.public_base_url)
        if any(twilio_parts) and not all(twilio_parts):
            raise ValueError(
                "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN and PUBLIC_BASE_URL must be set together"
            )
        return self

    @property
    def is_phone_enabled(self) -> bool:
        return self.twilio_account_sid is not None
