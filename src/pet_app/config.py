import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration loaded from environment."""
    
    DEBUG = False
    APP_NAME = "Desktop Pet"


class AIConfig:
    """AI API configuration."""
    
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
    SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    SILICONFLOW_MODEL = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2-7B-Instruct")
    
    @classmethod
    def is_api_configured(cls) -> bool:
        """Check if API is configured."""
        return bool(cls.SILICONFLOW_API_KEY)


config = Config()
ai_config = AIConfig()
