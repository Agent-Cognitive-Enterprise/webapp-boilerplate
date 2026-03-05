# Release Checklist (Go/No-Go)

Use this checklist before publishing or cutting a release.

Only proceed when every required item is checked.

## 1) Repository Settings (GitHub UI, required)

Path: `Settings -> Advanced Security -> Code security and analysis`

- [x] Enable `Dependency graph`
- [x] Enable `Dependabot alerts`
- [x] Enable `Dependabot security updates`
- [ ] Enable `Code scanning`
- [ ] Enable `Secret scanning` (if available on your plan)
- [ ] Enable `Push protection` (if available on your plan)

Path: `Settings -> Security -> Vulnerability reporting`

- [ ] Enable `Private vulnerability reporting`

Path: `Settings -> Branches -> Branch protection rules -> main`

- [ ] Require a pull request before merging
- [ ] Require approvals (at least 1)
- [ ] Dismiss stale approvals on new commits
- [ ] Require status checks to pass before merging
- [ ] Require branches to be up to date before merging
- [ ] Include administrators

## 2) Required Status Checks on `main`

After the first workflows run, mark these checks as required:

- [ ] `backend-tests`
- [ ] `frontend-tests`
- [ ] `Analyze (python)`
- [ ] `Analyze (javascript-typescript)`
- [ ] `gitleaks`
- [ ] `analysis`

## 3) Ownership and Review Control

- [ ] Update `.github/CODEOWNERS` with real GitHub users/teams (`@org/team`)
- [ ] Verify sensitive paths have explicit owners (`.github/`, `backend/auth/`, `backend/api/`)

## 4) Pre-Publish Validation

From a clean clone or fresh environment:

- [ ] Backend install and startup works
- [ ] Frontend install and startup works
- [ ] Tests pass (`make test` or equivalent backend/frontend commands)
- [ ] Docs match reality (ports, env vars, setup, migrations)

## 5) Security and Secrets

- [ ] Run full secret scan on working tree
- [ ] Run full secret scan on git history
- [ ] If a leak is found: rotate secret and remove from history per GitHub guidance
- [ ] Verify `.env`, DB files, logs, dumps are ignored
- [ ] Replace real-looking tokens/URLs/emails in examples with safe placeholders

## 6) AI and Licensing Gate

- [ ] Human review completed for all AI-generated changes
- [ ] Confirm rights for all AI input material
- [ ] Confirm output is acceptable to open-source under repository license
- [ ] Confirm no internal prompts/notes/customer identifiers leaked into repo

## 7) Final Publish Steps

- [ ] Push default branch
- [ ] Create release tag (for example `v0.1.0`)
- [ ] Publish release notes
- [ ] Check GitHub Community Profile for missing recommended files
