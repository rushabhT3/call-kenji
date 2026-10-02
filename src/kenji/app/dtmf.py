"""Keypad digits from a phone call link it to the one browser tab showing that code."""

from collections.abc import Callable

from loguru import logger
from pipecat.frames.frames import Frame, InputDTMFFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from kenji.app.linking import CODE_LENGTH

type Redeem = Callable[[str, str], str | None]
type Link = Callable[[str, str], bool]


class DtmfLinker(FrameProcessor):
    def __init__(self, call_id: str, redeem: Redeem, link: Link) -> None:
        super().__init__()
        self._call_id = call_id
        self._redeem = redeem
        self._link = link
        self._digits = ""
        self._is_linked = False

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, InputDTMFFrame) and not self._is_linked:
            self._collect(str(frame.button.value))
        await self.push_frame(frame, direction)

    def _collect(self, key: str) -> None:
        if not key.isdigit():
            self._digits = ""
            return
        self._digits = (self._digits + key)[-CODE_LENGTH:]
        if len(self._digits) == CODE_LENGTH:
            self._try_link(self._digits)
            self._digits = ""

    def _try_link(self, code: str) -> None:
        viewer_id = self._redeem(self._call_id, code)
        if viewer_id is not None and self._link(self._call_id, viewer_id):
            self._is_linked = True
            logger.info("phone call linked to a browser tab", call_id=self._call_id)
        else:
            logger.info("keypad code did not match a waiting tab", call_id=self._call_id)
