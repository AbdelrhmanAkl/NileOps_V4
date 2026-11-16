"""In-Memory Sliding Window Rate Limiter & Account Lockout Guard.

Provides production defenses against credential-stuffing brute force attacks,
denial-of-service on LLM/RAG vector search, and runaway API queries.
"""

import asyncio
import math
import time
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, Request, status

from app.core.config import settings


class RateLimitExceeded(HTTPException):
    def __init__(self, detail: str, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """Sliding-window in-memory rate limiter with thread-safe lock protection."""

    def __init__(self):
        # Key: (endpoint, identifier) -> list of timestamp floats
        self._requests: Dict[Tuple[str, str], List[float]] = {}
        # Key: username -> (consecutive_failures, locked_until_timestamp)
        self._login_failures: Dict[str, Tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "127.0.0.1"

    async def check_rate_limit(
        self,
        request: Request,
        endpoint_tag: str,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None,
        identifier_override: Optional[str] = None,
    ):
        """Check if request exceeds rate limit; raises HTTP 429 with Retry-After if exceeded."""
        if not settings.RATE_LIMIT_ENABLED:
            return

        max_req = max_requests if max_requests is not None else settings.RATE_LIMIT_RAG_MAX
        window = window_seconds if window_seconds is not None else settings.RATE_LIMIT_RAG_WINDOW_SECONDS

        now = time.time()
        identifier = identifier_override or self._get_client_ip(request)
        key = (endpoint_tag, identifier)

        async with self._lock:
            timestamps = self._requests.get(key, [])
            cutoff = now - window
            timestamps = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= max_req:
                oldest_in_window = timestamps[0]
                retry_after = max(1, math.ceil(oldest_in_window + window - now))
                raise RateLimitExceeded(
                    detail=f"Rate limit exceeded for {endpoint_tag}. Maximum {max_req} requests per {window}s. Try again in {retry_after} seconds.",
                    retry_after=retry_after,
                )

            timestamps.append(now)
            self._requests[key] = timestamps

    async def check_login_lockout(self, username: str):
        """Check if account is temporarily locked out due to repeated failed logins."""
        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.time()
        clean_user = username.strip().lower()

        async with self._lock:
            failures, locked_until = self._login_failures.get(clean_user, (0, 0.0))
            if locked_until > now:
                retry_after = max(1, math.ceil(locked_until - now))
                raise RateLimitExceeded(
                    detail=f"Account '{clean_user}' is temporarily locked due to repeated failed login attempts. Retry in {retry_after} seconds.",
                    retry_after=retry_after,
                )
            elif locked_until > 0.0:
                # Lockout period expired: reset failures
                self._login_failures[clean_user] = (0, 0.0)

    async def record_login_attempt(self, username: str, success: bool):
        """Update consecutive failed logins; triggers temporary lockout when threshold reached."""
        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.time()
        clean_user = username.strip().lower()

        async with self._lock:
            if success:
                self._login_failures.pop(clean_user, None)
            else:
                failures, locked_until = self._login_failures.get(clean_user, (0, 0.0))
                if locked_until > 0.0 and now > locked_until:
                    failures = 0
                failures += 1

                if failures >= settings.LOGIN_LOCKOUT_MAX_FAILURES:
                    lock_duration = settings.LOGIN_LOCKOUT_DURATION_SECONDS
                    self._login_failures[clean_user] = (failures, now + lock_duration)
                else:
                    self._login_failures[clean_user] = (failures, 0.0)

    def reset_for_tests(self):
        """Reset internal rate limit and lockout state (strictly for automated tests)."""
        self._requests.clear()
        self._login_failures.clear()


limiter = RateLimiter()

