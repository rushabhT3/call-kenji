"""HTTP and WebSocket entry points. Run with `uv run kenji-server`."""

import asyncio
import hmac
import secrets
import sys
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from loguru import logger
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import IceServer as PipecatIceServer
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.request_handler import (
    IceCandidate,
    SmallWebRTCPatchRequest,
    SmallWebRTCRequest,
    SmallWebRTCRequestHandler,
)
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.utils.tracing.setup import setup_tracing
from pipecat_ai_prebuilt.frontend import PipecatPrebuiltUI
from pydantic import TypeAdapter, ValidationError

from kenji.adapters.clock import SystemClock
from kenji.adapters.storage import purge_expired_calls
from kenji.app.events import CallEvent
from kenji.app.launcher import CallRequest
from kenji.app.linking import CODE_REFRESH
from kenji.app.ports import IceServer
from kenji.app.privacy import caller_ref
from kenji.config import Settings
from kenji.container import Services, build_services
from kenji.domain.guardrails import usage_day
from kenji.phone_routes import add_phone_routes
from kenji.softphone_routes import add_softphone_routes

PURGE_INTERVAL_SECS = 6 * 60 * 60
CODE_REFRESH_SECS = CODE_REFRESH.total_seconds()
_EVENT = TypeAdapter[CallEvent](CallEvent)


class _Background:
    """Keeps strong references to running calls so they are not garbage-collected."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[Any]] = set()

    def start(self, work: Coroutine[Any, Any, Any]) -> None:
        task = asyncio.create_task(work)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)


def configure_logging(level: str) -> None:
    logger.remove()
    logger.add(sys.stdout, level=level, serialize=True)


async def _purge_forever(settings: Settings) -> None:
    clock = SystemClock()
    while True:
        removed = await asyncio.to_thread(
            purge_expired_calls, settings.data_dir, usage_day(clock.now()), settings.retention_days
        )
        if removed:
            logger.info("deleted expired call records", days=[path.name for path in removed])
        await asyncio.sleep(PURGE_INTERVAL_SECS)


def create_app(settings: Settings, services: Services | None = None) -> FastAPI:
    services = services or build_services(settings)
    webrtc = SmallWebRTCRequestHandler(ice_servers=[PipecatIceServer(urls=settings.stun_url)])
    background = _Background()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        background.start(_purge_forever(settings))
        yield
        await webrtc.close()  # type: ignore[no-untyped-call]

    app = FastAPI(lifespan=lifespan, title="Call Kenji")
    _add_browser_call_routes(app, services, webrtc, background)
    _add_viewer_route(app, services)
    if services.phone is not None:
        add_phone_routes(app, services, services.phone)
    if services.softphone is not None:
        add_softphone_routes(app, services.softphone, settings.port)
    if settings.enable_dev_client:
        _add_dev_client(app, services, webrtc, background)
    return app


def _first(urls: list[str], prefixes: tuple[str, ...]) -> str | None:
    return next((url for url in urls if url.startswith(prefixes)), None)


def bot_ice_servers(servers: list[IceServer]) -> list[PipecatIceServer]:
    """aiortc reads one STUN and one TURN URL, so pick the best of each (UDP relay first)."""
    urls = [url for server in servers for url in server.urls]
    stun = _first(urls, ("stun:",))
    udp_turn = next((url for url in urls if url.startswith("turn:") and "udp" in url), None)
    turn = udp_turn or _first(urls, ("turns:", "turn:"))
    credentials = next((server for server in servers if server.username), None)
    picked = [PipecatIceServer(urls=stun)] if stun else []
    if turn and credentials:
        picked.append(
            PipecatIceServer(
                urls=turn, username=credentials.username, credential=credentials.credential
            )
        )
    return picked


def client_address(http: Request, proxy_secret: str | None) -> str:
    """The visitor's address; a forwarded one counts only from our own proxy."""
    claimed = http.headers.get("X-Kenji-Proxy", "")
    if proxy_secret and hmac.compare_digest(claimed.encode(), proxy_secret.encode()):
        return http.headers.get("X-Client-Address", "unknown")
    return http.client.host if http.client else "unknown"


def _browser_request(services: Services, http: Request, viewer_id: str | None) -> CallRequest:
    address = client_address(http, services.proxy_secret)
    return CallRequest(
        transport="browser", caller_ref=caller_ref(address, services.salt), viewer_id=viewer_id
    )


async def _answer_offer(
    webrtc: SmallWebRTCRequestHandler,
    offer: dict[str, Any],
    start_call: Callable[[SmallWebRTCConnection], None],
) -> dict[str, str] | None:
    async def on_connection(connection: SmallWebRTCConnection) -> None:
        start_call(connection)

    return await webrtc.handle_web_request(
        request=SmallWebRTCRequest.from_dict(offer), webrtc_connection_callback=on_connection
    )


async def _add_candidates(
    webrtc: SmallWebRTCRequestHandler, body: dict[str, Any]
) -> dict[str, str]:
    candidates = [IceCandidate(**candidate) for candidate in body.get("candidates", [])]
    await webrtc.handle_patch_request(
        SmallWebRTCPatchRequest(pc_id=body["pc_id"], candidates=candidates)
    )
    return {"status": "success"}


def _call_starter(
    services: Services, background: _Background, request: CallRequest
) -> Callable[[SmallWebRTCConnection], None]:
    def start(connection: SmallWebRTCConnection) -> None:
        transport = SmallWebRTCTransport(
            webrtc_connection=connection,
            params=TransportParams(audio_in_enabled=True, audio_out_enabled=True),
        )
        background.start(services.launcher.run(transport, request))

    return start


def _add_browser_call_routes(
    app: FastAPI, services: Services, webrtc: SmallWebRTCRequestHandler, background: _Background
) -> None:
    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/ice")
    async def ice() -> dict[str, list[dict[str, Any]]]:
        servers = await services.ice.ice_servers()
        webrtc.update_ice_servers(bot_ice_servers(servers))
        return {"iceServers": [server.to_browser() for server in servers]}

    @app.post("/api/offer")
    async def offer(http: Request) -> dict[str, str] | None:
        body: dict[str, Any] = await http.json()
        request_data = body.get("requestData") or body.get("request_data") or {}
        viewer_id = request_data.get("viewer_id") if isinstance(request_data, dict) else None
        request = _browser_request(services, http, viewer_id)
        return await _answer_offer(webrtc, body, _call_starter(services, background, request))

    @app.patch("/api/offer")
    async def ice_candidates(http: Request) -> dict[str, str]:
        return await _add_candidates(webrtc, await http.json())


class _ViewerFeed:
    """One browser tab's private feed: a link code that never goes stale, and its call's events."""

    def __init__(self, websocket: WebSocket, services: Services) -> None:
        self._websocket = websocket
        self._services = services
        self._viewer_id = secrets.token_urlsafe(16)

    async def run(self) -> None:
        hub = self._services.hub
        queue = hub.subscribe(self._viewer_id)
        await self._send_code()
        work = (self._forward_events(queue), self._refresh_code(), self._wait_for_close())
        tasks = [asyncio.create_task(job) for job in work]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except WebSocketDisconnect:
            pass
        finally:
            for task in tasks:
                task.cancel()
            hub.unsubscribe(self._viewer_id)

    async def _send_code(self) -> None:
        code = self._services.links.issue(self._viewer_id)
        await self._websocket.send_json(
            {"type": "viewer_ready", "viewer_id": self._viewer_id, "code": code}
        )

    async def _refresh_code(self) -> None:
        while True:
            await asyncio.sleep(CODE_REFRESH_SECS)
            await self._send_code()

    async def _forward_events(self, queue: asyncio.Queue[CallEvent]) -> None:
        while True:
            event = await queue.get()
            await self._websocket.send_text(_EVENT.dump_json(event).decode("utf-8"))

    async def _wait_for_close(self) -> None:
        while True:
            await self._websocket.receive_text()


def _add_viewer_route(app: FastAPI, services: Services) -> None:
    @app.websocket("/ws/viewer")
    async def viewer(websocket: WebSocket) -> None:
        await websocket.accept()
        await _ViewerFeed(websocket, services).run()


def _add_dev_client(
    app: FastAPI, services: Services, webrtc: SmallWebRTCRequestHandler, background: _Background
) -> None:
    app.mount("/client", PipecatPrebuiltUI)
    sessions: set[str] = set()

    @app.post("/start")
    async def start() -> dict[str, str]:
        session_id = secrets.token_urlsafe(16)
        sessions.add(session_id)
        return {"sessionId": session_id}

    @app.post("/sessions/{session_id}/api/offer")
    async def session_offer(session_id: str, http: Request) -> dict[str, str] | None:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="unknown session")
        request = _browser_request(services, http, viewer_id=None)
        body: dict[str, Any] = await http.json()
        return await _answer_offer(webrtc, body, _call_starter(services, background, request))

    @app.patch("/sessions/{session_id}/api/offer")
    async def session_ice(session_id: str, http: Request) -> dict[str, str]:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="unknown session")
        return await _add_candidates(webrtc, await http.json())


def configure_tracing(endpoint: str | None) -> bool:
    if endpoint is None:
        return False
    return setup_tracing("call-kenji", exporter=OTLPSpanExporter(endpoint=endpoint))


def load_settings() -> Settings:
    """Load settings, reporting problems by field name only so no secret reaches the logs."""
    try:
        return Settings()
    except ValidationError as error:
        problems = [
            f"{'.'.join(str(part) for part in detail['loc']).upper()}: {detail['msg']}"
            for detail in error.errors(include_input=False, include_url=False)
        ]
        raise SystemExit("Invalid configuration: " + "; ".join(problems)) from None


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    configure_tracing(settings.otel_exporter_otlp_endpoint)
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, log_config=None)
