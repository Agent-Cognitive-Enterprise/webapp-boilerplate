# /backend/ai/deepseek_api_client.py
import asyncio
from typing import Optional
from openai import AsyncOpenAI
import logging

from services.system_settings import get_provider_api_key_from_db
from utils.profiling import measure_time


logging.basicConfig(level=logging.INFO)

BASE_URL = "https://api.deepseek.com"


# Reuse a single async client
_aclient: Optional[AsyncOpenAI] = None
_client_api_key: Optional[str] = None


@measure_time
async def get_deepseek_client(base_url: str = None) -> AsyncOpenAI:
    """
    Initialises and returns an OpenAI API client using the provided API key.
    """

    global _aclient, _client_api_key
    resolved_key = await get_provider_api_key_from_db("deepseek")
    if not resolved_key:
        raise RuntimeError("DeepSeek API key is not configured")

    if _aclient is None or _client_api_key != resolved_key:
        _aclient = AsyncOpenAI(
            api_key=resolved_key,
            timeout=10,
            base_url=base_url,
        )
        _client_api_key = resolved_key

    return _aclient


# noinspection PyTypeChecker
@measure_time
async def get_openai_response(
    prompt: str,
    stream: bool = False,
    model: str = "deepseek-chat",
    max_tokens: int = 100,
    temperature: float = 0.0,
    return_reasoning: bool = False,
    system_prompt: str = "You are a helpful assistant.",
) -> str:
    """
    Sends a prompt to the DeepSeek API and returns the generated response.

    If stream=True, deltas are yielded from the server as they arrive.
    The function aggregates them into a final string return value.
    Pass `on_delta` to receive each text chunk as it's produced.
    """
    client = await get_deepseek_client(base_url=BASE_URL)

    content_parts: list[str] = []
    reasoning_parts: list[str] = []

    if stream:
        try:
            stream_resp = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            async for chunk in stream_resp:
                delta = getattr(chunk.choices[0], "delta", None)
                if not delta:
                    continue

                r_text = getattr(delta, "reasoning_content", None)
                if r_text and return_reasoning:
                    reasoning_parts.append(r_text)

                text = getattr(delta, "content", None)
                if text:
                    content_parts.append(text)

        except Exception as exc:
            raise exc

        if return_reasoning:
            return "".join(content_parts), "".join(reasoning_parts)
        else:
            return "".join(content_parts)

    # Non-streaming
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if return_reasoning:
        msg = response.choices[0].message
        reasoning = getattr(msg, "reasoning_content", "")
        content = getattr(msg, "content", "") or ""
        return content, reasoning
    else:
        return response.choices[0].message.content or ""


async def main() -> None:
    test_prompt = "What is the capital of France?"

    answer = await get_openai_response(
        test_prompt,
        stream=True,
        model="deepseek-chat",
        # model="deepseek-reasoner",
        max_tokens=128,
        temperature=0.0,
    )
    print("me:", test_prompt)
    print(f"AI: {answer}")


if __name__ == "__main__":
    asyncio.run(main())
