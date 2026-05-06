---
name: mongo-pr-review
description: Performs deep pull request reviews by quickly explaining code changes and identifying potential bugs grouped by severity (critical, non-critical, nit). Use when reviewing pull requests, code diffs, or when the user asks for structured review comments with Cursor/VSCode-clickable code references and reviewer-facing reasoning.
---

# Mongo PR Review

## When To Use

Use this skill when the user asks for:
- pull request review
- deep code review of a diff
- bug-risk analysis before merge
- feedback grouped by severity

## Scope and Filtering Rules

- **Repository**: Only consider PRs in the `10gen/mongo` GitHub repository.
- **Review Assignment**: Only process PRs where the user has been explicitly requested as a reviewer OR auto-assigned via a team assignment.
- **PR Status**: Only consider official, non-draft PRs that are open and ready for review.

## Review Workflow

### Step 1: Scope the Diff

1. **Scope the diff to only the author's changes** by using the `mongo-extract-changes` skill first.
   - Do not review unrelated files pulled in by merge commits.
   - Review only files confirmed by `mongo-extract-changes`.
2. Determine whether this is a **first-round review** or a **subsequent review round** by checking if the user already has submitted review comments on this PR.

### Step 2: Gather Context

1. **PR Details**: Title, description, author, base branch, target branch, linked commits, files changed, additions/deletions.
2. **Jira Ticket**: Extract the Jira ticket ID from the PR title or description (commonly formatted as `SERVER-XXXXX`). Retrieve the full ticket including summary, description, and acceptance criteria.
3. **Project/Epic Context**: If the Jira ticket is part of a project or epic, retrieve scope definition, design documents, and related tickets for broader context.
4. **Previous Review History** (for subsequent rounds): Retrieve prior review comments and the author's responses/resolutions.

### Step 3: Perform Analysis

#### First-Round Review

Conduct a thorough analysis covering:
- **Summary of Changes**: High-level overview cross-referenced with Jira ticket goals.
- **Correctness & Bugs**: Logic errors, race conditions, edge cases, null pointer risks, off-by-one errors, invariant violations.
- **Security Issues**: Vulnerabilities, injection risks, improper privilege handling, data exposure.
- **Performance Concerns**: Expensive operations in hot paths, missing indexes, inefficient algorithms, lock contention.
- **Code Quality**: Readability, naming conventions, complexity, MongoDB C++ coding standards adherence.
- **Testing**: Test coverage adequacy, missing edge case tests, test correctness.
- **Design Alignment**: Cross-check implementation against Jira acceptance criteria and linked design documents.
- **Improvements & Suggestions**: Non-blocking suggestions for cleaner solutions or future-proofing.
- **Verdict**: `APPROVE`, `REQUEST CHANGES`, or `COMMENT`.

#### Subsequent Review Round

Focus exclusively on what changed since the last review:
- **Delta Summary**: What changed in the new commits.
- **Feedback Resolution**: For each prior comment, assess whether resolved, partially addressed, or unresolved.
- **New Issues**: Flag any new bugs or concerns introduced.
- **Updated Verdict**: Based on resolution of prior feedback and any new findings.

### Step 4: Classify Findings

- `critical`: must fix before merge; high production risk
- `non-critical`: important issue, acceptable only as temporary risk
- `nit`: style/readability/preference

## Hard Requirements

- Every finding must include a code reference.
- Prefer Cursor/VSCode code citation blocks over GitHub or markdown links.
- For each finding, include a separate code citation block using the format `startLine:endLine:path/to/file.ext` followed by at least 1 line of real code from that file. This is the most reliable way to make code clickable in Cursor.
- Do not prefer GitHub blob links unless the user explicitly asks for web links.
- If a code citation block is not possible, include backticked path and line range.
- Every finding must include both:
  - **Review comment**: concise message to post on the PR.
  - **Explanation**: reviewer-facing reasoning, impact, and severity logic.
- Do not report a finding without code evidence.
- Show `critical` findings first and make them obvious.

## Required Output Template

Use this structure exactly:

````markdown
## Change Summary
- <quick explanation of what changed>
- <quick explanation of what changed>

## Jira Context
{Brief summary of the ticket goal and acceptance criteria}

## Critical (must warn immediately)
- **Finding:** <title>
  - **Code:** include a Cursor/VSCode citation block immediately below this bullet, for example:

```120:146:path/to/file.ext
// relevant code line(s) here
```
  - **Review comment:** <what the author should change now>
  - **Explanation:** <why this is risky, expected failure mode, why critical>

## Non-Critical (acceptable for now, but should be tracked)
- **Finding:** <title>
  - **Code:** include a Cursor/VSCode citation block immediately below this bullet
  - **Review comment:** <suggested fix>
  - **Explanation:** <trade-off, impact, and urgency>

## Nit (style or preference)
- **Finding:** <title>
  - **Code:** include a Cursor/VSCode citation block immediately below this bullet
  - **Review comment:** <small improvement suggestion>

## Verdict
**{APPROVE | REQUEST CHANGES | COMMENT}**
{One-sentence rationale}
````

For **subsequent review rounds**, replace the analysis sections with:

```markdown
## Delta Since Last Review
{Summary of new commits/changes}

## Prior Feedback Resolution
| Comment | Status | Notes |
|---------|--------|-------|
| {comment summary} | ✅ Resolved / ⚠️ Partial / ❌ Unresolved | {notes} |

## New Issues Found
{If any new bugs or concerns exist, list them with the same finding structure and Cursor/VSCode citation blocks used above; otherwise write "None"}

## Updated Verdict
**{APPROVE | REQUEST CHANGES | COMMENT}**
{Rationale}
```

Fallback when Cursor/VSCode citation blocks are not possible:

```markdown
- **Code:** `path/to/file.ext:120-146`
```

## Empty Section Rules

- Always include all three severity sections.
- If a section has no findings, write:

```markdown
- None.
```

## Quality Gate Before Sending Review

- Every finding maps to specific changed code.
- Severity is justified by concrete user or system impact.
- Review comments are actionable and concise.
- Explanations are understandable without hidden context.
- No duplicates across severity sections.
- Be constructive: frame issues as actionable feedback, not criticism.

## Additional Resource

- For a complete example response, see [examples.md](examples.md).
