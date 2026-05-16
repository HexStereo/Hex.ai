from typing import Any

from fastapi.encoders import jsonable_encoder

from app.agent.orchestrator import AgentOrchestrator
from app.audit.audit_store import CommandAuditStore
from app.audit.trace_store import AgentTraceStore
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
        command_audit_store: CommandAuditStore,
        agent_trace_store: AgentTraceStore,
    ):
        self.orchestrator = orchestrator
        self.ollama_client = ollama_client
        self.memory_store = memory_store
        self.document_store = document_store
        self.codebase_tools = codebase_tools
        self.command_tools = command_tools
        self.system_diagnostics = system_diagnostics
        self.command_audit_store = command_audit_store
        self.agent_trace_store = agent_trace_store

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
            audit_record = self.command_audit_store.record_command_event(
                source="agent",
                action="execute",
                command_text=command,
                cwd=cwd,
                command_plan=command_plan,
                executed=False,
                reason="Command is not allowed to run through the Hex.ai API.",
                warnings=command_plan["warnings"],
                confirmation_provided=False,
            )

            return {
                "executed": False,
                "requires_confirmation": command_plan["requires_confirmation"],
                "command_plan": command_plan,
                "result": None,
                "audit_record": audit_record,
                "reason": "Command is not allowed to run through the Hex.ai API.",
                "warnings": command_plan["warnings"],
            }

        if command_plan["requires_confirmation"]:
            audit_record = self.command_audit_store.record_command_event(
                source="agent",
                action="execute",
                command_text=command,
                cwd=cwd,
                command_plan=command_plan,
                executed=False,
                reason="Command requires explicit confirmation before execution.",
                warnings=command_plan["warnings"],
                confirmation_provided=False,
            )

            return {
                "executed": False,
                "requires_confirmation": True,
                "command_plan": command_plan,
                "result": None,
                "audit_record": audit_record,
                "reason": "Command requires explicit confirmation before execution.",
                "warnings": command_plan["warnings"],
            }

        if not auto_execute_safe_commands:
            audit_record = self.command_audit_store.record_command_event(
                source="agent",
                action="execute",
                command_text=command,
                cwd=cwd,
                command_plan=command_plan,
                executed=False,
                reason="Command is safe, but automatic command execution is disabled for this request.",
                warnings=command_plan["warnings"],
                confirmation_provided=False,
            )

            return {
                "executed": False,
                "requires_confirmation": False,
                "command_plan": command_plan,
                "result": None,
                "audit_record": audit_record,
                "reason": "Command is safe, but automatic command execution is disabled for this request.",
                "warnings": command_plan["warnings"],
            }

        command_result = self.command_tools.run_confirmed_command(
            command=command,
            cwd=cwd,
            confirmation_phrase=None,
        )

        audit_record = self.command_audit_store.record_command_event(
            source="agent",
            action="execute",
            command_text=command,
            cwd=cwd,
            command_plan=command_plan,
            command_result=command_result,
            executed=True,
            reason="Safe command executed automatically.",
            warnings=command_plan["warnings"],
            confirmation_provided=False,
        )

        return {
            "executed": True,
            "requires_confirmation": False,
            "command_plan": command_plan,
            "result": command_result,
            "audit_record": audit_record,
            "reason": "Safe command executed automatically.",
            "warnings": command_plan["warnings"],
        }

    def _execute_confirmed_command(
        self,
        parameters: dict,
        confirmation_phrase: str | None,
    ) -> dict:
        command = parameters.get("command", "")
        cwd = parameters.get("cwd", ".")

        command_plan = self.command_tools.plan_command(
            command=command,
            cwd=cwd,
        )

        if not command_plan["allowed_to_run"]:
            audit_record = self.command_audit_store.record_command_event(
                source="agent",
                action="execute_confirmed",
                command_text=command,
                cwd=cwd,
                command_plan=command_plan,
                executed=False,
                reason="Command is not allowed to run through the Hex.ai API.",
                warnings=command_plan["warnings"],
                confirmation_provided=confirmation_phrase is not None,
            )

            return {
                "executed": False,
                "requires_confirmation": command_plan["requires_confirmation"],
                "command_plan": command_plan,
                "result": None,
                "audit_record": audit_record,
                "reason": "Command is not allowed to run through the Hex.ai API.",
                "warnings": command_plan["warnings"],
            }

        if command_plan["requires_confirmation"] and not confirmation_phrase:
            audit_record = self.command_audit_store.record_command_event(
                source="agent",
                action="execute_confirmed",
                command_text=command,
                cwd=cwd,
                command_plan=command_plan,
                executed=False,
                reason=(
                    "Command requires explicit confirmation. "
                    f"Required phrase: {command_plan.get('confirmation_phrase')}"
                ),
                warnings=command_plan["warnings"],
                confirmation_provided=False,
            )

            return {
                "executed": False,
                "requires_confirmation": True,
                "command_plan": command_plan,
                "result": None,
                "audit_record": audit_record,
                "reason": (
                    "Command requires explicit confirmation. "
                    f"Required phrase: {command_plan.get('confirmation_phrase')}"
                ),
                "warnings": command_plan["warnings"],
            }

        required_phrase = command_plan.get("confirmation_phrase")

        if command_plan["requires_confirmation"] and confirmation_phrase != required_phrase:
            audit_record = self.command_audit_store.record_command_event(
                source="agent",
                action="execute_confirmed",
                command_text=command,
                cwd=cwd,
                command_plan=command_plan,
                executed=False,
                reason="Invalid confirmation phrase.",
                warnings=command_plan["warnings"],
                confirmation_provided=True,
            )

            return {
                "executed": False,
                "requires_confirmation": True,
                "command_plan": command_plan,
                "result": None,
                "audit_record": audit_record,
                "reason": "Invalid confirmation phrase.",
                "warnings": command_plan["warnings"],
            }

        command_result = self.command_tools.run_confirmed_command(
            command=command,
            cwd=cwd,
            confirmation_phrase=confirmation_phrase,
        )

        audit_record = self.command_audit_store.record_command_event(
            source="agent",
            action="execute_confirmed",
            command_text=command,
            cwd=cwd,
            command_plan=command_plan,
            command_result=command_result,
            executed=True,
            reason="Confirmed command executed.",
            warnings=command_plan["warnings"],
            confirmation_provided=confirmation_phrase is not None,
        )

        return {
            "executed": True,
            "requires_confirmation": False,
            "command_plan": command_plan,
            "result": command_result,
            "audit_record": audit_record,
            "reason": "Confirmed command executed.",
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

    def _record_trace_and_build_response(
        self,
        trace_type: str,
        message: str,
        cwd: str,
        model: str | None,
        plan: dict,
        executed: bool,
        requires_confirmation: bool,
        result: Any,
        reason: str,
        warnings: list[str],
    ) -> dict:
        trace_record = self.agent_trace_store.record_trace(
            source="agent",
            trace_type=trace_type,
            message=message,
            cwd=cwd,
            model=model or settings.DEFAULT_MODEL,
            plan=plan,
            executed=executed,
            requires_confirmation=requires_confirmation,
            result=result,
            reason=reason,
            warnings=warnings,
        )

        return {
            "trace_id": trace_record["id"],
            "message": plan["message"],
            "intent": plan["intent"],
            "confidence": plan["confidence"],
            "planned_method": plan["method"],
            "planned_endpoint": plan["endpoint"],
            "planned_parameters": plan["parameters"],
            "executed": executed,
            "requires_confirmation": requires_confirmation,
            "result": self._safe_result(result),
            "reason": reason,
            "warnings": warnings,
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
                "audit_record": command_execution["audit_record"],
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

        return self._record_trace_and_build_response(
            trace_type="execute",
            message=message,
            cwd=cwd,
            model=model,
            plan=plan,
            executed=executed,
            requires_confirmation=requires_confirmation,
            result=result,
            reason=reason,
            warnings=warnings,
        )

    def execute_confirmed(
        self,
        message: str,
        cwd: str = ".",
        model: str | None = None,
        confirmation_phrase: str | None = None,
    ) -> dict:
        plan = self.orchestrator.plan(
            message=message,
            cwd=cwd,
            model=model,
        )

        intent = plan["intent"]
        parameters = plan["parameters"]
        warnings = list(plan["warnings"])

        if intent != "COMMAND_PLAN":
            warnings.append("Confirmed execution is only available for command planning intents.")

            return self._record_trace_and_build_response(
                trace_type="execute_confirmed",
                message=message,
                cwd=cwd,
                model=model,
                plan=plan,
                executed=False,
                requires_confirmation=False,
                result=None,
                reason="This request was not routed as a command, so confirmed execution was not performed.",
                warnings=warnings,
            )

        command_execution = self._execute_confirmed_command(
            parameters=parameters,
            confirmation_phrase=confirmation_phrase,
        )

        warnings.extend(command_execution["warnings"])

        result = {
            "command_plan": command_execution["command_plan"],
            "command_result": command_execution["result"],
            "audit_record": command_execution["audit_record"],
        }

        return self._record_trace_and_build_response(
            trace_type="execute_confirmed",
            message=message,
            cwd=cwd,
            model=model,
            plan=plan,
            executed=command_execution["executed"],
            requires_confirmation=command_execution["requires_confirmation"],
            result=result,
            reason=command_execution["reason"],
            warnings=warnings,
        )