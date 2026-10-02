"""The real vendor adapters assemble from settings alone, so a wiring mistake fails in CI."""

from pathlib import Path

from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.soniox.stt import SonioxSTTService
from pydantic import SecretStr

from kenji.adapters.openai_models import OpenAIAdviceModel, OpenAITranslator
from kenji.adapters.turn import CloudflareTurn, StunOnly
from kenji.app.turns import BackchannelTurnStartStrategy
from kenji.config import Settings
from kenji.container import build_kit, build_services
from kenji.domain.turn import LexiconBackchannelClassifier, TurnPolicy


def _settings(data_dir: Path, **overrides: object) -> Settings:
    return Settings(
        _env_file=None,
        llm_api_key=SecretStr("dummy-llm-key"),
        soniox_api_key=SecretStr("dummy-soniox-key"),
        cartesia_api_key=SecretStr("dummy-cartesia-key"),
        data_dir=data_dir,
        **overrides,  # type: ignore[arg-type]
    )


def test_real_speech_and_model_adapters_build_without_a_network(tmp_path: Path) -> None:
    kit = build_kit(_settings(tmp_path))
    strategy = BackchannelTurnStartStrategy(
        classifier=LexiconBackchannelClassifier(),
        policy=lambda: TurnPolicy(min_interruption_score=0.5),
        on_decision=lambda *_: None,
    )

    assert isinstance(kit.voice.speech_to_text.create(), SonioxSTTService)
    assert isinstance(kit.voice.text_to_speech.create(), CartesiaTTSService)
    assert isinstance(kit.voice.talker.create("You are Kenji."), OpenAILLMService)
    assert kit.voice.turn_detection.user_params(strategy).vad_analyzer is not None
    assert isinstance(kit.advice_model, OpenAIAdviceModel)
    assert isinstance(kit.translator, OpenAITranslator)


def test_browser_only_services_have_no_phone_line_and_use_stun(tmp_path: Path) -> None:
    services = build_services(_settings(tmp_path))

    assert services.phone is None
    assert isinstance(services.ice, StunOnly)
    assert (tmp_path / "caller-salt.bin").exists()


def test_phone_and_turn_settings_switch_both_on(tmp_path: Path) -> None:
    services = build_services(
        _settings(
            tmp_path,
            twilio_account_sid="AC-dummy",
            twilio_auth_token=SecretStr("dummy-twilio-token"),
            public_base_url="https://kenji.example/",
            cloudflare_turn_key_id="dummy-turn-key",
            cloudflare_turn_api_token=SecretStr("dummy-turn-token"),
        )
    )

    assert services.phone is not None
    assert services.phone.public_base_url == "https://kenji.example"
    assert isinstance(services.ice, CloudflareTurn)


def test_softphone_settings_switch_the_softphone_on(tmp_path: Path) -> None:
    services = build_services(
        _settings(
            tmp_path,
            twilio_account_sid="AC-dummy",
            twilio_auth_token=SecretStr("dummy-twilio-token"),
            public_base_url="https://kenji.example",
            twilio_api_key_sid="SK-dummy",
            twilio_api_key_secret=SecretStr("dummy-key-secret"),
            twilio_twiml_app_sid="AP-dummy",
        )
    )

    assert services.softphone is not None


def test_without_softphone_settings_there_is_no_softphone(tmp_path: Path) -> None:
    assert build_services(_settings(tmp_path)).softphone is None
