"""Pipecat Flows nodes for one call: which tools exist at each step, and what Kenji says."""

from collections.abc import Callable
from typing import Any

from pipecat.flows import (
    ActionConfig,
    ConsolidatedFunctionResult,
    FlowArgs,
    FlowManager,
    FlowsDirectFunction,
    FlowsFunctionSchema,
    NodeConfig,
)
from pipecat.frames.frames import TTSSpeakFrame

from kenji.app.agreement import describe_balance, describe_read_back
from kenji.app.script import Line, Script
from kenji.app.session import CallSession
from kenji.app.tools import CallTools, NodeName, ToolOutcome
from kenji.domain.account import AccountLocked
from kenji.domain.turn import TurnPolicy

_PARAMETER_TYPES = {
    "name_kana": "string",
    "date_of_birth": "string",
    "monthly_yen": "integer",
    "first_payment_date": "string",
    "reason": "string",
    "summary": "string",
}
_OPTIONAL_PARAMETERS = frozenset({"first_payment_date"})
_CLOSING_POLICY = TurnPolicy(min_interruption_score=0.85)
# Flows' own tts_say counts as pending until its finish marker reaches the end of the
# pipeline. An interruption drops that marker, and every later step that waits on pending
# actions then waits forever, so scripted lines are queued as plain speech instead.
_SAY_SCRIPTED = "say_scripted"

type ToolRunner = Callable[[FlowArgs], ToolOutcome]
type LineSpoken = Callable[[Line], None]


def _text(args: FlowArgs, name: str) -> str:
    return str(args.get(name, ""))


def _optional_text(args: FlowArgs, name: str) -> str | None:
    value = args.get(name)
    return str(value) if value else None


async def _say_scripted(action: dict[str, Any], flow_manager: FlowManager) -> None:
    await flow_manager.worker.queue_frame(TTSSpeakFrame(str(action["text"])))


class CallFlow:
    def __init__(
        self, script: Script, session: CallSession, tools: CallTools, on_line: LineSpoken
    ) -> None:
        self._script = script
        self._session = session
        self._tools = tools
        self._on_line = on_line
        self._step_after_speech: NodeName | None = None

    def turn_policy(self) -> TurnPolicy:
        node = getattr(self._script.nodes, self._session.node, None)
        return _CLOSING_POLICY if node is None else node.turn_policy

    def when_caller_speaks(self) -> NodeConfig | None:
        """A step that ends with Kenji speaking gives way to the next when the caller replies.

        The caller's reply, not the end of the speech, is the boundary: the strict turn policy
        holds while Kenji is still talking, and the next step's tools are in place before the
        model answers.
        """
        target = self._step_after_speech
        return None if target is None else self._enter(target, respond=False)

    def initial_node(self) -> NodeConfig:
        return self._enter(NodeName.GREETING, respond=False)

    def global_functions(self) -> list[FlowsFunctionSchema | FlowsDirectFunction]:
        tools = self._tools
        return [
            self._schema(
                "request_human",
                lambda a: tools.request_human(_text(a, "reason"), _text(a, "summary")),
            ),
            self._schema("record_stop_contact", lambda _: tools.record_stop_contact()),
            self._schema(
                "end_without_agreement", lambda a: tools.end_without_agreement(_text(a, "reason"))
            ),
        ]

    def _enter(self, name: NodeName, *, respond: bool) -> NodeConfig:
        self._step_after_speech = None
        self._session.enter_node(name)
        builders: dict[NodeName, Callable[[bool], NodeConfig]] = {
            NodeName.GREETING: self._greeting,
            NodeName.VERIFY_IDENTITY: self._verify_identity,
            NodeName.STATE_BALANCE: self._state_balance,
            NodeName.LISTEN: self._listen,
            NodeName.NEGOTIATE: self._negotiate,
            NodeName.READ_BACK: self._read_back,
        }
        build = builders.get(name)
        return build(respond) if build else self._ending(name)

    def _greeting(self, respond: bool) -> NodeConfig:
        lines = self._script.lines
        is_phone = self._session.context.transport == "phone"
        opening = [lines.greeting, *([lines.link_prompt] if is_phone else []), lines.ask_identity]
        return self._node(
            NodeName.GREETING,
            functions=[self._verify_identity_tool(), self._third_party_tool()],
            respond=respond,
            say=opening,
            then=NodeName.VERIFY_IDENTITY,
        )

    def _verify_identity(self, respond: bool) -> NodeConfig:
        return self._node(
            NodeName.VERIFY_IDENTITY,
            functions=[self._verify_identity_tool(), self._third_party_tool()],
            respond=respond,
        )

    def _state_balance(self, respond: bool) -> NodeConfig:
        summary = self._session.account_summary()
        if isinstance(summary, AccountLocked):
            raise RuntimeError("the balance can only be stated after identity is verified")
        return self._node(
            NodeName.STATE_BALANCE,
            functions=[self._account_summary_tool()],
            respond=respond,
            say=describe_balance(self._script.lines, summary),
            then=NodeName.LISTEN,
        )

    def _listen(self, respond: bool) -> NodeConfig:
        return self._node(
            NodeName.LISTEN,
            functions=[self._account_summary_tool(), self._terms_tool("check_terms")],
            respond=respond,
        )

    def _negotiate(self, respond: bool) -> NodeConfig:
        return self._node(
            NodeName.NEGOTIATE,
            functions=[
                self._terms_tool("check_terms"),
                self._terms_tool("confirm_plan"),
                self._account_summary_tool(),
            ],
            respond=respond,
        )

    def _read_back(self, respond: bool) -> NodeConfig:
        plan = self._session.confirmed_plan
        if plan is None:
            raise RuntimeError("read-back needs a confirmed plan")
        return self._node(
            NodeName.READ_BACK,
            functions=[
                self._schema("record_promise", lambda _: self._tools.record_promise()),
                self._terms_tool("confirm_plan"),
            ],
            respond=respond,
            say=describe_read_back(self._script.lines, plan),
        )

    def _ending(self, name: NodeName) -> NodeConfig:
        lines = self._script.lines
        closing = {
            NodeName.CLOSE: lines.promise_close
            if self._session.promise
            else lines.no_agreement_close,
            NodeName.THIRD_PARTY: lines.third_party_callback,
            NodeName.HUMAN_HANDOFF: lines.handoff_close,
            NodeName.STOP_CONTACT: lines.stop_contact_close,
            NodeName.IDENTITY_LOCKED: lines.identity_locked,
        }[name]
        self._on_line(closing)
        return NodeConfig(
            name=name,
            task_messages=[],
            functions=[],
            pre_actions=[ActionConfig(type="end_conversation", text=closing.ja)],
            respond_immediately=False,
        )

    def _node(
        self,
        name: NodeName,
        *,
        functions: list[FlowsFunctionSchema],
        respond: bool,
        say: Line | list[Line] | None = None,
        then: NodeName | None = None,
    ) -> NodeConfig:
        task = getattr(self._script.nodes, name).task
        config = NodeConfig(
            name=name,
            task_messages=[{"role": "developer", "content": task}],
            functions=list(functions),
            respond_immediately=respond and not say,
        )
        spoken = [say] if isinstance(say, Line) else (say or [])
        for line in spoken:
            self._on_line(line)
        if spoken:
            config["pre_actions"] = [
                ActionConfig(type=_SAY_SCRIPTED, text=line.ja, handler=_say_scripted)
                for line in spoken
            ]
        self._step_after_speech = then
        return config

    def _verify_identity_tool(self) -> FlowsFunctionSchema:
        return self._schema(
            "verify_identity",
            lambda a: self._tools.verify_identity(_text(a, "name_kana"), _text(a, "date_of_birth")),
        )

    def _third_party_tool(self) -> FlowsFunctionSchema:
        return self._schema("third_party_answered", lambda _: self._tools.third_party_answered())

    def _account_summary_tool(self) -> FlowsFunctionSchema:
        return self._schema("get_account_summary", lambda _: self._tools.get_account_summary())

    def _terms_tool(self, name: str) -> FlowsFunctionSchema:
        run = self._tools.check_terms if name == "check_terms" else self._tools.confirm_plan
        return self._schema(
            name,
            lambda a: run(a.get("monthly_yen"), _optional_text(a, "first_payment_date")),
        )

    def _schema(self, name: str, run: ToolRunner) -> FlowsFunctionSchema:
        content = getattr(self._script.tools, name)
        properties = {
            parameter: {"type": _PARAMETER_TYPES[parameter], "description": description}
            for parameter, description in content.parameters.items()
        }

        async def handler(args: FlowArgs, _flow_manager: FlowManager) -> ConsolidatedFunctionResult:
            outcome = run(args)
            next_node = (
                None if outcome.next_node is None else self._enter(outcome.next_node, respond=True)
            )
            return outcome.result, next_node

        return FlowsFunctionSchema(
            name=name,
            description=content.description,
            properties=properties,
            required=[
                parameter for parameter in properties if parameter not in _OPTIONAL_PARAMETERS
            ],
            handler=handler,
            cancel_on_interruption=True,
        )
