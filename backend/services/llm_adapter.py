import os
import logging
import ollama
from dotenv import load_dotenv
from openai import OpenAI
from google import genai

load_dotenv()
logger = logging.getLogger(__name__)

class ErrorLLM(Exception):
    pass

class ChatAI:
    def __init__(self, temperature=0):
        self.temperature = temperature
        self._client = None

    @property
    def openai_client(self):
        if self._client is None:
            self._client = OpenAI(
                base_url=os.environ['BASE_URL'],
                api_key=os.environ['OPENAI_API_KEY'],
                timeout=60,
                max_retries=0
            )
        return self._client

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

    def ask_openai(self, message, model="google/gemini-3.1-pro-preview"):

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=message,
                temperature=self.temperature,
                max_tokens = 8000
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise ErrorLLM(f"OpenAI error: {e}")


    def ask_gemini(self, message, model="gemini-2.5-flash"):
        full_prompt = "\n\n".join(msg['role']+'\t'+msg['content'] for msg in message)
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        try:
            response = client.models.generate_content(
                model=model,
                contents=full_prompt
            )

            return response.text
        except Exception as e:
            logger.error(f"genai.Client error: {e}")
            raise ErrorLLM(f"genai.Client error: {e}")
