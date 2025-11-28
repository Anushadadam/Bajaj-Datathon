"""Configuration management for the Bill Extraction API"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "3000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Google Cloud Vision API
    google_cloud_vision_api_key: Optional[str] = os.getenv("GOOGLE_CLOUD_VISION_API_KEY")
    use_google_vision: bool = os.getenv("USE_GOOGLE_VISION", "true").lower() == "true"
    
    # Tesseract (fallback OCR)
    tesseract_path: str = os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")
    
    # Google Gemini API
    google_gemini_api_key: Optional[str] = os.getenv("GOOGLE_GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "8192"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
