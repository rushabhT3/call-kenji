"""Routes each call's events to the one browser tab linked to it, and to nobody else."""

import asyncio
from collections import defaultdict

from kenji.app.events import CallEvent


class _CallChannel:
    def __init__(self, hub: "EventHub", call_id: str) -> None:
        self._hub = hub
        self._call_id = call_id

    def publish(self, event: CallEvent) -> None:
        self._hub.publish(self._call_id, event)


class EventHub:
    def __init__(self) -> None:
        self._history: dict[str, list[CallEvent]] = defaultdict(list)
        self._viewer_of_call: dict[str, str] = {}
        self._queues: dict[str, asyncio.Queue[CallEvent]] = {}

    def channel(self, call_id: str) -> _CallChannel:
        return _CallChannel(self, call_id)

    def publish(self, call_id: str, event: CallEvent) -> None:
        self._history[call_id].append(event)
        viewer_id = self._viewer_of_call.get(call_id)
        queue = None if viewer_id is None else self._queues.get(viewer_id)
        if queue is not None:
            queue.put_nowait(event)

    def subscribe(self, viewer_id: str) -> asyncio.Queue[CallEvent]:
        queue: asyncio.Queue[CallEvent] = asyncio.Queue()
        self._queues[viewer_id] = queue
        return queue

    def unsubscribe(self, viewer_id: str) -> None:
        self._queues.pop(viewer_id, None)
        self._viewer_of_call = {
            call: viewer for call, viewer in self._viewer_of_call.items() if viewer != viewer_id
        }

    def link(self, call_id: str, viewer_id: str) -> bool:
        queue = self._queues.get(viewer_id)
        if queue is None or call_id in self._viewer_of_call:
            return False
        self._viewer_of_call[call_id] = viewer_id
        for event in self._history[call_id]:
            queue.put_nowait(event)
        return True

    def forget(self, call_id: str) -> None:
        self._history.pop(call_id, None)
        self._viewer_of_call.pop(call_id, None)
