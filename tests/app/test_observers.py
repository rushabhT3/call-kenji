"""Kenji's sentences reach the transcript as their audio starts, with their original text."""

from pipecat.frames.frames import AggregatedTextFrame, Frame, TTSTextFrame
from pipecat.observers.base_observer import FramePushed
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.base_output import BaseOutputTransport
from pipecat.transports.base_transport import TransportParams

from kenji.app.observers import SpokenSentenceObserver

SENTENCE = "ご確認ありがとうございます。"


def _pushed(source: FrameProcessor, frame: Frame) -> FramePushed:
    return FramePushed(
        source=source,
        destination=FrameProcessor(),
        frame=frame,
        direction=FrameDirection.DOWNSTREAM,
        timestamp=0,
    )


async def _heard(source: FrameProcessor, *frames: Frame) -> list[str]:
    heard: list[str] = []
    observer = SpokenSentenceObserver(heard.append)
    for frame in frames:
        await observer.on_push_frame(_pushed(source, frame))
    return heard


async def test_a_sentence_is_reported_as_it_leaves_for_the_caller() -> None:
    sentence = AggregatedTextFrame(text=SENTENCE, aggregated_by="sentence")

    heard = await _heard(BaseOutputTransport(TransportParams()), sentence)

    assert heard == [SENTENCE]


async def test_word_by_word_text_is_not_reported_again() -> None:
    word = TTSTextFrame(text="ご確認", aggregated_by="word")

    heard = await _heard(BaseOutputTransport(TransportParams()), word)

    assert heard == []


async def test_a_sentence_still_on_its_way_to_the_speaker_is_ignored() -> None:
    sentence = AggregatedTextFrame(text=SENTENCE, aggregated_by="sentence")

    heard = await _heard(FrameProcessor(), sentence)

    assert heard == []
