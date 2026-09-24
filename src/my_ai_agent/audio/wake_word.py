import numpy as np
import pyaudio
from openwakeword.model import Model
from openwakeword.utils import download_models

from my_ai_agent.settings import settings

# Built-in openWakeWord model; runs fully offline, no API key.
WAKE_WORD = settings.wake_word
THRESHOLD = settings.wake_threshold  # detection score 0..1; raise to reduce false triggers

SAMPLE_RATE = 16000  # openWakeWord expects 16 kHz, 16-bit, mono audio
FRAME_SIZE = 1280  # 80 ms, the frame length the models are trained on


def load_model() -> Model:
    # Fetches the model files on first run only; existing files are skipped.
    download_models(model_names=[WAKE_WORD])
    # ONNX runtime is used because tflite-runtime is not available on Windows.
    return Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")


def wake_sanctuary() -> bool:
    """Block until the wake word is heard. Returns False if interrupted with Ctrl+C."""
    model = load_model()
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAME_SIZE,
    )

    try:
        while True:
            frame = np.frombuffer(
                stream.read(FRAME_SIZE, exception_on_overflow=False), dtype=np.int16
            )
            scores = model.predict(frame)
            if max(scores.values()) >= THRESHOLD:
                return True
    except KeyboardInterrupt:
        return False
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
