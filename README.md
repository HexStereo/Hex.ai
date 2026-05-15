# Hex.ai

Hex.ai is a local-first personal AI assistant project.

The goal of Hex.ai is to build a private, modular, extensible AI system that runs on a personal computer, uses local language models, stores user-defined memory, reads project documents, analyzes codebases, and later performs controlled tool-based actions.

Hex.ai is being developed as a personal AI assistant system, not just a chatbot.

---

## Project Status

Current version: `v0.5`

Current state:

- Local FastAPI backend
- Ollama integration
- Local model chat endpoint
- System identity prompt for Hex.ai
- SQLite-based memory storage
- Memory-aware chat
- Simple document ingestion
- Document-aware chat
- Safe file listing
- Safe file reading
- Codebase file collection
- Codebase analysis endpoint

---

## Purpose

Hex.ai is designed to become a private personal AI assistant that can help with:

- Software engineering
- Game development
- AI development
- Debugging
- Project planning
- Codebase analysis
- Technical learning
- Document-based question answering
- Local database and tool usage in future versions

The long-term goal is to create a Jarvis-like personal AI system, but in a realistic, modular, local-first architecture.

---

## Design Philosophy

Hex.ai follows these principles:

- Local-first
- Private by default
- Modular
- Extensible
- Safe tool execution
- No accidental upload of private data
- Small working system before complex features
- Clear versioned development roadmap

---

## Tech Stack

Current stack:

- Python 3.12
- FastAPI
- Uvicorn
- Ollama
- qwen2.5-coder:14b
- SQLite
- Pydantic
- Requests

Planned additions:

- qwen3-coder:30b
- Chroma or Qdrant
- Embeddings
- LangGraph
- Safe command execution
- SQL Server / PostgreSQL connectors
- Open WebUI
- Docker
- Whisper / whisper.cpp
- Piper TTS
- Voice assistant layer

---

## Current Local Model

Current stable local model:

```text
qwen2.5-coder:14b