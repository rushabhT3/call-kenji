"""Twilio Programmable Voice: signed webhooks in, Media Streams over a WebSocket."""

from collections.abc import Mapping
from xml.sax.saxutils import escape, quoteattr

from fastapi import WebSocket
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams, FastAPIWebsocketTransport
from twilio.request_validator import RequestValidator


class TwilioWebhooks:
    def __init__(self, auth_token: str) -> None:
        self._validator = RequestValidator(auth_token)

    def is_signed(self, url: str, form: Mapping[str, str], signature: str) -> bool:
        return bool(signature) and bool(self._validator.validate(url, dict(form), signature))


JAPANESE_VOICE = "Polly.Takumi"
ENGLISH_VOICE = "Polly.Matthew"


def refusal_twiml(japanese: str, english: str) -> str:
    """Say why the call cannot go ahead, then hang up, without opening a media stream."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="{JAPANESE_VOICE}" language="ja-JP">{escape(japanese)}</Say>'
        f'<Say voice="{ENGLISH_VOICE}" language="en-US">{escape(english)}</Say>'
        "<Hangup/>"
        "</Response>"
    )


def stream_twiml(stream_url: str, token: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response><Connect>"
        f"<Stream url={quoteattr(stream_url)}>"
        f'<Parameter name="token" value={quoteattr(token)}/>'
        "</Stream>"
        "</Connect></Response>"
    )


def twilio_transport(
    websocket: WebSocket, *, stream_sid: str, call_sid: str, credentials: tuple[str, str]
) -> BaseTransport:
    account_sid, auth_token = credentials
    serializer = TwilioFrameSerializer(
        stream_sid=stream_sid, call_sid=call_sid, account_sid=account_sid, auth_token=auth_token
    )
    return FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=serializer,
            allowed_origins=[],
        ),
    )
