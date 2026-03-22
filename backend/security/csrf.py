from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse

from settings import (
    AUTH_BACKEND_BASE_URL,
    COOKIE_ACCESS_NAME,
    COOKIE_REFRESH_NAME,
    CORS_ALLOW_ORIGINS,
)


UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_ERROR_DETAIL = "CSRF validation failed"


def _normalize_origin(value: str | None) -> str | None:
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return None

    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _resolve_request_origin(request: Request) -> str | None:
    origin = _normalize_origin(request.headers.get("origin"))
    if origin:
        return origin
    return _normalize_origin(request.headers.get("referer"))


def _trusted_origins() -> set[str]:
    origins = {
        normalized
        for normalized in (
            _normalize_origin(origin) for origin in CORS_ALLOW_ORIGINS + [AUTH_BACKEND_BASE_URL]
        )
        if normalized
    }
    return origins


def request_requires_csrf_protection(request: Request) -> bool:
    if request.method.upper() not in UNSAFE_METHODS:
        return False

    if request.headers.get("authorization"):
        return False

    return bool(
        request.cookies.get(COOKIE_ACCESS_NAME)
        or request.cookies.get(COOKIE_REFRESH_NAME)
    )


async def csrf_protect_cookie_auth(request: Request, call_next):
    if not request_requires_csrf_protection(request):
        return await call_next(request)

    request_origin = _resolve_request_origin(request)
    if request_origin in _trusted_origins():
        return await call_next(request)

    return JSONResponse(
        status_code=403,
        content={"detail": CSRF_ERROR_DETAIL},
    )
