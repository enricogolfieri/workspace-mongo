---
name: ticket-state-machine
description: >-
  MANDATORY when invoked or attached. Delivers Jira tickets end-to-end as a
  resumable state machine. Every session runs PRECHECK → LOAD_MEMORY → EXECUTION
  before any ticket-scoped answers or repo edits. Overrides narrow code-only
  interpretation of the user message.
user-invocable: true
---

# Ticket State Machine

Deliver a Jira ticket end-to-end as a resumable state machine.

## Invocation contract (mandatory)

When this skill is **attached** or the user invokes **`/ticket-state-machine <TICKET>`**:

1. **This skill governs the entire session.** No ticket-scoped code edits, Jira lookups, or ticket-scoped answers until **PRECHECK → LOAD_MEMORY** complete successfully.
2. **Sub-questions do not bypass the workflow.** Questions like “why is this test written this way?” are answered *after* LOAD_MEMORY, using restored `state.json`, `context.md`, and branch diffs — not by improvising from the open file alone.
3. **Ask mode does not exempt you.** Complete PRECHECK and LOAD_MEMORY with readonly tools; defer repo edits until Agent mode. If PRECHECK fails, stop and report the blocker — do not answer ticket-scoped questions from partial context.
4. **Do not treat attached code selections as a separate task.** If the skill is active, the selection is handled inside the current `phase_reached`, not as a one-off Q&A that skips session states.
5. **End every EXECUTION turn** with `state_memory.py dump` when anything changed (code, validation, plan, gotchas, branch, or understanding).
6. **Final response must include:** `phase_reached`, memory path (`/tmp/<ticket-key>/`), `branch` (if set), whether `state.json` was updated this turn, validation results, PR URL if any, and any skipped optional phases with reason.

If steps 1–3 cannot complete, **stop and report the blocker**. Do not improvise ticket work.

Two layers:

| Layer | What | In `phase_reached`? | Memory dump? |
|-------|------|---------------------|--------------|
| **Session** | PRECHECK, LOAD_MEMORY, EXECUTION | Never | No |
| **Execution** | LOAD_TICKET_CONTEXT … OPEN_DRAFT_PR | Yes | Yes |

Every session runs in order:

```text
PRECHECK  →  LOAD_MEMORY  →  EXECUTION
```

Do not skip user confirmation gates in execution phases.

**Reminder:** See [Invocation contract (mandatory)](#invocation-contract-mandatory) — session states run before execution phases on every turn.

## Requirements

**Ticket key** (required) — usually `SERVER-XXXXX`.

**Optional inputs** — preserve in memory when provided:
- `user_instructions` — user steering guidance
- `extra_context` — arbitrary structured context
- `work_kind` — `original` (default) or `sub-work`

## Session

Session states run on **every invocation** (new ticket or resume). They are never stored in `phase_reached` and never call `state_memory.py dump`.

### PRECHECK

**Purpose:** Verify prerequisites before any ticket work.

**Steps:**
1. Require the ticket key. If missing, ask and stop.
2. Verify the devprod MCP is installed and available.
3. Verify devprod MCP authentication with the smallest harmless read possible.
4. Before calling any MCP tool, read that tool's JSON descriptor/schema.
5. Use only the devprod MCP for Jira and docs.
6. Re-verify every session — do not assume a prior session was authenticated.

**Exit:** All checks pass → LOAD_MEMORY. Any failure → stop immediately (no `/tmp/`, no Jira, no repo edits). Report the missing prerequisite.

### LOAD_MEMORY

**Purpose:** Restore resumable state before execution work.

**Steps:**
1. Read `/tmp/<ticket-key>/state.json` if present.
2. Restore from linked paths (not inline bodies): `context_path` → `context.md`, `design_path` → `design.md`, `plan_path`, `gotchas`, `user_instructions`, `split_decision`, `validation`, `work_kind`.
3. Determine `phase_reached`. Default `LOAD_TICKET_CONTEXT` when no state exists. Legacy `phase_reached: LOAD_MEMORY` → treat as `LOAD_TICKET_CONTEXT`.
4. **Git checkout (resume):** when `branch` is set and `phase_reached` >= `PHASE_3_IMPLEMENT` run `git checkout <branch>` if current branch does not match `state.branch`. Never edit or push on `master` when a ticket branch is recorded.
5. Inspect prior work on the ticket branch: `git diff <base_ref>...HEAD` plus `git diff` for uncommitted edits.
6. If `work_kind` is `sub-work`, skip split execution phases.

**Exit:** Context restored; correct branch checked out when required → EXECUTION.

### EXECUTION

**Purpose:** Run the execution phase named by `phase_reached` and keep persisted state consistent.

**Steps:**
1. Open the matching section under **Execution phases** for `phase_reached`.
2. Do that phase's work (may span multiple chat turns).
3. On every checkpoint (end of turn, user gate, plan revision, validation run, meaningful discovery): dump memory with `--phase` set to the **current execution phase** — even when not advancing yet.
4. Do not re-run earlier execution phases unless `phase_reached` still points there.

**State consistency (mandatory):** every dump during EXECUTION must reflect the latest truth:
- `gotchas` — hygiene on every dump
- `user_instructions` — new steering from this session
- `context.md` / `design.md` — if understanding changed
- `plan_path` — if plan created or revised
- `branch` / `base_ref` / `head_commit` — after branch create or new commits
- `validation` — after compile/test commands
- `split_decision` — when split choice is recorded
- `changes.patch` — `--capture-patch` when the ticket branch has commits or WIP

**Exit:** Phase work complete → final dump advances `phase_reached` to the next execution phase, or session ends awaiting a user gate with state fully current.

## Execution phases

Progressive ticket workflow. Only these names appear in `phase_reached`:

```text
LOAD_TICKET_CONTEXT
  → PHASE_1_CONTEXT_SUMMARY
  → PHASE_2_PLAN_MODE
  → SPLIT_DECISION
  → SPLIT_TICKET_CREATION (optional)
  → PHASE_3_IMPLEMENT
  → OPEN_DRAFT_PR
```

Each execution phase section uses: **Purpose**, **Steps**, **State updates**, **Memory dump**, **Exit**.

### Execution state consistency

State is not write-once at phase boundaries. Throughout EXECUTION, every dump must keep persisted state accurate:

1. Read current state from `/tmp/<ticket-key>/state.json` (or prior turn context).
2. **Gotcha hygiene (every dump):** remove entries superseded by approved plan, implementation, or later discussion; use `--set-gotchas '["…"]'` to replace the full list; use `--gotcha` only to append new constraints.
3. Update fields that changed — pass matching flags (`--context`, `--design`, `--plan-path`, `--instruction`, `--validation`, `--split-decision`, `--ensure-branch`, `--capture-patch`, `--extra-json`, …).
4. Keep `phase_reached` on the current execution phase until that phase is fully complete; advance only on the final dump for that phase.
5. Stale state breaks resume — finishing a turn without dumping, or dumping outdated gotchas/context, poisons the next session's LOAD_MEMORY.

`PHASE_3_IMPLEMENT` often needs multiple dumps at the same `phase_reached`: entry (`--ensure-branch`), checkpoints (`--capture-patch`), validation (`--validation`).

### LOAD_TICKET_CONTEXT

**Purpose:** Load all Jira/product context before summarizing.

**Steps:**
1. Read the ticket description and all comments.
2. If an epic is present: load the technical design and titles of every committed and non-committed ticket in the epic.
3. Call out exactly what is missing if design or ticket titles cannot be found.

**State updates:** `design.md` / `design_path`; gotchas from epic and ticket.

**Memory dump:** `--phase LOAD_TICKET_CONTEXT` with `--design`. `design.md` captures epic goal, technical design summary, related ticket titles, architectural constraints.

**Exit:** Design cached → advance to `PHASE_1_CONTEXT_SUMMARY`.

### PHASE_1_CONTEXT_SUMMARY

**Purpose:** Prove understanding of ticket scope before planning.

**Steps:**
1. Summarize: ticket goal, relevant comments and constraints, epic/project goal (if present), important gotchas, how optional user context changes interpretation.
2. Ask the user to confirm before planning. Do not propose an implementation plan yet.

**State updates:** `context.md` / `context_path` (goal, constraints, in/out of scope, open questions); gotchas; `user_instructions`.

**Memory dump:** `--phase PHASE_1_CONTEXT_SUMMARY` with `--context` and `--gotcha`.

**Exit:** User confirms → advance to `PHASE_2_PLAN_MODE`.

### PHASE_2_PLAN_MODE

**Purpose:** Produce an approved implementation plan with tests.

**Steps:**
1. Switch to Plan Mode before producing the plan.
2. Propose a detailed plan with implementation and tests together — never detach testing from implementation.
3. Include validation commands and expected confidence.
4. Re-dump on plan revision without advancing `phase_reached`.
5. Ask for explicit plan approval before implementation.

Plan format:

```markdown
## Context Summary
<short refreshed summary>

## Implementation Plan
- <change area, files/symbols, intended behavior>

## Test Plan
- <unit/integration/jstest coverage paired with the change>

## Validation
- <compile commands>
- <unit tests>
- <resmoke or smoke tests>

## Risks and Gotchas
- <known constraints or unknowns>
```

**State updates:** `plan_path`; gotchas; `user_instructions`.

**Memory dump:** `--phase PHASE_2_PLAN_MODE` with `--plan-path`. Re-dump on revision.

**Exit:** User approves plan → advance to `SPLIT_DECISION`.

### SPLIT_DECISION

**Purpose:** Decide whether to split work into sub-tickets.

**Steps:**
1. Skip if `work_kind` is `sub-work`.
2. Propose keeping one ticket or splitting into multiple tickets. Every split ticket must include implementation and tests — never split implementation from testing.
3. Ask the user to: keep one ticket, accept the split, or skip split-ticket creation.
4. If the user says "implement" without a split discussion, record `split_decision` as `keep one ticket`.

**State updates:** `split_decision`; gotchas.

**Memory dump:** `--phase SPLIT_DECISION` with `--split-decision`.

**Exit:** Decision recorded → `SPLIT_TICKET_CREATION` (if split accepted) or `PHASE_3_IMPLEMENT`.

### SPLIT_TICKET_CREATION

**Purpose:** Create sub-tickets when the user accepted a split.

**Steps:**
1. Read and follow `/create-jira-ticket`.
2. Create each sub-ticket with concise title and Jira Wiki Markup description.
3. Reuse parent project, assigned team, priority, and epic when possible.
4. Assign every new ticket to the current user and set to the current sprint.
5. Link split tickets to the parent.
6. Mark each new ticket's memory as `work_kind: sub-work`.
7. If any Jira tool cannot set assignee or sprint, stop and report the missing capability.

**State updates:** `extra_context` (created ticket keys); gotchas.

**Memory dump:** `--phase SPLIT_TICKET_CREATION` with `--extra-json` for created keys.

**Exit:** Sub-tickets created → advance to `PHASE_3_IMPLEMENT` on the parent (or hand off sub-tickets).

### PHASE_3_IMPLEMENT

**Purpose:** Implement the approved plan on a ticket branch.

**Steps:**
1. **Before any repo edit:** dump with `--ensure-branch --branch-keywords <kw1>,<kw2>`.
2. Branch naming: `SERVER-<ticket-number>-<keyword1>-<keyword2>-...` (2–4 kebab-case keywords from title or plan; script builds the name from `--branch-keywords`).
3. Confirm `state.json` has `branch` and `base_ref`; `git branch --show-current` matches `state.branch`.
4. Follow the approved plan. If new evidence changes the plan materially, stop and ask for re-approval.
5. Keep implementation and tests in the same work unit. Follow MongoDB repository patterns.
6. Use focused validation (compile, unit-test, resmoke, or smoke-test skills as appropriate).
7. Commit on the ticket branch as you go.

**State updates:** `branch`, `base_ref`, `head_commit`; `validation`; `changes.patch`; gotchas — update on every checkpoint while `phase_reached` stays `PHASE_3_IMPLEMENT`.

**Memory dump:**
- Entry (before first edit): `--phase PHASE_3_IMPLEMENT --ensure-branch --branch-keywords … --capture-patch`
- Checkpoints during work: `--capture-patch`, refreshed gotchas
- After validation: `--validation` with commands and results

**Exit:** Implementation and validation complete → advance to `OPEN_DRAFT_PR`.

### OPEN_DRAFT_PR

**Purpose:** Push the ticket branch and open a draft PR.

**Steps:**
1. **Pre-PR consistency check:** `state.json` reflects latest `phase_reached`, doc paths, `branch`, `gotchas`, `validation`; `context.md` and `design.md` exist; `git branch --show-current` == `state.branch`; `changes.patch` matches branch diff + WIP. Re-dump if stale.
2. Read and follow the pull-request-guidelines skill.
3. Push: `git push -u origin <branch>`.
4. Open a **draft** PR. Use the ticket in the PR title per pull-request-guidelines.
5. Keep the PR description concise; include validation results.
6. Never write `Co-authored-by:` or any agent attribution in PR body, commit message, or description.

If GitHub cannot open a PR (no commits, no remote branch, missing auth), stop and report the exact blocker.

**State updates:** `validation`; PR URL in `extra_json`; final `changes.patch`; gotchas.

**Memory dump:** `--phase OPEN_DRAFT_PR` with PR URL in `--extra-json`.

**Exit:** Draft PR opened.

## Shared reference

### Memory location

All under `/tmp/<ticket-key>/`:

| File | Purpose |
|------|---------|
| `state.json` | Execution phase, gotchas, links (`context_path`, `design_path`, `plan_path`, `branch`, …) |
| `context.md` | Ticket scope: goal, constraints, comments, user steering |
| `design.md` | Epic goal, technical design, related tickets, architectural constraints |
| `changes.patch` | Git diff snapshot (branch commits + WIP with `--capture-patch`) |

`state.json` stores **paths only** for markdown caches — never inline `context` or `design` bodies.

Resumability uses three stores: `state.json`, cached markdown files, and the git ticket branch.

Never implement on `master` without recording the branch in state.

### Script

```bash
SKILL_DIR="/root/.claude/skills/ticket-state-machine"
REPO_ROOT="/root/mongo-quick"   # or the active workspace root

source "${REPO_ROOT}/python3-venv/bin/activate"
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase <EXECUTION_PHASE_NAME> \
  --repo "${REPO_ROOT}"
```

**CLI flags:** `--work-kind`, `--gotcha`, `--set-gotchas`, `--instruction`, `--context`, `--design`, `--write-context-from`, `--write-design-from`, `--plan-path`, `--split-decision`, `--validation`, `--extra-json`, `--capture-patch`, `--branch-keywords`, `--ensure-branch`, `--base-ref`, `--branch`.

| Flag | Effect |
|------|--------|
| `--context "..."` | Writes `context.md`, sets `context_path` |
| `--design "..."` | Writes `design.md`, sets `design_path` |
| `--plan-path <file>` | Links external plan file |
| `--set-gotchas '["a","b"]'` | Replaces full gotchas list (JSON array of strings) |
| `--capture-patch` | Refreshes `changes.patch` from branch diff + WIP |

### `state.json` fields

| Field | When to set |
|-------|-------------|
| `phase_reached` | Execution phase name only; current phase until complete, then next |
| `work_kind` | `original` or `sub-work` |
| `split_phase_allowed` | Derived from `work_kind` |
| `branch` | `PHASE_3_IMPLEMENT` onward |
| `base_ref` | Branch creation — usually `master` or upstream base |
| `head_commit` | Each dump on the ticket branch |
| `gotchas` | Review on every dump |
| `user_instructions` | User steering guidance |
| `extra_context` | Arbitrary structured context |
| `context_path` | Auto-set by `--context` |
| `design_path` | Auto-set by `--design` |
| `plan_path` | Phase 2 and on revision |
| `split_decision` | Split decision phase |
| `validation` | After compile/test validation |
| `updated_at` | Auto-set by script |

### Final response

Always tell the user:
- current `phase_reached`
- memory path (`/tmp/<ticket-key>/`)
- current `branch` from `state.json` (if set)
- whether `state.json` was updated this turn
- PR link, if opened
- validation results
- any skipped optional phases and why

## Examples

One example per session state and execution phase. Session states do not dump.

### PRECHECK (session)

```text
# Every invocation — before LOAD_MEMORY
1. Confirm ticket key SERVER-XXXXX
2. Read devprod MCP tool schema (e.g. jira_get_issue)
3. Harmless auth probe (e.g. jira_get_fields)
# No state_memory.py dump
```

### LOAD_MEMORY (session)

```bash
# Every invocation — read state, checkout branch if resuming implementation on master
cat /tmp/SERVER-XXXXX/state.json
# phase_reached: PHASE_3_IMPLEMENT, branch: SERVER-XXXXX-strict-chunks
git branch --show-current   # master
git checkout SERVER-XXXXX-strict-chunks
git diff master...HEAD
# No state_memory.py dump
```

### EXECUTION (session)

```text
# Dispatch to the execution phase section matching phase_reached from state.json
# Dump memory per that phase's Memory dump rules — keep gotchas et al. current
```

### LOAD_TICKET_CONTEXT

```bash
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase LOAD_TICKET_CONTEXT \
  --design "$(cat <<'EOF'
# Epic SPM-4061
Authoritative shard catalog ...
EOF
)" \
  --repo "${REPO_ROOT}"
```

### PHASE_1_CONTEXT_SUMMARY

```bash
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase PHASE_1_CONTEXT_SUMMARY \
  --context "$(cat <<'EOF'
# SERVER-XXXXX scope
Goal: strict per-chunk validation when CSR is authoritative.
EOF
)" \
  --gotcha "Skip checks when critical section active" \
  --repo "${REPO_ROOT}"
```

### PHASE_2_PLAN_MODE

```bash
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase PHASE_2_PLAN_MODE \
  --plan-path /root/.cursor/plans/server-xxxxx.plan.md \
  --set-gotchas '["Skip checks when critical section active","Gate on csrIsAuthoritative"]' \
  --instruction "User confirmed: skip not serialize" \
  --repo "${REPO_ROOT}"
```

### SPLIT_DECISION

```bash
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase SPLIT_DECISION \
  --split-decision "keep one ticket" \
  --repo "${REPO_ROOT}"
```

### SPLIT_TICKET_CREATION

```bash
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase SPLIT_TICKET_CREATION \
  --extra-json '{"created_tickets":["SERVER-YYYYY","SERVER-ZZZZZ"]}' \
  --repo "${REPO_ROOT}"
```

### PHASE_3_IMPLEMENT

```bash
# Entry — before first repo edit
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase PHASE_3_IMPLEMENT \
  --ensure-branch \
  --branch-keywords strict,chunks \
  --capture-patch \
  --repo "${REPO_ROOT}"

# Checkpoint during implementation (same phase_reached)
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase PHASE_3_IMPLEMENT \
  --set-gotchas '["Skip checks when critical section active"]' \
  --capture-patch \
  --repo "${REPO_ROOT}"

# After validation
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase PHASE_3_IMPLEMENT \
  --validation "bazel run +foo_test: PASS; resmoke core foo.js: PASS" \
  --capture-patch \
  --repo "${REPO_ROOT}"
```

### OPEN_DRAFT_PR

```bash
python "${SKILL_DIR}/scripts/state_memory.py" dump SERVER-XXXXX \
  --phase OPEN_DRAFT_PR \
  --extra-json '{"pr_url":"https://github.com/10gen/mongo/pull/12345"}' \
  --capture-patch \
  --repo "${REPO_ROOT}"
```
