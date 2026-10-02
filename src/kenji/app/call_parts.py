"""Everything one call needs besides the audio pipeline, built from shared dependencies."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from kenji.app.agreement import describe_plan_en, format_date_en, format_yen
from kenji.app.events import StrategistUpdated
from kenji.app.fast_path import FastPathParts, FastPathPlanner
from kenji.app.flows import CallFlow
from kenji.app.latency import LatencyTracker
from kenji.app.ports import (
    AdviceModel,
    AuditLog,
    Clock,
    ContactStore,
    EventSink,
    SpeechToTextFactory,
    TalkerFactory,
    TextToSpeechFactory,
    Translator,
    TurnDetection,
)
from kenji.app.script import Script
from kenji.app.session import CallContext, CallSession
from kenji.app.strategist import Advice, Strategist, StrategistInjector, render_conversation
from kenji.app.tools import CallTools
from kenji.app.transcript import TranscriptFeed
from kenji.domain.account import Account
from kenji.domain.terms import smallest_acceptable_monthly, suggested_plans
from kenji.domain.turn import BackchannelClassifier


@dataclass(frozen=True, slots=True)
class VoiceServices:
    speech_to_text: SpeechToTextFactory
    text_to_speech: TextToSpeechFactory
    talker: TalkerFactory
    turn_detection: TurnDetection


@dataclass(frozen=True, slots=True)
class CallKit:
    script: Script
    account: Account
    voice: VoiceServices
    advice_model: AdviceModel
    translator: Translator
    classifier: BackchannelClassifier
    contacts: ContactStore
    clock: Clock


@dataclass(frozen=True, slots=True)
class CallIO:
    sink: EventSink
    audit: AuditLog


@dataclass(frozen=True, slots=True)
class CallParts:
    io: CallIO
    session: CallSession
    flow: CallFlow
    feed: TranscriptFeed
    strategist: Strategist
    injector: StrategistInjector
    planner: FastPathPlanner
    latency: LatencyTracker
    talker_instruction: str

    def conversation(self, messages: Sequence[object]) -> str:
        return render_conversation(
            messages, step=self.session.node, identity=self.session.identity_status.value
        )


def _persona_fields(kit: CallKit, context: CallContext) -> dict[str, str]:
    account, terms = kit.account, context.negotiation.terms
    return {
        "debtor_name": account.debtor.written_name,
        "balance_yen": format_yen(account.balance_yen),
        "overdue_since_en": format_date_en(account.overdue_since),
        "today": format_date_en(context.negotiation.today),
        "smallest_monthly": format_yen(smallest_acceptable_monthly(context.negotiation)),
        "suggested_plans": "; ".join(
            describe_plan_en(plan) for plan in suggested_plans(context.negotiation)
        ),
        "minimum_monthly": format_yen(terms.minimum_monthly_yen),
        "maximum_installments": str(terms.maximum_installments),
        "first_payment_within_days": str(terms.first_payment_within_days),
    }


def _publish_advice(sink: EventSink) -> Callable[[Advice], None]:
    def publish(advice: Advice) -> None:
        sink.publish(StrategistUpdated(**advice.model_dump()))

    return publish


def build_call_parts(kit: CallKit, context: CallContext, io: CallIO) -> CallParts:
    prompts = kit.script.prompts
    fields = _persona_fields(kit, context)
    session = CallSession(context, io.sink, io.audit, kit.clock)
    feed = TranscriptFeed(io.sink, kit.translator, kit.clock)
    tools = CallTools(session, kit.contacts)
    flow = CallFlow(kit.script, session, tools, feed.expect_scripted)
    for waiting_line in (
        kit.script.lines.acknowledgement,
        kit.script.lines.holding,
        kit.script.lines.answer_failed,
    ):
        feed.expect_scripted(waiting_line)
    planner = FastPathPlanner(
        FastPathParts(
            flow=flow,
            tools=tools,
            session=session,
            debtor=kit.account.debtor,
            lines=kit.script.lines,
            on_line=feed.expect_scripted,
        )
    )
    strategist = Strategist(
        kit.advice_model, prompts.strategist_system.format_map(fields), _publish_advice(io.sink)
    )

    def hint(caller_turn: int) -> str | None:
        next_move = strategist.next_move_before(caller_turn)
        return None if next_move is None else prompts.strategist_hint.format(next_move=next_move)

    return CallParts(
        io=io,
        session=session,
        flow=flow,
        feed=feed,
        strategist=strategist,
        injector=StrategistInjector(hint),
        planner=planner,
        latency=LatencyTracker(io.sink),
        talker_instruction=prompts.talker_role.format_map(fields),
    )
