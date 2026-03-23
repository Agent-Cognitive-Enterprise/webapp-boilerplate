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


def resolve_csp_header(request: Request, response: Response) -> str:
    return build_default_csp()
