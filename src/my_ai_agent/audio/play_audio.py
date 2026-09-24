import asyncio
import logging
import re

import pygame

from my_ai_agent.audio.text_to_speech import OUTPUT_PATH, text_to_speech

logger = logging.getLogger(__name__)

# A sentence ends at . ! ? or a newline followed by whitespace, so "3.14" or "e.g.x"
# mid-stream is not split. Short fragments are joined with the next sentence.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")
MIN_SENTENCE_CHARS = 20


def _ensure_mixer():
    """Start the audio mixer on first use, not when the module is imported."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()


def clean_for_speech(text: str) -> str:
    """Drop markdown symbols that TTS would read out loud."""
    text = re.sub(r"`{1,3}|\*{1,2}|#{1,6}\s|_{2}", "", text)
    return re.sub(r"\s+", " ", text).strip()


async def synthesize(text: str) -> pygame.mixer.Sound:
    """Turn one sentence into a Sound held in memory (the WAV file can be reused)."""
    await text_to_speech(text)
    return pygame.mixer.Sound(OUTPUT_PATH)


class SentenceSpeaker:
    """Speaks a reply while it is still being generated.

    feed() receives text as it streams in; each complete sentence is queued and
    spoken in order. The next sentence is synthesized while the current one plays.
    """

    def __init__(self):
        _ensure_mixer()
        self.buffer = ""
        self.spoke_anything = False
        self.queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.task = asyncio.create_task(self._speak_loop())

    def feed(self, delta: str) -> None:
        self.buffer += delta
        while True:
            match = next(
                (m for m in SENTENCE_END.finditer(self.buffer) if m.start() >= MIN_SENTENCE_CHARS),
                None,
            )
            if match is None:
                return
            self._enqueue(self.buffer[: match.start()])
            self.buffer = self.buffer[match.end():]

    def _enqueue(self, text: str) -> None:
        text = clean_for_speech(text)
        if text:
            self.spoke_anything = True
            self.queue.put_nowait(text)

    async def finish(self) -> None:
        """Speak whatever is left and wait until playback has ended."""
        self._enqueue(self.buffer)
        self.buffer = ""
        self.queue.put_nowait(None)
        await self.task

    async def cancel(self) -> None:
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        pygame.mixer.stop()

    async def _speak_loop(self) -> None:
        channel = None
        while (sentence := await self.queue.get()) is not None:
            sound = await synthesize(sentence)  # runs while the previous sentence plays
            while channel is not None and channel.get_busy():
                await asyncio.sleep(0.05)
            channel = sound.play()
        while channel is not None and channel.get_busy():
            await asyncio.sleep(0.05)


async def speak(text: str) -> None:
    """Speak a complete text (used when nothing was streamed)."""
    speaker = SentenceSpeaker()
    speaker.feed(text)
    await speaker.finish()


async def play_intro_outro(path):
    _ensure_mixer()
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()
    await asyncio.sleep(0.2)
