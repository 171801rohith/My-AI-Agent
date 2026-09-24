import keyboard
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from rich.console import Console

from my_ai_agent.settings import settings

SAMPLE_RATE = 16000  # Whisper works on 16 kHz mono audio

_model: WhisperModel | None = None


def load_model() -> WhisperModel:
    """Load the Whisper model once and reuse it. The first call downloads it."""
    global _model
    if _model is None:
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    return _model


def speech_to_text(audio: np.ndarray) -> str:
    """Transcribe a mono float32 recording, fully offline."""
    # English-only models (*.en) skip language detection; others detect it.
    language = "en" if settings.whisper_model.endswith(".en") else None
    segments, _ = load_model().transcribe(
        audio, language=language, beam_size=1, vad_filter=True
    )
    return " ".join(segment.text.strip() for segment in segments).strip()


def record_audio(console: Console) -> np.ndarray | None:
    """Record while SPACE is held. Returns the audio in memory, or None if empty."""
    recording = []

    def callback(indata, frames, time, status):
        recording.append(indata.copy())

    keyboard.wait("space")  # blocks on a key event instead of spinning the CPU

    console.print(f"[bold blue]Recording...[/bold blue]")

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=callback
    ):
        while keyboard.is_pressed("space"):
            sd.sleep(50)

    console.print(f"[bold green]Done Recording[/bold green]")

    if not recording:
        return None
    return np.concatenate(recording, axis=0).flatten()
