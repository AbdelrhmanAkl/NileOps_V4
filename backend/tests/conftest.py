"""Pytest Configuration and Fixtures for NileOps Backend.

Strictly enforces PostgreSQL 'nileops_test' database isolation.
The development database 'nileops' is completely unreachable from tests.
"""

import asyncio
import os
from pathlib import Path
import urllib.parse
import pytest
from starlette.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# 1. Resolve & Force Test Database URL before any application imports
env_file = Path(__file__).resolve().parent.parent / ".env"
raw_db_url = os.getenv("DATABASE_URL")
if not raw_db_url and env_file.exists():
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                raw_db_url = line.split("=", 1)[1].strip()
                break

if not raw_db_url:
    raise RuntimeError("CRITICAL: No DATABASE_URL found in environment or backend/.env")

parsed_url = urllib.parse.urlsplit(raw_db_url)
# Force target database strictly to nileops_test
test_db_url = f"{parsed_url.scheme}://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}:{parsed_url.port}/nileops_test"
os.environ["DATABASE_URL"] = test_db_url

# 2. Strict Hard-Fail Guard: Must be checked BEFORE any create_all or fixture runs
effective_parsed = urllib.parse.urlsplit(os.environ["DATABASE_URL"])
effective_db = effective_parsed.path.lstrip("/")
if effective_db != "nileops_test":
    raise RuntimeError(
        f"CRITICAL TEST ISOLATION FAILURE: Effective database is '{effective_db}', "
        f"but MUST be exactly 'nileops_test'. Aborting test execution to guarantee dev DB isolation!"
    )

# 3. Strict Qdrant Vector Collection Test Isolation Guard
test_qdrant_collection = os.getenv("QDRANT_COLLECTION", "nileops_kb_test")
if not test_qdrant_collection.endswith("_test"):
    raise RuntimeError(
        f"CRITICAL TEST ISOLATION FAILURE: Qdrant collection is '{test_qdrant_collection}', "
        f"but MUST end with '_test' (e.g. 'nileops_kb_test'). Aborting test execution to guarantee nileops_kb protection!"
    )
os.environ["QDRANT_COLLECTION"] = test_qdrant_collection

# Now safely import application modules after isolation is verified
from app.api.v1.auth import seed_demo_data
from app.core.config import settings
from app.db.base import Base
import app.db.session as session_module
from app.main import app as fastapi_app
from app.services.vector_store import qdrant_service

# Rebind qdrant_service collection strictly to test collection
qdrant_service.collection_name = test_qdrant_collection

# Verify settings also picked up the exact test database
settings_parsed = urllib.parse.urlsplit(settings.DATABASE_URL)
if settings_parsed.path.lstrip("/") != "nileops_test":
    raise RuntimeError(
        f"CRITICAL TEST ISOLATION FAILURE: Settings DATABASE_URL points to "
        f"'{settings_parsed.path.lstrip('/')}', expected 'nileops_test'!"
    )

# Rebind session module engine to use NullPool for test client thread/event-loop safety
test_engine = create_async_engine(test_db_url, poolclass=NullPool, future=True)
test_sessionmaker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
session_module.engine = test_engine
session_module.async_session_maker = test_sessionmaker


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Session-scoped fixture to initialize schema and seed baseline demo data in nileops_test."""
    # Re-verify guard inside fixture before touching database
    guard_check = urllib.parse.urlsplit(str(session_module.engine.url)).path.lstrip("/")
    if guard_check != "nileops_test":
        raise RuntimeError(
            f"ABORT: Engine connected to '{guard_check}' instead of 'nileops_test'!"
        )

    async def init():
        async with test_engine.begin() as conn:
            # Clean schema recreation for test isolation in nileops_test
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        # Seed baseline demo accounts and staff roles
        async with test_sessionmaker() as session:
            await seed_demo_data(db=session)
            await session.commit()

            # Initialize and seed isolated test collection in Qdrant
            if not qdrant_service.client.collection_exists(test_qdrant_collection):
                await qdrant_service.init_collection()
            else:
                try:
                    from qdrant_client.http import models as q_models
                    qdrant_service.client.delete(
                        collection_name=test_qdrant_collection,
                        points_selector=q_models.FilterSelector(filter=q_models.Filter()),
                    )
                except Exception:
                    pass
            await qdrant_service.reconcile_with_postgres(session=session)

    asyncio.run(init())
    yield


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client fixture for FastAPI app."""
    return TestClient(fastapi_app)
