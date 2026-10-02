"""A real phone call shows only in the tab whose code the caller keyed in."""

from pipecat.audio.dtmf.types import KeypadEntry
from pipecat.frames.frames import Frame, InputDTMFFrame
from pipecat.tests.utils import run_test

from kenji.app.dtmf import DtmfLinker
from kenji.app.events import FlowNodeEntered
from kenji.app.hub import EventHub
from kenji.app.linking import LinkRegistry
from tests.conversation.harness import FixedClock


def _keys(digits: str) -> list[Frame]:
    return [InputDTMFFrame(button=KeypadEntry(digit)) for digit in digits]


async def test_typed_code_links_the_call_to_that_tab_only() -> None:
    hub, links = EventHub(), LinkRegistry(FixedClock())
    tab_a, tab_b = hub.subscribe("tab-a"), hub.subscribe("tab-b")
    code_a = links.issue("tab-a")
    links.issue("tab-b")
    linker = DtmfLinker("call-1", links.redeem, hub.link)

    await run_test(linker, frames_to_send=_keys(code_a))
    hub.channel("call-1").publish(FlowNodeEntered(node="greeting"))

    assert tab_a.get_nowait() == FlowNodeEntered(node="greeting")
    assert tab_b.empty()


async def test_wrong_code_links_nobody() -> None:
    hub, links = EventHub(), LinkRegistry(FixedClock(), code_source=lambda: "1234")
    tab = hub.subscribe("tab-a")
    links.issue("tab-a")
    linker = DtmfLinker("call-1", links.redeem, hub.link)

    await run_test(linker, frames_to_send=_keys("9999"))
    hub.channel("call-1").publish(FlowNodeEntered(node="greeting"))

    assert tab.empty()


async def test_star_or_hash_starts_the_code_again() -> None:
    hub, links = EventHub(), LinkRegistry(FixedClock(), code_source=lambda: "1234")
    tab = hub.subscribe("tab-a")
    links.issue("tab-a")
    linker = DtmfLinker("call-1", links.redeem, hub.link)

    await run_test(linker, frames_to_send=_keys("12#1234"))
    hub.channel("call-1").publish(FlowNodeEntered(node="greeting"))

    assert tab.qsize() == 1


async def test_keypad_frames_still_flow_downstream() -> None:
    linker = DtmfLinker("call-1", lambda _call, _code: None, lambda _call, _viewer: False)

    downstream, _ = await run_test(linker, frames_to_send=_keys("5"))

    assert any(isinstance(frame, InputDTMFFrame) for frame in downstream)
