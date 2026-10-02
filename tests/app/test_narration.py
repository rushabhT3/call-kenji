"""Words that only announce a scripted step are left unsaid; every other answer is spoken."""

from pathlib import Path

from pipecat.frames.frames import (
    Frame,
    FunctionCallFromLLM,
    FunctionCallsStartedFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.tests.utils import run_test

from kenji.adapters.content import load_script
from kenji.app.narration import SCRIPTED_HANDOVERS, HandoverNarrationFilter


def _calls(name: str) -> FunctionCallsStartedFrame:
    call = FunctionCallFromLLM(
        function_name=name, tool_call_id="call-1", arguments={}, context=LLMContext()
    )
    return FunctionCallsStartedFrame(function_calls=[call])


async def _spoken(*frames: Frame) -> list[str]:
    downstream, _ = await run_test(
        HandoverNarrationFilter(),
        frames_to_send=[LLMFullResponseStartFrame(), *frames, LLMFullResponseEndFrame()],
    )
    return [frame.text for frame in downstream if isinstance(frame, LLMTextFrame)]


async def test_words_before_a_scripted_step_are_left_unsaid() -> None:
    spoken = await _spoken(LLMTextFrame("担当者におつなぎします。"), _calls("request_human"))

    assert spoken == []


async def test_words_while_terms_are_checked_are_spoken() -> None:
    spoken = await _spoken(LLMTextFrame("確認いたします。"), _calls("check_terms"))

    assert spoken == ["確認いたします。"]


async def test_an_answer_with_no_tool_is_spoken_in_full_and_in_order() -> None:
    spoken = await _spoken(LLMTextFrame("ご事情、"), LLMTextFrame("お察しいたします。"))

    assert spoken == ["ご事情、", "お察しいたします。"]


def test_every_handover_is_a_tool_kenji_has() -> None:
    script = load_script(Path("content/script_ja.yaml"))

    assert all(hasattr(script.tools, name) for name in SCRIPTED_HANDOVERS)
