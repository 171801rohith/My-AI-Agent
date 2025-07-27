import pvleopard
import sounddevice as sd
from dotenv import load_dotenv
import os
from scipy.io.wavfile import write
import keyboard
from rich.console import Console
import numpy as np

load_dotenv()
base_dir = os.path.dirname(__file__)
audio_path = os.path.join(base_dir, "..", "input_audios", "audio_in.wav")


def speech_to_text() -> str:
    leopard = pvleopard.create(access_key=os.getenv("PICOVOICE_API_KEY"))
    transcript, words = leopard.process_file(audio_path)
    return transcript


def record_audio(console: Console) -> bool:
    fs = 44100
    recording = []

    def callback(indata, frames, time, status):
        recording.append(indata.copy())

    while not keyboard.is_pressed("space"):
        pass

    console.print(f"[bold blue]Recording...[/bold blue]")

    with sd.InputStream(samplerate=fs, channels=2, callback=callback):
        while keyboard.is_pressed("space"):
            sd.sleep(100)

    console.print(f"[bold green]Done Recording[/bold green]")

    if recording:
        sound_out = np.concatenate(recording, axis=0)
        write(audio_path, fs, sound_out)
        return True
    else:
        return False
