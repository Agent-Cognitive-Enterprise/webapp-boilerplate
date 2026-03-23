from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


def _load_module():
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "smoke_deployment_topology.py"
    )
    spec = importlib.util.spec_from_file_location("smoke_deployment_topology_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_frontend_dist_accepts_built_output_with_configured_api_url(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text(
        '<!doctype html><script type="module" src="/assets/app.js"></script>',
        encoding="utf-8",
    )
    (assets_dir / "app.js").write_text(
        'const apiBaseUrl = "https://api.example.com"; console.log(apiBaseUrl);',
        encoding="utf-8",
    )

    mod.validate_frontend_dist(dist_dir, "https://api.example.com")


def test_validate_frontend_dist_rejects_development_api_origin(tmp_path: Path) -> None:
    mod = _load_module()
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text(
        '<!doctype html><script type="module" src="/assets/app.js"></script>',
        encoding="utf-8",
    )
    (assets_dir / "app.js").write_text(
        'const apiBaseUrl = "http://localhost:8000"; console.log(apiBaseUrl);',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="development API origin"):
        mod.validate_frontend_dist(dist_dir, "https://api.example.com")


def test_main_builds_and_validates_deployment_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    mod = _load_module()
    frontend_dir = tmp_path / "frontend"
    dist_dir = frontend_dir / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    frontend_config = tmp_path / "nginx.frontend.conf"
    api_config = tmp_path / "nginx.api.conf"

    frontend_config.write_text(
        "\n".join(
            [
                "server {",
                "    server_name app.example.com;",
                "    root /srv/webapp/frontend/dist;",
                "    return 301 https://$host$request_uri;",
                "    add_header Content-Security-Policy \"connect-src 'self' https://api.example.com\" always;",
                "    location / {",
                "        try_files $uri /index.html;",
                "    }",
                "}",
            ]
        ),
        encoding="utf-8",
    )
    api_config.write_text(
        "\n".join(
            [
                "server {",
                "    server_name api.example.com;",
                "    return 301 https://$host$request_uri;",
                "    proxy_set_header Host $host;",
                "    proxy_set_header X-Forwarded-Proto https;",
                "    proxy_set_header X-Forwarded-Host $host;",
                "    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    def _fake_build(project_dir: Path, api_url: str) -> None:
        assert project_dir == frontend_dir
        assert api_url == "https://api.example.com"
        (dist_dir / "index.html").write_text(
            '<!doctype html><script type="module" src="/assets/app.js"></script>',
            encoding="utf-8",
        )
        (assets_dir / "app.js").write_text(
            'const apiBaseUrl = "https://api.example.com"; console.log(apiBaseUrl);',
            encoding="utf-8",
        )

    monkeypatch.setattr(mod, "build_frontend", _fake_build)

    rc = mod.main(
        [
            "--frontend-dir",
            str(frontend_dir),
            "--frontend-dist-dir",
            str(dist_dir),
            "--frontend-nginx-config",
            str(frontend_config),
            "--api-nginx-config",
            str(api_config),
        ]
    )
    out = capsys.readouterr().out

    assert rc == 0
    assert "Smoke check passed." in out
