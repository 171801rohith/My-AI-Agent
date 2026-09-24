import asyncio
from unittest.mock import MagicMock

import pytest

from my_ai_agent.audio import play_audio


def test_mixer_starts_on_first_playback_only(monkeypatch):
    mixer = MagicMock()
    mixer.get_init.side_effect = [None, (44100, -16, 2)]  # not started, then started
    mixer.music.get_busy.return_value = False
    monkeypatch.setattr(play_audio.pygame, "mixer", mixer)

    asyncio.run(play_audio.play_intro_outro("intro.wav"))
    asyncio.run(play_audio.play_intro_outro("outro.wav"))

    mixer.init.assert_called_once()
    assert mixer.music.load.call_count == 2


class FakeChannel:
    def __init__(self, log, text):
        self.log, self.text, self.polls = log, text, 0

    def get_busy(self):
        self.polls += 1
        busy = self.polls < 3  # "plays" for a couple of polls
        if not busy and ("done", self.text) not in self.log:
            self.log.append(("done", self.text))
        return busy


@pytest.fixture
def fake_audio(monkeypatch):
    log = []

    class FakeSound:
        def __init__(self, text):
            self.text = text

        def play(self):
            log.append(("play", self.text))
            return FakeChannel(log, self.text)

    async def fake_synthesize(text):
        log.append(("synth", text))
        return FakeSound(text)

    monkeypatch.setattr(play_audio, "synthesize", fake_synthesize)
    monkeypatch.setattr(play_audio, "_ensure_mixer", lambda: None)
    monkeypatch.setattr(play_audio.asyncio, "sleep", _instant_sleep)
    return log


_real_sleep = asyncio.sleep


async def _instant_sleep(seconds):
    await _real_sleep(0)


def spoken(log):
    return [text for kind, text in log if kind == "play"]


def test_sentences_are_spoken_in_order_as_they_stream(fake_audio):
    async def stream():
        speaker = play_audio.SentenceSpeaker()
        for delta in ["Hello, I am **Sanctuary**. ", "Pi is 3.14", " and it never ends! Short.", " Bye"]:
            speaker.feed(delta)
        await speaker.finish()

    asyncio.run(stream())

    assert spoken(fake_audio) == [
        "Hello, I am Sanctuary.",
        "Pi is 3.14 and it never ends!",
        "Short. Bye",  # fragments under 20 characters wait for more text
    ]


def test_next_sentence_is_synthesized_before_previous_finishes(fake_audio):
    async def stream():
        speaker = play_audio.SentenceSpeaker()
        speaker.feed("This is the first sentence. And this is the second one. ")
        await speaker.finish()

    asyncio.run(stream())

    order = [(kind, text[:5]) for kind, text in fake_audio]
    assert order.index(("synth", "And t")) < order.index(("done", "This "))


def test_clean_for_speech_strips_markdown():
    assert play_audio.clean_for_speech("## Title\n**bold** and `code`") == "Title bold and code"
