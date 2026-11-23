import yaml
import re
import requests

from constants import CONVERSATION_WINDOW, COLAB_API_URL, API_TIMEOUT


class LLMWrapper:

    def __init__(self, signals, model_manager, tts):

        self.signals = signals
        self.modelmgr = model_manager
        self.tts = tts

        with open("personality.yaml", "r") as f:
            cfg = yaml.safe_load(f)

        self.system_prompt = cfg["system_prompt"]
        self.personality = cfg.get("personality", "")

    # -----------------------------
    # BUILD SYSTEM CONTENT
    # -----------------------------

    def build_system_content(self):

        # keep system minimal and rigid
        return "/no_think\n" + self.system_prompt.strip()

    # -----------------------------
    # BUILD USER CONTENT
    # -----------------------------

    def build_user_content(self, injections):

        text = ""

        # personality first
        if self.personality.strip():
            text += "Personality and speaking style:\n"
            text += self.personality.strip()
            text += "\n\n"

        # memory injections
        if injections and injections.strip():
            text += "Known facts:\n"
            text += injections.strip()
            text += "\n\n"

        # conversation history
        text += "Conversation so far:\n\n"

        for m in self.signals.history[-CONVERSATION_WINDOW:]:
            text += m["content"] + "\n"

        text += "\nReply to the last message."

        return text.strip()

    # -----------------------------
    # BUILD CHAT MESSAGES
    # -----------------------------

    def build_messages(self, injections):

        system_content = self.build_system_content()
        user_content = self.build_user_content(injections)

        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": user_content
            }
        ]

        return messages

    # -----------------------------
    # CLEAN RESPONSE
    # -----------------------------

    def clean_response(self, text):

        if not text:
            return ""

        text = text.strip()

        text = re.split(r"###", text)[0]

        for prefix in ["Assistant:", "assistant:", "Goober:", "goober:"]:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        text = text.replace("<|im_end|>", "").replace("<|im_start|>", "")
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # -----------------------------
    # MAIN PROMPT CALL
    # -----------------------------

    def prompt(self, injections):

        self.signals.AI_thinking = True
        self.signals.new_message = False

        messages = self.build_messages(injections)

        payload = {
            "messages": messages
        }

        text = ""

        try:

            response = requests.post(
                COLAB_API_URL,
                json=payload,
                timeout=API_TIMEOUT
            )

            response.raise_for_status()

            text = response.text.strip()

        except Exception as e:

            print("API request error:", e)

        cleaned = self.clean_response(text)

        if not cleaned:
            cleaned = "Hmm, I didn't quite catch that."

        print("Assistant:", cleaned)

        self.tts.enqueue(cleaned)

        self.signals.history.append({
            "role": "assistant",
            "content": f"Goober: {cleaned}"
        })

        self.signals.AI_thinking = False