from typing import Any

from fastapi.encoders import jsonable_encoder

from app.agent.orchestrator import AgentOrchestrator
from app.config import settings
from app.llm.ollama_client import OllamaClient
from app.memory.memory_store import MemoryStore
from app.rag.document_store import DocumentStore
from app.system.diagnostics import SystemDiagnostics
from app.tools.codebase_tools import CodebaseTools
from app.tools.command_tools import CommandTools


class AgentExecutor:
    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        ollama_client: OllamaClient,
        memory_store: MemoryStore,
        document_store: DocumentStore,
        codebase_tools: CodebaseTools,
        command_tools: CommandTools,
        system_diagnostics: SystemDiagnostics,
    ):
        self.orchestrator = orchestrator
        self.ollama_client = ollama_client
        self.memory_store = memory_store
        self.document_store = document_store
        self.codebase_tools = codebase_tools
        self.command_tools = command_tools
        self.system_diagnostics = system_diagnostics

    def _safe_result(self, value: Any) -> Any:
        return jsonable_encoder(value)

    def _execute_system_info(self) -> dict:
        return self.system_diagnostics.get_system_info()

    def _execute_command_plan(
        self,
        parameters: dict,
        auto_execute_safe_commands: bool,
    ) -> dict:
        command = parameters.get("command", "")
        cwd = parameters.get("cwd", ".")

        command_plan = self.command_tools.plan_command(
            command=command,
            cwd=cwd,
        )

        if not command_plan["allowed_to_run"]:
            return {
                "executed": False,
                "requires_confirmation": command_plan["requires_confirmation"],
                "command_plan": command_plan,
                "result": None,
                "reason": "Command is not allowed to run through the Hex.ai API.",
                "warnings": command_plan["warnings"],
            }

        if command_plan["requires_confirmation"]:
            return {
                "executed": False,
                "requires_confirmation": True,
                "command_plan": command_plan,
                "result": None,
                "reason": "Command requires explicit confirmation before execution.",
                "warnings": command_plan["warnings"],
            }

        if not auto_execute_safe_commands:
            return {
                "executed": False,
                "requires_confirmation": False,
                "command_plan": command_plan,
                "result": None,
                "reason": "Command is safe, but automatic command execution is disabled for this request.",
                "warnings": command_plan["warnings"],
            }

        command_result = self.command_tools.run_confirmed_command(
            command=command,
            cwd=cwd,
            confirmation_phrase=None,
        )

        return {
            "executed": True,
            "requires_confirmation": False,
            "command_plan": command_plan,
            "result": command_result,
            "reason": "Safe command executed automatically.",
            "warnings": command_plan["warnings"],
        }

    def _execute_codebase_analysis(self, parameters: dict) -> dict:
        context = self.codebase_tools.collect_code_context(
            input_path=parameters.get("path", "."),
            max_files=parameters.get("max_files", 25),
            max_chars_per_file=parameters.get("max_chars_per_file", 2500),
            max_total_chars=parameters.get("max_total_chars", 30000),
        )

        analysis_prompt = self.codebase_tools.build_analysis_prompt(
            code_context=context,
            focus=parameters.get("focus", "Analyze this codebase."),
        )

        response_text = self.ollama_client.generate(
            prompt=analysis_prompt,
            model=parameters.get("model") or settings.DEFAULT_MODEL,
            memories=[],
            documents=[],
        )

        return {
            "model": parameters.get("model") or settings.DEFAULT_MODEL,
            "path": context["path"],
            "files_analyzed": context["file_count"],
            "total_chars": context["total_chars"],
            "files": context["files"],
            "response": response_text,
        }

    def _execute_document_search(self, parameters: dict) -> dict:
        query = parameters.get("query", "")
        limit = parameters.get("limit", 8)

        query_embedding = None
        search_type = "keyword"

        try:
            query_embedding = self.ollama_client.embed(query)
            search_type = "semantic"
        except RuntimeError:
            query_embedding = None
            search_type = "keyword"

        results = self.document_store.get_document_context(
            query=query,
            query_embedding=query_embedding,
            limit=limit,
        )

        return {
            "query": query,
            "search_type": search_type,
            "results": results,
        }

    def _execute_memory_search(self, parameters: dict) -> dict:
        query = parameters.get("query", "")
        limit = parameters.get("limit", 10)

        results = self.memory_store.search_memories(
            query=query,
            limit=limit,
        )

        return {
            "query": query,
            "results": results,
        }

    def _execute_chat(self, parameters: dict) -> dict:
        message = parameters.get("message", "")
        model = parameters.get("model") or settings.DEFAULT_MODEL
        use_memory = parameters.get("use_memory", True)
        use_documents = parameters.get("use_documents", True)

        memories = []
        documents = []
        query_embedding = None

        if use_memory:
            memories = self.memory_store.get_memory_context(
                query=message,
                limit=8,
            )

        if use_documents:
            try:
                query_embedding = self.ollama_client.embed(message)
            except RuntimeError:
                query_embedding = None

            documents = self.document_store.get_document_context(
                query=message,
                query_embedding=query_embedding,
                limit=5,
            )

        response_text = self.ollama_client.generate(
            prompt=message,
            model=model,
            memories=memories,
            documents=documents,
        )

        return {
            "model": model,
            "response": response_text,
            "memory_used": len(memories),
            "documents_used": len(documents),
        }

    def execute(
        self,
        message: str,
        cwd: str = ".",
        model: str | None = None,
        auto_execute_safe_commands: bool = True,
    ) -> dict:
        plan = self.orchestrator.plan(
            message=message,
            cwd=cwd,
            model=model,
        )

        intent = plan["intent"]
        parameters = plan["parameters"]

        executed = False
        requires_confirmation = plan["requires_confirmation"]
        result = None
        reason = plan["reason"]
        warnings = list(plan["warnings"])

        if intent == "INVALID":
            executed = False
            result = None
            reason = "Invalid request cannot be executed."

        elif intent == "SYSTEM_INFO":
            executed = True
            result = self._execute_system_info()
            reason = "System diagnostics executed."

        elif intent == "COMMAND_PLAN":
            command_execution = self._execute_command_plan(
                parameters=parameters,
                auto_execute_safe_commands=auto_execute_safe_commands,
            )

            executed = command_execution["executed"]
            requires_confirmation = command_execution["requires_confirmation"]
            result = {
                "command_plan": command_execution["command_plan"],
                "command_result": command_execution["result"],
            }
            reason = command_execution["reason"]
            warnings.extend(command_execution["warnings"])

        elif intent == "CODEBASE_ANALYSIS":
            executed = True
            result = self._execute_codebase_analysis(parameters)
            reason = "Codebase analysis executed."

        elif intent == "DOCUMENT_SEARCH":
            executed = True
            result = self._execute_document_search(parameters)
            reason = "Document search executed."

        elif intent == "MEMORY_SEARCH":
            executed = True
            result = self._execute_memory_search(parameters)
            reason = "Memory search executed."

        elif intent == "CHAT":
            executed = True
            result = self._execute_chat(parameters)
            reason = "Chat executed."

        else:
            executed = False
            result = None
            reason = f"Unknown intent '{intent}' cannot be executed."
            warnings.append("The planner returned an unsupported intent.")

        return {
            "message": plan["message"],
            "intent": intent,
            "confidence": plan["confidence"],
            "planned_method": plan["method"],
            "planned_endpoint": plan["endpoint"],
            "planned_parameters": parameters,
            "executed": executed,
            "requires_confirmation": requires_confirmation,
            "result": self._safe_result(result),
            "reason": reason,
            "warnings": warnings,
        }