from fastapi import FastAPI, HTTPException, Query

from app.config import settings
from app.llm.ollama_client import OllamaClient
from app.memory.memory_store import MemoryStore
from app.rag.document_store import DocumentStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.codebase import (
    CodebaseAnalyzeRequest,
    CodebaseAnalyzeResponse,
    CodebaseFilesResponse,
)
from app.schemas.document import DocumentIngestResponse, DocumentSearchResponse
from app.schemas.memory import MemoryCreate, MemoryItem
from app.schemas.tool import DirectoryListResponse, FileReadResponse
from app.tools.codebase_tools import CodebaseTools
from app.tools.file_tools import FileTools

app = FastAPI(
    title="Hex.ai Backend",
    description="Local-first personal AI assistant backend.",
    version="0.7.0",
)

ollama_client = OllamaClient()
memory_store = MemoryStore()
document_store = DocumentStore()
file_tools = FileTools()
codebase_tools = CodebaseTools()


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.7.0",
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
        query_embedding = None

        if request.use_memory:
            memories = memory_store.get_memory_context(
                query=request.message,
                limit=8
            )

        if request.use_documents:
            try:
                query_embedding = ollama_client.embed(request.message)
            except RuntimeError:
                query_embedding = None

            documents = document_store.get_document_context(
                query=request.message,
                query_embedding=query_embedding,
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
    try:
        return document_store.ingest_documents(
            embedder=ollama_client.embed,
            embedding_model=settings.EMBEDDING_MODEL,
        )

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/documents/search", response_model=DocumentSearchResponse)
def search_documents(query: str, limit: int = 8):
    query_embedding = None
    search_type = "keyword"

    try:
        query_embedding = ollama_client.embed(query)
        search_type = "semantic"
    except RuntimeError:
        query_embedding = None
        search_type = "keyword"

    results = document_store.get_document_context(
        query=query,
        query_embedding=query_embedding,
        limit=limit,
    )

    return DocumentSearchResponse(
        query=query,
        search_type=search_type,
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


@app.get("/tools/codebase/files", response_model=CodebaseFilesResponse)
def list_codebase_files(
    path: str = Query(default=".", description="Project-relative codebase path"),
    max_files: int = Query(default=25, ge=1, le=80),
):
    try:
        context = codebase_tools.collect_code_context(
            input_path=path,
            max_files=max_files,
            max_chars_per_file=500,
            max_total_chars=10000,
        )

        return CodebaseFilesResponse(
            path=context["path"],
            file_count=context["file_count"],
            files=context["files"],
        )

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/tools/codebase/analyze", response_model=CodebaseAnalyzeResponse)
def analyze_codebase(request: CodebaseAnalyzeRequest):
    try:
        context = codebase_tools.collect_code_context(
            input_path=request.path,
            max_files=request.max_files,
            max_chars_per_file=request.max_chars_per_file,
            max_total_chars=request.max_total_chars,
        )

        analysis_prompt = codebase_tools.build_analysis_prompt(
            code_context=context,
            focus=request.focus,
        )

        response_text = ollama_client.generate(
            prompt=analysis_prompt,
            model=request.model,
            memories=[],
            documents=[],
        )

        return CodebaseAnalyzeResponse(
            model=request.model or settings.DEFAULT_MODEL,
            path=context["path"],
            files_analyzed=context["file_count"],
            total_chars=context["total_chars"],
            files=context["files"],
            response=response_text,
        )

    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))