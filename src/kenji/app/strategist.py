"""A second model reads each finished caller turn and advises the talker's next move.

It runs beside the conversation, never in front of it. Advice is tagged with the number of
caller turns it was computed from, and the talker only receives advice from an earlier turn:
advice computed after turn N reaches the talker at turn N+1, however fast the model answers.
A slow or failed strategist leaves the call untouched.
"""

import asyncio
from collections.abc import Callable, Sequence
from typing import Any

from loguru import logger
from pipecat.frames.frames import Frame, LLMContextFrame
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kenji.app.ports import AdviceModel, CallerTone

STRATEGIST_TIMEOUT_SECS = 8.0
_TURNS_KEPT = 2
_SPEAKERS = {"user": "Caller", "assistant": "Kenji"}


class Advice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str
    situation: str
    ability_to_pay: str
    offers: list[str] = Field(max_length=3)
    next_move: str


ADVICE_JSON_SCHEMA: dict[str, Any] = Advice.model_json_schema()


def count_caller_turns(messages: Sequence[object]) -> int:
    return sum(
        1 for message in messages if isinstance(message, dict) and message.get("role") == "user"
    )


def render_conversation(messages: Sequence[object], step: str, identity: str) -> str:
    lines = [f"Current step: {step}. Identity: {identity}."]
    for message in messages:
        if not isinstance(message, dict):
            continue
        speaker = _SPEAKERS.get(str(message.get("role")))
        content = message.get("content")
        if speaker and isinstance(content, str) and content:
            lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def with_caller_tone(conversation: str, tone: CallerTone | None) -> str:
    """Add how the caller's voice sounded on the turn just finished, which the words can miss."""
    if tone is None:
        return conversation
    emotion = "no clear emotion" if tone.emotion == "unknown" else tone.emotion
    heard = "; ".join([emotion, *tone.sounds])
    return f"{conversation}\nThe caller's voice on that last turn: {heard}."


class Strategist:
    def __init__(
        self,
        model: AdviceModel,
        system_prompt: str,
        on_advice: Callable[[Advice], None],
        timeout_secs: float = STRATEGIST_TIMEOUT_SECS,
    ) -> None:
        self._model = model
        self._system_prompt = system_prompt
        self._on_advice = on_advice
        self._timeout_secs = timeout_secs
        self._requested_turn = 0
        self._advice_by_turn: dict[int, Advice] = {}

    def next_move_before(self, caller_turn: int) -> str | None:
        earlier = [turn for turn in self._advice_by_turn if turn < caller_turn]
        return self._advice_by_turn[max(earlier)].next_move if earlier else None

    async def advise(self, conversation: str, caller_turn: int) -> None:
        self._requested_turn = caller_turn
        advice = await self._ask(conversation, caller_turn)
        if advice is None or caller_turn != self._requested_turn:
            return
        self._advice_by_turn = {
            turn: kept
            for turn, kept in self._advice_by_turn.items()
            if turn >= caller_turn - _TURNS_KEPT
        } | {caller_turn: advice}
        self._on_advice(advice)

    async def _ask(self, conversation: str, turn: int) -> Advice | None:
        try:
            raw = await asyncio.wait_for(
                self._model.advise(self._system_prompt, conversation, ADVICE_JSON_SCHEMA),
                self._timeout_secs,
            )
            return Advice.model_validate_json(raw)
        except TimeoutError:
            logger.warning("strategist timed out", turn=turn, timeout_secs=self._timeout_secs)
        except ValidationError as error:
            logger.warning("strategist returned invalid advice", turn=turn, error=str(error))
        except Exception:
            logger.exception("strategist failed; the call continues without advice", turn=turn)
        return None


class StrategistInjector(FrameProcessor):
    """Sends the talker a provisional copy of the context that ends with the latest advice."""

    def __init__(self, hint: Callable[[int], str | None]) -> None:
        super().__init__()
        self._hint = hint

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, LLMContextFrame) and not frame.speculation:
            hint = self._hint(count_caller_turns(frame.context.get_messages()))
            if hint:
                frame = LLMContextFrame(context=_with_hint(frame.context, hint))
        await self.push_frame(frame, direction)


def _with_hint(context: LLMContext, hint: str) -> LLMContext:
    return LLMContext(
        messages=[*context.get_messages(), {"role": "developer", "content": hint}],
        tools=context.tools,
        tool_choice=context.tool_choice,
    )
