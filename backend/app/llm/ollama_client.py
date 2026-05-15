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

    def build_document_context(self, documents: list[dict] | None = None) -> str:
        if not documents:
            return "No document context was provided for this request."

        document_lines = []

        for document in documents:
            score_text = ""

            if document.get("score") is not None:
                score_text = f"\nSimilarity score: {document.get('score')}"

            document_lines.append(
                f"""
Source: {document.get("source_path")}
Chunk: {document.get("chunk_index")}{score_text}
Content:
{document.get("content")}
""".strip()
            )

        return "\n\n---\n\n".join(document_lines)

    def build_prompt(
        self,
        user_message: str,
        memories: list[dict] | None = None,
        documents: list[dict] | None = None,
    ) -> str:
        memory_context = self.build_memory_context(memories)
        document_context = self.build_document_context(documents)

        return f"""
{HEXAI_SYSTEM_PROMPT}

Stored memory context:
{memory_context}

Document context:
{document_context}

Instruction:
Use stored memory and document context only if relevant to the user's message.
If the context is not relevant, ignore it.
Do not invent memories, files, or document content that are not provided.
If the answer depends on missing information, say what is missing.

User message:
{user_message}

Hex.ai response:
""".strip()

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        memories: list[dict] | None = None,
        documents: list[dict] | None = None,
    ) -> str:
        selected_model = model or settings.DEFAULT_MODEL

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": selected_model,
            "prompt": self.build_prompt(
                user_message=prompt,
                memories=memories,
                documents=documents,
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

    def embed(self, text: str, model: str | None = None) -> list[float]:
        selected_model = model or settings.EMBEDDING_MODEL

        url = f"{self.base_url}/api/embeddings"

        payload = {
            "model": selected_model,
            "prompt": text
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                "Ollama is not reachable. Make sure Ollama is running."
            ) from exc

        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                "Ollama embedding request timed out."
            ) from exc

        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Ollama embedding request failed: {exc}"
            ) from exc

        data = response.json()
        embedding = data.get("embedding")

        if not embedding:
            raise RuntimeError("Ollama did not return an embedding vector.")

        return embedding