from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpenAIChatRequest:
    prompt: str
    model: str
    max_tokens: int
    system_prompt: str
    stream: bool = False
    temperature: float | None = None


def build_messages(request: OpenAIChatRequest) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": request.system_prompt,
        },
        {
            "role": "user",
            "content": request.prompt,
        },
    ]


def build_chat_completion_kwargs(request: OpenAIChatRequest) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": request.model,
        "messages": build_messages(request),
        "stream": request.stream,
        "max_tokens": request.max_tokens,
    }
    if request.temperature is not None:
        kwargs["temperature"] = request.temperature
    return kwargs


async def collect_stream_text(stream_response: Any) -> str:
    final_text_parts: list[str] = []
    async for chunk in stream_response:
        try:
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                final_text_parts.append(text)
        except Exception:
            continue
    return "".join(final_text_parts)


def extract_response_text(response: Any) -> str:
    return response.choices[0].message.content or ""
