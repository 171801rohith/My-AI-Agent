import pytest

from my_ai_agent.tools import app_file_tools
from my_ai_agent.tools.app_file_tools import AppAndFileTools
from my_ai_agent.settings import Settings


@pytest.fixture
def tools():
    return AppAndFileTools()


@pytest.fixture
def fake_appopener(monkeypatch):
    calls = []

    def fake(action):
        def run(name, **kwargs):
            calls.append((action, name))
            if name == "missing":
                raise ValueError("app not found")

        return run

    monkeypatch.setattr(app_file_tools.AppOpener, "open", fake("open"))
    monkeypatch.setattr(app_file_tools.AppOpener, "close", fake("close"))
    return calls


def test_registered_tool_names(tools):
    assert {t.metadata.name for t in tools.tools} == {
        "open_app",
        "close_app",
        "open_directory",
        "rename_files_to_episodes",
        "note_down_in_txt",
    }


def test_open_app(tools, fake_appopener):
    assert tools.open_app("brave") == "Successfully opened brave."
    assert fake_appopener == [("open", "brave")]


def test_open_app_failure_is_reported(tools, fake_appopener):
    assert tools.open_app("missing").startswith("Failed to open missing")


def test_close_app_message(tools, fake_appopener):
    assert tools.close_app("brave") == "Successfully closed brave."
    assert tools.close_app("missing").startswith("Failed to close missing")


def test_open_directory(tools, tmp_path, no_startfile):
    assert tools.open_directory(str(tmp_path)).startswith("Successfully")
    assert no_startfile == [str(tmp_path)]


def test_open_directory_refuses_files(tools, tmp_path, no_startfile):
    program = tmp_path / "program.bat"
    program.write_text("echo hi")

    tools.open_directory(str(program))

    assert no_startfile == []


def test_rename_files_to_episodes_reports_errors(tools, tmp_path, no_startfile):
    assert tools.rename_files_to_episodes(str(tmp_path / "missing")).startswith("Failed")


def test_note_down_in_txt_uses_configured_folder(tools, tmp_path, monkeypatch, no_startfile):
    notes = tmp_path / "notes"  # does not exist yet
    monkeypatch.setattr(app_file_tools, "settings", Settings(notes_dir=str(notes)))

    assert tools.note_down_in_txt("hello").startswith("Successfully")
    assert (notes / "File_1.txt").read_text() == "hello"
    assert no_startfile == [str(notes)]



def test_declined_close_app_does_nothing(tools, fake_appopener, confirm_answer):
    confirm_answer.approve = False

    assert tools.close_app("brave").startswith("Cancelled")
    assert fake_appopener == []


def test_rename_shows_plan_and_can_be_declined(tools, tmp_path, no_startfile, confirm_answer):
    (tmp_path / "Ep 2.mkv").write_text("")
    (tmp_path / "Ep 10.mkv").write_text("")
    confirm_answer.approve = False

    assert tools.rename_files_to_episodes(str(tmp_path)).startswith("Cancelled")
    assert "Ep 2.mkv  ->  E01.mkv" in confirm_answer.asked[0][1]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Ep 10.mkv", "Ep 2.mkv"]


def test_rename_approved(tools, tmp_path, no_startfile):
    (tmp_path / "x.mkv").write_text("")

    assert tools.rename_files_to_episodes(str(tmp_path)).startswith("Successfully")
    assert [p.name for p in tmp_path.iterdir()] == ["E01.mkv"]
    assert no_startfile == [str(tmp_path)]
