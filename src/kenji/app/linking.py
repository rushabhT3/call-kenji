"""Link a phone call to the one browser tab whose 4-digit code the caller keyed in."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from kenji.app.ports import Clock

CODE_LENGTH = 4
CODE_TTL = timedelta(minutes=10)
CODE_REFRESH = CODE_TTL / 2
MAX_FAILED_ATTEMPTS_PER_CALL = 3


def random_code() -> str:
    return f"{secrets.randbelow(10**CODE_LENGTH):0{CODE_LENGTH}d}"


@dataclass(frozen=True, slots=True)
class _PendingLink:
    viewer_id: str
    issued_at: datetime


class LinkRegistry:
    def __init__(self, clock: Clock, code_source: Callable[[], str] = random_code) -> None:
        self._clock = clock
        self._code_source = code_source
        self._pending: dict[str, _PendingLink] = {}
        self._failed_attempts: dict[str, int] = {}

    def issue(self, viewer_id: str) -> str:
        self._drop_expired()
        self._pending = {
            code: link for code, link in self._pending.items() if link.viewer_id != viewer_id
        }
        code = self._unused_code()
        self._pending[code] = _PendingLink(viewer_id=viewer_id, issued_at=self._clock.now())
        return code

    def redeem(self, call_id: str, code: str) -> str | None:
        if self._failed_attempts.get(call_id, 0) >= MAX_FAILED_ATTEMPTS_PER_CALL:
            return None
        self._drop_expired()
        link = self._pending.pop(code, None)
        if link is None:
            self._failed_attempts[call_id] = self._failed_attempts.get(call_id, 0) + 1
            return None
        return link.viewer_id

    def _unused_code(self) -> str:
        for _ in range(10**CODE_LENGTH):
            code = self._code_source()
            if code not in self._pending:
                return code
        raise RuntimeError("no free link codes")

    def _drop_expired(self) -> None:
        oldest_valid = self._clock.now() - CODE_TTL
        self._pending = {
            code: link for code, link in self._pending.items() if link.issued_at >= oldest_valid
        }
