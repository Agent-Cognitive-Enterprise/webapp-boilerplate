from pathlib import Path

from services.startup_migrations import build_startup_migration_plan


def _build_env(
    *,
    app_env: str,
    sqlite_db_path: str,
    auto_migrate_on_start: str | None = None,
) -> dict[str, str]:
    env = {
        "APP_ENV": app_env,
        "DATABASE_URL": "",
        "DB_TYPE": "sqlite",
        "SQLITE_DB_PATH": sqlite_db_path,
    }
    if auto_migrate_on_start is not None:
        env["AUTO_MIGRATE_ON_START"] = auto_migrate_on_start
    return env


def test_dev_with_existing_sqlite_file_runs_startup_migration(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "existing.db"
    sqlite_db.touch()

    plan = build_startup_migration_plan(
        env=_build_env(app_env="development", sqlite_db_path=sqlite_db.name),
        cwd=tmp_path,
    )

    assert plan.should_run is True
    assert plan.env_updates == {"SQLITE_DB_PATH": str(sqlite_db.resolve())}


def test_prod_with_existing_sqlite_file_skips_startup_migration(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "existing.db"
    sqlite_db.touch()

    plan = build_startup_migration_plan(
        env=_build_env(app_env="production", sqlite_db_path=sqlite_db.name),
        cwd=tmp_path,
    )

    assert plan.should_run is False
    assert plan.env_updates == {"SQLITE_DB_PATH": str(sqlite_db.resolve())}


def test_prod_with_missing_sqlite_file_runs_startup_migration(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "missing.db"

    plan = build_startup_migration_plan(
        env=_build_env(app_env="production", sqlite_db_path=sqlite_db.name),
        cwd=tmp_path,
    )

    assert plan.should_run is True
    assert plan.env_updates == {"SQLITE_DB_PATH": str(sqlite_db.resolve())}


def test_auto_migrate_false_skips_startup_migration(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "missing.db"

    plan = build_startup_migration_plan(
        env=_build_env(
            app_env="development",
            sqlite_db_path=sqlite_db.name,
            auto_migrate_on_start="false",
        ),
        cwd=tmp_path,
    )

    assert plan.should_run is False


def test_auto_migrate_true_runs_startup_migration(tmp_path: Path) -> None:
    sqlite_db = tmp_path / "existing.db"
    sqlite_db.touch()

    plan = build_startup_migration_plan(
        env=_build_env(
            app_env="production",
            sqlite_db_path=sqlite_db.name,
            auto_migrate_on_start="true",
        ),
        cwd=tmp_path,
    )

    assert plan.should_run is True
