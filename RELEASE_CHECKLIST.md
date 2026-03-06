# Release Checklist (Go/No-Go)

Use this checklist before publishing or cutting a release.

Only proceed when every required item is checked.

## 1) Repository Settings (GitHub UI, required)

Path: `Settings -> Advanced Security -> Code security and analysis`

- [x] Enable `Dependency graph`
- [x] Enable `Dependabot alerts`
- [x] Enable `Dependabot security updates`
- [x] Enable `Code scanning`
- [x] Enable `Secret scanning` (if available on your plan)
- [X] Enable `Push protection` (if available on your plan)

Path: `Settings -> Branches -> Branch protection rules -> main`

- [x] Require a pull request before merging
- [X] Require approvals (at least 1)
- [x] Dismiss stale approvals on new commits
- [x] Require status checks to pass before merging
- [x] Require branches to be up to date before merging
- [x] Include administrators

## 2) Required Status Checks on `main`

After the first workflows run, mark these checks as required:

- [x] `backend-tests`
- [x] `frontend-tests`
- [x] `Analyze (python)`
- [x] `Analyze (javascript-typescript)`
- [x] `gitleaks`
- [ ] `analysis`

## 3) Ownership and Review Control

- [x] Verify sensitive paths have explicit owners (`.github/`, `backend/auth/`, `backend/api/`)

## 4) Pre-Publish Validation

From a clean clone or fresh environment:

- [x] Backend install and startup works
- [x] Frontend install and startup works
- [x] Tests pass (`make test` or equivalent backend/frontend commands)
- [x] Docs match reality (ports, env vars, setup, migrations)

## 5) Security and Secrets

- [x] Run full secret scan on working tree
- [x] Run full secret scan on git history
- [x] If a leak is found: rotate secret and remove from history per GitHub guidance
- [x] Verify `.env`, DB files, logs, dumps are ignored
- [x] Replace real-looking tokens/URLs/emails in examples with safe placeholders

## 6) AI and Licensing Gate

- [x] Human review completed for all AI-generated changes
- [x] Confirm rights for all AI input material
- [x] Confirm output is acceptable to open-source under repository license
- [x] Confirm no internal prompts/notes/customer identifiers leaked into repo

## 7) Final Publish Steps

- [x] Push default branch
- [x] Create release tag (for example `v0.1.0`)
- [x] Publish release notes
- [x] Check GitHub Community Profile for missing recommended files
