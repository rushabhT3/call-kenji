"""Kenji's words that only announce a step the system then speaks for him are left unsaid."""

from loguru import logger
from pipecat.frames.frames import (
    Frame,
    FunctionCallsStartedFrame,
    InterruptionFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

# Each of these moves the call to a step that opens with a scripted line: the balance, the
# read-back, a closing. Words the model says before calling one only announce that line.
SCRIPTED_HANDOVERS = frozenset(
    {
        "verify_identity",
        "third_party_answered",
        "confirm_plan",
        "record_promise",
        "request_human",
        "record_stop_contact",
        "end_without_agreement",
    }
)

type _ResponseFrame = LLMFullResponseStartFrame | LLMTextFrame | LLMFullResponseEndFrame


class HandoverNarrationFilter(FrameProcessor):
    """Holds each model response until it ends, and drops one that hands over to a scripted step.

    Told to say nothing before these tools, Muse Spark narrated as often and grew less reliable,
    so the response is dropped here instead, start and end included: the scripted line then
    opens and closes its own turn, as every scripted line does. Muse delivers a response in one
    burst, so holding it to the end costs about a tenth of a second.
    """

    def __init__(self) -> None:
        super().__init__()
        self._held: list[_ResponseFrame] = []
        self._is_handover = False

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if direction is not FrameDirection.DOWNSTREAM:
            await self.push_frame(frame, direction)
        elif isinstance(frame, (LLMFullResponseStartFrame, LLMTextFrame)):
            self._held.append(frame)
        elif isinstance(frame, LLMFullResponseEndFrame):
            self._held.append(frame)
            await self._release()
        else:
            if isinstance(frame, InterruptionFrame):
                self._forget()
            elif isinstance(frame, FunctionCallsStartedFrame):
                self._is_handover |= any(
                    call.function_name in SCRIPTED_HANDOVERS for call in frame.function_calls
                )
            await self.push_frame(frame, direction)

    async def _release(self) -> None:
        held, is_handover = self._held, self._is_handover
        self._forget()
        if is_handover:
            words = "".join(frame.text for frame in held if isinstance(frame, LLMTextFrame))
            logger.debug("left unsaid before a scripted step", words=words)
            return
        for frame in held:
            await self.push_frame(frame)

    def _forget(self) -> None:
        self._held = []
        self._is_handover = False
