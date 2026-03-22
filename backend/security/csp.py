from fastapi import Request, Response


def build_default_csp() -> str:
    return "; ".join(
        [
            "default-src 'self'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "form-action 'self'",
            "script-src 'self'",
            "style-src 'self'",
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
        ]
    )


def build_verification_feedback_csp() -> str:
    return "; ".join(
        [
            "default-src 'self'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "object-src 'none'",
            "form-action 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
        ]
    )


def resolve_csp_header(request: Request, response: Response) -> str:
    content_type = (response.headers.get("content-type") or "").lower()
    if request.url.path == "/auth/verify-email" and "text/html" in content_type:
        return build_verification_feedback_csp()
    return build_default_csp()
