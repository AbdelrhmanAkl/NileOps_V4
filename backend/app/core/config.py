import os
from typing import List

try:
    from pydantic_settings import BaseSettings
    
    class Settings(BaseSettings):
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        PROJECT_NAME: str = "NileOps Digital Banking Operations"
        API_V1_PREFIX: str = "/api/v1"

        # Security & Authentication
        SECRET_KEY: str = "change-this-insecure-key-to-a-secure-256-bit-random-secret"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        # Primary Database (PostgreSQL 16)
        POSTGRES_SERVER: str = "localhost"
        POSTGRES_PORT: int = 5432
        POSTGRES_USER: str = "nileops_app"
        POSTGRES_PASSWORD: str = "nileops_dev_pass"
        POSTGRES_DB: str = "nileops_db"
        DATABASE_URL: str = "postgresql+asyncpg://nileops_app:nileops_dev_pass@localhost:5432/nileops_db"

        # Vector Database (Qdrant)
        QDRANT_HOST: str = "localhost"
        QDRANT_PORT: int = 6333
        QDRANT_GRPC_PORT: int = 6334
        QDRANT_COLLECTION: str = "nileops_kb"
        EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
        EMBEDDING_DIMENSION: str = "dynamic"

        # AI / Ollama Inference
        OLLAMA_BASE_URL: str = "http://localhost:11434"
        OLLAMA_MODEL: str = "qwen3:8b"

        # Document Upload & Storage
        UPLOAD_DIR: str = "backend/uploads"
        MAX_UPLOAD_SIZE_BYTES: int = 15728640  # 15 MB

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
        ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")))
        REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))

        # Primary Database (PostgreSQL 16)
        POSTGRES_SERVER: str = Field(default_factory=lambda: os.getenv("POSTGRES_SERVER", "localhost"))
        POSTGRES_PORT: int = Field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
        POSTGRES_USER: str = Field(default_factory=lambda: os.getenv("POSTGRES_USER", "nileops_app"))
        POSTGRES_PASSWORD: str = Field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "nileops_dev_pass"))
        POSTGRES_DB: str = Field(default_factory=lambda: os.getenv("POSTGRES_DB", "nileops_db"))
        DATABASE_URL: str = Field(
            default_factory=lambda: os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://nileops_app:nileops_dev_pass@localhost:5432/nileops_db"
            )
        )

        # Vector Database (Qdrant)
        QDRANT_HOST: str = Field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
        QDRANT_PORT: int = Field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
        QDRANT_GRPC_PORT: int = Field(default_factory=lambda: int(os.getenv("QDRANT_GRPC_PORT", "6334")))
        QDRANT_COLLECTION: str = Field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "nileops_kb"))
        EMBEDDING_MODEL: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
        EMBEDDING_DIMENSION: str = Field(default_factory=lambda: os.getenv("EMBEDDING_DIMENSION", "dynamic"))

        # AI / Ollama Inference
        OLLAMA_BASE_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
        OLLAMA_MODEL: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))

        # Document Upload & Storage
        UPLOAD_DIR: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "backend/uploads"))
        MAX_UPLOAD_SIZE_BYTES: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "15728640")))

        # CORS Origins
        ALLOWED_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]


settings = Settings()
