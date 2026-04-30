"""持久记忆系统 - 支持跨会话记住用户偏好、项目和环境"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MemoryProvider(ABC):
    """记忆提供者抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """提供者名称"""

    @abstractmethod
    def is_available(self) -> bool:
        """返回提供者是否可用"""

    @abstractmethod
    def initialize(self, session_id: str, **kwargs) -> None:
        """初始化会话"""

    def system_prompt_block(self) -> str:
        """返回系统提示中的记忆块"""
        return ""

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """召回相关上下文"""
        return ""

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        """后台预取"""

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        """同步对话轮次"""

    @abstractmethod
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """返回工具模式"""

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        """处理工具调用"""
        raise NotImplementedError(f"Provider {self.name} does not handle tool {tool_name}")

    def shutdown(self) -> None:
        """关闭提供者"""

    def on_turn_start(self, turn_number: int, message: str, **kwargs) -> None:
        """每轮开始时调用"""

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        """会话结束时调用"""


class ProjectContext:
    """项目上下文类"""

    def __init__(self, project_id: str, name: str, path: str, **kwargs):
        self.project_id = project_id
        self.name = name
        self.path = path
        self.description = kwargs.get("description", "")
        self.tags = kwargs.get("tags", [])
        self.last_accessed = kwargs.get("last_accessed", datetime.now().isoformat())
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.metadata = kwargs.get("metadata", {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "tags": self.tags,
            "last_accessed": self.last_accessed,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectContext":
        return cls(
            project_id=data.get("project_id", ""),
            name=data.get("name", ""),
            path=data.get("path", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            last_accessed=data.get("last_accessed"),
            created_at=data.get("created_at"),
            metadata=data.get("metadata", {})
        )


class EnvironmentState:
    """环境状态类"""

    def __init__(self, **kwargs):
        self.variables = kwargs.get("variables", {})
        self.working_directory = kwargs.get("working_directory", "")
        self.platform = kwargs.get("platform", "")
        self.shell = kwargs.get("shell", "")
        self.session_history = kwargs.get("session_history", [])
        self.last_updated = kwargs.get("last_updated", datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables": self.variables,
            "working_directory": self.working_directory,
            "platform": self.platform,
            "shell": self.shell,
            "session_history": self.session_history[-50:],
            "last_updated": self.last_updated
        }

    def add_session_record(self, session_id: str, summary: str) -> None:
        self.session_history.append({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary[:200]
        })
        self.last_updated = datetime.now().isoformat()


class BuiltinMemoryProvider(MemoryProvider):
    """内置记忆提供者 - 使用文件系统存储"""

    def __init__(self):
        self._kronos_home = None
        self._memory_file = None
        self._user_file = None
        self._projects_file = None
        self._env_file = None
        self._memory_data = {}
        self._user_data = {}
        self._projects: Dict[str, ProjectContext] = {}
        self._env_state: Optional[EnvironmentState] = None
        self._current_session_id = ""
        self._turn_count = 0

    @property
    def name(self) -> str:
        return "builtin"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        self._current_session_id = session_id
        self._kronos_home = kwargs.get("kronos_home", str(Path.home() / ".kronos"))
        Path(self._kronos_home).mkdir(parents=True, exist_ok=True)
        
        self._memory_file = Path(self._kronos_home) / "MEMORY.json"
        self._user_file = Path(self._kronos_home) / "USER.json"
        self._projects_file = Path(self._kronos_home) / "PROJECTS.json"
        self._env_file = Path(self._kronos_home) / "ENVIRONMENT.json"
        
        self._load_memory()
        self._load_user()
        self._load_projects()
        self._load_environment()

    def _load_memory(self):
        if self._memory_file.exists():
            try:
                with open(self._memory_file, "r", encoding="utf-8") as f:
                    self._memory_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load memory file: {e}")
                self._memory_data = {}
        else:
            self._memory_data = {"entries": [], "session_summaries": {}}

    def _load_user(self):
        if self._user_file.exists():
            try:
                with open(self._user_file, "r", encoding="utf-8") as f:
                    self._user_data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load user file: {e}")
                self._user_data = {}
        else:
            self._user_data = {"preferences": {}, "projects": {}, "environment": {}}

    def _load_projects(self):
        if self._projects_file.exists():
            try:
                with open(self._projects_file, "r", encoding="utf-8") as f:
                    projects_data = json.load(f)
                    for pid, pdata in projects_data.items():
                        self._projects[pid] = ProjectContext.from_dict(pdata)
            except Exception as e:
                logger.warning(f"Failed to load projects file: {e}")

    def _load_environment(self):
        if self._env_file.exists():
            try:
                with open(self._env_file, "r", encoding="utf-8") as f:
                    env_data = json.load(f)
                    self._env_state = EnvironmentState(**env_data)
            except Exception as e:
                logger.warning(f"Failed to load environment file: {e}")
                self._env_state = EnvironmentState()
        else:
            self._env_state = EnvironmentState()

    def _save_memory(self):
        try:
            with open(self._memory_file, "w", encoding="utf-8") as f:
                json.dump(self._memory_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save memory file: {e}")

    def _save_user(self):
        try:
            with open(self._user_file, "w", encoding="utf-8") as f:
                json.dump(self._user_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save user file: {e}")

    def _save_projects(self):
        try:
            projects_data = {pid: pctx.to_dict() for pid, pctx in self._projects.items()}
            with open(self._projects_file, "w", encoding="utf-8") as f:
                json.dump(projects_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save projects file: {e}")

    def _save_environment(self):
        try:
            with open(self._env_file, "w", encoding="utf-8") as f:
                json.dump(self._env_state.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save environment file: {e}")

    def on_turn_start(self, turn_number: int, message: str, **kwargs) -> None:
        self._turn_count = turn_number
        working_dir = kwargs.get("working_directory", "")
        if working_dir and self._env_state:
            self._env_state.working_directory = working_dir
            self._env_state.last_updated = datetime.now().isoformat()

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if self._env_state:
            session_summary = self._generate_session_summary(messages)
            self._env_state.add_session_record(self._current_session_id, session_summary)
            self._save_environment()
        
        self._memory_data.setdefault("session_summaries", {})[self._current_session_id] = {
            "ended_at": datetime.now().isoformat(),
            "turn_count": self._turn_count,
            "summary": self._generate_session_summary(messages)
        }
        self._save_memory()

    def _generate_session_summary(self, messages: List[Dict[str, Any]]) -> str:
        if not messages:
            return "Empty session"
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        tool_calls = sum(1 for m in messages if m.get("tool_calls"))
        return f"Messages: {len(messages)}, Tools used: {tool_calls}, Chars: {total_chars}"

    def system_prompt_block(self) -> str:
        blocks = [
            "## Memory System",
            "You have access to persistent memory across sessions.",
            "Use the memory tool to store and retrieve information.",
            "",
            "Available memory types:",
            "- memory_add: Store important information with optional tags",
            "- memory_search: Search for relevant memories by content or tags",
            "- memory_list: List all stored memories",
            "",
        ]
        
        if self._projects:
            blocks.append("## Known Projects")
            for pid, proj in list(self._projects.items())[:5]:
                blocks.append(f"- {proj.name}: {proj.path}")
        
        if self._env_state and self._env_state.working_directory:
            blocks.append(f"\n## Current Working Directory")
            blocks.append(f"`{self._env_state.working_directory}`")
        
        return "\n".join(blocks)

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        parts = []
        query_lower = query.lower()
        
        relevant = self._search_entries(query_lower)
        if relevant:
            parts.append("[Relevant Memories]")
            for entry in relevant[:5]:
                parts.append(f"- [{entry.get('timestamp', '')}] {entry.get('content', '')[:100]}")
        
        related_projects = self._search_projects(query_lower)
        if related_projects:
            parts.append("\n[Related Projects]")
            for proj in related_projects[:3]:
                parts.append(f"- {proj.name}: {proj.description[:80]}")
        
        return "\n".join(parts) if parts else ""

    def _search_entries(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        entries = self._memory_data.get("entries", [])
        scored = []
        
        for entry in entries:
            content = entry.get("content", "").lower()
            tags = [t.lower() for t in entry.get("tags", [])]
            
            score = 0
            for word in query.split():
                if word in content:
                    score += content.count(word)
                if any(word in tag for tag in tags):
                    score += 3
            
            if score > 0:
                scored.append((score, entry))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:max_results]]

    def _search_projects(self, query: str) -> List[ProjectContext]:
        results = []
        for proj in self._projects.values():
            if (query in proj.name.lower() or 
                query in proj.description.lower() or
                any(query in tag.lower() for tag in proj.tags)):
                results.append(proj)
        return results

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or self._current_session_id,
            "user": user_content[:500],
            "assistant": assistant_content[:500],
            "tags": self._extract_tags_from_content(user_content + " " + assistant_content),
            "type": "conversation"
        }
        
        self._memory_data.setdefault("entries", []).append(entry)
        
        if len(self._memory_data["entries"]) > 1000:
            self._memory_data["entries"] = self._memory_data["entries"][-500:]
        
        self._save_memory()

    def _extract_tags_from_content(self, content: str) -> List[str]:
        tags = set()
        
        tech_patterns = [
            r'\b(python|javascript|typescript|java|cpp|rust|go|golang)\b',
            r'\b(react|vue|angular|node|flask|fastapi|django)\b',
            r'\b(docker|kubernetes|k8s|aws|azure|gcp)\b',
            r'\b(git|github|gitlab|jenkins|ci|cd)\b',
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tags.update(m.lower() for m in matches)
        
        return list(tags)[:10]

    def add_project(self, name: str, path: str, description: str = "", 
                    tags: List[str] = None, **kwargs) -> Dict[str, Any]:
        import uuid
        project_id = str(uuid.uuid4().hex[:12])
        
        project = ProjectContext(
            project_id=project_id,
            name=name,
            path=path,
            description=description,
            tags=tags or [],
            **kwargs
        )
        
        self._projects[project_id] = project
        self._save_projects()
        
        return {"success": True, "project": project.to_dict()}

    def get_project(self, project_id: str = None, path: str = None) -> Optional[ProjectContext]:
        if project_id and project_id in self._projects:
            proj = self._projects[project_id]
            proj.last_accessed = datetime.now().isoformat()
            self._save_projects()
            return proj
        
        if path:
            for proj in self._projects.values():
                if proj.path == path:
                    proj.last_accessed = datetime.now().isoformat()
                    self._save_projects()
                    return proj
        
        return None

    def update_environment(self, **kwargs) -> Dict[str, Any]:
        if not self._env_state:
            self._env_state = EnvironmentState()
        
        if "variables" in kwargs:
            self._env_state.variables.update(kwargs["variables"])
        if "working_directory" in kwargs:
            self._env_state.working_directory = kwargs["working_directory"]
        if "platform" in kwargs:
            self._env_state.platform = kwargs["platform"]
        if "shell" in kwargs:
            self._env_state.shell = kwargs["shell"]
        
        self._env_state.last_updated = datetime.now().isoformat()
        self._save_environment()
        
        return {"success": True, "environment": self._env_state.to_dict()}

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "memory_add",
                "description": "Store important information in persistent memory with optional tags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to store"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional tags"},
                        "importance": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "memory_search",
                "description": "Search persistent memory for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "memory_list",
                "description": "List all stored memories",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filter by category"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 20}
                    },
                    "required": []
                }
            },
            {
                "name": "project_add",
                "description": "Register a new project for context tracking",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name"},
                        "path": {"type": "string", "description": "Project directory path"},
                        "description": {"type": "string", "description": "Project description"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Project tags"}
                    },
                    "required": ["name", "path"]
                }
            },
            {
                "name": "project_list",
                "description": "List all registered projects",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search projects"}
                    },
                    "required": []
                }
            },
            {
                "name": "project_info",
                "description": "Get details about a specific project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"},
                        "path": {"type": "string", "description": "Project path"}
                    },
                    "required": []
                }
            },
            {
                "name": "set_preference",
                "description": "Set a user preference",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Preference key"},
                        "value": {"type": "string", "description": "Preference value"},
                        "category": {"type": "string", "description": "Preference category", "default": "general"}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "get_preference",
                "description": "Get a user preference value",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Preference key"},
                        "category": {"type": "string", "description": "Preference category", "default": "general"}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "get_environment",
                "description": "Get current environment state",
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        ]

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        try:
            if tool_name == "memory_add":
                content = args.get("content", "")
                tags = args.get("tags", [])
                importance = args.get("importance", "medium")
                
                self._memory_data.setdefault("entries", []).append({
                    "timestamp": datetime.now().isoformat(),
                    "content": content,
                    "tags": tags,
                    "importance": importance,
                    "type": "manual"
                })
                self._save_memory()
                return json.dumps({"success": True, "message": "Memory saved"})
            
            elif tool_name == "memory_search":
                query = args.get("query", "").lower()
                limit = args.get("limit", 10)
                results = self._search_entries(query, limit)
                return json.dumps({"success": True, "results": results})
            
            elif tool_name == "memory_list":
                limit = args.get("limit", 20)
                entries = self._memory_data.get("entries", [])
                return json.dumps({"success": True, "entries": entries[-limit:]})
            
            elif tool_name == "project_add":
                result = self.add_project(
                    name=args.get("name", ""),
                    path=args.get("path", ""),
                    description=args.get("description", ""),
                    tags=args.get("tags", [])
                )
                return json.dumps(result)
            
            elif tool_name == "project_list":
                query = args.get("query", "").lower()
                if query:
                    projects = self._search_projects(query)
                else:
                    projects = list(self._projects.values())
                return json.dumps({"success": True, "projects": [p.to_dict() for p in projects]})
            
            elif tool_name == "project_info":
                proj = self.get_project(project_id=args.get("project_id"), path=args.get("path"))
                if proj:
                    return json.dumps({"success": True, "project": proj.to_dict()})
                return json.dumps({"success": False, "error": "Project not found"})
            
            elif tool_name == "set_preference":
                key = args.get("key", "")
                value = args.get("value", "")
                category = args.get("category", "general")
                self._user_data.setdefault("preferences", {}).setdefault(category, {})[key] = value
                self._save_user()
                return json.dumps({"success": True, "message": "Preference saved"})
            
            elif tool_name == "get_preference":
                key = args.get("key", "")
                category = args.get("category", "general")
                value = self._user_data.get("preferences", {}).get(category, {}).get(key)
                return json.dumps({"success": True, "value": value})
            
            elif tool_name == "get_environment":
                if self._env_state:
                    return json.dumps({"success": True, "environment": self._env_state.to_dict()})
                return json.dumps({"success": True, "environment": {}})
            
            else:
                return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})
        
        except Exception as e:
            logger.error(f"Memory tool error: {e}")
            return json.dumps({"success": False, "error": str(e)})


class MemoryManager:
    """记忆管理器 - 协调多个记忆提供者"""

    def __init__(self):
        self._providers: List[MemoryProvider] = []
        self._tool_to_provider: Dict[str, MemoryProvider] = {}
        self._current_session_id = ""
        self._session_data: Dict[str, Any] = {}

    def add_provider(self, provider: MemoryProvider) -> None:
        if not provider.is_available():
            logger.warning(f"Memory provider {provider.name} is not available")
            return
        
        self._providers.append(provider)
        
        for schema in provider.get_tool_schemas():
            tool_name = schema.get("name", "")
            if tool_name:
                self._tool_to_provider[tool_name] = provider
        
        logger.info(f"Memory provider '{provider.name}' registered")

    def initialize_all(self, session_id: str, **kwargs) -> None:
        self._current_session_id = session_id
        self._session_data = {"start_time": datetime.now().isoformat(), "turn_count": 0}
        
        for provider in self._providers:
            try:
                provider.initialize(session_id=session_id, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize provider {provider.name}: {e}")

    def build_system_prompt(self) -> str:
        blocks = []
        for provider in self._providers:
            try:
                block = provider.system_prompt_block()
                if block:
                    blocks.append(block)
            except Exception as e:
                logger.warning(f"Provider {provider.name} system_prompt_block failed: {e}")
        return "\n\n".join(blocks)

    def prefetch_all(self, query: str, *, session_id: str = "") -> str:
        parts = []
        for provider in self._providers:
            try:
                result = provider.prefetch(query, session_id=session_id or self._current_session_id)
                if result:
                    parts.append(result)
            except Exception as e:
                logger.debug(f"Provider {provider.name} prefetch failed: {e}")
        return "\n\n".join(parts)

    def sync_all(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        self._session_data["turn_count"] = self._session_data.get("turn_count", 0) + 1
        
        for provider in self._providers:
            try:
                provider.on_turn_start(
                    self._session_data["turn_count"],
                    user_content,
                    working_directory=self._session_data.get("working_directory", "")
                )
                provider.sync_turn(user_content, assistant_content, session_id=session_id or self._current_session_id)
            except Exception as e:
                logger.warning(f"Provider {provider.name} sync failed: {e}")

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        for provider in self._providers:
            try:
                provider.on_session_end(messages)
            except Exception as e:
                logger.warning(f"Provider {provider.name} on_session_end failed: {e}")

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        seen = set()
        for provider in self._providers:
            try:
                for schema in provider.get_tool_schemas():
                    name = schema.get("name", "")
                    if name and name not in seen:
                        schemas.append(schema)
                        seen.add(name)
            except Exception as e:
                logger.warning(f"Provider {provider.name} get_tool_schemas failed: {e}")
        return schemas

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        provider = self._tool_to_provider.get(tool_name)
        if not provider:
            return json.dumps({"success": False, "error": f"No memory provider handles tool '{tool_name}'"})
        
        try:
            return provider.handle_tool_call(tool_name, args, **kwargs)
        except Exception as e:
            logger.error(f"Provider {provider.name} handle_tool_call failed: {e}")
            return json.dumps({"success": False, "error": str(e)})

    def shutdown_all(self) -> None:
        for provider in reversed(self._providers):
            try:
                provider.shutdown()
            except Exception as e:
                logger.warning(f"Provider {provider.name} shutdown failed: {e}")

    def set_working_directory(self, path: str) -> None:
        self._session_data["working_directory"] = path
        for provider in self._providers:
            try:
                if hasattr(provider, '_env_state') and provider._env_state:
                    provider._env_state.working_directory = path
            except Exception:
                pass