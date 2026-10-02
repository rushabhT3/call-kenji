"""A call stays inside its limits: the time cap ends it, a stuck strategist never slows Kenji."""

import asyncio
from dataclasses import replace
from typing import Any

from kenji.app.strategist import STRATEGIST_TIMEOUT_SECS
from kenji.domain.outcome import CallOutcome
from tests.conversation.harness import (
    Say,
    build_text_kit,
    launch_text_call,
    wait_until,
)
from tests.conversation.test_scenarios import IDENTITY_ANSWER, VERIFY


class HangingAdvice:
    """A strategist model that is consulted but never answers."""

    def __init__(self) -> None:
        self.calls = 0

    async def advise(
        self,
        system_prompt: str,  # noqa: ARG002
        conversation: str,  # noqa: ARG002
        json_schema: dict[str, Any],  # noqa: ARG002
    ) -> str:
        self.calls += 1
        await asyncio.Event().wait()
        raise AssertionError("a hanging strategist never answers")


async def test_call_says_goodbye_and_ends_at_its_time_limit() -> None:
    parts = build_text_kit([])
    call = await launch_text_call(parts, max_seconds=1)

    outcome = await call.finish()

    assert parts.kit.script.lines.time_up.ja in call.kenji_lines()
    assert "time_limit_reached" in [record.entry.kind for record in call.recorder.records()]
    assert outcome is CallOutcome.IDENTITY_NOT_VERIFIED


async def test_a_strategist_that_never_answers_does_not_slow_kenji() -> None:
    advice = HangingAdvice()
    parts = build_text_kit([VERIFY, Say("ご事情をお聞かせいただけますか。")])
    call = await launch_text_call(replace(parts, kit=replace(parts.kit, advice_model=advice)))
    await call.wait_for_node("verify_identity")
    await call.caller_says(IDENTITY_ANSWER, then_node="listen")
    await call.bot_finishes_speaking()

    loop = asyncio.get_running_loop()
    heard = len(call.kenji_lines())
    started = loop.time()
    await call.transport.caller_says("今月は少し厳しいです。")
    await wait_until(lambda: len(call.kenji_lines()) > heard, "Kenji's reply")
    reply_secs = loop.time() - started
    await call.hang_up()

    assert advice.calls >= 1
    assert reply_secs < STRATEGIST_TIMEOUT_SECS / 4
