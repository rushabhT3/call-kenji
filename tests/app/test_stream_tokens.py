from datetime import timedelta

from kenji.app.stream_tokens import STREAM_TOKEN_TTL, StreamGrant, StreamTokens
from tests.conversation.harness import FixedClock


def test_token_opens_one_stream_for_its_caller_and_persona() -> None:
    tokens = StreamTokens(FixedClock())
    token = tokens.issue(StreamGrant("caller-a", persona_id="tanaka"))

    assert tokens.redeem(token) == StreamGrant("caller-a", persona_id="tanaka")
    assert tokens.redeem(token) is None


def test_unknown_tokens_open_nothing() -> None:
    assert StreamTokens(FixedClock()).redeem("guess") is None


def test_tokens_expire() -> None:
    clock = FixedClock()
    tokens = StreamTokens(clock)
    token = tokens.issue(StreamGrant("caller-a"))
    clock.current += STREAM_TOKEN_TTL + timedelta(seconds=1)

    assert tokens.redeem(token) is None
