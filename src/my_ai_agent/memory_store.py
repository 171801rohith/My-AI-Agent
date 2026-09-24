"""Long-term memory kept on disk between runs:
- data/memory.json: facts the user asked the agent to remember.
- data/conversation.json: the most recent user/assistant messages, to resume a chat.
"""

import json
from pathlib import Path

from llama_index.core.llms import ChatMessage

from my_ai_agent.settings import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
FACTS_PATH = DATA_DIR / "memory.json"
HISTORY_PATH = DATA_DIR / "conversation.json"
HISTORY_MESSAGES = 20  # how many recent messages are carried over to the next run


def _read(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default  # a damaged file must not stop the app from starting


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # atomic: a crash mid-write never leaves a half-written file


def load_facts() -> list[str]:
    return _read(FACTS_PATH, [])


def add_fact(fact: str) -> bool:
    """Store a fact; returns False if it was already known."""
    fact = fact.strip()
    facts = load_facts()
    if not fact or fact.lower() in (f.lower() for f in facts):
        return False
    _write(FACTS_PATH, facts + [fact])
    return True


def remove_facts(text: str) -> list[str]:
    """Remove every fact containing `text` (case-insensitive) and return them."""
    needle = text.strip().lower()
    facts = load_facts()
    removed = [f for f in facts if needle and needle in f.lower()]
    if removed:
        _write(FACTS_PATH, [f for f in facts if f not in removed])
    return removed


def facts_prompt() -> str:
    """System-prompt section listing remembered facts, or '' if there are none."""
    facts = load_facts()
    if not facts:
        return ""
    lines = "\n".join(f"- {f}" for f in facts)
    return f"\n## What you remember about the user\n\n{lines}\n"


def load_history() -> list[ChatMessage]:
    return [
        ChatMessage(role=m["role"], content=m["content"])
        for m in _read(HISTORY_PATH, [])
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]


def save_history(messages: list[ChatMessage]) -> None:
    """Keep only plain user/assistant text; tool-call messages don't survive a restart."""
    plain = [
        {"role": m.role.value, "content": m.content}
        for m in messages
        if m.role.value in ("user", "assistant") and isinstance(m.content, str) and m.content.strip()
    ]
    _write(HISTORY_PATH, plain[-HISTORY_MESSAGES:])
