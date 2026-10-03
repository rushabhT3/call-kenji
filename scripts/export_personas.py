"""Export what the page shows of each persona to web/public/personas.json.

    uv run python scripts/export_personas.py

content/personas.yaml stays the one source: the server reads the accounts from it, and the page
reads this export, which a test keeps in step with it. Each line gets the path of the clip that
scripts/phrase_clips.py records for it.
"""

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "content" / "personas.yaml"
OUTPUT = ROOT / "web" / "public" / "personas.json"


def clip_path(persona_id: str, phrase_id: str) -> str:
    return f"/phrases/{persona_id}/{phrase_id}.m4a"


def _public(persona: dict[str, Any]) -> dict[str, Any]:
    debtor = persona["debtor"]
    return {
        "id": persona["id"],
        "name": {
            "ja": debtor["written_name"],
            "kana": debtor["family_name_kana"] + debtor["given_name_kana"],
            "en": persona["name_en"],
        },
        "birth": {"iso": str(debtor["date_of_birth"]), "ja": persona["birth_date_ja"]},
        "account_suffix": persona["account_suffix"],
        "balance_yen": persona["balance_yen"],
        "overdue_since": str(persona["overdue_since"]),
        "situation": persona["situation"],
        "mood": persona["mood"],
        "phrases": [
            phrase | {"clip": clip_path(persona["id"], phrase["id"])}
            for phrase in persona["phrases"]
        ],
    }


def exported(source: Path = SOURCE) -> dict[str, Any]:
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    return {"default": raw["default"], "personas": [_public(p) for p in raw["personas"]]}


def main() -> None:
    OUTPUT.write_text(json.dumps(exported(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
