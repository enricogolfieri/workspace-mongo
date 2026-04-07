#!/usr/bin/env python3
"""
Analyzes a merge to mechanically detect:
1. Deleted code re-introduced by the merge
2. Comments I wrote that the merge altered or removed
3. Code I changed that the merge reverted back to the base version
4. Interaction zones where both sides made changes
5. Intent conflicts: merge introduces code matching patterns I was removing

Usage: python3 analyze_merge.py [--verbose]
"""

import subprocess
import sys
import re
from dataclasses import dataclass, field


def git(*args: str) -> str:
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True)
    return r.stdout


def git_show(rev: str, path: str) -> list[str]:
    r = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, text=True
    )
    return r.stdout.splitlines() if r.returncode == 0 else []


def get_refs() -> tuple[str, str, str, str]:
    merge = git("rev-list", "--first-parent", "--merges", "-n", "1", "HEAD").strip()
    if not merge:
        sys.exit("ERROR: No merge commit found in HEAD history")
    pre = f"{merge}^1"
    other = f"{merge}^2"
    base = git("merge-base", pre, other).strip()
    return base, pre, other, merge


def get_file_sets(
    base: str, pre: str, merge: str
) -> tuple[list[str], list[str], set[str], set[str]]:
    """Returns (merge_scope_files, merge_only_files, my_file_set, merge_file_set)."""
    my_files = set(git("diff", "--name-only", f"{base}..{pre}").strip().splitlines())
    merge_files = set(
        git("diff", "--name-only", f"{pre}..{merge}").strip().splitlines()
    )
    scope = sorted(my_files & merge_files)
    merge_only = sorted(merge_files - my_files)
    return scope, merge_only, my_files, merge_files


def is_comment(line: str) -> bool:
    s = line.strip()
    return bool(
        re.match(r"^(//|/\*|\*[^/]|\*/|#(?!include|pragma|define|if|else|endif))", s)
    )


_IDENT_RE = re.compile(r"[A-Za-z_]\w{3,}")


def extract_identifiers(line: str) -> set[str]:
    return set(_IDENT_RE.findall(line))


def find_line_numbers(lines: list[str], needles: set[str]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for i, l in enumerate(lines, 1):
        key = l.rstrip()
        if key in needles:
            result.setdefault(key, []).append(i)
    return result


@dataclass
class Finding:
    category: str
    lines: list[str] = field(default_factory=list)
    meta: dict[str, object] = field(default_factory=dict)


def extract_my_deleted_identifiers(
    base_ref: str, pre_ref: str, my_files: set[str]
) -> set[str]:
    """Collect identifiers from lines I deleted across all my changed files."""
    deleted_ids: set[str] = set()
    for path in my_files:
        base_lines = git_show(base_ref, path)
        mine_lines = git_show(pre_ref, path)
        base_s = {l.rstrip() for l in base_lines}
        mine_s = {l.rstrip() for l in mine_lines}
        for line in base_s - mine_s:
            if line.strip() and not is_comment(line):
                deleted_ids |= extract_identifiers(line)
    return deleted_ids


def extract_my_added_identifiers(
    base_ref: str, pre_ref: str, my_files: set[str]
) -> set[str]:
    """Collect identifiers from lines I added across all my changed files."""
    added_ids: set[str] = set()
    for path in my_files:
        base_lines = git_show(base_ref, path)
        mine_lines = git_show(pre_ref, path)
        base_s = {l.rstrip() for l in base_lines}
        mine_s = {l.rstrip() for l in mine_lines}
        for line in mine_s - base_s:
            if line.strip() and not is_comment(line):
                added_ids |= extract_identifiers(line)
    return added_ids


def filter_rare_identifiers(
    deleted_ids: set[str], added_ids: set[str], min_len: int = 10
) -> set[str]:
    """Keep identifiers that are specific to my deleted code.

    Requires: deleted but NOT re-added, >= min_len chars, not a common keyword.
    The high min_len filters generic words while keeping domain symbols like
    keepTemporaryTables, TemporaryRecordStore, etc."""
    common = {
        "void", "auto", "bool", "char", "const", "enum", "extern", "float",
        "inline", "long", "namespace", "nullptr", "return", "short", "signed",
        "sizeof", "static", "struct", "switch", "template", "this", "throw",
        "typedef", "typename", "unsigned", "using", "virtual", "volatile",
        "while", "class", "catch", "break", "case", "continue", "default",
        "delete", "double", "else", "explicit", "export", "false", "final",
        "friend", "goto", "import", "include", "module", "modules", "mutable",
        "noexcept", "operator", "override", "private", "protected", "public",
        "register", "requires", "static_cast", "dynamic_cast",
        "reinterpret_cast", "const_cast", "true", "string", "vector",
        "unique_ptr", "shared_ptr", "make_unique", "make_shared", "optional",
        "variant", "tuple", "pair", "size_t", "int32_t", "int64_t", "uint32_t",
        "uint64_t", "Status", "StatusWith", "StringData", "BSONObj",
        "BSONElement", "OperationContext", "NamespaceString", "UUID",
        "container", "define", "config", "context", "server", "client",
        "result", "value", "error", "handle", "create", "insert", "update",
        "remove", "find", "begin", "assert", "expect", "index", "build",
        "test", "Test", "TEST", "mock", "Mock", "Impl", "impl", "Base",
        "base", "util", "utils", "Util", "Utils", "param", "params",
        "option", "options", "callback", "listener", "handler", "factory",
        "manager", "service", "cursor", "session", "opCtx",
    }
    purely_deleted = deleted_ids - added_ids - common
    return {i for i in purely_deleted if len(i) >= min_len}


def analyze_scope_file(
    path: str,
    base_ref: str,
    pre_ref: str,
    other_ref: str,
    merge_ref: str,
) -> list[Finding]:
    base = git_show(base_ref, path)
    mine = git_show(pre_ref, path)
    theirs = git_show(other_ref, path)
    merged = git_show(merge_ref, path)

    base_s = {l.rstrip() for l in base}
    mine_s = {l.rstrip() for l in mine}
    merged_s = {l.rstrip() for l in merged}
    theirs_s = {l.rstrip() for l in theirs}

    findings: list[Finding] = []

    # 1. Lines I deleted (in base, not in mine) that reappear in merged
    my_deletions = base_s - mine_s
    reintroduced = sorted(l for l in my_deletions & merged_s if l.strip())
    if reintroduced:
        lnums = find_line_numbers(merged, set(reintroduced))
        details = []
        for line in reintroduced:
            nums = lnums.get(line, [])
            prefix = f"L{','.join(map(str, nums))}" if nums else "?"
            details.append(f"{prefix}: {line}")
        findings.append(Finding("DELETED_CODE_REINTRODUCED", details))

    # 2. Comment lines I added/changed that are missing from merged
    my_additions = mine_s - base_s
    my_comments = {l for l in my_additions if is_comment(l)}
    lost_comments = sorted(l for l in my_comments - merged_s if l.strip())
    if lost_comments:
        lnums = find_line_numbers(mine, set(lost_comments))
        details = []
        for line in lost_comments:
            nums = lnums.get(line, [])
            prefix = f"L{','.join(map(str, nums))} (mine)" if nums else "?"
            details.append(f"{prefix}: {line}")
        findings.append(Finding("MY_COMMENTS_MODIFIED_OR_REMOVED", details))

    # 3. Code lines I added/changed that are gone in merged
    my_code_adds = {l for l in my_additions if not is_comment(l) and l.strip()}
    reverted = sorted(l for l in my_code_adds - merged_s if l.strip())
    if reverted:
        back_to_base = [l for l in reverted if l.rstrip() in base_s]
        genuinely_modified = [l for l in reverted if l.rstrip() not in base_s]
        if back_to_base:
            lnums = find_line_numbers(mine, set(back_to_base))
            details = [
                f"L{','.join(map(str, lnums.get(l, [])))} (mine): {l}"
                for l in back_to_base
            ]
            findings.append(Finding("MY_CODE_REVERTED_TO_BASE", details))
        if genuinely_modified:
            lnums = find_line_numbers(mine, set(genuinely_modified))
            details = [
                f"L{','.join(map(str, lnums.get(l, [])))} (mine): {l}"
                for l in genuinely_modified
            ]
            findings.append(Finding("MY_CODE_MODIFIED_BY_MERGE", details))

    # 4. Interaction zones: both sides added non-trivial new code
    their_additions = theirs_s - base_s
    their_new = {l for l in their_additions if l.strip() and not is_comment(l)}
    my_new = {l for l in my_additions if l.strip() and not is_comment(l)}
    if their_new and my_new:
        findings.append(
            Finding(
                "INTERACTION_ZONE",
                meta={
                    "my_new_code_lines": len(my_new),
                    "their_new_code_lines": len(their_new),
                    "shared_new_lines": len(my_new & their_new),
                },
            )
        )

    return findings


def analyze_merge_only_file(
    path: str,
    base_ref: str,
    merge_ref: str,
    deleted_patterns: set[str],
) -> list[Finding]:
    """Analyze a file changed only by the merge (not by me).
    Flag lines the merge introduced that contain identifiers I was deleting."""
    base = git_show(base_ref, path)
    merged = git_show(merge_ref, path)

    base_s = {l.rstrip() for l in base}
    merged_s = {l.rstrip() for l in merged}

    merge_additions = merged_s - base_s
    if not merge_additions:
        return []

    flagged: list[str] = []
    lnums = find_line_numbers(merged, merge_additions)
    for line in sorted(merge_additions):
        if not line.strip() or is_comment(line):
            continue
        line_ids = extract_identifiers(line)
        hits = line_ids & deleted_patterns
        if hits:
            nums = lnums.get(line, [])
            prefix = f"L{','.join(map(str, nums))}" if nums else "?"
            flagged.append(f"{prefix}: {line}  (matches: {', '.join(sorted(hits))})")

    if flagged:
        return [Finding("INTENT_CONFLICT", flagged)]
    return []


def print_findings(path: str, findings: list[Finding]) -> None:
    print(f"{'=' * 70}")
    print(f"FILE: {path}")
    print(f"{'=' * 70}")
    for finding in findings:
        print(f"\n  [{finding.category}]")
        for line in finding.lines[:20]:
            print(f"    {line}")
        if len(finding.lines) > 20:
            print(f"    ... and {len(finding.lines) - 20} more")
        for k, v in finding.meta.items():
            print(f"    {k}: {v}")
    print()


def main():
    verbose = "--verbose" in sys.argv
    base, pre, other, merge = get_refs()
    scope_files, merge_only_files, my_file_set, _ = get_file_sets(base, pre, merge)

    merge_short = git("rev-parse", "--short", merge.split("^")[0]).strip()
    base_short = git("rev-parse", "--short", base).strip()
    print(f"Merge commit : {merge_short}")
    print(f"Common base  : {base_short}")
    print(f"Scope files  : {len(scope_files)} (changed by both sides)")
    print(f"Merge-only   : {len(merge_only_files)} (changed only by merge)")
    print()

    # Build deleted-identifier set for intent conflict detection
    deleted_ids = extract_my_deleted_identifiers(base, pre, my_file_set)
    added_ids = extract_my_added_identifiers(base, pre, my_file_set)
    deleted_patterns = filter_rare_identifiers(deleted_ids, added_ids)

    # Scope merge-only files to directories where I have changes
    my_dirs = {"/".join(f.split("/")[:-1]) for f in my_file_set if "/" in f}
    related_merge_only = [
        f for f in merge_only_files
        if any(f.startswith(d + "/") for d in my_dirs)
    ]

    if verbose and deleted_patterns:
        sample = sorted(deleted_patterns)[:20]
        print(f"Deleted-identifier patterns ({len(deleted_patterns)} total): "
              f"{', '.join(sample)}{'...' if len(deleted_patterns) > 20 else ''}")
        print(f"Related merge-only files: {len(related_merge_only)} "
              f"(of {len(merge_only_files)} total, scoped to {len(my_dirs)} dirs)")
        print()

    flagged_scope = []
    clean_scope = []
    flagged_merge_only = []

    # Phase 1: Analyze merge scope files
    for f in scope_files:
        findings = analyze_scope_file(f, base, pre, other, merge)
        if findings:
            flagged_scope.append(f)
            print_findings(f, findings)
        else:
            clean_scope.append(f)

    # Phase 2: Analyze merge-only files for intent conflicts
    if deleted_patterns:
        for f in related_merge_only:
            findings = analyze_merge_only_file(f, base, merge, deleted_patterns)
            if findings:
                flagged_merge_only.append(f)
                print_findings(f, findings)

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Scope flagged       : {len(flagged_scope)} files")
    print(f"  Scope clean         : {len(clean_scope)} files")
    print(f"  Intent conflicts    : {len(flagged_merge_only)} files")
    if verbose:
        for f in clean_scope:
            print(f"    OK {f}")


if __name__ == "__main__":
    main()
