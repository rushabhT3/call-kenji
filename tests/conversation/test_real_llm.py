"""Smoke run against the real language model: the same five conversations, judged by outcome.

Opt in with `uv run pytest -m real_llm`. It needs LLM_API_KEY (and, for Muse Spark or another
provider, LLM_BASE_URL and the model names) in the environment or .env; without a key it skips.
Assertions are about what the call did (tools, records, outcome), never about exact wording.
"""

from collections.abc import Sequence
from typing import cast

import pytest
from pydantic import ValidationError

from kenji.adapters.openai_models import OpenAIAdviceModel, OpenAITalker
from kenji.app.events import SmsPreview
from kenji.config import LanguageModelSettings
from kenji.container import chat_endpoint
from kenji.domain.outcome import CallOutcome
from tests.conversation.harness import LiveModels, TextCall, start_text_call

IDENTITY = "佐藤ゆうきです。生年月日は1990年7月14日です。"
DEBT_WORDS = ("債権", "回収", "返済", "支払", "延滞", "滞納", "円", "7731")
MAX_TURNS = 8


def _live_models() -> LiveModels:
    try:
        settings = LanguageModelSettings()
    except ValidationError:
        pytest.skip("LLM_API_KEY is not set")
    endpoint = chat_endpoint(settings)
    return LiveModels(
        talker=OpenAITalker(endpoint, settings.talker_model),
        advice=OpenAIAdviceModel(endpoint, settings.strategist_model),
    )


pytestmark = pytest.mark.real_llm


async def _converse(call: TextCall, opening: Sequence[str], persist: str) -> CallOutcome:
    """Say the opening lines, then keep repeating `persist` until the call ends."""
    await call.wait_for_node("verify_identity")
    for line in opening:
        if not call.task.done():
            await call.reply(line)
    for _ in range(MAX_TURNS):
        if call.task.done():
            break
        await call.reply(persist)
    if not call.task.done():
        return await call.hang_up()
    return await call.finish()


async def test_normal_caller_agrees_a_plan_inside_the_terms() -> None:
    call = await start_text_call([], live=_live_models())

    outcome = await _converse(
        call,
        [IDENTITY, "今月は仕事が減って苦しいです。毎月6,000円なら払えます。"],
        "はい、毎月6,000円、初回は来週でお願いします。その内容で大丈夫です。",
    )

    assert outcome is CallOutcome.PROMISE_TO_PAY
    sms = cast(SmsPreview, call.recorder.of_type("sms_preview")[0])
    assert "6,000円" in sms.ja


async def test_spouse_hears_nothing_about_the_debt() -> None:
    call = await start_text_call([], live=_live_models())

    outcome = await _converse(
        call,
        ["佐藤の妻です。主人は今出かけています。"],
        "私は妻です。主人は留守です。",
    )

    assert outcome is CallOutcome.CALLBACK_REQUESTED
    for line in call.kenji_lines():
        assert not any(word in line for word in DEBT_WORDS), line


async def test_hard_bargainer_never_gets_3000_yen() -> None:
    call = await start_text_call([], live=_live_models())

    outcome = await _converse(
        call,
        [IDENTITY, "毎月3,000円しか払えません。", "3,000円で決めてください。"],
        "わかりました。条件の範囲で一番少ない金額でお願いします。それで結構です。",
    )

    sms = call.recorder.of_type("sms_preview")
    if outcome is CallOutcome.PROMISE_TO_PAY:
        assert "3,000円" not in cast(SmsPreview, sms[0]).ja
    else:
        assert outcome is CallOutcome.NO_AGREEMENT


async def test_asking_for_a_person_is_handed_over() -> None:
    call = await start_text_call([], live=_live_models())

    outcome = await _converse(call, [IDENTITY], "人間の担当者と話したいです。代わってください。")

    assert outcome is CallOutcome.HUMAN_HANDOFF
    assert call.recorder.of_type("handoff")


async def test_stop_contact_is_recorded() -> None:
    call = await start_text_call([], live=_live_models())

    outcome = await _converse(
        call, [IDENTITY], "もう電話してこないでください。連絡はやめてください。"
    )

    assert outcome is CallOutcome.STOP_CONTACT
    assert "caller-ref" in call.contacts.preferences().stopped_callers
