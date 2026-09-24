import asyncio
import os
from rich.panel import Panel
from rich.console import Console
import pygame

from Functions.text_to_speech import text_to_speech

base_dir = os.path.dirname(__file__)
audio_path = os.path.join(base_dir, "..", "output_audios", "audio_out.wav")


def _ensure_mixer():
    """Start the audio mixer on first use, not when the module is imported."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()


async def play_audio_and_print_response(response_text: str, console: Console):
    _ensure_mixer()
    pygame.mixer.music.stop()
    await text_to_speech(response_text)
    pygame.mixer.music.load(audio_path)
    console.print(
        Panel(
            response_text,
            title="[magenta]Assistant",
            border_style="magenta",
            expand=True,
            title_align="left",
        )
    )
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()
    await asyncio.sleep(0.2)


async def play_intro_outro(path):
    _ensure_mixer()
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()
    await asyncio.sleep(0.2)
