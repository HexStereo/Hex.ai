# Hex.ai

Hex.ai is a local-first personal AI assistant project.

The goal of Hex.ai is to build a private, modular, extensible AI system that runs on a personal computer, uses local language models, stores user-defined memory, reads local project documents, analyzes codebases, and performs controlled tool-based actions.

Hex.ai is being developed as a personal AI assistant system, not just a chatbot.

Current version: **v1.6.0**

---

## Core Principles

Hex.ai is designed around the following principles:

- **Local-first:** The system is intended to run on the user's own machine.
- **Private by default:** Private files, memory databases, vector stores, and local documents should stay local.
- **Modular architecture:** Chat, memory, documents, tools, command execution, codebase analysis, and agent orchestration are separated into modules.
- **Explicit safety boundaries:** Risky or destructive actions require explicit confirmation or are blocked.
- **Developer-oriented workflow:** The system is built to support programming, debugging, project analysis, documentation, and controlled automation.
- **Extensible by design:** New tools, model providers, databases, and agent skills can be added later.

---

## Current Backend Stack

Hex.ai currently uses:

- **Python**
- **FastAPI**
- **Uvicorn**
- **Ollama**
- **qwen2.5-coder:14b** as the default local LLM
- **nomic-embed-text** for local embeddings
- **SQLite** for memory, command audit logs, agent traces, and document metadata
- **Local file-based document ingestion**
- **Hybrid RAG search**
- **Controlled command execution**
- **Codebase analysis tools**
- **Swagger UI** for manual API testing

---

## Current Status

Hex.ai v1.6.0 includes:

- Local chat endpoint
- SQLite-backed memory system
- Local document ingestion
- Local embedding creation through Ollama
- RAG-based document search
- Hybrid document search using semantic and keyword scoring
- Document source metadata tracking
- Duplicate document ingestion prevention
- Codebase file listing
- Codebase analysis
- File read/list tools
- System info endpoint
- Command planning
- Safe command execution
- Confirmed command execution
- Command audit history
- Agent planning
- Agent execution
- Agent confirmed execution
- Agent trace history
- Safety rules for local commands
- GitHub-safe project structure

---

## Important Security Notes

Hex.ai is designed to operate on local files and local system commands, so security is a core part of the project.

The current rules are:

- Private data should not be committed to GitHub.
- Local memory databases should not be committed.
- Vector databases should not be committed.
- Local documents should not be committed.
- `.env` should not be committed.
- Dangerous commands should require explicit confirmation.
- System-level destructive commands should be blocked from API execution.
- Commands that modify files should be audited.
- Command execution should stay inside the project directory unless explicitly allowed by safe rules.
- The assistant should not silently execute risky commands.

Examples of sensitive local data:

```text
data/
.env
*.db
*.sqlite
*.sqlite3
local documents
memory files
private notes
logs containing private paths or private information
```

---

## Project Structure

Current project structure:

```text
Hex.ai/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── executor.py
│   │   │   ├── orchestrator.py
│   │   │   ├── trace_store.py
│   │   │   └── __init__.py
│   │   ├── codebase/
│   │   │   ├── codebase_tools.py
│   │   │   └── __init__.py
│   │   ├── llm/
│   │   │   ├── ollama_client.py
│   │   │   └── __init__.py
│   │   ├── memory/
│   │   │   ├── memory_store.py
│   │   │   └── __init__.py
│   │   ├── rag/
│   │   │   ├── document_store.py
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   ├── command.py
│   │   │   ├── document.py
│   │   │   └── __init__.py
│   │   ├── system/
│   │   │   ├── diagnostics.py
│   │   │   └── __init__.py
│   │   ├── tools/
│   │   │   ├── command_tools.py
│   │   │   ├── file_tools.py
│   │   │   └── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   └── __init__.py
│   └── requirements.txt
├── data/
│   ├── documents/
│   ├── memory/
│   └── vector_db/
├── scripts/
├── .env.example
├── .gitignore
└── README.md
```

The `data/` directory is local-only and should not be committed to GitHub.

---

## Local Models

Hex.ai currently expects Ollama to be installed and running locally.

Current default model:

```text
qwen2.5-coder:14b
```

Current embedding model:

```text
nomic-embed-text
```

Required Ollama models:

```cmd
ollama pull qwen2.5-coder:14b
ollama pull nomic-embed-text
```

To verify installed models:

```cmd
ollama list
```

To test embeddings manually:

```cmd
curl http://localhost:11434/api/embeddings -d "{\"model\":\"nomic-embed-text\",\"prompt\":\"Hex.ai is a local-first personal AI assistant.\"}"
```

---

## Setup

### 1. Clone the repository

```cmd
git clone https://github.com/HexStereo/Hex.ai.git
cd Hex.ai
```

### 2. Create a virtual environment

```cmd
cd backend
python -m venv .venv
```

### 3. Activate the virtual environment

```cmd
.venv\Scripts\activate
```

### 4. Install dependencies

```cmd
pip install -r requirements.txt
```

### 5. Start the backend

```cmd
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### 6. Open Swagger UI

```text
http://127.0.0.1:8010/docs
```

---

## Environment Configuration

Hex.ai uses `.env` for local configuration.

Do not commit `.env`.

Use `.env.example` as a safe public template.

Example:

```env
HEXAI_APP_NAME=Hex.ai
HEXAI_ENV=development
HEXAI_VERSION=1.6.0

HEXAI_PROJECT_ROOT=C:\Projects\Hex.ai

HEXAI_DEFAULT_MODEL=qwen2.5-coder:14b
HEXAI_EMBEDDING_MODEL=nomic-embed-text
HEXAI_OLLAMA_BASE_URL=http://localhost:11434

HEXAI_MEMORY_DB_PATH=data/memory/hexai_memory.db
HEXAI_DOCUMENTS_PATH=data/documents
HEXAI_VECTOR_DB_PATH=data/vector_db
```

---

## API Overview

Swagger UI is available at:

```text
http://127.0.0.1:8010/docs
```

---

## System Endpoints

### GET `/`

Basic health check.

Expected result:

```json
{
  "app": "Hex.ai",
  "status": "running"
}
```

### GET `/system/info`

Returns current system status, version, model names, and local path checks.

Expected important fields:

```json
{
  "app_name": "Hex.ai",
  "app_env": "development",
  "version": "1.6.0",
  "project_root": "C:\\Projects\\Hex.ai",
  "default_model": "qwen2.5-coder:14b",
  "embedding_model": "nomic-embed-text"
}
```

---

## Chat Endpoint

### POST `/chat`

Sends a message to Hex.ai.

Example request:

```json
{
  "message": "Hex.ai nedir?",
  "model": "qwen2.5-coder:14b",
  "use_memory": true,
  "use_documents": true
}
```

Expected response fields:

```json
{
  "model": "qwen2.5-coder:14b",
  "response": "...",
  "memory_used": 5,
  "documents_used": 5
}
```

The chat endpoint can use:

- Direct LLM response
- SQLite memory context
- Local document context through RAG

---

## Memory System

Hex.ai includes a SQLite-backed memory system.

Memory is stored locally.

Memory database path:

```text
data/memory/hexai_memory.db
```

Memory should not be committed to GitHub.

The memory system is used to provide persistent local context to the assistant.

---

## Document RAG System

Hex.ai v1.6.0 includes an improved document retrieval system.

Documents are stored locally in:

```text
data/documents
```

Supported document extensions:

```text
.cs
.css
.html
.js
.json
.md
.py
.sql
.ts
.txt
```

---

## Document Ingestion

### POST `/documents/ingest`

Reads supported files from `data/documents`, chunks them, creates embeddings, and stores metadata.

Expected first ingestion result:

```json
{
  "files_processed": 5,
  "files_skipped": 0,
  "files_refreshed": 0,
  "chunks_created": 5,
  "embeddings_created": 5,
  "embedding_model": "nomic-embed-text"
}
```

Expected second ingestion result without file changes:

```json
{
  "files_processed": 0,
  "files_skipped": 5,
  "files_refreshed": 0,
  "chunks_created": 0,
  "embeddings_created": 0,
  "embedding_model": "nomic-embed-text"
}
```

This confirms duplicate ingestion prevention.

---

## Document Source Tracking

### GET `/documents/sources`

Lists indexed document sources.

Example response fields:

```json
{
  "source_path": "rag_v16_test.md",
  "file_name": "rag_v16_test.md",
  "extension": ".md",
  "content_hash": "...",
  "size_bytes": 680,
  "chunk_count": 1,
  "embedding_model": "nomic-embed-text",
  "created_at": "2026-05-16 12:51:10",
  "updated_at": "2026-05-16 12:51:10"
}
```

v1.6.0 source tracking includes:

- Source path
- File name
- Extension
- Content hash
- File size
- Modified timestamp
- Chunk count
- Embedding model
- Created timestamp
- Updated timestamp

---

## Hybrid Document Search

### GET `/documents/search`

Searches local documents.

Example query:

```text
query = hybrid search security private by default
limit = 8
```

Expected important fields:

```json
{
  "query": "hybrid search security private by default",
  "search_type": "hybrid",
  "results": [
    {
      "source_path": "rag_v16_test.md",
      "chunk_index": 0,
      "content": "...",
      "content_preview": "...",
      "char_count": 638,
      "token_estimate": 160,
      "content_hash": "...",
      "embedding_model": "nomic-embed-text",
      "semantic_score": 0.492254,
      "keyword_score": 0.516667,
      "score": 0.49909,
      "score_type": "hybrid"
    }
  ]
}
```

Hybrid search combines:

- `semantic_score`
- `keyword_score`

The final score is calculated from both semantic similarity and keyword matching.

---

## Codebase Tools

Hex.ai includes codebase tools for reading and analyzing project files.

### GET `/tools/codebase/files`

Lists files inside the project codebase.

Example:

```text
path = backend/app
max_files = 25
```

### POST `/tools/codebase/analyze`

Analyzes selected codebase files.

Example request:

```json
{
  "path": "backend/app",
  "model": "qwen2.5-coder:14b",
  "max_files": 25,
  "max_chars_per_file": 2500,
  "max_total_chars": 30000,
  "focus": "Analyze Hex.ai backend architecture, module responsibilities, safety design, current capabilities, and next development steps."
}
```

The codebase analysis tool is useful for:

- Architecture review
- Module responsibility review
- Safety review
- Refactoring plans
- Development roadmap planning

---

## File Tools

Hex.ai includes local file tools.

### GET `/tools/files/list`

Lists files inside the project directory.

### GET `/tools/files/read`

Reads project-relative files.

The file tools are constrained by project safety rules.

Blocked examples:

```text
.env
../
data/memory
```

The system should not expose private memory databases, secrets, or paths outside the project safety boundary.

---

## Command Tools

Hex.ai includes controlled command tools.

### GET `/tools/commands/allowed`

Lists allowed command templates.

Examples:

```json
{
  "git_status": ["git", "status"],
  "git_log": ["git", "log", "--oneline", "--max-count=10"],
  "git_diff": ["git", "diff"],
  "python_version": ["python", "--version"],
  "pip_version": ["pip", "--version"],
  "pip_list": ["pip", "list"],
  "ollama_list": ["ollama", "list"]
}
```

### POST `/tools/commands/plan`

Plans a command and returns risk information.

Example:

```json
{
  "command": "git status",
  "cwd": "."
}
```

Expected safe result:

```json
{
  "command": "git status",
  "risk_level": "READ_ONLY",
  "requires_confirmation": false,
  "allowed_to_run": true
}
```

### POST `/tools/commands/run`

Runs allowed safe commands.

Example:

```json
{
  "command_key": "git_status",
  "cwd": "."
}
```

### POST `/tools/commands/run-confirmed`

Runs commands that require explicit confirmation.

Example:

```json
{
  "command": "echo Hex.ai command engine test > data\\documents\\command_test.txt",
  "cwd": ".",
  "confirmation_phrase": "I_CONFIRM_HEXAI_COMMAND"
}
```

### GET `/tools/commands/history`

Lists command audit history.

The command system records:

- Source
- Action
- Command text
- CWD
- Risk level
- Confirmation status
- Execution status
- Return code
- Timeout status
- stdout preview
- stderr preview

---

## Command Safety Model

Hex.ai command execution uses several risk levels.

Current command risk categories:

```text
READ_ONLY
LOW_RISK
MIXED_OR_CHAINED
SYSTEM_HIGH_RISK
BLOCKED
```

Read-only commands can run without confirmation.

Examples:

```text
git status
python --version
pip --version
ollama list
```

Commands with redirection, chaining, or file-writing behavior require explicit confirmation.

Examples:

```text
echo test > data\documents\test.txt
```

Dangerous system-level commands are blocked from API execution.

Examples:

```text
format C:
del
rmdir
shutdown
reg delete
diskpart
```

The system may still plan and explain risky commands, but it should not execute blocked commands through the API.

---

## Agent System

Hex.ai includes an agent layer that routes natural language requests to tools.

### POST `/agent/plan`

Plans which endpoint should handle a user request.

Example:

```json
{
  "message": "sistem durumunu kontrol et",
  "cwd": ".",
  "model": "qwen2.5-coder:14b"
}
```

Expected result:

```json
{
  "intent": "SYSTEM_INFO",
  "method": "GET",
  "endpoint": "/system/info",
  "requires_confirmation": false
}
```

### POST `/agent/execute`

Plans and executes safe requests.

Example:

```json
{
  "message": "dokümanlarda hybrid search ve güvenlik kurallarını ara",
  "cwd": ".",
  "model": "qwen2.5-coder:14b",
  "auto_execute_safe_commands": true
}
```

Expected result:

```json
{
  "intent": "DOCUMENT_SEARCH",
  "planned_method": "GET",
  "planned_endpoint": "/documents/search",
  "executed": true,
  "requires_confirmation": false,
  "result": {
    "search_type": "hybrid"
  }
}
```

### POST `/agent/execute-confirmed`

Executes commands that require explicit confirmation.

Example:

```json
{
  "message": "command: echo Hex.ai confirmed test > data\\documents\\confirmed_agent_test.txt",
  "cwd": ".",
  "model": "qwen2.5-coder:14b",
  "confirmation_phrase": "I_CONFIRM_HEXAI_COMMAND"
}
```

### GET `/agent/traces`

Lists agent traces.

Agent traces include:

- Trace ID
- Source
- Trace type
- Message
- Intent
- Confidence
- Planned method
- Planned endpoint
- Planned parameters
- Execution status
- Confirmation status
- Result summary
- Error message if any

---

## Agent Routing

The agent can currently route requests to:

```text
SYSTEM_INFO
COMMAND_PLAN
DOCUMENT_SEARCH
CODEBASE_ANALYSIS
CHAT
```

Examples:

```text
"sistem durumunu kontrol et" -> /system/info
"git status komutunu planla" -> /tools/commands/plan
"dokümanlarda güvenlik kurallarını ara" -> /documents/search
"backend/app kod tabanını analiz et" -> /tools/codebase/analyze
"Hex.ai nedir?" -> /chat
```

---

## v1.6.0 Improvements

v1.6.0 focuses on improving the document RAG system.

Main improvements:

- Document source metadata table added
- Content hash tracking added
- Duplicate ingestion prevention added
- Changed file refresh behavior added
- Document chunks now store metadata
- Hybrid search added
- Search results now include semantic and keyword scores
- Search result metadata improved
- Agent document search now consistently reports `hybrid`
- Document paths now resolve correctly from project root
- RAG database separated from normal memory database
- SQLite migration order fixed
- Index creation moved after migration
- System info reports v1.6.0

---

## Tested v1.6.0 Behavior

The following tests were completed successfully:

### System Info

```text
GET /system/info
```

Confirmed:

```json
"version": "1.6.0"
```

### First Document Ingestion

```text
POST /documents/ingest
```

Confirmed:

```json
"files_processed": 5
"chunks_created": 5
"embeddings_created": 5
```

### Duplicate Ingestion Prevention

```text
POST /documents/ingest
```

Confirmed on second run:

```json
"files_processed": 0
"files_skipped": 5
"chunks_created": 0
"embeddings_created": 0
```

### Document Sources

```text
GET /documents/sources
```

Confirmed:

```json
"count": 5
```

### Hybrid Search

```text
GET /documents/search
```

Confirmed:

```json
"search_type": "hybrid"
"score_type": "hybrid"
```

### Chat With Documents

```text
POST /chat
```

Confirmed:

```json
"documents_used": 5
"memory_used": 5
```

### Agent Document Search

```text
POST /agent/execute
```

Confirmed:

```json
"intent": "DOCUMENT_SEARCH"
"planned_endpoint": "/documents/search"
"executed": true
"requires_confirmation": false
"search_type": "hybrid"
```

---

## GitHub Safety

Before committing, always check:

```cmd
git status
```

Do not commit:

```text
data/
.env
*.db
*.sqlite
*.sqlite3
private documents
local memory
local vector stores
local logs containing private data
```

Safe files to commit usually include:

```text
backend/app/**/*.py
backend/requirements.txt
README.md
.env.example
.gitignore
scripts/
```

Example commit flow:

```cmd
cd /d C:\Projects\Hex.ai
git status
git add backend\app README.md .env.example .gitignore
git reset data
git commit -m "Improve RAG indexing and hybrid document search"
git push
```

After pushing:

```cmd
git status
```

Expected:

```text
nothing to commit, working tree clean
```

---

## Development Roadmap

### v1.7.0 — Conversation and Session System

Planned next step:

- Add conversation sessions
- Add session IDs
- Store chat history by session
- Retrieve previous messages by session
- Add conversation list endpoint
- Add conversation detail endpoint
- Add message history endpoint
- Improve context construction
- Separate memory from conversation history
- Allow document-aware conversation continuity

### Later Versions

Possible future features:

- User profile memory
- Long-term memory management UI
- Tool permission profiles
- Stronger command sandboxing
- Voice assistant mode
- Speech-to-text
- Text-to-speech
- SQL database connectors
- Project-specific workspaces
- File editing tools
- Code editing tools
- Task planning
- Local desktop app
- Mobile companion app
- Stronger local models
- Multi-model routing
- External API provider support
- Local vector database upgrade
- Plugin system
- Agent skill registry

---

## Development Philosophy

Hex.ai should evolve from a simple local chatbot into a personal operating layer for the user’s computer.

The long-term goal is not only to answer questions, but to:

- Understand local projects
- Search local documents
- Remember user-defined information
- Analyze code
- Plan technical steps
- Execute safe commands
- Ask for confirmation before risky actions
- Keep private data local
- Become a modular personal AI assistant

Hex.ai is built step by step, with each version adding one controlled capability at a time.

---

## License

No public license has been selected yet.

Until a license is added, all rights are reserved by the project owner.

---

## Owner

Hex.ai is owned and developed by Arda Bilen.

Project name:

```text
Hex.ai
```