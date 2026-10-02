"""Answer the predictable caller turns from rules, so Kenji does not wait on the language model.

A matching name and date of birth, a monthly offer, and a plain yes to a plan or to the read-back
run the same tools the model would call and speak scripted lines, in the time speech recognition
and synthesis take. Anything the rules are not sure of goes to the model, after an immediate
「はい、」 so the caller hears Kenji while it thinks.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import date

from loguru import logger
from pipecat.flows import NodeConfig
from pipecat.frames.frames import Frame, LLMContextFrame, TTSSpeakFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from kenji.app.agreement import describe_offer_reply
from kenji.app.events import Opening
from kenji.app.flows import CallFlow, LineSpoken
from kenji.app.script import Line, Lines
from kenji.app.session import CallSession
from kenji.app.tools import CallTools, NodeName, ToolOutcome
from kenji.app.turns import Floor
from kenji.domain.identity import DebtorIdentity
from kenji.domain.terms import (
    PaymentProposal,
    TermsViolation,
    check_terms,
    default_first_payment_date,
    smallest_acceptable_monthly,
)
from kenji.domain.understanding import (
    find_birth_date,
    find_month_day,
    find_monthly_yen,
    is_plain_agreement,
    mentions_relative_timing,
    names_the_debtor,
    only_identity_words,
    only_offer_words,
)

type NodeSetter = Callable[[NodeConfig], Awaitable[None]]

_IDENTITY_STEPS = frozenset({NodeName.GREETING, NodeName.VERIFY_IDENTITY})
_PLAN_STEPS = frozenset({NodeName.STATE_BALANCE, NodeName.LISTEN, NodeName.NEGOTIATE})
# Only the amount can be countered with a scripted line; date problems go to the model.
_AMOUNT_VIOLATIONS = frozenset(
    {TermsViolation.BELOW_MINIMUM_MONTHLY, TermsViolation.TOO_MANY_INSTALLMENTS}
)


@dataclass(frozen=True, slots=True)
class FastReply:
    """What Kenji does instead of asking the model: move to a step, say a line, or both."""

    node: NodeConfig | None = None
    line: Line | None = None


@dataclass(frozen=True, slots=True)
class FastPathParts:
    flow: CallFlow
    tools: CallTools
    session: CallSession
    debtor: DebtorIdentity
    lines: Lines
    on_line: LineSpoken


@dataclass(frozen=True, slots=True)
class Acknowledgement:
    """The word Kenji says at once when the model must answer, and the floor he keeps.

    It stays out of the model's context, so the model's turn is the same with or without it.
    """

    text: str
    floor: Floor
    on_spoken: Callable[[str], object]


@dataclass(frozen=True, slots=True)
class _PendingPlan:
    monthly_yen: int
    first_payment_on: date | None


class FastPathPlanner:
    def __init__(self, parts: FastPathParts) -> None:
        self._parts = parts
        self._pending: _PendingPlan | None = None

    def answer(self, caller_text: str) -> FastReply | None:
        """A reply the rules are sure of, or None to let the model answer."""
        reply = (
            self._identity(caller_text) or self._agreement(caller_text) or self._offer(caller_text)
        )
        if reply is None:
            # The model may now propose something else, so a plain yes must not confirm ours.
            self._pending = None
        return reply

    def _identity(self, text: str) -> FastReply | None:
        parts = self._parts
        if parts.session.node not in _IDENTITY_STEPS:
            return None
        debtor = parts.debtor
        born = find_birth_date(text)
        if born != debtor.date_of_birth or not names_the_debtor(text, debtor):
            return None
        if not only_identity_words(text, debtor):
            return None
        spoken_name = debtor.family_name_kana + debtor.given_name_kana
        return self._follow(
            parts.tools.verify_identity(spoken_name, debtor.date_of_birth.isoformat())
        )

    def _agreement(self, text: str) -> FastReply | None:
        if not is_plain_agreement(text):
            return None
        node, pending, tools = self._parts.session.node, self._pending, self._parts.tools
        if node == NodeName.READ_BACK:
            return self._follow(tools.record_promise())
        if node != NodeName.NEGOTIATE or pending is None:
            return None
        self._pending = None
        first_payment = pending.first_payment_on.isoformat() if pending.first_payment_on else None
        return self._follow(tools.confirm_plan(pending.monthly_yen, first_payment))

    def _offer(self, text: str) -> FastReply | None:
        parts = self._parts
        monthly = find_monthly_yen(text)
        if parts.session.node not in _PLAN_STEPS or monthly is None:
            return None
        if mentions_relative_timing(text) or self._proposed(monthly) or not only_offer_words(text):
            return None
        negotiation = parts.session.negotiation
        first_payment_on = find_month_day(text, negotiation.today)
        proposal = PaymentProposal(
            monthly, first_payment_on or default_first_payment_date(negotiation)
        )
        decision = check_terms(proposal, negotiation)
        if not _counterable(decision.violations) or len(decision.schedule) == 1:
            return None
        counter = smallest_acceptable_monthly(negotiation)
        first_payment = first_payment_on.isoformat() if first_payment_on else None
        outcome = parts.tools.check_terms(monthly, first_payment)
        self._pending = _PendingPlan(monthly if decision.is_accepted else counter, first_payment_on)
        line = describe_offer_reply(parts.lines, decision, counter)
        parts.on_line(line)
        node = None if outcome.next_node is None else parts.flow.enter(outcome.next_node)
        return FastReply(node=node, line=line)

    def _proposed(self, monthly_yen: int) -> bool:
        """The caller restating the plan Kenji just proposed: the rules never ask twice."""
        return self._pending is not None and self._pending.monthly_yen == monthly_yen

    def _follow(self, outcome: ToolOutcome) -> FastReply | None:
        if outcome.next_node is None:
            logger.warning("fast path tool did not move the call on; the model answers instead")
            return None
        return FastReply(node=self._parts.flow.enter(outcome.next_node))


def _counterable(violations: Sequence[TermsViolation]) -> bool:
    return set(violations) <= _AMOUNT_VIOLATIONS


def last_caller_text(messages: Sequence[object]) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            return content if isinstance(content, str) else ""
    return ""


class FastPath(FrameProcessor):
    """Sits between the caller's turn and the model, and answers the turns the rules are sure of."""

    def __init__(
        self, planner: FastPathPlanner, acknowledgement: Acknowledgement, set_node: NodeSetter
    ) -> None:
        super().__init__()
        self._planner = planner
        self._acknowledgement = acknowledgement
        self._set_node = set_node
        self.last_opening: Opening = "model"

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if not isinstance(frame, LLMContextFrame) or frame.speculation:
            await self.push_frame(frame, direction)
            return
        reply = self._planner.answer(last_caller_text(frame.context.get_messages()))
        self.last_opening = "acknowledgement" if reply is None else "rules"
        if reply is None:
            acknowledgement = self._acknowledgement
            acknowledgement.floor.hold()
            await self.push_frame(
                TTSSpeakFrame(acknowledgement.text, append_to_context=False), direction
            )
            acknowledgement.on_spoken(acknowledgement.text)
            await self.push_frame(frame, direction)
            return
        if reply.node is not None:
            await self._set_node(reply.node)
        if reply.line is not None:
            await self.push_frame(TTSSpeakFrame(reply.line.ja), direction)
