"""Start a call: apply the guardrails, link the viewer, run the call and count its minutes."""

import asyncio
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Literal

from loguru import logger
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.transports.base_transport import BaseTransport

from kenji.app.call import Call, CallSetup
from kenji.app.call_parts import CallIO, CallKit
from kenji.app.dtmf import DtmfLinker
from kenji.app.events import CallEnded, CallEvent
from kenji.app.hub import EventHub
from kenji.app.linking import LinkRegistry
from kenji.app.ports import CallRecorder, EventSink, UsageLedger
from kenji.app.refusal import publish_refusal, refusal_line, speak_and_hang_up
from kenji.app.script import Line
from kenji.app.session import CallContext
from kenji.domain.guardrails import Admission, CallLimits, Refusal, admit_call, usage_day
from kenji.domain.outcome import CallOutcome
from kenji.domain.terms import Negotiation

type TransportKind = Literal["phone", "browser"]
type RecorderFactory = Callable[[str, date], CallRecorder]


@dataclass(frozen=True, slots=True)
class CallRequest:
    transport: TransportKind
    caller_ref: str
    viewer_id: str | None = None
    call_id: str = ""
    persona_id: str | None = None


@dataclass(frozen=True, slots=True)
class CallRouting:
    """Where a call's events go: the hub, and the codes that link phone calls to tabs."""

    hub: EventHub
    links: LinkRegistry


@dataclass(frozen=True, slots=True)
class CallAccounting:
    """What a call costs: daily usage, per-call records and the limits per transport."""

    usage: UsageLedger
    recorder: RecorderFactory
    limits: dict[TransportKind, CallLimits]


@dataclass(frozen=True, slots=True)
class _Attempt:
    request: CallRequest
    context: CallContext
    io: CallIO

    @property
    def day(self) -> date:
        return usage_day(self.context.started_at)


class _FanOut:
    def __init__(self, sinks: list[EventSink]) -> None:
        self._sinks = sinks

    def publish(self, event: CallEvent) -> None:
        for sink in self._sinks:
            sink.publish(event)


class CallLauncher:
    def __init__(self, kit: CallKit, routing: CallRouting, accounting: CallAccounting) -> None:
        self._kit = kit
        self._routing = routing
        self._accounting = accounting

    async def run(self, transport: BaseTransport, request: CallRequest) -> CallOutcome:
        async with self._recording(request) as attempt:
            if request.viewer_id is not None:
                self._routing.hub.link(attempt.context.call_id, request.viewer_id)
            admission = await self._admit(attempt)
            if admission.refusal is not None:
                return await self._refuse_on_the_line(transport, admission.refusal, attempt)
            return await self._run_admitted(transport, admission, attempt)

    async def screen(self, request: CallRequest) -> Line | None:
        """Refuse a phone call before answering it, so a refused call opens no media stream.

        Returns the line to say instead of answering, or None when the call is admitted.
        """
        async with self._recording(request) as attempt:
            admission = await self._admit(attempt)
            if admission.refusal is None:
                return None
            line = self._record_refusal(admission.refusal, attempt)
            self._end_refused(attempt)
            return line

    @asynccontextmanager
    async def _recording(self, request: CallRequest) -> AsyncIterator[_Attempt]:
        context = self._context(request)
        call_id = context.call_id
        recorder = self._accounting.recorder(call_id, usage_day(context.started_at))
        hub = self._routing.hub
        io = CallIO(sink=_FanOut([hub.channel(call_id), recorder]), audit=recorder)
        try:
            yield _Attempt(request=request, context=context, io=io)
        finally:
            await recorder.close()
            hub.forget(call_id)

    async def _run_admitted(
        self, transport: BaseTransport, admission: Admission, attempt: _Attempt
    ) -> CallOutcome:
        request, context, usage = attempt.request, attempt.context, self._accounting.usage
        await asyncio.to_thread(
            usage.record_call, request.transport, request.caller_ref, attempt.day
        )
        try:
            processors = self._input_processors(context)
            setup = CallSetup(context, attempt.io, admission.call_seconds_allowed, processors)
            return await Call(self._kit, setup, transport).run()
        finally:
            seconds = int((self._kit.clock.now() - context.started_at).total_seconds())
            await asyncio.to_thread(usage.record_seconds, request.transport, attempt.day, seconds)

    def _input_processors(self, context: CallContext) -> tuple[FrameProcessor, ...]:
        if context.transport != "phone":
            return ()
        routing = self._routing
        return (DtmfLinker(context.call_id, routing.links.redeem, routing.hub.link),)

    def _context(self, request: CallRequest) -> CallContext:
        started_at = self._kit.clock.now()
        persona_id = self._persona_id(request.persona_id)
        account = self._kit.personas.account_for(persona_id)
        return CallContext(
            call_id=request.call_id or uuid.uuid4().hex,
            transport=request.transport,
            caller_ref=request.caller_ref,
            started_at=started_at,
            persona_id=persona_id,
            account=account,
            negotiation=Negotiation(balance_yen=account.balance_yen, today=usage_day(started_at)),
        )

    def _persona_id(self, requested: str | None) -> str:
        persona_id = self._kit.personas.resolve(requested)
        if requested is not None and requested != persona_id:
            logger.warning(
                "unknown persona {persona_id!r}; playing the default", persona_id=requested
            )
        return persona_id

    async def _admit(self, attempt: _Attempt) -> Admission:
        request = attempt.request
        usage = await asyncio.to_thread(
            self._accounting.usage.usage_today, request.transport, request.caller_ref, attempt.day
        )
        limits = self._accounting.limits[request.transport]
        return admit_call(usage, limits)

    def _record_refusal(self, refusal: Refusal, attempt: _Attempt) -> Line:
        line = refusal_line(self._kit.script.lines, refusal)
        publish_refusal(attempt.io, attempt.context, line, self._kit.clock)
        return line

    async def _refuse_on_the_line(
        self, transport: BaseTransport, refusal: Refusal, attempt: _Attempt
    ) -> CallOutcome:
        line = self._record_refusal(refusal, attempt)
        await speak_and_hang_up(transport, line, self._kit.voice.text_to_speech)
        return self._end_refused(attempt)

    def _end_refused(self, attempt: _Attempt) -> CallOutcome:
        outcome = CallOutcome.DAILY_LIMIT_REACHED
        attempt.io.sink.publish(CallEnded(outcome=outcome, ended_at=self._kit.clock.now()))
        return outcome
