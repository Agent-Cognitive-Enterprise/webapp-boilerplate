# /backend/ai/open_ai_api_client.py

import asyncio
from typing import Optional

import httpcore
import httpx
from openai import AsyncOpenAI, APITimeoutError, RateLimitError
import logging

from settings import (
    OPENAI_TIMEOUT_BACKOFF_SECONDS,
    OPENAI_TIMEOUT_RETRY_LIMIT,
)
from services.system_settings import get_provider_api_key_from_db
from utils.profiling import measure_time


logging.basicConfig(level=logging.INFO)


# Reuse a single async client
_aclient: Optional[AsyncOpenAI] = None
_client_api_key: Optional[str] = None


OPENAI_RETRY_EXCEPTIONS = (
    asyncio.TimeoutError,
    APITimeoutError,
    RateLimitError,
    httpx.ReadTimeout,
    httpcore.ReadTimeout,
)


async def get_openai_client() -> AsyncOpenAI:
    """
    Initializes and returns an OpenAI API client using the provided API key.
    """

    global _aclient, _client_api_key
    resolved_key = await get_provider_api_key_from_db("openai")
    if not resolved_key:
        raise RuntimeError("OpenAI API key is not configured")

    if _aclient is None or _client_api_key != resolved_key:
        _aclient = AsyncOpenAI(
            api_key=resolved_key,
            timeout=100,
            # timeout=httpx.Timeout(10.0, read=10.0, connect=10.0),
            # max_retries=0,
        )
        _client_api_key = resolved_key

    return _aclient


# noinspection PyTypeChecker
@measure_time
async def get_openai_response(
    prompt: str,
    stream: bool = False,
    model: str = "gpt-4.1-mini",
    max_tokens: int = 100,
    temperature: float = 0.0,
    system_prompt: str = "You are a helpful assistant.",
) -> str:
    """
    Sends a prompt to the OpenAI API and returns the generated response.

    If stream=True, deltas are yielded from the server as they arrive.
    The function aggregates them into a final string return value.
    Pass `on_delta` to receive each text chunk as it's produced.
    """
    client = await get_openai_client()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    for attempt in range(1, OPENAI_TIMEOUT_RETRY_LIMIT + 1):
        try:
            if stream:
                final_text_parts: list[str] = []
                try:
                    stream_resp = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    async for chunk in stream_resp:
                        try:
                            delta = chunk.choices[0].delta
                            text = getattr(delta, "content", None)
                            if text:
                                final_text_parts.append(text)
                        except (Exception,):
                            # Ignore non-text deltas or malformed chunks
                            continue
                except Exception as exc:
                    raise exc

                return "".join(final_text_parts)

            # Non-streaming
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content or ""

        except OPENAI_RETRY_EXCEPTIONS as exc:
            if attempt == OPENAI_TIMEOUT_RETRY_LIMIT:
                raise exc
            await asyncio.sleep(OPENAI_TIMEOUT_BACKOFF_SECONDS * attempt)

    return ""


# noinspection PyTypeChecker
@measure_time
async def get_openai_response_five_one(
    prompt: str,
    stream: bool = False,
    model: str = "gpt-5.1",
    max_tokens: int = 100,
    temperature: float = 0.0,
    system_prompt: str = "You are a helpful assistant.",
) -> str:
    """
    Sends a prompt to the OpenAI API and returns the generated response.

    If stream=True, deltas are yielded from the server as they arrive.
    The function aggregates them into a final string return value.
    Pass `on_delta` to receive each text chunk as it's produced.
    """
    client = await get_openai_client()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    for attempt in range(1, OPENAI_TIMEOUT_RETRY_LIMIT + 1):
        try:
            if stream:
                final_text_parts: list[str] = []
                try:
                    stream_resp = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True,
                        max_tokens=max_tokens,
                    )
                    async for chunk in stream_resp:
                        try:
                            delta = chunk.choices[0].delta
                            text = getattr(delta, "content", None)
                            if text:
                                final_text_parts.append(text)
                        except (Exception,):
                            # Ignore non-text deltas or malformed chunks
                            continue
                except Exception as exc:
                    raise exc

                return "".join(final_text_parts)

            # Non-streaming
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        except OPENAI_RETRY_EXCEPTIONS as exc:
            if attempt == OPENAI_TIMEOUT_RETRY_LIMIT:
                raise exc
            await asyncio.sleep(OPENAI_TIMEOUT_BACKOFF_SECONDS * attempt)

    return ""


async def main() -> None:

    test_prompt = "What is the capital of France?"

    answer = await get_openai_response(
        test_prompt,
        stream=True,
        model="gpt-4.1-mini",
        max_tokens=128,
        temperature=0.0,
        system_prompt="You are a scraper-hint reviewer.",
    )
    print("me:", test_prompt)
    print("AI:", answer)


if __name__ == "__main__":
    asyncio.run(main())

# me: list all valid models for OpenAI chat completions api including gpt-4.1 and gpt-5 and mini variations. Show results as a table, order them by intelligence.
# AI: As of my knowledge cutoff in June 2024, here is a list of valid OpenAI Chat Completion API models including GPT-4.1, GPT-5, and their mini variations, ordered by estimated intelligence and capabilities from strongest to lighter/smaller versions.
#
# | Model Name           | Description                              | Notes                             |
# |----------------------|----------------------------------------|----------------------------------|
# | gpt-5                | Latest flagship GPT model               | Most advanced, highest capability|
# | gpt-5-mini           | Smaller variant of GPT-5                | Lower latency, fewer parameters  |
# | gpt-4.1              | Improved GPT-4 version                   | Better reasoning than GPT-4       |
# | gpt-4.1-mini         | Smaller GPT-4.1 variation                | Faster, less expensive            |
# | gpt-4                | Previous flagship model                  | Very strong, high reliability    |
# | gpt-4-mini           | Smaller GPT-4 variant                    | Faster inference                  |
# | gpt-3.5-turbo        | High-performance GPT-3.5 variant        | Widely used, cost-effective      |
# | gpt-3.5-turbo-mini   | Mini version of GPT-3.5-turbo            | Low latency, light compute       |
#
# ### Notes:
# - "Mini" variations trade off some performance for speed and cost-efficiency.
# - Models like GPT-5 and GPT-4.1 (and their minis) are speculative based on typical OpenAI versioning patterns and known announcements as of mid-2024.
# - Always check OpenAI official documentation or API endpoint `/models` listing for the most current available models.
#
# If you want me to fetch the exact current list from OpenAI API or show usage examples, I can help with that too!
