import json

import httpx

from kenji.adapters.turn import CloudflareTurn, StunOnly
from kenji.app.ports import IceServer
from kenji.server import bot_ice_servers

CLOUDFLARE_REPLY = {
    "iceServers": [
        {"urls": ["stun:stun.cloudflare.com:3478", "stun:stun.cloudflare.com:53"]},
        {
            "urls": [
                "turn:turn.cloudflare.com:3478?transport=udp",
                "turn:turn.cloudflare.com:53?transport=udp",
                "turns:turn.cloudflare.com:443?transport=tcp",
            ],
            "username": "user",
            "credential": "secret",
        },
    ]
}


async def test_cloudflare_credentials_are_minted_per_call() -> None:
    seen: list[httpx.Request] = []

    def reply(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=CLOUDFLARE_REPLY)

    client = httpx.AsyncClient(transport=httpx.MockTransport(reply))
    servers = await CloudflareTurn("key-1", "token-1", client).ice_servers()

    assert seen[0].url.path.endswith("/turn/keys/key-1/credentials/generate-ice-servers")
    assert seen[0].headers["Authorization"] == "Bearer token-1"
    assert json.loads(seen[0].content) == {"ttl": 600}
    assert servers[1].username == "user"
    assert all(":53" not in url for server in servers for url in server.urls)


async def test_local_development_uses_stun_only() -> None:
    servers = await StunOnly("stun:stun.example:3478").ice_servers()

    assert [server.to_browser() for server in servers] == [{"urls": ["stun:stun.example:3478"]}]


def test_bot_gets_one_stun_and_the_udp_relay() -> None:
    servers = [
        IceServer(urls=["stun:stun.cloudflare.com:3478"]),
        IceServer(
            urls=[
                "turns:turn.cloudflare.com:443?transport=tcp",
                "turn:turn.cloudflare.com:3478?transport=udp",
            ],
            username="user",
            credential="secret",
        ),
    ]

    picked = bot_ice_servers(servers)

    assert [server.urls for server in picked] == [
        "stun:stun.cloudflare.com:3478",
        "turn:turn.cloudflare.com:3478?transport=udp",
    ]
    assert picked[1].username == "user"


def test_bot_without_turn_credentials_uses_stun_only() -> None:
    picked = bot_ice_servers([IceServer(urls=["stun:stun.example:3478"])])

    assert [server.urls for server in picked] == ["stun:stun.example:3478"]
