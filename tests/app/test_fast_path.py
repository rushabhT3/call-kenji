"""The fast path answers only what the rules are sure of, through the same tools the model uses."""

from typing import cast

import pytest
from pipecat.flows import NodeConfig
from pipecat.frames.frames import Frame, LLMContextFrame, LLMTextFrame, TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.tests.utils import SleepFrame, run_test

from kenji.app.call_parts import CallIO, CallParts, build_call_parts
from kenji.app.events import ComplianceUpdated
from kenji.app.fast_path import Acknowledgement, FastPath, last_caller_text
from kenji.app.tools import NodeName
from kenji.app.turns import AnswerWatch, Floor
from kenji.domain.compliance import CheckStatus
from kenji.domain.identity import IdentityStatus
from tests.conversation.harness import MemoryRecorder, build_text_kit, text_call_context

IDENTITY = "佐藤ゆうきです。生年月日は、平成2年7月14日です。"


def _call_parts() -> tuple[CallParts, MemoryRecorder]:
    kit = build_text_kit([]).kit
    recorder = MemoryRecorder()
    parts = build_call_parts(kit, text_call_context(kit), CallIO(sink=recorder, audit=recorder))
    parts.flow.initial_node()
    return parts, recorder


def _verified() -> tuple[CallParts, MemoryRecorder]:
    parts, recorder = _call_parts()
    assert parts.planner.answer(IDENTITY) is not None
    parts.flow.enter(NodeName.LISTEN)
    return parts, recorder


def _node_name(node: NodeConfig | None) -> str | None:
    return None if node is None else str(node.get("name"))


def test_matching_name_and_birth_date_verify_identity_without_the_model() -> None:
    parts, recorder = _call_parts()

    reply = parts.planner.answer(IDENTITY)

    assert reply is not None
    assert _node_name(reply.node) == NodeName.STATE_BALANCE
    assert parts.session.identity_status is IdentityStatus.VERIFIED
    assert "identity_checked" in [record.entry.kind for record in recorder.records()]


def test_a_wrong_birth_date_is_left_to_the_model_and_costs_no_attempt() -> None:
    parts, recorder = _call_parts()

    reply = parts.planner.answer("佐藤ゆうきです。生年月日は1985年3月3日です。")

    assert reply is None
    assert "identity_checked" not in [record.entry.kind for record in recorder.records()]


def test_a_name_without_a_birth_date_is_left_to_the_model() -> None:
    parts, _ = _call_parts()

    assert parts.planner.answer("佐藤ゆうきです。") is None


def test_an_offer_below_the_terms_gets_the_smallest_acceptable_counter_offer() -> None:
    parts, recorder = _verified()

    reply = parts.planner.answer("毎月3,000円なら払えます。")

    assert reply is not None
    assert reply.line is not None
    assert "3,000円" in reply.line.ja
    assert "6,000円" in reply.line.ja
    assert _node_name(reply.node) == NodeName.NEGOTIATE
    compliance = cast(ComplianceUpdated, recorder.of_type("compliance")[-1])
    assert compliance.offer_within_terms is CheckStatus.BLOCKED


def test_yes_to_the_counter_offer_confirms_that_plan_and_reads_it_back() -> None:
    parts, _ = _verified()
    parts.planner.answer("毎月3,000円なら払えます。")

    reply = parts.planner.answer("はい、お願いします。")

    assert reply is not None
    assert _node_name(reply.node) == NodeName.READ_BACK
    plan = parts.session.confirmed_plan
    assert plan is not None
    assert plan.proposal.monthly_yen == 6_000


def test_an_acceptable_offer_is_confirmed_only_after_a_plain_yes() -> None:
    parts, _ = _verified()

    offer = parts.planner.answer("毎月7,000円でお願いします。")
    yes = parts.planner.answer("はい。")

    assert offer is not None
    assert offer.line is not None
    assert "7,000円" in offer.line.ja
    assert yes is not None
    plan = parts.session.confirmed_plan
    assert plan is not None
    assert plan.proposal.monthly_yen == 7_000


def test_a_turn_the_model_answers_cancels_the_pending_offer() -> None:
    parts, _ = _verified()
    parts.planner.answer("毎月6,000円なら払えます。")

    assert parts.planner.answer("来月から少し収入が増えるかもしれません。") is None
    assert parts.planner.answer("はい。") is None
    assert parts.session.confirmed_plan is None


def test_a_plain_yes_to_the_read_back_records_the_promise() -> None:
    parts, _ = _verified()
    parts.planner.answer("毎月6,000円なら払えます。")
    parts.planner.answer("はい。")

    reply = parts.planner.answer("はい、間違いありません。")

    assert reply is not None
    assert _node_name(reply.node) == NodeName.CLOSE
    assert parts.session.promise is not None


def test_a_correction_to_the_read_back_goes_to_the_model() -> None:
    parts, _ = _verified()
    parts.planner.answer("毎月6,000円なら払えます。")
    parts.planner.answer("はい。")

    assert parts.planner.answer("いいえ、初回の日付を変えたいです。") is None
    assert parts.session.promise is None


def test_a_first_payment_too_late_or_a_lump_sum_goes_to_the_model() -> None:
    parts, _ = _verified()

    assert parts.planner.answer("毎月6,000円で、初回は12月25日にしてください。") is None
    assert parts.planner.answer("35,000円を一度に払います。") is None


def test_the_last_caller_message_is_found_after_task_instructions() -> None:
    messages: list[object] = [
        {"role": "user", "content": "最初"},
        {"role": "assistant", "content": "はい"},
        {"role": "user", "content": "最後"},
        {"role": "developer", "content": "task"},
    ]

    assert last_caller_text(messages) == "最後"
    assert last_caller_text([]) == ""


async def _through_fast_path(
    caller_text: str,
) -> tuple[list[object], list[NodeConfig], Floor]:
    parts, _ = _verified()
    moved: list[NodeConfig] = []

    async def set_node(node: NodeConfig) -> None:
        moved.append(node)

    context = LLMContext(messages=[{"role": "user", "content": caller_text}])
    floor = Floor()
    acknowledgement = Acknowledgement("はい、", floor, on_spoken=lambda _text: None)
    processor = FastPath(parts.planner, acknowledgement, set_node=set_node)
    downstream, _ = await run_test(processor, frames_to_send=[LLMContextFrame(context=context)])
    return list(downstream), moved, floor


async def test_an_open_question_is_acknowledged_at_once_and_passed_to_the_model() -> None:
    frames, moved, floor = await _through_fast_path("今月はちょっと厳しいんです。")

    assert isinstance(frames[0], TTSSpeakFrame)
    assert frames[0].text == "はい、"
    assert not frames[0].append_to_context
    assert isinstance(frames[1], LLMContextFrame)
    assert moved == []
    assert floor.is_held


async def test_a_turn_the_rules_answer_never_reaches_the_model() -> None:
    frames, moved, floor = await _through_fast_path("毎月3,000円なら払えます。")

    assert not any(isinstance(frame, LLMContextFrame) for frame in frames)
    spoken = [frame.text for frame in frames if isinstance(frame, TTSSpeakFrame)]
    assert len(spoken) == 1
    assert "6,000円" in spoken[0]
    assert [_node_name(node) for node in moved] == [NodeName.NEGOTIATE]
    assert not floor.is_held


def test_an_offer_with_timing_the_rules_cannot_read_goes_to_the_model() -> None:
    parts, _ = _verified()

    assert parts.planner.answer("はい、毎月6,000円、初回は来週でお願いします。") is None


def test_restating_the_proposed_plan_goes_to_the_model_instead_of_asking_again() -> None:
    parts, _ = _verified()
    parts.planner.answer("毎月3,000円なら払えます。")

    assert parts.planner.answer("わかりました、6,000円にします。") is None


@pytest.mark.parametrize(
    "speech",
    [
        IDENTITY + "もう電話してこないでください。",
        IDENTITY + "担当者の方と話したいです。",
    ],
)
def test_a_second_request_beside_the_identity_goes_to_the_model(speech: str) -> None:
    parts, recorder = _call_parts()

    assert parts.planner.answer(speech) is None
    assert "identity_checked" not in [record.entry.kind for record in recorder.records()]


@pytest.mark.parametrize(
    "speech",
    [
        "毎月6,000円なら払えますが、人間の担当者と話したいです。",
        "6,000円なら払えます。でも、もう連絡しないでください。",
        "毎月6,000円なら払えます。弁護士に相談しています。",
    ],
)
def test_a_second_request_beside_an_offer_goes_to_the_model(speech: str) -> None:
    parts, _ = _verified()

    assert parts.planner.answer(speech) is None
    assert parts.session.confirmed_plan is None


def _tool_names(node: NodeConfig | None) -> set[str]:
    assert node is not None
    return {str(getattr(function, "name", "")) for function in node.get("functions", [])}


def test_steps_that_change_on_the_callers_reply_keep_the_same_tools() -> None:
    parts, _ = _call_parts()
    greeting = parts.flow.initial_node()
    verify = parts.flow.enter(NodeName.VERIFY_IDENTITY)
    balance = parts.planner.answer(IDENTITY)
    assert balance is not None

    listen = parts.flow.enter(NodeName.LISTEN)

    assert _tool_names(greeting) == _tool_names(verify)
    assert _tool_names(balance.node) == _tool_names(listen)


GUARD_SECS = 0.15


async def _model_stays_silent(
    model_frames: list[Frame],
) -> tuple[list[object], Floor]:
    parts, _ = _verified()
    floor = Floor()
    spoken: list[str] = []
    acknowledgement = Acknowledgement(
        "はい、",
        floor,
        on_spoken=spoken.append,
        holding="少々お待ちください。",
        apology="申し訳ございません。もう一度お聞かせいただけますか。",
        deadline_secs=GUARD_SECS,
    )

    async def set_node(_node: NodeConfig) -> None:
        return None

    context = LLMContext(messages=[{"role": "user", "content": "今月はちょっと厳しいんです。"}])
    pipeline = Pipeline([FastPath(parts.planner, acknowledgement, set_node), AnswerWatch(floor)])
    downstream, _ = await run_test(
        pipeline,
        frames_to_send=[
            LLMContextFrame(context=context),
            *model_frames,
            SleepFrame(sleep=GUARD_SECS * 3),
        ],
    )
    return list(downstream), floor


def _spoken_texts(frames: list[object]) -> list[str]:
    return [frame.text for frame in frames if isinstance(frame, TTSSpeakFrame)]


async def test_a_silent_model_gets_a_holding_line_a_retry_then_an_apology() -> None:
    frames, floor = await _model_stays_silent([])

    assert _spoken_texts(frames) == [
        "はい、",
        "少々お待ちください。",
        "申し訳ございません。もう一度お聞かせいただけますか。",
    ]
    assert sum(isinstance(frame, LLMContextFrame) for frame in frames) == 2
    assert not floor.is_held


async def test_a_model_that_answers_in_time_is_left_alone() -> None:
    frames, _ = await _model_stays_silent(
        [SleepFrame(sleep=0.02), LLMTextFrame("ご事情お察しします。")]
    )

    assert _spoken_texts(frames) == ["はい、"]
    assert sum(isinstance(frame, LLMContextFrame) for frame in frames) == 1
