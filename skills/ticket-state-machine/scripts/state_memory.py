#!/usr/bin/env python3
"""Write and read resumable ticket state under /tmp/<ticket-key>."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _memory_dir(base_dir: Path, ticket: str) -> Path:
    return base_dir / ticket


def _state_path(base_dir: Path, ticket: str) -> Path:
    return _memory_dir(base_dir, ticket) / "state.json"


def _patch_path(base_dir: Path, ticket: str) -> Path:
    return _memory_dir(base_dir, ticket) / "changes.patch"


def _doc_path(memory_dir: Path, doc_name: str) -> Path:
    """Standard cached markdown paths live beside state.json in the memory dir."""
    return memory_dir / f"{doc_name}.md"


def cache_markdown_document(
    memory_dir: Path,
    doc_name: str,
    *,
    source: Path | None = None,
    text: str | None = None,
) -> Path:
    """Write or refresh a cached markdown file and return its absolute path."""
    dest = _doc_path(memory_dir, doc_name)
    if source is not None:
        if str(source) == "-":
            import sys

            text = sys.stdin.read()
        else:
            if not source.is_file():
                raise SystemExit(f"Source file does not exist: {source}")
            text = source.read_text(encoding="utf-8")
    if text is None:
        raise SystemExit(f"No content provided for {doc_name}.md")
    dest.write_text(text, encoding="utf-8")
    return dest.resolve()


def _sync_standard_doc_links(state: dict[str, Any], memory_dir: Path) -> None:
    """If context.md / design.md exist in the memory dir, ensure state links to them."""
    for doc_name, field in (("context", "context_path"), ("design", "design_path")):
        doc_path = _doc_path(memory_dir, doc_name)
        if doc_path.is_file():
            state[field] = str(doc_path.resolve())


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _append_unique(existing: list[str], values: list[str]) -> list[str]:
    result = list(existing)
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _parse_ticket(ticket: str) -> tuple[str, str]:
    match = re.fullmatch(r"([A-Z]+)-(\d+)", ticket)
    if not match:
        raise SystemExit(f"Ticket key must look like SERVER-12345, got: {ticket}")
    return match.group(1), match.group(2)


def _normalize_keyword(keyword: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", keyword.strip().lower())
    normalized = normalized.strip("-")
    if not normalized:
        raise SystemExit(f"Invalid branch keyword: {keyword!r}")
    return normalized


def branch_name_from_ticket(ticket: str, keywords: list[str]) -> str:
    """Build SERVER-<number>-<kw1>-<kw2>-... from ticket key and keywords."""
    project, number = _parse_ticket(ticket)
    if not keywords:
        raise SystemExit("At least one branch keyword is required (use --branch-keywords).")
    normalized = [_normalize_keyword(keyword) for keyword in keywords]
    return f"{project}-{number}-{'-'.join(normalized)}"


def _detect_base_ref(repo: Path) -> str:
    upstream = _run_git(repo, "rev-parse", "--abbrev-ref", "HEAD@{upstream}", check=False)
    if upstream.returncode == 0:
        upstream_ref = upstream.stdout.strip()
        if upstream_ref:
            if "/" in upstream_ref:
                return upstream_ref.split("/", 1)[1]
            return upstream_ref
    for candidate in ("master", "main"):
        if _run_git(repo, "show-ref", "--verify", f"refs/heads/{candidate}", check=False).returncode == 0:
            return candidate
    return "HEAD"


def _branch_exists(repo: Path, branch: str) -> bool:
    result = _run_git(repo, "show-ref", "--verify", f"refs/heads/{branch}", check=False)
    return result.returncode == 0


def _current_branch(repo: Path) -> str:
    return _run_git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def _head_commit(repo: Path) -> str:
    return _run_git(repo, "rev-parse", "HEAD").stdout.strip()


def ensure_branch(repo: Path, branch: str, base_ref: str) -> None:
    current = _current_branch(repo)
    if current == branch:
        return
    if _branch_exists(repo, branch):
        _run_git(repo, "checkout", branch)
        return
    _run_git(repo, "checkout", "-b", branch, base_ref)


def _capture_patch(repo: Path, patch_path: Path, base_ref: str | None, branch: str | None) -> None:
    sections: list[str] = []

    if base_ref and branch:
        committed = _run_git(repo, "diff", "--binary", f"{base_ref}...HEAD", check=False)
        if committed.returncode == 0 and committed.stdout:
            sections.append(
                f"# Committed changes on branch {branch} since {base_ref}\n{committed.stdout}"
            )

    working_tree = _run_git(repo, "diff", "--binary", check=False)
    if working_tree.returncode == 0 and working_tree.stdout:
        sections.append(f"# Uncommitted working tree changes\n{working_tree.stdout}")

    staged = _run_git(repo, "diff", "--binary", "--cached", check=False)
    if staged.returncode == 0 and staged.stdout:
        sections.append(f"# Staged changes\n{staged.stdout}")

    if not sections:
        # Fallback: capture whatever is dirty in the working tree.
        fallback = _run_git(repo, "diff", "--binary")
        patch_path.write_text(fallback.stdout, encoding="utf-8")
        return

    patch_path.write_text("\n".join(sections), encoding="utf-8")


def read_state(args: argparse.Namespace) -> int:
    path = _state_path(args.base_dir, args.ticket)
    if not path.exists():
        print(json.dumps({"exists": False, "ticket": args.ticket}, indent=2, sort_keys=True))
        return 0
    print(path.read_text(encoding="utf-8"))
    return 0


def dump_state(args: argparse.Namespace) -> int:
    memory_dir = _memory_dir(args.base_dir, args.ticket)
    memory_dir.mkdir(parents=True, exist_ok=True)

    state_path = _state_path(args.base_dir, args.ticket)
    patch_path = _patch_path(args.base_dir, args.ticket)
    state = _load_state(state_path)

    extra_context = state.get("extra_context", {})
    if args.extra_json:
        extra_context.update(json.loads(args.extra_json))

    work_kind = args.work_kind or state.get("work_kind") or "original"

    if args.set_gotchas is not None:
        gotchas = json.loads(args.set_gotchas)
        if not isinstance(gotchas, list) or not all(isinstance(item, str) for item in gotchas):
            raise SystemExit("--set-gotchas must be a JSON array of strings")
    else:
        gotchas = _append_unique(state.get("gotchas", []), args.gotcha)

    if args.plan_path is not None:
        plan_path = Path(args.plan_path).resolve()
        if not plan_path.is_file():
            raise SystemExit(f"Plan file does not exist: {plan_path}")
        state["plan_path"] = str(plan_path)
        state.pop("plan", None)

    if args.context is not None:
        state["context_path"] = str(
            cache_markdown_document(memory_dir, "context", text=args.context)
        )
    elif args.write_context_from is not None:
        state["context_path"] = str(
            cache_markdown_document(memory_dir, "context", source=args.write_context_from)
        )

    if args.design is not None:
        state["design_path"] = str(
            cache_markdown_document(memory_dir, "design", text=args.design)
        )
    elif args.write_design_from is not None:
        state["design_path"] = str(
            cache_markdown_document(memory_dir, "design", source=args.write_design_from)
        )

    _sync_standard_doc_links(state, memory_dir)

    base_ref = args.base_ref or state.get("base_ref") or _detect_base_ref(args.repo)

    branch = args.branch or state.get("branch")
    if args.branch_keywords:
        branch = branch_name_from_ticket(args.ticket, args.branch_keywords)
    if args.ensure_branch:
        if not branch:
            raise SystemExit("--ensure-branch requires --branch or --branch-keywords")
        ensure_branch(args.repo, branch, base_ref)

    head_commit = _head_commit(args.repo) if branch and _current_branch(args.repo) == branch else None

    state.update(
        {
            "ticket": args.ticket,
            "phase_reached": args.phase,
            "work_kind": work_kind,
            "split_phase_allowed": work_kind != "sub-work",
            "gotchas": gotchas,
            "user_instructions": _append_unique(
                state.get("user_instructions", []), args.instruction
            ),
            "extra_context": extra_context,
            "split_decision": args.split_decision
            if args.split_decision is not None
            else state.get("split_decision"),
            "validation": args.validation
            if args.validation is not None
            else state.get("validation"),
            "base_ref": base_ref,
            "branch": branch or state.get("branch"),
            "head_commit": head_commit or state.get("head_commit"),
            "memory_dir": str(memory_dir),
            "patch_path": str(patch_path),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    if args.capture_patch:
        _capture_patch(args.repo, patch_path, state.get("base_ref"), state.get("branch"))
    elif not patch_path.exists():
        patch_path.write_text("", encoding="utf-8")

    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(state_path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("read", "dump"))
    parser.add_argument("ticket", help="Ticket key, for example SERVER-12345")
    parser.add_argument("--base-dir", type=Path, default=Path("/tmp"))

    parser.add_argument("--phase", default="LOAD_MEMORY")
    parser.add_argument("--work-kind", choices=("original", "sub-work"))
    parser.add_argument("--gotcha", action="append", default=[])
    parser.add_argument("--instruction", action="append", default=[])
    parser.add_argument("--extra-json", help="JSON object merged into extra_context")
    parser.add_argument(
        "--plan-path",
        help="Link an existing plan file (stored as plan_path, not inlined)",
    )
    parser.add_argument(
        "--context",
        help="Ticket scope markdown; written to <memory_dir>/context.md (context_path set automatically)",
    )
    parser.add_argument(
        "--design",
        help="Design context markdown; written to <memory_dir>/design.md (design_path set automatically)",
    )
    parser.add_argument(
        "--write-context-from",
        type=Path,
        help="Optional: copy a file or stdin (-) into context.md instead of --context",
    )
    parser.add_argument(
        "--write-design-from",
        type=Path,
        help="Optional: copy a file or stdin (-) into design.md instead of --design",
    )
    parser.add_argument(
        "--set-gotchas",
        help='Replace the entire gotchas list with a JSON array of strings, e.g. \'["gotcha one"]\'',
    )
    parser.add_argument("--split-decision")
    parser.add_argument("--validation")
    parser.add_argument("--capture-patch", action="store_true")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--branch",
        help="Explicit git branch name (normally derived via --branch-keywords)",
    )
    parser.add_argument(
        "--branch-keywords",
        help="Comma-separated keywords for branch name, e.g. strict,chunks",
    )
    parser.add_argument(
        "--base-ref",
        help="Base branch/ref for diffs and new branch creation (default: upstream base or master)",
    )
    parser.add_argument(
        "--ensure-branch",
        action="store_true",
        help="Create the ticket branch if missing and check it out",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.branch_keywords:
        args.branch_keywords = [
            keyword.strip()
            for keyword in args.branch_keywords.split(",")
            if keyword.strip()
        ]
    if args.command == "read":
        return read_state(args)
    return dump_state(args)


if __name__ == "__main__":
    raise SystemExit(main())
