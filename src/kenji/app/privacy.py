"""Callers are counted by a salted hash, never by their phone number or address."""

import hashlib
import hmac

CALLER_REF_LENGTH = 16


def caller_ref(raw_identifier: str, salt: bytes) -> str:
    if not salt:
        raise ValueError("a caller hash needs a salt")
    digest = hmac.new(salt, raw_identifier.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:CALLER_REF_LENGTH]
