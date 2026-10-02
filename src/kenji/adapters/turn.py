"""ICE servers for browser calls: plain STUN locally, short-lived Cloudflare TURN when deployed.

A container on Cloud Run cannot receive UDP, so in production both peers relay media through
Cloudflare's TURN service. Credentials are minted per call and expire on their own.
"""

from typing import Any

import httpx

from kenji.app.ports import IceServer

CLOUDFLARE_TURN_API = (
    "https://rtc.live.cloudflare.com/v1/turn/keys/{key_id}/credentials/generate-ice-servers"
)
CREDENTIAL_TTL_SECS = 600
_TIMEOUT_SECS = 5.0


class StunOnly:
    def __init__(self, stun_url: str) -> None:
        self._stun_url = stun_url

    async def ice_servers(self) -> list[IceServer]:
        return [IceServer(urls=[self._stun_url])]


def _usable(urls: list[str]) -> list[str]:
    # Port 53 relays are only useful with full ICE gathering, which the browser call skips.
    return [url for url in urls if ":53?" not in url and not url.endswith(":53")]


def _parse(payload: dict[str, Any]) -> list[IceServer]:
    servers = []
    for raw in payload.get("iceServers", []):
        urls = raw["urls"] if isinstance(raw["urls"], list) else [raw["urls"]]
        servers.append(
            IceServer(
                urls=_usable([str(url) for url in urls]),
                username=raw.get("username"),
                credential=raw.get("credential"),
            )
        )
    return [server for server in servers if server.urls]


class CloudflareTurn:
    def __init__(
        self, key_id: str, api_token: str, client: httpx.AsyncClient | None = None
    ) -> None:
        self._url = CLOUDFLARE_TURN_API.format(key_id=key_id)
        self._api_token = api_token
        self._client = client or httpx.AsyncClient(timeout=_TIMEOUT_SECS)

    async def ice_servers(self) -> list[IceServer]:
        response = await self._client.post(
            self._url,
            headers={"Authorization": f"Bearer {self._api_token}"},
            json={"ttl": CREDENTIAL_TTL_SECS},
        )
        response.raise_for_status()
        return _parse(response.json())
