import subprocess
import sounddevice as sd
import numpy as np
import time
import threading
import queue
import re
import os

from constants import *


class TTS:

    def __init__(self):

        self.voice_model = PIPER_MODEL

        # bounded queue for robustness
        self.text_queue = queue.Queue(maxsize=20)
        self.audio_queue = queue.Queue()

        self.sample_rate = 22050
        self.chunk_bytes = 4096
        self.audio_timeout = 0.20

        self.proc = self._spawn_piper()

        threading.Thread(target=self._tts_worker, daemon=True).start()
        threading.Thread(target=self._audio_player, daemon=True).start()

    # ------------------------------------------------
    # SPAWN / RESTART PIPER
    # ------------------------------------------------

    def _spawn_piper(self):

        piper_path = os.path.join("models", "piper", "piper.exe")

        return subprocess.Popen(
            [
                piper_path,
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

    def _sanitize(self, text):

        if not text:
            return ""

        text = text.lower()

        emoji_map = {
            "😝": " tongue face ",
            "😂": " joy ",
            "🤣": " raw fill ",
            "😅": " nervous laugh ",
            "😊": " smile ",
            "😎": " cool ",
            "😡": " angry ",
            "❤️": " heart ",
            "👍": " thumbs up ",
            "🤔": " thonk ",
            "🙏": " pray ",
        }

        for emoji, word in emoji_map.items():
            text = text.replace(emoji, word)

        text = re.sub(r"<:([a-zA-Z0-9_]+):\d+>", r"\1", text)

        text = text.encode("ascii", "ignore").decode()

        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ------------------------------------------------
    # SAFE ENQUEUE
    # ------------------------------------------------

    def enqueue(self, text):

        clean = self._sanitize(text)

        if not clean:
            return

        try:
            self.text_queue.put_nowait(clean)

        except queue.Full:

            # drop oldest message
            try:
                self.text_queue.get_nowait()
            except queue.Empty:
                pass

            self.text_queue.put_nowait(clean)

    # ------------------------------------------------
    # TTS WORKER
    # ------------------------------------------------

    def _tts_worker(self):

        while True:

            text = self.text_queue.get()

            print("Speaking:", text)

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
            channels=2,
            dtype="int16",
            device=TTS_OUTPUT_DEVICE
        )

        stream.start()

        while True:

            audio_np = self.audio_queue.get()

            try:
                stereo = np.column_stack((audio_np, audio_np))
                stream.write(stereo)
            except Exception as e:
                print("Audio error:", e)

            # restart Piper after utterance
            if self.audio_queue.empty():
                self._restart_piper()

            self.audio_queue.task_done()