"""并行子智能体系统 - 为并行工作流生成隔离的子智能体"""

import json
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT_CHILDREN = 3
DEFAULT_CHILD_TIMEOUT = 600


class SubagentRecord:
    """子智能体记录"""
    
    def __init__(self, subagent_id: str, parent_id: str, goal: str, model: str = None):
        self.subagent_id = subagent_id
        self.parent_id = parent_id
        self.goal = goal
        self.model = model
        self.started_at = time.time()
        self.tool_count = 0
        self.status = "running"
        self.result = None
        self.progress_callbacks: List[Callable] = []


class SubagentManager:
    """子智能体管理器"""
    
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._active_subagents: Dict[str, SubagentRecord] = {}
        self._lock = threading.Lock()
        self._spawn_paused = False
        self._max_depth = 3
        self._current_depth = 0
    
    def set_spawn_paused(self, paused: bool) -> bool:
        with self._lock:
            self._spawn_paused = bool(paused)
        return self._spawn_paused
    
    def is_spawn_paused(self) -> bool:
        with self._lock:
            return self._spawn_paused
    
    def set_max_depth(self, depth: int) -> None:
        self._max_depth = max(1, depth)
    
    def _register_subagent(self, record: SubagentRecord) -> None:
        with self._lock:
            self._active_subagents[record.subagent_id] = record
    
    def _unregister_subagent(self, subagent_id: str) -> None:
        with self._lock:
            self._active_subagents.pop(subagent_id, None)
    
    def interrupt_subagent(self, subagent_id: str) -> bool:
        with self._lock:
            record = self._active_subagents.get(subagent_id)
        if not record:
            return False
        
        record.status = "interrupted"
        return True
    
    def list_active_subagents(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "subagent_id": r.subagent_id,
                    "parent_id": r.parent_id,
                    "goal": r.goal,
                    "model": r.model,
                    "started_at": r.started_at,
                    "tool_count": r.tool_count,
                    "status": r.status
                }
                for r in self._active_subagents.values()
            ]
    
    def _build_child_prompt(self, goal: str, context: str = None) -> str:
        parts = [
            "你是一个专注的子智能体，正在执行一个委托任务。",
            "",
            f"你的任务：\n{goal}"
        ]
        
        if context and context.strip():
            parts.append(f"\n上下文：\n{context}")
        
        parts.append("\n使用可用的工具完成此任务。完成后，提供清晰简洁的总结。")
        
        return "\n".join(parts)
    
    def _run_single_child(self, task_index: int, goal: str, context: str = None, 
                         toolsets: List[str] = None, model: str = None) -> Dict[str, Any]:
        subagent_id = f"sa-{task_index}-{uuid.uuid4().hex[:8]}"
        
        record = SubagentRecord(
            subagent_id=subagent_id,
            parent_id="main",
            goal=goal[:50] + "..." if len(goal) > 50 else goal,
            model=model
        )
        self._register_subagent(record)
        
        try:
            result = self._simulate_agent_execution(goal, context, toolsets, subagent_id)
            
            record.status = "completed"
            record.result = result
            
            return {"success": True, "subagent_id": subagent_id, "result": result, "tool_count": record.tool_count}
        
        except Exception as e:
            record.status = "failed"
            record.result = str(e)
            
            return {"success": False, "subagent_id": subagent_id, "error": str(e)}
        
        finally:
            self._unregister_subagent(subagent_id)
    
    def _simulate_agent_execution(self, goal: str, context: str, toolsets: List[str], 
                                  subagent_id: str) -> str:
        time.sleep(2)
        
        record = self._active_subagents.get(subagent_id)
        if record and record.status == "interrupted":
            return "子智能体已被中断"
        
        record.tool_count += 1
        
        summary = f"已完成任务: {goal}\n\n执行步骤：\n- 分析任务需求\n- 执行必要操作\n- 生成结果\n\n结果总结：任务已成功完成"
        
        return summary
    
    def delegate_task(self, goal: str, context: str = None, toolsets: List[str] = None,
                     model: str = None, max_iterations: int = 50, 
                     max_concurrent: int = None) -> Dict[str, Any]:
        if self.is_spawn_paused():
            return {"success": False, "error": "子智能体生成已暂停"}
        
        if self._current_depth >= self._max_depth:
            return {"success": False, "error": f"最大嵌套深度 {self._max_depth} 已达"}
        
        max_concurrent = max_concurrent or DEFAULT_MAX_CONCURRENT_CHILDREN
        
        if isinstance(goal, str):
            self._current_depth += 1
            try:
                result = self._run_single_child(0, goal, context, toolsets, model)
                return result
            finally:
                self._current_depth -= 1
        
        if isinstance(goal, list):
            results = []
            futures = []
            
            for i, task in enumerate(goal[:max_concurrent]):
                task_goal = task.get("goal", "")
                task_context = task.get("context", "")
                future = self._executor.submit(
                    self._run_single_child, i, task_goal, task_context, toolsets, model
                )
                futures.append((i, future))
            
            for i, future in futures:
                try:
                    result = future.result(timeout=DEFAULT_CHILD_TIMEOUT)
                    results.append(result)
                except FuturesTimeoutError:
                    results.append({"success": False, "error": "子智能体超时"})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
            
            return {"success": True, "results": results}
        
        return {"success": False, "error": "无效的任务格式"}
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "delegate_task",
                "description": "将任务委托给并行子智能体执行",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {
                            "oneOf": [
                                {"type": "string", "description": "单个任务目标"},
                                {"type": "array", "items": {"type": "object", "properties": {"goal": {"type": "string"}, "context": {"type": "string"}}}, "description": "多个并行任务"}
                            ],
                            "description": "任务目标"
                        },
                        "context": {"type": "string", "description": "任务上下文"},
                        "toolsets": {"type": "array", "items": {"type": "string"}, "description": "可用工具集"},
                        "model": {"type": "string", "description": "使用的模型"},
                        "max_concurrent": {"type": "integer", "description": "最大并发数"}
                    },
                    "required": ["goal"]
                }
            },
            {"name": "list_subagents", "description": "列出当前运行的子智能体", "parameters": {"type": "object", "properties": {}, "required": []}},
            {"name": "interrupt_subagent", "description": "中断指定的子智能体", "parameters": {"type": "object", "properties": {"subagent_id": {"type": "string"}}, "required": ["subagent_id"]}},
            {"name": "pause_subagents", "description": "暂停子智能体生成", "parameters": {"type": "object", "properties": {}, "required": []}},
            {"name": "resume_subagents", "description": "恢复子智能体生成", "parameters": {"type": "object", "properties": {}, "required": []}}
        ]
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            if tool_name == "delegate_task":
                result = self.delegate_task(goal=args.get("goal", ""), context=args.get("context"), toolsets=args.get("toolsets"), model=args.get("model"), max_concurrent=args.get("max_concurrent"))
            elif tool_name == "list_subagents":
                result = {"success": True, "subagents": self.list_active_subagents()}
            elif tool_name == "interrupt_subagent":
                success = self.interrupt_subagent(subagent_id=args.get("subagent_id", ""))
                result = {"success": success, "message": "中断成功" if success else "未找到子智能体"}
            elif tool_name == "pause_subagents":
                self.set_spawn_paused(True)
                result = {"success": True, "message": "子智能体生成已暂停"}
            elif tool_name == "resume_subagents":
                self.set_spawn_paused(False)
                result = {"success": True, "message": "子智能体生成已恢复"}
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Subagent tool error: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    def shutdown(self):
        self._executor.shutdown(wait=True)
        logger.info("Subagent manager shutdown")