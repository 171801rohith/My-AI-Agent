import asyncio

import pytest
from rich.console import Console

from my_ai_agent import chat_session
from my_ai_agent.chat_session import ChatSession, check_for_termination


@pytest.mark.parametrize(
    "message",
    ["exit chat", "quit chat", "please quit chat now", "Exit chat.", "Quit, chat!", "OK. Exit chat",
     "exit", "Quit.", "  EXIT  "],
)
def test_termination(message):
    assert check_for_termination(message)


@pytest.mark.parametrize(
    "message", ["chat", "open chat", "chat exit", "exit chatroom", "how do I exit vim", "quite"]
)
def test_not_termination(message):
    assert not check_for_termination(message)


class ScriptedSource:
    hint = ""

    def __init__(self, messages):
        self.messages = list(messages)

    def prepare(self):
        pass

    async def read(self):
        return self.messages.pop(0)


class RecordingSink:
    def __init__(self):
        self.replies = []

    async def show(self, text):
        self.replies.append(text)


def run_session(messages, respond):
    sink = RecordingSink()
    session = ChatSession(respond, ScriptedSource(messages), sink, Console(quiet=True))
    asyncio.run(session.run())
    return sink.replies


def test_session_replies_until_exit():
    async def echo(message):
        return f"echo: {message}"

    replies = run_session(["hi", None, "   ", "how are you", "exit chat", "never read"], echo)

    assert replies == ["echo: hi", "echo: how are you"]


def test_agent_error_is_reported_and_chat_continues():
    async def flaky(message):
        if message == "boom":
            raise RuntimeError("model unavailable")
        return "ok"

    assert run_session(["boom", "again", "quit"], flaky) == ["ok"]


def test_voice_output_still_shows_reply_when_speech_fails(monkeypatch):
    import my_ai_agent.audio.play_audio as play_audio

    async def broken(response_text, console):
        raise RuntimeError("no audio device")

    monkeypatch.setattr(play_audio, "play_audio_and_print_response", broken)
    console = Console(record=True, width=80)

    asyncio.run(chat_session.VoiceOutput(console).show("the reply"))

    output = console.export_text()
    assert "the reply" in output and "no audio device" in output
