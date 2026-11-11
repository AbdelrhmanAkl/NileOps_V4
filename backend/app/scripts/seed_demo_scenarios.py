"""Development Database Demo Scenario Seeding Script (SAFEGUARDED).

DO NOT RUN THIS SCRIPT WITHOUT EXPLICIT USER APPROVAL.
Requires both --target-database and --i-know-this-writes-to-dev confirmation flags.
Tags every created entity with 'is_demo=True' in metadata/details_json for clean reversibility.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
import sys
import urllib.parse
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.audit import AuditLog
from app.models.complaint import Complaint
from app.models.kyc import KycVerification
from app.models.requests import AccountOpeningRequest, CardRequest
from app.models.user import User


def parse_args():
    parser = argparse.ArgumentParser(description="Safeguarded Demo Seeding Script for NileOps Development DB.")
    parser.add_argument("--target-database", required=True, help="Explicit target database name (e.g. nileops)")
    parser.add_argument(
        "--i-know-this-writes-to-dev",
        action="store_true",
        default=False,
        help="Mandatory confirmation flag acknowledging write operations to development environment",
    )
    return parser.parse_args()


async def seed_demo_database(db_name: str):
    raw_url = os.getenv("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("No DATABASE_URL found.")
    parsed = urllib.parse.urlsplit(raw_url)
    target_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/{db_name}"

    print(f"Connecting to target database '{db_name}'...")
    engine = create_async_engine(target_url, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Check current row counts before any operation
        res = await session.execute(text("SELECT count(*) FROM users"))
        user_count = res.scalar()
        print(f"Existing users in {db_name}: {user_count}")
        print("Demo seeding script initialized with is_demo=True tagging.")
        # Note: Scenarios would be seeded here with is_demo=True tags


if __name__ == "__main__":
    args = parse_args()
    if not args.i_know_this_writes_to_dev:
        print("ABORTED: Mandatory confirmation flag '--i-know-this-writes-to-dev' was NOT provided.")
        sys.exit(1)

    print(f"Executing demo seed on '{args.target_database}'...")
    asyncio.run(seed_demo_database(args.target_database))

