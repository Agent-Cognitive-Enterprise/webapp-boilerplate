import re
from dataclasses import dataclass

from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from settings import (
    COOKIE_ACCESS_NAME,
    COOKIE_REFRESH_NAME,
    COOKIE_SESSION_BINDING_NAME,
)
from tests.helper import create_test_user


TEST_PASSWORD = "$ecurepAssw0rd"
TRUSTED_ORIGIN = "http://localhost:5173"
TRUSTED_ORIGIN_HEADERS = {"Origin": TRUSTED_ORIGIN}
UNTRUSTED_ORIGIN = "http://evil.example"


@dataclass(frozen=True)
class LoggedInUserSession:
    user: User
    refresh_token: str


def assert_auth_cookie_delete_headers(response: Response) -> None:
    set_cookie_headers = response.headers.get_list("set-cookie")

    assert any(
        COOKIE_ACCESS_NAME in header and "Max-Age=0" in header
        for header in set_cookie_headers
    )
    assert any(
        COOKIE_REFRESH_NAME in header and "Max-Age=0" in header
        for header in set_cookie_headers
    )
    assert any(
        COOKIE_SESSION_BINDING_NAME in header and "Max-Age=0" in header
        for header in set_cookie_headers
    )


def extract_cookie_value(response: Response, cookie_name: str) -> str:
    pattern = re.compile(rf"{re.escape(cookie_name)}=([^;]+);")
    for set_cookie_header in response.headers.get_list("set-cookie"):
        match = pattern.search(set_cookie_header)
        if match is not None:
            return match.group(1)

    raise AssertionError(f"Cookie {cookie_name} not found in response headers")


async def login_cookie_session(
    client: AsyncClient,
    email: str,
    password: str,
) -> None:
    response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200


async def create_logged_in_user_session(
    client: AsyncClient,
    session: AsyncSession,
    *,
    email: str | None = None,
    password: str = TEST_PASSWORD,
) -> LoggedInUserSession:
    user = await create_test_user(
        session=session,
        email=email,
        password=password,
    )
    response = await client.post(
        "/auth/token",
        data={"username": user.email, "password": password},
    )

    assert response.status_code == 200
    return LoggedInUserSession(
        user=user,
        refresh_token=extract_cookie_value(response, COOKIE_REFRESH_NAME),
    )
