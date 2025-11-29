#!/usr/bin/env bash
# Mutation testing using git worktree isolation
#
# Usage:
#   mutation-worktree.sh setup     Create/update worktree and sync dependencies
#   mutation-worktree.sh init      Initialize mutation testing session
#   mutation-worktree.sh exec      Execute mutation testing
#   mutation-worktree.sh status    Show worktree and session status
#   mutation-worktree.sh clean     Remove worktree and session files
#
# Options:
#   --fresh    Force recreation of worktree (with setup/init)
#   --resume   Skip init, continue existing session (with exec)

set -euo pipefail

# Project root (where this script lives is scripts/, go up one level)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Worktree location
WORKTREE_DIR="$PROJECT_ROOT/.mutation-worktree"

# Session database (stored in main project for easy access)
SESSION_DB="$PROJECT_ROOT/session.sqlite"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

# Check if worktree exists
worktree_exists() {
    [[ -d "$WORKTREE_DIR" ]]
}

# Get current HEAD commit
get_head_commit() {
    git -C "$PROJECT_ROOT" rev-parse HEAD
}

# Get worktree commit (if exists)
get_worktree_commit() {
    if worktree_exists; then
        git -C "$WORKTREE_DIR" rev-parse HEAD 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Check for staged changes
has_staged_changes() {
    ! git -C "$PROJECT_ROOT" diff --cached --quiet
}

# Create stash ref from staged changes (without actually stashing)
create_staged_stash() {
    git -C "$PROJECT_ROOT" stash create
}

# Setup worktree
cmd_setup() {
    local force_fresh=false

    # Parse options
    for arg in "$@"; do
        case "$arg" in
            --fresh)
                force_fresh=true
                ;;
        esac
    done

    local head_commit
    head_commit=$(get_head_commit)

    # Remove existing worktree if --fresh
    if $force_fresh && worktree_exists; then
        info "Removing existing worktree (--fresh)"
        git -C "$PROJECT_ROOT" worktree remove "$WORKTREE_DIR" --force 2>/dev/null || rm -rf "$WORKTREE_DIR"
    fi

    if worktree_exists; then
        local worktree_commit
        worktree_commit=$(get_worktree_commit)

        if [[ "$worktree_commit" != "$head_commit" ]]; then
            info "Updating worktree to HEAD ($head_commit)"
            git -C "$WORKTREE_DIR" fetch origin 2>/dev/null || true
            git -C "$WORKTREE_DIR" reset --hard "$head_commit"
        else
            info "Worktree already at HEAD ($head_commit)"
        fi
    else
        info "Creating worktree at $WORKTREE_DIR"
        git -C "$PROJECT_ROOT" worktree add "$WORKTREE_DIR" HEAD
    fi

    # Handle staged changes
    if has_staged_changes; then
        info "Applying staged changes to worktree"
        local stash_ref
        stash_ref=$(create_staged_stash)

        if [[ -n "$stash_ref" ]]; then
            if git -C "$WORKTREE_DIR" stash apply "$stash_ref" 2>/dev/null; then
                success "Staged changes applied successfully"
            else
                warn "Could not apply staged changes, continuing with HEAD only"
                git -C "$WORKTREE_DIR" reset --hard HEAD
            fi
        fi
    fi

    # Warn about unstaged changes
    if ! git -C "$PROJECT_ROOT" diff --quiet; then
        warn "Unstaged changes detected - these will NOT be included in mutation testing"
    fi

    # Sync dependencies in worktree
    info "Syncing dependencies in worktree"
    (cd "$WORKTREE_DIR" && uv sync --frozen)

    success "Worktree ready at $WORKTREE_DIR"
}

# Initialize mutation testing session
cmd_init() {
    # Setup worktree first
    cmd_setup "$@"

    info "Running baseline tests"
    (cd "$WORKTREE_DIR" && uv run cosmic-ray baseline cosmic-ray.toml)

    info "Initializing mutation session"
    (cd "$WORKTREE_DIR" && uv run cosmic-ray init cosmic-ray.toml "$SESSION_DB")

    success "Mutation session initialized: $SESSION_DB"
}

# Execute mutation testing
cmd_exec() {
    local resume=false

    # Parse options
    for arg in "$@"; do
        case "$arg" in
            --resume)
                resume=true
                ;;
        esac
    done

    # Verify worktree exists
    if ! worktree_exists; then
        error "Worktree does not exist. Run 'just mutation-init' first."
        exit 1
    fi

    # Verify session exists (unless resuming)
    if ! $resume && [[ ! -f "$SESSION_DB" ]]; then
        error "Session database not found. Run 'just mutation-init' first."
        exit 1
    fi

    info "Running mutation testing in worktree"
    (cd "$WORKTREE_DIR" && uv run cosmic-ray exec cosmic-ray.toml "$SESSION_DB")

    success "Mutation testing complete. View results with 'just mutation-results'"
}

# Show status
cmd_status() {
    echo "=== Mutation Testing Status ==="
    echo

    # Worktree status
    echo "Worktree:"
    if worktree_exists; then
        local worktree_commit head_commit
        worktree_commit=$(get_worktree_commit)
        head_commit=$(get_head_commit)

        echo "  Location: $WORKTREE_DIR"
        echo "  Commit: $worktree_commit"

        if [[ "$worktree_commit" == "$head_commit" ]]; then
            echo -e "  Status: ${GREEN}Up to date with HEAD${NC}"
        else
            echo -e "  Status: ${YELLOW}Behind HEAD ($head_commit)${NC}"
        fi
    else
        echo -e "  Status: ${YELLOW}Not created${NC}"
    fi
    echo

    # Session status
    echo "Session:"
    if [[ -f "$SESSION_DB" ]]; then
        echo "  Database: $SESSION_DB"
        echo "  Size: $(du -h "$SESSION_DB" | cut -f1)"
        echo "  Modified: $(stat -f '%Sm' "$SESSION_DB" 2>/dev/null || stat -c '%y' "$SESSION_DB" 2>/dev/null)"

        # Try to get summary from cosmic-ray
        if worktree_exists; then
            echo
            echo "Results preview:"
            (cd "$WORKTREE_DIR" && uv run cr-report "$SESSION_DB" 2>/dev/null | head -20) || true
        fi
    else
        echo -e "  Status: ${YELLOW}No session database${NC}"
    fi
    echo

    # Staged changes status
    echo "Working directory:"
    if has_staged_changes; then
        echo -e "  Staged changes: ${GREEN}Yes (will be included)${NC}"
    else
        echo "  Staged changes: No"
    fi

    if ! git -C "$PROJECT_ROOT" diff --quiet; then
        echo -e "  Unstaged changes: ${YELLOW}Yes (will NOT be included)${NC}"
    else
        echo "  Unstaged changes: No"
    fi
}

# Clean up
cmd_clean() {
    info "Cleaning mutation testing artifacts"

    # Remove worktree
    if worktree_exists; then
        info "Removing worktree"
        git -C "$PROJECT_ROOT" worktree remove "$WORKTREE_DIR" --force 2>/dev/null || rm -rf "$WORKTREE_DIR"
    fi

    # Remove session files
    rm -f "$PROJECT_ROOT"/session.sqlite
    rm -f "$PROJECT_ROOT"/*-session.sqlite
    rm -f "$PROJECT_ROOT"/mutation-report.html

    success "Cleanup complete"
}

# Show usage
usage() {
    echo "Usage: $(basename "$0") <command> [options]"
    echo
    echo "Commands:"
    echo "  setup     Create/update worktree and sync dependencies"
    echo "  init      Initialize mutation testing session (includes setup)"
    echo "  exec      Execute mutation testing"
    echo "  status    Show worktree and session status"
    echo "  clean     Remove worktree and session files"
    echo
    echo "Options:"
    echo "  --fresh   Force recreation of worktree (with setup/init)"
    echo "  --resume  Skip init, continue existing session (with exec)"
}

# Main entry point
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi

    local cmd="$1"
    shift

    case "$cmd" in
        setup)
            cmd_setup "$@"
            ;;
        init)
            cmd_init "$@"
            ;;
        exec)
            cmd_exec "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        clean)
            cmd_clean "$@"
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            error "Unknown command: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
