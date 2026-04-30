from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os

from .core.config import settings
from .api.v1.auth import router as auth_router
from .api.v1.chat import router as chat_router
from .services.kronos_client import kronos_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hermes-Kronos Backend API",
    description="基于 Hermes-Agent 框架的智能金融预测系统 API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("Starting Hermes-Kronos Backend API...")
    
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from .tools import kronos_tools
        logger.info("Kronos tools loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load Kronos tools: {e}")
    
    try:
        health = await kronos_client.health_check()
        logger.info(f"Kronos service status: {health.get('status', 'unknown')}")
    except Exception as e:
        logger.warning(f"Kronos service health check failed: {e}")
    
    logger.info("Application startup complete")


@app.get("/")
async def root():
    return {
        "message": "Hermes-Kronos Backend API",
        "version": "2.0.0",
        "framework": "Hermes-Agent",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    kronos_health = await kronos_client.health_check()
    kronos_status = kronos_health.get("status", "unknown")

    return {
        "status": "healthy" if kronos_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "kronos_service": kronos_status,
        "framework": "Hermes-Agent v1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
