from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    FROM_NAME: str
    ADMIN_EMAIL: str
    
    # Application
    APP_NAME: str = "ArrivApp"
    APP_VERSION: str = "2.0.0"
    LATE_THRESHOLD_HOUR: int = 9
    LATE_THRESHOLD_MINUTE: int = 1
    CHECK_ABSENT_TIME: str = "09:10"
    TIMEZONE: str = "Europe/Madrid"
    FRONTEND_URL: str = "http://localhost:8080"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
