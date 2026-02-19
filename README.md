# workspace-mongo

A zsh plugin (antigen bundle) that provides shell functions and aliases to streamline MongoDB server development. It wraps common workflows — building, testing, formatting, patching, and environment setup — into concise commands that automatically adapt to the target branch and build system (SCons/Ninja for <= v8.0, Bazel for master/v8.1+).

> Tailored for a specific workflow. Your mileage may vary.

## Installation

### As an antigen bundle

```zsh
antigen bundle enricogolfieri/workspace-mongo --branch=main
```

Then activate the environment in your shell:

```zsh
mongo-enable
```

### Manual

```zsh
git clone git@github.com:enricogolfieri/workspace-mongo.git $HOME/.config/workspace-mongo
source $HOME/.config/workspace-mongo/workspace-mongo.plugin.zsh
mongo-enable
```

## Setup

### Docker (recommended)

A Docker-based development environment is provided with all dependencies pre-installed (toolchain, mongosh, evergreen CLI, mrlog, fzf, etc.).

```zsh
# Configure git identity and global settings
mongo-setup-env

# Build and start the container
mongo-build-docker

# Attach to the running container
mongo-attach
```

Additional Docker commands:

| Command | Description |
|---|---|
| `mongo-run-docker` | Start an existing container without rebuilding |
| `mongo-stop-docker` | Stop the container |

### Remote Workstation

```zsh
# Configure git identity
mongo-setup-env

# Link shell configs (.zshrc, .zshenv, .gitconfig, .gitignore)
mongo-setup-workstation

# Install required tools (mrlog, db-contrib-tool, m)
mongo-setup-tools

# Install or update the MongoDB toolchain
mongo-setup-toolchain
```

## Commands

### Environment & Setup

| Command | Description |
|---|---|
| `mongo-enable` | Activate the mongo development environment for the current shell |
| `mongo-setup-env` | Configure git identity and global settings |
| `mongo-setup-workstation` | Link shell and git configs to your home directory |
| `mongo-setup-tools` | Install mrlog, db-contrib-tool, and m |
| `mongo-setup-toolchain` | Install or update the MongoDB toolchain |
| `mongo-setup-mongosh` | Install mongosh |
| `mongo-setup-user-tools` | Install mongoexport, mongodump, etc. |
| `mongo-setup-repo` | Clone the mongo repository |
| `mongo-setup-repos` | Clone multiple version branches and workloads |
| `mongo-setup-vscode-plugins` | Build and install VS Code extensions for mongo development |
| `mongo-setup-dsi` | Clone and configure DSI (performance testing infrastructure) |

### Build

| Command | Description |
|---|---|
| `mongo-venv` | Create or update the Python virtual environment |
| `mongo-configure` | Generate `build.ninja` and `compile_commands.json` (SCons branches) |
| `mongo-build` / `mbuild` | Build the project |
| `mongo-make-compiledb` / `mcompiledb` | Generate the compilation database for IDE support |
| `mongo-clean-ninja` | Remove build artifacts and clear ccache |

### Test

| Command | Description |
|---|---|
| `mongo-test-locally` / `mtl` | Run a JS test with resmoke |
| `mongo-test-locally-loop` | Run a test across all relevant suites, stop on first failure |
| `mongo-unit` | Run C++ unit tests |
| `mongo-dbtest` | Run dbtests (Bazel branches only) |
| `mongo-benchmark` | Run benchmark tests |
| `mongo-enable-multiversion` | Download last-LTS and last-continuous binaries for multiversion testing |
| `mongo-clean-core` | Remove core dump files from the working directory |

### Code Quality

| Command | Description |
|---|---|
| `mongo-format` | Format changed source files with clang-format |
| `mongo-lint-check` | Run the SCons lint target |
| `mongo-code-analysis` | Run IWYU (Include What You Use) analysis |

### Evergreen (CI)

| Command | Description |
|---|---|
| `mongo-run-patch` | Submit a finalized patch with required variants auto-selected |
| `mongo-set-patch` | Submit a patch interactively (choose variants and description) |
| `mongo-run-patch-perf` | Submit a sys-perf patch |
| `mongo-set-patch-perf` | Submit a sys-perf patch interactively |
| `mongo-set-patch-workload` | Submit a patch with custom workloads |
| `mongo-get-failing-tests` | List failing tests for a given patch ID |
| `mongo-group-failing-tests` | Group and display failing tests by file |
| `mongo-evg-ls` | Export failing test info to a file |
| `mongo-download-evg-logs` | Download Evergreen log files locally |

### Utilities

| Command | Description |
|---|---|
| `mongo-backport` | Cherry-pick a commit to a release branch, push, create EVG patch and PR |
| `mongo-download-bin-and-symbols` | Download MongoDB binaries and debug symbols for a given version |
| `mongo-data-files-setup` | Set up a venv with wiredtiger-debug-tools |
| `mongo-free-memory` | Clean up temp files and dump directories |
| `mongo-debug` | Print the current parsed configuration (branch, toolchain, build mode, etc.) |
| `checkout` | Shortcut for `git checkout <branch>` using the parsed branch |

### Bundled Scripts

The `bashscripts/` directory is added to `$PATH` when the environment is activated:

| Script | Description |
|---|---|
| `mcluster` | Cluster management utility |
| `sdb` | Debug helper |
| `pmp` | Poor man's profiler |
| `mtails` | Tail multiple log files |
| `watch_catalog` | Watch the MongoDB catalog (see `WATCH_CATALOG_README.md`) |
| `hex_2_bson.py` | Convert hex strings to BSON |

## Common Options

Most commands accept the following flags:

| Flag | Description |
|---|---|
| `--master`, `--v8.1`, `--v8.0`, `--v7.0`, ... | Target branch (auto-detected from directory name by default) |
| `--clang` / `--gcc` | Compiler family (default: clang) |
| `--debug` / `--opt` / `--release` | Build mode |
| `--dynamic` / `--static` | Link model |
| `--sanitize-address` / `--sanitize-thread` | Enable sanitizers |
| `--format` / `--no-format` | Run clang-format before building |
| `--mono-task` / `--multi-task` | Test concurrency |
| `--local` | Disable icecc, use 12 local jobs |
| `--echo` | Dry-run — print commands instead of executing them |
| `--burn-in` | Evergreen burn-in mode |
| `--verbose` | Increase log component verbosity |

## Branch Auto-Detection

If your working directory is named `mongo-vX.Y` (e.g., `mongo-v8.0`), the branch is detected automatically. Otherwise it defaults to `master`. You can always override with `--v8.0`, `--v7.0`, etc.
