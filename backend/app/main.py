from fastapi import FastAPI, HTTPException, Query

from app.config import settings
from app.llm.ollama_client import OllamaClient
from app.memory.memory_store import MemoryStore
from app.rag.document_store import DocumentStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.document import DocumentIngestResponse, DocumentSearchResponse
from app.schemas.memory import MemoryCreate, MemoryItem
from app.schemas.tool import DirectoryListResponse, FileReadResponse
from app.tools.file_tools import FileTools

app = FastAPI(
    title="Hex.ai Backend",
    description="Local-first personal AI assistant backend.",
    version="0.4.0",
)

ollama_client = OllamaClient()
memory_store = MemoryStore()
document_store = DocumentStore()
file_tools = FileTools()


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.4.0",
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
        documents = []

        if request.use_memory:
            memories = memory_store.get_memory_context(
                query=request.message,
                limit=8
            )

        if request.use_documents:
            documents = document_store.get_document_context(
                query=request.message,
                limit=5
            )

        response_text = ollama_client.generate(
            prompt=request.message,
            model=request.model,
            memories=memories,
            documents=documents,
        )

        return ChatResponse(
            model=request.model or settings.DEFAULT_MODEL,
            response=response_text,
            memory_used=len(memories),
            documents_used=len(documents),
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


@app.post("/documents/ingest", response_model=DocumentIngestResponse)
def ingest_documents():
    return document_store.ingest_documents()


@app.get("/documents/search", response_model=DocumentSearchResponse)
def search_documents(query: str, limit: int = 8):
    results = document_store.search_documents(query=query, limit=limit)

    return DocumentSearchResponse(
        query=query,
        results=results,
    )


@app.get("/tools/files/list", response_model=DirectoryListResponse)
def list_files(path: str = Query(default=".", description="Project-relative directory path")):
    try:
        return file_tools.list_directory(path)

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/tools/files/read", response_model=FileReadResponse)
def read_file(path: str = Query(..., description="Project-relative file path")):
    try:
        return file_tools.read_file(path)

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except IsADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))