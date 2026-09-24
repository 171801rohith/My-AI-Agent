"""Start Sanctuary.

    uv run main.py                     # text chat with Gemini
    uv run main.py --mode voice        # voice chat (wake word, push-to-talk, spoken replies)
    uv run main.py --model ollama      # use the local Ollama model instead of Gemini
    uv run main.py --wake              # text chat, but wait for the wake word first
"""

import argparse
import asyncio
import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from my_ai_agent.chat_session import ChatSession, ConsoleOutput, TextInput, VoiceInput, VoiceOutput
from my_ai_agent.logging_setup import setup_logging

logger = logging.getLogger(__name__)

ASSETS = Path(__file__).resolve().parent / "assets"
INTRO_PATH = str(ASSETS / "intro.wav")
OUTRO_PATH = str(ASSETS / "outro.wav")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sanctuary, your AI agent.")
    parser.add_argument("--mode", choices=["text", "voice"], default="text")
    parser.add_argument("--model", choices=["gemini", "ollama"], default="gemini")
    parser.add_argument(
        "--wake",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="wait for the wake word first (default: on for voice, off for text)",
    )
    args = parser.parse_args(argv)
    if args.wake is None:
        args.wake = args.mode == "voice"
    return args


def load_responder(model: str):
    """Import only the chosen agent, so the other model's client is never built."""
    if model == "ollama":
        from my_ai_agent.agents.ollama import generateResponse
    else:
        from my_ai_agent.agents.gemini import generateResponse
    return generateResponse


async def main(args: argparse.Namespace, console: Console | None = None) -> None:
    from my_ai_agent.audio.play_audio import play_intro_outro
    from my_ai_agent.audio.wake_word import wake_sanctuary

    console = console or Console()
    logger.info("Starting: mode=%s model=%s wake=%s", args.mode, args.model, args.wake)

    with console.status(f"Loading {args.model} agent..."):
        respond = load_responder(args.model)

    if args.mode == "voice":
        source, sink = VoiceInput(console), VoiceOutput(console)
    else:
        source, sink = TextInput(console), ConsoleOutput(console)
    source.prepare()

    if args.wake:
        console.print(
            Panel(
                Text("⚔️  Say 'Hey Jarvis' to wake SANCTUARY!", justify="center", style="italic bright_magenta"),
                title="[bold white] My AI Agent",
                border_style="white",
                expand=True,
            )
        )
        if not wake_sanctuary():
            return
    await play_intro_outro(INTRO_PATH)

    console.print(source.hint)
    await ChatSession(respond, source, sink, console).run()
    await play_intro_outro(OUTRO_PATH)
    logger.info("Chat ended")


def run(argv: list[str] | None = None) -> None:
    setup_logging()
    try:
        asyncio.run(main(parse_args(argv)))
    except (KeyboardInterrupt, EOFError):
        pass  # Ctrl+C / Ctrl+Z ends the chat quietly


if __name__ == "__main__":
    run()
