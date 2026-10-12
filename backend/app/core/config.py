from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import List, Union, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "documind"
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/documind"
    
    SUPABASE_URL: str = "http://localhost:8000"
    SUPABASE_JWT_SECRET: str = "your-jwt-secret-at-least-32-characters-long"
    SUPABASE_JWT_PUBLIC_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    ENABLE_DEMO_LOGIN: bool = True
    
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    OPENAI_API_KEY: str = ""
    
    # Upload
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024
    STORAGE_DIR: str = "storage/documents"
    
    # OCR
    OCR_DPI: int = 300
    OCR_MAX_IMAGE_PIXELS: int = 150000000
    OCR_LANGUAGES: str = "eng"
    OCR_MIN_CHARS_PER_PAGE: int = 50
    OCR_FAILURE_POLICY: str = "fail_if_all_failed"

    # RAG
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 80
    CHUNK_SIZE_CHARS: int = 800
    CHUNK_OVERLAP_CHARS: int = 120
    EMBEDDING_DIM: int = 384
    TOP_K: int = 5
    MIN_SIMILARITY: float = 0.20
    
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
