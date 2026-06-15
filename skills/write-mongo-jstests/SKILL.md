---
name: write-mongo-jstests
description: Write clean, focused MongoDB jstests with one mocha-style test case per scenario, short purposeful comments, a single shared helper for boilerplate, robust teardown, and correct OWNERS assignment. Use when authoring or restructuring a .js test under jstests/ or src/mongo/**/jstests/.
user-invocable: true
---

# Writing MongoDB jstests

Apply these principles when creating or rewriting a jstest.

## 1. One test case per `it`, mocha-style

Structure new test files with mocha-style `describe`/`it` from `jstests/libs/mochalite.js`. Every
scenario is its own `it(...)` block — this is the clear visual split between cases. The case-specific
intent lives in the `it` name plus its assertions.

```js
import {afterEach, describe, it} from "jstests/libs/mochalite.js";

describe("feature under test", function () {
    afterEach(function () { /* teardown */ });

    it("does X", function () { /* setup via helper, then assert */ });
    it("does Y", function () { /* ... */ });
});
```

Do NOT use a single opaque table/loop that hides the cases, and do NOT cram multiple scenarios into
one `it`.

## 2. Test only the behavior under test

Decide the one thing the test verifies and cut everything orthogonal:

- No negative/boundary cases that exercise unrelated machinery unless that machinery IS the subject.
- No generic "did the whole subsystem behave" checks when the point is one specific outcome.
- Drop flags/params/setup that only existed to support a removed case.

If a parameter exists only to flip between "the thing under test" and "some adjacent behavior",
remove it and keep the test pointed at the one outcome.

## 3. One small shared helper for boilerplate

Put the mechanical setup (start fixture, perform the operation, restart/restore, return a handle) in
one helper so the `it` bodies stay short and readable. Parameterize per case via an options object.

```js
function runScenario({collName, setup, action, ...opts}) {
    // ... build fixture, apply action, return a handle to assert against ...
}
```

Add small assertion helpers too (e.g. `assertState(handle, expected)`) rather than repeating the same
multi-step checks in each case.

## 4. Comments: short and purposeful

Comment only non-obvious intent, trade-offs, or constraints. No step-by-step narration, no restating
what the code plainly does.

```js
// Good: explains a non-obvious constraint
// Pin the stable timestamp so the writes below stay in the oplog for recovery to replay.
```

```js
// Bad: narrates the obvious
// Start a session
const session = primary.startSession();
```

## 5. Robust teardown

Use `afterEach` and track fixture state so a mid-test failure does not leak processes/fixtures.

```js
let fixture;
let fixtureRunning = false;
afterEach(function () {
    if (fixture && fixtureRunning) {
        fixture.stop(); // e.g. rst.stopSet() / MongoRunner.stopMongod(conn)
    }
    fixture = null;
    fixtureRunning = false;
});
```

Set the running flag right after the fixture is up, and clear it when you intentionally stop it (e.g.
a stop-for-restart), so `afterEach` only stops what is actually running.

## 6. Assign the correct owner

A new test file is owned by the nearest `OWNERS.yml`. Default/glob filters often point at the
directory's team, which may not own the feature you are testing. Add a specific filter mapping the new
file to the team that owns the feature under test (not the directory default).

```yaml
  - "my_new_test.js":
    approvers:
      - 10gen/server-<owning-team>
```

Then regenerate the generated CODEOWNERS file:

```bash
bazel run codeowners
```

Never hand-edit `.github/CODEOWNERS` — it is generated from the `OWNERS.yml` files. To find the right
team, check who owns the analogous existing test or the feature's source (a sibling test of the same
feature, the ticket's assigned team, or CODEOWNERS for the source file).

## 7. Standard conventions (jstests/AGENTS.md, cs-robust-jstests)

- Top-of-file comment stating the test's purpose; add required `@tags` (feature flags, `requires_*`,
  `uses_transactions`, etc.).
- Wrap commands in `assert.commandWorked` / check expected failures; use `assert.soon` only for
  eventually-consistent conditions.
- Prefer deterministic outcomes and direct state assertions over timing or count proxies.
- Derive unique namespaces from `jsTestName()` when not running an isolated fixture.
- Pass objects via the `attr` arg instead of `tojson()` in message strings.

## 8. Verify before finishing

Run the test (enabling any required feature flag) until green, then format:

```bash
python3-venv/bin/python3 buildscripts/resmoke.py run --suites=<suite> \
  --additionalFeatureFlags=<featureFlag> path/to/test.js
bazel run format
```

No server C++ changes means no recompile is needed; otherwise `bazel build install-dist-test` first.
