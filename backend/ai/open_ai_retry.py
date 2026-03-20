from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeAlias

import httpcore
import httpx
from openai import APITimeoutError, RateLimitError

from settings import OPENAI_TIMEOUT_BACKOFF_SECONDS, OPENAI_TIMEOUT_RETRY_LIMIT


RetryOperation: TypeAlias = Callable[[], Awaitable[str]]

OPENAI_RETRY_EXCEPTIONS = (
    asyncio.TimeoutError,
    APITimeoutError,
    RateLimitError,
    httpx.ReadTimeout,
    httpcore.ReadTimeout,
)


async def run_with_openai_retries(
    operation: RetryOperation,
) -> str:
    for attempt in range(1, OPENAI_TIMEOUT_RETRY_LIMIT + 1):
        try:
            return await operation()
        except OPENAI_RETRY_EXCEPTIONS:
            if attempt == OPENAI_TIMEOUT_RETRY_LIMIT:
                raise
            await asyncio.sleep(OPENAI_TIMEOUT_BACKOFF_SECONDS * attempt)

    return ""
