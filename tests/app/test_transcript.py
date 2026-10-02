"""Kenji's transcript shows what he meant to say, even when the speech service's text drifts."""

from typing import cast

from kenji.app.events import Subtitle, TranscriptLine
from kenji.app.script import Line
from kenji.app.transcript import TranscriptFeed
from tests.conversation.doubles import EchoTranslator, FixedClock, MemoryRecorder

GREETING = Line(ja="お電話ありがとうございます。ケンジと申します。", en="Thank you for calling.")


def _feed() -> tuple[TranscriptFeed, MemoryRecorder]:
    recorder = MemoryRecorder()
    return TranscriptFeed(recorder, EchoTranslator(), FixedClock()), recorder


def test_scripted_line_is_shown_as_written_with_its_own_subtitle() -> None:
    feed, recorder = _feed()
    feed.expect_scripted(GREETING)

    scripted = feed.kenji_said("お電話ありがとうございます。ケンジと申します。。")

    assert scripted == GREETING
    assert cast(TranscriptLine, recorder.of_type("transcript")[0]).ja == GREETING.ja
    assert cast(Subtitle, recorder.of_type("subtitle")[0]).en == GREETING.en


async def test_model_line_loses_a_repeated_full_stop_before_translation() -> None:
    feed, recorder = _feed()

    scripted = feed.kenji_said("承知いたしました。。")
    await feed.drain()

    assert scripted is None
    assert cast(TranscriptLine, recorder.of_type("transcript")[0]).ja == "承知いたしました。"
    assert cast(Subtitle, recorder.of_type("subtitle")[0]).en == "[en] 承知いたしました。"
