"""Pipeline observers that feed the live page without changing the pipeline."""

from collections.abc import Callable

from pipecat.frames.frames import AggregatedTextFrame, InterimTranscriptionFrame
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.transports.base_output import BaseOutputTransport


class InterimTranscriptObserver(BaseObserver):
    def __init__(self, on_partial: Callable[[str], None]) -> None:
        super().__init__(observe_every_push=False)
        self._on_partial = on_partial

    async def on_push_frame(self, data: FramePushed) -> None:
        frame = data.frame
        if isinstance(frame, InterimTranscriptionFrame) and frame.text:
            self._on_partial(frame.text)


class SpokenSentenceObserver(BaseObserver):
    """Tells the transcript each time Kenji starts a sentence, as its audio leaves for the caller.

    The output transport releases each sentence's text frame in step with the audio before it,
    so the frame leaves the transport as the sentence starts playing. It carries the original
    text, not the kana sent to speech synthesis. Its word-level subclass is left out.
    """

    def __init__(self, on_sentence: Callable[[str], None]) -> None:
        super().__init__()
        self._on_sentence = on_sentence

    async def on_push_frame(self, data: FramePushed) -> None:
        frame = data.frame
        if type(frame) is not AggregatedTextFrame or not isinstance(
            data.source, BaseOutputTransport
        ):
            return
        if frame.text.strip():
            self._on_sentence(frame.text.strip())
