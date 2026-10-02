from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from kenji.app.events import FlowNodeEntered
from kenji.config import Settings
from kenji.container import Services
from kenji.server import create_app


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


def test_dev_client_is_off_by_default(client: TestClient) -> None:
    with client:
        assert client.post("/start").status_code == 404
