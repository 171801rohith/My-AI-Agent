import importlib
import sys
import types

import pytest


@pytest.fixture
def no_startfile(monkeypatch):
    """Replace os.startfile so tests never open Explorer or launch files."""
    calls = []
    monkeypatch.setattr("os.startfile", lambda path: calls.append(path), raising=False)
    return calls


@pytest.fixture
def stub_modules(monkeypatch):
    """Install fake modules in sys.modules so entry points can be imported
    without a microphone, speakers, Picovoice keys or a Gemini client."""

    def install(**modules):
        for name, attrs in modules.items():
            module = types.ModuleType(name)
            for key, value in attrs.items():
                setattr(module, key, value)
            monkeypatch.setitem(sys.modules, name, module)

    return install


@pytest.fixture
def fresh_import(monkeypatch):
    """Import a module from scratch, removing any cached copy first."""

    def _import(name):
        monkeypatch.delitem(sys.modules, name, raising=False)
        return importlib.import_module(name)

    return _import


@pytest.fixture(autouse=True)
def confirm_answer(monkeypatch):
    """Auto-approve confirmation prompts so tests never block on input.
    Set `confirm_answer.approve = False` in a test to simulate declining."""
    from my_ai_agent.tools import confirm as confirmation

    class Answer:
        approve = True
        asked = []

    answer = Answer()
    answer.asked = []

    def fake_confirm(title, details):
        answer.asked.append((title, details))
        return answer.approve

    monkeypatch.setattr(confirmation, "confirm", fake_confirm)
    return answer
