#!/usr/bin/env python3
from __future__ import annotations

import os
import ssl
import smtplib
import socket
from email.message import EmailMessage
from dotenv import load_dotenv


def as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y", "t"}


def main() -> int:
    load_dotenv()

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "0"))
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    to_email = os.getenv("SMTP_TO_EMAIL", from_email).strip()

    # true for STARTTLS on port 587
    use_tls = as_bool(os.getenv("SMTP_USE_TLS"), False)

    # true for implicit TLS on port 465
    use_ssl = as_bool(os.getenv("SMTP_USE_SSL"), False)

    timeout = int(os.getenv("SMTP_TIMEOUT", "20"))
    debug = as_bool(os.getenv("SMTP_DEBUG"), True)

    print("Config:")
    print(f"  host={host}")
    print(f"  port={port}")
    print(f"  username={'<set>' if username else '<empty>'}")
    print(f"  from={from_email}")
    print(f"  to={to_email}")
    print(f"  use_tls(STARTTLS)={use_tls}")
    print(f"  use_ssl(implicit TLS)={use_ssl}")
    print(f"  timeout={timeout}")
    print()


    print("Password diagnostics:")
    print("  length:", len(password))
    print("  contains '^':", "^" in password)
    print("  contains '>':", ">" in password)
    print("  contains '}':", "}" in password)
    print("  starts/ends with whitespace:", password != password.strip())

    if not host or not port or not from_email:
        print("Missing required env vars.")
        return 2

    # Step 1: raw TCP connectivity
    print("1) Testing raw TCP connectivity...")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            print("   OK: TCP connection established")
    except Exception as e:
        print(f"   FAIL: TCP connection failed: {type(e).__name__}: {e}")
        return 1

    context = ssl.create_default_context()

    try:
        # Step 2: open SMTP connection
        print("2) Opening SMTP connection...")
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
        else:
            server = smtplib.SMTP(host, port, timeout=timeout)

        with server:
            if debug:
                server.set_debuglevel(1)

            print("3) Waiting for SMTP greeting / EHLO...")
            code, msg = server.ehlo()
            print(f"   EHLO response: {code} {msg.decode(errors='ignore') if isinstance(msg, bytes) else msg}")

            if use_tls:
                print("4) Starting STARTTLS...")
                code, msg = server.starttls(context=context)
                print(f"   STARTTLS response: {code} {msg.decode(errors='ignore') if isinstance(msg, bytes) else msg}")

                code, msg = server.ehlo()
                print(f"   EHLO after STARTTLS: {code} {msg.decode(errors='ignore') if isinstance(msg, bytes) else msg}")

            if username:
                print("5) Logging in...")
                server.login(username, password)
                print("   OK: authenticated")

            print("6) Sending test email...")
            msg = EmailMessage()
            msg["Subject"] = "SMTP test"
            msg["From"] = from_email
            msg["To"] = to_email
            msg.set_content("SMTP test email sent successfully.")

            server.send_message(msg)
            print("   OK: email sent")
            return 0

    except socket.timeout as e:
        print(f"FAIL: timeout: {e}")
        return 1
    except smtplib.SMTPAuthenticationError as e:
        print(f"FAIL: authentication error: {e}")
        return 1
    except smtplib.SMTPConnectError as e:
        print(f"FAIL: connect error: {e}")
        return 1
    except smtplib.SMTPServerDisconnected as e:
        print(f"FAIL: server disconnected: {e}")
        return 1
    except smtplib.SMTPException as e:
        print(f"FAIL: SMTP error: {e}")
        return 1
    except Exception as e:
        print(f"FAIL: unexpected error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())