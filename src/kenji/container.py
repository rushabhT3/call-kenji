"""Composition root: the one place that reads settings and picks concrete adapters."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from kenji.adapters.clock import SystemClock
from kenji.adapters.content import load_account, load_script
from kenji.adapters.onnx_classifier import OnnxBackchannelClassifier
from kenji.adapters.openai_models import (
    ChatEndpoint,
    OpenAIAdviceModel,
    OpenAITalker,
    OpenAITranslator,
)
from kenji.adapters.speech import (
    CartesiaTextToSpeech,
    SileroSmartTurnDetection,
    SonioxSpeechToText,
)
from kenji.adapters.storage import CallRecord, JsonContactStore, JsonUsageLedger
from kenji.adapters.twilio import TwilioWebhooks
from kenji.app.call_parts import CallKit, VoiceServices
from kenji.app.hub import EventHub
from kenji.app.launcher import CallAccounting, CallLauncher, CallRouting, TransportKind
from kenji.app.linking import LinkRegistry
from kenji.app.ports import CallRecorder, Clock, TalkerFactory
from kenji.app.script import Script
from kenji.app.stream_tokens import StreamTokens
from kenji.config import Settings
from kenji.domain.account import Account
from kenji.domain.guardrails import CallLimits
from kenji.domain.turn import BackchannelClassifier, LexiconBackchannelClassifier

SALT_BYTES = 32


@dataclass(frozen=True, slots=True)
class PhoneLine:
    webhooks: TwilioWebhooks
    tokens: StreamTokens
    credentials: tuple[str, str]
    public_base_url: str


@dataclass(frozen=True, slots=True)
class Services:
    launcher: CallLauncher
    hub: EventHub
    links: LinkRegistry
    salt: bytes
    phone: PhoneLine | None = None


def chat_endpoint(settings: Settings) -> ChatEndpoint:
    return ChatEndpoint(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        reasoning_effort=settings.llm_reasoning_effort,
        temperature=settings.llm_temperature,
    )


def _openai_talker(settings: Settings) -> TalkerFactory:
    return OpenAITalker(chat_endpoint(settings), settings.talker_model)


TALKERS: dict[str, Callable[[Settings], TalkerFactory]] = {"openai": _openai_talker}


def build_classifier(settings: Settings) -> BackchannelClassifier:
    if settings.backchannel_classifier == "onnx" and settings.backchannel_onnx_path is not None:
        return OnnxBackchannelClassifier(settings.backchannel_onnx_path)
    return LexiconBackchannelClassifier()


def load_or_create_salt(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_bytes(SALT_BYTES)
    path.write_bytes(salt)
    return salt


def _voice(settings: Settings, script: Script, account: Account) -> VoiceServices:
    vocabulary = [
        script.persona.agent_name,
        script.persona.servicer_full,
        account.debtor.written_name,
    ]
    return VoiceServices(
        speech_to_text=SonioxSpeechToText(
            settings.soniox_api_key.get_secret_value(), settings.soniox_model, vocabulary
        ),
        text_to_speech=CartesiaTextToSpeech(
            settings.cartesia_api_key.get_secret_value(),
            settings.cartesia_model,
            settings.cartesia_voice_id,
        ),
        talker=TALKERS[settings.talker_provider](settings),
        turn_detection=SileroSmartTurnDetection(),
    )


def build_kit(settings: Settings) -> CallKit:
    script = load_script(settings.content_dir / "script_ja.yaml")
    account = load_account(settings.content_dir / "account.yaml")
    endpoint = chat_endpoint(settings)
    return CallKit(
        script=script,
        account=account,
        voice=_voice(settings, script, account),
        advice_model=OpenAIAdviceModel(endpoint, settings.strategist_model),
        translator=OpenAITranslator(
            endpoint, settings.translator_model, script.prompts.translator_system
        ),
        classifier=build_classifier(settings),
        contacts=JsonContactStore(settings.data_dir / "contacts.json"),
        clock=SystemClock(),
    )


def _limits(settings: Settings) -> dict[TransportKind, CallLimits]:
    def limits(daily_seconds: int) -> CallLimits:
        return CallLimits(
            max_call_seconds=settings.max_call_seconds,
            daily_seconds=daily_seconds,
            calls_per_caller_per_day=settings.calls_per_caller_per_day,
        )

    return {
        "phone": limits(settings.daily_phone_seconds),
        "browser": limits(settings.daily_browser_seconds),
    }


def build_phone_line(settings: Settings, clock: Clock) -> PhoneLine | None:
    sid, token, base_url = (
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.public_base_url,
    )
    if sid is None or token is None or base_url is None:
        return None
    return PhoneLine(
        webhooks=TwilioWebhooks(token.get_secret_value()),
        tokens=StreamTokens(clock),
        credentials=(sid, token.get_secret_value()),
        public_base_url=base_url.rstrip("/"),
    )


def build_services(settings: Settings) -> Services:
    kit = build_kit(settings)
    routing = CallRouting(hub=EventHub(), links=LinkRegistry(kit.clock))

    def recorder(call_id: str, call_date: date) -> CallRecorder:
        return CallRecord(settings.data_dir, call_date, call_id)

    accounting = CallAccounting(
        usage=JsonUsageLedger(settings.data_dir / "usage"),
        recorder=recorder,
        limits=_limits(settings),
    )
    return Services(
        launcher=CallLauncher(kit, routing, accounting),
        hub=routing.hub,
        links=routing.links,
        salt=load_or_create_salt(settings.data_dir / "caller-salt.bin"),
        phone=build_phone_line(settings, kit.clock),
    )
