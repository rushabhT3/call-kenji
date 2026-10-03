"""Drive the production call assembly in text mode: no audio, no network, scripted talker.

Only the edges are replaced (see doubles.py). Flows, tools, domain rules, turn strategy,
transcript, compliance and audit run for real.
"""

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from kenji.adapters.content import load_personas, load_script
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
MAX_CALL_SECS = 300
BROWSER_OPENING_LINES = 2

__all__ = [
    "FixedClock",
    "LiveModels",
    "MemoryContacts",
    "MemoryRecorder",
    "Say",
    "TextCall",
    "TextKit",
    "TextTransport",
    "ToolCall",
    "build_text_kit",
    "launch_text_call",
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
    acknowledgement: str = ""

    def nodes(self) -> list[str]:
        return [event.node for event in self.recorder.of_type("flow_node")]  # type: ignore[union-attr]

    async def wait_for_node(self, node: str) -> None:
        await wait_until(
            lambda: node in self.nodes(), f"node {node}; saw {self.nodes()}", self.wait_secs
        )

    async def opening_played(self) -> None:
        await wait_until(
            lambda: len(self.kenji_lines()) >= BROWSER_OPENING_LINES,
            "the opening to play",
            self.wait_secs,
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

    def kenji_answers(self) -> list[str]:
        return [line for line in self.kenji_lines() if line != self.acknowledgement]

    async def reply(self, text: str) -> None:
        """Say a line, then wait for Kenji's answer to it (not his 「はい、」) or the call's end."""
        heard = len(self.kenji_answers())
        await self.caller_says(text)
        await wait_until(
            lambda: len(self.kenji_answers()) > heard or self.task.done(),
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
        personas=load_personas(CONTENT / "personas.yaml"),
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


def text_call_context(kit: CallKit, persona_id: str | None = None) -> CallContext:
    started_at = kit.clock.now()
    account = kit.personas.account_for(persona_id)
    return CallContext(
        call_id="text-call",
        transport="browser",
        caller_ref="caller-ref",
        started_at=started_at,
        persona_id=kit.personas.resolve(persona_id),
        account=account,
        negotiation=Negotiation(balance_yen=account.balance_yen, today=started_at.date()),
    )


async def start_text_call(
    steps: Sequence[TalkerStep],
    clock: FixedClock | None = None,
    live: LiveModels | None = None,
    persona_id: str | None = None,
) -> TextCall:
    wait_secs = LIVE_WAIT_SECS if live else WAIT_SECS
    return await launch_text_call(
        build_text_kit(steps, clock, live), wait_secs=wait_secs, persona_id=persona_id
    )


async def launch_text_call(
    parts: TextKit,
    max_seconds: int = MAX_CALL_SECS,
    wait_secs: float = WAIT_SECS,
    persona_id: str | None = None,
) -> TextCall:
    recorder, transport = MemoryRecorder(), TextTransport()
    io = CallIO(sink=recorder, audit=recorder)
    setup = CallSetup(text_call_context(parts.kit, persona_id), io, max_seconds)
    task = asyncio.create_task(Call(parts.kit, setup, transport).run())
    await asyncio.sleep(0.2)
    await transport.connect()
    return TextCall(
        transport,
        parts.talker,
        parts.speech,
        recorder,
        parts.contacts,
        parts.advice,
        task,
        wait_secs,
        parts.kit.script.lines.acknowledgement.ja,
    )
