"""
Hermes Agent Chat API

This module exposes the complete capabilities of Hermes Agent through REST API endpoints,
including:
- Full conversation loop with tool calling
- Streaming responses
- Tool management
- Session management
- Capability discovery
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any, Callable

from ...models.schemas import ChatRequest, ChatResponse, User, Token
from ...services.hermes_agent_service import hermes_agent_service, HermesAgentService
from ..v1.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


def get_agent() -> HermesAgentService:
    """Dependency to get the Hermes Agent service instance"""
    return hermes_agent_service


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Process user chat message using Hermes Agent
    
    This endpoint provides access to the full Hermes Agent capabilities including:
    - Natural language understanding
    - Tool calling (including Kronos prediction)
    - Memory integration
    - Context management
    """
    try:
        logger.info(f"Processing chat from user {current_user.email}: {request.message[:50]}...")
        
        response = await agent.chat(
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(
            message=response,
            conversation_id=request.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            prediction=None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理消息失败：{str(e)}")


@router.post("/chat/conversation")
async def run_conversation(
    user_message: str,
    system_message: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    task_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Run a complete conversation with full Hermes capabilities
    
    This endpoint exposes the complete AIAgent.run_conversation() method,
    providing access to:
    - Full tool calling loop
    - Context compression
    - Memory management
    - Streaming support
    - Complete message history
    
    Args:
        user_message: The user's input message
        system_message: Custom system prompt (optional)
        conversation_history: Previous messages for context
        task_id: Unique task identifier for isolation
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
        logger.error(f"Conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话处理失败：{str(e)}")


@router.websocket("/chat/stream")
async def chat_stream(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_agent)
):
    """
    WebSocket endpoint for streaming chat responses
    
    Provides real-time streaming of agent responses including:
    - Token-by-token response streaming
    - Tool execution updates
    - Status updates
    - Reasoning steps
    """
    await websocket.accept()
    
    async def stream_handler(delta: str):
        """Send streaming delta to client"""
        await websocket.send_json({"type": "delta", "content": delta})
    
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message:
                await websocket.send_json({"type": "error", "message": "消息不能为空"})
                continue
            
            result = await agent.run_conversation(
                user_message=message,
                stream_callback=stream_handler
            )
            
            await websocket.send_json({
                "type": "complete",
                "response": result.get("response", ""),
                "messages": result.get("messages", []),
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()


@router.post("/agent/initialize")
async def initialize_agent(agent: HermesAgentService = Depends(get_agent)):
    """
    Initialize Hermes Agent with all capabilities
    
    This endpoint initializes the AIAgent instance with:
    - Tool registration (including Kronos tools)
    - Memory management setup
    - Callback registration
    - Provider configuration
    """
    try:
        await agent.initialize()
        return {
            "status": "success",
            "message": "Hermes Agent 初始化成功",
            "capabilities": agent.get_capabilities()
        }
    except Exception as e:
        logger.error(f"Agent initialization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"初始化失败：{str(e)}")


@router.get("/agent/capabilities")
async def get_capabilities(agent: HermesAgentService = Depends(get_agent)):
    """
    Get Hermes Agent capabilities overview
    
    Returns information about:
    - Enabled toolsets
    - Registered tools
    - Provider configuration
    - Available capabilities
    """
    try:
        capabilities = agent.get_capabilities()
        return {
            "status": "success",
            "capabilities": capabilities
        }
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取能力信息失败：{str(e)}")


@router.get("/agent/tools")
async def get_tools(agent: HermesAgentService = Depends(get_agent)):
    """
    Get all available tools registered with Hermes Agent
    
    Returns detailed information about each tool including:
    - Tool name
    - Description
    - Parameters
    - Toolset membership
    """
    try:
        tools = agent.get_available_tools()
        return {
            "status": "success",
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        logger.error(f"Failed to get tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取工具列表失败：{str(e)}")


@router.post("/agent/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    args: Dict[str, Any],
    task_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Direct tool invocation
    
    Allows direct calling of any registered tool including:
    - kronos_predict: Predict financial asset prices
    - kronos_batch_predict: Batch predict multiple assets
    - And any other Hermes tools
    
    Args:
        tool_name: Name of the tool to call
        args: Tool arguments as JSON object
        task_id: Optional task identifier for isolation
    """
    try:
        logger.info(f"Calling tool {tool_name} with args: {args}")
        
        result = await agent.call_tool(tool_name, args, task_id)
        
        try:
            result_json = {"result": result}
        except:
            result_json = {"result": result}
        
        return {
            "status": "success",
            "tool": tool_name,
            "result": result_json
        }
    except Exception as e:
        logger.error(f"Tool call error {tool_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"工具调用失败：{str(e)}")


@router.post("/agent/session")
async def create_session(
    user_id: Optional[str] = None,
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Create a new session for conversation management
    
    Sessions allow tracking conversation history and state across multiple requests.
    
    Args:
        user_id: Optional user identifier for session association
    """
    try:
        session_id = agent.create_session(user_id)
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Session created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建会话失败：{str(e)}")


@router.get("/agent/session/{session_id}")
async def get_session(
    session_id: str,
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Get session information by ID
    
    Args:
        session_id: The session identifier
    """
    try:
        session = agent.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "status": "success",
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话失败：{str(e)}")


@router.delete("/agent/session/{session_id}")
async def close_session(
    session_id: str,
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Close a session and release resources
    
    Args:
        session_id: The session identifier to close
    """
    try:
        agent.close_session(session_id)
        return {
            "status": "success",
            "message": "会话已关闭"
        }
    except Exception as e:
        logger.error(f"Failed to close session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"关闭会话失败：{str(e)}")


@router.post("/predict")
async def direct_predict(
    symbol: str,
    pred_len: int = 5,
    model_name: Optional[str] = None,
    lookback: int = 400,
    freq: str = "daily",
    sample_count: int = 5,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Direct Kronos prediction via tool call
    
    This is a convenience endpoint that directly calls the kronos_predict tool,
    providing a simplified interface for financial predictions.
    
    Args:
        symbol: Asset symbol (e.g., "600519.SH", "AAPL", "BTC/USDT")
        pred_len: Number of trading days to predict
        model_name: Kronos model name
        lookback: Historical lookback window
        freq: Data frequency
        sample_count: Number of sampling paths for confidence interval
    """
    try:
        result = await agent.call_tool("kronos_predict", {
            "symbol": symbol,
            "pred_len": pred_len,
            "model_name": model_name,
            "lookback": lookback,
            "freq": freq,
            "sample_count": sample_count
        })
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预测失败：{str(e)}")


@router.post("/predict/batch")
async def batch_predict(
    symbols: List[str],
    pred_len: int = 5,
    model_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    agent: HermesAgentService = Depends(get_agent)
):
    """
    Batch prediction for multiple assets
    
    Args:
        symbols: List of asset symbols
        pred_len: Number of trading days to predict
        model_name: Kronos model name
    """
    try:
        result = await agent.call_tool("kronos_batch_predict", {
            "symbols": symbols,
            "pred_len": pred_len,
            "model_name": model_name
        })
        
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Batch prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量预测失败：{str(e)}")
