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
    async def show(self, text: str) -> None: ...


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

    async def show(self, text: str) -> None:
        self.console.print(panel(text, "Assistant", "magenta"))


class VoiceOutput:
    def __init__(self, console: Console):
        self.console = console

    async def show(self, text: str) -> None:
        from my_ai_agent.audio.play_audio import play_audio_and_print_response

        try:
            await play_audio_and_print_response(response_text=text, console=self.console)
        except Exception as e:
            # Speech failed: still show the reply rather than losing it.
            logger.exception("Text-to-speech failed")
            self.console.print(panel(text, "Assistant", "magenta"))
            self.console.print(f"[bold red]Speech error:[/bold red] {e}")


class ChatSession:
    def __init__(
        self,
        respond: Callable[[str], Awaitable[str]],
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
                reply = await self.respond(message)
            except Exception as e:
                logger.exception("Agent failed to respond")
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                continue

            await self.sink.show(str(reply))
