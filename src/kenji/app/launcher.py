"""Start a call: apply the guardrails, link the viewer, run the call and count its minutes."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Literal

from pipecat.transports.base_transport import BaseTransport

from kenji.app.call import Call, CallSetup
from kenji.app.call_parts import CallIO, CallKit
from kenji.app.events import CallEnded, CallEvent
from kenji.app.hub import EventHub
from kenji.app.ports import CallRecorder, EventSink, UsageLedger
from kenji.app.refusal import publish_refusal, refusal_line, refusal_outcome, speak_and_hang_up
from kenji.app.session import CallContext
from kenji.domain.guardrails import Admission, CallLimits, admit_call, usage_day
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


class _FanOut:
    def __init__(self, sinks: list[EventSink]) -> None:
        self._sinks = sinks

    def publish(self, event: CallEvent) -> None:
        for sink in self._sinks:
            sink.publish(event)


class CallLauncher:
    def __init__(
        self,
        kit: CallKit,
        hub: EventHub,
        usage: UsageLedger,
        recorder: RecorderFactory,
        limits: dict[TransportKind, CallLimits],
    ) -> None:
        self._kit = kit
        self._hub = hub
        self._usage = usage
        self._recorder = recorder
        self._limits = limits

    async def run(self, transport: BaseTransport, request: CallRequest) -> CallOutcome:
        context = self._context(request)
        day = usage_day(context.started_at)
        recorder = self._recorder(context.call_id, day)
        io = CallIO(sink=_FanOut([self._hub.channel(context.call_id), recorder]), audit=recorder)
        if request.viewer_id is not None:
            self._hub.link(context.call_id, request.viewer_id)
        admission = self._admit(request, day, context)
        if not admission.is_admitted:
            return await self._refuse(transport, admission, context, io)
        self._usage.record_call(request.transport, request.caller_ref, day)
        try:
            setup = CallSetup(context, io, admission.call_seconds_allowed)
            return await Call(self._kit, setup, transport).run()
        finally:
            elapsed = self._kit.clock.now() - context.started_at
            self._usage.record_seconds(request.transport, day, int(elapsed.total_seconds()))

    def link(self, call_id: str, viewer_id: str) -> bool:
        return self._hub.link(call_id, viewer_id)

    def _context(self, request: CallRequest) -> CallContext:
        started_at = self._kit.clock.now()
        account = self._kit.account
        return CallContext(
            call_id=request.call_id or uuid.uuid4().hex,
            transport=request.transport,
            caller_ref=request.caller_ref,
            started_at=started_at,
            account=account,
            negotiation=Negotiation(balance_yen=account.balance_yen, today=usage_day(started_at)),
        )

    def _admit(self, request: CallRequest, day: date, context: CallContext) -> Admission:
        usage = self._usage.usage_today(request.transport, request.caller_ref, day)
        return admit_call(context.started_at, usage, self._limits[request.transport])

    async def _refuse(
        self, transport: BaseTransport, admission: Admission, context: CallContext, io: CallIO
    ) -> CallOutcome:
        if admission.refusal is None:
            raise ValueError("only a refused admission can be refused")
        line = refusal_line(self._kit.script.lines, admission.refusal)
        outcome = refusal_outcome(admission.refusal)
        publish_refusal(io, context, line, self._kit.clock)
        await speak_and_hang_up(transport, line, self._kit.voice.text_to_speech)
        io.sink.publish(CallEnded(outcome=outcome, ended_at=self._kit.clock.now()))
        return outcome
