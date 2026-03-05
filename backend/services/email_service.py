from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Optional


@dataclass
class SmtpConfig:
    host: str
    port: int
    from_email: str
    use_tls: bool = True
    username: Optional[str] = None
    password: Optional[str] = None


def _open_smtp_connection(config: SmtpConfig) -> smtplib.SMTP:
    # Port 465 is implicit TLS (SMTPS). Using plain SMTP here can hang/time out.
    if config.port == 465:
        return smtplib.SMTP_SSL(config.host, config.port, timeout=10)
    return smtplib.SMTP(config.host, config.port, timeout=10)


def _authenticate_smtp_connection(smtp: smtplib.SMTP, config: SmtpConfig) -> None:
    smtp.ehlo()
    if config.use_tls and config.port != 465:
        smtp.starttls()
        smtp.ehlo()
    if config.username:
        smtp.login(config.username, config.password or "")


def is_smtp_configured(
    *,
    host: str | None,
    port: int | None,
    from_email: str | None,
) -> bool:
    return bool(host and str(host).strip() and port and from_email and str(from_email).strip())


def test_smtp_connection(config: SmtpConfig) -> None:
    with _open_smtp_connection(config) as smtp:
        _authenticate_smtp_connection(smtp, config)


# Prevent pytest from collecting this runtime function as a test.
test_smtp_connection.__test__ = False


def send_email(
    *,
    config: SmtpConfig,
    to_email: str,
    subject: str,
    body_text: str,
) -> None:
    message = EmailMessage()
    message["From"] = config.from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body_text)

    with _open_smtp_connection(config) as smtp:
        _authenticate_smtp_connection(smtp, config)
        smtp.send_message(message)
