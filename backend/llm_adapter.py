import logging
import ollama
from openai import OpenAI

logger = logging.getLogger(__name__)

class ErrorLLM(Exception):
    pass

class ChatAI:
    def __init__(self, temperature=0):
        self.temperature = temperature
        self._openai_client = None

    @property
    def openai_client(self):
        if self._openai_client is None:
            self._openai_client = OpenAI()
        return self._openai_client

    def ask_ollama(self, message, model="llama3:70b"):

        try:
            response = ollama.chat(
                model=model,
                messages=message,
                options={"temperature": self.temperature}
            )

            return response["message"]["content"]
        except Exception as e:
            logger.error(f"OllamaAI error: {e}")
            raise ErrorLLM(f"OllamaAI error: {e}")

    def ask_openai(self, message, model="gpt-4.1"):

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=message,
                temperature=self.temperature
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise ErrorLLM(f"OpenAI error: {e}")

