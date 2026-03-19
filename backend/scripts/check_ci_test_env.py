#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml


FORBIDDEN_TEST_ENV_KEYS = (
    "AUTH_SECRET_KEY",
    "INITIAL_SETUP_TOKEN",
)
TEST_JOBS = (
    "backend-quality",
    "frontend-e2e",
)


def _load_ci_workflow(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("CI workflow did not parse to a mapping")
    return loaded


def _find_forbidden_test_env_entries(workflow: dict) -> list[str]:
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        raise ValueError("CI workflow is missing a jobs mapping")

    findings: list[str] = []
    for job_name in TEST_JOBS:
        job = jobs.get(job_name)
        if not isinstance(job, dict):
            findings.append(f"missing required CI job: {job_name}")
            continue

        env = job.get("env") or {}
        if not isinstance(env, dict):
            findings.append(f"job {job_name} has a non-mapping env block")
            continue

        for key in FORBIDDEN_TEST_ENV_KEYS:
            if key in env:
                findings.append(f"job {job_name} must not define env.{key}")

    return findings


def main(argv: list[str] | None = None) -> int:
    del argv
    workflow_path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
    workflow = _load_ci_workflow(workflow_path)
    findings = _find_forbidden_test_env_entries(workflow)

    if findings:
        print("CI test env guard failed:")
        for finding in findings:
            print(f"- {finding}")
        print(
            "Use backend/tests/test_env.py as the shared source of truth for test auth/setup defaults."
        )
        return 1

    print("CI test env guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
