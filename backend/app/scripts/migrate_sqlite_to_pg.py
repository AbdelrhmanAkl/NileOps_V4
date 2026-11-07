"""Migration script from SQLite nileops_mvp.db to PostgreSQL 16."""

import asyncio
import os
import sys
from pathlib import Path

# Set PYTHONPATH
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.base import Base
import app.models  # Register all models


async def migrate():
    sqlite_url = "sqlite+aiosqlite:///C:/AI/NileOps_V4/backend/nileops_mvp.db"
    pg_url = settings.DATABASE_URL
    print(f"Migrating from {sqlite_url} to PostgreSQL ({pg_url})")

    # Connect to SQLite
    sqlite_engine = create_async_engine(sqlite_url, echo=False)
    sqlite_sessionmaker = async_sessionmaker(sqlite_engine, expire_on_commit=False)

    # Connect to PostgreSQL
    pg_engine = create_async_engine(pg_url, echo=False)
    pg_sessionmaker = async_sessionmaker(pg_engine, expire_on_commit=False)

    # Initialize PostgreSQL schema
    print("Creating tables in PostgreSQL...")
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("PostgreSQL tables created successfully.")

    # Table migration order respecting foreign keys:
    # 1. users
    # 2. accounts (FK to users)
    # 3. transactions (FK to accounts)
    # 4. complaints (FK to users)
    # 5. kyc_verifications (FK to users)
    # 6. policy_documents (FK to users)
    # 7. audit_logs (FK to users)

    models_order = [
        app.models.User,
        app.models.Account,
        app.models.Transaction,
        app.models.Complaint,
        app.models.KycVerification,
        app.models.PolicyDocument,
        app.models.AuditLog,
    ]

    async with sqlite_sessionmaker() as s_session, pg_sessionmaker() as pg_session:
        for model in models_order:
            table_name = model.__tablename__
            # Read from SQLite
            result = await s_session.execute(select(model))
            records = result.scalars().all()
            print(f"Read {len(records)} records for {table_name} from SQLite.")

            # Check existing count in PostgreSQL
            pg_res = await pg_session.execute(select(model))
            existing_count = len(pg_res.scalars().all())

            if existing_count == 0 and records:
                for rec in records:
                    # Detach from session by creating a clean copy of attributes
                    cols = {c.name: getattr(rec, c.name) for c in model.__table__.columns}
                    new_rec = model(**cols)
                    pg_session.add(new_rec)
                await pg_session.commit()
                print(f"Migrated {len(records)} records into PostgreSQL {table_name}.")
            else:
                print(f"PostgreSQL {table_name} already has {existing_count} records. Skipping.")

    # Verification
    print("\n--- Verification Summary ---")
    async with pg_sessionmaker() as pg_session:
        for model in models_order:
            table_name = model.__tablename__
            res = await pg_session.execute(select(model))
            cnt = len(res.scalars().all())
            print(f"PostgreSQL table '{table_name}': {cnt} rows")

    await sqlite_engine.dispose()
    await pg_engine.dispose()
    print("Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
