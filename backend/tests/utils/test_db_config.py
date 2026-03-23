import pytest

from utils.db_config import DatabaseConfig, resolve_database_config


def test_resolve_database_config_defaults_to_sqlite_path() -> None:
    config = resolve_database_config(
        database_url=None,
        db_type="sqlite",
        sqlite_db_path="app.db",
    )

    assert config == DatabaseConfig(
        async_url="sqlite+aiosqlite:///app.db",
        sync_url="sqlite:///app.db",
        dialect="sqlite",
    )


def test_resolve_database_config_accepts_postgresql_sync_url() -> None:
    config = resolve_database_config(
        database_url="postgresql://user:pass@db.example/app",
        db_type="sqlite",
        sqlite_db_path="ignored.db",
    )

    assert config == DatabaseConfig(
        async_url="postgresql+asyncpg://user:pass@db.example/app",
        sync_url="postgresql://user:pass@db.example/app",
        dialect="postgresql",
    )


def test_resolve_database_config_accepts_postgresql_async_url() -> None:
    config = resolve_database_config(
        database_url="postgresql+asyncpg://user:pass@db.example/app",
        db_type="sqlite",
        sqlite_db_path="ignored.db",
    )

    assert config == DatabaseConfig(
        async_url="postgresql+asyncpg://user:pass@db.example/app",
        sync_url="postgresql://user:pass@db.example/app",
        dialect="postgresql",
    )


def test_resolve_database_config_requires_database_url_for_postgresql_type() -> None:
    with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
        resolve_database_config(
            database_url=None,
            db_type="postgresql",
            sqlite_db_path="ignored.db",
        )


def test_resolve_database_config_rejects_unsupported_url() -> None:
    with pytest.raises(RuntimeError, match="Unsupported DATABASE_URL"):
        resolve_database_config(
            database_url="mysql://user:pass@db.example/app",
            db_type="sqlite",
            sqlite_db_path="ignored.db",
        )
