"""Twilio Programmable Voice: signed webhooks in, Media Streams over a WebSocket."""

from collections.abc import Mapping
from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr

from fastapi import WebSocket
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams, FastAPIWebsocketTransport
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.request_validator import RequestValidator

# One identity for every softphone call, so the per-caller daily limit applies to it as a whole.
SOFTPHONE_IDENTITY = "kenji-softphone"
SOFTPHONE_TOKEN_TTL_SECS = 600


class TwilioWebhooks:
    def __init__(self, auth_token: str) -> None:
        self._validator = RequestValidator(auth_token)

    def is_signed(self, url: str, form: Mapping[str, str], signature: str) -> bool:
        return bool(signature) and bool(self._validator.validate(url, dict(form), signature))


@dataclass(frozen=True, slots=True)
class SoftphoneCredentials:
    account_sid: str
    api_key_sid: str
    api_key_secret: str
    twiml_app_sid: str


class SoftphoneTokens:
    """Short-lived Voice SDK tokens that can place a call to Kenji's TwiML App and nothing else."""

    def __init__(self, credentials: SoftphoneCredentials) -> None:
        self._credentials = credentials

    def issue(self) -> str:
        credentials = self._credentials
        token = AccessToken(
            credentials.account_sid,
            credentials.api_key_sid,
            credentials.api_key_secret,
            identity=SOFTPHONE_IDENTITY,
            ttl=SOFTPHONE_TOKEN_TTL_SECS,
        )
        token.add_grant(VoiceGrant(outgoing_application_sid=credentials.twiml_app_sid))
        return str(token.to_jwt())


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
