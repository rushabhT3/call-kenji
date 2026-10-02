"""Run the voice server on this machine for testing, optionally with the phone line.

    uv run python scripts/dev_server.py                       # browser calls, like `kenji-server`
    uv run python scripts/dev_server.py --afternoon-in-tokyo  # answer calls at any hour
    uv run python scripts/dev_server.py --phone               # also open the phone line

--afternoon-in-tokyo moves the server's clock to 15:00 Japan time, so a call is answered whatever
the hour. It is for testing only; the calling-hours rule has its own tests and the deployed
server never moves its clock.

--phone starts a Cloudflare quick tunnel (free, no account), points the softphone's TwiML App at
it, and sets PUBLIC_BASE_URL to the tunnel. Then open the printed softphone page on this machine
and call Kenji through Twilio. Needs cloudflared on PATH (or CLOUDFLARED=<path to it>) and the
TWILIO_* settings in .env, including the softphone's API key and TwiML App (see README,
"Try the phone line"). Ctrl+C stops the server and the tunnel.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import replace
from typing import IO

import uvicorn
from afternoon_clock import AfternoonInTokyoClock
from twilio.rest import Client

from kenji.app.ports import IceServer
from kenji.config import Settings
from kenji.container import build_kit, build_services
from kenji.phone_routes import VOICE_PATH
from kenji.server import configure_logging, create_app, load_settings
from kenji.softphone_routes import SOFTPHONE_PATH

TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


class ThisMachineOnly:
    """No STUN or TURN: the browser and the server share this machine, so they connect directly.

    Asking a STUN server costs aioice up to 5 s per call on a network adapter that cannot reach
    it, such as a virtual switch, and a call within one machine never needs a public address.
    """

    async def ice_servers(self) -> list[IceServer]:
        return []


def _cloudflared() -> str:
    path = os.environ.get("CLOUDFLARED") or shutil.which("cloudflared")
    if path is None:
        raise SystemExit("cloudflared not found: install it, or set CLOUDFLARED to its path")
    return path


def _drain(stream: IO[str]) -> None:
    for _ in stream:
        pass


def open_tunnel(port: int) -> tuple[subprocess.Popen[str], str]:
    """Start a quick tunnel to the local port and return it with its public https URL."""
    tunnel = subprocess.Popen(  # noqa: S603 - our own cloudflared, with fixed arguments
        [_cloudflared(), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    output = tunnel.stderr
    if output is None:
        raise SystemExit("cloudflared gave no output to read the tunnel URL from")
    for line in output:
        found = TUNNEL_URL.search(line)
        if found:
            threading.Thread(target=_drain, args=(output,), daemon=True).start()
            return tunnel, found.group(0)
    raise SystemExit("cloudflared stopped before it printed a tunnel URL")


def point_softphone_at(settings: Settings, public_url: str) -> None:
    sid, token, app_sid = (
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.twilio_twiml_app_sid,
    )
    if sid is None or token is None or app_sid is None:
        raise SystemExit("set the TWILIO_* settings in .env first, including TWILIO_TWIML_APP_SID")
    Client(sid, token.get_secret_value()).applications(app_sid).update(
        voice_url=public_url + VOICE_PATH, voice_method="POST"
    )


def _open_phone_line(settings: Settings) -> tuple[subprocess.Popen[str], Settings]:
    tunnel, public_url = open_tunnel(settings.port)
    point_softphone_at(settings, public_url)
    os.environ["PUBLIC_BASE_URL"] = public_url
    print(f"Twilio reaches Kenji at {public_url}", file=sys.stderr)
    print(f"Softphone: http://127.0.0.1:{settings.port}{SOFTPHONE_PATH}", file=sys.stderr)
    return tunnel, load_settings()


def _serve(settings: Settings, *, is_afternoon_in_tokyo: bool) -> None:
    kit = build_kit(settings)
    if is_afternoon_in_tokyo:
        kit = replace(kit, clock=AfternoonInTokyoClock())
        print("Testing: the clock reads 15:00 Japan time, so calls are answered", file=sys.stderr)
    configure_logging(settings.log_level)
    services = replace(build_services(settings, kit), ice=ThisMachineOnly())
    app = create_app(settings, services)
    uvicorn.run(app, host="127.0.0.1", port=settings.port, log_config=None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phone", action="store_true", help="open the phone line through Twilio")
    parser.add_argument(
        "--afternoon-in-tokyo", action="store_true", help="answer calls at any hour, for testing"
    )
    options = parser.parse_args()
    settings = load_settings()
    tunnel = None
    try:
        if options.phone:
            tunnel, settings = _open_phone_line(settings)
        _serve(settings, is_afternoon_in_tokyo=options.afternoon_in_tokyo)
    finally:
        if tunnel is not None:
            tunnel.terminate()


if __name__ == "__main__":
    main()
