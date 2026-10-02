from datetime import datetime

from kenji.app.events import CallStarted, FlowNodeEntered
from kenji.app.hub import EventHub
from kenji.domain.calling_hours import JAPAN_STANDARD_TIME

STARTED = CallStarted(
    call_id="call-a",
    transport="phone",
    started_at=datetime(2026, 10, 2, 15, 0, tzinfo=JAPAN_STANDARD_TIME),
)


def test_events_reach_only_the_linked_tab() -> None:
    hub = EventHub()
    tab_a, tab_b = hub.subscribe("tab-a"), hub.subscribe("tab-b")
    hub.link("call-a", "tab-a")

    hub.channel("call-a").publish(STARTED)

    assert tab_a.get_nowait() == STARTED
    assert tab_b.empty()


def test_linking_late_replays_the_call_so_far() -> None:
    hub = EventHub()
    hub.channel("call-a").publish(STARTED)
    tab = hub.subscribe("tab-a")

    assert hub.link("call-a", "tab-a")
    assert tab.get_nowait() == STARTED


def test_a_call_links_to_one_tab_only() -> None:
    hub = EventHub()
    hub.subscribe("tab-a")
    hub.subscribe("tab-b")

    assert hub.link("call-a", "tab-a")
    assert not hub.link("call-a", "tab-b")


def test_unknown_tabs_cannot_be_linked() -> None:
    assert not EventHub().link("call-a", "nobody")


def test_closed_tab_stops_receiving_and_frees_the_call() -> None:
    hub = EventHub()
    hub.subscribe("tab-a")
    hub.link("call-a", "tab-a")
    hub.unsubscribe("tab-a")
    tab_b = hub.subscribe("tab-b")

    assert hub.link("call-a", "tab-b")
    hub.channel("call-a").publish(FlowNodeEntered(node="greeting"))
    assert tab_b.qsize() == 1


def test_forgotten_calls_keep_no_history() -> None:
    hub = EventHub()
    hub.channel("call-a").publish(STARTED)
    hub.forget("call-a")
    tab = hub.subscribe("tab-a")
    hub.link("call-a", "tab-a")

    assert tab.empty()
