#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
SOURCE_SKILLS_DIR="${SCRIPT_DIR}/skills"
SOURCE_AGENTS_DIR="${SCRIPT_DIR}/agents"

die() { echo "Error: $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $0 [--target claude|cursor|both]

Install skills and agents via symlink into Claude and/or Cursor.
Agents are installed for Claude only (Cursor does not support agents).

Options:
  --target claude   Install for Claude Code only
  --target cursor   Install for Cursor only
  --target both     Install for both (default)
  -h, --help        Show this help

Environment overrides:
  CLAUDE_HOME       Override Claude home (default: ~/.claude)
  CURSOR_HOME       Override Cursor home (default: ~/.cursor)
EOF
  exit 0
}

TARGET="both"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    -h|--help) usage ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ "${TARGET}" =~ ^(claude|cursor|both)$ ]] || die "Invalid target '${TARGET}'. Use claude, cursor, or both."
[[ -d "${SOURCE_SKILLS_DIR}" ]] || die "Skills folder not found at '${SOURCE_SKILLS_DIR}'."

install_skills() {
  local tool_name="$1"
  local target_skills_dir="$2"

  mkdir -p "${target_skills_dir}"

  local installed_count=0
  local skill_dir
  for skill_dir in "${SOURCE_SKILLS_DIR}"/*/; do
    [[ -d "${skill_dir}" ]] || continue
    [[ -f "${skill_dir}/SKILL.md" ]] || continue

    local skill_name
    skill_name="$(basename "${skill_dir}")"
    local source_abs
    source_abs="$(cd "${skill_dir}" && pwd)"
    local destination="${target_skills_dir}/${skill_name}"

    rm -rf "${destination}"
    ln -s "${source_abs}" "${destination}"

    installed_count=$((installed_count + 1))
    echo "  Linked: ${skill_name} -> ${source_abs}"
  done

  [[ "${installed_count}" -gt 0 ]] || die "No skills found in '${SOURCE_SKILLS_DIR}'."
  echo "  ${tool_name}: ${installed_count} skill(s) installed into '${target_skills_dir}'."
}

install_agents() {
  local target_agents_dir="$1"

  [[ -d "${SOURCE_AGENTS_DIR}" ]] || return 0

  mkdir -p "${target_agents_dir}"

  local installed_count=0
  local agent_file
  for agent_file in "${SOURCE_AGENTS_DIR}"/*.md; do
    [[ -f "${agent_file}" ]] || continue

    local agent_name
    agent_name="$(basename "${agent_file}")"
    local source_abs
    source_abs="$(cd "$(dirname "${agent_file}")" && pwd)/${agent_name}"
    local destination="${target_agents_dir}/${agent_name}"

    rm -f "${destination}"
    ln -s "${source_abs}" "${destination}"

    installed_count=$((installed_count + 1))
    echo "  Linked: ${agent_name} -> ${source_abs}"
  done

  if [[ "${installed_count}" -gt 0 ]]; then
    echo "  Claude: ${installed_count} agent(s) installed into '${target_agents_dir}'."
  fi
}

if [[ "${TARGET}" == "claude" || "${TARGET}" == "both" ]]; then
  CLAUDE_ROOT="${CLAUDE_HOME:-$HOME/.claude}"
  echo "Installing for Claude..."
  install_skills "Claude" "${CLAUDE_ROOT}/skills"
  install_agents "${CLAUDE_ROOT}/agents"
fi

if [[ "${TARGET}" == "cursor" || "${TARGET}" == "both" ]]; then
  CURSOR_SKILLS="${CURSOR_HOME:-$HOME/.cursor}/skills"
  echo "Installing for Cursor..."
  install_skills "Cursor" "${CURSOR_SKILLS}"
fi

echo
echo "Done. Symlinks point to the repo — updates via git pull take effect immediately."
