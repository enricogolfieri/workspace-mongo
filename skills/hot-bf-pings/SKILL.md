---
name: hot-bf-pings
description: Drafts Slack ping messages for hot Build Failures (BFs) from a Jira filter, listing the assignee, the SERVER dependency ticket, the GitHub PR, and a one-line status question. Use when the user asks to "prepare slack messages for hot BFs", "ping people about BFs", "draft hot BF status updates", or shares a Jira filter URL/JQL with BF tickets.
---

# Hot BF Slack Pings

Drafts short Slack messages that nudge owners of currently-hot BFs about progress, in the style used in the team's daily babysitting channel.

## Inputs

The Jira link https://jira.mongodb.org/issues/?filter=49343&jql=project%20in%20(AF%2C%20BF%2C%20PERF)%20and%20status%20not%20in%20(Resolved%2C%20Closed)%20and%20priority%20!%3D%20%22Trivial%20-%20P5%22%20and%20filter%20%3D%2053085%20and%20filter%20%3D%2053200%20and%20created%20%3C%3D%20-2d%20and%20%22Assigned%20Teams%22%20%3D%20%22Catalog%20and%20Routing%22%20and%20filter%20%3D%2053085%20and%20filter%20%3D%2053200%20and%20created%20%3C%3D%20-2d%20and%20%22Assigned%20Teams%22%20%3D%20%22Catalog%20and%20Routing%22


If only a filter ID is given without JQL, ask the user to paste the JQL or filter URL with the `jql=` parameter.

## Workflow

1. **Fetch hot BFs**. Use the `jira_search_issues` MCP tool (`devprod-mcp-gateway`) with the JQL extracted from the URL. Decode URL-encoded characters first.

2. **For each BF**, call `jira_get_issue` and read these `custom_fields`:
   - `Assignee`
   - `Status`
   - `Dependencies` — extract the `SERVER-XXXXX` key(s) from the HTML
   - `Dependency Due Date` — gives status of the dependency ticket
   - `Last Comment` / `Last commenter` — surfaces who last touched it and any handoff (e.g. "passed context to X")

3. **For each SERVER dependency**, find the open PR via gh:
   ```bash
   gh pr list --repo 10gen/mongo --search "SERVER-XXXXX" --state all \
     --json number,title,url,state,author
   ```
   Use the most recent OPEN PR. If none, note "no PR yet".

4. **If a BF has no SERVER dependency**, fetch the last few comments with `jira_get_issue_comments` to figure out what's blocking it (handoff, investigation, etc.).

5. **Draft one Slack line per BF** using the format below.

## Message format

One line per BF, following Dani's style. Vary phrasing slightly so it doesn't read like a template:

```
<BF jira link> [short context], @<assignee> has <PR link> <pr state phrase>, what's the status?
```

Concrete patterns to mix and match:

- Has SERVER + PR in review:
  `https://jira.mongodb.org/browse/BF-XXXXX waiting on https://jira.mongodb.org/browse/SERVER-YYYYY, @<assignee> has https://github.com/10gen/mongo/pull/NNNN open in code review, what's the current status?`

- PR through a second review:
  `https://jira.mongodb.org/browse/BF-XXXXX is waiting on https://jira.mongodb.org/browse/SERVER-YYYYY, https://github.com/10gen/mongo/pull/NNNN has gone through a second review, @<assignee> what's the status?`

- PR ready / approved:
  `https://jira.mongodb.org/browse/BF-XXXXX waiting on https://jira.mongodb.org/browse/SERVER-YYYYY, @<assignee> has https://github.com/10gen/mongo/pull/NNNN, ready to merge?`

- Handoff with no PR yet:
  `https://jira.mongodb.org/browse/BF-XXXXX <previous owner> had a first look and passed the context on to @<new assignee>. Any update?`

- BF with no SERVER ticket / PR:
  `https://jira.mongodb.org/browse/BF-XXXXX still In Progress with @<assignee>, no SERVER ticket or PR yet. Any update?`

## Style rules

- Use **bare jira.mongodb.org and github.com URLs** — Slack auto-unfurls them. Never wrap in markdown link syntax.
- **One BF per line**, separated by blank lines.
- Keep each line to a single sentence; end with a question (`what's the status?`, `ready to merge?`, `any update?`).
- Use `@FirstName LastName` placeholders for assignees. The user will replace these with real Slack mentions (`https://mongodb.enterprise.slack.com/team/U...`) — do NOT invent Slack user IDs.
- Order BFs by Jira key ascending (matches Dani's pattern).

## Output

After drafting the messages, also print a small recap table so the user can sanity-check:

| BF | Assignee | SERVER | PR | State |
|---|---|---|---|---|
| BF-XXXXX | Name | SERVER-YYYYY | #NNNN | In Code Review |

Then offer to:
- Swap `@Name` placeholders for real Slack user IDs if the user provides them.
- Consolidate into a single multi-line message vs. one message per BF.
