import edge_tts
import os


async def text_to_speech(text: str) -> bool:
    try:
        base_dir = os.path.dirname(__file__)
        output_path = os.path.join(base_dir, "..", "output_audios", "audio_out.mp3")
        if os.path.exists(output_path):
            os.remove(output_path)
        communicate = edge_tts.Communicate(
            text, "en-US-ChristopherNeural", rate="+20%", pitch="-20Hz"
        )

        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
