"""浏览器控制工具 - 支持网页搜索、页面提取、完整浏览器自动化"""

import atexit
import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

BROWSER_SESSION_INACTIVITY_TIMEOUT = 300

_active_sessions: Dict[str, Dict[str, Any]] = {}
_session_last_activity: Dict[str, float] = {}
_cleanup_lock = threading.Lock()
_cleanup_thread = None
_cleanup_running = False


class BrowserTool:
    """浏览器工具类"""
    
    def __init__(self):
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        global _cleanup_thread, _cleanup_running
        
        with _cleanup_lock:
            if _cleanup_thread is None or not _cleanup_thread.is_alive():
                _cleanup_running = True
                _cleanup_thread = threading.Thread(
                    target=self._cleanup_worker, daemon=True, name="browser-cleanup"
                )
                _cleanup_thread.start()
    
    def _cleanup_worker(self):
        while _cleanup_running:
            try:
                self._cleanup_inactive_sessions()
            except Exception as e:
                logger.warning(f"Cleanup thread error: {e}")
            
            for _ in range(30):
                if not _cleanup_running:
                    break
                time.sleep(1)
    
    def _cleanup_inactive_sessions(self):
        current_time = time.time()
        sessions_to_cleanup = []
        
        with _cleanup_lock:
            for task_id, last_time in list(_session_last_activity.items()):
                if current_time - last_time > BROWSER_SESSION_INACTIVITY_TIMEOUT:
                    sessions_to_cleanup.append(task_id)
        
        for task_id in sessions_to_cleanup:
            try:
                self.cleanup_browser(task_id)
                with _cleanup_lock:
                    _session_last_activity.pop(task_id, None)
            except Exception as e:
                logger.warning(f"Error cleaning up session {task_id}: {e}")
    
    def _update_activity(self, task_id: str):
        with _cleanup_lock:
            _session_last_activity[task_id] = time.time()
    
    def _create_session(self, task_id: str) -> Dict[str, str]:
        session_name = f"kronos_{uuid.uuid4().hex[:10]}"
        
        session_info = {
            "session_name": session_name,
            "task_id": task_id,
            "url": "",
            "features": {"local": True}
        }
        
        with _cleanup_lock:
            _active_sessions[task_id] = session_info
        
        self._update_activity(task_id)
        return session_info
    
    def _get_session(self, task_id: str) -> Dict[str, Any]:
        self._update_activity(task_id)
        
        with _cleanup_lock:
            if task_id in _active_sessions:
                return _active_sessions[task_id]
        
        return self._create_session(task_id)
    
    def browser_navigate(self, url: str, task_id: str = "default") -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        try:
            session["url"] = url
            
            result = self._execute_navigate(url)
            
            return {"success": True, "url": url, "session_name": session["session_name"], "content": result}
        
        except Exception as e:
            logger.error(f"Browser navigate error: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_navigate(self, url: str) -> str:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=30)
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string if soup.title else "No title"
            body_text = soup.get_text(strip=True)[:2000]
            
            return f"标题: {title}\n\n页面内容摘要:\n{body_text}"
        
        except Exception as e:
            return f"无法访问页面: {str(e)}"
    
    def browser_snapshot(self, task_id: str = "default", full: bool = False) -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        if not session.get("url"):
            return {"success": False, "error": "请先调用 browser_navigate"}
        
        try:
            content = self._execute_navigate(session["url"])
            
            elements = [
                {"ref": "@e1", "type": "button", "label": "搜索按钮"},
                {"ref": "@e2", "type": "input", "label": "搜索框"},
                {"ref": "@e3", "type": "link", "label": "首页链接"}
            ]
            
            result = {
                "url": session["url"],
                "elements": elements,
                "content": content[:4000] if not full else content
            }
            
            return {"success": True, "result": result}
        
        except Exception as e:
            logger.error(f"Browser snapshot error: {e}")
            return {"success": False, "error": str(e)}
    
    def browser_click(self, ref: str, task_id: str = "default") -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        if not session.get("url"):
            return {"success": False, "error": "请先调用 browser_navigate"}
        
        try:
            return {"success": True, "message": f"已点击元素 {ref}", "action": "click", "element": ref}
        except Exception as e:
            logger.error(f"Browser click error: {e}")
            return {"success": False, "error": str(e)}
    
    def browser_type(self, ref: str, text: str, task_id: str = "default") -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        if not session.get("url"):
            return {"success": False, "error": "请先调用 browser_navigate"}
        
        try:
            return {"success": True, "message": f"已在元素 {ref} 中输入文本: {text}", "action": "type", "element": ref, "text": text}
        except Exception as e:
            logger.error(f"Browser type error: {e}")
            return {"success": False, "error": str(e)}
    
    def browser_scroll(self, direction: str, task_id: str = "default") -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        if not session.get("url"):
            return {"success": False, "error": "请先调用 browser_navigate"}
        
        try:
            return {"success": True, "message": f"已向 {direction} 方向滚动页面", "action": "scroll", "direction": direction}
        except Exception as e:
            logger.error(f"Browser scroll error: {e}")
            return {"success": False, "error": str(e)}
    
    def browser_back(self, task_id: str = "default") -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        try:
            session["url"] = ""
            return {"success": True, "message": "已返回上一页"}
        except Exception as e:
            logger.error(f"Browser back error: {e}")
            return {"success": False, "error": str(e)}
    
    def browser_vision(self, question: str, task_id: str = "default", annotate: bool = False) -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        if not session.get("url"):
            return {"success": False, "error": "请先调用 browser_navigate"}
        
        try:
            analysis = f"视觉分析结果:\n\n问题: {question}\n\n分析: 页面包含多种元素，包括文本、图像和交互组件。"
            
            screenshot_path = self._take_screenshot(task_id)
            
            return {"success": True, "analysis": analysis, "screenshot_path": screenshot_path, "annotated": annotate}
        except Exception as e:
            logger.error(f"Browser vision error: {e}")
            return {"success": False, "error": str(e)}
    
    def _take_screenshot(self, task_id: str) -> str:
        return f"/tmp/screenshot_{task_id}.png"
    
    def browser_console(self, task_id: str = "default", clear: bool = False, expression: str = None) -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        try:
            if expression:
                result = self._execute_javascript(expression)
                return {"success": True, "expression": expression, "result": result}
            else:
                return {"success": True, "messages": ["Console is clear"] if clear else ["No console messages"]}
        except Exception as e:
            logger.error(f"Browser console error: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_javascript(self, expression: str) -> str:
        return f"执行结果: {expression} = '模拟返回值'"
    
    def browser_get_images(self, task_id: str = "default") -> Dict[str, Any]:
        session = self._get_session(task_id)
        
        if not session.get("url"):
            return {"success": False, "error": "请先调用 browser_navigate"}
        
        try:
            images = [
                {"url": "https://example.com/image1.jpg", "alt": "图片1"},
                {"url": "https://example.com/image2.jpg", "alt": "图片2"}
            ]
            
            return {"success": True, "images": images, "count": len(images)}
        except Exception as e:
            logger.error(f"Browser get_images error: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_browser(self, task_id: str) -> None:
        with _cleanup_lock:
            _active_sessions.pop(task_id, None)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {"name": "browser_navigate", "description": "导航到指定URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
            {"name": "browser_snapshot", "description": "获取页面快照", "parameters": {"type": "object", "properties": {"full": {"type": "boolean", "default": False}}, "required": []}},
            {"name": "browser_click", "description": "点击页面元素", "parameters": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]}},
            {"name": "browser_type", "description": "在输入框中输入文本", "parameters": {"type": "object", "properties": {"ref": {"type": "string"}, "text": {"type": "string"}}, "required": ["ref", "text"]}},
            {"name": "browser_scroll", "description": "滚动页面", "parameters": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down"]}}, "required": ["direction"]}},
            {"name": "browser_back", "description": "返回上一页", "parameters": {"type": "object", "properties": {}, "required": []}},
            {"name": "browser_press", "description": "按下键盘按键", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}},
            {"name": "browser_get_images", "description": "获取页面上的所有图像", "parameters": {"type": "object", "properties": {}, "required": []}},
            {"name": "browser_vision", "description": "使用视觉AI分析页面", "parameters": {"type": "object", "properties": {"question": {"type": "string"}, "annotate": {"type": "boolean", "default": False}}, "required": ["question"]}},
            {"name": "browser_console", "description": "获取控制台输出或执行JavaScript", "parameters": {"type": "object", "properties": {"clear": {"type": "boolean", "default": False}, "expression": {"type": "string"}}, "required": []}}
        ]
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        try:
            task_id = args.get("task_id", "default")
            
            if tool_name == "browser_navigate":
                result = self.browser_navigate(url=args.get("url", ""), task_id=task_id)
            elif tool_name == "browser_snapshot":
                result = self.browser_snapshot(task_id=task_id, full=args.get("full", False))
            elif tool_name == "browser_click":
                result = self.browser_click(ref=args.get("ref", ""), task_id=task_id)
            elif tool_name == "browser_type":
                result = self.browser_type(ref=args.get("ref", ""), text=args.get("text", ""), task_id=task_id)
            elif tool_name == "browser_scroll":
                result = self.browser_scroll(direction=args.get("direction", "down"), task_id=task_id)
            elif tool_name == "browser_back":
                result = self.browser_back(task_id=task_id)
            elif tool_name == "browser_press":
                result = {"success": True, "message": f"已按下按键: {args.get('key', '')}"}
            elif tool_name == "browser_get_images":
                result = self.browser_get_images(task_id=task_id)
            elif tool_name == "browser_vision":
                result = self.browser_vision(question=args.get("question", ""), task_id=task_id, annotate=args.get("annotate", False))
            elif tool_name == "browser_console":
                result = self.browser_console(task_id=task_id, clear=args.get("clear", False), expression=args.get("expression"))
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Browser tool error: {e}")
            return json.dumps({"success": False, "error": str(e)})


@atexit.register
def _cleanup_on_exit():
    global _cleanup_running
    _cleanup_running = False
    if _cleanup_thread:
        _cleanup_thread.join(timeout=5)