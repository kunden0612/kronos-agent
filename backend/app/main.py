from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from .core.config import settings
from .api.v1.auth import router as auth_router
from .api.v1.chat import router as chat_router
from .services.kronos_client import kronos_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

app = FastAPI(
    title="Hermes-Kronos Backend API",
    description="API Gateway for Hermes-Kronos Intelligent Financial Prediction System",
    version="1.0.0",
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


@app.get("/")
async def root():
    return {
        "message": "Hermes-Kronos Backend API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    kronos_health = await kronos_client.health_check()
    kronos_status = kronos_health.get("status", "unknown")

    return {
        "status": "healthy" if kronos_status == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "kronos_service": kronos_status,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
