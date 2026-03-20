---
name: mongo-dev-workflow
description: Build, test, format, and verify MongoDB server code changes using Bazel. Use when compiling the mongo server, running unit tests, formatting C++ code, or preparing changes for a pull request. For JS integration execution details, defer to linked smoke/resmoke skills.
---

# MongoDB Development Workflow

Instructions for building, testing, and formatting code in the MongoDB server repository. All commands assume the workspace root is the mongo repo checkout.

## Prerequisites

Activate the Python virtual environment before running any command that needs Python (resmoke, format, poetry):

```bash
source .venv/bin/activate
```

The venv should already exist. If it does not, create it:

```bash
/opt/mongodbtoolchain/v5/bin/python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install 'poetry==2.0.0'
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
buildscripts/poetry_sync.sh
```

## 1. Format Code

Run before committing. Formats only files changed relative to the upstream branch:

```bash
source .venv/bin/activate
./buildscripts/clang_format.py format-my
```

This is mandatory before any PR. It auto-detects changed files via git.

## 2. Build (Compile)

### Default build (fast, includes all test binaries)

```bash
bazel build --config=fastbuild install-dist-test --verbose_failures
```

### Build only core server binaries (faster)

```bash
bazel build --config=fastbuild install-devcore --verbose_failures
```

### Build with debug symbols

```bash
bazel build --config=dbg install-dist-test --verbose_failures
```

### Generate compile_commands.json (for IDE/clangd)

```bash
bazel run compiledb
```

Only needed after adding/removing source files or when `compile_commands.json` is missing.

## 3. Run Unit Tests

Unit tests are C++ tests built and executed via Bazel.

### Run a specific unit test target

```bash
bazel test +<target_name> --verbose_failures
```

Example - run the catalog helper test:

```bash
bazel test +//src/mongo/db/timeseries:catalog_helper_test --verbose_failures
```

### Run all unit tests (slow - use sparingly)

```bash
bazel test --test_tag_filters=mongo_unittest,-intermediate_target --local_test_jobs=HOST_CPUS //src/...
```

### How to find the right test target

1. Look for `*_test.cpp` files near the code you changed
2. Check the `BUILD.bazel` file in the same directory for the test target name
3. The target name is usually the test file name without extension

## 4. Run JS Integration Tests (resmoke)

Do not duplicate resmoke command details here.

- Use the `resmoke` skill for resmoke command syntax, options, suite exploration, and diagnostics.
- Use the `mongo-smoke-test` skill for small, sequential smoke passes.
- Use the `extract-author-changes` skill first when you need to pick relevant suites/tests from branch changes.

## 5. Run DB Tests

For C++ integration tests registered in `src/mongo/dbtests/`:

```bash
bazel build --config=fastbuild install-dbtest --verbose_failures
bazel-bin/install/bin/dbtest <test_name>
```

Use `bazel-bin/install/bin/dbtest --list` to see available tests.

## 6. Run Benchmarks

```bash
bazel run <benchmark_target> --verbose_failures
```

Example:

```bash
bazel run //src/mongo/db/query/plan_cache:plan_cache_classic_bm
```

## Pre-PR Verification Workflow

Before requesting a PR review, run through this checklist in order. Stop at the first failure, fix it, and restart from that step.

```
Verification Progress:
- [ ] Step 1: Format code
- [ ] Step 2: Build
- [ ] Step 3: Run related unit tests
- [ ] Step 4: Run related JS tests (if applicable)
```

### Step 1: Format

```bash
bazel run format
```

If formatting changes files, stage and include them in the commit.

### Step 2: Build

```bash
bazel build --config=fastbuild install-dist-test --verbose_failures
```

Fix any compilation errors before proceeding.

### Step 3: Unit tests

Identify test files near the changed code (`*_test.cpp` in the same or nearby directories). Run each one:

```bash
bazel test +//src/mongo/<path>:<test_target> --verbose_failures
```

## Step 4: JS tests (if applicable)

If the change affects behavior tested by JS tests, use linked skills in this order:

1. `extract-author-changes` to identify impacted test areas.
2. `mongo-smoke-test` for fast smoke validation (up to 3 sequential combinations).
3. `resmoke` for full command construction and deeper suite/test execution.

## Important Notes

- **NEVER run resmoke tests in parallel.** Always run them one at a time, sequentially. They use fixed ports and will conflict.
- When monitoring background commands (builds, tests), poll every **10 seconds max**. Do not use long sleep intervals.
- Build outputs go to `bazel-bin/install-dist-test/bin/` (for `install-dist-test` target)
- The `--config=fastbuild` flag is the default balanced mode (optimized + debug info)
- Use `--config=dbg` for full debug builds, `--config=opt` for optimized builds
- Resmoke test logs go to `tests.log` in the working directory
- Always activate `.venv` before running Python-based tools
- Long-running builds and tests should be backgrounded (`block_until_ms: 0`) and monitored via terminal output, polling every 10s.