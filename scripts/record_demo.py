"""Turn one call's event log into the replay the page shows at ?demo=1.

    uv run python scripts/record_demo.py var/calls/2026-10-02/<call_id>/events.jsonl
    uv run python scripts/record_demo.py --text-mode     # scripted run, for development

The output is web/public/demo/call.json. Only the text events the live page already
received are kept; there is never any audio.
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "web" / "public" / "demo" / "call.json"


def from_event_log(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


async def from_text_mode() -> list[dict[str, Any]]:
    sys.path.insert(0, str(ROOT))
    from tests.conversation.harness import Say, ToolCall, start_text_call

    verify = ToolCall(
        "verify_identity", {"name_kana": "サトウユウキ", "date_of_birth": "1990-07-14"}
    )
    call = await start_text_call(
        [
            verify,
            Say("それはご心配ですね。毎月どのくらいでしたらお支払いいただけそうでしょうか。"),
            ToolCall("check_terms", {"monthly_yen": 3000}),
            Say("3,000円ですと、6回では完済に届きません。毎月6,000円ではいかがでしょうか。"),
            ToolCall("confirm_plan", {"monthly_yen": 6000}),
            ToolCall("record_promise"),
        ]
    )
    opened = time.monotonic()
    timeline: list[dict[str, Any]] = []
    original_publish = call.recorder.publish

    def timed_publish(event: Any) -> None:
        offset_ms = round((time.monotonic() - opened) * 1000)
        timeline.append({"offset_ms": offset_ms, "event": event.model_dump(mode="json")})
        original_publish(event)

    call.recorder.publish = timed_publish  # type: ignore[method-assign]
    for event in list(call.recorder.events):
        timeline.append({"offset_ms": 0, "event": event.model_dump(mode="json")})
    await call.wait_for_node("verify_identity")
    for utterance, node in [
        ("佐藤ゆうきです。平成2年7月14日生まれです。", "listen"),
        ("今月は仕事が減ってしまって、少し厳しいです。", None),
        ("3,000円なら払えると思います。", "negotiate"),
        ("わかりました。6,000円でお願いします。", "read_back"),
        ("はい、大丈夫です。", None),
    ]:
        await call.caller_says(utterance, then_node=node)
    await call.finish()
    return timeline


def write_recording(events: list[dict[str, Any]], source: str) -> None:
    recorded_on = datetime.now().astimezone().date().isoformat()
    recording = {"source": source, "recorded_on": recorded_on, "events": events}
    OUTPUT.write_text(json.dumps(recording, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(events)} events to {OUTPUT.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_log", nargs="?", type=Path)
    parser.add_argument("--text-mode", action="store_true")
    args = parser.parse_args()
    if args.text_mode:
        write_recording(asyncio.run(from_text_mode()), "scripted text-mode run (development only)")
    elif args.event_log:
        source = f"recorded call {args.event_log.parent.name}"
        write_recording(from_event_log(args.event_log), source)
    else:
        parser.error("give an events.jsonl path or --text-mode")


if __name__ == "__main__":
    main()
