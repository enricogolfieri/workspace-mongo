---
name: create-jira-ticket
description: Create a Jira ticket following team conventions, with duplicate detection and preview
user-invocable: true
---

# Create a Jira Ticket

Follow these steps in order when creating a Jira ticket.

## 1. Gather information

Infer as much as possible from the conversation context. Only ask the user about fields that cannot be reasonably inferred.

- **Project**: Use **SERVER** for bugs or improvements related to the MongoDB server main repository. For other projects, ask the user.
- **Issue type**: Bug, Improvement, Task, etc. (e.g., "this is broken" implies Bug)
- **Summary**: concise, to the point
- **Description**: concise, to the point. Include only what's necessary.
- **Assigned Team**: required field (customfield_12751). Ask the user if not clear from context.
- **Assignee**: optional. Only set if the user explicitly asks. Use the full email address (e.g., `user@mongodb.com`), not the short username.

**Every** mention of a function, class, method, or code construct in the description **must** be an inline GitHub link. Do not mention code identifiers as plain text — always look up the file and line number and link them. This is mandatory, not optional.

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
- Link format: `https://github.com/mongodb/mongo/blob/<commit-sha>/path/to/file.cpp#L42`
- **Never use raw URLs in the description.** Every link must use Markdown link syntax: `[text](url)`. This applies to all links — GitHub code references, Jira tickets, external resources, etc. The Jira MCP tool accepts Markdown and converts it to Jira Wiki Markup automatically.
- Make links inline in the description text — link the relevant words/phrases directly to the code rather than appending a bare URL at the end. For example: `the [preconditions check](https://github.com/mongodb/mongo/blob/<sha>/path/to/file.cpp#L125) does not include...`
- If the ticket is not about specific code at all, skip the links. But if any code entity is mentioned by name, it must be linked.

## 2. Check for duplicates

Before creating, search Jira for similar existing tickets:

- Use `mcp__jira__jira_search` with a JQL query targeting the same project and relevant keywords.
- Search broadly: use multiple key terms, not just the exact summary. Use `text ~ "keyword1 keyword2"` to match across summary, description, and comments.
- Include all statuses — a closed or resolved ticket can still be a duplicate.
- Limit results to 10 to keep output readable.
- Example: `project = SERVER AND text ~ "keyword1 keyword2" ORDER BY created DESC`
- If potential duplicates are found, show them to the user (key, summary, status) and ask whether to proceed or not.

## 3. Validate and preview

Use `mcp__jira__jira_get_field_options` with `field_id: "customfield_12751"`, `project_key`, and `issue_type` to verify the team value is valid. Use the `contains` parameter to filter by the team name. If it doesn't match any option, show the user the closest matches and ask them to pick one.

Then display a preview:

```
Project:        SERVER
Type:           Bug
Summary:        <title>
Assigned Team:  <team>
Assignee:       <email or "Unassigned">
Description:
<description with GitHub links>
```

Wait for explicit user confirmation before proceeding.

## 4. Create the ticket

Use `mcp__jira__jira_create_issue` with:
- `project_key`: the selected project
- `summary`: the title
- `issue_type`: the issue type
- `description`: the description in **Markdown format** — the Jira MCP tool accepts Markdown and converts it to Jira Wiki Markup automatically. Standard Markdown features are supported: `[text](url)` for links, `` `code` `` for inline code, fenced code blocks with language tags (` ```cpp `), `###` for headings, `**bold**`, `*italic*`, `1.` for ordered lists, `-` for unordered lists, tables (`| col | col |`), and blockquotes (`>`). **Do NOT use Jira Wiki Markup directly** (e.g., `[text|url]`, `{{code}}`, `h3.`, `#` for lists) — the `#` character in particular will be misinterpreted as a Markdown heading and rendered as bold h1 text instead of a list item.
- `assignee`: if requested (see above)
- `additional_fields`: `{"customfield_12751": [{"value": "<assigned team>"}]}` — note: the value must be an array of objects

After creation, show the ticket key and a direct link: `https://jira.mongodb.org/browse/<TICKET-KEY>`
