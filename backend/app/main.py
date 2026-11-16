"""NileOps Intelligent Digital Banking Operations Platform — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    is_production = settings.ENVIRONMENT.lower() == "production"
    docs_enabled = (not is_production) and settings.DEBUG and settings.ENABLE_DOCS

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Bilingual Intelligent Digital Banking Operations Platform (Simulation: NileOps Demo Bank)",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
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

    # Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # Static frontend distribution path
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    index_html = frontend_dist / "index.html"
    assets_dir = frontend_dist / "assets"

    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Root endpoint: serves SPA index.html for browser navigation, JSON metadata for API probes
    @app.get("/", tags=["Root"])
    async def root(request: Request):
        """Root endpoint with SPA browser serving and API probe fallback."""
        accept = request.headers.get("accept", "")
        if "text/html" in accept and index_html.exists():
            return FileResponse(index_html)
        return {
            "platform": settings.PROJECT_NAME,
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if docs_enabled else "disabled",
        }

    # SPA Fallback for client-side routing (e.g. /customer, /employee, /login)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = (frontend_dist / full_path).resolve()
        if file_path.is_file() and str(file_path).startswith(str(frontend_dist)):
            return FileResponse(file_path)
        if index_html.exists():
            return FileResponse(index_html)
        raise HTTPException(status_code=404, detail="Page not found")

    return app


app = create_application()
