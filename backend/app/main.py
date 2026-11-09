"""NileOps Intelligent Digital Banking Operations Platform — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import seed_demo_data
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.db.session import async_session_maker, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle handler."""
    # 1. Initialize database tables
    await init_db()

    # 2. Automatically seed demo data on fresh SQLite database
    async with async_session_maker() as session:
        try:
            await seed_demo_data(session)
        except Exception as e:
            print(f"[NileOps Startup] Demo seeder notice: {e}")

    yield


def create_application() -> FastAPI:
    """Application factory for NileOps backend service."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Bilingual Intelligent Digital Banking Operations Platform (Simulation: NileOps Demo Bank)",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS Middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Unauthenticated Health-Check Endpoint (Acceptance Criteria Requirement)
    @app.get("/health", tags=["Health"], summary="System Health Status")
    async def health_check():
        """Unauthenticated health status probe."""
        db_type = "PostgreSQL 16" if "postgresql" in settings.DATABASE_URL else "SQLite Async MVP"
        return {
            "status": "healthy",
            "service": "NileOps Backend",
            "version": "1.0.0",
            "database": db_type,
        }

    # Root redirect / greeting
    @app.get("/", tags=["Root"])
    async def root():
        """Root API metadata."""
        return {
            "platform": settings.PROJECT_NAME,
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if settings.DEBUG else "disabled",
        }

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
