from __future__ import annotations

import hashlib
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from html import escape
from time import time

from fastapi import HTTPException, Request, status

from i18n.messages import msg
from settings import (
    AUTH_BACKEND_BASE_URL,
    AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS,
    AUTH_FRONTEND_BASE_URL,
    AUTH_RATE_LIMIT_ENABLED,
)

_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "register": (5, 3600),
    "token": (10, 900),
    "refresh": (30, 3600),
    "forgot_password": (10, 3600),
    "reset_password": (10, 3600),
}
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def hash_plain_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode()).hexdigest()


def generate_email_verification_token() -> tuple[str, str]:
    plain_token = secrets.token_urlsafe(48)
    return plain_token, hash_plain_token(plain_token)


def email_verification_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS)


def normalize_base_url(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    stripped = value.strip().rstrip("/")
    return stripped or fallback


def resolve_auth_frontend_base_url(settings) -> str:
    return normalize_base_url(
        getattr(settings, "auth_frontend_base_url", None) if settings else None,
        AUTH_FRONTEND_BASE_URL,
    )


def resolve_auth_backend_base_url(settings) -> str:
    return normalize_base_url(
        getattr(settings, "auth_backend_base_url", None) if settings else None,
        AUTH_BACKEND_BASE_URL,
    )


def check_rate_limit(action: str, ip: str | None, request: Request | None = None) -> None:
    if not AUTH_RATE_LIMIT_ENABLED:
        return
    limit, window_seconds = _RATE_LIMITS[action]
    key = f"{action}:{ip or 'unknown'}"
    now = time()
    bucket = _RATE_BUCKETS[key]
    cutoff = now - window_seconds

    while bucket and bucket[0] < cutoff:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg(
                request=request,
                key="auth.too_many_requests",
                default="Too many requests. Please try again later.",
            ),
        )

    bucket.append(now)


def request_accepts_html(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "text/html" in accept


def verification_feedback_html(message: str, login_url: str) -> str:
    safe_message = escape(message)
    safe_login_url = escape(login_url, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="10;url={safe_login_url}" />
  <title>Email Verification</title>
  <style>
    :root {{
      color-scheme: light;
      --bg-top: #eef2ff;
      --bg-bottom: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --subtle: #475569;
      --border: #dbe3f3;
      --shadow: 0 12px 32px rgba(15, 23, 42, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: linear-gradient(160deg, var(--bg-top), var(--bg-bottom));
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--text);
      padding: 1rem;
    }}
    .card {{
      width: min(640px, 100%);
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 2rem 1.5rem;
      text-align: center;
    }}
    h1 {{
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
    }}
    p.message {{
      margin: 1rem 0 0;
      font-size: 1.05rem;
      color: var(--subtle);
    }}
    p.redirect {{
      margin: 1.25rem 0 0;
      font-size: 0.95rem;
      color: var(--subtle);
    }}
    a {{
      color: #1d4ed8;
      text-decoration: none;
      font-weight: 600;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <main class="card">
    <h1>Email Verification</h1>
    <p class="message">{safe_message}</p>
    <p class="redirect">Redirecting to login in <span id="countdown">10</span> seconds. <a href="{safe_login_url}">Go now</a>.</p>
  </main>
  <script>
    let remaining = 10;
    const countdown = document.getElementById("countdown");
    const loginUrl = {safe_login_url!r};
    const timer = setInterval(() => {{
      remaining -= 1;
      if (countdown) countdown.textContent = String(Math.max(remaining, 0));
      if (remaining <= 0) {{
        clearInterval(timer);
        window.location.replace(loginUrl);
      }}
    }}, 1000);
  </script>
</body>
</html>"""
