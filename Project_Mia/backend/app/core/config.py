"""核心配置"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Literal

class Settings(BaseSettings):
    # API配置
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Project_Mia"
    
    # AI Provider配置 (支持 OpenAI 兼容接口和 Gemini)
    AI_PROVIDER: Literal["gemini", "openai"] = "openai"
    
    # Gemini配置 (Google AI Studio — 备用)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"
    
    # OpenAI 兼容接口配置 (DeepSeek / VectorEngine / etc)
    # ⚠️ 风险标记: API Key 通过 .env 注入，注意不要将 .env 提交到版本控制
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_MODEL: str = "deepseek-v4-pro"
    

    # Vision 模型配置 (用于图片批改 — Gemini via coreloop)
    VISION_API_KEY: str = ""
    VISION_BASE_URL: str = "https://api.coreloop.cool:50001/v1"
    VISION_MODEL: str = "gemini-2.5-flash"

    # 数据库
    DATABASE_DIR: Path = Path(__file__).parent.parent.parent / "data"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
