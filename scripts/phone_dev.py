"""Open the phone line from this machine: a public tunnel for Twilio, then the voice server.

    uv run python scripts/phone_dev.py

Starts a Cloudflare quick tunnel (free, no account), points the softphone's TwiML App at it,
and runs the voice server with PUBLIC_BASE_URL set to the tunnel. Then open the printed
softphone page on this machine and call Kenji through Twilio. Ctrl+C stops both.

Needs cloudflared on PATH (or CLOUDFLARED=<path to it>) and the TWILIO_* settings in .env,
including the softphone's API key and TwiML App (see README, "Try the phone line").
Calls are answered only between 08:00 and 21:00 Japan time, as on the real line.
"""

import os
import re
import shutil
import subprocess
import sys
import threading
from typing import IO

import uvicorn
from twilio.rest import Client

from kenji.config import Settings
from kenji.phone_routes import VOICE_PATH
from kenji.server import configure_logging, create_app, load_settings
from kenji.softphone_routes import SOFTPHONE_PATH

TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


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


def main() -> None:
    settings = load_settings()
    tunnel, public_url = open_tunnel(settings.port)
    try:
        point_softphone_at(settings, public_url)
        os.environ["PUBLIC_BASE_URL"] = public_url
        settings = load_settings()
        configure_logging(settings.log_level)
        print(f"Twilio reaches Kenji at {public_url}", file=sys.stderr)
        print(f"Softphone: http://127.0.0.1:{settings.port}{SOFTPHONE_PATH}", file=sys.stderr)
        uvicorn.run(create_app(settings), host="127.0.0.1", port=settings.port, log_config=None)
    finally:
        tunnel.terminate()


if __name__ == "__main__":
    main()
