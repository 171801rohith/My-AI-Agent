from types import SimpleNamespace

import numpy as np
import pytest
from rich.console import Console

from my_ai_agent.audio import speech_to_text as stt


class FakeWhisper:
    created = 0

    def __init__(self, *args, **kwargs):
        FakeWhisper.created += 1
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append(kwargs)
        return iter([SimpleNamespace(text=" Exit"), SimpleNamespace(text=" chat. ")]), None


@pytest.fixture
def whisper(monkeypatch):
    FakeWhisper.created = 0
    monkeypatch.setattr(stt, "WhisperModel", FakeWhisper)
    monkeypatch.setattr(stt, "_model", None)
    return FakeWhisper


def test_transcript_segments_are_joined(whisper):
    assert stt.speech_to_text(np.zeros(16000, dtype=np.float32)) == "Exit chat."


def test_model_is_loaded_once(whisper):
    stt.speech_to_text(np.zeros(10, dtype=np.float32))
    stt.speech_to_text(np.zeros(10, dtype=np.float32))

    assert whisper.created == 1


def test_english_model_skips_language_detection(whisper):
    stt.speech_to_text(np.zeros(10, dtype=np.float32))

    assert stt._model.calls[0]["language"] == "en"


@pytest.fixture
def mic(monkeypatch):
    """Fake keyboard and microphone: SPACE stays held while blocks remain, and
    each poll delivers one block of audio to the stream callback."""

    def setup(blocks):
        state = {"polls": 0}
        waited = []

        class FakeStream:
            def __init__(self, samplerate, channels, dtype, callback):
                state["callback"] = callback
                state["args"] = (samplerate, channels, dtype)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def is_pressed(key):
            if state["polls"] < len(blocks):
                state["callback"](blocks[state["polls"]], len(blocks[state["polls"]]), None, None)
                state["polls"] += 1
                return True
            return False

        monkeypatch.setattr(stt.keyboard, "wait", waited.append)
        monkeypatch.setattr(stt.keyboard, "is_pressed", is_pressed)
        monkeypatch.setattr(stt.sd, "InputStream", FakeStream)
        monkeypatch.setattr(stt.sd, "sleep", lambda ms: None)
        return state, waited

    return setup


def test_record_audio_returns_mono_16k_audio_in_memory(mic):
    block = np.ones((800, 1), dtype=np.float32)
    state, waited = mic([block, block])

    audio = stt.record_audio(Console(quiet=True))

    assert waited == ["space"]
    assert state["args"] == (16000, 1, "float32")
    assert audio.shape == (1600,)


def test_record_audio_with_no_audio_returns_none(mic):
    mic([])

    assert stt.record_audio(Console(quiet=True)) is None
