from __future__ import annotations

import logging
import os
import subprocess
import sys
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path

from utils.db_config import SQLITE_SYNC_PREFIX, resolve_database_config


logger = logging.getLogger(__name__)

AUTO_MIGRATE_AUTO = "auto"
AUTO_MIGRATE_TRUE = "true"
AUTO_MIGRATE_FALSE = "false"
DEFAULT_APP_ENV = "development"
DEFAULT_DB_TYPE = "sqlite"
DEFAULT_SQLITE_DB_PATH = "app.db"
DEVELOPMENT_ENVS = {"development", "dev"}
BACKEND_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class StartupMigrationPlan:
    should_run: bool
    reason: str
    env_updates: dict[str, str]


def build_startup_migration_plan(
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> StartupMigrationPlan:
    source_env = os.environ if env is None else env
    working_dir = Path.cwd() if cwd is None else Path(cwd)

    database_url = _read_env_value(source_env, "DATABASE_URL")
    db_type = _read_env_value(source_env, "DB_TYPE") or DEFAULT_DB_TYPE
    sqlite_db_path = (
        _read_env_value(source_env, "SQLITE_DB_PATH") or DEFAULT_SQLITE_DB_PATH
    )
    app_env = (_read_env_value(source_env, "APP_ENV") or DEFAULT_APP_ENV).lower()
    auto_migrate = normalize_auto_migrate_on_start(
        _read_env_value(source_env, "AUTO_MIGRATE_ON_START")
    )

    db_config = resolve_database_config(
        database_url=database_url,
        db_type=db_type,
        sqlite_db_path=sqlite_db_path,
    )
    env_updates = _build_sqlite_env_updates(
        database_url=database_url,
        sync_url=db_config.sync_url,
        cwd=working_dir,
    )
    sqlite_file = _resolve_sqlite_file_path(db_config.sync_url, cwd=working_dir)

    if auto_migrate == AUTO_MIGRATE_TRUE:
        return StartupMigrationPlan(
            should_run=True,
            reason="AUTO_MIGRATE_ON_START=true forces startup migrations.",
            env_updates=env_updates,
        )

    if auto_migrate == AUTO_MIGRATE_FALSE:
        return StartupMigrationPlan(
            should_run=False,
            reason="AUTO_MIGRATE_ON_START=false disables startup migrations.",
            env_updates=env_updates,
        )

    if app_env in DEVELOPMENT_ENVS:
        return StartupMigrationPlan(
            should_run=True,
            reason=f"APP_ENV={app_env} enables startup migrations for direct runs.",
            env_updates=env_updates,
        )

    if sqlite_file is not None and not sqlite_file.exists():
        return StartupMigrationPlan(
            should_run=True,
            reason=(
                "SQLite database file is missing, so direct startup will migrate "
                f"{sqlite_file} before serving traffic."
            ),
            env_updates=env_updates,
        )

    return StartupMigrationPlan(
        should_run=False,
        reason=(
            f"APP_ENV={app_env} skips startup migrations for direct runs by default."
        ),
        env_updates=env_updates,
    )


def normalize_auto_migrate_on_start(value: str | None) -> str:
    normalized = (value or AUTO_MIGRATE_AUTO).strip().lower()
    if normalized in {
        AUTO_MIGRATE_AUTO,
        AUTO_MIGRATE_TRUE,
        AUTO_MIGRATE_FALSE,
    }:
        return normalized
    return AUTO_MIGRATE_AUTO


def run_startup_migration_preflight(
    *,
    env: MutableMapping[str, str] | None = None,
    cwd: Path | None = None,
    backend_dir: Path | None = None,
) -> StartupMigrationPlan:
    runtime_env = os.environ if env is None else env
    plan = build_startup_migration_plan(env=runtime_env, cwd=cwd)
    _apply_env_updates(runtime_env, plan.env_updates)

    if not plan.should_run:
        logger.info("Startup migration preflight skipped: %s", plan.reason)
        return plan

    command = [sys.executable, "-m", "alembic", "upgrade", "head"]
    logger.info("Startup migration preflight running: %s", plan.reason)
    subprocess.run(
        command,
        cwd=str(backend_dir or BACKEND_DIR),
        env=dict(runtime_env),
        check=True,
    )
    logger.info("Startup migration preflight completed.")
    return plan


def _apply_env_updates(env: MutableMapping[str, str], updates: Mapping[str, str]) -> None:
    for key, value in updates.items():
        env[key] = value


def _build_sqlite_env_updates(
    *,
    database_url: str | None,
    sync_url: str,
    cwd: Path,
) -> dict[str, str]:
    sqlite_file = _resolve_sqlite_file_path(sync_url, cwd=cwd)
    if sqlite_file is None:
        return {}

    if database_url:
        return {"DATABASE_URL": f"{SQLITE_SYNC_PREFIX}{sqlite_file}"}

    return {"SQLITE_DB_PATH": str(sqlite_file)}


def _resolve_sqlite_file_path(sync_url: str, *, cwd: Path) -> Path | None:
    if not sync_url.startswith(SQLITE_SYNC_PREFIX):
        return None

    path_fragment = sync_url[len(SQLITE_SYNC_PREFIX) :]
    if not path_fragment or path_fragment == ":memory:" or path_fragment.startswith("file:"):
        return None

    sqlite_file = Path(path_fragment).expanduser()
    if sqlite_file.is_absolute():
        return sqlite_file.resolve(strict=False)

    return (cwd / sqlite_file).resolve(strict=False)


def _read_env_value(env: Mapping[str, str], key: str) -> str | None:
    value = env.get(key)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
