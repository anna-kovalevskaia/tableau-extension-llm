import ollama
from openai import OpenAI


class ChatAI:
    def __init__(self, system_prompt, temperature=0):
        self.system_prompt = system_prompt
        self.temperature = temperature
        self._openai_client = None

    @property
    def openai_client(self):
        if self._openai_client is None:
            self._openai_client = OpenAI()
        return self._openai_client

    def ask_ollama(self, user_content, model="llama3:70b"):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]
        try:
            response = ollama.chat(
                model=model,
                messages=message,
                options={"temperature": self.temperature}
            )

            return response["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OllamaAI error: {e}")

    def ask_openai(self, user_content, model="gpt-4.1"):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=message,
                temperature=self.temperature
            )

            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI error: {e}")

