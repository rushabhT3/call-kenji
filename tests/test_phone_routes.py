"""The public phone endpoints only answer Twilio, and only for the call it announced."""

import json
import re
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.websockets import WebSocketDisconnect
from twilio.request_validator import RequestValidator

from kenji.adapters.twilio import TwilioWebhooks
from kenji.app.events import CallStarted
from kenji.app.launcher import CallRequest
from kenji.app.stream_tokens import StreamTokens
from kenji.config import Settings
from kenji.container import PhoneLine, Services
from kenji.domain.outcome import CallOutcome
from kenji.server import create_app
from tests.app.test_launcher import MemoryUsage, launcher_for
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
    return _client(phone_services, tmp_path)


def _client(services: Services, tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        llm_api_key=SecretStr("test"),
        soniox_api_key=SecretStr("test"),
        cartesia_api_key=SecretStr("test"),
        data_dir=tmp_path,
    )
    return TestClient(create_app(settings, services))


def _signature(form: dict[str, str]) -> str:
    return str(RequestValidator(AUTH_TOKEN).compute_signature(BASE_URL + "/twilio/voice", form))


def _signed_voice_webhook(client: TestClient, form: dict[str, str]) -> str:
    response = client.post(
        "/twilio/voice", data=form, headers={"X-Twilio-Signature": _signature(form)}
    )
    assert response.status_code == 200
    return response.text


def _stream_start(token: str) -> dict[str, Any]:
    return {
        "event": "start",
        "start": {"streamSid": "MZ1", "callSid": "CA123", "customParameters": {"token": token}},
    }


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


def test_signed_webhook_over_the_daily_limit_says_why_and_hangs_up(
    phone_services: Services, tmp_path: Path
) -> None:
    spent_launcher = launcher_for(FixedClock(), MemoryUsage(calls_by_caller=3)).launcher
    client = _client(replace(phone_services, launcher=spent_launcher), tmp_path)

    with client:
        response = client.post(
            "/twilio/voice", data=FORM, headers={"X-Twilio-Signature": _signature(FORM)}
        )

    assert response.status_code == 200
    assert '<Say voice="Polly.Takumi" language="ja-JP">' in response.text
    assert "上限" in response.text
    assert response.text.endswith("<Hangup/></Response>")
    assert "<Stream" not in response.text


def test_media_stream_without_a_valid_token_is_closed(client: TestClient) -> None:
    with client, client.websocket_connect("/twilio/ws") as stream:
        stream.send_text(json.dumps({"event": "connected", "protocol": "Call"}))
        stream.send_text(json.dumps(_stream_start("forged")))
        with pytest.raises(WebSocketDisconnect) as closed:
            stream.receive_text()

    assert closed.value.code == 1008


@pytest.mark.parametrize(
    ("persona_field", "persona_id"),
    [({"persona": "tanaka"}, "tanaka"), ({"persona": ""}, None), ({}, None)],
)
def test_the_softphones_persona_is_played_on_the_media_stream(
    client: TestClient,
    phone_services: Services,
    monkeypatch: pytest.MonkeyPatch,
    persona_field: dict[str, str],
    persona_id: str | None,
) -> None:
    requests: list[CallRequest] = []
    # The test client runs the app on another thread; the stream stays open until the call starts.
    call_started = threading.Event()

    async def run(_transport: object, request: CallRequest) -> CallOutcome:
        requests.append(request)
        call_started.set()
        return CallOutcome.NO_AGREEMENT

    monkeypatch.setattr(phone_services.launcher, "run", run)
    with client:
        twiml = _signed_voice_webhook(client, FORM | persona_field)
        token = re.findall(r'<Parameter name="token" value="([^"]+)"', twiml)[0]
        with client.websocket_connect("/twilio/ws") as stream:
            stream.send_text(json.dumps({"event": "connected", "protocol": "Call"}))
            stream.send_text(json.dumps(_stream_start(token)))
            assert call_started.wait(timeout=5)

    assert [(request.call_id, request.persona_id) for request in requests] == [
        ("CA123", persona_id)
    ]


def test_a_refused_softphone_call_names_its_persona(
    phone_services: Services, tmp_path: Path
) -> None:
    spent = launcher_for(FixedClock(), MemoryUsage(calls_by_caller=3))
    client = _client(replace(phone_services, launcher=spent.launcher), tmp_path)

    with client:
        _signed_voice_webhook(client, FORM | {"persona": "ito"})

    started = cast(CallStarted, spent.recorder.of_type("call_started")[0])
    assert started.persona_id == "ito"
