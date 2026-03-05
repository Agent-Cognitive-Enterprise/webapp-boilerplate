# /backend/main.py

import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from utils.logger import setup_logging
from api.lifespan import lifespan
from api.health import router as health_router
from api.auth import router as auth_router
from api.users import router as users_router
from api.user_settings import router as user_settings_router
from api.ui_label import router as ui_label_router
from api.setup import router as setup_router
from api.admin_settings import router as admin_settings_router
from services.bootstrap import is_initialized
from settings import CORS_ALLOW_ORIGINS
from utils.db import get_session


logger = logging.getLogger(__name__)

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
    logger.warning(
        "Validation error for %s (%s): %s",
        request.url.path,
        request.method,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


ALLOWED_DURING_SETUP = {
    "/health",
    "/setup",
    "/setup/status",
    "/setup/email/check",
}


async def _get_setup_guard_initialized_state() -> bool:
    dependency = app.dependency_overrides.get(get_session, get_session)
    dependency_result = dependency()

    if hasattr(dependency_result, "__anext__"):
        session = await anext(dependency_result)
        try:
            return await is_initialized(session=session)
        finally:
            await dependency_result.aclose()

    session = await dependency_result
    return await is_initialized(session=session)


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

    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


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


if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=None,
        log_level="debug",
    )
