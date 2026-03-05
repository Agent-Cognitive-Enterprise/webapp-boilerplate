#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.email_service import SmtpConfig, test_smtp_connection


SMTP_KEYS = (
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM_EMAIL",
    "SMTP_USE_TLS",
)


def _parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


def _mask(value: str, show_secrets: bool) -> str:
    if show_secrets:
        return value
    if not value:
        return "<empty>"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_smtp_config(values: dict[str, str]) -> SmtpConfig | None:
    host = values.get("SMTP_HOST")
    port_raw = values.get("SMTP_PORT")
    from_email = values.get("SMTP_FROM_EMAIL")

    if not host or not port_raw or not from_email:
        return None

    try:
        port = int(port_raw)
    except ValueError:
        return None

    return SmtpConfig(
        host=host.strip(),
        port=port,
        username=values.get("SMTP_USERNAME", "").strip() or None,
        password=values.get("SMTP_PASSWORD"),
        from_email=from_email.strip(),
        use_tls=_parse_bool(values.get("SMTP_USE_TLS"), default=True),
    )


def _detect_email_library(email_service_path: Path) -> list[str]:
    if not email_service_path.exists():
        return ["backend/services/email_service.py not found"]

    source = email_service_path.read_text(encoding="utf-8")
    findings: list[str] = []
    findings.append("library: smtplib" if "import smtplib" in source else "library: unknown")
    findings.append("uses SMTP: yes" if "smtplib.SMTP(" in source else "uses SMTP: no")
    findings.append("uses SMTP_SSL: yes" if "smtplib.SMTP_SSL(" in source else "uses SMTP_SSL: no")

    if "config.port == 465" in source and "SMTP_SSL" in source:
        findings.append("port 465 behavior: implicit TLS (SMTP_SSL)")
    else:
        findings.append("port 465 behavior: not explicitly detected")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect current SMTP/email library usage and SMTP values from .env.",
    )
    parser.add_argument(
        "--show-secrets",
        action="store_true",
        help="Print raw values (including SMTP_PASSWORD). Default is masked output.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"

    env_paths = [
        backend_dir / ".env",
        repo_root / ".env",
    ]

    print("== Email Library Detection ==")
    for line in _detect_email_library(backend_dir / "services" / "email_service.py"):
        print(f"- {line}")

    print("\n== SMTP .env Values ==")
    attempted_auth_check = False
    auth_check_ok = False
    for env_path in env_paths:
        print(f"\n[{env_path}]")
        env_values = _parse_dotenv(env_path)
        if not env_values:
            print("- no values found")
            continue
        for key in SMTP_KEYS:
            if key not in env_values:
                print(f"- {key}=<missing>")
                continue
            value = env_values[key]
            if key == "SMTP_PASSWORD":
                value = _mask(value, args.show_secrets)
            print(f"- {key}={value}")

        if attempted_auth_check:
            continue

        config = _build_smtp_config(env_values)
        if config is None:
            print("- auth-check: skipped (missing or invalid SMTP_HOST/SMTP_PORT/SMTP_FROM_EMAIL)")
            continue

        attempted_auth_check = True
        try:
            test_smtp_connection(config)
            auth_check_ok = True
            print("- auth-check: success")
        except Exception as exc:  # pragma: no cover - exercised via tests with monkeypatch
            print(f"- auth-check: failed ({exc})")

    if attempted_auth_check and not auth_check_ok:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
