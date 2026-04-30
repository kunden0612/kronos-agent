import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    API_PREFIX: str = "/api/v1"
    
    # Model Settings
    DEFAULT_MODEL: str = "NeoQuasar/Kronos-mini"
    AVAILABLE_MODELS: list = [
        "NeoQuasar/Kronos-mini",
        "NeoQuasar/Kronos-small",
        "NeoQuasar/Kronos-base"
    ]
    MODEL_CACHE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
    
    # Data Settings
    DEFAULT_LOOKBACK: int = 400
    DEFAULT_PRED_LEN: int = 5
    DEFAULT_FREQ: str = "daily"
    DEFAULT_SAMPLE_COUNT: int = 5
    DEFAULT_TEMPERATURE: float = 1.0
    DEFAULT_TOP_P: float = 0.9
    
    # Redis Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure model cache directory exists
os.makedirs(settings.MODEL_CACHE_DIR, exist_ok=True)
