---
name: mongo-dev-workflow
description: Build, test, format, and verify MongoDB server code changes using Bazel. Use when compiling the mongo server, running unit tests, running JS integration tests locally with resmoke, formatting C++ code, or preparing changes for a pull request. Also use when the user asks to verify, validate, or check their changes before submitting.
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

JS tests use the resmoke test runner and require a prior build of `install-dist-test`.

### Run a single JS test

```bash
source .venv/bin/activate
python buildscripts/resmoke.py run \
    --storageEngine=wiredTiger \
    --storageEngineCacheSizeGB=0.5 \
    --jobs=1 \
    --installDir bazel-bin/install-dist-test/bin \
    <path/to/test.js>
```

### Run a JS test with a specific suite

```bash
python buildscripts/resmoke.py run \
    --storageEngine=wiredTiger \
    --storageEngineCacheSizeGB=0.5 \
    --jobs=1 \
    --installDir bazel-bin/install-dist-test/bin \
    --suite=<suite_name> \
    <path/to/test.js>
```

### Choosing what to run

Read [suites.md](suites.md) for a list of pre-built suite + test file combinations. Pick **at most 3** that are most relevant to the changes, then run each one **sequentially** (one at a time). Never run multiple resmoke tests in parallel -- they use fixed ports and will conflict.

### Run with verbose logging

Add to the command:

```
--mongodSetParameters='{logComponentVerbosity: {verbosity: 2}}'
--mongosSetParameters='{logComponentVerbosity: {verbosity: 2}}'
```

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
source .venv/bin/activate
./buildscripts/clang_format.py format-my
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

If the change affects behavior tested by JS tests, or if JS tests were modified:

```bash
source .venv/bin/activate
python buildscripts/resmoke.py run \
    --storageEngine=wiredTiger \
    --storageEngineCacheSizeGB=0.5 \
    --jobs=1 \
    --installDir bazel-bin/install-dist-test/bin \
    --suite=<suite-name>
    <path/to/test.js>
```
We defined a combination a test run on a specific suite.
Pick up to 3 relevant combination. Run each one **sequentially**.
You choose a combination by
a) inspect the suites name via `ls buildscripts/resmokeconfig/suites/`
b) pick only "passthrough" suites. The name indicates the fixture type (replica_set vs standalone vs sharding)
c) you inspect the list of tests name via 
    1) `ls jstests/core` - list of folders containing tests that can run on any "passthrough" suite
    2) chose a folder and pick a test within the folder 
This is a best-effort attempt to smoke tests.
Some tests might be banned within the suite. This can happen. You will see the test failing immediately.
Inspect the logs, if you see the test is excluded on that suite just ignore it and pick another one.

## Important Notes

- **NEVER run resmoke tests in parallel.** Always run them one at a time, sequentially. They use fixed ports and will conflict.
- When monitoring background commands (builds, tests), poll every **10 seconds max**. Do not use long sleep intervals.
- Build outputs go to `bazel-bin/install-dist-test/bin/` (for `install-dist-test` target)
- The `--config=fastbuild` flag is the default balanced mode (optimized + debug info)
- Use `--config=dbg` for full debug builds, `--config=opt` for optimized builds
- Resmoke test logs go to `tests.log` in the working directory
- Always activate `.venv` before running Python-based tools
- Long-running builds and tests should be backgrounded (`block_until_ms: 0`) and monitored via terminal output, polling every 10ssuites.md
# Pre-built Test Runs

Pick **at most 3** of the following to run. Each is a ready-to-use `--suite` + test file combination.

## Sharding

| # | Suite | Test file | What it validates |
|---|---|---|---|
| S1 | `sharding` | `jstests/sharding/basic_split.js` | Basic chunk split on a sharded cluster |
| S2 | `sharding` | `jstests/sharding/move_collection_basic.js` | Move a collection between shards |
| S3 | `sharding` | `jstests/sharding/drop_collection.js` | Drop collection in a sharded environment |
| S4 | `sharding` | `jstests/sharding/invalid_system_views_sharded_collection.js` | System views on sharded collections |

## No Passthrough (standalone, exact config)

| # | Suite | Test file | What it validates |
|---|---|---|---|
| N1 | `no_passthrough` | `jstests/noPassthrough/ddl/coll_mod_index_noop.js` | collMod with no-op index changes |
| N2 | `no_passthrough` | `jstests/noPassthrough/catalog/catalog_snapshot_consistency.js` | Catalog snapshot isolation |
| N3 | `no_passthrough` | `jstests/noPassthrough/ddl/coll_mod_convert_to_unique_disallow_duplicates.js` | collMod unique index conversion |
| N4 | `no_passthrough` | `jstests/noPassthrough/timeseries/create/timeseries_create_drop_only_buckets.js` | Timeseries bucket create/drop |

## Aggregation on sharded collections

| # | Suite | Test file | What it validates |
|---|---|---|---|
| A1 | `aggregation_sharded_collections_passthrough` | `jstests/aggregation/views/view_resolution_namespace_collision.js` | View resolution with namespace collisions on sharded cluster |
| A2 | `aggregation_sharded_collections_passthrough` | `jstests/aggregation/sources/agg_stages_basic_behavior_pbt.js` | Basic aggregation stage behavior on sharded collections |

## Core views (passthrough variants)

| # | Suite | Test file | What it validates |
|---|---|---|---|
| V1 | `sharding_jscore_passthrough` | `jstests/core/views/views_find.js` | Views with find on a sharded cluster |
| V2 | `replica_sets_jscore_passthrough` | `jstests/core/views/views_find.js` | Views with find on a replica set |
| V3 | `sharded_collections_jscore_passthrough` | `jstests/core/views/views_validation.js` | View validation on sharded collections |

## How to pick

- **Changed catalog/DDL code** (collMod, drop, create)? Pick S3, N1, N2.
- **Changed sharding/routing code**? Pick S1, S2, S4.
- **Changed timeseries code**? Pick N4, S3.
- **Changed views code**? Pick V1, V2, S4.
- **Changed aggregation code**? Pick A1, A2.
- **Not sure / general change**? Pick S1, N2, V1.