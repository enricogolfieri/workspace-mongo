---
name: mongo-knowledge
description: MongoDB Knowledge Layer — a persistent, curated knowledge base about MongoDB internals. ALWAYS load this skill before answering ANY question about MongoDB internals, modifying MongoDB source code, planning a feature, reviewing a patch, debugging engine behavior, or explaining how any part of the codebase works. Also triggers on: "update mongo knowledge", "add to knowledge layer", "save this about X", "remember this about X", "teach you about X". Do NOT rely on training data about MongoDB internals — consult this knowledge base first.
---

# MongoDB Knowledge Layer

Two modes. Detect which applies and follow it exactly.

## Mode Detection

**MODE 1 — Read** when:
- Answering any question about MongoDB internals
- Writing, reviewing, or planning code in the MongoDB codebase
- Explaining how something works, debugging engine behavior

**MODE 2 — Update** when the user says things like:
- "update the knowledge layer with..."
- "add this to mongo knowledge..."
- "save/remember this about [topic]..."
- "teach you about [topic]..."

---

## MODE 1 — Read

Do not answer yet. First:

1. Read `references/index.md` (relative to this skill's directory: `~/.antigen/bundles/enricogolfieri/workspace-mongo-main/skills/mongo-knowledge/references/index.md`)
2. Find the row(s) matching the topic
3. Read the file(s) listed for that row
4. Then answer — grounded in what you read, not training data

**If `index.md` has no match:** tell the user:
> "No entry for this topic in the knowledge base yet. You can add one with `/mongo-knowledge` in update mode."

Then answer with explicit uncertainty.

---

## MODE 2 — Update

You are adding or updating knowledge. Follow these steps exactly.

### Step 1 — Gather inputs

If not already provided, ask for:
- **Topic**: what is this about?
- **Content**: the knowledge to store (paste, notes, raw text — anything)

### Step 2 — Read the index

Read `references/index.md` to see what already exists.

### Step 3 — New file or append?

- If a closely related entry exists → read that file, append the new content as a new `##` section. Do not duplicate what's already there.
- If the topic is new → choose a filename: `references/<topic-name>.md`. If the topic belongs to a broader domain that will grow (e.g. multiple WiredTiger subtopics), use `references/<domain>/<topic>.md`.

### Step 4 — Write the file

Use this template for new files:

```markdown
# <Topic Name>

## Overview
<!-- What is this? Why does it matter? -->

## Key source paths
<!-- src/mongo/... -->

## Core concepts
<!-- Bullet list -->

## Invariants
<!-- What must always be true -->

## Gotchas
<!-- What goes wrong without this knowledge -->

## Related topics
<!-- Other files in this knowledge base to read alongside this one -->
```

All files live under `~/.antigen/bundles/enricogolfieri/workspace-mongo-main/skills/mongo-knowledge/references/`.

### Step 5 — Update index.md

Add or update a row in `references/index.md` for the entry. See that file for format.

### Step 6 — Confirm

Tell the user:
- What file was created or updated (full path)
- What row was added/updated in the index
- Whether you reused an existing file or created new, and why

---

## Guardrails

- Never answer MongoDB internals questions from training data alone — always check the index first.
- Never invent file paths or source locations that you have not read or verified.
- Keep index rows concise (one line, under 150 chars each).
- Do not duplicate knowledge — search for related topics before creating a new file.
- If the knowledge base has no entry for a topic, say so explicitly; do not silently fall back to training data without acknowledging it.
