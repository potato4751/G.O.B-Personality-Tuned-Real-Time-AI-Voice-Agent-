import queue
import time


class Signals:

    def __init__(self):
        self.awaiting_user = False

        self._human_speaking = False
        self._AI_speaking = False
        self._AI_thinking = False

        self._last_message_time = 0.0
        self._new_message = False

        self._stt_ready = False
        self._tts_ready = False

        self._history = []

        self._terminate = False

        # NEW: timestamp of last TTS playback
        self._last_tts_time = 0.0

        self.sio_queue = queue.SimpleQueue()

    @property
    def human_speaking(self):
        return self._human_speaking

    @human_speaking.setter
    def human_speaking(self, v):
        self._human_speaking = v

    @property
    def AI_speaking(self):
        return self._AI_speaking

    @AI_speaking.setter
    def AI_speaking(self, v):
        self._AI_speaking = v

    @property
    def AI_thinking(self):
        return self._AI_thinking

    @AI_thinking.setter
    def AI_thinking(self, v):
        self._AI_thinking = v

    @property
    def last_message_time(self):
        return self._last_message_time

    @last_message_time.setter
    def last_message_time(self, v):
        self._last_message_time = v

    @property
    def new_message(self):
        return self._new_message

    @new_message.setter
    def new_message(self, v):
        self._new_message = v

    @property
    def stt_ready(self):
        return self._stt_ready

    @stt_ready.setter
    def stt_ready(self, v):
        self._stt_ready = v

    @property
    def tts_ready(self):
        return self._tts_ready

    @tts_ready.setter
    def tts_ready(self, v):
        self._tts_ready = v

    @property
    def history(self):
        return self._history

    @history.setter
    def history(self, v):
        self._history = v

    @property
    def terminate(self):
        return self._terminate

    @terminate.setter
    def terminate(self, v):
        self._terminate = v

    # NEW PROPERTY
    @property
    def last_tts_time(self):
        return self._last_tts_time

    @last_tts_time.setter
    def last_tts_time(self, v):
        self._last_tts_time = v