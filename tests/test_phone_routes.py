"""The public phone endpoints only answer Twilio, and only for the call it announced."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.websockets import WebSocketDisconnect
from twilio.request_validator import RequestValidator

from kenji.adapters.twilio import TwilioWebhooks
from kenji.app.stream_tokens import StreamTokens
from kenji.config import Settings
from kenji.container import PhoneLine, Services
from kenji.server import create_app
from tests.conversation.harness import FixedClock

AUTH_TOKEN = "twilio-test-token"
BASE_URL = "https://kenji.example"
FORM = {"CallSid": "CA123", "From": "+15551230000", "To": "+15550001111"}


@pytest.fixture
def phone_services(services: Services) -> Services:
    phone = PhoneLine(
        webhooks=TwilioWebhooks(AUTH_TOKEN),
        tokens=StreamTokens(FixedClock()),
        credentials=("AC123", AUTH_TOKEN),
        public_base_url=BASE_URL,
    )
    return Services(
        launcher=services.launcher,
        hub=services.hub,
        links=services.links,
        salt=services.salt,
        ice=services.ice,
        phone=phone,
    )


@pytest.fixture
def client(phone_services: Services, tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        llm_api_key=SecretStr("test"),
        soniox_api_key=SecretStr("test"),
        cartesia_api_key=SecretStr("test"),
        data_dir=tmp_path,
    )
    return TestClient(create_app(settings, phone_services))


def _signature(form: dict[str, str]) -> str:
    return str(RequestValidator(AUTH_TOKEN).compute_signature(BASE_URL + "/twilio/voice", form))


def test_unsigned_webhook_is_refused(client: TestClient) -> None:
    with client:
        response = client.post("/twilio/voice", data=FORM)

    assert response.status_code == 403


def test_signed_webhook_streams_with_a_one_time_token(client: TestClient) -> None:
    with client:
        response = client.post(
            "/twilio/voice", data=FORM, headers={"X-Twilio-Signature": _signature(FORM)}
        )

    assert response.status_code == 200
    assert '<Stream url="wss://kenji.example/twilio/ws">' in response.text
    assert '<Parameter name="token" value="' in response.text
    assert FORM["From"] not in response.text


def test_media_stream_without_a_valid_token_is_closed(client: TestClient) -> None:
    start = {
        "event": "start",
        "start": {
            "streamSid": "MZ1",
            "callSid": "CA123",
            "customParameters": {"token": "forged"},
        },
    }
    with client, client.websocket_connect("/twilio/ws") as stream:
        stream.send_text(json.dumps({"event": "connected", "protocol": "Call"}))
        stream.send_text(json.dumps(start))
        with pytest.raises(WebSocketDisconnect) as closed:
            stream.receive_text()

    assert closed.value.code == 1008
