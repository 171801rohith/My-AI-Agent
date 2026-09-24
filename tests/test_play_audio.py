import asyncio
from unittest.mock import MagicMock

from Functions import play_audio


def test_mixer_starts_on_first_playback_only(monkeypatch):
    mixer = MagicMock()
    mixer.get_init.side_effect = [None, (44100, -16, 2)]  # not started, then started
    mixer.music.get_busy.return_value = False
    monkeypatch.setattr(play_audio.pygame, "mixer", mixer)

    asyncio.run(play_audio.play_intro_outro("intro.wav"))
    asyncio.run(play_audio.play_intro_outro("outro.wav"))

    mixer.init.assert_called_once()
    assert mixer.music.load.call_count == 2
