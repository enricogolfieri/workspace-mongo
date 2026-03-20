---
name: mcluster
description: Manage local MongoDB clusters with the mcluster script, including setup, version linking, cluster init, status checks, and binary diagnostics. Use when the user asks to spin up a local cluster, inspect ports/primary, or troubleshoot mcluster setup/link errors.
---

# mcluster Workflow

Use `bashscripts/mcluster` for local cluster lifecycle and diagnostics.

## Quick Start

```bash
mcluster setup
mcluster link <major>.<minor> (8.0). To link master we use "." which must be compiled via resmoke. 
mcluster init-cluster
mcluster status --json
```

`init*` commands initialize and start a cluster in one step.

## Core Commands

- `mcluster setup`: mandatory bootstrap; recreates `~/.mcluster/.venv`, installs tools, and cleans prior cluster state/processes.
- `mcluster link .`: use local repo binaries (`./bazel-bin/install/bin`).
- `mcluster link <version>`: activate/install via `m`, then link that version.
- `mcluster initd|init-replica|init-lite|init-cluster`: create and start cluster layouts.
- `mcluster start`: restart an already-initialized cluster.
- `mcluster status --json`: machine-readable cluster state (`mongos`, `mongod`, `primary`).
- `mcluster binary --json`: show resolved binary paths and versions for troubleshooting.

## Troubleshooting Order

1. Run `mcluster setup` if any command says setup is missing or stale.
2. Run `mcluster binary --json` to confirm `mongod`/`mongos` resolution.
3. If `.mongo_paths` is missing, run `mcluster link .` or `mcluster link <version>`.
4. If startup metadata is missing, run an `init*` command before `start`.

## AI Usage Notes

- Prefer `mcluster status --json` for automation and summaries.
- Report:
  - `mongos` ports
  - `mongod` ports
  - `primary`
  - `running` flag
- On failures, include the exact remediation command shown by `mcluster`.
