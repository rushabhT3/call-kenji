from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import SecretStr

from kenji import server
from kenji.app.events import FlowNodeEntered
from kenji.app.launcher import CallRequest
from kenji.config import Settings
from kenji.container import Services
from kenji.server import client_address, create_app


@pytest.fixture
def client(services: Services, tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        enable_dev_client=False,
        llm_api_key=SecretStr("test"),
        soniox_api_key=SecretStr("test"),
        cartesia_api_key=SecretStr("test"),
        data_dir=tmp_path,
    )
    return TestClient(create_app(settings, services))


def test_health(client: TestClient) -> None:
    with client:
        assert client.get("/api/health").json() == {"status": "ok"}


def test_viewer_gets_a_private_code_and_only_its_linked_call(
    client: TestClient, services: Services
) -> None:
    with client, client.websocket_connect("/ws/viewer") as viewer:
        ready = viewer.receive_json()
        assert ready["type"] == "viewer_ready"
        assert len(ready["code"]) == 4

        linked_viewer = services.links.redeem("call-1", ready["code"])
        assert linked_viewer == ready["viewer_id"]
        services.hub.link("call-1", ready["viewer_id"])
        services.hub.channel("call-2").publish(FlowNodeEntered(node="someone-else"))
        services.hub.channel("call-1").publish(FlowNodeEntered(node="greeting"))

        assert viewer.receive_json() == {"type": "flow_node", "node": "greeting"}


def test_viewer_code_is_renewed_before_it_expires(
    client: TestClient, services: Services, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "CODE_REFRESH_SECS", 0.05)

    with client, client.websocket_connect("/ws/viewer") as viewer:
        first, renewed = viewer.receive_json(), viewer.receive_json()

    assert renewed["type"] == "viewer_ready"
    assert renewed["viewer_id"] == first["viewer_id"]
    assert services.links.redeem("call-1", renewed["code"]) == first["viewer_id"]


def test_dev_client_is_off_by_default(client: TestClient) -> None:
    with client:
        assert client.post("/start").status_code == 404


def test_ice_servers_for_a_browser_call(client: TestClient) -> None:
    with client:
        reply = client.get("/api/ice").json()

    assert reply == {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}


def _request(headers: dict[str, str]) -> Request:
    raw = [(key.lower().encode(), value.encode()) for key, value in headers.items()]
    return Request({"type": "http", "headers": raw, "client": ("10.0.0.1", 1234)})


def test_forwarded_address_is_trusted_only_with_the_proxy_secret() -> None:
    forwarded = {"X-Client-Address": "203.0.113.9"}
    from_proxy = _request({**forwarded, "X-Kenji-Proxy": "s3cret"})
    spoofed = _request({**forwarded, "X-Kenji-Proxy": "guess"})

    assert client_address(from_proxy, "s3cret") == "203.0.113.9"
    assert client_address(spoofed, "s3cret") == "10.0.0.1"
    assert client_address(_request(forwarded), None) == "10.0.0.1"


@pytest.mark.parametrize(
    ("extra", "persona_id"),
    [
        ({"requestData": {"viewer_id": "tab", "persona_id": "tanaka"}}, "tanaka"),
        ({"request_data": {"persona_id": "nobody"}}, "nobody"),
        ({"requestData": {"viewer_id": "tab", "persona_id": ""}}, None),
        ({}, None),
    ],
)
def test_the_offer_passes_the_chosen_persona_to_the_call(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    extra: dict[str, Any],
    persona_id: str | None,
) -> None:
    requests: list[CallRequest] = []

    def starter(
        _services: Services, _background: object, request: CallRequest
    ) -> Callable[..., None]:
        requests.append(request)
        return lambda _connection: None

    async def answer(_webrtc: object, _offer: object, _start: object) -> dict[str, str]:
        return {"sdp": "answer", "type": "answer"}

    monkeypatch.setattr(server, "_call_starter", starter)
    monkeypatch.setattr(server, "_answer_offer", answer)
    with client:
        reply = client.post("/api/offer", json={"sdp": "offer", "type": "offer"} | extra)

    assert reply.json() == {"sdp": "answer", "type": "answer"}
    assert [request.persona_id for request in requests] == [persona_id]
