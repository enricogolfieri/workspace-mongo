---
name: implement-plan
description: >-
  Implement code changes from an agreed plan with minimal, clean edits.
  Use when executing a plan, applying approved changes, or when the user
  says "implement", "apply the plan", "make the changes", or "do it".
---

# Implement Plan

## Core rules

1. **Change only what the plan says.** Do not touch unrelated code.
2. **Preserve existing comments, logging, and formatting.** Never delete a comment unless the plan explicitly calls for it. Never add or remove log statements unless planned.
3. **No narration comments.** Do not add comments that explain *why you are making this change* or reference the ticket/bug. Comments in code should describe the code's intent, not the change's history.
4. **Keep the style of the surrounding code.** Match indentation, brace style, naming, comment style. New code should look like it was always there.
5. **Minimal diff.** Move code only when structurally required. Don't reorder includes, reformat blocks, or rename variables beyond what the plan requires.

## When you hit a wall

If an implementation step fails (private API, missing include, wrong signature, access control), **stop immediately**. Do not:

- Add wrapper classes, friend declarations, or shims that weren't in the plan.
- Substitute a different mechanism without approval.
- Pile workarounds on top of workarounds.

Instead, tell the user what went wrong and why. Ask whether to revise the plan.

## Workflow

1. Read each file you will edit before editing it.
2. Make one logical change at a time. Verify it compiles before moving on.
3. After all edits, run `bazel run format`.
4. Run the relevant unit tests.
5. Mark todos complete as you go.
