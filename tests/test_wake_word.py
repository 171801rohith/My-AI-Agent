import numpy as np
import pytest

from my_ai_agent.audio import wake_word


class FakeStream:
    def __init__(self, reads):
        self.reads = list(reads)
        self.closed = False

    def read(self, frames, exception_on_overflow=True):
        item = self.reads.pop(0)
        if isinstance(item, BaseException):
            raise item
        return np.zeros(frames, dtype=np.int16).tobytes()

    def stop_stream(self):
        pass

    def close(self):
        self.closed = True


class FakePyAudio:
    def __init__(self, stream):
        self.stream = stream
        self.open_kwargs = None
        self.terminated = False

    def open(self, **kwargs):
        self.open_kwargs = kwargs
        return self.stream

    def terminate(self):
        self.terminated = True


class FakeModel:
    def __init__(self, scores):
        self.scores = list(scores)

    def predict(self, frame):
        assert frame.dtype == np.int16 and len(frame) == wake_word.FRAME_SIZE
        return {"hey_jarvis": self.scores.pop(0)}


@pytest.fixture
def mic(monkeypatch):
    """Fake microphone and model. Configure with mic(scores, reads=None)."""

    def setup(scores, reads=None):
        stream = FakeStream(reads if reads is not None else [None] * len(scores))
        audio = FakePyAudio(stream)
        monkeypatch.setattr(wake_word.pyaudio, "PyAudio", lambda: audio)
        monkeypatch.setattr(wake_word, "load_model", lambda: FakeModel(scores))
        return audio

    return setup


def test_returns_true_when_score_crosses_threshold(mic):
    audio = mic([0.01, 0.2, 0.9])

    assert wake_word.wake_sanctuary() is True
    assert audio.open_kwargs["rate"] == 16000
    assert audio.open_kwargs["channels"] == 1
    assert audio.stream.closed and audio.terminated


def test_keeps_listening_below_threshold(mic):
    audio = mic([0.1, 0.49, 0.5])

    assert wake_word.wake_sanctuary() is True
    assert audio.stream.reads == []  # all three frames were needed


def test_ctrl_c_returns_false_and_releases_microphone(mic):
    audio = mic([0.1], reads=[None, KeyboardInterrupt()])

    assert wake_word.wake_sanctuary() is False
    assert audio.stream.closed and audio.terminated

