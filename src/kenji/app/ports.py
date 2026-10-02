"""Interfaces the application depends on; adapters implement them."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.services.llm_service import LLMService
from pipecat.turns.user_start import BaseUserTurnStartStrategy

from kenji.app.events import CallEvent
from kenji.app.turns import CallerHold
from kenji.domain.audit import AuditEntry, AuditRecord
from kenji.domain.contact import ContactPreferences, StopContactRequest
from kenji.domain.guardrails import UsageToday


@dataclass(frozen=True, slots=True)
class IceServer:
    urls: list[str]
    username: str | None = None
    credential: str | None = None

    def to_browser(self) -> dict[str, Any]:
        server: dict[str, Any] = {"urls": self.urls}
        if self.username is not None and self.credential is not None:
            server |= {"username": self.username, "credential": self.credential}
        return server


class IceServerSource(Protocol):
    async def ice_servers(self) -> list[IceServer]: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class EventSink(Protocol):
    def publish(self, event: CallEvent) -> None: ...


class AuditLog(Protocol):
    def append(self, entry: AuditEntry) -> AuditRecord: ...

    def records(self) -> list[AuditRecord]: ...


class ContactStore(Protocol):
    def record(self, request: StopContactRequest) -> None: ...

    def preferences(self) -> ContactPreferences: ...


class Translator(Protocol):
    async def translate(self, japanese: str) -> str: ...


class AdviceModel(Protocol):
    async def advise(
        self, system_prompt: str, conversation: str, json_schema: dict[str, Any]
    ) -> str: ...


class UsageLedger(Protocol):
    def usage_today(self, pool: str, caller_ref: str, day: date) -> UsageToday: ...

    def record_call(self, pool: str, caller_ref: str, day: date) -> None: ...

    def record_seconds(self, pool: str, day: date, seconds: int) -> None: ...


class CallRecorder(EventSink, AuditLog, Protocol):
    """Keeps one call's events and audit chain."""

    async def close(self) -> None:
        """Finish writing; nothing is published after this."""


class SpeechToTextFactory(Protocol):
    def create(self) -> FrameProcessor: ...


class TextToSpeechFactory(Protocol):
    def create(self) -> FrameProcessor: ...


class TurnDetection(Protocol):
    def user_params(
        self, start: BaseUserTurnStartStrategy, caller_hold: CallerHold
    ) -> LLMUserAggregatorParams: ...


class TalkerFactory(Protocol):
    def create(self, system_instruction: str) -> LLMService[Any]: ...
