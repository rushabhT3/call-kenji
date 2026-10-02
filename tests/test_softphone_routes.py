"""The softphone mints Twilio credentials, so only a browser on this machine is answered."""

from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from kenji.adapters.twilio import SoftphoneCredentials, SoftphoneTokens
from kenji.config import Settings
from kenji.container import Services
from kenji.server import create_app

LOCAL_BASE_URL = "http://127.0.0.1:7860"
LOOPBACK_CLIENT = ("127.0.0.1", 50000)
CREDENTIALS = SoftphoneCredentials(
    account_sid="AC123",
    api_key_sid="SK123",
    api_key_secret="softphone-key-secret-of-thirty-two-bytes",
    twiml_app_sid="AP123",
)


def _client(
    services: Services,
    tmp_path: Path,
    *,
    base_url: str = LOCAL_BASE_URL,
    client: tuple[str, int] = LOOPBACK_CLIENT,
) -> TestClient:
    settings = Settings(
        _env_file=None,
        llm_api_key=SecretStr("test"),
        soniox_api_key=SecretStr("test"),
        cartesia_api_key=SecretStr("test"),
        data_dir=tmp_path,
    )
    return TestClient(create_app(settings, services), base_url=base_url, client=client)


@pytest.fixture
def softphone_services(services: Services) -> Services:
    return replace(services, softphone=SoftphoneTokens(CREDENTIALS))


def test_a_browser_on_this_machine_gets_the_page_and_a_token(
    softphone_services: Services, tmp_path: Path
) -> None:
    with _client(softphone_services, tmp_path) as client:
        page = client.get("/dev/softphone")
        token = client.post("/dev/softphone/token")

    assert page.status_code == 200
    assert "Twilio.Device" in page.text
    assert token.status_code == 200
    assert token.json()["token"].count(".") == 2


@pytest.mark.parametrize(
    "header", ["CF-Connecting-IP", "X-Forwarded-For", "Forwarded", "X-Kenji-Proxy"]
)
def test_a_request_through_a_tunnel_or_proxy_is_not_answered(
    softphone_services: Services, tmp_path: Path, header: str
) -> None:
    with _client(softphone_services, tmp_path) as client:
        response = client.post("/dev/softphone/token", headers={header: "203.0.113.7"})

    assert response.status_code == 404


def test_a_page_that_names_another_host_is_not_answered(
    softphone_services: Services, tmp_path: Path
) -> None:
    with _client(softphone_services, tmp_path, base_url="http://attacker.example") as client:
        response = client.post("/dev/softphone/token")

    assert response.status_code == 404


def test_another_machine_is_not_answered(softphone_services: Services, tmp_path: Path) -> None:
    with _client(softphone_services, tmp_path, client=("192.168.1.20", 50000)) as client:
        response = client.get("/dev/softphone")

    assert response.status_code == 404


def test_without_softphone_settings_there_is_no_softphone(
    services: Services, tmp_path: Path
) -> None:
    with _client(services, tmp_path) as client:
        response = client.post("/dev/softphone/token")

    assert response.status_code == 404
