"""Twilio entry points: a signed voice webhook and the call's media stream."""

from fastapi import FastAPI, HTTPException, Request, WebSocket, status
from fastapi.responses import Response
from loguru import logger
from pipecat.runner.utils import parse_telephony_websocket

from kenji.adapters.twilio import stream_twiml, twilio_transport
from kenji.app.launcher import CallRequest
from kenji.app.privacy import caller_ref
from kenji.container import PhoneLine, Services

VOICE_PATH = "/twilio/voice"
STREAM_PATH = "/twilio/ws"
POLICY_VIOLATION = 1008


def _stream_url(public_base_url: str) -> str:
    return (
        public_base_url.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
        + STREAM_PATH
    )


def add_phone_routes(app: FastAPI, services: Services, phone: PhoneLine) -> None:
    @app.post(VOICE_PATH)
    async def voice(http: Request) -> Response:
        form = {key: str(value) for key, value in (await http.form()).items()}
        signature = http.headers.get("X-Twilio-Signature", "")
        if not phone.webhooks.is_signed(phone.public_base_url + VOICE_PATH, form, signature):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unsigned request")
        token = phone.tokens.issue(caller_ref(form.get("From", "unknown"), services.salt))
        twiml = stream_twiml(_stream_url(phone.public_base_url), token)
        return Response(content=twiml, media_type="application/xml")

    @app.websocket(STREAM_PATH)
    async def media_stream(websocket: WebSocket) -> None:
        await websocket.accept()
        _, call_data = await parse_telephony_websocket(websocket)
        token = str((call_data.get("body") or {}).get("token", ""))
        caller = phone.tokens.redeem(token)
        if caller is None or not call_data.call_id or not call_data.stream_id:
            logger.warning("media stream without a valid token was refused")
            await websocket.close(code=POLICY_VIOLATION)
            return
        transport = twilio_transport(
            websocket,
            stream_sid=call_data.stream_id,
            call_sid=call_data.call_id,
            credentials=phone.credentials,
        )
        request = CallRequest(transport="phone", caller_ref=caller, call_id=call_data.call_id)
        await services.launcher.run(transport, request)
