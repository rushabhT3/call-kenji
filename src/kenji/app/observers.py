"""Pipeline observers that feed the live page without changing the pipeline."""

from collections.abc import Callable

from pipecat.frames.frames import InterimTranscriptionFrame
from pipecat.observers.base_observer import BaseObserver, FramePushed


class InterimTranscriptObserver(BaseObserver):
    def __init__(self, on_partial: Callable[[str], None]) -> None:
        super().__init__(observe_every_push=False)
        self._on_partial = on_partial

    async def on_push_frame(self, data: FramePushed) -> None:
        frame = data.frame
        if isinstance(frame, InterimTranscriptionFrame) and frame.text:
            self._on_partial(frame.text)
