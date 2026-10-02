"""The five conversations the brief names, run through the real flows.

Turns the rules are sure of take the fast path; the rest go to a scripted talker standing in for
the language model, after an immediate acknowledgement.
"""

from typing import cast

from kenji.app.events import (
    AuditPublished,
    ComplianceUpdated,
    HandoffRecorded,
    SmsPreview,
    Subtitle,
    TranscriptLine,
)
from kenji.domain.compliance import CheckStatus
from kenji.domain.outcome import CallOutcome
from tests.conversation.harness import Say, TextCall, ToolCall, start_text_call, wait_until

VERIFY = ToolCall("verify_identity", {"name_kana": "サトウユウキ", "date_of_birth": "1990-07-14"})
IDENTITY_ANSWER = "佐藤ゆうきです。平成2年7月14日生まれです。"
ACKNOWLEDGEMENT = "はい、"
DEBT_WORDS = ("債権", "回収", "返済", "支払", "延滞", "滞納", "円", "7731", "35,000", "万")


def _kenji_lines(call: TextCall) -> list[str]:
    lines = cast(list[TranscriptLine], call.recorder.of_type("transcript"))
    return [line.ja for line in lines if line.speaker == "kenji"]


def _last_compliance(call: TextCall) -> ComplianceUpdated:
    return cast(ComplianceUpdated, call.recorder.of_type("compliance")[-1])


async def _verified(call: TextCall) -> None:
    """Name and date of birth in one answer: the fast path verifies without the model."""
    await call.opening_played()
    await call.caller_says(IDENTITY_ANSWER, then_node="state_balance")


async def _verified_by_the_model(call: TextCall) -> None:
    """Name and date of birth in separate answers: the rules are unsure, so the model verifies."""
    await call.opening_played()
    await call.caller_says("佐藤ゆうきです。")
    await call.caller_says("平成2年7月14日です。", then_node="state_balance")


async def test_normal_path_reaches_a_promise_with_every_safeguard_passed() -> None:
    call = await start_text_call([])
    await _verified(call)
    await call.caller_says("毎月6,000円なら払えます。", then_node="negotiate")
    await call.caller_says("それでお願いします。", then_node="read_back")
    await call.caller_says("はい、大丈夫です。")

    assert await call.finish() is CallOutcome.PROMISE_TO_PAY
    assert call.nodes() == [
        "greeting", "verify_identity", "state_balance", "listen", "negotiate", "read_back", "close"
    ]  # fmt: skip
    assert set(vars(_last_compliance(call)).values()) - {"compliance"} == {CheckStatus.PASSED}
    sms = cast(SmsPreview, call.recorder.of_type("sms_preview")[0])
    assert "6,000円" in sms.ja
    assert not sms.is_sent
    audit = cast(AuditPublished, call.recorder.of_type("audit")[-1])
    assert audit.is_chain_valid
    assert call.talker.inferences == []


async def test_spouse_hears_nothing_about_the_debt() -> None:
    call = await start_text_call([ToolCall("third_party_answered")])
    await call.opening_played()
    await call.caller_says("佐藤の妻です。主人はいま出かけています。")

    assert await call.finish() is CallOutcome.CALLBACK_REQUESTED
    assert "third_party" in call.nodes()
    for line in _kenji_lines(call):
        assert not any(word in line for word in DEBT_WORDS), line
    assert not call.recorder.of_type("sms_preview")


async def test_hard_bargainer_offering_3000_is_held_to_the_terms() -> None:
    call = await start_text_call([ToolCall("confirm_plan", {"monthly_yen": 6000})])
    await _verified(call)
    await call.caller_says("3,000円しか払えません。", then_node="negotiate")
    await call.caller_says("3,000円で決めてください。")
    await call.caller_says("わかりました、6,000円にします。", then_node="read_back")
    await call.caller_says("はい。")

    assert await call.finish() is CallOutcome.PROMISE_TO_PAY
    offers = cast(list[ComplianceUpdated], call.recorder.of_type("compliance"))
    assert CheckStatus.BLOCKED in {update.offer_within_terms for update in offers}
    sms = cast(SmsPreview, call.recorder.of_type("sms_preview")[0])
    assert "6,000円" in sms.ja
    assert "3,000円" not in sms.ja


async def test_asking_for_a_human_leaves_a_handoff_record() -> None:
    reason = {"reason": "担当者と話したい", "summary": "Caller asked for a person."}
    call = await start_text_call([ToolCall("request_human", reason)])
    await _verified(call)
    await call.caller_says("人間の担当者と話したいです。")

    assert await call.finish() is CallOutcome.HUMAN_HANDOFF
    handoff = cast(HandoffRecorded, call.recorder.of_type("handoff")[0])
    assert handoff.reason == "担当者と話したい"
    assert handoff.identity_status == "verified"
    assert call.recorder.of_type("sms_preview")


async def test_stop_contact_is_recorded_and_the_call_ends() -> None:
    call = await start_text_call([ToolCall("record_stop_contact")])
    await _verified(call)
    await call.caller_says("もう電話してこないでください。")

    assert await call.finish() is CallOutcome.STOP_CONTACT
    assert "caller-ref" in call.contacts.preferences().stopped_callers
    assert not call.recorder.of_type("sms_preview")


async def test_an_open_turn_is_acknowledged_before_the_model_answers() -> None:
    answer = "ご事情をお聞かせいただけますか。"
    call = await start_text_call([Say(answer)])
    await _verified(call)
    await call.caller_says("今月は少し厳しいです。")
    await wait_until(lambda: answer in call.kenji_lines(), "the model's answer")
    await call.hang_up()

    spoken = [text.strip() for text in call.speech.spoken]
    assert spoken.index(ACKNOWLEDGEMENT) < spoken.index(answer)


async def test_strategist_advice_reaches_the_next_talker_turn_only() -> None:
    call = await start_text_call(
        [
            Say("生年月日もお願いいたします。"),
            VERIFY,
            Say("ご事情をお聞かせいただけますか。"),
            Say("承知いたしました。"),
        ]
    )
    await _verified_by_the_model(call)
    await call.caller_says("今月は少し厳しいです。")
    await call.caller_says("来月なら少し払えます。")
    await call.bot_finishes_speaking()
    await call.hang_up()

    hint = "交渉アドバイザー"
    first_turn, later_turn = call.talker.inferences[0], call.talker.inferences[-1]
    assert not any(hint in str(message.get("content")) for message in first_turn)
    assert hint in str(later_turn[-1].get("content"))
    assert call.recorder.of_type("strategist")


async def test_caller_lines_get_english_subtitles() -> None:
    call = await start_text_call([Say("ありがとうございます。")])
    await _verified(call)
    await call.caller_says("よろしくお願いします。")
    await call.bot_finishes_speaking()
    await call.hang_up()

    subtitles = cast(list[Subtitle], call.recorder.of_type("subtitle"))
    assert any(subtitle.en == "[en] よろしくお願いします。" for subtitle in subtitles)
    assert any(subtitle.en.startswith("Thank you for calling.") for subtitle in subtitles)
