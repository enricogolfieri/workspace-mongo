---
name: mongo-smoke-test
description: Orchestrates focused MongoDB smoke validation by selecting and sequencing passthrough suite+test combinations. Use when the user asks for a fast smoke pass after code changes. For resmoke command syntax and options, use the resmoke skill.
---

# MongoDB Smoke Test Workflow

Extracted smoke-test workflow for MongoDB server changes.

## Quick Start

Use this checklist and stop on first actionable failure:

```text
Smoke Test Progress:
- [ ] Step 1: Build install-dist-test
- [ ] Step 2: Run mongo-extract-changes and select up to 3 relevant combos
- [ ] Step 3: Run each combo sequentially via the resmoke skill
- [ ] Step 4: Summarize PASS/FAIL/EXCLUDED results
```

## Linked Skills

- Use `mongo-extract-changes` to identify what changed and choose relevant suite+test combinations.
- Use `resmoke` for command syntax, flags, and resmoke-specific troubleshooting.

## Prerequisites

```bash
source .venv/bin/activate
```

If `.venv` is missing:

```bash
/opt/mongodbtoolchain/v5/bin/python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install 'poetry==2.0.0'
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
buildscripts/poetry_sync.sh
```

## Step 1: Build install-dist-test

```bash
bazel build --config=fastbuild install-dist-test --verbose_failures
```

## Step 2: Pick combinations (max 3)

Run `mongo-extract-changes` first and use its file/area summary to pick combinations:

1. Restrict to passthrough-style suites.
2. Choose tests aligned with the changed areas.
3. Cap scope to at most 3 suite+test combinations.

## Step 3: Run resmoke sequentially

Use the `resmoke` skill for command construction, activation requirements, suite options, and diagnostics.

Smoke-specific execution constraints:

- Execute one combination at a time (no parallel runs).
- Keep scope to at most 3 combinations.
- If a test is excluded by a suite and exits quickly, classify it as `EXCLUDED` and pick another combination.

## Step 4: Report smoke results

For each attempted run, report:

- Suite name
- Test file
- Result (`PASS`, `FAIL`, or `EXCLUDED`)
- First actionable error if failed

## Guardrails

- **NEVER run resmoke tests in parallel.** Use strictly sequential execution.
- Poll long-running background commands every 10 seconds max.
- Keep smoke scope small: at most 3 suite+test combinations.
- Build outputs are under `bazel-bin/install-dist-test/bin/`.
- For resmoke logs/options, defer to the `resmoke` skill.
