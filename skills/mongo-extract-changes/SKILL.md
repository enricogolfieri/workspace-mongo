---
name: mongo-extract-changes
description: Extracts and summarizes only the author's changes from git history and diffs. Use when you need an accurate commit/file scope for review, test selection, or change reporting.
---

# Mongo Extract Changes

Use this workflow to identify what changed in the author's branch.

This skill only extracts and summarizes author changes. It does not run tests.

## Inputs To Confirm

Before running commands, confirm:

1. Base ref for comparison (default `origin/master` if user did not specify).
2. Whether output should be high-level only or include file-level details.

If base ref is ambiguous (for example `origin/main` vs `origin/master`), ask the user.

## Extraction Workflow

Copy this checklist and keep it current while working:

```text
Author Change Extraction Progress
- [ ] Confirm base ref
- [ ] Collect branch commit range
- [ ] Collect changed file list and status
- [ ] Group changes by area
- [ ] Produce concise change summary
```

### 1) Commit range

Use:

```bash
git log --oneline <base_ref>..HEAD
```

### 2) Changed files and status

Use:

```bash
git diff --name-status <base_ref>...HEAD
git diff --stat <base_ref>...HEAD
```

### 3) Focus by path (optional)

Narrow to specific areas when needed:

```bash
git diff --name-only <base_ref>...HEAD -- <path-prefix>
```

### 4) Group by area

Group changed files into clear buckets, for example:

- server code
- tests
- build/config/scripts
- docs/metadata

## Output Format

Return:

- Base ref used
- Commits in range (short list)
- Changed files grouped by area

Keep output concise and action-oriented.
