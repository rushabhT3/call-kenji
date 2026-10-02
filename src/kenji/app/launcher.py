"""Start a call: apply the guardrails, link the viewer, run the call and count its minutes."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Literal

from pipecat.processors.frame_processor import FrameProcessor
from pipecat.transports.base_transport import BaseTransport

from kenji.app.call import Call, CallSetup
from kenji.app.call_parts import CallIO, CallKit
from kenji.app.dtmf import DtmfLinker
from kenji.app.events import CallEnded, CallEvent
from kenji.app.hub import EventHub
from kenji.app.linking import LinkRegistry
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
        context = self._context(request)
        day = usage_day(context.started_at)
        io = self._io(context.call_id, day)
        if request.viewer_id is not None:
            self._routing.hub.link(context.call_id, request.viewer_id)
        admission = self._admit(request, day, context)
        if not admission.is_admitted:
            return await self._refuse(transport, admission, context, io)
        usage = self._accounting.usage
        usage.record_call(request.transport, request.caller_ref, day)
        try:
            setup = CallSetup(
                context, io, admission.call_seconds_allowed, self._input_processors(context)
            )
            return await Call(self._kit, setup, transport).run()
        finally:
            elapsed = self._kit.clock.now() - context.started_at
            usage.record_seconds(request.transport, day, int(elapsed.total_seconds()))

    def _io(self, call_id: str, day: date) -> CallIO:
        recorder = self._accounting.recorder(call_id, day)
        return CallIO(sink=_FanOut([self._routing.hub.channel(call_id), recorder]), audit=recorder)

    def _input_processors(self, context: CallContext) -> tuple[FrameProcessor, ...]:
        if context.transport != "phone":
            return ()
        routing = self._routing
        return (DtmfLinker(context.call_id, routing.links.redeem, routing.hub.link),)

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
        usage = self._accounting.usage.usage_today(request.transport, request.caller_ref, day)
        return admit_call(context.started_at, usage, self._accounting.limits[request.transport])

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
