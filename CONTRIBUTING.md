# Contributing Guide

Thanks for contributing to `webapp-boilerplate`.

## Development Setup

1. Fork and clone the repository.
2. Create a feature branch from `main`.
3. Set up backend:
   `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`
4. Set up frontend:
   `cd frontend && npm install`

## Change Requirements

1. Keep scope focused to the issue/feature.
2. Add or update tests for behavior changes.
3. Update docs when behavior/configuration changes.
4. Avoid committing secrets, local databases, and generated artifacts.

## Verification Before PR

Run the relevant checks before opening a pull request:

1. Backend tests: `cd backend && PYTHONPATH=. pytest -q`
2. Frontend tests: `cd frontend && npm test`
3. Frontend build: `cd frontend && npm run build`

If a check cannot run in your environment, explain why in the PR.

## Pull Request Checklist

1. Clear title and description with motivation.
2. Linked issue (if applicable).
3. Tests added/updated.
4. Docs updated (README, env docs, API/auth docs) if needed.
5. No unrelated refactors.
