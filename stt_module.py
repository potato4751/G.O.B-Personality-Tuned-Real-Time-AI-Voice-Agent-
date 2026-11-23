import threading
import time
from RealtimeSTT import AudioToTextRecorder

from constants import (
    STT_MODEL,
    STT_BEAM_SIZE,
    STT_DEVICE,
    STT_COMPUTE_TYPE
)


# ================================
# STT CONFIG
# ================================

STT_BIAS_WORDS = [
    "Pranav",
    "Anae",
    "Goober",
    "Goober Sama"
]


def build_bias_prompt():

    if not STT_BIAS_WORDS:
        return None

    return "The following words may appear in speech: " + ", ".join(STT_BIAS_WORDS)


class STTModule:

    def __init__(self, signals, prompter, mic_device, system_device):

        self.signals = signals
        self.prompter = prompter

        # cooldown for STT after speaking
        self.cooldown = 1.5

        # echo suppression window
        self.echo_window = 2.0

        bias_prompt = build_bias_prompt()

        # ===============================
        # MICROPHONE STT RECORDER
        # ===============================

        self.mic = AudioToTextRecorder(
            input_device_index=mic_device,
            model=STT_MODEL,
            language="en",
            beam_size=STT_BEAM_SIZE,
            device=STT_DEVICE,
            compute_type=STT_COMPUTE_TYPE,
            initial_prompt=bias_prompt
        )

        # ===============================
        # SYSTEM AUDIO STT RECORDER
        # ===============================

        self.system = AudioToTextRecorder(
            input_device_index=system_device,
            model=STT_MODEL,
            language="en",
            beam_size=STT_BEAM_SIZE,
            device=STT_DEVICE,
            compute_type=STT_COMPUTE_TYPE
        )

        # Start STT threads
        threading.Thread(target=self.loop_mic, daemon=True).start()
        threading.Thread(target=self.loop_system, daemon=True).start()

    # ===============================
    # LISTEN PERMISSION LOGIC
    # ===============================

    def allowed_to_listen(self):

        # block while LLM is generating
        if self.signals.AI_thinking:
            return False

        # block while AI is speaking
        if self.signals.AI_speaking:
            return False

        # echo suppression
        if time.time() - self.signals.last_tts_time < self.echo_window:
            return False

        return True

    # ===============================
    # MIC CALLBACK
    # ===============================

    def mic_callback(self, text):

        if not text:
            return

        # user speech unlocks system audio
        self.signals.awaiting_user = False

        if not self.allowed_to_listen():
            return

        print("Pranav:", text)

        self.signals.history.append({
            "role": "user",
            "content": f"Pranav: {text}"
        })

        self.signals.new_message = True

        self.prompter.notify_speech()

    # ===============================
    # SYSTEM AUDIO CALLBACK
    # ===============================

    def sys_callback(self, text):

        if not text:
            return

        # ignore system audio until user speaks again
        if self.signals.awaiting_user:
            return

        if not self.allowed_to_listen():
            return

        print("other:", text)

        self.signals.history.append({
            "role": "user",
            "content": f"other: {text}"
        })

        self.signals.new_message = True

        self.prompter.notify_speech()

    # ===============================
    # MIC LOOP
    # ===============================

    def loop_mic(self):

        while True:

            self.mic.text(self.mic_callback)

            time.sleep(0.05)

    # ===============================
    # SYSTEM AUDIO LOOP
    # ===============================

    def loop_system(self):

        while True:

            self.system.text(self.sys_callback)

            time.sleep(0.05)