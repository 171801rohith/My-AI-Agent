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
        self.deltas = []
        self.aborted = 0

    def on_text(self, delta):
        self.deltas.append(delta)

    async def show(self, text):
        self.replies.append(text)

    async def abort(self):
        self.aborted += 1


def run_session(messages, respond, sink=None):
    sink = sink or RecordingSink()
    session = ChatSession(respond, ScriptedSource(messages), sink, Console(quiet=True))
    asyncio.run(session.run())
    return sink.replies


def test_session_replies_until_exit():
    async def echo(message, on_text=None):
        return f"echo: {message}"

    replies = run_session(["hi", None, "   ", "how are you", "exit chat", "never read"], echo)

    assert replies == ["echo: hi", "echo: how are you"]


def test_agent_error_is_reported_and_chat_continues():
    async def flaky(message, on_text=None):
        if message == "boom":
            on_text("Half a sent")
            raise RuntimeError("model unavailable")
        return "ok"

    sink = RecordingSink()
    assert run_session(["boom", "again", "quit"], flaky, sink) == ["ok"]
    assert sink.aborted == 1


def test_streamed_text_reaches_the_sink():
    async def streaming(message, on_text=None):
        for part in ["Hello ", "there."]:
            on_text(part)
        return "Hello there."

    sink = RecordingSink()
    run_session(["hi", "exit"], streaming, sink)

    assert sink.deltas == ["Hello ", "there."]
    assert sink.replies == ["Hello there."]


def test_voice_output_still_shows_reply_when_speech_fails(monkeypatch):
    import my_ai_agent.audio.play_audio as play_audio

    async def broken(text):
        raise RuntimeError("no audio device")

    monkeypatch.setattr(play_audio, "speak", broken)
    console = Console(record=True, width=80)

    asyncio.run(chat_session.VoiceOutput(console).show("the reply"))

    output = console.export_text()
    assert "the reply" in output and "no audio device" in output


class FakeSpeaker:
    instances = []

    def __init__(self):
        self.fed, self.finished, self.cancelled = [], False, False
        self.spoke_anything = False
        FakeSpeaker.instances.append(self)

    def feed(self, delta):
        self.fed.append(delta)
        self.spoke_anything = True

    async def finish(self):
        self.finished = True

    async def cancel(self):
        self.cancelled = True


def test_voice_output_streams_into_one_speaker_per_reply(monkeypatch):
    import my_ai_agent.audio.play_audio as play_audio

    FakeSpeaker.instances = []
    monkeypatch.setattr(play_audio, "SentenceSpeaker", FakeSpeaker)
    output = chat_session.VoiceOutput(Console(quiet=True))

    async def one_reply():
        output.on_text("First sentence here. ")
        output.on_text("Second one.")
        await output.show("First sentence here. Second one.")

    asyncio.run(one_reply())
    asyncio.run(one_reply())

    assert len(FakeSpeaker.instances) == 2
    assert FakeSpeaker.instances[0].fed == ["First sentence here. ", "Second one."]
    assert FakeSpeaker.instances[0].finished


def test_voice_output_abort_stops_speech(monkeypatch):
    import my_ai_agent.audio.play_audio as play_audio

    FakeSpeaker.instances = []
    monkeypatch.setattr(play_audio, "SentenceSpeaker", FakeSpeaker)
    output = chat_session.VoiceOutput(Console(quiet=True))

    async def failed_reply():
        output.on_text("Let me check")
        await output.abort()

    asyncio.run(failed_reply())

    assert FakeSpeaker.instances[0].cancelled
