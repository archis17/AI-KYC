from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/kyc_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Storage
    STORAGE_TYPE: str = "local"  # "local" or "minio"
    STORAGE_PATH: str = "./storage"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "kyc-documents"
    MINIO_SECURE: bool = False
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/kyc-process"
    N8N_API_KEY: str = ""
    
    # Internal API key for automated workflows
    INTERNAL_API_KEY: str = "change-this-in-production-use-secure-random-string"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

