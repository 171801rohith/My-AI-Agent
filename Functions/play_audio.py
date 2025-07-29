import asyncio
from rich.panel import Panel
from rich.console import Console
import pygame

from Functions.text_to_speech import text_to_speech

pygame.mixer.init()
audio_path = "output_audios/audio_out.mp3"


async def play_audio_and_print_response(response_text: str, console: Console):
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
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()
    await asyncio.sleep(0.2)
