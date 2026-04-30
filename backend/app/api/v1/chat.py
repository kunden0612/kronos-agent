from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging
from typing import Optional

from ...models.schemas import ChatRequest, ChatResponse, User
from ...services.hermes_agent_service import hermes_agent_service, HermesAgentService
from ..v1.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


def get_hermes_agent() -> HermesAgentService:
    """获取 Hermes Agent 实例"""
    return hermes_agent_service


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_hermes_agent)
):
    """
    处理用户聊天消息（使用 Hermes Agent）
    
    用户通过自然语言描述需求，Hermes Agent 自动：
    1. 理解用户意图
    2. 调用 Kronos 预测工具
    3. 整合结果并生成自然语言回复
    """
    try:
        logger.info(f"Processing chat message from user {current_user.email}")
        
        response = await agent.chat(request.message)
        
        return ChatResponse(
            message=response,
            conversation_id=request.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            prediction=None
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"处理消息失败：{str(e)}"
        )


@router.post("/chat/conversation")
async def chat_conversation(
    user_message: str,
    system_message: Optional[str] = None,
    conversation_history: Optional[list] = None,
    task_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_hermes_agent)
):
    """
    运行完整对话流程（使用 Hermes Agent）
    
    返回完整的消息历史和响应
    """
    try:
        result = await agent.run_conversation(
            user_message=user_message,
            system_message=system_message,
            conversation_history=conversation_history,
            task_id=task_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"对话处理失败：{str(e)}"
        )


@router.get("/agent/capabilities")
async def get_agent_capabilities(
    agent: HermesAgentService = Depends(get_hermes_agent)
):
    """
    获取 Hermes Agent 能力信息
    """
    try:
        capabilities = agent.get_capabilities()
        return {
            "status": "success",
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取能力信息失败：{str(e)}"
        )


@router.post("/agent/initialize")
async def initialize_agent(
    agent: HermesAgentService = Depends(get_hermes_agent)
):
    """
    初始化 Hermes Agent
    """
    try:
        await agent.initialize()
        return {
            "status": "success",
            "message": "Hermes Agent 初始化成功"
        }
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"初始化失败：{str(e)}"
        )


@router.post("/predict")
async def direct_predict(
    symbol: str,
    pred_len: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    直接调用 Kronos 预测接口（绕过对话）
    """
    try:
        from ...services.kronos_client import kronos_client
        
        result = await kronos_client.predict(
            symbol=symbol,
            pred_len=pred_len
        )
        return result
        
    except Exception as e:
        logger.error(f"Error in direct predict: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"预测失败：{str(e)}"
        )
