from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI

from api.lifespan import lifespan


@pytest.mark.asyncio
async def test_lifespan_starts_without_schema_bootstrap(monkeypatch: pytest.MonkeyPatch):
    app = FastAPI()
    state = {"entered": False}

    class _FailingEngine:
        @asynccontextmanager
        async def begin(self):
            raise AssertionError("runtime schema bootstrap should not run during startup")
            yield

    monkeypatch.setattr("utils.db.async_engine", _FailingEngine())

    async with lifespan(app):
        state["entered"] = True

    assert state["entered"] is True
