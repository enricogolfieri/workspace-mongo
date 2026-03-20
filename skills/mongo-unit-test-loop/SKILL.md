---
name: mongo-unit-test-loop
description: Runs a Bazel unit test in a fix-and-retry loop until it passes, with 10-second heartbeat updates and hang detection. Use when the user asks to run a unit test, keep retrying until green, investigate failures, handle hangs, or report progress every 10 seconds.
---

# Mongo Unit Test Loop

## Purpose

Run one unit test repeatedly until it passes:

- Use the command `bazel test +<unit_test_name>` by default.
- Keep retrying until compile and test both pass.
- If the run hangs or fails, investigate, fix, and retry.
- Post progress updates every 10 seconds so the user can see active work.

## Linked Skills

- Use `mongo-extract-changes` to confirm changed areas and derive candidate targets before running the loop.
- Use `resmoke` when JS/integration repro or follow-up validation is needed.

## Inputs To Confirm

Before starting, gather:

1. Unit test target name (required) also referred as unit_test_name
2. Optional timeout policy for "hang" if user gives one.

If missing or ambiguous, ask with `AskQuestion`.

Always run `mongo-extract-changes` first to confirm scope. If no unit test target is provided, derive candidate `*_test` targets and confirm one with the user.

## Execution Workflow

Copy this checklist and keep it current while working:

```text
Unit Test Loop Progress
- [ ] Run mongo-extract-changes and confirm scope
- [ ] Confirm unit test target
- [ ] Start test run
- [ ] Post 10s heartbeat updates
- [ ] Detect pass/fail/hang
- [ ] If failing/hanging: investigate and fix
- [ ] Re-run test
- [ ] Use resmoke for JS/integration follow-up if needed
- [ ] Stop only when test passes
```

### 1) Start the test run

- Run `bazel test +<unit_test_name>` unless the user requested a different command.
- Use background-friendly execution and monitor terminal output.

### 2) Heartbeat every 10 seconds

- Every 10 seconds, send a short status update in `commentary`, for example:
  - "Test still running; checking output for progress or stalls."
  - "Build phase in progress; no errors yet."
  - "Still waiting on test completion; monitoring logs."
- Never stay silent for more than 10 seconds during long runs.

### 3) Detect outcomes

- **Pass:** stop loop and report success.
- **Fail:** collect key error lines, identify probable root cause, fix code/tests, rerun.
- **Hang:** if output stalls for an extended interval, treat as hang, inspect likely cause, and recover.

For hangs:
- Poll logs every 10 seconds first.
- If clearly stuck, stop the stuck process safely.
- Investigate deadlock/wait/retry patterns or environment blockers.
- Apply a fix and rerun.

### 4) Investigate and fix

When failing or hanging:

1. Capture the minimal relevant error evidence.
2. Form a concrete hypothesis.
3. Edit code/test/build files as needed.
4. Re-run the same unit test.
5. Continue loop until green.

If multiple valid fixes exist or requirements are unclear, ask the user how to proceed using `AskQuestion`.

### 5) Exit criteria

Stop only when the unit test run succeeds (compile + test pass), then report:

- Final command used
- Number of attempts
- What was fixed
- Final passing result

## Communication Style

- Keep updates concise and frequent.
- Prioritize concrete state over vague statements.
- Include current phase: building, running, investigating, fixing, rerunning.
- If blocked by missing context, ask targeted multiple-choice questions.
