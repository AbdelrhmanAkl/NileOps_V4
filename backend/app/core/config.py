import os
import sys
from typing import List
from pydantic import Field

def get_default_cors_origins() -> List[str]:
    origins_env = os.getenv("CORS_ORIGINS")
    if origins_env:
        # Split by comma and strip whitespace; disallow wildcard * when credentials are used
        parsed = [o.strip() for o in origins_env.split(",") if o.strip() and o.strip() != "*"]
        if parsed:
            return parsed
    return [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


INSECURE_SECRET_KEYS = {
    "change-this-insecure-key-to-a-secure-256-bit-random-secret",
    "change-this-to-a-secure-random-secret-in-production",
    "secret",
    "default",
    "changeme",
    "password",
}


def get_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "change-this-insecure-key-to-a-secure-256-bit-random-secret").strip()
    env = os.getenv("ENVIRONMENT", "development").lower()
    is_testing = (
        "pytest" in sys.modules
        or os.getenv("PYTEST_CURRENT_TEST") is not None
        or os.getenv("NILEOPS_TEST_MODE") == "1"
    )
    if not is_testing and env == "production":
        if not key or key in INSECURE_SECRET_KEYS or len(key) < 32:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Weak, default, or undersized 'SECRET_KEY' detected in production environment! "
                "Production requires a cryptographically secure random secret of at least 32 characters (256 bits)."
            )
    return key


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url or not url.strip():
        raise ValueError(
            "CRITICAL CONFIGURATION ERROR: 'DATABASE_URL' environment variable is missing or empty. "
            "NileOps production requires a valid PostgreSQL database connection string."
        )
    return url.strip()


try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")
        PROJECT_NAME: str = "NileOps Digital Banking Operations"
        API_V1_PREFIX: str = "/api/v1"

        # Security & Authentication
        SECRET_KEY: str = Field(default_factory=get_secret_key)
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7

        # Database (Mandatory PostgreSQL connection; fails loudly if not configured)
        DATABASE_URL: str = Field(default_factory=get_database_url)

        # Document Upload & Storage
        UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "backend/uploads")
        MAX_UPLOAD_SIZE_BYTES: int = 15728640  # 15 MB

        # AI & Vector DB Integration
        QDRANT_URL: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
        OLLAMA_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"))
        OLLAMA_MODEL: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))

        # CORS Origins
        ALLOWED_ORIGINS: List[str] = Field(default_factory=get_default_cors_origins)

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
        SECRET_KEY: str = Field(default_factory=get_secret_key)
        ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
        ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")))
        REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))

        # Database
        DATABASE_URL: str = Field(default_factory=get_database_url)

        # Document Upload & Storage
        UPLOAD_DIR: str = Field(default_factory=lambda: os.getenv("UPLOAD_DIR", "backend/uploads"))
        MAX_UPLOAD_SIZE_BYTES: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_BYTES", "15728640")))

        # AI & Vector DB Integration
        QDRANT_URL: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
        OLLAMA_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"))
        OLLAMA_MODEL: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen3:8b"))

        # CORS Origins
        ALLOWED_ORIGINS: List[str] = Field(default_factory=get_default_cors_origins)


settings = Settings()
