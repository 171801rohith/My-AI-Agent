import pytest

from Tools import app_file_tools
from Tools.app_file_tools import AppAndFileTools


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


@pytest.mark.xfail(reason="close_app reports 'Successfully opened' instead of 'closed'")
def test_close_app_message(tools, fake_appopener):
    assert "closed" in tools.close_app("brave")


def test_open_directory(tools, tmp_path, no_startfile):
    assert tools.open_directory(str(tmp_path)).startswith("Successfully")
    assert no_startfile == [str(tmp_path)]


@pytest.mark.xfail(reason="open_directory passes any path to os.startfile, including executables")
def test_open_directory_refuses_files(tools, tmp_path, no_startfile):
    program = tmp_path / "program.bat"
    program.write_text("echo hi")

    tools.open_directory(str(program))

    assert no_startfile == []


def test_rename_files_to_episodes_reports_errors(tools, tmp_path, no_startfile):
    assert tools.rename_files_to_episodes(str(tmp_path / "missing")).startswith("Failed")


def test_note_down_in_txt(tools, monkeypatch, no_startfile):
    written = []
    monkeypatch.setattr(app_file_tools, "write_txt_file", lambda c, p: written.append((c, p)))

    assert tools.note_down_in_txt("hello").startswith("Successfully")
    assert written == [("hello", "R:/MOVIES/Created By Sanctuary")]
