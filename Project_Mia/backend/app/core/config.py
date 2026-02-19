"""核心配置"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Literal

class Settings(BaseSettings):
    # API配置
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Project_Mia"
    
    # AI Provider配置 (支持Gemini和OpenAI兼容接口)
    AI_PROVIDER: Literal["gemini", "openai"] = "openai"  # 默认使用OpenAI兼容接口
    
    # Gemini配置 (Google AI Studio)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    
    # OpenAI兼容接口配置 (VectorEngine / DeepSeek / etc)
    OPENAI_API_KEY: str = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
    OPENAI_BASE_URL: str = "https://api.vectorengine.ai/v1"
    OPENAI_MODEL: str = "gemini-3-flash-preview"
    
    # 数据库
    DATABASE_DIR: Path = Path(__file__).parent.parent.parent / "data"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
