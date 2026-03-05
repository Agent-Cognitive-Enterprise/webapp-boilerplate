# /backend/settings.py

import os
from dotenv import load_dotenv, find_dotenv
import logging


load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

APP_NAME = os.getenv("APP_NAME", "boilerplate")
APP_ENV = os.getenv("APP_ENV", "development").lower()
INITIAL_SETUP_TOKEN = os.getenv("INITIAL_SETUP_TOKEN")

# Database connection parameters
# For production use SQLite, for testing use in-memory SQLite
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "app.db")

# Authentication settings
# to get a string like this run:
# openssl rand -hex 32
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
AUTH_ALGORITHM = os.getenv("AUTH_ALGORITHM", "HS256")
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", 15)  # 15 minutes
)
AUTH_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("AUTH_REFRESH_TOKEN_EXPIRE_DAYS", 14))
AUTH_RATE_LIMIT_ENABLED = os.getenv("AUTH_RATE_LIMIT_ENABLED", "true") == "true"
AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS = int(
    os.getenv("AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS", 24)
)
AUTH_FRONTEND_BASE_URL = os.getenv(
    "AUTH_FRONTEND_BASE_URL",
    "http://localhost:5173",
).rstrip("/")
AUTH_BACKEND_BASE_URL = os.getenv(
    "AUTH_BACKEND_BASE_URL",
    os.getenv("AUTH_EMAIL_VERIFICATION_BASE_URL", "http://localhost:8000"),
).rstrip("/")
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Cookie settings
COOKIE_REFRESH_NAME = os.getenv("COOKIE_REFRESH_NAME", "rt")
COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false") == "true"
)  # True in prod (HTTPS only)
COOKIE_SAME_SITE = os.getenv(
    "COOKIE_SAME_SITE", "lax"
)  # "lax" or "strict"; "none" requires HTTPS
COOKIE_DOMAIN: str | None = os.getenv(
    "COOKIE_DOMAIN", None
)  # e.g. ".yourdomain.com" in prod
COOKIE_PATH = os.getenv("COOKIE_PATH", "/")
COOKIE_HTTPONLY = os.getenv("COOKIE_HTTPONLY", "true") == "true"

if not AUTH_SECRET_KEY:
    raise RuntimeError("AUTH_SECRET_KEY must be set.")

if COOKIE_SAME_SITE.lower() == "none" and not COOKIE_SECURE:
    raise RuntimeError("COOKIE_SAME_SITE=none requires COOKIE_SECURE=true.")

if APP_ENV in {"prod", "production"} and not COOKIE_SECURE:
    raise RuntimeError("COOKIE_SECURE must be true in production.")

# AI
OPENAI_TIMEOUT_RETRY_LIMIT = int(os.getenv("OPENAI_TIMEOUT_RETRY_LIMIT", 3))
OPENAI_TIMEOUT_BACKOFF_SECONDS = float(os.getenv("OPENAI_TIMEOUT_BACKOFF_SECONDS", 0.5))
