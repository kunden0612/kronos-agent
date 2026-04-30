"""
Hermes Agent Integration Service

This module provides a complete integration with the Hermes Agent framework,
exposing all core capabilities including:
- Full AIAgent conversation loop
- Tool calling with Kronos prediction tools
- Memory management
- Context compression
- Subagent delegation
- Skill learning
- Session management
- Streaming responses
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)

# Add hermes-agent to path
HERMES_AGENT_PATH = os.environ.get("HERMES_AGENT_PATH", "/workspace/hermes-agent")
if HERMES_AGENT_PATH not in sys.path:
    sys.path.insert(0, HERMES_AGENT_PATH)

try:
    from run_agent import AIAgent, IterationBudget
    from model_tools import get_tool_definitions, handle_function_call
    from tools.registry import registry
    from hermes_cli.config import cfg_get, DEFAULT_CONFIG
    HERMES_AVAILABLE = True
    logger.info("✅ Hermes Agent framework loaded successfully")
except ImportError as e:
    HERMES_AVAILABLE = False
    logger.warning(f"⚠️ Hermes Agent not available: {e}")
    AIAgent = None
    registry = None


class HermesAgentService:
    """
    Complete Hermes Agent integration service that exposes all core capabilities.
    
    This class provides:
    - Full AIAgent with tool calling
    - Kronos prediction tools registered in Hermes tool system
    - Session management
    - Streaming responses
    - Memory integration
    - Subagent delegation
    - Callback support for real-time updates
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._agent: Optional[AIAgent] = None
        self._is_initialized = False
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
        # Configure from environment and config
        self._configure()
    
    def _configure(self):
        """Configure Hermes Agent parameters"""
        # Provider configuration
        self.provider = self.config.get("provider") or os.getenv("HERMES_PROVIDER", "openrouter")
        self.model = self.config.get("model") or os.getenv("HERMES_MODEL", "anthropic/claude-3.5-sonnet")
        self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.base_url = self.config.get("base_url")
        
        # Agent configuration
        self.max_iterations = self.config.get("max_iterations", 90)
        self.enabled_toolsets = self.config.get("enabled_toolsets", ["kronos"])
        self.disabled_toolsets = self.config.get("disabled_toolsets", [])
        self.tool_delay = self.config.get("tool_delay", 1.0)
        
        # Session configuration
        self.save_trajectories = self.config.get("save_trajectories", False)
        self.skip_memory = self.config.get("skip_memory", False)
        self.skip_context_files = self.config.get("skip_context_files", True)
        
        logger.info(f"🔧 Hermes Agent configured: provider={self.provider}, model={self.model}")
    
    def _register_kronos_tools(self):
        """Register Kronos prediction tools with Hermes tool registry"""
        if not HERMES_AVAILABLE or registry is None:
            logger.warning("Cannot register tools: Hermes registry not available")
            return
        
        # Import here to avoid circular imports
        from ..tools.kronos_tools import kronos_predict_tool, kronos_batch_predict_tool, check_kronos_requirements
        
        # Register kronos_predict tool
        registry.register(
            name="kronos_predict",
            toolset="kronos",
            schema={
                "name": "kronos_predict",
                "description": "使用 Kronos 深度学习模型预测金融资产的未来走势。支持 A股（如茅台 600519.SH）、美股（如苹果 AAPL）、加密货币（如比特币 BTC/USDT）。返回 OHLCV 数据、置信区间和 AI 解读。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "资产代码，例如：600519.SH（茅台）、AAPL（苹果）、BTC/USDT（比特币）"},
                        "pred_len": {"type": "integer", "description": "预测长度（交易日数量）", "default": 5},
                        "model_name": {"type": "string", "description": "模型名称", "default": "NeoQuasar/Kronos-mini"},
                        "lookback": {"type": "integer", "description": "历史回看窗口长度（天数）", "default": 400},
                        "freq": {"type": "string", "description": "数据频率，如 daily, 1h, 5min", "default": "daily"},
                        "sample_count": {"type": "integer", "description": "采样路径数", "default": 5},
                        "T": {"type": "number", "description": "采样温度", "default": 1.0},
                        "top_p": {"type": "number", "description": "核采样概率", "default": 0.9}
                    },
                    "required": ["symbol"]
                }
            },
            handler=lambda args, **kw: kronos_predict_tool(
                symbol=args.get("symbol"),
                pred_len=args.get("pred_len", 5),
                model_name=args.get("model_name"),
                lookback=args.get("lookback", 400),
                freq=args.get("freq", "daily"),
                sample_count=args.get("sample_count", 5),
                T=args.get("T", 1.0),
                top_p=args.get("top_p", 0.9),
                task_id=kw.get("task_id")
            ),
            check_fn=check_kronos_requirements,
            requires_env=[],
        )
        
        # Register kronos_batch_predict tool
        registry.register(
            name="kronos_batch_predict",
            toolset="kronos",
            schema={
                "name": "kronos_batch_predict",
                "description": "批量预测多个金融资产的未来走势，提高效率。适用于分析投资组合或多个相关资产。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbols": {"type": "array", "items": {"type": "string"}, "description": "资产代码列表"},
                        "pred_len": {"type": "integer", "description": "预测长度（交易日数量）", "default": 5},
                        "model_name": {"type": "string", "description": "模型名称", "default": "NeoQuasar/Kronos-mini"},
                        "lookback": {"type": "integer", "description": "历史回看窗口长度（天数）", "default": 400},
                        "freq": {"type": "string", "description": "数据频率", "default": "daily"},
                        "sample_count": {"type": "integer", "description": "采样路径数", "default": 5}
                    },
                    "required": ["symbols"]
                }
            },
            handler=lambda args, **kw: kronos_batch_predict_tool(
                symbols=args.get("symbols"),
                pred_len=args.get("pred_len", 5),
                model_name=args.get("model_name"),
                lookback=args.get("lookback", 400),
                freq=args.get("freq", "daily"),
                sample_count=args.get("sample_count", 5),
                task_id=kw.get("task_id")
            ),
            check_fn=check_kronos_requirements,
            requires_env=[],
        )
        
        logger.info("✅ Kronos tools registered with Hermes tool system")
    
    async def initialize(self):
        """Initialize Hermes Agent with all capabilities"""
        if not HERMES_AVAILABLE:
            raise RuntimeError("Hermes Agent framework not installed")
        
        if self._is_initialized:
            logger.info("Agent already initialized")
            return
        
        try:
            # Register Kronos tools first
            self._register_kronos_tools()
            
            # Create AIAgent instance with full capabilities
            self._agent = AIAgent(
                base_url=self.base_url,
                api_key=self.api_key,
                provider=self.provider,
                model=self.model,
                max_iterations=self.max_iterations,
                tool_delay=self.tool_delay,
                enabled_toolsets=self.enabled_toolsets,
                disabled_toolsets=self.disabled_toolsets,
                save_trajectories=self.save_trajectories,
                skip_memory=self.skip_memory,
                skip_context_files=self.skip_context_files,
                # Callbacks for real-time updates
                tool_progress_callback=self._on_tool_progress,
                tool_start_callback=self._on_tool_start,
                tool_complete_callback=self._on_tool_complete,
                thinking_callback=self._on_thinking,
                reasoning_callback=self._on_reasoning,
                clarify_callback=self._on_clarify,
                step_callback=self._on_step,
                stream_delta_callback=self._on_stream_delta,
                status_callback=self._on_status,
            )
            
            self._is_initialized = True
            logger.info("🎉 Hermes Agent initialized with full capabilities")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Hermes Agent: {e}", exc_info=True)
            raise
    
    def _on_tool_progress(self, tool_name: str, progress: float, message: str):
        """Callback when tool execution progresses"""
        logger.debug(f"🔧 Tool progress: {tool_name} - {progress}% - {message}")
    
    def _on_tool_start(self, tool_name: str, args: dict):
        """Callback when tool starts execution"""
        logger.debug(f"🔧 Tool started: {tool_name} with args: {args}")
    
    def _on_tool_complete(self, tool_name: str, result: str, duration_ms: int):
        """Callback when tool completes"""
        logger.debug(f"✅ Tool completed: {tool_name} in {duration_ms}ms")
    
    def _on_thinking(self, thinking: str):
        """Callback when agent is thinking"""
        logger.debug(f"🤔 Thinking: {thinking}")
    
    def _on_reasoning(self, reasoning: str):
        """Callback for reasoning updates"""
        logger.debug(f"💡 Reasoning: {reasoning}")
    
    def _on_clarify(self, question: str):
        """Callback when agent needs clarification"""
        logger.debug(f"❓ Clarification needed: {question}")
    
    def _on_step(self, step: dict):
        """Callback for each step in the conversation"""
        logger.debug(f"🚶 Step: {step}")
    
    def _on_stream_delta(self, delta: str):
        """Callback for streaming response deltas"""
        logger.debug(f"📡 Stream delta: {delta}")
    
    def _on_status(self, status: str):
        """Callback for status updates"""
        logger.debug(f"📊 Status: {status}")
    
    async def chat(self, message: str, conversation_id: Optional[str] = None) -> str:
        """
        Simple chat interface - returns final response string
        
        Args:
            message: User's message
            conversation_id: Optional session identifier
        
        Returns:
            Final response from the agent
        """
        if not self._is_initialized:
            await self.initialize()
        
        if not self._agent:
            raise RuntimeError("Agent not initialized")
        
        try:
            result = self._agent.run_conversation(message)
            return result.get("final_response", "")
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            raise
    
    async def run_conversation(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[str] = None,
        stream_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Full conversation interface with all Hermes capabilities
        
        Args:
            user_message: The user's message
            system_message: Custom system message (optional)
            conversation_history: Previous conversation messages
            task_id: Unique task identifier
            stream_callback: Callback for streaming responses
        
        Returns:
            Dict containing final_response, messages, and metadata
        """
        if not self._is_initialized:
            await self.initialize()
        
        if not self._agent:
            raise RuntimeError("Agent not initialized")
        
        try:
            result = self._agent.run_conversation(
                user_message=user_message,
                system_message=system_message,
                conversation_history=conversation_history,
                task_id=task_id,
                stream_callback=stream_callback
            )
            
            return {
                "response": result.get("final_response", ""),
                "messages": result.get("messages", []),
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "task_id": task_id,
                "metadata": result.get("metadata", {})
            }
        except Exception as e:
            logger.error(f"Error in conversation: {e}", exc_info=True)
            raise
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any], task_id: Optional[str] = None) -> str:
        """
        Direct tool invocation
        
        Args:
            tool_name: Name of the tool to call
            args: Tool arguments
            task_id: Optional task identifier
        
        Returns:
            Tool execution result
        """
        if not HERMES_AVAILABLE:
            raise RuntimeError("Hermes Agent framework not available")
        
        try:
            result = handle_function_call(tool_name, args, task_id=task_id)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}", exc_info=True)
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools"""
        if not HERMES_AVAILABLE:
            return []
        
        return get_tool_definitions(
            enabled_toolsets=self.enabled_toolsets,
            disabled_toolsets=self.disabled_toolsets
        )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities overview"""
        return {
            "framework": "hermes-agent",
            "initialized": self._is_initialized,
            "provider": self.provider,
            "model": self.model,
            "max_iterations": self.max_iterations,
            "enabled_toolsets": self.enabled_toolsets,
            "capabilities": [
                "natural_language_understanding",
                "tool_calling",
                "persistent_memory",
                "skill_learning",
                "subagent_delegation",
                "context_compression",
                "streaming_responses",
                "session_management"
            ],
            "tools": [tool["name"] for tool in self.get_available_tools()]
        }
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(8).hex()}"
        self._sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self._sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """Close a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Global singleton instance
hermes_agent_service = HermesAgentService()
