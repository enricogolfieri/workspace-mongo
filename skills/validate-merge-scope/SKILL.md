---
name: validate-merge-scope
description: >-
  Validates a merge by analyzing files changed by both sides. Detects deleted
  code re-introduced, comments altered, changes reverted, and semantic
  dependencies between my code and theirs. Use when the user asks to validate
  a merge, check merge scope, or review what a merge did to their changes.
---

# Validate Merge Scope

Analyze the intersection of "my changes" and "their merge" to catch regressions,
lost work, and unreviewed interactions.

## Terminology

| Ref   | Meaning |
|-------|---------|
| BASE  | Common ancestor of both sides |
| PRE   | My branch tip just before the merge (`MERGE^1`) |
| OTHER | The branch that was merged in (`MERGE^2`) |
| MERGE | The merge commit itself |
| Merge scope files | Files changed in both `BASE..PRE` **and** `PRE..MERGE` |

## Workflow

### Phase 1 — Mechanical scan

Run the analysis script:

```bash
python3 ~/.cursor/skills/validate-merge-scope/scripts/analyze_merge.py --verbose
```

The script auto-detects the merge commit and reports:

| Category | What it means |
|----------|---------------|
| `DELETED_CODE_REINTRODUCED` | Lines I intentionally removed that the merge brought back |
| `MY_COMMENTS_MODIFIED_OR_REMOVED` | Comments I wrote that the merge altered or dropped |
| `MY_CODE_REVERTED_TO_BASE` | Code I changed that the merge reset to the pre-change version |
| `MY_CODE_MODIFIED_BY_MERGE` | Code I added/changed that the merge altered further |
| `INTERACTION_ZONE` | Both sides introduced new code in the same file — needs manual review |
| `INTENT_CONFLICT` | Merge introduced code in a file I didn't touch, containing identifiers I was deleting — the merge may be working against my changes |

Review each flagged item. For every finding:

1. Read the file at the flagged lines.
2. Compare the PRE version (`git show PRE:<file>`) with the merged version.
3. Determine if the change is intentional, accidental, or a conflict resolution error.
4. Report the verdict to the user.

### Phase 2 — Semantic dependency analysis

For every file marked `INTERACTION_ZONE`, plus any file where the user asks
for deeper review, perform the following manual checks by reading the relevant
diffs and code:

#### Check 1: Does my new code depend on their changes?

Look for code I introduced (in `BASE..PRE`) that references symbols, types,
functions, or APIs that only exist because of their changes (`BASE..OTHER`).

How to check:
```bash
# My additions
git diff BASE..PRE -- <file>
# Their additions
git diff BASE..OTHER -- <file>
```

Grep my added lines for identifiers that appear only in their diff.

#### Check 2: Does their new code depend on my changes?

Reverse of Check 1. Look for code they introduced that references symbols
I added or modified.

#### Check 3: Does my new code require adaptation to their changes?

Even without direct symbol references, structural changes (renamed parameters,
changed signatures, moved code blocks) on their side may require my code to
be updated. Look for:

- Function signatures I call that they changed
- Struct/class fields I use that they renamed or retyped
- Header includes or imports that shifted

#### Check 4: Do their changes require adaptation to mine?

Reverse of Check 3.

### Phase 3 — Report

Produce a summary grouped by severity:

```
## Merge Scope Validation Report

### Critical (likely bugs)
- [file:line] Description of the issue

### Warning (needs human review)
- [file:line] Description of the interaction

### Info (confirmed OK)
- [file] No issues found / interaction reviewed and correct
```

## Shell helpers

Source the helper script before using shell functions:

```bash
source ~/.agents/validate-merge-scope/scripts/merge_scope.sh
```

Available after sourcing:

- `merge_scope_files` — list files changed by both sides
- `git-diff-merge-scope` — combined diff for merge scope files
