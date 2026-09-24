from unittest.mock import MagicMock

import pytest

from my_ai_agent import action_log
from my_ai_agent.settings import Settings
from my_ai_agent.tools import app_file_tools, history_tools
from my_ai_agent.tools.app_file_tools import AppAndFileTools
from my_ai_agent.tools.history_tools import HistoryTools


def test_record_and_read_back():
    first = action_log.record("send_mail", "Sent email to a@x.com")
    second = action_log.record("note", "Wrote note", undo={"type": "delete_file", "path": "p"})

    assert (first, second) == (1, 2)
    assert [e["summary"] for e in action_log.read_all()] == ["Sent email to a@x.com", "Wrote note"]
    assert action_log.last_undoable()["id"] == 2


def test_nothing_to_undo():
    action_log.record("send_mail", "Sent email")  # not undoable

    assert HistoryTools().undo_last_action() == "There is nothing that can be undone."


def test_rename_then_undo_restores_names(tmp_path, no_startfile, confirm_answer):
    for name in ["Show 2.mkv", "Show 10.mkv"]:
        (tmp_path / name).write_text(name)
    AppAndFileTools().rename_files_to_episodes(str(tmp_path))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["E01.mkv", "E02.mkv"]

    result = HistoryTools().undo_last_action()

    assert result.startswith("Undid")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Show 10.mkv", "Show 2.mkv"]
    assert (tmp_path / "Show 10.mkv").read_text() == "Show 10.mkv"
    assert "E02.mkv  ->  Show 10.mkv" in confirm_answer.asked[-1][1]
    assert action_log.last_undoable() is None  # already undone


def test_undo_refuses_when_files_changed(tmp_path, no_startfile):
    (tmp_path / "a.mkv").write_text("")
    AppAndFileTools().rename_files_to_episodes(str(tmp_path))
    (tmp_path / "E01.mkv").rename(tmp_path / "moved.mkv")

    result = HistoryTools().undo_last_action()

    assert result.startswith("Failed") and "E01.mkv" in result
    assert [p.name for p in tmp_path.iterdir()] == ["moved.mkv"]


def test_declined_undo_changes_nothing(tmp_path, no_startfile, confirm_answer):
    (tmp_path / "a.mkv").write_text("")
    AppAndFileTools().rename_files_to_episodes(str(tmp_path))
    confirm_answer.approve = False

    assert HistoryTools().undo_last_action().startswith("Cancelled")
    assert [p.name for p in tmp_path.iterdir()] == ["E01.mkv"]
    assert action_log.last_undoable() is not None


def test_note_then_undo_deletes_the_note(tmp_path, monkeypatch, no_startfile):
    monkeypatch.setattr(app_file_tools, "settings", Settings(notes_dir=str(tmp_path)))
    assert AppAndFileTools().note_down_in_txt("buy milk") == "Successfully noted down to File_1.txt."

    HistoryTools().undo_last_action()

    assert list(tmp_path.iterdir()) == []


def test_draft_undo_deletes_the_draft(monkeypatch):
    gmail = MagicMock()
    monkeypatch.setattr(history_tools, "get_gmail_service", lambda: gmail)
    action_log.record("create_draft", "Created draft", undo={"type": "delete_draft", "draft_id": "d1"})

    assert HistoryTools().undo_last_action() == "Undid 'Created draft': deleted the Gmail draft."
    gmail.users().drafts().delete.assert_called_with(userId="me", id="d1")


def test_list_recent_actions_marks_undoable():
    action_log.record("send_mail", "Sent email to a@x.com")
    action_log.record("note", "Wrote note File_1.txt", undo={"type": "delete_file", "path": "p"})

    listing = HistoryTools().list_recent_actions()

    assert "#1" in listing and "Sent email to a@x.com" in listing
    assert "Wrote note File_1.txt (undoable)" in listing


def test_list_recent_actions_when_empty():
    assert HistoryTools().list_recent_actions() == "No actions have been recorded yet."
