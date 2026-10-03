"""Download SenseVoice-Small (int8, for sherpa-onnx), which hears how the caller sounds.

    uv run python scripts/fetch_emotion_model.py                  # into models/sense-voice
    uv run python scripts/fetch_emotion_model.py path/to/dir

Then set CALLER_EMOTION_MODEL_DIR to that directory. The archive (163 MB) is checked against its
published SHA-256, and only the model (228 MB) and its token list are kept. models/ is gitignored.
"""

import argparse
import hashlib
import shutil
import tarfile
import tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "models" / "sense-voice"
RELEASE = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17"
ARCHIVE_URL = (
    f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{RELEASE}.tar.bz2"
)
ARCHIVE_SHA256 = "7d1efa2138a65b0b488df37f8b89e3d91a60676e416f515b952358d83dfd347e"
KEPT_FILES = ("model.int8.onnx", "tokens.txt")
CHUNK_BYTES = 1 << 20


def download(url: str, destination: Path) -> str:
    digest = hashlib.sha256()
    with (
        httpx.stream("GET", url, follow_redirects=True, timeout=60) as response,
        destination.open("wb") as file,
    ):
        response.raise_for_status()
        for chunk in response.iter_bytes(CHUNK_BYTES):
            digest.update(chunk)
            file.write(chunk)
    return digest.hexdigest()


def extract(archive: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r|bz2") as tar:
        for member in tar:
            name = Path(member.name).name
            source = tar.extractfile(member) if member.isfile() and name in KEPT_FILES else None
            if source is not None:
                with source, (target / name).open("wb") as file:
                    shutil.copyfileobj(source, file, CHUNK_BYTES)
                print(f"wrote {target / name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target", nargs="?", type=Path, default=DEFAULT_DIR)
    target: Path = parser.parse_args().target
    with tempfile.TemporaryDirectory() as scratch:
        archive = Path(scratch) / f"{RELEASE}.tar.bz2"
        print(f"downloading {ARCHIVE_URL}")
        if download(ARCHIVE_URL, archive) != ARCHIVE_SHA256:
            raise SystemExit("the downloaded archive does not match its published SHA-256")
        extract(archive, target)


if __name__ == "__main__":
    main()
