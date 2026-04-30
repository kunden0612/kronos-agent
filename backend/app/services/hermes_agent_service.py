import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

HERMES_AVAILABLE = False

try:
    from run_agent import AIAgent
    HERMES_AVAILABLE = True
    logger.info("Hermes AIAgent loaded successfully")
except ImportError as e:
    logger.warning(f"Hermes AIAgent not available: {e}")
    AIAgent = None


class HermesAgentService:
    """
    基于 Hermes-agent 框架的 Agent 服务
    
    集成 NousResearch 的 Hermes Agent，提供：
    - 自进化学习能力
    - 持久记忆
    - 工具调用
    - 子 Agent 并行委派
    - 定时任务调度
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._agent: Optional[AIAgent] = None
        self._is_initialized = False
        
        self._setup_config()
    
    def _setup_config(self):
        """配置 Agent 参数"""
        self.provider = self.config.get("provider", "openrouter")
        self.model = self.config.get("model", "anthropic/claude-3.5-sonnet")
        self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = self.config.get("base_url")
        
        self.max_iterations = self.config.get("max_iterations", 90)
        self.enabled_toolsets = self.config.get("enabled_toolsets", ["kronos"])
        self.disabled_toolsets = self.config.get("disabled_toolsets", [])
        
        logger.info(f"Hermes Agent configured with provider={self.provider}, model={self.model}")
    
    async def initialize(self):
        """初始化 Hermes Agent"""
        if not HERMES_AVAILABLE:
            logger.error("Cannot initialize: Hermes AIAgent not available")
            raise RuntimeError("Hermes Agent framework not installed")
        
        if self._is_initialized:
            logger.info("Agent already initialized")
            return
        
        try:
            self._agent = AIAgent(
                provider=self.provider,
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,
                max_iterations=self.max_iterations,
                enabled_toolsets=self.enabled_toolsets,
                disabled_toolsets=self.disabled_toolsets,
                skip_memory=False,
                skip_context_files=True,
            )
            
            self._is_initialized = True
            logger.info("Hermes Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hermes Agent: {e}")
            raise
    
    async def chat(self, message: str) -> str:
        """
        处理用户聊天消息
        
        Args:
            message: 用户输入的自然语言消息
        
        Returns:
            Agent 响应字符串
        """
        if not self._is_initialized:
            await self.initialize()
        
        if not self._agent:
            raise RuntimeError("Agent not initialized")
        
        try:
            logger.info(f"Processing message: {message}")
            response = self._agent.chat(message)
            logger.info("Message processed successfully")
            return response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def run_conversation(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行完整对话流程
        
        Args:
            user_message: 用户消息
            system_message: 可选的系统提示
            conversation_history: 可选的对话历史
            task_id: 可选的任务 ID
        
        Returns:
            包含响应和消息历史的字典
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
                task_id=task_id
            )
            
            return {
                "response": result.get("final_response", ""),
                "messages": result.get("messages", []),
                "timestamp": datetime.now().isoformat(),
                "model": self.model
            }
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        获取 Agent 能力信息
        """
        return {
            "framework": "hermes-agent",
            "version": "1.0.0",
            "provider": self.provider,
            "model": self.model,
            "initialized": self._is_initialized,
            "capabilities": [
                "natural_language_understanding",
                "tool_calling",
                "persistent_memory",
                "skill_learning",
                "subagent_delegation",
                "scheduled_tasks"
            ]
        }


hermes_agent_service = HermesAgentService()
