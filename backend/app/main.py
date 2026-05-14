from fastapi import FastAPI, HTTPException

from app.config import settings
from app.llm.ollama_client import OllamaClient
from app.memory.memory_store import MemoryStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.memory import MemoryCreate, MemoryItem

app = FastAPI(
    title="Hex.ai Backend",
    description="Local-first personal AI assistant backend.",
    version="0.2.0",
)

ollama_client = OllamaClient()
memory_store = MemoryStore()


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.2.0",
        "status": "running",
        "message": "Hex.ai backend is alive."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        memories = []

        if request.use_memory:
            memories = memory_store.get_memory_context(
                query=request.message,
                limit=8
            )

        response_text = ollama_client.generate(
            prompt=request.message,
            model=request.model,
            memories=memories
        )

        return ChatResponse(
            model=request.model or settings.DEFAULT_MODEL,
            response=response_text,
            memory_used=len(memories)
        )

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/memory", response_model=MemoryItem)
def create_memory(memory: MemoryCreate):
    return memory_store.add_memory(
        key=memory.key,
        value=memory.value,
        category=memory.category,
    )


@app.get("/memory", response_model=list[MemoryItem])
def list_memories(limit: int = 50):
    return memory_store.list_memories(limit=limit)


@app.get("/memory/search", response_model=list[MemoryItem])
def search_memories(query: str, limit: int = 10):
    return memory_store.search_memories(query=query, limit=limit)