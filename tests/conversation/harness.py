"""Drive the production call assembly in text mode: no audio, no network, scripted talker.

Only the edges are replaced: the transport, speech services, talker and strategist models.
Flows, tools, domain rules, turn strategy, transcript, compliance and audit run for real.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator, Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
    FunctionCallFromLLM,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.aggregators.llm_response_universal import LLMUserAggregatorParams
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.llm_service import LLMService
from pipecat.services.settings import LLMSettings, TTSSettings
from pipecat.services.tts_service import TTSService
from pipecat.transports.base_transport import BaseTransport
from pipecat.turns.user_start import BaseUserTurnStartStrategy
from pipecat.turns.user_stop import ExternalUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat.utils.time import time_now_iso8601

from kenji.adapters.content import load_account, load_script
from kenji.app.call import Call, CallSetup
from kenji.app.call_parts import CallIO, CallKit, VoiceServices
from kenji.app.events import CallEvent, TranscriptLine
from kenji.app.ports import AdviceModel, TalkerFactory
from kenji.app.session import CallContext
from kenji.domain.audit import AuditEntry, AuditRecord, append_entry
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME
from kenji.domain.contact import ContactPreferences, StopContactRequest, record_stop_contact
from kenji.domain.outcome import CallOutcome
from kenji.domain.terms import Negotiation
from kenji.domain.turn import LexiconBackchannelClassifier

CONTENT = Path(__file__).resolve().parents[2] / "content"
AFTERNOON_IN_TOKYO = datetime(2026, 10, 2, 15, 0, tzinfo=JAPAN_STANDARD_TIME)
WAIT_SECS = 8.0
LIVE_WAIT_SECS = 45.0
PLAYOUT_SECS = 0.05


@dataclass(frozen=True)
class Say:
    text: str


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


type TalkerStep = Say | ToolCall


class ScriptedTalker(LLMService):
    """Answers each inference with the next scripted reply or tool call."""

    def __init__(self, steps: Sequence[TalkerStep]) -> None:
        super().__init__(
            settings=LLMSettings(
                model="scripted",
                system_instruction=None,
                temperature=None,
                max_tokens=None,
                top_p=None,
                top_k=None,
                frequency_penalty=None,
                presence_penalty=None,
                seed=None,
                filter_incomplete_user_turns=None,
                user_turn_completion_config=None,
            )
        )
        self._steps = list(steps)
        self.inferences: list[list[dict[str, Any]]] = []
        self.system_instructions: list[str | None] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if not isinstance(frame, LLMContextFrame):
            await self.push_frame(frame, direction)
            return
        self.inferences.append(
            [dict(m) for m in frame.context.get_messages() if isinstance(m, dict)]
        )
        instruction = self._settings.system_instruction
        self.system_instructions.append(instruction if isinstance(instruction, str) else None)
        step = self._steps.pop(0) if self._steps else Say("（台本の終わり）")
        await self.push_frame(LLMFullResponseStartFrame())
        if isinstance(step, ToolCall):
            await self.run_function_calls(
                [
                    FunctionCallFromLLM(
                        function_name=step.name,
                        tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
                        arguments=step.arguments,
                        context=frame.context,
                    )
                ]
            )
        else:
            await self.push_frame(LLMTextFrame(step.text))
        await self.push_frame(LLMFullResponseEndFrame())


class SilentSpeech(TTSService):
    """A speech service that 'speaks' one short silent frame per sentence."""

    def __init__(self) -> None:
        super().__init__(
            push_start_frame=True,
            push_stop_frames=True,
            stop_frame_timeout_s=0.05,
            settings=TTSSettings(model="silent", voice="none", language="ja"),
        )
        self.spoken: list[str] = []

    async def run_tts(self, text: str, context_id: str) -> AsyncGenerator[Frame | None, None]:
        self.spoken.append(text)
        yield TTSAudioRawFrame(
            audio=bytes(320), sample_rate=self.sample_rate, num_channels=1, context_id=context_id
        )


class _Passthrough(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)


class _SpeakingOutput(FrameProcessor):
    """Turns TTS start/stop into the bot-speaking frames a real output transport emits.

    A real transport reports the bot stopped only after the audio has played out, which is
    after the frames queued behind the audio have passed; a short delay reproduces that order.
    """

    def __init__(self) -> None:
        super().__init__()
        self.is_speaking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, TTSStartedFrame):
            self.is_speaking = True
            await self._both_ways(BotStartedSpeakingFrame())
        await self.push_frame(frame, direction)
        if isinstance(frame, TTSStoppedFrame):
            self.create_task(self._stop_after_playout())

    async def _stop_after_playout(self) -> None:
        await asyncio.sleep(PLAYOUT_SECS)
        self.is_speaking = False
        await self._both_ways(BotStoppedSpeakingFrame())

    async def _both_ways(self, frame: Frame) -> None:
        await self.push_frame(frame, FrameDirection.DOWNSTREAM)
        await self.push_frame(type(frame)(), FrameDirection.UPSTREAM)


class TextTransport(BaseTransport):
    def __init__(self) -> None:
        super().__init__()
        self._input = _Passthrough()
        self._output = _SpeakingOutput()
        self._register_event_handler("on_client_connected")
        self._register_event_handler("on_client_disconnected")

    def input(self) -> FrameProcessor:
        return self._input

    def output(self) -> FrameProcessor:
        return self._output

    @property
    def is_bot_speaking(self) -> bool:
        return self._output.is_speaking

    async def connect(self) -> None:
        await self._call_event_handler("on_client_connected", None)

    async def disconnect(self) -> None:
        await self._call_event_handler("on_client_disconnected", None)

    async def caller_says(self, text: str) -> None:
        await self._input.push_frame(
            TranscriptionFrame(text=text, user_id="caller", timestamp=time_now_iso8601())
        )
        await self._input.push_frame(UserStoppedSpeakingFrame())


class _Factory:
    def __init__(self, create: Callable[[], Any]) -> None:
        self.create = create


class _Talker:
    def __init__(self, talker: ScriptedTalker) -> None:
        self._talker = talker

    def create(self, system_instruction: str) -> LLMService:
        self._talker._settings.system_instruction = system_instruction
        return self._talker


class TextTurnDetection:
    def user_params(self, start: BaseUserTurnStartStrategy) -> LLMUserAggregatorParams:
        return LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                start=[start], stop=[ExternalUserTurnStopStrategy(timeout=0.05)]
            )
        )


class FixedClock:
    def __init__(self, now: datetime = AFTERNOON_IN_TOKYO) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class MemoryRecorder:
    def __init__(self) -> None:
        self.events: list[CallEvent] = []
        self._records: list[AuditRecord] = []

    def publish(self, event: CallEvent) -> None:
        self.events.append(event)

    def append(self, entry: AuditEntry) -> AuditRecord:
        record = append_entry(self._records[-1] if self._records else None, entry)
        self._records.append(record)
        return record

    def records(self) -> list[AuditRecord]:
        return list(self._records)

    def of_type(self, kind: str) -> list[CallEvent]:
        return [event for event in self.events if event.type == kind]


class MemoryContacts:
    def __init__(self) -> None:
        self._preferences = ContactPreferences()

    def record(self, request: StopContactRequest) -> None:
        self._preferences = record_stop_contact(self._preferences, request)

    def preferences(self) -> ContactPreferences:
        return self._preferences


class CannedAdvice:
    def __init__(self, next_move: str = "Offer ¥6,000 × 6 from 16 Oct.") -> None:
        self.calls = 0
        self.requests: list[tuple[str, str, dict[str, Any]]] = []
        self._next_move = next_move

    async def advise(
        self, system_prompt: str, conversation: str, json_schema: dict[str, Any]
    ) -> str:
        self.calls += 1
        self.requests.append((system_prompt, conversation, json_schema))
        return json.dumps(
            {
                "identity": "Caller claims to be Yuki Sato.",
                "situation": "Short of money this month.",
                "ability_to_pay": "partial: can pay a little each month",
                "offers": ["¥6,000 × 6 from 16 Oct"],
                "next_move": self._next_move,
            }
        )


class EchoTranslator:
    async def translate(self, japanese: str) -> str:
        return f"[en] {japanese}"


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
