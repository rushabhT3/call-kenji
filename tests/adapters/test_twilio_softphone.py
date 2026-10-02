"""A softphone token can only place a call to Kenji's own TwiML App, and soon expires."""

from twilio.jwt import Jwt

from kenji.adapters.twilio import (
    SOFTPHONE_IDENTITY,
    SOFTPHONE_TOKEN_TTL_SECS,
    SoftphoneCredentials,
    SoftphoneTokens,
)

KEY_SECRET = "softphone-key-secret-of-thirty-two-bytes"
CREDENTIALS = SoftphoneCredentials(
    account_sid="AC123", api_key_sid="SK123", api_key_secret=KEY_SECRET, twiml_app_sid="AP123"
)


def _issued() -> Jwt:
    return Jwt.from_jwt(SoftphoneTokens(CREDENTIALS).issue(), KEY_SECRET)


def test_the_token_grants_an_outgoing_call_to_kenjis_app_only() -> None:
    grants = _issued().payload["grants"]

    assert grants == {
        "identity": SOFTPHONE_IDENTITY,
        "voice": {"outgoing": {"application_sid": "AP123"}},
    }


def test_the_token_is_signed_by_the_api_key_for_the_account_and_expires() -> None:
    payload = _issued().payload

    assert payload["iss"] == "SK123"
    assert payload["sub"] == "AC123"
    assert payload["exp"] - payload["nbf"] == SOFTPHONE_TOKEN_TTL_SECS
