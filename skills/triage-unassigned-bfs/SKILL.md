---
name: triage-unassigned-bfs
description: Lists unassigned hot and cold Build Failures (BFs) for a team and, on request, suggests an owner. Hot BFs get suggestions based on the first failing revision and recent code authors of the failing test/source files; cold BFs get suggestions based on which teammates have the lightest BF load lately. Use when the user asks to "triage unassigned BFs", "list unassigned BFs", "find owners for hot BFs", "balance the cold BF backlog", or shares a BF dashboard / filter URL and wants assignees suggested.
---

# Triage Unassigned BFs

Tooling: Always use the Jira MCP tools on `user-devprod-mcp-gateway` for BF triage; do **not** use the `jira` CLI for this skill. If the Jira MCP returns an auth or gateway issue, stop and report back to the user; do not continue with fallbacks. Glean MCP may miss Jira tickets due to stale indexing, so use it only as supplemental context after the Jira MCP succeeds, never as the source of truth for ticket discovery.

Two-phase workflow. **Always run Phase 1 first.** Only run Phase 2 if the user explicitly asks for owner suggestions or confirms after seeing the Phase 1 list.

## Source board (fixed)

Static board: <https://jira.mongodb.org/secure/Dashboard.jspa?selectPageId=32941> — scopes to the **Catalog and Routing** team's open BFs. Use the JQL templates below directly; do **not** ask the user for a filter URL, JQL, or team name. Only override the team name if the user explicitly says so.

---

## Phase 1 — List unassigned BFs

Use `jira_search_issues` (`user-devprod-mcp-gateway`) to query unassigned non-resolved BFs, split by temperature (run once with `hot`, once with `cold`):

```
project = BF
  and status not in (Resolved, Closed)
  and assignee is EMPTY
  and Temperature ~ "<hot|cold>"
  and "Assigned Teams" = "Catalog and Routing"
```

**JQL gotcha**: `Temperature` only supports `~`, not `=` (HTTP 400 otherwise).

### Output format

Two sections, each a table sorted by **Priority desc, then Created desc** so the most actionable items lead.

**Only list non-Trivial-P5 BFs in tables.** Trivial-P5 BFs (including ones tagged `keep-trivial*`, `not-*-blocker`, `oldshardingemea`, etc.) are noise for triage — collapse them into a single trailing count line per section. Do not list keys, do not give them rows.

```
🔥 Unassigned hot BFs (<count>)

| BF | Priority | Status | Test / Task | Created |
|---|---|---|---|---|
| BF-XXXXX | Major-P3 | Waiting for bug fix | foo.js / sharded_jscore | 3d ago |

_+ <N> Trivial-P5 hot BFs not shown._

🧊 Unassigned cold BFs (<count>)

| BF | Priority | Status | Test / Task | Created | Note |
|---|---|---|---|---|---|
| BF-YYYYY | Major-P3 | Open | bar.js / concurrency | 3d ago | ⚠️ non-trivial |

_+ <N> Trivial-P5 cold BFs not shown._
```

If a section has **no non-trivial BFs**, omit the table and just print the trivial count line — and explicitly call out that there is nothing actionable in that section.

**Always flag non-Trivial-P5 cold BFs with ⚠️** — they deserve a real owner. Do not bury them in a paragraph (lesson learned: a Major-P3 cold BF is the headline, not a parenthetical).

After the tables, ask: *"Want me to suggest owners (Phase 2)?"*

---

## Phase 2 — Suggest owners

Run only after Phase 1 if the user asks. Different strategies for hot vs. cold. For any non-trivial BF, the **fixed pre-flight order** is:

1. **Duplicate check** (below) — same root cause as another BF?
2. **Team-fit / mis-routing check** (below) — does the failure even belong to our team, or is the BF auto-assigned to us only because the failing suite is owned by us?
3. **Owner search** (hot: code blame; cold: load-balance) — only run this once steps 1 and 2 don't fully dispose of the BF.

If step 1 or step 2 dispose of the BF, **stop** — don't suggest a teammate. Re-route or link-as-duplicate instead.

### Mandatory duplicate check (non-trivial BFs)

A **duplicate** here means: two BFs likely share the **same core issue**, such that the same fix would probably apply to both. Do **not** require the same exact test, task, or team. Do **not** prove via deep log analysis (too expensive); infer from **error symptoms** + **execution conditions**.

After `jira_get_issue` succeeds, use Glean MCP (`user-glean_default`) as supplemental context together with Jira fields:

1. Use `jira_get_issue` for the BF, especially to read: `Failing Tests`, `Failing Tasks`, `Failing Buildvariants`, `Bug Symptoms`, `Last Comment`, `Dependencies`, `Fix Revision` (if present).
2. First `search`: short, discriminative failure-signature keywords — BF key (e.g. `BF-42857`), failing test basename (e.g. `change_stream_future_start_time_new_shard.js`), core error fragment (e.g. `A shard named newShard already exists`).
3. Second `search`: failing task/buildvariant + error fragment.
4. If neither surfaces a convincing candidate, run a **symptom-family pass**:
   - Normalize the symptom before searching; keep the durable signal, drop incidental wording.
   - Examples: reduce `No progress was made executing write ops in after 5 rounds (6 rounds total)` and `no progress was made executing bulkWrite ops in after 5 rounds (0 ops completed in 9 rounds total)` to the same family: `NoProgressMade`, `bulk write`, `code 82`. Ignore exact round counts, document ids, hostnames, and `/data/mci/...` path prefixes.
   - Search on the condition bundle, not just the test name: suite/task family; operation family (`movePrimary`, `bulkWrite`, `stepdown`, `unsplittable`, etc.); environment hints that materially affect behavior.
5. `read_document` on top candidate URLs to verify the **symptoms + conditions** line up.
6. Explicitly inspect whether any linked fix/dependency on the candidate BF plausibly applies to the current BF — best cheap proxy for "same core issue."
7. Use `chat` only when synthesis across several candidate sources is needed.

Heuristics:

- Different failing tests do **not** disqualify a duplicate if the symptom family and execution conditions still point to the same bug.
- Different teams do **not** disqualify a duplicate; some bug families cross ownership boundaries.
- A shared generic error alone is **not** enough. `NoProgressMade` or `code 82` by itself only says "same symptom family," not "same root cause."
- Prefer an older BF with a linked fix ticket whose fix description matches the current BF's conditions over a newer BF that only shares a string fragment.
- **Suite-disable / test-skip fixes are sticky.** If a recently-closed BF on the **same suite** with an overlapping test-family was fixed by disabling those tests (e.g. `SERVER-XXX Disable <family> tests in <suite>`), a new BF on the same suite touching any test in that family is almost certainly the same issue — even if the literal exception text differs (one run may surface as a primary assertion, another as a teardown error). Look for a `Dependencies` / `Fix Revision` like `Disable …` or `Skip …` on the candidate BF; that's a high-confidence dup signal.

Confidence rubric:

- **High ("likely duplicate")** — all of: same normalized symptom family; similar execution conditions (same suite/task family, operation family, failover pattern, or other meaningful scenario overlap); candidate BF's known fix/dependency/root-cause notes plausibly apply to the current BF.
- **Medium ("possible duplicate")** — symptom family matches and conditions look related, but fix applicability is still uncertain.
- **Low** — only generic symptom overlap, or conditions/root-cause notes point in different directions; explicitly say no clear duplicate found.

When high confidence, state certainty plainly, link the suspected duplicate ticket(s), and name the fix ticket if one exists. When medium, say whether it looks like a real duplicate or merely the same symptom family.

### Mandatory team-fit / mis-routing check (non-trivial BFs)

Run **after** the duplicate check, **before** any commit blame. BFs are often auto-assigned to the team that owns the failing suite, even when the actual failure has nothing to do with that team's code. Catching this saves the team a useless triage round and gets the BF to the right owner faster.

A BF is **likely mis-routed** if any of these hold:

- `Failure Type` is `system-failed` and `Bug Symptoms` contains test-runner / infra strings such as:
  - `No test results found for target … in 'build_events.json'`
  - `fetch remote test results` / `One or more shards had TIMEOUT or NO_REPORT status` (where "shards" are Bazel test shards, not DB shards)
  - `validating expanded params: AWS key cannot be blank` / `s3.get` / `s3.put` failures
  - `Failed to import a dependency … the task did not initialize the venv`
  - `subprocess.exec … in block 'post' failed: process encountered problem: exit code 127`
  - any Evergreen `Command 'X' in function 'Y'` failure where `Y` is a generic Evergreen function (`do setup`, `fetch …`, `upload …`, `cleanup …`, `kill processes`)
- `Failing Tasks` contains many unrelated tasks across many unrelated suites (a sign the failure hit at the runner / variant level, not in any one suite's code).
- `Failing Buildvariants` is dominated by one variant (often a `*-required` or `*-compile-required` variant) and the buildvariant — not the suite — is the common factor across recent occurrences.
- `First Failing Revision` is a commit that touches files clearly unrelated to the failing suite (e.g. a search/disagg or unrelated component change that wouldn't plausibly affect a sharding suite).
- The error contains no MongoDB-side stack frame, assertion, fassert, invariant, or `src/mongo/...` source pointer.

When mis-routing is suspected, **also do a quick cross-team duplicate sweep** with `jira_search_issues`: search BF for the same `Failing Buildvariants` + `Failure Type = system-failed` regardless of `Assigned Teams`. Sibling BFs on other teams with overlapping infra error fragments are strong evidence the root cause lives in shared infra (DevProd Build / Runtime Environments / Evergreen), not in any product team.

```
project = BF and "Failing Buildvariants" = "<variant>" and "Failure Type" = "system-failed" and updated >= -7d
```

Output for a likely-mis-routed BF (instead of an owner suggestion):

```
BF-XXXXX → likely mis-routed
  Symptom: <short infra-error string>
  Sibling BFs on other teams: BF-AAAA (DevProd Build), BF-BBBB (Storage Engines)
  Recommended re-route target: <DevProd Build | Runtime Environments | Server Triage | …>
  Suggested action: re-route Assigned Teams + link as duplicate of <oldest sibling>
```

Recommended re-route targets (defaults, override only with strong evidence):

- Bazel test-shard / `build_events.json` / `fetch remote test results` → **DevProd Build**
- Evergreen function plumbing (`s3.get`/`s3.put`, AWS creds, `do setup` venv) → **DevProd Build**
- Build-host / OS / package / kernel / EC2 instance issues → **Runtime Environments**
- Compile / linker / sanitizer infra (mold, ASan/UBSan toolchain) → **DevProd Build**
- Genuinely unclear → leave the team alone, but flag in the output as "needs human re-route decision".

If the BF is clearly mis-routed, **do not run the commit-blame step** — it will give a misleading product-code suspect. Stop here for that BF.

### Hot BFs → blame the code

Hot BFs typically come from a recent regression, so the most relevant person is whoever touched the failing code last. **But first, classify the BF** — chronic flakes need a different lookup than fresh regressions.

#### Step 0 — Classify: fresh regression vs chronic flake / timeout

Use `jira_get_issue` and look at these fields:

- `Failure Type` — `system-failed` or `task-timed-out` is a strong "this isn't a code-line bug" signal.
- `Score` and `Score Breakdown` — a Score ≥ 100 with a breakdown line like *"X% of its runs over the past 30 days"* (anything > ~5%) means the suite has been bleeding for weeks. The `First Failing Revision` is just today's run that finally tripped the BF threshold.
- `Count of Linked BFGs (Last 30 days)` — values ≥ ~30 also indicate chronic.
- `Bug Symptoms` — for chronic timeouts this is usually a generic infra string ("shard had TIMEOUT", "no progress was made"), not a source line. Treat that as "no code pointer" and move on.

| Signature | Treat as | Where to look for the culprit commit |
|---|---|---|
| `failed` + specific assertion + `Bug Symptoms` points at `src/mongo/...:LINE` + low BFG count | **Fresh regression** | The `First Failing Revision` and `git_blame` on the asserted line. |
| `system-failed` or `task-timed-out`, OR Score ≥ 100, OR ≥ ~30 BFGs/30d, OR > 5% failure rate | **Chronic flake / timeout** | Recent (last 1–2 weeks) commits to the **production code dir** the suite exercises (e.g. `src/mongo/db/s/` for sharding suites). Ignore the literal first-failing commit; ignore old suite-YAML history. |

#### Step 1 — Fresh-regression path

1. From `jira_get_issue`, pull:
   - `Failing Tests` (custom field) — list of `.js` paths
   - `Failing Buildvariants` and `Failing Tasks` — context only
   - `First Failing Revision` — e.g. `4a82218791380e8fdb01c12169b6b34bca43795e(mongodb-mongo-master)`
   - `Bug Symptoms` — often points at a specific source file (e.g. `src/mongo/db/commands/feature_compatibility_version.cpp:384`)
2. Candidate files: failing test path(s) from `Failing Tests` + any `src/mongo/...` paths mentioned in `Bug Symptoms`.
3. Use git tools (`git_log`, `git_blame`, `git_show`) on each candidate file:
   - `git_log --max-count 5` on the file for the last few authors.
   - `git_show` on the `First Failing Revision` to see what changed in that commit.
   - `git_blame` on the specific lines mentioned in the assertion location.
   - Extract the likely culprit change ticket from commit messages (usually `SERVER-<num>`). Prefer (1) ticket from `First Failing Revision` commit subject, then (2) ticket from most recent touching commit on failing file(s).
4. Cross-reference authors against the team: prefer authors on the assigned team (`<TEAM>`); if the most recent author is outside the team, still surface them as "likely external owner — may need re-routing."
5. Rank candidates: `(commit recency) + (line count touched) + (team membership)`. Pick top 1–2.

#### Step 2 — Chronic-flake / timeout path

1. Identify the **production code area** the suite exercises. For sharding suites, that's `src/mongo/db/s/` (and subdirs like `balancer`, `config`, `resharding`). For replication suites, `src/mongo/db/repl/`. Pick the dir that matches the suite name.
2. `git_log --max-count ~25` on that **production directory** — bound the search to the last 1–2 weeks.
3. Rank by:
   - **Blast radius**: invasive metadata-commit / catalog / locking changes outrank local refactors.
   - **Recency**: prefer commits within the failure-rate spike window. If you don't know exactly when the spike started, prefer the most recent 1–2 weeks; assume anything older than 4 weeks is *not* the trigger unless the user says otherwise.
   - **Suite relevance**: a balancer-active suite spike → favor balancer/migration changes. A `config_transitions_and_add_remove_shard` suite spike → favor topology/add-shard changes.
4. Surface top 2–3 candidates as a table; explicitly tell the user this is a chronic-flake heuristic and offer to bisect via Evergreen failure history if they want a more precise pin.
5. **Do not** rank suite-YAML / hook changes older than ~4 weeks as the suspect — they're almost never the trigger of a fresh spike. If the only "match" is a months-old suite-config tweak, say so and pivot to the production-code path above.

#### Step 3 — Auto-resolve rule already attached?

Before recommending an owner, scan `Last Comment` and the BF's recent activity for phrases like *"A new auto-resolution rule has been created"* with a `Resolution: Duplicate` block. If present:

- **An auto-resolve rule does NOT close the BF.** It is a *bucketing* mechanism — future Build Failures matching the rule's `failure_types` / `tasks` / `tests` / `search_terms` are auto-linked to this BF instead of spawning new BFs. The BF stays open until a human fixes the underlying issue.
- Therefore the rule's presence makes the BF **more** important to own, not less — it's now the canonical inbox for an entire family of recurring failures.
- Surface the rule plainly in the duplicate-check output (`Duplicate check: auto-resolve rule attached by @<author> — this BF is the canonical bucket for <failure pattern>`) and then **continue to the team-fit check and owner search as usual**.
- The rule's **author** is a useful CC / consult (they classified the pattern), but they are not necessarily the right owner of the fix — pick the owner via the normal hot-BF code-blame path.

Default output (one line per hot BF):

```
BF-XXXXX → @<top candidate> (touched <file> in <commit-sha> on <date>)
   alt: @<second candidate> (last author on <other-file>)
```

If the user asks for a table (or columns like `person, ticket, commit, reason`):

```
| Person | Ticket | Commit | Reason |
|---|---|---|---|
| <name> | <culprit-change-ticket, e.g. SERVER-12345> | <sha> | <why this person/commit is likely culprit> |
```

In this table, `Ticket` means the **ticket related to the suspect commit** (e.g. `SERVER-xxxxx`), **not** the BF ticket key.

### Cold BFs → balance the load

Cold BFs are usually long-lived noise; assignment should spread the burden, not punish the last code-toucher.

1. Discover team members from recent BF activity:
   ```
   project = BF and "Assigned Teams" = "Catalog and Routing" and updated >= -30d and assignee is not EMPTY
   ```
   Collect distinct `assignee` values. Only ask the user for a roster if this returns fewer than 3 names.
2. Per teammate, count their **active** BF load (open + in progress + waiting):
   ```
   project = BF and status not in (Resolved, Closed) and assignee = "<email>"
   ```
   Use `total` from `jira_search_issues` (request `max_results: 1` and read `total`; don't fetch all issues).
3. Also count BFs **closed by them** in the last 30 days (proxy for actual triage work, so we don't punish people who clear their queue fast):
   ```
   project = BF and assignee was "<email>" and resolved >= -30d
   ```
   Fallback: some Jira API paths reject `assignee was "<Display Name>"`. If that happens, use `assignee = "<Display Name>" and resolved >= -30d` and call out this proxy in the response.
4. Rank teammates by **active BF count ascending**, breaking ties by lower closed-recently count (lighter overall touch).
5. Per cold BF, suggest the lightest-loaded teammate. Round-robin so the same person isn't suggested for every cold BF in the same run.

Output:

```
Team load (active unresolved BFs):
  @alice — 1
  @bob — 2
  @carol — 3
  ...

Cold BF assignment suggestions (round-robin from lightest):
  BF-YYYYY → @alice
  BF-ZZZZZ → @bob
  ...
```

For non-trivial cold BFs (⚠️ from Phase 1), prefer the lightest-loaded teammate but **also** note recent code authors of the failing area, in case the user wants a hot-style assignment instead.

---

## Style rules

- Use bare jira/github URLs so Slack auto-unfurls them.
- Use `@FirstName LastName` placeholders for people. Never invent Slack user IDs.
- Always show **counts** in section headers (`Unassigned hot BFs (4)`) so the user can spot drift over time.
- Never silently filter out Trivial-P5 — but never list them individually either. Aggregate into a single trailing count line per section so the user knows they exist without drowning in rows.
- For non-trivial BF triage, always include a short `Duplicate check:` line with confidence (`likely duplicate` / `possible duplicate` / `no clear duplicate`) and supporting links.
- If the evidence only gets you to symptom-level overlap, say that plainly, e.g. `possible duplicate (same symptom family only)` rather than over-claiming.
- After Phase 2, offer to draft a Slack ping (delegate to the `hot-bf-pings` skill) or to actually update the assignee via `jira_update_issue` (require explicit confirmation before any write).

## Anti-patterns

- ❌ Don't suggest someone for a hot BF based purely on past triage volume — for hot, code ownership wins.
- ❌ Don't suggest someone for a cold BF based purely on git blame — for cold, fair load wins.
- ❌ Don't treat different tests/tasks/components as near-disqualifying during duplicate triage.
- ❌ Don't require explicit root-cause proof from logs before calling something a likely duplicate; use symptoms + conditions + likely fix applicability.
- ❌ Don't blame the literal `First Failing Revision` for a chronic flake. A high `Score` / high `BFGs/30d` / high failure rate means the spike predates today's commit; reach into recent (last 1–2 week) production-code commits instead.
- ❌ Don't suggest a months-old suite-YAML / hook author as the culprit for a fresh failure-rate spike. If the suite-config history shows nothing within the last ~4 weeks, drop that line of reasoning entirely and pivot to recent production-code authors.
- ❌ Don't assume an attached auto-resolve rule will close the BF. Auto-resolve rules **bucket** future matching failures into the BF; they don't resolve it. The BF still needs an owner — usually it needs one *more* because it now represents a whole family of failures.
- ❌ Don't pick the auto-resolve rule's *author* as the default owner. They classified the failure pattern; the right fix-owner is whoever the normal code-blame / team-fit checks point to.
- ❌ Don't treat `Bug Symptoms` as a code pointer when `Failure Type` is `system-failed` or `task-timed-out`; in those cases it usually contains an effect string ("shard had TIMEOUT"), not a source line.
- ❌ Don't accept the team auto-assignment at face value. A `system-failed` BF whose error is `fetch remote test results`, `build_events.json`, `AWS key cannot be blank`, or `subprocess.exec … exit code 127` is almost always shared-infra, not product code — re-route, don't blame a teammate.
- ❌ Don't confuse "Bazel test shards" with "MongoDB DB shards" in error strings. `One or more shards had TIMEOUT or NO_REPORT status` from `fetch remote test results` is a Bazel-runner failure, not a sharding-cluster failure.
- ❌ Don't run commit blame on a BF that fails the team-fit check — the commit list will produce a confident-looking but wrong product-code suspect.
