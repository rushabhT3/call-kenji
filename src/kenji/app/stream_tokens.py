"""Single-use tokens that let only the call Twilio announced open the media stream."""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from kenji.app.ports import Clock

STREAM_TOKEN_TTL = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class StreamGrant:
    """What the webhook announced for the stream: who is calling and the persona they play."""

    caller_ref: str
    persona_id: str | None = None


@dataclass(frozen=True, slots=True)
class _Pending:
    grant: StreamGrant
    issued_at: datetime


class StreamTokens:
    def __init__(self, clock: Clock, ttl: timedelta = STREAM_TOKEN_TTL) -> None:
        self._clock = clock
        self._ttl = ttl
        self._pending: dict[str, _Pending] = {}

    def issue(self, grant: StreamGrant) -> str:
        self._drop_expired()
        token = secrets.token_urlsafe(24)
        self._pending[token] = _Pending(grant=grant, issued_at=self._clock.now())
        return token

    def redeem(self, token: str) -> StreamGrant | None:
        self._drop_expired()
        pending = self._pending.pop(token, None)
        return None if pending is None else pending.grant

    def _drop_expired(self) -> None:
        oldest_valid = self._clock.now() - self._ttl
        self._pending = {
            token: pending
            for token, pending in self._pending.items()
            if pending.issued_at >= oldest_valid
        }
