# AGENTS.md

This file defines repository-wide instructions for AI coding assistants.

It is intentionally generic so it can be reused across projects.
Project-specific product goals, architecture, setup, and roadmap belong in `README.md` and any deeper, path-specific documentation.

If a deeper or path-specific `AGENTS.md` is added later, the more specific file should take precedence for files in that subtree. Otherwise, this root file is the default house law.


---

## 1. Purpose

Use this file to govern how agents work in the repository.

Use `README.md` and other project documentation to understand:
- what the project is for,
- what the architecture should be,
- what is already implemented,
- what remains to be done.

If this file and project-specific documentation appear to conflict, prefer the more specific project-level instruction unless it would reduce code quality, testing discipline, or documentation truthfulness.

---

## 2. Core working rules

### 2.1 Read before writing

Before making changes:
1. Read this `AGENTS.md`.
2. Read the relevant parts of `README.md` and any task-specific docs.
3. Inspect the current repository state.
4. Identify the exact acceptance criteria, affected files, and required tests.
5. Make a small plan before editing.

Do not make blind edits.

### 2.2 Keep changes scoped

- Prefer small, targeted changes over broad rewrites.
- Change only the files needed for the task unless a broader refactor is required.
- Avoid incidental cleanup unrelated to the current task.
- Preserve existing behavior unless the task explicitly changes it.

### 2.3 No fake completion

Do not claim work is complete unless:
- the implementation exists,
- the relevant tests were added or updated,
- the required verification commands were run,
- documentation was updated where reality changed.

---

## 3. Testing policy

### 3.1 Every non-trivial code change must be tested

This is a hard rule.

Examples:
- New logic -> add or update unit tests.
- Bug fix -> add or update a regression test.
- API change -> add or update integration or contract tests.
- UI change -> add or update UI tests.
- CLI change -> add or update CLI tests.
- Config or orchestration change -> add focused tests or validation coverage.

If a change cannot reasonably be tested in the usual way, the agent must:
- explain why,
- add the closest useful test coverage possible,
- document the remaining gap explicitly.

### 3.2 Test the right layer

Prefer the narrowest test that proves the behavior, but use broader coverage when needed.

Typical ladder:
- unit tests,
- integration tests,
- end-to-end or UI tests,
- smoke tests.

### 3.3 UI test rule

DOM presence alone is not proof of correctness.
For UI work, verify as applicable:
- existence,
- visibility,
- interactability,
- semantic correctness,
- user-visible outcome.

### 3.4 Regression rule

Every bug fix should add or update a regression test unless there is a documented reason not to.

---

## 4. Verification rules

After every meaningful code change, run the relevant verification commands for the affected stack.

Prefer repository-standard commands when they exist, for example:
- Make targets
- task runner commands
- `tox`, `nox`, `pytest`
- `ruff`, `mypy`
- `npm test`, `pnpm test`, `playwright test`

Minimum rule:
- run the narrowest relevant checks while iterating,
- run the broader required suite before marking work complete.
- for meaningful backend changes, run the full backend test suite before marking work complete
- for meaningful frontend changes, run the full frontend test suite before marking work complete
- for changes that affect both stacks or shared behavior, run both full backend and full frontend suites before marking work complete

Do not leave the repository in a knowingly failing state unless the task explicitly asks for a spike, failing repro, or partial draft.

---

## 5. Documentation maintenance

Documentation is part of the deliverable.
If code, behavior, setup, layout, configuration, or workflow changes, update the relevant documentation.

Typical files include:
- `README.md`
- setup docs
- architecture docs
- examples
- configuration samples
- inline comments where needed

### 5.1 TODO handling in README.md and docs

If the repository uses `TODO:` markers as implementation backlog items:
- remove a `TODO:` only when the described work is actually complete,
- if work is partial, replace it with a smaller and truthful remaining `TODO:`,
- if implementation reveals new required work, add a new `TODO:` in the appropriate place,
- keep documentation truthful at all times.

Bad behavior:
- deleting TODOs because scaffolding exists,
- deleting TODOs because work started,
- leaving docs stale after behavior changed.

Good behavior:
- updating text to reflect reality,
- removing only the TODOs that are no longer true,
- narrowing partial TODOs instead of deleting them.

---

## 6. Code style expectations

Unless the repository states otherwise:

### 6.1 General

- Prefer readable, explicit code over clever code.
- Favor small functions and clear responsibilities.
- Keep side effects obvious.
- Name important constants.
- Use types where practical.
- Add comments when intent is non-obvious.
- Avoid giant god-functions and tangled control flow.

### 6.2 Errors and logs

- Fail clearly.
- Surface actionable error messages.
- Do not swallow exceptions without a reason.
- Preserve useful evidence for debugging.
- Prefer structured results over vague success or failure strings when practical.

---

## 7. Review loop discipline

If the project uses a creator-checker, implementer-reviewer, or similar loop:
- only the implementation side should modify repository artifacts,
- the review side may inspect, test, verify, approve, reject, block, or escalate,
- the review side must not silently change code.

If a task is blocked, report:
- what is blocked,
- why it is blocked,
- what evidence supports the block,
- what the smallest next unblock step is.

---

## 8. Anti-loop discipline

Iterative coding loops can get stuck repeating the same weak fix and the same weak feedback.
Avoid polite infinite loops.

Treat a task as stalled when repeated iterations are semantically the same and the failing evidence is materially unchanged.
When stalled:
- state clearly that repetition has occurred,
- explain why prior attempts were ineffective,
- narrow the next step to one concrete experiment,
- escalate if needed.

Escalation may include:
- alternate reviewer,
- alternate model,
- narrower sub-task,
- human intervention.

---

## 9. Preferred implementation workflow

When implementing a task:
1. Read the relevant docs.
2. Identify acceptance criteria and affected files.
3. Inspect the current implementation.
4. Make the smallest coherent change.
5. Add or update tests.
6. Run verification.
7. Fix failures.
8. Update documentation.
9. Summarize what changed, what was tested, and what remains.

---

## 10. Reporting expectations

When reporting completed work, include:
- files changed,
- behavior added or changed,
- tests added or updated,
- commands run,
- documentation updated,
- remaining risks, caveats, or follow-up work.

---

## 11. What not to do

Do not:
- mark work complete without testing,
- rely on generated code alone as proof of correctness,
- delete TODOs without full implementation,
- make unrelated refactors during focused tasks,
- ignore failing verification,
- leave documentation stale after changing behavior,
- silently change more than the task requires.

---

## 12. File naming

This repository uses `AGENTS.md` as the shared instruction file for coding assistants.

If tool-specific files are added later, keep shared rules here and put tool-specific additions in their own files.

Examples:
- `AGENTS.md` -> shared repository-wide instructions
- `.github/copilot-instructions.md` -> GitHub Copilot-specific additions
- other tool-specific config files -> optional extra behavior for a specific assistant

---

## Code Shape and Test Performance Rules

These rules are mandatory unless there is a clearly documented reason to deviate.

### 1. Avoid gravity wells

A gravity well is a file that becomes too large, attracts unrelated logic, and gets harder to reason about, test, and safely modify.

Rules:

- Prefer small, focused files with a single clear responsibility.
- Soft limit: keep source files under **400 lines**.
- Hard limit: do not let source files exceed **600 lines** unless explicitly justified in comments or project notes.
- If a file approaches the soft limit, split it before adding more logic.
- Do not use a large file as a convenience bucket for “just one more thing”.
- Organize by responsibility, not by dumping related-but-different concerns into one file.
- When splitting, prefer extracting:
  - domain logic
  - adapters/integrations
  - validation/serialization
  - UI subcomponents
  - test helpers
- Generated files, lockfiles, migrations, and fixture snapshots are exempt, but handwritten source files are not.

Heuristics that require refactoring even before line limits are reached:

- the file mixes multiple responsibilities
- the file is difficult to navigate without search
- unrelated changes often touch the same file
- tests require large setup because too much behavior lives together

### 2. Avoid functions with too many arguments

Functions with too many arguments are harder to understand, harder to call correctly, and usually signal missing structure.

Rules:

- Prefer **5 or fewer arguments** per function.
- Hard limit: **7 arguments maximum**.
- If a function needs more than 5 arguments, refactor.
- Group related inputs into a typed object or structure rather than passing long primitive argument lists.
- Prefer explicit domain types over long sequences of `str`, `int`, `bool`, `dict`, etc.
- Avoid boolean flag accumulation. If a function has multiple boolean flags, redesign it.
- If optional arguments keep growing, split the function into smaller functions or introduce a request/config object.
- Public APIs should be especially strict here.

Preferred remedies:

- introduce a small typed parameter object
- split orchestration from implementation
- separate read/validate/transform/persist stages
- move repeated argument groups into a domain model

Do not hide bad design inside a giant “context” object. Group arguments only when they are meaningfully related.

### 3. Tests must stay fast

Slow tests reduce iteration speed and make the codebase hostile to development. Test speed is a feature.

Rules:

- Favor fast unit tests by default.
- Investigate any test or test group that feels slow.
- If tests become noticeably slower, stop and fix the cause rather than accepting the regression.
- Avoid real network calls, unnecessary filesystem work, long sleeps, large fixtures, and heavyweight setup in normal test runs.
- Mock or fake external systems unless the test is explicitly integration or end-to-end.
- Keep fixtures minimal and reusable.
- Prefer deterministic tests with small inputs.
- Reset state cheaply.
- Run only the minimal required setup for each test.

Performance expectations:

- Unit tests should usually run in milliseconds.
- Any individual test taking around **>1 second** should be treated as suspicious and reviewed.
- Any test suite slowdown should trigger investigation.
- Add or maintain separate categories for:
  - fast unit tests
  - integration tests
  - end-to-end tests
- The default local and CI test command should prioritize the fast suite.

When tests are slow, investigate and fix by checking for:

- unnecessary sleeps or retry waits
- real I/O where fakes would work
- expensive global fixtures
- database setup repeated per test when avoidable
- oversized factories/fixtures
- accidental integration coverage inside unit tests
- poor test isolation causing cascading setup
- inefficient algorithms in the code under test

The correct response to slow tests is optimization, decomposition, or better test design, not simply raising timeouts.

### Enforcement mindset

When making changes:

- do not add code to an already-large file without first considering extraction
- do not add “just one more argument” to a function already near the limit
- do not accept slow tests as normal

If a rule must be broken, document:
1. why the exception is necessary
2. why simpler alternatives were rejected
3. what future refactor would remove the exception

### Delivery flow

When you finish the current task:

- suggest the next task that most directly brings the project closer to its goal
- if the user replies with `yes`, start working on that task immediately

## Session handoff discipline

At the end of each meaningful task, and before yielding control, update `HANDOFF.md`.

Purpose:
- Preserve enough context for a new session to resume work quickly.
- Record what was completed, current status, and the immediate next step.

Rules:
- Read and follow `AGENTS.md`.
- Keep `HANDOFF.md` concise, current, and action-oriented.
- Prefer overwriting stale content rather than appending indefinitely.
- Do not turn `HANDOFF.md` into a changelog, diary, or long narrative.
- Keep entries factual, specific, and relevant to the current workstream.
- Include only the minimum context needed for a fresh agent or session to continue effectively.
- Always update the `Last updated` timestamp.
- If priorities changed, explicitly rewrite `Current objective` and `Next step`.
- If work is fully complete, mark that clearly and state what should be tackled next, if anything.
- If blocked, state the blocker clearly and the exact condition required to unblock progress.
- If `HANDOFF.md` grows beyond roughly 150 to 250 lines, compress it. Keep only current-relevant context and remove obsolete details.
- Maintain the exact section structure shown below so future sessions can parse it quickly.

Use the following template for `HANDOFF.md`:

# HANDOFF

## Current objective
...

## Completed in this session
- ...
- ...

## Current status
...

## Next step
...

## Important files
- path/to/file
- path/to/file

## Notes for next session
...

## Last updated
YYYY-MM-DD HH:MM TZ
