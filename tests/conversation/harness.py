"""Drive the production call assembly in text mode: no audio, no network, scripted talker.

Only the edges are replaced (see doubles.py). Flows, tools, domain rules, turn strategy,
transcript, compliance and audit run for real.
"""

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from kenji.adapters.content import load_account, load_script
from kenji.app.call import Call, CallSetup
from kenji.app.call_parts import CallIO, CallKit, VoiceServices
from kenji.app.events import TranscriptLine
from kenji.app.ports import AdviceModel, TalkerFactory
from kenji.app.session import CallContext
from kenji.domain.outcome import CallOutcome
from kenji.domain.terms import Negotiation
from kenji.domain.turn import LexiconBackchannelClassifier
from tests.conversation.doubles import (
    CONTENT,
    PLAYOUT_SECS,
    CannedAdvice,
    EchoTranslator,
    FixedClock,
    MemoryContacts,
    MemoryRecorder,
    Say,
    ScriptedTalker,
    SilentSpeech,
    TalkerStep,
    TextTransport,
    TextTurnDetection,
    ToolCall,
    _Factory,
    _Passthrough,
    _Talker,
)

WAIT_SECS = 8.0
LIVE_WAIT_SECS = 45.0

__all__ = [
    "FixedClock",
    "LiveModels",
    "MemoryContacts",
    "MemoryRecorder",
    "Say",
    "TextCall",
    "TextTransport",
    "ToolCall",
    "build_text_kit",
    "start_text_call",
    "wait_until",
]


@dataclass
class TextCall:
    transport: TextTransport
    talker: ScriptedTalker
    speech: SilentSpeech
    recorder: MemoryRecorder
    contacts: MemoryContacts
    advice: CannedAdvice
    task: "asyncio.Task[CallOutcome]"
    wait_secs: float = WAIT_SECS

    def nodes(self) -> list[str]:
        return [event.node for event in self.recorder.of_type("flow_node")]  # type: ignore[union-attr]

    async def wait_for_node(self, node: str) -> None:
        await wait_until(
            lambda: node in self.nodes(), f"node {node}; saw {self.nodes()}", self.wait_secs
        )

    async def caller_says(self, text: str, then_node: str | None = None) -> None:
        await self.bot_finishes_speaking()
        await self.transport.caller_says(text)
        if then_node is not None:
            await self.wait_for_node(then_node)

    async def bot_finishes_speaking(self) -> None:
        await asyncio.sleep(PLAYOUT_SECS * 4)
        await wait_until(
            lambda: not self.transport.is_bot_speaking, "the bot to stop speaking", self.wait_secs
        )

    def kenji_lines(self) -> list[str]:
        lines = self.recorder.of_type("transcript")
        return [
            line.ja
            for line in lines
            if isinstance(line, TranscriptLine) and line.speaker == "kenji"
        ]

    async def reply(self, text: str) -> None:
        """Say a line, then wait for Kenji to answer it or for the call to end."""
        heard = len(self.kenji_lines())
        await self.caller_says(text)
        await wait_until(
            lambda: len(self.kenji_lines()) > heard or self.task.done(),
            f"a reply to {text!r}",
            self.wait_secs,
        )
        await self.bot_finishes_speaking()

    async def finish(self) -> CallOutcome:
        return await asyncio.wait_for(self.task, self.wait_secs)

    async def hang_up(self) -> CallOutcome:
        await self.transport.disconnect()
        return await self.finish()


async def wait_until(
    condition: Callable[[], bool], what: str, timeout_secs: float = WAIT_SECS
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_secs
    while not condition():
        if asyncio.get_running_loop().time() > deadline:
            raise TimeoutError(f"timed out waiting for {what}")
        await asyncio.sleep(0.02)


@dataclass
class TextKit:
    kit: CallKit
    talker: ScriptedTalker
    speech: SilentSpeech
    contacts: MemoryContacts
    advice: CannedAdvice


@dataclass(frozen=True)
class LiveModels:
    """Real language models in place of the scripted talker and canned strategist."""

    talker: TalkerFactory
    advice: AdviceModel


def build_text_kit(
    steps: Sequence[TalkerStep], clock: FixedClock | None = None, live: LiveModels | None = None
) -> TextKit:
    talker, speech = ScriptedTalker(steps), SilentSpeech()
    contacts, advice = MemoryContacts(), CannedAdvice()
    kit = CallKit(
        script=load_script(CONTENT / "script_ja.yaml"),
        account=load_account(CONTENT / "account.yaml"),
        voice=VoiceServices(
            speech_to_text=_Factory(_Passthrough),
            text_to_speech=_Factory(lambda: speech),
            talker=live.talker if live else _Talker(talker),
            turn_detection=TextTurnDetection(),
        ),
        advice_model=live.advice if live else advice,
        translator=EchoTranslator(),
        classifier=LexiconBackchannelClassifier(),
        contacts=contacts,
        clock=clock or FixedClock(),
    )
    return TextKit(kit, talker, speech, contacts, advice)


def text_call_context(kit: CallKit) -> CallContext:
    started_at = kit.clock.now()
    return CallContext(
        call_id="text-call",
        transport="browser",
        caller_ref="caller-ref",
        started_at=started_at,
        account=kit.account,
        negotiation=Negotiation(balance_yen=kit.account.balance_yen, today=started_at.date()),
    )


async def start_text_call(
    steps: Sequence[TalkerStep],
    clock: FixedClock | None = None,
    live: LiveModels | None = None,
) -> TextCall:
    parts = build_text_kit(steps, clock, live)
    recorder, transport = MemoryRecorder(), TextTransport()
    setup = CallSetup(text_call_context(parts.kit), CallIO(sink=recorder, audit=recorder), 300)
    task = asyncio.create_task(Call(parts.kit, setup, transport).run())
    await asyncio.sleep(0.2)
    await transport.connect()
    wait_secs = LIVE_WAIT_SECS if live else WAIT_SECS
    return TextCall(
        transport,
        parts.talker,
        parts.speech,
        recorder,
        parts.contacts,
        parts.advice,
        task,
        wait_secs,
    )
