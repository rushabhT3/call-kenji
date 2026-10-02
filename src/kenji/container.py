"""Composition root: the one place that reads settings and picks concrete adapters."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from openai import AsyncOpenAI

from kenji.adapters.clock import SystemClock
from kenji.adapters.content import load_account, load_script
from kenji.adapters.onnx_classifier import OnnxBackchannelClassifier
from kenji.adapters.openai_models import OpenAIAdviceModel, OpenAITalker, OpenAITranslator
from kenji.adapters.speech import (
    CartesiaTextToSpeech,
    SileroSmartTurnDetection,
    SonioxSpeechToText,
)
from kenji.adapters.storage import CallRecord, JsonContactStore, JsonUsageLedger
from kenji.app.call_parts import CallKit, VoiceServices
from kenji.app.hub import EventHub
from kenji.app.launcher import CallLauncher, TransportKind
from kenji.app.linking import LinkRegistry
from kenji.app.ports import CallRecorder, TalkerFactory
from kenji.app.script import Script
from kenji.config import Settings
from kenji.domain.account import Account
from kenji.domain.guardrails import CallLimits
from kenji.domain.turn import BackchannelClassifier, LexiconBackchannelClassifier

SALT_BYTES = 32


@dataclass(frozen=True, slots=True)
class Services:
    launcher: CallLauncher
    hub: EventHub
    links: LinkRegistry
    salt: bytes


def _openai_talker(settings: Settings) -> TalkerFactory:
    return OpenAITalker(
        settings.openai_api_key.get_secret_value(),
        settings.talker_model,
        base_url=settings.talker_base_url,
        reasoning_effort=settings.openai_reasoning_effort,
    )


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
    client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
    effort = settings.openai_reasoning_effort
    return CallKit(
        script=script,
        account=account,
        voice=_voice(settings, script, account),
        advice_model=OpenAIAdviceModel(client, settings.strategist_model, effort),
        translator=OpenAITranslator(
            client, settings.translator_model, effort, script.prompts.translator_system
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


def build_services(settings: Settings) -> Services:
    kit = build_kit(settings)
    hub = EventHub()

    def recorder(call_id: str, call_date: date) -> CallRecorder:
        return CallRecord(settings.data_dir, call_date, call_id)

    launcher = CallLauncher(
        kit, hub, JsonUsageLedger(settings.data_dir / "usage"), recorder, _limits(settings)
    )
    return Services(
        launcher=launcher,
        hub=hub,
        links=LinkRegistry(kit.clock),
        salt=load_or_create_salt(settings.data_dir / "caller-salt.bin"),
    )
