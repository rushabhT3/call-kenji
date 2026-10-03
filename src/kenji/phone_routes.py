"""Twilio entry points: a signed voice webhook and the call's media stream."""

from collections.abc import Mapping

from fastapi import FastAPI, HTTPException, Request, WebSocket, status
from fastapi.responses import Response
from loguru import logger
from pipecat.runner.utils import parse_telephony_websocket

from kenji.adapters.twilio import refusal_twiml, stream_twiml, twilio_transport
from kenji.app.launcher import CallRequest
from kenji.app.privacy import caller_ref
from kenji.app.stream_tokens import StreamGrant
from kenji.container import PhoneLine, Services

VOICE_PATH = "/twilio/voice"
STREAM_PATH = "/twilio/ws"
# The dev softphone names a persona as a Twilio custom parameter; a real phone call has none.
PERSONA_PARAMETER = "persona"
POLICY_VIOLATION = 1008


def _stream_url(public_base_url: str) -> str:
    return (
        public_base_url.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
        + STREAM_PATH
    )


def _twiml(document: str) -> Response:
    return Response(content=document, media_type="application/xml")


def _grant(form: Mapping[str, str], salt: bytes) -> StreamGrant:
    return StreamGrant(
        caller_ref=caller_ref(form.get("From", "unknown"), salt),
        persona_id=form.get(PERSONA_PARAMETER) or None,
    )


def _phone_request(grant: StreamGrant, call_id: str) -> CallRequest:
    return CallRequest(
        transport="phone", caller_ref=grant.caller_ref, call_id=call_id, persona_id=grant.persona_id
    )


def add_phone_routes(app: FastAPI, services: Services, phone: PhoneLine) -> None:
    @app.post(VOICE_PATH)
    async def voice(http: Request) -> Response:
        form = {key: str(value) for key, value in (await http.form()).items()}
        signature = http.headers.get("X-Twilio-Signature", "")
        if not phone.webhooks.is_signed(phone.public_base_url + VOICE_PATH, form, signature):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unsigned request")
        grant = _grant(form, services.salt)
        refusal = await services.launcher.screen(_phone_request(grant, form.get("CallSid", "")))
        if refusal is not None:
            return _twiml(refusal_twiml(refusal.ja, refusal.en))
        token = phone.tokens.issue(grant)
        return _twiml(stream_twiml(_stream_url(phone.public_base_url), token))

    @app.websocket(STREAM_PATH)
    async def media_stream(websocket: WebSocket) -> None:
        await websocket.accept()
        _, call_data = await parse_telephony_websocket(websocket)
        token = str((call_data.get("body") or {}).get("token", ""))
        grant = phone.tokens.redeem(token)
        if grant is None or not call_data.call_id or not call_data.stream_id:
            logger.warning("media stream without a valid token was refused")
            await websocket.close(code=POLICY_VIOLATION)
            return
        transport = twilio_transport(
            websocket,
            stream_sid=call_data.stream_id,
            call_sid=call_data.call_id,
            credentials=phone.credentials,
        )
        await services.launcher.run(transport, _phone_request(grant, call_data.call_id))
