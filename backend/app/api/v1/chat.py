from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from ...models.schemas import ChatRequest, ChatResponse
from ...services.agent_service import AgentService
from ...services.kronos_client import kronos_client

router = APIRouter(prefix="/api/v1", tags=["chat"])

logger = logging.getLogger(__name__)

agent_service = AgentService(kronos_client)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理用户聊天消息"""
    try:
        result = await agent_service.process_message(
            message=request.message,
            conversation_id=request.conversation_id
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"处理消息失败：{str(e)}")


@router.post("/predict")
async def direct_predict(symbol: str, pred_len: int = 5):
    """直接调用预测接口（绕过对话）"""
    try:
        result = await kronos_client.predict(symbol=symbol, pred_len=pred_len)
        return result
    except Exception as e:
        logger.error(f"Error in direct predict: {e}")
        raise HTTPException(status_code=500, detail=str(e))
