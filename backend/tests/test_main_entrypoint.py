import main


def test_run_calls_startup_migration_preflight_before_server_start(
    monkeypatch,
) -> None:
    calls: list[str] = []
    uvicorn_target: dict[str, str] = {}

    def fake_preflight() -> None:
        calls.append("preflight")

    def fake_uvicorn_run(app_target: str, **_: object) -> None:
        calls.append("uvicorn")
        uvicorn_target["value"] = app_target

    monkeypatch.setattr(
        "services.startup_migrations.run_startup_migration_preflight",
        fake_preflight,
    )
    monkeypatch.setattr(main.uvicorn, "run", fake_uvicorn_run)

    main.run()

    assert calls == ["preflight", "uvicorn"]
    assert uvicorn_target["value"] == "main:app"
