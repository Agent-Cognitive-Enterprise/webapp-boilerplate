from typing import Optional

import logging
from openai import AsyncOpenAI

from ai.open_ai_chat import OpenAIChatRequest
from ai.open_ai_chat import build_chat_completion_kwargs
from ai.open_ai_chat import collect_stream_text
from ai.open_ai_chat import extract_response_text
from ai.open_ai_retry import run_with_openai_retries
from services.system_settings import get_provider_api_key_from_db
from utils.profiling import measure_time


logging.basicConfig(level=logging.INFO)


# Reuse a single async client
_aclient: Optional[AsyncOpenAI] = None
_client_api_key: Optional[str] = None


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
    client = await get_openai_client()
    request = OpenAIChatRequest(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt,
        stream=stream,
    )
    return await run_with_openai_retries(
        lambda: _request_chat_completion(
            client=client,
            request=request,
        )
    )


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
    client = await get_openai_client()
    request = OpenAIChatRequest(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        stream=stream,
    )
    return await run_with_openai_retries(
        lambda: _request_chat_completion(
            client=client,
            request=request,
        )
    )


async def _request_chat_completion(
    *,
    client: AsyncOpenAI,
    request: OpenAIChatRequest,
) -> str:
    response = await client.chat.completions.create(
        **build_chat_completion_kwargs(request)
    )
    if request.stream:
        return await collect_stream_text(response)
    return extract_response_text(response)
