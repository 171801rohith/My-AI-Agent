import edge_tts
import os


# async def text_to_speech(text: str) -> bool:
#     try:
#         base_dir = os.path.dirname(__file__)
#         output_path = os.path.join(base_dir, "..", "output_audios", "audio_out.mp3")
#         if os.path.exists(output_path):
#             os.remove(output_path)
#         communicate = edge_tts.Communicate(
#             text, "en-US-ChristopherNeural", rate="+20%", pitch="-20Hz"
#         )

#         await communicate.save(output_path)
#         return True
#     except Exception as e:
#         print(f"Error: {e}")

import pyttsx3
from pydub import AudioSegment


async def text_to_speech(text: str) -> bool:
    base_dir = os.path.dirname(__file__)
    output_path = os.path.join(base_dir, "..", "output_audios", "audio_out.wav")
    output_path_temp = os.path.join(base_dir, "..", "output_audios", "temp.wav")

    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(output_path_temp):
            os.remove(output_path_temp)

        engine = pyttsx3.init()
        engine.setProperty("rate", 225)
        engine.setProperty("volume", 1.0)

        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[0].id)

        engine.save_to_file(
            text,
            output_path_temp,
        )
        engine.runAndWait()

        sound = AudioSegment.from_file(output_path_temp)

        final_audio = sound._spawn(
            sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * 0.90)}
        ).set_frame_rate(sound.frame_rate)

        final_audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"Error: {e}")
