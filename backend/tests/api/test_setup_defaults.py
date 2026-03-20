from api.setup_defaults import read_setup_email_defaults_from_env
from api.setup_defaults import resolve_setup_optional_defaults
from schemas.bootstrap import SetupInitializeRequest


def test_read_setup_email_defaults_from_env_excludes_password(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.env.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-pass")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("SMTP_USE_TLS", "false")

    defaults = read_setup_email_defaults_from_env()

    assert defaults is not None
    assert defaults.smtp_host == "smtp.env.example.com"
    assert defaults.smtp_port == 587
    assert defaults.smtp_username == "smtp-user"
    assert str(defaults.smtp_from_email) == "noreply@example.com"
    assert defaults.smtp_use_tls is False
    assert not hasattr(defaults, "smtp_password")


def test_resolve_setup_optional_defaults_prefers_payload_over_env(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.env.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-env-pass")

    payload = SetupInitializeRequest(
        setup_token="token",
        site_name="ACE",
        default_locale="en",
        supported_locales=["en"],
        admin_email="admin@example.com",
        admin_password="SetupAdminPass123!",
        smtp_host="smtp.payload.example.com",
        smtp_port=2525,
        smtp_use_tls=False,
    )

    resolved = resolve_setup_optional_defaults(payload)

    assert resolved["smtp_host"] == "smtp.payload.example.com"
    assert resolved["smtp_port"] == 2525
    assert resolved["smtp_password"] == "smtp-env-pass"
    assert resolved["smtp_use_tls"] is False
