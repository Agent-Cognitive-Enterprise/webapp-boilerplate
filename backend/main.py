# /backend/main.py

import uvicorn
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from utils.logger import setup_logging
from api.lifespan import lifespan
from api.health import router as health_router
from api.auth import router as auth_router
from api.users import router as users_router
from api.user_settings import router as user_settings_router
from api.ui_label import router as ui_label_router
from api.setup import router as setup_router
from api.admin_settings import router as admin_settings_router
from auth.auth_handler import (
    get_current_admin_user_from_request,
    get_current_user_from_request,
)
from security.csp import resolve_csp_header
from security.csrf import csrf_protect_cookie_auth
from services.bootstrap import is_initialized
from settings import CORS_ALLOW_ORIGINS
from utils.db import get_session


logger = logging.getLogger(__name__)
HSTS_HEADER_VALUE = "max-age=31536000; includeSubDomains"
PROTECTED_USER_PATHS = {
    "/user-settings",
    "/users/me/",
}
PROTECTED_ADMIN_PATHS = {
    "/admin/settings",
    "/admin/settings/email/check",
    "/users",
}
T = TypeVar("T")

setup_logging()
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("passlib").setLevel(logging.ERROR)

app = FastAPI(
    lifespan=lifespan,
    # Disable docs, redoc, and openapi for production
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    errors = exc.errors()
    logger.warning(
        "Validation error for %s (%s): %s",
        request.url.path,
        request.method,
        errors,
    )
    status_code = (
        400 if any(error.get("type") == "json_invalid" for error in errors) else 422
    )
    return JSONResponse(
        status_code=status_code,
        content={"detail": errors},
    )


ALLOWED_DURING_SETUP = {
    "/health",
    "/setup",
    "/setup/status",
    "/setup/email/check",
}


async def _get_setup_guard_initialized_state() -> bool:
    return await _run_with_session_dependency(
        lambda session: is_initialized(session=session),
    )


async def _run_with_session_dependency(
    operation: Callable[[AsyncSession], Awaitable[T]],
) -> T:
    dependency = app.dependency_overrides.get(get_session, get_session)
    dependency_result = dependency()

    if hasattr(dependency_result, "__anext__"):
        session = await anext(dependency_result)
        try:
            return await operation(session)
        finally:
            await dependency_result.aclose()

    session = await dependency_result
    return await operation(session)


def _resolve_protected_access_level(path: str) -> str | None:
    if path in PROTECTED_USER_PATHS:
        return "user"
    if path in PROTECTED_ADMIN_PATHS:
        return "admin"
    if path.startswith("/users/") and path != "/users/me/":
        return "admin"
    return None


def _http_exception_to_json_response(exc: HTTPException) -> JSONResponse:
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def _authorize_protected_route(request: Request) -> JSONResponse | None:
    access_level = _resolve_protected_access_level(request.url.path)
    if access_level is None:
        return None

    async def _authorize(session) -> None:
        if access_level == "admin":
            await get_current_admin_user_from_request(
                request=request,
                session=session,
            )
            return
        await get_current_user_from_request(
            request=request,
            session=session,
        )

    try:
        await _run_with_session_dependency(_authorize)
    except HTTPException as exc:
        return _http_exception_to_json_response(exc)

    return None


def _request_is_https(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        first_hop_proto = forwarded_proto.split(",", 1)[0].strip().lower()
        return first_hop_proto == "https"
    return request.url.scheme == "https"


@app.middleware("http")
async def setup_mode_guard(request: Request, call_next):
    path = request.url.path

    if request.method == "OPTIONS":
        return await call_next(request)

    if path in ALLOWED_DURING_SETUP:
        return await call_next(request)

    initialized = await _get_setup_guard_initialized_state()

    if not initialized:
        accept = request.headers.get("accept", "")
        if request.method in {"GET", "HEAD"} and "text/html" in accept:
            return RedirectResponse(url="/setup", status_code=307)
        return JSONResponse(
            status_code=423,
            content={
                "detail": "Application initialization is required. Complete setup at /setup."
            },
        )

    auth_guard_response = await _authorize_protected_route(request)
    if auth_guard_response is not None:
        return auth_guard_response

    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    if _request_is_https(request):
        response.headers["Strict-Transport-Security"] = HSTS_HEADER_VALUE
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = resolve_csp_header(request, response)

    return response


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    return await csrf_protect_cookie_auth(request, call_next)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    expose_headers=["Content-Type"],
    max_age=3600,
)

app.include_router(health_router)
app.include_router(setup_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(user_settings_router)
app.include_router(ui_label_router)
app.include_router(admin_settings_router)


def run() -> None:
    from services.startup_migrations import run_startup_migration_preflight

    run_startup_migration_preflight()
    logger.info("Starting server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=None,
        log_level="debug",
    )


if __name__ == "__main__":
    run()
