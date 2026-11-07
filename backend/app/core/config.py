import os
from typing import List
from pydantic import Field

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")
        PROJECT_NAME: str = "NileOps Digital Banking Operations"
        API_V1_PREFIX: str = "/api/v1"

        # Security & Authentication
        SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-insecure-key-to-a-secure-256-bit-random-secret")
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        # Database (Supports SQLite for Native Windows MVP; portable to PostgreSQL 16)
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nileops_mvp.db")

        # Document Upload & Storage
        UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "backend/uploads")
        MAX_UPLOAD_SIZE_BYTES: int = 15728640  # 15 MB

        # AI & Vector DB Integration
        QDRANT_URL: str = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
        OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")

        # AI & Vector DB Integration
        QDRANT_URL: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
        OLLAMA_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"))
        OLLAMA_MODEL: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))

        # CORS Origins
        ALLOWED_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

        class Config:
            env_file = ".env"
            case_sensitive = True
            extra = "ignore"

except ImportError:
    from pydantic import BaseModel, Field

    class Settings(BaseModel):  # type: ignore[no-redef]
        ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
        DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "t"))
        PROJECT_NAME: str = Field(default_factory=lambda: os.getenv("PROJECT_NAME", "NileOps Digital Banking Operations"))
        API_V1_PREFIX: str = Field(default_factory=lambda: os.getenv("API_V1_PREFIX", "/api/v1"))

        # Security & Authentication
        SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", "change-this-insecure-key-to-a-secure-256-bit-random-secret"))
        ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
        ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")))
        REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))

        # Database
        DATABASE_URL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./nileops_mvp.db"))

        # Document Upload & Storage
        UPLOAD_DIR: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "backend/uploads"))
        MAX_UPLOAD_SIZE_BYTES: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "15728640")))

        # AI & Vector DB Integration
        QDRANT_URL: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
        OLLAMA_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"))
        OLLAMA_MODEL: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))

        # CORS Origins
        ALLOWED_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]


settings = Settings()
