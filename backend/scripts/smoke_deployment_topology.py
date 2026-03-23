#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
FRONTEND_NGINX_CONFIG = REPO_ROOT / "deploy" / "nginx.frontend.conf.example"
API_NGINX_CONFIG = REPO_ROOT / "deploy" / "nginx.api.conf.example"
DEFAULT_FRONTEND_URL = "https://app.example.com"
DEFAULT_API_URL = "https://api.example.com"
DEV_API_URL = "http://localhost:8000"


@dataclass(frozen=True)
class SmokeConfig:
    frontend_dir: Path
    frontend_dist_dir: Path
    frontend_nginx_config: Path
    api_nginx_config: Path
    frontend_url: str
    api_url: str


def _normalize_origin(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Expected absolute URL, got: {url!r}")
    return f"{parsed.scheme}://{parsed.netloc}"


def _origin_host(url: str) -> str:
    parsed = urlparse(_normalize_origin(url))
    assert parsed.netloc
    return parsed.netloc


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_dist_texts(dist_dir: Path) -> dict[Path, str]:
    if not dist_dir.exists():
        raise ValueError(f"Frontend build output directory does not exist: {dist_dir}")

    texts: dict[Path, str] = {}
    for path in sorted(dist_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".html", ".js", ".css"}:
            continue
        texts[path] = _read_text(path)

    if not texts:
        raise ValueError(f"No HTML/JS/CSS files found under frontend build output: {dist_dir}")

    return texts


def validate_frontend_dist(dist_dir: Path, api_url: str) -> None:
    normalized_api_url = _normalize_origin(api_url)
    texts = _read_dist_texts(dist_dir)
    index_path = dist_dir / "index.html"

    if index_path not in texts:
        raise ValueError(f"Missing expected frontend entrypoint: {index_path}")

    if not any(path.suffix == ".js" and path.parent.name == "assets" for path in texts):
        raise ValueError("Expected at least one built JavaScript asset under dist/assets/")

    if any(DEV_API_URL in content for content in texts.values()):
        raise ValueError(
            f"Built frontend output still references the development API origin: {DEV_API_URL}"
        )

    if not any(normalized_api_url in content for content in texts.values()):
        raise ValueError(
            f"Built frontend output does not reference the configured API origin: {normalized_api_url}"
        )


def validate_frontend_nginx_config(config_path: Path, frontend_url: str, api_url: str) -> None:
    config = _read_text(config_path)
    frontend_host = _origin_host(frontend_url)
    normalized_api_url = _normalize_origin(api_url)

    required_fragments = (
        f"server_name {frontend_host};",
        "root /srv/webapp/frontend/dist;",
        "return 301 https://$host$request_uri;",
        "try_files $uri /index.html;",
        "Content-Security-Policy",
        f"connect-src 'self' {normalized_api_url}",
    )

    for fragment in required_fragments:
        if fragment not in config:
            raise ValueError(
                f"Frontend Nginx config {config_path} is missing required fragment: {fragment}"
            )


def validate_api_nginx_config(config_path: Path, api_url: str) -> None:
    config = _read_text(config_path)
    api_host = _origin_host(api_url)

    required_fragments = (
        f"server_name {api_host};",
        "return 301 https://$host$request_uri;",
        "proxy_set_header Host $host;",
        "proxy_set_header X-Forwarded-Proto https;",
        "proxy_set_header X-Forwarded-Host $host;",
        "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
    )

    for fragment in required_fragments:
        if fragment not in config:
            raise ValueError(
                f"API Nginx config {config_path} is missing required fragment: {fragment}"
            )


def build_frontend(frontend_dir: Path, api_url: str) -> None:
    env = os.environ.copy()
    env["VITE_API_URL"] = _normalize_origin(api_url)

    subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        env=env,
        check=True,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the frontend with the production API URL and validate the documented "
            "frontend-host/API-proxy deployment topology."
        )
    )
    parser.add_argument(
        "--frontend-url",
        default=DEFAULT_FRONTEND_URL,
        help=f"Public frontend origin to validate (default: {DEFAULT_FRONTEND_URL})",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Public API origin to validate (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--frontend-dir",
        type=Path,
        default=FRONTEND_DIR,
        help=f"Frontend project directory (default: {FRONTEND_DIR})",
    )
    parser.add_argument(
        "--frontend-dist-dir",
        type=Path,
        default=FRONTEND_DIST_DIR,
        help=f"Frontend build output directory (default: {FRONTEND_DIST_DIR})",
    )
    parser.add_argument(
        "--frontend-nginx-config",
        type=Path,
        default=FRONTEND_NGINX_CONFIG,
        help=f"Frontend Nginx example to validate (default: {FRONTEND_NGINX_CONFIG})",
    )
    parser.add_argument(
        "--api-nginx-config",
        type=Path,
        default=API_NGINX_CONFIG,
        help=f"API Nginx example to validate (default: {API_NGINX_CONFIG})",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip the frontend build step and validate the existing dist output only.",
    )
    return parser


def _build_config(args: argparse.Namespace) -> SmokeConfig:
    return SmokeConfig(
        frontend_dir=args.frontend_dir,
        frontend_dist_dir=args.frontend_dist_dir,
        frontend_nginx_config=args.frontend_nginx_config,
        api_nginx_config=args.api_nginx_config,
        frontend_url=_normalize_origin(args.frontend_url),
        api_url=_normalize_origin(args.api_url),
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = _build_config(args)

    print("== Deployment Topology Smoke Check ==")
    print(f"- frontend origin: {config.frontend_url}")
    print(f"- api origin: {config.api_url}")

    if not args.skip_build:
        print(f"- building frontend in {config.frontend_dir}")
        build_frontend(config.frontend_dir, config.api_url)
    else:
        print("- skipping frontend build")

    print(f"- validating frontend dist in {config.frontend_dist_dir}")
    validate_frontend_dist(config.frontend_dist_dir, config.api_url)

    print(f"- validating frontend Nginx config {config.frontend_nginx_config}")
    validate_frontend_nginx_config(
        config.frontend_nginx_config,
        frontend_url=config.frontend_url,
        api_url=config.api_url,
    )

    print(f"- validating API Nginx config {config.api_nginx_config}")
    validate_api_nginx_config(config.api_nginx_config, api_url=config.api_url)

    print("Smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
