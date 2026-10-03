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


ACKNOWLEDGEMENT = Line(ja="はい、", en="Yes,")
BALANCE = Line(
    ja="ご確認ありがとうございます。改めまして、ケンジです。",
    en="Thank you for confirming. I'm Kenji.",
)


class FlakyTranslator:
    """Times out a given number of times, then translates."""

    def __init__(self, failures: int) -> None:
        self._failures = failures

    async def translate(self, japanese: str) -> str:
        if self._failures > 0:
            self._failures -= 1
            raise TimeoutError
        return f"[en] {japanese}"


def _lines(recorder: MemoryRecorder) -> list[TranscriptLine]:
    return [cast(TranscriptLine, event) for event in recorder.of_type("transcript")]


def _subtitles(recorder: MemoryRecorder) -> list[Subtitle]:
    return [cast(Subtitle, event) for event in recorder.of_type("subtitle")]


def _finals(recorder: MemoryRecorder) -> list[str]:
    return [line.ja for line in _lines(recorder) if line.is_final]


def test_a_scripted_line_shows_with_its_english_from_its_first_sentence() -> None:
    feed, recorder = _feed()
    feed.expect_scripted(BALANCE)

    feed.kenji_speaking("ご確認ありがとうございます。")

    first = _lines(recorder)[0]
    assert not first.is_final
    assert first.ja == "ご確認ありがとうございます。"
    assert _subtitles(recorder)[0].en == BALANCE.en


async def test_the_instant_acknowledgement_opens_the_line_of_the_answer() -> None:
    feed, recorder = _feed()
    feed.expect_lead(ACKNOWLEDGEMENT)

    feed.kenji_speaking("はい、")
    feed.kenji_speaking("承知いたしました。")
    feed.kenji_said("承知いたしました。")
    await feed.drain()

    assert _finals(recorder) == ["はい、承知いたしました。"]
    assert len({line.line_id for line in _lines(recorder)}) == 1
    assert _subtitles(recorder)[-1].en == "Yes, [en] 承知いたしました。"


async def test_an_acknowledgement_waits_for_its_answer_while_the_caller_speaks() -> None:
    feed, recorder = _feed()
    feed.expect_lead(ACKNOWLEDGEMENT)

    feed.kenji_speaking("はい、")
    feed.caller_said("月9,000円でお願いします。")
    feed.kenji_speaking("承知いたしました。")
    feed.kenji_said("承知いたしました。")
    await feed.drain()

    assert _finals(recorder) == ["月9,000円でお願いします。", "はい、承知いたしました。"]


async def test_a_line_the_caller_cut_into_is_closed_when_they_finish() -> None:
    feed, recorder = _feed()

    feed.kenji_speaking("それでは、お約束の内容を確認させていただきます。")
    feed.caller_said("あ、すみません。")
    await feed.drain()

    assert _finals(recorder) == [
        "それでは、お約束の内容を確認させていただきます。",
        "あ、すみません。",
    ]


async def test_an_acknowledgement_whose_answer_never_came_is_closed_when_the_call_ends() -> None:
    feed, recorder = _feed()
    feed.expect_lead(ACKNOWLEDGEMENT)

    feed.kenji_speaking("はい、")
    await feed.drain()

    assert _finals(recorder) == ["はい、"]
    assert _subtitles(recorder)[0].en == "Yes,"


def test_lines_that_start_alike_wait_for_the_words_that_tell_them_apart() -> None:
    feed, recorder = _feed()
    feed.expect_scripted(Line(ja="申し訳ございません。もう一度お願いします。", en="Once more?"))
    feed.expect_scripted(Line(ja="申し訳ございません。お受けできません。", en="We can't."))

    feed.kenji_speaking("申し訳ございません。")
    undecided = list(_subtitles(recorder))
    feed.kenji_speaking("お受けできません。")

    assert undecided == []
    assert _subtitles(recorder)[-1].en == "We can't."


async def test_a_line_kenji_left_open_is_closed_when_the_call_ends() -> None:
    feed, recorder = _feed()

    feed.kenji_speaking("ご確認ありがとうございます。")
    await feed.drain()

    assert _finals(recorder) == ["ご確認ありがとうございます。"]


async def test_a_translation_that_times_out_once_is_tried_again() -> None:
    recorder = MemoryRecorder()
    feed = TranscriptFeed(recorder, FlakyTranslator(failures=1), FixedClock())

    feed.kenji_said("承知いたしました。")
    await feed.drain()

    subtitle = _subtitles(recorder)[-1]
    assert subtitle.en == "[en] 承知いたしました。"
    assert not subtitle.is_unavailable


async def test_a_line_whose_translation_never_comes_back_says_so() -> None:
    recorder = MemoryRecorder()
    feed = TranscriptFeed(recorder, FlakyTranslator(failures=2), FixedClock())

    feed.kenji_said("承知いたしました。")
    await feed.drain()

    assert _subtitles(recorder)[-1].is_unavailable


def test_the_next_line_started_before_this_one_was_reported_keeps_its_own_line() -> None:
    feed, recorder = _feed()
    feed.expect_scripted(GREETING)
    feed.expect_scripted(BALANCE)

    feed.kenji_speaking(GREETING.ja)
    feed.kenji_speaking("ご確認ありがとうございます。")
    feed.kenji_said(GREETING.ja)

    lines = _lines(recorder)
    assert _finals(recorder) == [GREETING.ja]
    assert lines[-1].ja == "ご確認ありがとうございます。"
    assert lines[-1].line_id != lines[0].line_id
    assert _subtitles(recorder)[-1].en == BALANCE.en
