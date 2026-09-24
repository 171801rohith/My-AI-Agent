import asyncio

import pytest
from rich.console import Console

from my_ai_agent import cli as main


@pytest.mark.parametrize(
    "argv, mode, model, wake",
    [
        ([], "text", "gemini", False),
        (["--mode", "voice"], "voice", "gemini", True),
        (["--mode", "voice", "--no-wake"], "voice", "gemini", False),
        (["--wake", "--model", "ollama"], "text", "ollama", True),
    ],
)
def test_parse_args(argv, mode, model, wake):
    args = main.parse_args(argv)
    assert (args.mode, args.model, args.wake) == (mode, model, wake)


@pytest.fixture
def app(monkeypatch, stub_modules):
    """Run main() with the agent, wake word, audio and chat loop replaced by fakes."""
    events = []

    async def play(path):
        events.append(("play", path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]))

    stub_modules(
        **{
            "my_ai_agent.audio.play_audio": {"play_intro_outro": play},
            "my_ai_agent.audio.wake_word": {"wake_sanctuary": lambda: events.append("wake") or True},
        }
    )
    class FakeResponder:
        def resume_history(self):
            events.append("resume")
            return 0

    def load_responder(model):
        events.append(("model", model))
        return FakeResponder()

    monkeypatch.setattr(main, "load_responder", load_responder)

    async def fake_run(self):
        events.append(("chat", type(self.source).__name__, type(self.sink).__name__))

    monkeypatch.setattr(main.ChatSession, "run", fake_run)
    monkeypatch.setattr(main.VoiceInput, "prepare", lambda self: events.append("stt-loaded"))
    return events


def start(argv):
    asyncio.run(main.main(main.parse_args(argv), Console(quiet=True)))


def test_text_mode_skips_wake_word(app):
    start([])

    assert app == [
        ("model", "gemini"),
        "resume",
        ("play", "intro.wav"),
        ("chat", "TextInput", "ConsoleOutput"),
        ("play", "outro.wav"),
    ]


def test_voice_mode_loads_speech_then_waits_for_wake_word(app):
    start(["--mode", "voice", "--model", "ollama"])

    assert app == [
        ("model", "ollama"),
        "resume",
        "stt-loaded",
        "wake",
        ("play", "intro.wav"),
        ("chat", "VoiceInput", "VoiceOutput"),
        ("play", "outro.wav"),
    ]


def test_fresh_skips_resuming_history(app):
    start(["--fresh"])

    assert "resume" not in app
