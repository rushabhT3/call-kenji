"""Record each persona's lines in the synthetic caller's voice, for the page's "Say it" buttons.

    uv run python scripts/phrase_clips.py           # only the clips that are missing
    uv run python scripts/phrase_clips.py --force   # every clip again

Every phrase in content/personas.yaml is spoken by the Cartesia caller voice of
scripts/synthetic_caller.py and saved as AAC at web/public/phrases/<persona>/<phrase>.m4a, the
path scripts/export_personas.py gives it. The voice is synthetic, so no one's own voice is used.
Needs CARTESIA_API_KEY and the rest of the server settings; a full run costs a few cents.
"""

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
from demo_recording import _encode
from export_personas import exported
from synthetic_caller import CallerVoice

from kenji.server import load_settings

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "web" / "public"


@dataclass(frozen=True)
class Clip:
    line: str
    path: Path


def all_clips() -> list[Clip]:
    return [
        Clip(phrase["ja"], PUBLIC_DIR / phrase["clip"].lstrip("/"))
        for persona in exported()["personas"]
        for phrase in persona["phrases"]
    ]


def _save(pcm: bytes, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _encode(np.frombuffer(pcm, dtype=np.int16), path)


async def record(clips: list[Clip]) -> None:
    async with httpx.AsyncClient(timeout=30) as http:
        voice = CallerVoice(load_settings(), http)
        for clip in clips:
            await asyncio.to_thread(_save, await voice.pcm(clip.line), clip.path)
            print(f"wrote {clip.path.relative_to(ROOT).as_posix()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--force", action="store_true", help="record clips that already exist")
    options = parser.parse_args()
    clips = [clip for clip in all_clips() if options.force or not clip.path.exists()]
    print(f"{len(clips)} clips to record")
    asyncio.run(record(clips))


if __name__ == "__main__":
    main()
