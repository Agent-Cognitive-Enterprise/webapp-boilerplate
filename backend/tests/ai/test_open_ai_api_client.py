import asyncio
from types import SimpleNamespace

import pytest

from ai import open_ai_api_client as client_module
from ai import open_ai_retry


def _response_with_text(text: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=text),
            )
        ]
    )


def _stream_chunk(text=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=text),
            )
        ]
    )


class _AsyncStream:
    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


@pytest.mark.asyncio
async def test_get_openai_client_reuses_cached_client_for_same_key(monkeypatch):
    created_clients = []

    class FakeAsyncOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            created_clients.append(self)

    keys = iter(["key-1", "key-1", "key-2"])

    async def _get_key(_provider: str):
        return next(keys)

    monkeypatch.setattr(client_module, "AsyncOpenAI", FakeAsyncOpenAI)
    monkeypatch.setattr(client_module, "get_provider_api_key_from_db", _get_key)
    monkeypatch.setattr(client_module, "_aclient", None)
    monkeypatch.setattr(client_module, "_client_api_key", None)

    first = await client_module.get_openai_client()
    second = await client_module.get_openai_client()
    third = await client_module.get_openai_client()

    assert first is second
    assert third is not first
    assert [client.kwargs["api_key"] for client in created_clients] == ["key-1", "key-2"]


@pytest.mark.asyncio
async def test_get_openai_response_builds_expected_non_stream_request(monkeypatch):
    captured = {}

    async def _create(**kwargs):
        captured.update(kwargs)
        return _response_with_text("hello")

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=_create),
        )
    )

    async def _get_client():
        return fake_client

    monkeypatch.setattr(client_module, "get_openai_client", _get_client)

    result = await client_module.get_openai_response(
        prompt="Hi",
        stream=False,
        model="gpt-test",
        max_tokens=12,
        temperature=0.4,
        system_prompt="System",
    )

    assert result == "hello"
    assert captured == {
        "model": "gpt-test",
        "messages": [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hi"},
        ],
        "stream": False,
        "max_tokens": 12,
        "temperature": 0.4,
    }


@pytest.mark.asyncio
async def test_get_openai_response_five_one_omits_temperature(monkeypatch):
    captured = {}

    async def _create(**kwargs):
        captured.update(kwargs)
        return _response_with_text("hello")

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=_create),
        )
    )

    async def _get_client():
        return fake_client

    monkeypatch.setattr(client_module, "get_openai_client", _get_client)

    result = await client_module.get_openai_response_five_one(
        prompt="Hi",
        stream=False,
        model="gpt-5.1",
        max_tokens=24,
        temperature=0.9,
        system_prompt="System",
    )

    assert result == "hello"
    assert "temperature" not in captured


@pytest.mark.asyncio
async def test_get_openai_response_stream_ignores_malformed_chunks(monkeypatch):
    async def _create(**_kwargs):
        return _AsyncStream(
            [
                _stream_chunk("hel"),
                SimpleNamespace(),
                _stream_chunk(None),
                _stream_chunk("lo"),
            ]
        )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=_create),
        )
    )

    async def _get_client():
        return fake_client

    monkeypatch.setattr(client_module, "get_openai_client", _get_client)

    result = await client_module.get_openai_response(
        prompt="Hi",
        stream=True,
        model="gpt-test",
        max_tokens=12,
        temperature=0.4,
        system_prompt="System",
    )

    assert result == "hello"


@pytest.mark.asyncio
async def test_run_with_openai_retries_retries_and_sleeps(monkeypatch):
    attempts = {"count": 0}
    delays = []

    async def _sleep(delay):
        delays.append(delay)

    async def _operation():
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise asyncio.TimeoutError("slow")
        return "ok"

    monkeypatch.setattr(open_ai_retry, "OPENAI_TIMEOUT_RETRY_LIMIT", 3)
    monkeypatch.setattr(open_ai_retry, "OPENAI_TIMEOUT_BACKOFF_SECONDS", 2)
    monkeypatch.setattr(open_ai_retry.asyncio, "sleep", _sleep)

    result = await open_ai_retry.run_with_openai_retries(_operation)

    assert result == "ok"
    assert attempts["count"] == 2
    assert delays == [2]


@pytest.mark.asyncio
async def test_run_with_openai_retries_raises_after_final_attempt(monkeypatch):
    attempts = {"count": 0}

    async def _sleep(_delay):
        return None

    async def _operation():
        attempts["count"] += 1
        raise asyncio.TimeoutError("slow")

    monkeypatch.setattr(open_ai_retry, "OPENAI_TIMEOUT_RETRY_LIMIT", 2)
    monkeypatch.setattr(open_ai_retry, "OPENAI_TIMEOUT_BACKOFF_SECONDS", 1)
    monkeypatch.setattr(open_ai_retry.asyncio, "sleep", _sleep)

    with pytest.raises(asyncio.TimeoutError):
        await open_ai_retry.run_with_openai_retries(_operation)

    assert attempts["count"] == 2
