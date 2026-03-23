---
name: full-ticket-delivery
description: Delivers a ticket end-to-end by gathering requirements from Glean (description, comments, project context, technical design, scope), proposing a production and test plan, waiting for approval, then implementing and validating with compile and test workflows. Use when the user asks to implement a Jira/ticket fully from issue context.
---

# Full Ticket Delivery

Use this skill to execute a ticket from discovery to validated code changes.

## When To Use

Use this skill when the user asks to:
- implement a ticket end-to-end
- start from Jira or issue context
- account for ticket comments and description
- include project/epic goals and technical design
- propose a plan before coding, then execute

## Hard Requirements

1. Explore the ticket with Glean search first.
2. Account for all ticket comments.
3. Account for the ticket description.
4. If the ticket is part of a project, account for project description and goal.
5. If it is part of a project, use Glean to find technical design and defined scope.
6. Propose a plan with two explicit sections:
   - production code changes
   - test code changes
7. Do not implement until the user accepts the plan.
8. After implementation, compile and test. Mention and use:
   - `mongo-unit-test-loop` skill for Bazel unit-test fix loops
   - `resmoke` skill for integration/correctness validation

## Workflow

Copy this checklist and keep it current:

```text
Full Ticket Delivery Progress
- [ ] Identify ticket and canonical source
- [ ] Gather description and acceptance criteria
- [ ] Gather and summarize all comments
- [ ] Gather project/epic context (if applicable)
- [ ] Gather technical design and scope docs (if applicable)
- [ ] Propose implementation plan (prod + tests)
- [ ] Receive user approval
- [ ] Implement production code changes
- [ ] Implement/adjust test coverage
- [ ] Compile and run validation tests
- [ ] Report outcomes, risks, and follow-ups
```

### 1) Discover ticket context in Glean

Use Glean tools in this order:
1. `search` for the ticket key/title and canonical issue document.
2. `read_document` for full issue content.
3. Additional `search` + `read_document` for linked docs/comments/design references.
4. Use `chat` only for synthesis after collecting source documents.

Capture:
- ticket ID and title
- full description
- acceptance criteria / definition of done
- all available comments (author + intent)
- explicit non-goals and constraints

If comments are split across multiple documents, aggregate them into a single normalized list.

### 2) Enrich with project context (conditional)

If ticket references an epic/project/program:
- extract project name/ID
- gather project description and business/engineering goal
- gather technical design docs and formal scope statements
- map scope boundaries to the current ticket

If any project context is missing, call it out before planning.

### 3) Build the plan (must happen before coding)

Produce a plan with these exact sections:

```markdown
## Ticket Understanding
- <description and key constraints>
- <comment-derived clarifications>
- <project/design scope boundaries>

## Plan: Production Code
- <change 1 with file areas and rationale>
- <change 2 with file areas and rationale>

## Plan: Test Code
- <unit-test updates/new tests>
- <integration/resmoke coverage updates>

## Validation Strategy
- <what will be compiled>
- <what unit tests will run>
- <what resmoke suite/test(s) will run and why>
```

The user must explicitly approve this plan before implementation.

### 4) Implement after approval

Execution guidance:
- Follow repository conventions and existing patterns first.
- Keep changes scoped to ticket goals and approved plan.
- If new information invalidates the plan, pause and request re-approval.
- Keep production and test changes aligned so behavior changes are verified.

### 5) Compile and test

After code changes:
1. Compile relevant targets.
2. Run focused unit tests first.
3. Run integration/correctness tests as appropriate.

Required skills to apply:
- Use `mongo-unit-test-loop` when running/fixing Bazel unit tests until green.
- Use `resmoke` for integration/correctness suites and jstests selection.

Recommended command patterns:

```bash
bazel build <target>
bazel run <unit_test_target>
source python3-venv/bin/activate
python3 buildscripts/resmoke.py run --suites=<suite> <optional_test_path>
```

### 6) Final report format

Use this response structure:

```markdown
## Ticket Context Used
- Ticket: <id/title/source>
- Description: <key points>
- Comments accounted: <count and key decisions>
- Project/design context: <present or not, with sources>

## Implemented Changes
- Production code: <what changed and why>
- Test code: <what changed and why>

## Validation
- Compile: <pass/fail + target>
- Unit tests: <pass/fail + target>
- Resmoke: <pass/fail + suite/tests>

## Risks / Follow-ups
- <remaining risk, edge cases, or deferred work>
```

## Quality Gate Before Completion

- All ticket comments were considered and reflected in plan or rationale.
- Description and acceptance criteria are traceable to code/test updates.
- Project goal and design scope were incorporated when applicable.
- The approved plan and implementation are consistent.
- Compile and test outcomes are explicitly reported.
