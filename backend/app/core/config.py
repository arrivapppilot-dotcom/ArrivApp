from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Email (optional for deployment without email features)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    FROM_NAME: Optional[str] = "ArrivApp"
    ADMIN_EMAIL: Optional[str] = None
    
    # Application
    APP_NAME: str = "ArrivApp"
    APP_VERSION: str = "2.0.0"
    LATE_THRESHOLD_HOUR: int = 9
    LATE_THRESHOLD_MINUTE: int = 1
    CHECK_ABSENT_TIME: str = "09:10"
    TIMEZONE: str = "Europe/Madrid"
    FRONTEND_URL: str = "http://localhost:8080"


@lru_cache()
def get_settings():
    return Settings()
