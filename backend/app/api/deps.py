"""NileOps Shared API Dependencies."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

# Re-export get_db dependency
get_db = get_db_session
