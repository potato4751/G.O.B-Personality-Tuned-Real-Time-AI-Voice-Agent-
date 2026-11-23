
import os
import logging

os.environ["ANONYMIZED_TELEMETRY"] = "False"

logging.getLogger("chromadb").setLevel(logging.ERROR)
logging.getLogger("RealtimeSTT").setLevel(logging.ERROR)
logging.getLogger("posthog").setLevel(logging.ERROR)

import time
import threading

from signals import Signals
from model_manager import ModelManager
from prompter import Prompter
from stt_module import STTModule
from tts_module import TTSModule
from modules.memory import Memory
from constants import *


def main():

    signals = Signals()

    # Load model
    model_manager = ModelManager()
    model_manager.load_base_model()

    # expose model to modules (memory reflection uses it)
    signals.model_manager = model_manager

    # TTS
    tts = TTSModule(signals)

    # Modules
    memory_module = Memory(signals)

    modules = [
        memory_module
    ]

    # Start module async loops
    for m in modules:
        threading.Thread(target=m.init_event_loop, daemon=True).start()

    # Prompter
    prompter = Prompter(signals, model_manager, tts, modules)

    prompter_thread = threading.Thread(
        target=prompter.loop,
        daemon=True
    )
    prompter_thread.start()

    # STT
    stt = STTModule(
        signals,
        prompter,
        MIC_DEVICE_INDEX,
        SYSTEM_DEVICE_INDEX
    )

    print("SYSTEM READY")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()