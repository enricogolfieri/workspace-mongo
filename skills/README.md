# Enrico's Skill Pack

This folder contains portable skills (`SKILL.md` per skill directory) plus a unified installer for Cursor and Claude.

## Included skills

- `mongo-compile`: compile server code and keep retrying until it builds cleanly.
- `mongo-pr-review`: perform a deep PR review and report risks grouped by severity.
- `mongo-extract-changes`: extract only the author's commit/file changes for accurate scope and provides a readable summary.
- `mongo-smoke-test`: run a focused jstests smoke pass with up to 3 relevant suite+test combos based on your changes.
- `mongo-unit-test-loop`: run one Bazel unit test in a fix-and-retry loop until it passes.
    - Note this is tricky given the model requires to understand what's the actual is (the code vs the test)
    - It's a best-effort and requires an attemptive review from your side.

## Install (clone + run)

From the workspace repository root:

```bash
bash install.sh
```

This installs for **both Claude and Cursor** by default. To install for only one:

```bash
bash install.sh --target claude
bash install.sh --target cursor
```

Default install locations:

- Claude: `~/.claude/skills`
- Cursor: `~/.cursor/skills`

Optional overrides via environment variables:

- `CLAUDE_HOME=/custom/path`
- `CURSOR_HOME=/custom/path`

## What the installer does

- Finds all subdirectories under `skills/` that contain a `SKILL.md`
- Creates a **symlink** from the target app's `skills` directory to each skill in this repo
- Because symlinks are used, any changes you pull to this repo are immediately reflected in your Claude/Cursor configuration without re-running the installer
