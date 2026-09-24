"""Append-only record of every side-effecting action the agent takes.

Each line of logs/actions.jsonl is one JSON entry:
    {"id": 3, "time": "...", "action": "rename", "summary": "...", "undo": {...} | null}
Undoing an action appends {"action": "undo", "target": <id>} instead of editing history.
"""

import json
from datetime import datetime

from my_ai_agent.settings import PROJECT_ROOT

ACTION_LOG_PATH = PROJECT_ROOT / "logs" / "actions.jsonl"


def read_all() -> list[dict]:
    if not ACTION_LOG_PATH.exists():
        return []
    with open(ACTION_LOG_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def record(action: str, summary: str, undo: dict | None = None, target: int | None = None) -> int:
    """Append an entry and return its id. `undo` describes how to reverse it, if possible."""
    entries = read_all()
    entry = {
        "id": (entries[-1]["id"] + 1) if entries else 1,
        "time": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "summary": summary,
        "undo": undo,
    }
    if target is not None:
        entry["target"] = target
    ACTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["id"]


def last_undoable() -> dict | None:
    """The most recent action that can be undone and has not been undone yet."""
    entries = read_all()
    undone = {e["target"] for e in entries if e["action"] == "undo"}
    for entry in reversed(entries):
        if entry.get("undo") and entry["id"] not in undone:
            return entry
    return None


def recent(count: int = 5) -> list[dict]:
    return [e for e in read_all() if e["action"] != "undo"][-count:]
