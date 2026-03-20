import pytest
from fastapi import Request, Response
from starlette.datastructures import Headers

from api.auth_sessions import logout_handler


class _FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


async def _receive() -> dict:
    return {"type": "http.request", "body": b"", "more_body": False}


def _request_with_cookie(cookie_header: str | None) -> Request:
    headers = Headers({"cookie": cookie_header} if cookie_header else {})
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/logout",
        "headers": headers.raw,
    }
    return Request(scope, _receive)


async def _get_by_token_hash(_session, _token_hash):
    return None


async def _revoke_token_and_descendants(_session, _rt):
    return None


@pytest.mark.asyncio
async def test_logout_handler_is_idempotent_without_cookie() -> None:
    session = _FakeSession()
    response = Response()

    result = await logout_handler(
        session=session,
        request=_request_with_cookie(None),
        response=response,
    )

    assert result.status_code == 204
    assert "Max-Age=0" in result.headers.get("set-cookie", "")
    assert session.committed is False
    assert session.rolled_back is False
