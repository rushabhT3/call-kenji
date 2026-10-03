"""The strategist hears how the caller's voice sounded, not only what they said."""

from kenji.app.ports import CallerTone
from kenji.app.strategist import with_caller_tone

CONVERSATION = "Current step: listen. Identity: verified.\nCaller: 今月は少し厳しいです。"


def test_the_tone_of_the_last_turn_follows_the_conversation() -> None:
    tone = CallerTone(emotion="angry", sounds=("laughter",))

    seen = with_caller_tone(CONVERSATION, tone)

    assert seen == f"{CONVERSATION}\nThe caller's voice on that last turn: angry; laughter."


def test_an_unclear_emotion_is_said_to_be_unclear() -> None:
    seen = with_caller_tone(CONVERSATION, CallerTone(emotion="unknown"))

    assert seen.endswith("The caller's voice on that last turn: no clear emotion.")


def test_a_turn_not_heard_leaves_the_conversation_as_it_was() -> None:
    assert with_caller_tone(CONVERSATION, None) == CONVERSATION
