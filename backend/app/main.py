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

    # 3. Guard 4(c): Verify Qdrant collection integrity at startup
    qdrant_startup_error = None
    try:
        from app.services.embedding import embedding_service
        from app.services.vector_store import qdrant_service

        expected_dim = await embedding_service.probe_dimension()
        collections = [c.name for c in qdrant_service.client.get_collections().collections]
        if qdrant_service.collection_name not in collections:
            qdrant_startup_error = f"Qdrant collection '{qdrant_service.collection_name}' does not exist."
        else:
            col_info = qdrant_service.client.get_collection(qdrant_service.collection_name)
            points_count = getattr(col_info, "points_count", 0) or 0
            vectors_cfg = getattr(getattr(col_info, "config", None), "params", None)
            actual_dim = getattr(getattr(vectors_cfg, "vectors", None), "size", None)
            if actual_dim is None and isinstance(getattr(vectors_cfg, "vectors", None), dict):
                actual_dim = getattr(vectors_cfg, "vectors", {}).get("size")

            if points_count == 0:
                qdrant_startup_error = f"Qdrant collection '{qdrant_service.collection_name}' is empty (0 points)."
            elif actual_dim is not None and actual_dim != expected_dim:
                qdrant_startup_error = (
                    f"Qdrant vector size mismatch: collection has {actual_dim}, "
                    f"embedding model requires {expected_dim}."
                )

        if qdrant_startup_error:
            import logging
            logging.getLogger("uvicorn.error").error(f"[NileOps Qdrant Integrity Error] {qdrant_startup_error}")
    except Exception as e:
        import logging
        qdrant_startup_error = f"Qdrant startup verification check failed: {e}"
        logging.getLogger("uvicorn.error").error(f"[NileOps Qdrant Integrity Error] {qdrant_startup_error}")

    app.state.qdrant_error = qdrant_startup_error

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
        qdrant_err = getattr(app.state, "qdrant_error", None)
        res = {
            "status": "healthy" if not qdrant_err else "degraded",
            "service": "NileOps Backend",
            "version": "1.0.0",
            "database": db_type,
        }
        if qdrant_err:
            res["qdrant_error"] = qdrant_err
        return res

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
