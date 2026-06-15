---
name: mongo-failure-investigator
description: >
  Investigates MongoDB test failures from a local log file (./tests.log).
  Use this skill whenever the user says "investigate the test failure",
  "why did the test fail", "investigate the logs", "look at what failed",
  or anything pointing to a test failure that needs root cause analysis.
  Do not wait for an explicit request — if the user mentions a test failure
  and ./tests.log is present, invoke this skill immediately.
  This skill has two phases: Phase 1 is investigation (root cause + code
  pointers), Phase 2 is writing a repro — and Phase 2 only happens if the
  user explicitly agrees with the Phase 1 hypothesis.
---

# MongoDB Test Failure Investigator

Test logs are large. Never read `./tests.log` whole — always use targeted grep
to extract only the relevant signal.

---

## Phase 1: Investigation

### Step 1 — Triage the log

Grep `./tests.log` with this pattern to surface all failure-relevant lines:

```
Task completed - FAILURE|failed to load|invariant|fassert|invalid access|BACKTRACE|\d+ threads? with tid|checkReplicatedDataHa|Tripwire assertion
```

Use at least 30 lines of context around each match (`-C 30`).

This gives you:
- The failure type and message
- Stack frames surrounding a crash
- The test name embedded in the log prefix `[js_test:<name>]`

Also scan near the top of the log for the resmoke invocation line:
```
resmoke.py run ... jstests/path/to/test.js
```
That gives you the exact file path of the test being run.

**Important**: if you see both `fassert`/`BACKTRACE` and `failed to load` for the
same test, the `failed to load` is a consequence of the crash — ignore it and
focus on the real failure.

### Step 2 — Read the failing test

From the resmoke invocation line, get the test file path and read it. You want to
understand:
- What the test is verifying
- The topology it sets up (standalone, replica set, sharded)
- The specific operations and assertions it exercises

### Step 3 — Failure-specific deep dive

Apply the strategy that matches the failure type from Step 1:

#### Crash — `fassert` / `invariant` / `BACKTRACE`

1. Extract the full backtrace from the log (all `#NN 0x... in ...` lines)
2. Skip the first ~10 frames (signal/stacktrace plumbing) — start from the first
   `mongo::` application-code frame
3. Walk up the call chain from the `fassert`/`invariant` frame to understand which
   function triggered it and what state it was checking
4. Read the relevant C++ source around the failing assertion
5. Pay particular attention to locking: `lockGlobal`, `DBLock`, `GlobalLock` in
   the backtrace often indicate a lock-ordering violation or re-entrant locking issue

#### JS assertion failure

1. Find the JS stack trace in the log (distinct from any C++ backtrace)
2. Identify the exact `assert.*()` call that fired and its expected vs. actual values
3. Trace back through the test to understand what operation produced the unexpected result
4. Look at server-side log lines near the same timestamp for additional context

#### Timeout

1. Find what the test was waiting for when it timed out
2. Grep for `\d+ threads? with tid` — thread dumps often reveal deadlocked or stalled threads
3. Look at lock acquisition patterns in the log lines immediately preceding the timeout
4. Assess whether the operation was making any progress or was completely stuck

#### Data inconsistency — `checkReplicatedDataHa` / Tripwire

1. Identify which replica set members diverged
2. Look for replication lag signals or oplog gaps in the surrounding lines
3. Note the oplog operation that was being applied when divergence occurred

### Step 4 — Root cause summary

Present findings in this format — be specific, not verbose:

```
Failing test: jstests/path/to/test.js
Failure type: [crash | js assertion | timeout | data inconsistency]
Root cause: <1–3 sentences: what went wrong and why>
Key evidence: <2–3 most revealing log lines>
Code pointers: <file:line references to relevant source>
```

If the evidence is ambiguous, say so explicitly and describe what would
disambiguate it. Do not speculate beyond what the logs and code show.

Stop here. Phase 2 only begins if the user confirms they agree with the hypothesis.

---

## Phase 2: Repro (only when the user explicitly agrees with the Phase 1 hypothesis)

Create a minimal test that reproduces the failure:

**File**: `jstests/repro.js`

**Rules**:
- Spin up the topology that matches the failure: `ReplSetTest` for replication
  issues, `ShardingTest` for sharding issues, `MongoRunner` for standalone
- Reproduce the specific failure with the smallest possible setup
- No extra assertions, no unrelated cleanup, no surrounding noise
- The test should fail when the bug is present (and ideally pass when it is fixed)

**Reference patterns**:
```js
// Replica set topology
import {ReplSetTest} from "jstests/libs/replsettest.js";
const rst = new ReplSetTest({nodes: 2});
rst.startSet();
rst.initiate();
// ... reproduce the failure ...
rst.stopSet();

// Sharded topology
import {ShardingTest} from "jstests/libs/shardingtest.js";
let s = new ShardingTest({shards: 2});
// ... reproduce the failure ...
s.stop();
```

This is a debugging aid, not a permanent test. Keep it lean.
