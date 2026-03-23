---
name: mongo-compile
description: Compiles MongoDB server code with a fix-and-retry loop until build success. Use when the user asks to compile server code, resolve compilation failures, or keep retrying build errors until green. Links to the resmoke skill for post-compile test execution.
---

# Mongo Compile

Compile server code and keep iterating until the build succeeds.

## Linked Skills

- Use `resmoke` after successful compilation when integration or JS validation is requested.

## Inputs To Confirm

Before starting, confirm:

1. Build target (default `install-dist-test`).
2. Build config (default `--config=fastbuild`).

If user does not specify, run:

```bash
bazel build --config=fastbuild install-dist-test --verbose_failures
```

## Compile Loop

Copy this checklist and keep it current:

```text
Compile Progress
- [ ] Confirm target and config
- [ ] Start build
- [ ] Monitor output with <=10s polling
- [ ] If compile fails: diagnose and fix
- [ ] Re-run build
- [ ] Stop only when compilation succeeds
```

### 1) Start build

- Start the build command.
- Prefer background-friendly execution for long builds and monitor output.

### 2) Polling and waiting rule

- If waiting between checks, never sleep more than 10 seconds.
- Keep status updates frequent during long builds.

### 3) On failure: fix and retry

When compilation fails:

1. Capture minimal actionable compiler errors.
2. Identify root cause and edit relevant code.
3. Re-run the same compile command.
4. Repeat until success.

### 4) Exit condition

Return only after successful compilation.

Report:

- Final compile command
- Number of attempts
- Key fix(es) applied
- Final success confirmation
