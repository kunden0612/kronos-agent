from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    KRONOS_SERVICE_URL: str = "http://kronos:8001"
    
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "kronos"
    POSTGRES_PASSWORD: str = "kronos"
    POSTGRES_DB: str = "kronos"
    POSTGRES_PORT: int = 5432
    
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
