from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_email_config.py"
    spec = importlib.util.spec_from_file_location("check_email_config_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_smtp_config_reads_values() -> None:
    mod = _load_module()
    config = mod._build_smtp_config(
        {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "smtp-user",
            "SMTP_PASSWORD": "smtp-pass",
            "SMTP_FROM_EMAIL": "noreply@example.com",
            "SMTP_USE_TLS": "true",
        }
    )

    assert config is not None
    assert config.host == "smtp.example.com"
    assert config.port == 587
    assert config.username == "smtp-user"
    assert config.password == "smtp-pass"
    assert config.from_email == "noreply@example.com"
    assert config.use_tls is True


def test_build_smtp_config_returns_none_for_invalid_port() -> None:
    mod = _load_module()
    config = mod._build_smtp_config(
        {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "not-a-number",
            "SMTP_FROM_EMAIL": "noreply@example.com",
        }
    )
    assert config is None


def test_main_returns_zero_when_auth_check_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mod = _load_module()
    monkeypatch.setattr(
        mod,
        "_parse_dotenv",
        lambda _path: {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "465",
            "SMTP_USERNAME": "smtp-user",
            "SMTP_PASSWORD": "smtp-pass",
            "SMTP_FROM_EMAIL": "noreply@example.com",
            "SMTP_USE_TLS": "true",
        },
    )
    monkeypatch.setattr(mod, "test_smtp_connection", lambda _config: None)

    rc = mod.main([])
    out = capsys.readouterr().out

    assert rc == 0
    assert "auth-check: success" in out


def test_main_returns_one_when_auth_check_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mod = _load_module()
    monkeypatch.setattr(
        mod,
        "_parse_dotenv",
        lambda _path: {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "smtp-user",
            "SMTP_PASSWORD": "smtp-pass",
            "SMTP_FROM_EMAIL": "noreply@example.com",
            "SMTP_USE_TLS": "true",
        },
    )

    def _fail(_config):
        raise RuntimeError("bad auth")

    monkeypatch.setattr(mod, "test_smtp_connection", _fail)

    rc = mod.main([])
    out = capsys.readouterr().out

    assert rc == 1
    assert "auth-check: failed (bad auth)" in out
