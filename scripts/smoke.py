"""Check a running Call Kenji deployment end to end, without making a call.

    uv run python scripts/smoke.py https://call-kenji.example.workers.dev
    uv run python scripts/smoke.py http://localhost:7860 --server-only

Exits non-zero if any check fails.
"""

import argparse
import asyncio
import json
import sys
from collections.abc import Awaitable, Callable
from http import HTTPStatus

import httpx
import websockets

type Check = Callable[[httpx.AsyncClient, str], Awaitable[str]]


async def page_is_served(client: httpx.AsyncClient, base: str) -> str:
    response = await client.get(f"{base}/")
    response.raise_for_status()
    if "Call Kenji" not in response.text:
        raise AssertionError("page does not look like Call Kenji")
    return "page served"


async def demo_recording_is_served(client: httpx.AsyncClient, base: str) -> str:
    response = await client.get(f"{base}/demo/call.json")
    response.raise_for_status()
    return f"demo recording has {len(response.json()['events'])} events"


async def health_answers(client: httpx.AsyncClient, base: str) -> str:
    response = await client.get(f"{base}/api/health")
    response.raise_for_status()
    if response.json() != {"status": "ok"}:
        raise AssertionError(f"unexpected health reply: {response.text}")
    return "voice server healthy"


async def ice_servers_are_issued(client: httpx.AsyncClient, base: str) -> str:
    response = await client.get(f"{base}/api/ice")
    response.raise_for_status()
    urls = [url for server in response.json()["iceServers"] for url in server["urls"]]
    relays = [url for url in urls if url.startswith(("turn:", "turns:"))]
    return f"{len(urls)} ICE URLs, {len(relays)} TURN relays"


async def viewer_gets_a_code(_client: httpx.AsyncClient, base: str) -> str:
    socket_url = base.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
    async with websockets.connect(f"{socket_url}/ws/viewer") as viewer:
        ready = json.loads(await asyncio.wait_for(viewer.recv(), 10))
    code = ready.get("code", "")
    if ready.get("type") != "viewer_ready" or len(code) != 4 or not code.isdigit():
        raise AssertionError(f"unexpected viewer reply: {ready}")
    return "viewer feed issued a 4-digit code"


async def unsigned_webhook_is_refused(client: httpx.AsyncClient, base: str) -> str:
    response = await client.post(f"{base}/twilio/voice", data={"From": "+15550000000"})
    if response.status_code == HTTPStatus.NOT_FOUND:
        return "phone line not configured here"
    if response.status_code != HTTPStatus.FORBIDDEN:
        raise AssertionError(f"unsigned webhook got {response.status_code}, expected 403")
    return "unsigned Twilio webhook refused"


SITE_CHECKS: list[Check] = [page_is_served, demo_recording_is_served]
SERVER_CHECKS: list[Check] = [
    health_answers,
    ice_servers_are_issued,
    viewer_gets_a_code,
    unsigned_webhook_is_refused,
]


async def run(base: str, checks: list[Check]) -> bool:
    is_healthy = True
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for check in checks:
            try:
                print(f"PASS  {check.__name__}: {await check(client, base)}")
            except Exception as error:  # every failing check is reported, not just the first
                is_healthy = False
                print(f"FAIL  {check.__name__}: {error}")
    return is_healthy


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--server-only", action="store_true", help="skip the static page checks")
    args = parser.parse_args()
    checks = SERVER_CHECKS if args.server_only else SITE_CHECKS + SERVER_CHECKS
    sys.exit(0 if asyncio.run(run(args.base_url.rstrip("/"), checks)) else 1)


if __name__ == "__main__":
    main()
