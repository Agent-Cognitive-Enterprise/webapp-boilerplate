from __future__ import annotations

from pathlib import Path

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_yaml(relative_path: str) -> dict:
    path = _repo_root() / relative_path
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    assert isinstance(loaded, dict)
    return loaded


def test_sqlite_compose_example_has_persistent_volume_and_backend_env_file() -> None:
    compose = _load_yaml("deploy/docker-compose.sqlite.yml")

    backend = compose["services"]["backend"]

    assert backend["env_file"] == ["./backend.sqlite.env"]
    assert "sqlite_data:/data" in backend["volumes"]
    assert "alembic upgrade head" in backend["command"]
    assert "sqlite_data" in compose["volumes"]


def test_postgres_compose_example_has_backend_and_database_services() -> None:
    compose = _load_yaml("deploy/docker-compose.postgres.yml")

    services = compose["services"]
    postgres = services["postgres"]
    backend = services["backend"]

    assert postgres["env_file"] == ["./postgres.env"]
    assert "postgres_data:/var/lib/postgresql/data" in postgres["volumes"]
    assert backend["env_file"] == ["./backend.postgres.env"]
    assert backend["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert "alembic upgrade head" in backend["command"]


def test_deployment_docs_and_env_examples_exist() -> None:
    repo_root = _repo_root()

    assert (repo_root / "DEPLOYMENT.md").exists()
    assert (repo_root / "deploy" / "backend.sqlite.env.example").exists()
    assert (repo_root / "deploy" / "backend.postgres.env.example").exists()
    assert (repo_root / "deploy" / "postgres.env.example").exists()
