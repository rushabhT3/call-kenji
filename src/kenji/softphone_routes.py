"""A browser softphone that calls the phone line through Twilio, for trying it without a number.

It mints Twilio credentials, so it answers only a browser on this machine: a request that came
through a tunnel or a proxy, or that names another host, is told the page does not exist.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from kenji.adapters.twilio import SoftphoneTokens

SOFTPHONE_PATH = "/dev/softphone"
TOKEN_PATH = "/dev/softphone/token"  # noqa: S105 - a URL path, not a secret
LINK_PATH = "/api/softphone"
PAGE = Path(__file__).with_name("softphone.html")
LOOPBACK_ADDRESSES = frozenset({"127.0.0.1", "::1"})
LOCAL_HOSTNAMES = frozenset({"127.0.0.1", "localhost", "::1"})
FORWARDING_HEADERS = ("cf-connecting-ip", "x-forwarded-for", "forwarded", "x-kenji-proxy")


def is_from_this_machine(http: Request) -> bool:
    address = http.client.host if http.client else ""
    is_forwarded = any(header in http.headers for header in FORWARDING_HEADERS)
    return (
        address in LOOPBACK_ADDRESSES and http.url.hostname in LOCAL_HOSTNAMES and not is_forwarded
    )


def _require_this_machine(http: Request) -> None:
    if not is_from_this_machine(http):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


def add_softphone_routes(app: FastAPI, tokens: SoftphoneTokens, port: int) -> None:
    page = PAGE.read_text(encoding="utf-8")
    page_url = f"http://127.0.0.1:{port}{SOFTPHONE_PATH}"

    @app.get(LINK_PATH)
    async def softphone_link(http: Request) -> dict[str, str]:
        _require_this_machine(http)
        return {"url": page_url}

    @app.get(SOFTPHONE_PATH, response_class=HTMLResponse)
    async def softphone(http: Request) -> HTMLResponse:
        _require_this_machine(http)
        return HTMLResponse(page)

    @app.post(TOKEN_PATH)
    async def softphone_token(http: Request) -> dict[str, str]:
        _require_this_machine(http)
        return {"token": tokens.issue()}
