from pathlib import Path


def test_alembic_layout_and_baseline_migration_present() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_dir = backend_dir / "alembic"
    versions_dir = alembic_dir / "versions"
    baseline = versions_dir / "20260304_01_baseline_sqlmodel_schema.py"

    assert (backend_dir / "alembic.ini").exists()
    assert (alembic_dir / "env.py").exists()
    assert (alembic_dir / "script.py.mako").exists()
    assert versions_dir.exists()
    assert baseline.exists()

    content = baseline.read_text(encoding="utf-8")
    for table_name in (
        "users",
        "system_settings",
        "ui_labels",
        "ui_locales",
        "ui_label_suggestions",
        "user_settings",
        "refresh_tokens",
        "password_reset_tokens",
        "email_verification_tokens",
    ):
        assert f'"{table_name}"' in content
