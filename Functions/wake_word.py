import pvporcupine
from pvrecorder import PvRecorder
from dotenv import load_dotenv
import os

load_dotenv()
keywords = ["sanctuary"]


def wake_sanctuary() -> bool:
    porcupine = pvporcupine.create(
        access_key=os.getenv("PICOVOICE_API_KEY"),
        keyword_paths=["sanctuary_wake_word/sanctuary_en_windows_v3_0_0.ppn"],
    )
    recoder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)

    try:
        recoder.start()

        while True:
            keyword_index = porcupine.process(recoder.read())
            if keyword_index == 0:
                return True

    except KeyboardInterrupt:
        recoder.stop()
    finally:
        recoder.stop()
        porcupine.delete()
        recoder.delete()
