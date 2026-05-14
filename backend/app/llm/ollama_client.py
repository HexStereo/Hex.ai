import requests

from app.config import settings
from app.prompts.system_prompt import HEXAI_SYSTEM_PROMPT


class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL

    def build_memory_context(self, memories: list[dict] | None = None) -> str:
        if not memories:
            return "No stored memory was provided for this request."

        memory_lines = []

        for memory in memories:
            memory_lines.append(
                f"- [{memory.get('category')}] {memory.get('key')}: {memory.get('value')}"
            )

        return "\n".join(memory_lines)

    def build_prompt(self, user_message: str, memories: list[dict] | None = None) -> str:
        memory_context = self.build_memory_context(memories)

        return f"""
{HEXAI_SYSTEM_PROMPT}

Stored memory context:
{memory_context}

Instruction:
Use the stored memory context only if it is relevant to the user's message.
If the memory context is not relevant, ignore it.
Do not invent memories that are not provided.

User message:
{user_message}

Hex.ai response:
""".strip()

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        memories: list[dict] | None = None
    ) -> str:
        selected_model = model or settings.DEFAULT_MODEL

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": selected_model,
            "prompt": self.build_prompt(
                user_message=prompt,
                memories=memories
            ),
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