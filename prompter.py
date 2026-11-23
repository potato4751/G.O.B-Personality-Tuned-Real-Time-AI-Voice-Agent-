import time
from llm_wrapper import LLMWrapper


class Prompter:

    def __init__(self, signals, model_manager, tts, modules):

        self.signals = signals
        self.modules = modules

        self.wrapper = LLMWrapper(signals, model_manager, tts)

        self.last_speech_time = 0
        self.silence_threshold = 1.5

    def notify_speech(self):
        self.last_speech_time = time.time()

    def collect_injections(self):

        injections = []

        for module in self.modules:

            if not module.enabled:
                continue

            inj = module.get_prompt_injection()

            if inj and inj.text.strip():
                injections.append(inj)

        injections.sort(key=lambda x: x.priority, reverse=True)

        combined = ""

        for inj in injections:
            combined += str(inj) + "\n"

        return combined

    def loop(self):

        while True:

            if self.signals.AI_speaking or self.signals.AI_thinking:
                time.sleep(0.1)
                continue

            if not self.signals.new_message:
                time.sleep(0.1)
                continue

            silence_time = time.time() - self.last_speech_time

            if silence_time < self.silence_threshold:
                time.sleep(0.1)
                continue

            self.signals.new_message = False

            injections = self.collect_injections()

            self.wrapper.prompt(injections)