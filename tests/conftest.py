"""Fixtures shared by the server and phone-route tests."""

from datetime import date

import pytest

from kenji.app.hub import EventHub
from kenji.app.launcher import CallAccounting, CallLauncher, CallRouting
from kenji.app.linking import LinkRegistry
from kenji.app.ports import CallRecorder
from kenji.container import Services
from kenji.domain.guardrails import CallLimits
from tests.app.test_launcher import MemoryUsage
from tests.conversation.harness import MemoryRecorder, build_text_kit


@pytest.fixture
def services() -> Services:
    text = build_text_kit([])
    limits = CallLimits()

    def recorder(_call_id: str, _day: date) -> CallRecorder:
        return MemoryRecorder()

    routing = CallRouting(hub=EventHub(), links=LinkRegistry(text.kit.clock))
    accounting = CallAccounting(MemoryUsage(), recorder, {"phone": limits, "browser": limits})
    return Services(
        launcher=CallLauncher(text.kit, routing, accounting),
        hub=routing.hub,
        links=routing.links,
        salt=b"salt",
    )
