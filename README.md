# Hex.ai

Hex.ai is a local-first personal AI assistant project.

The goal of Hex.ai is to build a private, modular, extensible AI system that runs on a personal computer, uses local language models, stores user-defined memory, reads local documents, analyzes codebases, and later performs controlled tool-based actions.

Hex.ai is not just a chatbot. It is being developed as a personal AI assistant backend that can evolve into a Jarvis-like local AI system.

---

## Current Version

Current version: `v0.7`

Current status: active local development.

---

## Implemented Features

Hex.ai currently includes:

- Local FastAPI backend
- Ollama integration
- Local model chat endpoint
- System identity prompt for Hex.ai
- SQLite-based memory storage
- Memory-aware chat
- Document ingestion
- Document chunking
- Document-aware chat
- Safe file listing
- Safe file reading
- Codebase file collection
- Codebase analysis endpoint
- Embedding model integration
- `nomic-embed-text` support through Ollama
- Document embedding generation
- Document embedding storage in SQLite
- Semantic document search
- Semantic document-aware chat

---

## Purpose

Hex.ai is designed to assist with:

- Software engineering
- Game development
- AI development
- Debugging
- Project planning
- Codebase analysis
- Technical learning
- Document-based question answering
- Local database usage in future versions
- Controlled tool usage in future versions

The long-term goal is to create a private, local-first AI assistant that can understand the user's projects, remember relevant information, inspect local files, analyze code, use safe tools, and later support voice interaction.

---

## Design Philosophy

Hex.ai follows these principles:

- Local-first
- Private by default
- Modular architecture
- Extensible tool system
- Safe file and command access
- No accidental upload of private data
- Small working modules before complex autonomy
- Versioned development
- GitHub-ready project structure

---

## Tech Stack

Current stack:

- Python 3.12
- FastAPI
- Uvicorn
- Ollama
- qwen2.5-coder:14b
- nomic-embed-text
- SQLite
- Pydantic
- Requests
- Git / GitHub

Planned additions:

- qwen3-coder:30b
- Chroma or Qdrant
- Better vector search
- LangGraph
- Safe command execution
- SQL Server / PostgreSQL connectors
- Docker
- Open WebUI
- Whisper / whisper.cpp
- Piper TTS
- Voice assistant layer

---

## Local Models

Current stable chat model:

```text
qwen2.5-coder:14b