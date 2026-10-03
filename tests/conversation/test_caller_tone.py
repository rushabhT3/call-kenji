"""Kenji hears how the caller sounds on each turn: on its transcript line, and to the strategist."""

from dataclasses import replace
from typing import cast

import pytest

from kenji.app.events import CallerToneHeard, TranscriptLine
from tests.conversation.doubles import FixedToneClassifier
from tests.conversation.harness import (
    Say,
    TextCall,
    build_text_kit,
    launch_text_call,
    start_text_call,
    wait_until,
)
from tests.conversation.test_scenarios import IDENTITY_ANSWER

SPEECH_SECS = 0.8
TONE_NOTE = "The caller's voice on that last turn: angry; laughter."
STRUGGLING = "今月は少し厳しいです。"


async def _call_that_hears(classifier: FixedToneClassifier) -> TextCall:
    parts = build_text_kit([Say("ご事情をお聞かせいただけますか。")])
    return await launch_text_call(
        replace(parts, kit=replace(parts.kit, emotion_classifier=classifier))
    )


async def _two_spoken_turns(call: TextCall) -> None:
    await call.opening_played()
    await call.transport.caller_speaks_for(SPEECH_SECS)
    await call.caller_says(IDENTITY_ANSWER, then_node="state_balance")
    await call.bot_finishes_speaking()
    await call.transport.caller_speaks_for(SPEECH_SECS)
    await call.reply(STRUGGLING)
    await wait_until(lambda: len(call.advice.requests) == 2, "advice on both turns")


def _caller_line_ids(call: TextCall) -> list[str]:
    lines = cast(list[TranscriptLine], call.recorder.of_type("transcript"))
    return [line.line_id for line in lines if line.speaker == "caller" and line.is_final]


async def test_each_turn_is_heard_once_and_shown_on_its_own_line() -> None:
    classifier = FixedToneClassifier()
    call = await _call_that_hears(classifier)

    await _two_spoken_turns(call)
    await call.hang_up()

    tones = cast(list[CallerToneHeard], call.recorder.of_type("caller_tone"))
    assert [tone.line_id for tone in tones] == _caller_line_ids(call)
    assert [audio.seconds for audio in classifier.heard] == [pytest.approx(SPEECH_SECS)] * 2


async def test_the_strategist_hears_how_the_caller_sounded() -> None:
    call = await _call_that_hears(FixedToneClassifier())

    await _two_spoken_turns(call)
    await call.hang_up()

    conversations = [conversation for _, conversation, _ in call.advice.requests]
    assert all(conversation.endswith(TONE_NOTE) for conversation in conversations)


async def test_without_a_model_no_turn_is_heard() -> None:
    call = await start_text_call([Say("ご事情をお聞かせいただけますか。")])

    await _two_spoken_turns(call)
    await call.hang_up()

    assert call.recorder.of_type("caller_tone") == []
    assert not any("caller's voice" in conversation for _, conversation, _ in call.advice.requests)
