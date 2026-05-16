import re


class AgentOrchestrator:
    def __init__(self, default_model: str):
        self.default_model = default_model

    def _normalize(self, message: str) -> str:
        return message.strip().lower()

    def _word_pattern(self, keyword: str) -> str:
        return rf"(?<![\wçğıöşüÇĞİÖŞÜ]){re.escape(keyword)}(?![\wçğıöşüÇĞİÖŞÜ])"

    def _contains_any(self, message: str, keywords: list[str]) -> bool:
        normalized = self._normalize(message)

        for keyword in keywords:
            keyword = keyword.strip().lower()

            if not keyword:
                continue

            if " " in keyword or "/" in keyword:
                if keyword in normalized:
                    return True

                continue

            if re.search(self._word_pattern(keyword), normalized, flags=re.IGNORECASE):
                return True

        return False

    def _command_appears_in_message(self, normalized_message: str, command: str) -> bool:
        command = command.strip().lower()

        if not command:
            return False

        command_pattern = re.escape(command)
        command_pattern = command_pattern.replace(r"\ ", r"\s+")

        pattern = rf"(?<![\wçğıöşüÇĞİÖŞÜ]){command_pattern}(?![\wçğıöşüÇĞİÖŞÜ])"

        return re.search(pattern, normalized_message, flags=re.IGNORECASE) is not None

    def _extract_command(self, message: str) -> str | None:
        command_pattern = re.search(
            r"(?:komut|command|cmd|terminal|çalıştır|calistir|run)\s*:\s*(.+)",
            message,
            flags=re.IGNORECASE,
        )

        if command_pattern:
            return command_pattern.group(1).strip()

        known_commands = [
            "python --version",
            "python -m pytest",
            "dotnet --version",
            "dotnet build",
            "dotnet test",
            "git status",
            "git diff",
            "git log",
            "git branch",
            "git remote -v",
            "pip --version",
            "pip list",
            "pip install",
            "ollama list",
            "npm install",
            "npm test",
            "npm run",
            "pytest",
            "tree",
            "dir",
        ]

        normalized = self._normalize(message)

        for command in known_commands:
            if self._command_appears_in_message(normalized, command):
                return command

        return None

    def _extract_codebase_path(self, message: str) -> str:
        normalized = self._normalize(message)

        known_paths = [
            "backend/app",
            "backend",
            "scripts",
            ".",
        ]

        for path in known_paths:
            if path in normalized:
                return path

        if "backend" in normalized:
            return "backend/app"

        return "."

    def plan(self, message: str, cwd: str = ".", model: str | None = None) -> dict:
        normalized = self._normalize(message)
        selected_model = model or self.default_model

        if not normalized:
            return {
                "message": message,
                "intent": "INVALID",
                "confidence": 1.0,
                "method": "NONE",
                "endpoint": "",
                "parameters": {},
                "requires_confirmation": False,
                "reason": "The message is empty.",
                "warnings": [
                    "Empty messages cannot be routed."
                ],
            }

        if self._contains_any(
            normalized,
            [
                "sistem durumu",
                "system info",
                "system status",
                "diagnostics",
                "diagnostic",
                "ollama durumu",
                "model listesi",
                "kurulu modeller",
                "backend durumu",
            ],
        ):
            return {
                "message": message,
                "intent": "SYSTEM_INFO",
                "confidence": 0.95,
                "method": "GET",
                "endpoint": "/system/info",
                "parameters": {},
                "requires_confirmation": False,
                "reason": "The message asks for system, backend, Ollama, or model status.",
                "warnings": [],
            }

        command = self._extract_command(message)

        if command is not None or self._contains_any(
            normalized,
            [
                "komut",
                "komutu",
                "komutunu",
                "komutları",
                "command",
                "terminal",
                "cmd",
                "çalıştır",
                "calistir",
                "run",
            ],
        ):
            return {
                "message": message,
                "intent": "COMMAND_PLAN",
                "confidence": 0.9 if command else 0.65,
                "method": "POST",
                "endpoint": "/tools/commands/plan",
                "parameters": {
                    "command": command or message,
                    "cwd": cwd,
                },
                "requires_confirmation": False,
                "reason": "The message appears to request command planning or terminal-related work.",
                "warnings": [
                    "This only plans the command. Execution may require confirmation depending on risk level."
                ],
            }

        if self._contains_any(
            normalized,
            [
                "kod tabanı",
                "kod tabanını",
                "codebase",
                "kodları analiz",
                "projeyi analiz",
                "backend analiz",
                "mimari analiz",
                "architecture",
                "module responsibilities",
            ],
        ):
            codebase_path = self._extract_codebase_path(message)

            return {
                "message": message,
                "intent": "CODEBASE_ANALYSIS",
                "confidence": 0.88,
                "method": "POST",
                "endpoint": "/tools/codebase/analyze",
                "parameters": {
                    "path": codebase_path,
                    "model": selected_model,
                    "max_files": 25,
                    "max_chars_per_file": 2500,
                    "max_total_chars": 30000,
                    "focus": message,
                },
                "requires_confirmation": False,
                "reason": "The message asks for codebase or architecture analysis.",
                "warnings": [
                    "Large codebase analysis may take longer depending on the local model."
                ],
            }

        if self._contains_any(
            normalized,
            [
                "doküman",
                "dokuman",
                "belge",
                "document",
                "documents",
                "rag",
                "ara",
                "search",
                "notlarda",
                "bilgilerde",
                "kaynaklarda",
            ],
        ):
            return {
                "message": message,
                "intent": "DOCUMENT_SEARCH",
                "confidence": 0.82,
                "method": "GET",
                "endpoint": "/documents/search",
                "parameters": {
                    "query": message,
                    "limit": 8,
                },
                "requires_confirmation": False,
                "reason": "The message appears to request searching local documents or RAG context.",
                "warnings": [],
            }

        if self._contains_any(
            normalized,
            [
                "hafıza",
                "hafiza",
                "memory",
                "hatırla",
                "hatirla",
                "ne biliyorsun",
                "kaydettiğin",
                "kaydedilen",
            ],
        ):
            return {
                "message": message,
                "intent": "MEMORY_SEARCH",
                "confidence": 0.8,
                "method": "GET",
                "endpoint": "/memory/search",
                "parameters": {
                    "query": message,
                    "limit": 10,
                },
                "requires_confirmation": False,
                "reason": "The message appears to ask about stored memory.",
                "warnings": [],
            }

        return {
            "message": message,
            "intent": "CHAT",
            "confidence": 0.7,
            "method": "POST",
            "endpoint": "/chat",
            "parameters": {
                "message": message,
                "model": selected_model,
                "use_memory": True,
                "use_documents": True,
            },
            "requires_confirmation": False,
            "reason": "No specialized tool intent was detected, so the message is routed to normal chat.",
            "warnings": [],
        }