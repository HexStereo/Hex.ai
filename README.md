# Hex.ai

Hex.ai is a local-first personal AI assistant project.

The goal of Hex.ai is to build a private, modular, extensible AI system that runs on a personal computer, uses local language models, stores user-defined memory, reads local documents, analyzes codebases, performs controlled tool-based actions, checks its runtime environment, and routes user requests to the correct internal capability.

Hex.ai is not just a chatbot. It is being developed as a private personal AI assistant backend that can evolve into a Jarvis-like local AI system.

---

## Current Version

Current version: `v1.1.0`

Current status: local backend MVP with agent planning.

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
- Embedding model integration
- `nomic-embed-text` support through Ollama
- Document embedding generation
- Document embedding storage in SQLite
- Semantic document search
- Semantic document-aware chat
- Safe file listing
- Safe file reading
- Codebase file collection
- Codebase analysis endpoint
- Safe command execution layer
- Allowed command registry
- Command execution endpoint
- Raw command planning
- Command risk classification
- Confirmation-required command execution
- Read-only command auto-approval
- High-risk system command blocking
- System diagnostics endpoint
- Ollama reachability check
- Local model listing
- Path status checks for memory, documents, and vector database folders
- Agent planning endpoint
- Intent routing for system, command, codebase, document, memory, and chat requests

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
- Local file inspection
- Local command execution with permission control
- System status inspection
- Intent routing
- Local database usage in future versions
- Controlled automation in future versions

The long-term goal is to create a private, local-first AI assistant that can understand the user's projects, remember relevant information, inspect local files, analyze code, use safe tools, execute controlled commands, check its own runtime environment, route tasks to the correct internal module, and later support voice interaction.

---

## Design Philosophy

Hex.ai follows these principles:

- Local-first
- Private by default
- Modular architecture
- Extensible tool system
- Controlled command execution
- Permission-based risk handling
- Clear intent routing
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
- SQL Server / PostgreSQL connectors
- Docker
- Open WebUI
- Whisper / whisper.cpp
- Piper TTS
- Voice assistant layer
- Desktop UI

---

## Local Models

Current stable chat model:

```text
qwen2.5-coder:14b
```

Current embedding model:

```text
nomic-embed-text
```

Planned stronger local coding model:

```text
qwen3-coder:30b
```

---

## Tested Development Environment

Current development environment:

```text
Windows 11
Python 3.12.10
Git 2.54.0
Ollama 0.23.4
NVIDIA GeForce RTX 5090 Laptop GPU
24 GB VRAM
96 GB RAM
```

---

## Project Structure

```text
Hex.ai/
│
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   └── orchestrator.py
│   │   │
│   │   ├── llm/
│   │   │   └── ollama_client.py
│   │   │
│   │   ├── memory/
│   │   │   └── memory_store.py
│   │   │
│   │   ├── prompts/
│   │   │   └── system_prompt.py
│   │   │
│   │   ├── rag/
│   │   │   ├── ingest.py
│   │   │   └── document_store.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── agent.py
│   │   │   ├── chat.py
│   │   │   ├── memory.py
│   │   │   ├── document.py
│   │   │   ├── tool.py
│   │   │   ├── codebase.py
│   │   │   ├── command.py
│   │   │   └── system.py
│   │   │
│   │   ├── security/
│   │   │   └── command_policy.py
│   │   │
│   │   ├── system/
│   │   │   ├── __init__.py
│   │   │   └── diagnostics.py
│   │   │
│   │   ├── tools/
│   │   │   ├── file_tools.py
│   │   │   ├── codebase_tools.py
│   │   │   └── command_tools.py
│   │   │
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── data/
│   ├── documents/
│   ├── memory/
│   └── vector_db/
│
├── scripts/
│   └── run_backend.bat
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Architecture

Current architecture:

```text
User / API Client / Swagger
        ↓
FastAPI Backend
        ↓
Agent Planner + Core API Layer
        ↓
LLM Layer + Memory Layer + RAG Layer + Tool Layer + System Diagnostics
        ↓
Ollama + SQLite + Local Files + Controlled Commands
```

Current request planning flow:

```text
User message
    ↓
POST /agent/plan
    ↓
AgentOrchestrator classifies intent
    ↓
Returns target endpoint, method, parameters, reason, and warnings
```

---

## Main Components

### 1. FastAPI Backend

Main file:

```text
backend/app/main.py
```

Responsibilities:

- Exposes API endpoints
- Routes requests to memory, RAG, file tools, codebase tools, command tools, system diagnostics, agent planner, and LLM layer
- Provides Swagger documentation
- Returns structured JSON responses

---

### 2. Agent Planning Layer

Location:

```text
backend/app/agent/
```

Main file:

```text
orchestrator.py
```

Responsibilities:

- Reads user messages
- Detects user intent
- Selects the correct internal endpoint
- Prepares endpoint parameters
- Returns confidence, reason, and warnings
- Prevents basic routing mistakes such as treating Turkish words like `nedir` as the Windows `dir` command

Currently supported intents:

```text
SYSTEM_INFO
COMMAND_PLAN
CODEBASE_ANALYSIS
DOCUMENT_SEARCH
MEMORY_SEARCH
CHAT
INVALID
```

Current agent endpoint:

```text
POST /agent/plan
```

---

### 3. LLM Layer

Location:

```text
backend/app/llm/
```

Main file:

```text
ollama_client.py
```

Responsibilities:

- Connects to Ollama
- Sends prompts to local chat models
- Creates embeddings through Ollama
- Builds prompts with system identity, memory context, and document context
- Returns generated model responses

---

### 4. Prompt Layer

Location:

```text
backend/app/prompts/
```

Main file:

```text
system_prompt.py
```

Responsibilities:

- Defines Hex.ai identity
- Defines assistant behavior rules
- Defines privacy-first and safety-first operating style
- Prevents the model from claiming unimplemented abilities

---

### 5. Memory Layer

Location:

```text
backend/app/memory/
```

Main file:

```text
memory_store.py
```

Current storage:

```text
SQLite
```

Responsibilities:

- Stores long-term memory records
- Lists memory records
- Searches memory records
- Provides relevant memory context to chat

Memory flow:

```text
POST /memory
    ↓
Save memory into SQLite
    ↓
POST /chat with use_memory=true
    ↓
Retrieve relevant memory
    ↓
Add memory context to prompt
    ↓
Send prompt to Ollama
```

---

### 6. RAG Layer

Location:

```text
backend/app/rag/
```

Main file:

```text
document_store.py
```

Current implementation:

- Document ingestion
- Text/code document chunking
- SQLite document chunk storage
- SQLite embedding storage
- Keyword fallback search
- Semantic search with embeddings
- Document-aware chat

Current RAG flow:

```text
Add files into data/documents/
    ↓
POST /documents/ingest
    ↓
Split documents into chunks
    ↓
Generate embeddings
    ↓
Store chunks and embeddings in SQLite
    ↓
POST /chat with use_documents=true
    ↓
Create query embedding
    ↓
Retrieve semantically similar document chunks
    ↓
Add document context to prompt
    ↓
Send prompt to Ollama
```

---

### 7. Tool Layer

Location:

```text
backend/app/tools/
```

Current tools:

```text
file_tools.py
codebase_tools.py
command_tools.py
```

Current capabilities:

- Safe directory listing
- Safe file reading
- Codebase file collection
- Codebase context building
- Codebase analysis prompt generation
- Allowed command execution
- Raw command planning
- Command risk classification
- Confirmation-required command execution

---

### 8. Command Permission Engine

Main file:

```text
backend/app/tools/command_tools.py
```

Current command system supports:

- Allowed command registry
- Raw command planning
- Risk classification
- Confirmation phrase requirement
- Read-only command auto-approval
- Write command confirmation
- Network command confirmation
- Script execution confirmation
- Destructive command confirmation
- System high-risk command blocking

Current risk levels:

```text
READ_ONLY
DEV_SAFE
WRITE_PROJECT
DESTRUCTIVE
NETWORK
SCRIPT_EXECUTION
MIXED_OR_CHAINED
SYSTEM_HIGH_RISK
UNKNOWN
INVALID
```

Confirmation phrases:

```text
I_CONFIRM_HEXAI_COMMAND
I_CONFIRM_HEXAI_FULL_ACCESS
```

`SYSTEM_HIGH_RISK` commands are blocked from API execution in the current version.

---

### 9. System Diagnostics

Location:

```text
backend/app/system/
```

Main file:

```text
diagnostics.py
```

Current capabilities:

- Shows app name
- Shows app environment
- Shows backend version
- Shows project root
- Shows default chat model
- Shows embedding model
- Checks memory DB path
- Checks documents path
- Checks vector DB path
- Checks Ollama reachability
- Lists installed Ollama models

---

### 10. Security Layer

Location:

```text
backend/app/security/
```

Main file:

```text
command_policy.py
```

Responsibilities:

- Blocks sensitive file paths
- Prevents project directory escape
- Blocks `.env`, `.git`, `.venv`, memory database, and vector database paths
- Restricts readable file types
- Limits file read size
- Blocks dangerous working directories for command execution

---

## API Endpoints

### Core

```text
GET  /
GET  /health
POST /chat
```

### Agent

```text
POST /agent/plan
```

### System

```text
GET /system/info
```

### Memory

```text
POST /memory
GET  /memory
GET  /memory/search
```

### Documents

```text
POST /documents/ingest
GET  /documents/search
```

### Safe File Tools

```text
GET /tools/files/list
GET /tools/files/read
```

### Codebase Analysis

```text
GET  /tools/codebase/files
POST /tools/codebase/analyze
```

### Command Tools

```text
GET  /tools/commands/allowed
POST /tools/commands/run
POST /tools/commands/plan
POST /tools/commands/run-confirmed
```

---

## Security Rules

Hex.ai blocks access to the following paths by default:

```text
.env
.git
.venv
__pycache__
.pytest_cache__
.mypy_cache
.ruff_cache
data/memory
data/vector_db
```

Reasons:

- `.env` may contain secrets, API keys, tokens, or local configuration
- `.git` contains repository internals
- `.venv` contains installed packages and large dependency files
- `data/memory` contains personal assistant memory
- `data/vector_db` will contain embedded private documents in future versions

---

## Readable File Types

Currently allowed text/code file types:

```text
.txt
.md
.py
.cs
.js
.ts
.json
.html
.css
.sql
.bat
.env.example
.gitignore
.yml
.yaml
.toml
```

---

## GitHub Safety Rules

The following must not be committed:

```text
.env
data/documents/*
data/memory/*
data/vector_db/*
personal files
API keys
tokens
credentials
private logs
local database files
```

The `.gitignore` file is configured to prevent private local data from being uploaded accidentally.

---

## Setup Guide

### 1. Verify Required Tools

Open CMD:

```cmd
python --version
git --version
ollama --version
nvidia-smi
```

Expected:

```text
Python 3.12.x
git version ...
ollama version ...
NVIDIA GPU table
```

---

### 2. Install Local Models

Install chat model:

```cmd
ollama pull qwen2.5-coder:14b
```

Install embedding model:

```cmd
ollama pull nomic-embed-text
```

Test chat model:

```cmd
ollama run qwen2.5-coder:14b
```

Exit model shell:

```text
/bye
```

Test embedding model:

```cmd
curl http://localhost:11434/api/embeddings -d "{\"model\":\"nomic-embed-text\",\"prompt\":\"Hex.ai is a local-first personal AI assistant.\"}"
```

---

### 3. Open Project

```cmd
cd /d C:\Projects\Hex.ai
```

---

### 4. Create Python Virtual Environment

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
```

---

### 5. Install Dependencies

```cmd
pip install -r requirements.txt
```

---

### 6. Environment File

Default `.env.example`:

```env
APP_NAME=Hex.ai
APP_ENV=development

OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=qwen2.5-coder:14b
EMBEDDING_MODEL=nomic-embed-text

MEMORY_DB_PATH=./data/memory/hexai_memory.db
VECTOR_DB_PATH=./data/vector_db
DOCUMENTS_PATH=./data/documents

ALLOW_COMMAND_EXECUTION=false
```

`.env.example` can be copied to `.env` later if local overrides are needed.

---

### 7. Run Backend

From project root:

```cmd
scripts\run_backend.bat
```

Manual run:

```cmd
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

---

### 8. Open Swagger UI

```text
http://127.0.0.1:8010/docs
```

---

## Basic API Usage

### Health Check

Endpoint:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

### System Info

Endpoint:

```text
GET /system/info
```

Expected response includes:

```json
{
  "app_name": "Hex.ai",
  "app_env": "development",
  "version": "1.1.0",
  "default_model": "qwen2.5-coder:14b",
  "embedding_model": "nomic-embed-text"
}
```

---

### Agent Plan

Endpoint:

```text
POST /agent/plan
```

System status example:

```json
{
  "message": "sistem durumunu kontrol et",
  "cwd": ".",
  "model": "qwen2.5-coder:14b"
}
```

Expected routing:

```json
{
  "intent": "SYSTEM_INFO",
  "method": "GET",
  "endpoint": "/system/info"
}
```

Command planning example:

```json
{
  "message": "git status komutunu planla",
  "cwd": ".",
  "model": "qwen2.5-coder:14b"
}
```

Expected routing:

```json
{
  "intent": "COMMAND_PLAN",
  "method": "POST",
  "endpoint": "/tools/commands/plan"
}
```

Codebase analysis example:

```json
{
  "message": "backend/app kod tabanını analiz et",
  "cwd": ".",
  "model": "qwen2.5-coder:14b"
}
```

Expected routing:

```json
{
  "intent": "CODEBASE_ANALYSIS",
  "method": "POST",
  "endpoint": "/tools/codebase/analyze"
}
```

Document search example:

```json
{
  "message": "dokümanlarda Hex.ai güvenlik kurallarını ara",
  "cwd": ".",
  "model": "qwen2.5-coder:14b"
}
```

Expected routing:

```json
{
  "intent": "DOCUMENT_SEARCH",
  "method": "GET",
  "endpoint": "/documents/search"
}
```

Normal chat example:

```json
{
  "message": "Hex.ai nedir?",
  "cwd": ".",
  "model": "qwen2.5-coder:14b"
}
```

Expected routing:

```json
{
  "intent": "CHAT",
  "method": "POST",
  "endpoint": "/chat"
}
```

---

### Chat

Endpoint:

```text
POST /chat
```

Example body:

```json
{
  "message": "Sen kimsin?",
  "model": "qwen2.5-coder:14b",
  "use_memory": true,
  "use_documents": true
}
```

---

### Add Memory

Endpoint:

```text
POST /memory
```

Example body:

```json
{
  "key": "project_name",
  "value": "The personal local-first AI assistant project is named Hex.ai.",
  "category": "project"
}
```

---

### Ingest Documents

Put supported files into:

```text
data/documents/
```

Then run:

```text
POST /documents/ingest
```

Expected response includes:

```json
{
  "files_processed": 1,
  "chunks_created": 1,
  "embeddings_created": 1,
  "embedding_model": "nomic-embed-text"
}
```

---

### Search Documents

Endpoint:

```text
GET /documents/search?query=kişisel yapay zeka asistanının güvenlik kuralları
```

Expected response includes:

```json
{
  "search_type": "semantic",
  "results": [
    {
      "source_path": "data\\documents\\...",
      "score": 0.45
    }
  ]
}
```

---

### List Files Safely

Endpoint:

```text
GET /tools/files/list?path=.
```

Example paths:

```text
.
backend/app
scripts
```

Blocked examples:

```text
.env
data/memory
../
```

---

### Read File Safely

Endpoint:

```text
GET /tools/files/read?path=README.md
```

Example readable files:

```text
README.md
backend/app/main.py
backend/app/config.py
.env.example
.gitignore
```

---

### Analyze Codebase

Endpoint:

```text
POST /tools/codebase/analyze
```

Example body:

```json
{
  "path": "backend/app",
  "model": "qwen2.5-coder:14b",
  "max_files": 12,
  "max_chars_per_file": 1500,
  "max_total_chars": 15000,
  "focus": "Summarize Hex.ai backend architecture, module responsibilities, risks, and next steps."
}
```

---

### List Allowed Commands

Endpoint:

```text
GET /tools/commands/allowed
```

---

### Run Allowed Command

Endpoint:

```text
POST /tools/commands/run
```

Example body:

```json
{
  "command_key": "git_status",
  "cwd": "."
}
```

---

### Plan Raw Command

Endpoint:

```text
POST /tools/commands/plan
```

Example body:

```json
{
  "command": "git status",
  "cwd": "."
}
```

Expected response:

```json
{
  "risk_level": "READ_ONLY",
  "requires_confirmation": false,
  "allowed_to_run": true
}
```

Risky command example:

```json
{
  "command": "echo Hex.ai command engine test > data\\documents\\command_test.txt",
  "cwd": "."
}
```

Expected response:

```json
{
  "risk_level": "MIXED_OR_CHAINED",
  "requires_confirmation": true,
  "allowed_to_run": true,
  "confirmation_phrase": "I_CONFIRM_HEXAI_COMMAND"
}
```

---

### Run Confirmed Raw Command

Endpoint:

```text
POST /tools/commands/run-confirmed
```

Example body:

```json
{
  "command": "echo Hex.ai command engine test > data\\documents\\command_test.txt",
  "cwd": ".",
  "confirmation_phrase": "I_CONFIRM_HEXAI_COMMAND"
}
```

High-risk blocked example:

```json
{
  "command": "format C:",
  "cwd": "."
}
```

Expected planning result:

```json
{
  "risk_level": "SYSTEM_HIGH_RISK",
  "requires_confirmation": true,
  "allowed_to_run": false
}
```

---

## Version Roadmap

### v0.1 — Local Chat Backend

Status: Done

Implemented:

- FastAPI backend
- Ollama connection
- qwen2.5-coder:14b local model
- `/chat` endpoint
- Hex.ai system identity prompt

---

### v0.2 — SQLite Memory

Status: Done

Implemented:

- SQLite memory database
- Add memory endpoint
- List memory endpoint
- Search memory endpoint
- Memory-aware chat

---

### v0.3 — Simple RAG

Status: Done

Implemented:

- Document ingestion
- Text/code document chunking
- Document chunk storage
- Document search
- Document-aware chat

---

### v0.4 — Safe File Tools

Status: Done

Implemented:

- Safe directory listing
- Safe file reading
- Project directory boundary protection
- Blocked sensitive paths
- Restricted readable file types

---

### v0.5 — Codebase Analysis

Status: Done

Implemented:

- Codebase file collection
- Safe code context builder
- Codebase analysis prompt generation
- `/tools/codebase/files`
- `/tools/codebase/analyze`

---

### v0.6 — GitHub Preparation

Status: Done

Implemented:

- GitHub private repository setup
- Complete README
- Git remote configuration
- First GitHub push

---

### v0.7 — Embedding-Based RAG

Status: Done

Implemented:

- Added embedding model support
- Added `nomic-embed-text` through Ollama
- Added document embedding generation
- Added document embedding storage in SQLite
- Added semantic document search
- Added semantic document-aware chat

---

### v0.8 — Safe Command Tools

Status: Done

Implemented:

- Added allowed command execution layer
- Added `/tools/commands/allowed`
- Added `/tools/commands/run`
- Added safe commands such as `git status`, `git diff`, `python --version`, `pip list`, `ollama list`, `dir`, and `tree`
- Added project-relative working directory validation
- Added blocked path protection
- Added command timeout
- Added command output truncation
- Blocked unknown commands through the safe command registry

---

### v0.9 — Command Permission Engine

Status: Done

Implemented:

- Added raw command planning endpoint
- Added `/tools/commands/plan`
- Added `/tools/commands/run-confirmed`
- Added command risk classification
- Added confirmation-required execution
- Added read-only command detection
- Added development command detection
- Added write-project command detection
- Added destructive command detection
- Added network command detection
- Added script execution detection
- Added mixed/chained command detection
- Added system high-risk command blocking

---

### v1.0 — Backend MVP Stabilization

Status: Done

Implemented:

- Added centralized backend version
- Added system diagnostics module
- Added `/system/info`
- Added Ollama reachability check
- Added local Ollama model listing
- Added memory path status check
- Added documents path status check
- Added vector database path status check

---

### v1.1 — Agent Planning Orchestrator

Status: Done

Implemented:

- Added `/agent/plan`
- Added agent folder
- Added agent schemas
- Added `AgentOrchestrator`
- Added intent routing
- Added routing for system info
- Added routing for command planning
- Added routing for codebase analysis
- Added routing for document search
- Added routing for memory search
- Added fallback routing to normal chat
- Fixed false command detection for Turkish words such as `nedir`

---

## Planned Roadmap

### v1.2 — Agent Execution Layer

Planned:

- Execute planned tool routes
- Add `/agent/execute`
- Call internal tools based on planner output
- Return unified response objects
- Add safer execution flow
- Preserve confirmation requirements for risky commands

---

### v1.3 — Project-Specific Modules

Planned:

- Game development helper module
- ASP.NET Core analyzer module
- Flutter project analyzer module
- SQL database inspector module
- Vionefit-specific module

---

### v1.4 — UI Layer

Planned:

- Local web UI
- Chat interface
- Memory viewer
- Document manager
- Command approval panel
- Project analysis panel

---

### v1.5 — Voice Layer

Planned:

- Voice input
- Voice output
- Wake word
- Local speech-to-text
- Local text-to-speech

---

## Future Ideas

Possible future additions:

- n8n automation
- Home Assistant integration
- LoRA fine-tuning
- Multi-model routing
- Local desktop UI
- Mobile companion app
- SQL Server integration
- GitHub automation
- Project task planning agent

---

## Current Limitations

Hex.ai is still an early local assistant backend.

Current limitations:

- No autonomous agent loop yet
- No full tool-calling orchestration yet
- `/agent/plan` only plans routes; it does not execute them yet
- No voice system yet
- No UI except Swagger
- No authentication yet
- No multi-user support
- No production deployment setup yet
- Semantic search currently uses SQLite-stored embeddings instead of a dedicated vector database
- RAG ranking is simple and will need improvement
- System-level destructive commands are blocked from API execution
- Confirmed raw command execution still needs stronger logging and audit controls

---

## Development Notes

Current development strategy:

```text
Build small working systems first.
Test every module through Swagger.
Commit every stable step.
Keep private data out of GitHub.
Add more autonomy only after safety layers are working.
```

---

## License

This project is currently private and personal.

A license can be added later if the project becomes public.