from __future__ import annotations

from dataclasses import dataclass


SQLITE_SYNC_PREFIX = "sqlite:///"
SQLITE_ASYNC_PREFIX = "sqlite+aiosqlite:///"
POSTGRES_SYNC_PREFIXES = (
    "postgresql://",
    "postgres://",
    "postgresql+psycopg://",
    "postgresql+psycopg2://",
)
POSTGRES_ASYNC_PREFIX = "postgresql+asyncpg://"
SUPPORTED_DB_TYPES = {"sqlite", "postgres", "postgresql"}


@dataclass(frozen=True)
class DatabaseConfig:
    async_url: str
    sync_url: str
    dialect: str


def resolve_database_config(
    *,
    database_url: str | None,
    db_type: str | None,
    sqlite_db_path: str,
) -> DatabaseConfig:
    normalized_database_url = (database_url or "").strip()
    if normalized_database_url:
        return _config_from_database_url(normalized_database_url)

    normalized_db_type = (db_type or "sqlite").strip().lower()
    if normalized_db_type == "sqlite":
        return DatabaseConfig(
            async_url=f"{SQLITE_ASYNC_PREFIX}{sqlite_db_path}",
            sync_url=f"{SQLITE_SYNC_PREFIX}{sqlite_db_path}",
            dialect="sqlite",
        )

    if normalized_db_type in {"postgres", "postgresql"}:
        raise RuntimeError("DATABASE_URL must be set when DB_TYPE is 'postgresql'.")

    raise RuntimeError(
        f"Unsupported DB_TYPE: {db_type}. Supported values are sqlite and postgresql."
    )


def _config_from_database_url(database_url: str) -> DatabaseConfig:
    if database_url.startswith((SQLITE_ASYNC_PREFIX, SQLITE_SYNC_PREFIX)):
        return DatabaseConfig(
            async_url=_to_sqlite_async_url(database_url),
            sync_url=_to_sqlite_sync_url(database_url),
            dialect="sqlite",
        )

    if database_url.startswith(POSTGRES_SYNC_PREFIXES) or database_url.startswith(
        POSTGRES_ASYNC_PREFIX
    ):
        return DatabaseConfig(
            async_url=_to_postgres_async_url(database_url),
            sync_url=_to_postgres_sync_url(database_url),
            dialect="postgresql",
        )

    raise RuntimeError(
        "Unsupported DATABASE_URL. Use a SQLite or PostgreSQL SQLAlchemy URL."
    )


def _to_sqlite_async_url(database_url: str) -> str:
    if database_url.startswith(SQLITE_ASYNC_PREFIX):
        return database_url
    if database_url.startswith(SQLITE_SYNC_PREFIX):
        return database_url.replace(SQLITE_SYNC_PREFIX, SQLITE_ASYNC_PREFIX, 1)
    raise RuntimeError(f"Unsupported SQLite DATABASE_URL: {database_url}")


def _to_sqlite_sync_url(database_url: str) -> str:
    if database_url.startswith(SQLITE_SYNC_PREFIX):
        return database_url
    if database_url.startswith(SQLITE_ASYNC_PREFIX):
        return database_url.replace(SQLITE_ASYNC_PREFIX, SQLITE_SYNC_PREFIX, 1)
    raise RuntimeError(f"Unsupported SQLite DATABASE_URL: {database_url}")


def _to_postgres_async_url(database_url: str) -> str:
    if database_url.startswith(POSTGRES_ASYNC_PREFIX):
        return database_url

    normalized = _to_postgres_sync_url(database_url)
    return normalized.replace("postgresql://", POSTGRES_ASYNC_PREFIX, 1)


def _to_postgres_sync_url(database_url: str) -> str:
    if database_url.startswith(POSTGRES_ASYNC_PREFIX):
        return database_url.replace(POSTGRES_ASYNC_PREFIX, "postgresql://", 1)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if database_url.startswith("postgresql+psycopg2://"):
        return database_url.replace("postgresql+psycopg2://", "postgresql://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        return database_url
    raise RuntimeError(f"Unsupported PostgreSQL DATABASE_URL: {database_url}")
