#!/usr/bin/env bash
# Install or update rude-manager for the current user: the /rude skill and the rude-manager agent.
#
#   ./install.sh              install, or update to the latest version (re-run it any time)
#   ./install.sh --local      use this checkout instead of the managed copy (for development)
#   ./install.sh --uninstall  remove the skill and the agent
#
# The managed copy is a git clone in $RUDE_MANAGER_HOME (default ~/.local/share/rude-manager).
# The skill and the agent are symlinked into $CLAUDE_CONFIG_DIR (default ~/.claude), so an update
# is picked up by Claude Code without reinstalling.
set -euo pipefail

REPO_URL="${RUDE_MANAGER_REPO:-https://github.com/alexandregensse-blip/rude-manager-skill.git}"
BRANCH="${RUDE_MANAGER_BRANCH:-main}"
SRC="${RUDE_MANAGER_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/rude-manager}"
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILL_LINK="$CFG/skills/rude"
AGENT_LINK="$CFG/agents/rude-manager.md"

die() { echo "rude-manager: $*" >&2; exit 1; }

# Refuse to overwrite anything we did not create.
check_free() {
  if [ -e "$1" ] && [ ! -L "$1" ]; then
    die "$1 exists and is not a symlink from a previous install; move it away first"
  fi
}

link() {
  check_free "$2"
  mkdir -p "$(dirname "$2")"
  ln -sfn "$1" "$2"
}

version_of() { cat "$1/VERSION" 2>/dev/null || echo "?"; }

case "${1:-}" in
  --uninstall)
    for l in "$SKILL_LINK" "$AGENT_LINK"; do
      check_free "$l"
      rm -f "$l"
    done
    echo "rude-manager: uninstalled (the managed copy in $SRC is left in place)"
    exit 0
    ;;
  --local)
    SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    link "$SRC/skills/rude" "$SKILL_LINK"
    link "$SRC/agents/rude-manager.md" "$AGENT_LINK"
    echo "rude-manager: $(version_of "$SRC") linked from local checkout $SRC"
    exit 0
    ;;
  "") ;;
  *) die "unknown option: $1 (use --local or --uninstall)" ;;
esac

command -v git >/dev/null || die "git is required"

if [ -d "$SRC/.git" ]; then
  before="$(git -C "$SRC" rev-parse HEAD)"
  before_version="$(version_of "$SRC")"
  git -C "$SRC" remote set-url origin "$REPO_URL"
  git -C "$SRC" fetch --quiet origin "$BRANCH"
  git -C "$SRC" checkout --quiet "$BRANCH" 2>/dev/null \
    || git -C "$SRC" checkout --quiet -b "$BRANCH" "origin/$BRANCH"
  git -C "$SRC" merge --quiet --ff-only "origin/$BRANCH" \
    || die "$SRC has local changes that block the update; delete it and re-run"
else
  before=""
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$SRC"
fi

link "$SRC/skills/rude" "$SKILL_LINK"
link "$SRC/agents/rude-manager.md" "$AGENT_LINK"

after="$(git -C "$SRC" rev-parse HEAD)"
after_version="$(version_of "$SRC")"
short="$(git -C "$SRC" rev-parse --short HEAD)"

if [ -z "$before" ]; then
  echo "rude-manager: installed $after_version ($short)"
elif [ "$before" = "$after" ]; then
  echo "rude-manager: already up to date, $after_version ($short)"
else
  echo "rude-manager: updated $before_version -> $after_version ($short)"
fi
echo "  skill: $SKILL_LINK"
echo "  agent: $AGENT_LINK"
