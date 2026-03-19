from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_ci_test_env.py"
    spec = importlib.util.spec_from_file_location("check_ci_test_env_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_find_forbidden_test_env_entries_accepts_current_shape() -> None:
    mod = _load_module()
    findings = mod._find_forbidden_test_env_entries(
        {
            "jobs": {
                "backend-quality": {
                    "env": {
                        "APP_ENV": "test",
                        "DB_TYPE": "sqlite",
                    }
                },
                "frontend-e2e": {
                    "env": {
                        "APP_ENV": "test",
                        "DB_TYPE": "sqlite",
                    }
                },
            }
        }
    )

    assert findings == []


def test_find_forbidden_test_env_entries_rejects_secret_overrides() -> None:
    mod = _load_module()
    findings = mod._find_forbidden_test_env_entries(
        {
            "jobs": {
                "backend-quality": {
                    "env": {
                        "AUTH_SECRET_KEY": "ci-test-secret-key",
                    }
                },
                "frontend-e2e": {
                    "env": {
                        "INITIAL_SETUP_TOKEN": "ci-test-setup-token",
                    }
                },
            }
        }
    )

    assert findings == [
        "job backend-quality must not define env.AUTH_SECRET_KEY",
        "job frontend-e2e must not define env.INITIAL_SETUP_TOKEN",
    ]


def test_main_returns_zero_for_current_workflow(
    capsys,
) -> None:
    mod = _load_module()

    rc = mod.main([])
    out = capsys.readouterr().out

    assert rc == 0
    assert "CI test env guard passed." in out
