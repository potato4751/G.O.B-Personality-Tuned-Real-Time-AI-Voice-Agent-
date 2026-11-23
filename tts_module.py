import subprocess
import sounddevice as sd
import numpy as np
import time
import threading
import queue
import re


class TTSModule:

    def __init__(self, signals):

        self.signals = signals
        self.voice_model = "models/piper/en_US-lessac-medium.onnx"

        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()

        self.sample_rate = 22050
        self.chunk_bytes = 4096
        self.audio_timeout = 0.20

        # create first Piper instance at startup
        self.proc = self._spawn_piper()

        threading.Thread(target=self._tts_worker, daemon=True).start()
        threading.Thread(target=self._audio_player, daemon=True).start()

    # ------------------------------------------------
    # SPAWN / RESTART PIPER
    # ------------------------------------------------

    def _spawn_piper(self):

        return subprocess.Popen(
            [
                "piper",
                "--model",
                self.voice_model,
                "--output_raw"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )

    def _restart_piper(self):

        try:
            if self.proc:
                self.proc.terminate()
        except:
            pass

        self.proc = self._spawn_piper()

    # ------------------------------------------------
    # TEXT SANITIZER
    # ------------------------------------------------

    def _sanitize_for_tts(self, text):

        if not text:
            return ""

        text = text.lower()
        text = text.encode("ascii", "ignore").decode()

        text = re.sub(r"\*.*?\*", "", text)
        text = re.sub(r"\*\*", "", text)
        text = re.sub(r"#\w+", "", text)
        text = re.sub(r"\(.*?\)", "", text)

        text = re.sub(r"[^\w\s.,!?']", "", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ------------------------------------------------

    def enqueue(self, text):

        if not text or not text.strip():
            return

        clean = self._sanitize_for_tts(text)

        if clean:
            self.text_queue.put(clean)

    def speak(self, text):
        self.enqueue(text)

    # ------------------------------------------------
    # TTS WORKER
    # ------------------------------------------------

    def _tts_worker(self):

        while True:

            text = self.text_queue.get()
            self.signals.AI_speaking = True

            try:

                self.proc.stdin.write((text + "\n").encode())
                self.proc.stdin.flush()

                last_audio_time = time.time()

                while True:

                    chunk = self.proc.stdout.read(self.chunk_bytes)

                    if chunk:

                        audio_np = np.frombuffer(chunk, dtype=np.int16)

                        if len(audio_np) > 0:
                            self.audio_queue.put(audio_np)

                        last_audio_time = time.time()

                    else:
                        time.sleep(0.01)

                    if time.time() - last_audio_time > self.audio_timeout:
                        break

            except Exception as e:
                print("TTS error:", e)

            self.text_queue.task_done()

    # ------------------------------------------------
    # AUDIO PLAYER
    # ------------------------------------------------

    def _audio_player(self):

        stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16"
        )

        stream.start()

        while True:

            audio_np = self.audio_queue.get()

            try:
                stream.write(audio_np)
            except Exception as e:
                print("Audio error:", e)

            self.signals.last_tts_time = time.time()

            if self.audio_queue.empty():

                # playback finished
                self.signals.AI_speaking = False
                self.signals.awaiting_user = True

                # restart Piper here
                self._restart_piper()

            self.audio_queue.task_done()