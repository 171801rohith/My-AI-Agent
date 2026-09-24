import logging
import os

from llama_index.core.tools import FunctionTool

from my_ai_agent import action_log
from my_ai_agent.functions.file_ops import apply_renames
from my_ai_agent.gmail_auth import get_gmail_service
from my_ai_agent.tools import confirm as confirmation

logger = logging.getLogger(__name__)


def _undo_rename(undo: dict) -> str:
    folder = undo["folder"]
    reverse = [(new, old) for old, new in undo["renames"]]
    missing = [new for new, _ in reverse if not os.path.exists(os.path.join(folder, new))]
    if missing:
        raise RuntimeError(f"files changed since the rename; missing: {', '.join(missing[:5])}")
    apply_renames(folder, reverse)
    return f"restored {len(reverse)} original file names in {folder}"


def _undo_delete_file(undo: dict) -> str:
    os.remove(undo["path"])
    return f"deleted {undo['path']}"


def _undo_delete_draft(undo: dict) -> str:
    get_gmail_service().users().drafts().delete(userId="me", id=undo["draft_id"]).execute()
    return "deleted the Gmail draft"


UNDO_HANDLERS = {
    "rename": _undo_rename,
    "delete_file": _undo_delete_file,
    "delete_draft": _undo_delete_draft,
}


def describe_undo(undo: dict) -> str:
    if undo["type"] == "rename":
        pairs = "\n".join(f"{new}  ->  {old}" for old, new in undo["renames"])
        return f"Rename back in {undo['folder']}:\n{pairs}"
    if undo["type"] == "delete_file":
        return f"Delete the file {undo['path']}"
    return f"Delete Gmail draft {undo['draft_id']}"


class HistoryTools:
    def __init__(self):
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.list_recent_actions,
                description="""List the most recent actions the agent has taken (emails, drafts, renames,
                    notes, closed apps), newest last, and whether each can be undone.
                    Input: count (int, default 5).""",
            ),
            FunctionTool.from_defaults(
                fn=self.undo_last_action,
                description="""Undo the most recent action that can be undone: a file rename, a note,
                    or a Gmail draft. Sent emails and closed apps cannot be undone.
                    The user is asked to confirm first.""",
            ),
        ]

    def list_recent_actions(self, count: int = 5) -> str:
        entries = action_log.recent(max(1, min(int(count), 20)))
        if not entries:
            return "No actions have been recorded yet."
        return "\n".join(
            f"#{e['id']} {e['time']} {e['summary']}" + (" (undoable)" if e.get("undo") else "")
            for e in entries
        )

    def undo_last_action(self) -> str:
        entry = action_log.last_undoable()
        if entry is None:
            return "There is nothing that can be undone."
        undo = entry["undo"]
        if not confirmation.confirm(f"Undo: {entry['summary']}", describe_undo(undo)):
            return confirmation.CANCELLED
        try:
            result = UNDO_HANDLERS[undo["type"]](undo)
        except Exception as e:
            logger.exception("Undo failed")
            return f"Failed to undo '{entry['summary']}'. Error: {str(e)}"
        action_log.record("undo", f"Undid #{entry['id']}: {result}", target=entry["id"])
        return f"Undid '{entry['summary']}': {result}."
