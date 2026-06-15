---
name: extract-author-changes
description: Loads context for the current branch's PR-scope changes (merge-base to HEAD), including uncommitted edits, then confirms without summarizing. Use when starting a session and the user wants branch/PR context for follow-up work. Optional author filter only when they ask for "my commits only."
---

# Extract Branch / PR Changes

Load **what the PR shows** — the diff from the merge-base of the PR base branch to `HEAD` — not a two-dot range filtered by `git config user.email`.

This skill loads change context into the session. It does not run tests and does not summarize unless the user explicitly asks.

## Defaults

Unless the user says otherwise:

1. **Scope:** PR-style three-dot range (`<base>...HEAD`), same as GitHub’s “Files changed”
2. **Base ref resolution** (first match wins):
   - User-provided base (e.g. `origin/master`, parent stack branch)
   - Open PR for current branch: `gh pr view --json baseRefName` → `origin/<baseRefName>`
   - Upstream tracking branch: merge-base of `@{upstream}` and `HEAD`
   - `origin/master`
3. **Author filter:** **off** by default. Enable only when the user asks for their commits only (`--author`, “my changes”, “what I authored”).
4. **Output:** exactly `Context loaded.` (no summary, file list, or explanation)

Ask a clarifying question only if base ref cannot be resolved (no upstream, no PR, fetch failed) and the user did not name a base.

## Extraction Workflow

```text
Branch / PR Change Extraction Progress
- [ ] Identify branch, resolved PR base ref, merge-base
- [ ] Collect commits and diff in <base>...HEAD (three-dot)
- [ ] Optional: filter commits by author if user requested
- [ ] Collect uncommitted local edits separately
- [ ] Sanity-check scope (HEAD included, not empty/wrong)
- [ ] Confirm context loaded
```

### 1) Identify scope

```bash
git branch --show-current
git fetch origin --quiet  # best-effort; continue if it fails

# Resolve base (examples — use the first that applies)
# gh pr view --json baseRefName,headRefName -q '.baseRefName' 2>/dev/null
# git rev-parse --abbrev-ref @{upstream} 2>/dev/null
# Default: origin/master

base_ref="origin/master"   # replace with resolved base
merge_base="$(git merge-base "$base_ref" HEAD)"
```

Record internally: `branch`, `base_ref`, `merge_base`, `three_dot_range="${base_ref}...HEAD"`.

**Three-dot vs two-dot**

| Syntax | Meaning | Use for PR scope? |
|--------|---------|-------------------|
| `base...HEAD` | Changes since **merge-base**(base, HEAD) | **Yes** — matches GitHub PR |
| `base..HEAD` | All commits reachable from HEAD but not base | No — includes unrelated history on long branches |

### 2) PR-scope commits and diff (primary)

Always collect the full PR-scope patch first:

```bash
git log --date=short --format='%h %ad %an <%ae> %s' "${base_ref}...HEAD"
git diff --stat "${base_ref}...HEAD"
git diff --name-status "${base_ref}...HEAD"
```

If a PR exists for this branch, prefer matching GitHub exactly:

```bash
gh pr diff          # patch
gh pr view --json commits,files,baseRefName,headRefName
```

For file-level history, walk PR-scope commits (not `git show` on an author-filtered subset unless step 2b ran):

```bash
git log --format='%H' "${base_ref}...HEAD" |
while read -r commit; do
  git show --stat --name-status --format='commit %h %s' "$commit"
done
```

### 2b) Optional — author filter only on request

When the user wants **only their commits** within the PR range:

```bash
author_pattern="$(git config user.email)"
# if empty: author_pattern="$(git config user.name)"

git log --date=short --format='%h %ad %an <%ae> %s' \
  "${base_ref}...HEAD" --author="$author_pattern"
```

**Sanity checks** (run when author filter is used):

```bash
# HEAD should appear in PR-scope log
git log -1 --format='%h %ae %s' HEAD

# If author log is empty OR does not include recent HEAD work, warn internally:
# author filter missed branch tip — PR-scope diff (step 2) is still authoritative
```

Do **not** replace PR-scope diff with `origin/master..HEAD --author=...`; that misses other authors’ work on the same PR and picks up wrong commits when `git config` ≠ branch author.

### 3) Local working tree (always separate)

```bash
git status --short
git diff --name-status
git diff --stat
git diff --cached --name-status
git diff --cached --stat
```

Keep mentally separate: **`PR scope`** (`<base>...HEAD` plus optional author subset) vs **`Working tree`** (uncommitted).

### 4) Focus by path (optional)

```bash
git log --format='%H' "${base_ref}...HEAD" -- <path-prefix>
git diff --name-status "${base_ref}...HEAD" -- <path-prefix>
git diff --name-status -- <path-prefix>              # unstaged
git diff --cached --name-status -- <path-prefix>     # staged
```

### 5) Stacked PRs / Graphite

When the branch is one PR in a stack, base is usually the **parent branch**, not `master`:

```bash
# User may say: "base is origin/parent-branch-name"
git diff "origin/<parent-branch>...HEAD"
git log --oneline "origin/<parent-branch>...HEAD"
```

Use `gh pr view --json baseRefName` when unsure.

## Final response

After collecting context, do not summarize, list files, or explain what changed.

Use exactly:

```
Context loaded.
```

If the user explicitly asks for a summary afterward, summarize **PR-scope** changes (`<base>...HEAD`). If they also requested an author filter, note that the summary is limited to those commits within the PR range.

## Quick reference

```bash
# Default PR scope vs master
git log --oneline origin/master...HEAD
git diff origin/master...HEAD

# Match open PR
gh pr diff

# Stacked PR
git diff origin/<parent>...HEAD
```
