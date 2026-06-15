---
name: create-jira-ticket
description: Create a Jira ticket following team conventions, with duplicate detection and preview
user-invocable: true
---

# Create a Jira Ticket

Follow these steps in order when creating a Jira ticket.

## Tooling

Jira is accessed through the devprod MCP gateway. The relevant tools are:
`jira_get_issue`, `jira_search_issues`, `jira_create_issue`, `jira_update_issue`,
`jira_link_issues`, `jira_list_link_types`, `jira_set_epic`, `jira_get_fields`,
`jira_get_issue_transitions`, `jira_transition_issue`, `jira_add_comment`.

**Always read a tool's JSON schema (descriptor) before calling it the first time** — parameter
names differ from intuition (e.g. `jira_create_issue` uses `project`, not `project_key`; custom
fields go in `custom_fields`, not `additional_fields`). There is no `jira_get_field_options` tool —
use `jira_get_fields` to discover field names/values.

## 1. Gather information

Infer as much as possible from the conversation context. Only ask the user about fields that cannot be reasonably inferred.

- **Project**: Use **SERVER** for bugs or improvements related to the MongoDB server main repository. For other projects, ask the user.
- **Issue type**: Bug, Improvement, Task, etc. (e.g., "this is broken" implies Bug)
- **Summary**: concise, to the point. **When splitting an existing ticket into multiple tickets, do NOT put "split" (or "split from X") in the summary** — name each ticket by the work it covers, as if it were a standalone ticket.
- **Description**: concise, to the point. Include only what's necessary. Do not add a "Split from ..." preamble; describe the work directly.
- **Assigned Team**: required field, custom field display name **`Assigned Teams`** (plural). Ask the user if not clear from context. When splitting an existing ticket, reuse the parent's `Assigned Teams` value.
- **Assignee**: optional. Only set if the user explicitly asks. Use the full email address (e.g., `user@mongodb.com`), not the short username.

## Description formatting (Jira Wiki Markup)

The description field is **Jira Wiki Markup**, NOT Markdown. The gateway does **not** convert
Markdown — if you write Markdown links `[text](url)` they render broken (literal brackets). Use
wiki markup:

- **Links:** `[link text|https://url]` (pipe-separated). Example:
  `[setMultikeyMetadata applier|https://github.com/mongodb/mongo/blob/<sha>/src/mongo/db/repl/oplog.cpp#L1427]`
- **Inline code:** `{{identifier}}`
- **Code block:** `{code:cpp}...{code}`
- **Bold:** `*bold*` — **Italic:** `_italic_`
- **Headings:** `h3. Heading`
- **Bulleted list:** lines starting with `* ` — **Numbered list:** lines starting with `# `
- **Table:** `||header||header||` then `|cell|cell|`

**Every** mention of a function, class, method, or code construct in the description **must** be an inline GitHub link (using the `[text|url]` wiki syntax above). Do not mention code identifiers as plain text — always look up the file and line number and link them. This is mandatory, not optional.

GitHub link rules:
- Use the **github.com/mongodb/mongo** public repository for all links.
- **Never link to the `master` branch by name** — code on master changes over time. Instead, link to a specific commit SHA.
- **Determine the branch name** from local git metadata (branch names are shared between the private `10gen/mongo` and public `mongodb/mongo` repos):
  1. First, try `git rev-parse --abbrev-ref @{upstream}` — if set and it matches a mainline branch pattern (`origin/master` or `origin/v*`), use it. Otherwise fall through to step 2.
  2. Otherwise, find the closest remote branch: `git branch -r --sort=-committerdate --list 'origin/master' 'origin/v[0-9]*' | sed 's/^[ ]*//' | while read branch; do if git merge-base --is-ancestor "$branch" HEAD 2>/dev/null; then echo "$branch"; break; fi; done`. This only checks `master` and release branches, most recent first.
  3. If neither step 1 nor step 2 produces a result, ask the user which branch to use.
  4. Strip the `origin/` prefix and any `-staging` suffix to get the public branch name (e.g., `origin/v8.0-staging` → `v8.0`, `origin/master` → `master`).
- **Get the commit SHA from the public repo** (not from local refs, which track the private repo): `git ls-remote https://github.com/mongodb/mongo.git refs/heads/<branch> | cut -f1`.
- **Line numbers must come from the public repo, not the local working copy.** The local branch may have modifications that shift line numbers, and the public repo SHA is not fetched locally. Use `curl` to fetch file contents from the public repo: `curl -sL https://raw.githubusercontent.com/mongodb/mongo/<commit-sha>/<path/to/file> | grep -n '<pattern>'`.
- Link target format: `https://github.com/mongodb/mongo/blob/<commit-sha>/path/to/file.cpp#L42`
- Make links inline in the description text — link the relevant words/phrases directly to the code rather than appending a bare URL at the end. For example: `the [preconditions check|https://github.com/mongodb/mongo/blob/<sha>/path/to/file.cpp#L125] does not include...`
- If the ticket is not about specific code at all, skip the links. But if any code entity is mentioned by name, it must be linked.

## 2. Check for duplicates

Before creating, search Jira for similar existing tickets:

- Use `jira_search_issues` with a JQL query targeting the same project and relevant keywords.
- Search broadly: use multiple key terms, not just the exact summary. Use `text ~ "keyword1 keyword2"` to match across summary, description, and comments.
- Include all statuses — a closed or resolved ticket can still be a duplicate.
- Limit results to 10 to keep output readable (`max_results`).
- Example: `project = SERVER AND text ~ "keyword1 keyword2" ORDER BY created DESC`
- If potential duplicates are found, show them to the user (key, summary, status) and ask whether to proceed or not.

## 3. Validate and preview

Validate the team value: call `jira_get_fields` to find the `Assigned Teams` field and confirm the
desired value is a valid option. If it doesn't match any option, show the user the closest matches
and ask them to pick one. (When splitting/cloning, the parent's value is already known-valid.)

Then display a preview:

```
Project:        SERVER
Type:           Bug
Summary:        <title>
Assigned Team:  <team>
Epic:           <epic key or "None">
Assignee:       <email or "Unassigned">
Description:
<description with GitHub links>
```

Wait for explicit user confirmation before proceeding.

## 4. Create the ticket

Use `jira_create_issue` with:
- `project`: the selected project key (e.g. `SERVER`)
- `summary`: the title
- `issue_type`: the issue type (defaults to `Task`)
- `priority`: e.g. `Major - P3` (match the parent when splitting)
- `description`: in **Jira Wiki Markup** (see "Description formatting" above — links are `[text|url]`, not Markdown)
- `custom_fields`: `{"Assigned Teams": "<assigned team>"}` — pass the display name as the key and the value as a plain string; the tool auto-wraps option fields. (Do not use `additional_fields` or `[{"value": ...}]` shapes.)
- `assignee`: if requested (see above)

`jira_create_issue` returns the new issue `key`. After creation, show the ticket key and a direct link: `https://jira.mongodb.org/browse/<TICKET-KEY>`.

Then apply post-creation steps as needed:
- **Epic**: `jira_create_issue` has no epic parameter. Set the epic with a separate `jira_set_epic` call (`issue_key`, `epic_key`). When splitting a ticket, put children under the parent's epic.
- **Backlog placement**: see Project-specific conventions below.
- **Links**: see Linking issues below.

## 5. Project-specific conventions

### SERVER

- `Assigned Teams` is required.
- **Newly created tickets land in status `Needs Scheduling`.**
- Use `jira_set_epic` to attach tickets to an epic (e.g. an `SPM-*` epic) before deciding backlog
  placement.
- If the ticket is assigned to a project/epic, move it to the **Backlog** after setting the epic:
  call `jira_get_issue_transitions` to find the `Send to Backlog` transition (its numeric
  `transition_id` varies by workflow — do not hardcode it), then `jira_transition_issue` with that
  id so the status becomes `Backlog`.
- If the ticket is not assigned to a project/epic, leave it in **Needs Scheduling**.

## 6. Linking issues

- **Discover link types first** with `jira_list_link_types`. Names are exact and unintuitive — e.g. the blocking type is **`Block`** (singular, not "Blocks"); other common types include `Depends` (outward "depends on" / inward "is depended on by"), `Related`, `Duplicate`, and `Issue split` (outward "split to" / inward "split from").
- **Direction:** in `jira_link_issues`, `outward_issue` is the side the link type's *outward* phrase applies to. So for "**A depends on B**": `outward_issue = A`, `inward_issue = B`, `link_type = "Depends"`. For "**A blocks B**": `outward_issue = A`, `inward_issue = B`, `link_type = "Block"`.
- Prefer the link type that matches the user's wording (use `Depends` when they say "depends on").
