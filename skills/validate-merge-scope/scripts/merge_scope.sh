#!/usr/bin/env bash
# Source this file to get merge-scope helper functions.
# Usage: source ~/.cursor/skills/validate-merge-scope/scripts/merge_scope.sh

merge_scope_files() {
    local MERGE PRE OTHER BASE
    MERGE=$(git rev-list --first-parent --merges -n 1 HEAD)
    PRE="$MERGE^1"
    OTHER="$MERGE^2"
    BASE=$(git merge-base "$PRE" "$OTHER")
    comm -12 \
        <(git diff --name-only "$BASE..$PRE" | sort) \
        <(git diff --name-only "$PRE..$MERGE" | sort)
}

git-diff-merge-scope() {
    local MERGE PRE
    MERGE=$(git rev-list --first-parent --merges -n 1 HEAD)
    PRE="$MERGE^1"
    git diff "$PRE..$MERGE" -- $(merge_scope_files)
}
