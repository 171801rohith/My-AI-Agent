import os
import tempfile

import pyttsx3
from pydub import AudioSegment

# Generated speech is scratch data, so it lives in the system temp folder.
AUDIO_DIR = os.path.join(tempfile.gettempdir(), "sanctuary")
OUTPUT_PATH = os.path.join(AUDIO_DIR, "audio_out.wav")
TEMP_PATH = os.path.join(AUDIO_DIR, "temp.wav")


async def text_to_speech(text: str) -> bool:
    # Errors propagate so the caller can report them instead of playing stale audio.
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if os.path.exists(OUTPUT_PATH):
        os.remove(OUTPUT_PATH)
    if os.path.exists(TEMP_PATH):
        os.remove(TEMP_PATH)

    engine = pyttsx3.init()
    engine.setProperty("rate", 225)
    engine.setProperty("volume", 1.0)

    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[0].id)

    engine.save_to_file(text, TEMP_PATH)
    engine.runAndWait()

    sound = AudioSegment.from_file(TEMP_PATH)

    # Play back at 90% of the frame rate for a slower, deeper voice.
    final_audio = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * 0.90)}
    ).set_frame_rate(sound.frame_rate)

    final_audio.export(OUTPUT_PATH, format="wav")
    return True
