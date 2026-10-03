"""The page's copy of the personas stays in step with content/personas.yaml."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
EXPORT_SCRIPT = ROOT / "scripts" / "export_personas.py"
COMMITTED_EXPORT = ROOT / "web" / "public" / "personas.json"


def _export_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("export_personas", EXPORT_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_committed_export_matches_the_personas_file() -> None:
    committed = json.loads(COMMITTED_EXPORT.read_text(encoding="utf-8"))

    assert _export_script().exported() == committed, (
        "run `uv run python scripts/export_personas.py` and commit web/public/personas.json"
    )
