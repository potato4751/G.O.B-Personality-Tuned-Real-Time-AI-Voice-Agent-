import requests
from constants import COLAB_API_URL, API_TIMEOUT


class ModelManager:

    def __init__(self):
        pass

    def load_base_model(self):

        print("Remote LLM mode enabled.")
        print("Inference handled by Colab server.")

    def generate(self, prompt, max_new_tokens=120):

        payload = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens
        }

        try:

            response = requests.post(
                COLAB_API_URL,
                json=payload,
                timeout=API_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            return data.get("text", "")

        except Exception as e:

            print("Reflection generation error:", e)

            return ""