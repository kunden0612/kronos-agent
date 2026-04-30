"""Kronos Agent - 继承 Hermes-agent 核心能力的智能代理系统"""

import json
import logging
from typing import Dict, List, Any, Callable, Optional

logger = logging.getLogger(__name__)

__all__ = ["KronosAgent", "MemoryManager", "SkillManager", "CronScheduler", "SubagentManager", "BrowserTool", "ToolRegistry"]

from .memory import MemoryManager, BuiltinMemoryProvider
from .skills import SkillManager
from .cron import CronScheduler
from .subagent import SubagentManager
from .browser import BrowserTool


class ToolRegistry:
    """统一工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, List[str]] = {"memory": [], "skills": [], "cron": [], "subagent": [], "browser": [], "system": []}
        self._middleware: List[Callable] = []
    
    def register(self, name: str, schema: Dict[str, Any], handler: Callable, category: str = "system") -> None:
        self._tools[name] = {"schema": schema, "handler": handler, "category": category}
        
        if category not in self._categories:
            self._categories[category] = []
        
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        logger.debug(f"Registered tool: {name} (category: {category})")
    
    def unregister(self, name: str) -> bool:
        if name not in self._tools:
            return False
        
        category = self._tools[name]["category"]
        self._categories[category].remove(name)
        del self._tools[name]
        return True
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)
    
    def get_handler(self, name: str) -> Optional[Callable]:
        tool = self._tools.get(name)
        return tool["handler"] if tool else None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        return [tool["schema"] for tool in self._tools.values()]
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        tool_names = self._categories.get(category, [])
        return [self._tools[name]["schema"] for name in tool_names if name in self._tools]
    
    def list_categories(self) -> List[str]:
        return list(self._categories.keys())
    
    def add_middleware(self, middleware: Callable) -> None:
        self._middleware.append(middleware)
    
    def execute(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        handler = self.get_handler(tool_name)
        if not handler:
            return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})
        
        for mw in self._middleware:
            try:
                args, kwargs = mw(tool_name, args, kwargs)
            except Exception as e:
                logger.warning(f"Middleware error: {e}")
        
        try:
            return handler(tool_name, args, **kwargs)
        except Exception as e:
            logger.error(f"Tool execution error {tool_name}: {e}")
            return json.dumps({"success": False, "error": str(e)})


class KronosAgent:
    """Kronos 智能代理主类 - 整合所有 Hermes-agent 核心能力"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._session_id = self.config.get("session_id", "")
        self._initialized = False
        
        self._tool_registry = ToolRegistry()
        
        self._memory_manager: Optional[MemoryManager] = None
        self._skill_manager: Optional[SkillManager] = None
        self._cron_scheduler: Optional[CronScheduler] = None
        self._subagent_manager: Optional[SubagentManager] = None
        self._browser_tool: Optional[BrowserTool] = None
    
    def initialize(self) -> "KronosAgent":
        if self._initialized:
            return self
        
        kronos_home = self.config.get("kronos_home", None)
        
        self._memory_manager = MemoryManager()
        self._skill_manager = SkillManager(skills_dir=self.config.get("skills_dir") or (kronos_home and f"{kronos_home}/skills"))
        self._cron_scheduler = CronScheduler(cron_dir=self.config.get("cron_dir") or (kronos_home and f"{kronos_home}/cron"))
        self._subagent_manager = SubagentManager()
        self._browser_tool = BrowserTool()
        
        self._register_memory_tools()
        self._register_skill_tools()
        self._register_cron_tools()
        self._register_subagent_tools()
        self._register_browser_tools()
        self._register_system_tools()
        
        self._memory_manager.initialize_all(session_id=self._session_id)
        self._skill_manager.load_skills()
        self._cron_scheduler.start()
        
        self._initialized = True
        logger.info("Kronos Agent initialized with all Hermes capabilities")
        
        return self
    
    def _register_memory_tools(self) -> None:
        provider = BuiltinMemoryProvider()
        self._memory_manager.add_provider(provider)
        
        for tool in self._memory_manager.get_all_tool_schemas():
            self._tool_registry.register(name=tool["name"], schema=tool, handler=self._memory_manager.handle_tool_call, category="memory")
    
    def _register_skill_tools(self) -> None:
        for tool in self._skill_manager.get_tool_schemas():
            self._tool_registry.register(name=tool["name"], schema=tool, handler=self._skill_manager.handle_tool_call, category="skills")
    
    def _register_cron_tools(self) -> None:
        for tool in self._cron_scheduler.get_tool_schemas():
            self._tool_registry.register(name=tool["name"], schema=tool, handler=self._cron_scheduler.handle_tool_call, category="cron")
    
    def _register_subagent_tools(self) -> None:
        for tool in self._subagent_manager.get_tool_schemas():
            self._tool_registry.register(name=tool["name"], schema=tool, handler=self._subagent_manager.handle_tool_call, category="subagent")
    
    def _register_browser_tools(self) -> None:
        for tool in self._browser_tool.get_tool_schemas():
            self._tool_registry.register(name=tool["name"], schema=tool, handler=self._browser_tool.handle_tool_call, category="browser")
    
    def _register_system_tools(self) -> None:
        system_tools = [
            {"name": "agent_capabilities", "description": "Get information about available agent capabilities", "parameters": {"type": "object", "properties": {}}},
            {"name": "agent_status", "description": "Get current agent status including active components", "parameters": {"type": "object", "properties": {}}},
            {"name": "list_categories", "description": "List all tool categories", "parameters": {"type": "object", "properties": {}}}
        ]
        
        for tool in system_tools:
            self._tool_registry.register(name=tool["name"], schema=tool, handler=self._system_tool_handler, category="system")
    
    def _system_tool_handler(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name == "agent_capabilities":
            return json.dumps({"success": True, "capabilities": self.summarize_capabilities()})
        elif tool_name == "agent_status":
            return json.dumps({"success": True, "status": {"initialized": self._initialized, "session_id": self._session_id, "memory_providers": len(self._memory_manager._providers) if self._memory_manager else 0, "skills_count": len(self._skill_manager._skills) if self._skill_manager else 0, "cron_jobs": len(self._cron_scheduler._jobs) if self._cron_scheduler else 0, "active_subagents": len(self._subagent_manager._active_subagents) if self._subagent_manager else 0, "tool_categories": self._tool_registry.list_categories(), "total_tools": len(self._tool_registry._tools)}})
        elif tool_name == "list_categories":
            return json.dumps({"success": True, "categories": self._tool_registry.list_categories(), "tools_per_category": {cat: len(self._tool_registry.get_tools_by_category(cat)) for cat in self._tool_registry.list_categories()}})
        
        return json.dumps({"success": False, "error": f"Unknown system tool: {tool_name}"})
    
    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        return self._tool_registry.get_all_tools()
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        return self._tool_registry.get_tools_by_category(category)
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        return self._tool_registry.execute(tool_name, args, **kwargs)
    
    def get_memory_manager(self) -> Optional[MemoryManager]:
        return self._memory_manager
    
    def get_skill_manager(self) -> Optional[SkillManager]:
        return self._skill_manager
    
    def get_cron_scheduler(self) -> Optional[CronScheduler]:
        return self._cron_scheduler
    
    def get_subagent_manager(self) -> Optional[SubagentManager]:
        return self._subagent_manager
    
    def get_browser_tool(self) -> Optional[BrowserTool]:
        return self._browser_tool
    
    def get_tool_registry(self) -> ToolRegistry:
        return self._tool_registry
    
    def shutdown(self) -> None:
        if self._cron_scheduler:
            self._cron_scheduler.stop()
        if self._subagent_manager:
            self._subagent_manager.shutdown()
        if self._memory_manager:
            self._memory_manager.shutdown_all()
        self._initialized = False
        logger.info("Kronos Agent shutdown complete")
    
    def summarize_capabilities(self) -> str:
        return """## Kronos Agent Capabilities (Hermes-agent Core)

### 1. Persistent Memory System
- Cross-session user preferences, projects, and environment tracking
- Multiple memory providers support
- Automatic prefetch and retrieval

### 2. Automatic Skill Creation
- Create reusable skills from solved problems
- Skill search, update, delete operations
- Compatible with agentskills.io open standard

### 3. Scheduled Automation Tasks
- Built-in cron scheduler
- Job creation, update, delete operations
- Pre-script and working directory support

### 4. Parallel Subagents
- Generate isolated subagents for parallel workflows
- Batch task delegation support
- Subagent state management

### 5. Complete Browser Control
- Web navigation and page extraction
- Full browser automation (click, type, scroll)
- Visual analysis and screenshot"""
    
    def __enter__(self) -> "KronosAgent":
        return self.initialize()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()


def create_agent(config: Dict[str, Any] = None) -> KronosAgent:
    """创建并初始化代理的工厂函数"""
    agent = KronosAgent(config)
    agent.initialize()
    return agent