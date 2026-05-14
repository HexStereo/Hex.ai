import requests

from app.config import settings
from app.prompts.system_prompt import HEXAI_SYSTEM_PROMPT


class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    def build_prompt(self, user_message: str) -> str:
        return f"""
{HEXAI_SYSTEM_PROMPT}

User message:
{user_message}

Hex.ai response:
""".strip()

    def generate(self, prompt: str, model: str | None = None) -> str:
        selected_model = model or settings.DEFAULT_MODEL

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": selected_model,
            "prompt": self.build_prompt(prompt),
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 8192
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()

        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "Ollama is not reachable. Make sure Ollama is running."
            ) from exc

        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                "Ollama request timed out. The model may be loading or responding slowly."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        data = response.json()
        return data.get("response", "")