import os
import re
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

# from Agents.agent_ollama import generateResponse
from Agents.agent_gemini import generateResponse
from Functions.wake_word import wake_sanctuary
from Functions.play_audio import play_audio_and_print_response, play_intro_outro
from Functions.speech_to_text import load_model as load_speech_model, speech_to_text, record_audio

console = Console()

output_dir = "output_audios"
input_dir = "input_audios"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(input_dir, exist_ok=True)
intro_path = "output_audios/intro.wav"
outro_path = "output_audios/outro.wav"


def check_for_termination(prompt: str) -> bool:
    """True if the transcript contains "exit chat" or "quit chat", ignoring case
    and punctuation (speech-to-text returns e.g. "Exit chat.")."""
    return re.search(r"\b(exit|quit)\W+chat\b", prompt.lower()) is not None


async def main_loop():
    console.print(
        Panel(
            Text(
                "⚔️  Say 'Hey Jarvis' to wake SANCTUARY!",
                justify="center",
                style="italic bright_magenta",
            ),
            title="[bold white] My AI Agent",
            border_style="white",
            expand=True,
        )
    )
    with console.status("Loading speech model (first run downloads it)..."):
        load_speech_model()
    if wake_sanctuary():
        await play_intro_outro(intro_path)
        console.print(
            f"[bold white]Press and hold 'SPACE' to start recording 🎙️[/bold white]"
        )
        console.print(
            f"[italic grey]Say 'quit chat' or 'exit chat' to Terminate Sanctuary [/italic grey]"
        )
        while True:
            audio = record_audio(console)
            if audio is None:
                continue
            prompt = speech_to_text(audio)
            if not prompt:  # silence or noise only
                continue

            if check_for_termination(prompt):
                await play_intro_outro(outro_path)
                break

            try:
                response = await generateResponse(prompt)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                continue

            response_text = str(response)

            console.print(
                Panel(
                    prompt,
                    title="[yellow]You",
                    border_style="yellow",
                    expand=True,
                    title_align="left",
                )
            )
            try:
                await play_audio_and_print_response(
                    response_text=response_text, console=console
                )
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                continue


if __name__ == "__main__":
    asyncio.run(main_loop())
