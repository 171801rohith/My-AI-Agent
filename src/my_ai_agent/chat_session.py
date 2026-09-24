"""The conversation loop shared by text and voice chat. Where messages come from
(keyboard or microphone) and how replies go out (screen or speech) are pluggable."""

import logging
import re
from typing import Awaitable, Callable, Protocol

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

logger = logging.getLogger(__name__)

EXIT_PHRASE = re.compile(r"\b(exit|quit)\W+chat\b")
EXIT_WORDS = {"exit", "quit"}


def check_for_termination(message: str) -> bool:
    """True for "exit chat" / "quit chat" anywhere in the message, or a bare
    "exit" / "quit", ignoring case and punctuation (STT returns e.g. "Exit chat.")."""
    text = message.lower()
    bare = re.sub(r"[^\w\s]", "", text).strip()
    return bare in EXIT_WORDS or EXIT_PHRASE.search(text) is not None


def panel(text: str, title: str, color: str) -> Panel:
    return Panel(text, title=f"[{color}]{title}", border_style=color, expand=True, title_align="left")


class MessageSource(Protocol):
    hint: str

    def prepare(self) -> None: ...
    async def read(self) -> str | None: ...


class ReplySink(Protocol):
    def on_text(self, delta: str) -> None: ...  # streamed reply text, as it arrives
    async def show(self, text: str) -> None: ...  # the complete reply
    async def abort(self) -> None: ...  # the reply failed part-way


class TextInput:
    hint = "[italic grey]Type 'exit' or 'quit' to end the chat.[/italic grey]"

    def __init__(self, console: Console):
        self.console = console

    def prepare(self) -> None:
        pass

    async def read(self) -> str | None:
        return Prompt.ask("[bold cyan]You", console=self.console)


class VoiceInput:
    hint = (
        "[bold white]Press and hold 'SPACE' to start recording 🎙️[/bold white]\n"
        "[italic grey]Say 'quit chat' or 'exit chat' to end the chat.[/italic grey]"
    )

    def __init__(self, console: Console):
        self.console = console

    def prepare(self) -> None:
        from my_ai_agent.audio.speech_to_text import load_model

        with self.console.status("Loading speech model (first run downloads it)..."):
            load_model()

    async def read(self) -> str | None:
        from my_ai_agent.audio.speech_to_text import record_audio, speech_to_text

        audio = record_audio(self.console)
        if audio is None:
            return None
        text = speech_to_text(audio)
        if text:
            self.console.print(panel(text, "You", "yellow"))
        return text


class ConsoleOutput:
    def __init__(self, console: Console):
        self.console = console

    def on_text(self, delta: str) -> None:
        pass

    async def show(self, text: str) -> None:
        self.console.print(panel(text, "Assistant", "magenta"))

    async def abort(self) -> None:
        pass


class VoiceOutput:
    """Speaks each sentence as soon as it has streamed in, then shows the full reply."""

    def __init__(self, console: Console):
        self.console = console
        self.speaker = None

    def on_text(self, delta: str) -> None:
        from my_ai_agent.audio.play_audio import SentenceSpeaker

        try:
            if self.speaker is None:
                self.speaker = SentenceSpeaker()
            self.speaker.feed(delta)
        except Exception:
            logger.exception("Could not start streaming speech")  # show() still prints the text

    async def show(self, text: str) -> None:
        from my_ai_agent.audio.play_audio import speak

        speaker, self.speaker = self.speaker, None
        self.console.print(panel(text, "Assistant", "magenta"))
        try:
            if speaker is not None and speaker.spoke_anything:
                await speaker.finish()
            else:  # nothing was streamed: speak the whole reply
                if speaker is not None:
                    await speaker.cancel()
                await speak(text)
        except Exception as e:
            # Speech failed: the reply is already on screen, so nothing is lost.
            logger.exception("Text-to-speech failed")
            self.console.print(f"[bold red]Speech error:[/bold red] {e}")

    async def abort(self) -> None:
        speaker, self.speaker = self.speaker, None
        if speaker is not None:
            await speaker.cancel()


class ChatSession:
    def __init__(
        self,
        respond: Callable[..., Awaitable[str]],  # respond(message, on_text=callback)
        source: MessageSource,
        sink: ReplySink,
        console: Console,
    ):
        self.respond = respond
        self.source = source
        self.sink = sink
        self.console = console

    async def run(self) -> None:
        """Chat until the user says or types an exit command."""
        while True:
            message = await self.source.read()
            if not message or not message.strip():
                continue
            if check_for_termination(message):
                return

            try:
                reply = await self.respond(message, on_text=self.sink.on_text)
            except Exception as e:
                logger.exception("Agent failed to respond")
                await self.sink.abort()
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                continue

            await self.sink.show(str(reply))
