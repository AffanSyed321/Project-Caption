from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Captionator"

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None

    @field_validator('OPENAI_API_KEY', mode='before')
    @classmethod
    def strip_api_key(cls, v):
        """Strip whitespace from API key to handle Railway env var issues"""
        if v is not None and isinstance(v, str):
            return v.strip()
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# CORS Settings (not from .env to avoid parsing issues)
BACKEND_CORS_ORIGINS: List[str] = ["*"]

