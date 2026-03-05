import smtplib

import pytest

from services.email_service import SmtpConfig, send_email, test_smtp_connection


class _FakeSMTP:
    def __init__(self):
        self.calls: list[str] = []

    def __enter__(self):
        self.calls.append("enter")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.calls.append("exit")
        return False

    def ehlo(self):
        self.calls.append("ehlo")

    def starttls(self):
        self.calls.append("starttls")

    def login(self, username: str, password: str):
        self.calls.append(f"login:{username}:{password}")

    def send_message(self, _message):
        self.calls.append("send_message")


def test_test_smtp_connection_uses_implicit_tls_for_port_465(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    smtp = _FakeSMTP()
    used = {"smtp_ssl": False, "smtp": False}

    def _smtp_ssl(host: str, port: int, timeout: int):
        used["smtp_ssl"] = True
        assert host == "smtp.example.com"
        assert port == 465
        assert timeout == 10
        return smtp

    def _smtp_plain(*_args, **_kwargs):
        used["smtp"] = True
        raise AssertionError("Plain SMTP should not be used for port 465")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _smtp_ssl)
    monkeypatch.setattr(smtplib, "SMTP", _smtp_plain)

    test_smtp_connection(
        SmtpConfig(
            host="smtp.example.com",
            port=465,
            from_email="noreply@example.com",
            use_tls=True,
            username="smtp-user",
            password="smtp-pass",
        )
    )

    assert used["smtp_ssl"] is True
    assert used["smtp"] is False
    assert smtp.calls == [
        "enter",
        "ehlo",
        "login:smtp-user:smtp-pass",
        "exit",
    ]


def test_test_smtp_connection_uses_starttls_on_non_465(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    smtp = _FakeSMTP()
    used = {"smtp_ssl": False, "smtp": False}

    def _smtp_plain(host: str, port: int, timeout: int):
        used["smtp"] = True
        assert host == "smtp.example.com"
        assert port == 587
        assert timeout == 10
        return smtp

    def _smtp_ssl(*_args, **_kwargs):
        used["smtp_ssl"] = True
        raise AssertionError("SMTP_SSL should not be used for non-465 ports")

    monkeypatch.setattr(smtplib, "SMTP", _smtp_plain)
    monkeypatch.setattr(smtplib, "SMTP_SSL", _smtp_ssl)

    test_smtp_connection(
        SmtpConfig(
            host="smtp.example.com",
            port=587,
            from_email="noreply@example.com",
            use_tls=True,
            username="smtp-user",
            password="smtp-pass",
        )
    )

    assert used["smtp"] is True
    assert used["smtp_ssl"] is False
    assert smtp.calls == [
        "enter",
        "ehlo",
        "starttls",
        "ehlo",
        "login:smtp-user:smtp-pass",
        "exit",
    ]


def test_send_email_skips_starttls_when_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    smtp = _FakeSMTP()

    def _smtp_plain(_host: str, _port: int, timeout: int):
        assert timeout == 10
        return smtp

    monkeypatch.setattr(smtplib, "SMTP", _smtp_plain)

    send_email(
        config=SmtpConfig(
            host="smtp.example.com",
            port=25,
            from_email="noreply@example.com",
            use_tls=False,
            username="smtp-user",
            password="smtp-pass",
        ),
        to_email="user@example.com",
        subject="Subject",
        body_text="Body",
    )

    assert "starttls" not in smtp.calls
    assert "send_message" in smtp.calls
