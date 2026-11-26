#!/usr/bin/env bash
# Builds WhiteSur-lavender and -light in private staging, verifies all
# two themes together, and publishes atomically without touching the live
# desktop.
#   usage: build-whitesur-lavender.sh [UPSTREAM_CLONE] [OUTPUT_DIR]
#
# SPDX-License-Identifier: BSD-2-Clause
# Note: this license covers this script only. Derived WhiteSur icon artwork
# built by this script remains GNU GPL v3 only (GPL-3.0-only, per upstream
# COPYING and AUTHORS; no later-version grant is evidenced).
set -euo pipefail
umask 022

SAFE_PATH="/usr/local/bin:/usr/bin:/bin"

die() {
    printf 'build-whitesur-lavender: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
usage: build-whitesur-lavender.sh [UPSTREAM_CLONE] [OUTPUT_DIR]

Builds WhiteSur-lavender and WhiteSur-lavender-light
from the reviewed upstream WhiteSur commit into private staging, verifies all
two themes together, and publishes atomically to OUTPUT_DIR.
EOF
}

if [[ $# -eq 1 && ( $1 == "-h" || $1 == "--help" ) ]]; then
    usage
    exit 0
fi

if [[ $# -gt 2 ]]; then
    die "expected at most 2 arguments (UPSTREAM_CLONE and OUTPUT_DIR)"
fi

for arg in "$@"; do
    [[ -n $arg ]] || die "arguments must not be empty"
    [[ $arg != -* ]] || die "unrecognized option: $arg"
    [[ $arg != *[$'\t\n\r']* ]] || die "paths containing tabs or line breaks are not supported"
done

script_path=$(env -i PATH="$SAFE_PATH" LC_ALL=C readlink -f -- "$0")
here=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$script_path")
project=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$here")
generator="$here/whitesur-lavender.py"

if [[ $# -ge 1 ]]; then
    upstream_arg=$1
else
    upstream_arg="$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$project")/WhiteSur-icon-theme"
fi

if [[ $# -ge 2 ]]; then
    out_arg=$2
else
    out_arg="$project/dev/build/icons"
fi

# Resolve caller paths once relative to the caller's working directory (#104).
PATH="$SAFE_PATH" command -v python3 >/dev/null 2>&1 ||
    die "missing required dependency: python3 >= 3.11 (Arch package: python); nothing was changed"
upstream=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$upstream_arg")
out=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$out_arg")
custom_arg=${M9_ICON_CUSTOM_DIR:-$here/custom}
[[ $custom_arg != *[$'\t\n\r']* ]] || die "M9_ICON_CUSTOM_DIR containing tabs or line breaks is not supported"
custom_dir=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$custom_arg")

# Preflight every required tool/module before touching git, locks, or temp dirs (#118).
env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I "$generator" --preflight "$custom_dir"

pinned_commit=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I "$generator" --print-pin)
[[ $pinned_commit =~ ^[0-9a-f]{40}$ ]] || die "invalid pinned commit from generator: $pinned_commit"

# Verify upstream clone and exact reviewed full commit before any writes (#103, #143).
[[ -d $upstream ]] || die "upstream clone directory does not exist: $upstream"
upstream=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$upstream")
upstream_ceiling=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$upstream")
upstream_git_dir=$(env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$upstream_ceiling" \
    git -C "$upstream" rev-parse --absolute-git-dir 2>/dev/null || true)
[[ -n $upstream_git_dir && ( $upstream_git_dir == "$upstream" || $upstream_git_dir == "$upstream/.git" ) ]] \
    || die "not a valid git repository: $upstream"
head_commit=$(env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$upstream_ceiling" \
    git -C "$upstream" rev-parse --verify "HEAD^{commit}" 2>/dev/null) \
    || die "not a valid git repository: $upstream"
if [[ $head_commit != "$pinned_commit" ]]; then
    die "upstream HEAD ($head_commit) does not match reviewed pin ($pinned_commit)"
fi
env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$upstream_ceiling" \
    git -C "$upstream" cat-file -e "${pinned_commit}^{commit}" 2>/dev/null \
    || die "pinned commit $pinned_commit not found in $upstream"

# Fail fast if destination is symlinked, unsafe, trackable, or unowned (#101)
# or if the tracked custom icon layer contains invalid files/aliases.
out=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I "$generator" --check-dest "$out" "$project" "$upstream")
env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I "$generator" --validate-custom "$custom_dir"

# Respect caller TMPDIR (including spaces, #104), defaulting to /tmp.
tmp_base_arg=${TMPDIR:-/tmp}
[[ -n $tmp_base_arg ]] || die "TMPDIR must not be empty"
[[ $tmp_base_arg != *[$'\t\n\r']* ]] || die "TMPDIR containing tabs or line breaks is not supported"
tmp_base=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$tmp_base_arg")
[[ -d $tmp_base ]] || die "TMPDIR is not an existing directory: $tmp_base"

work=$(env -i PATH="$SAFE_PATH" LC_ALL=C mktemp -d "$tmp_base/whitesur-lavender.XXXXXX")
chmod 0700 -- "$work"
trap 'rm -rf -- "$work"' EXIT

export_dir="$work/export"
stage_dir="$work/stage"
home_dir="$work/home"
xdg_data="$work/xdg-data"
xdg_config="$work/xdg-config"
xdg_cache="$work/xdg-cache"
xdg_state="$work/xdg-state"
xdg_runtime="$work/xdg-runtime"
work_tmp="$work/tmp"

mkdir -p -- "$export_dir" "$stage_dir" "$home_dir" "$xdg_data" "$xdg_config" "$xdg_cache" "$xdg_state" "$xdg_runtime" "$work_tmp"
chmod 0700 -- "$home_dir" "$xdg_runtime" "$work_tmp"

# Archive only the verified pinned full commit, never HEAD (#103).
env -i PATH="$SAFE_PATH" LC_ALL=C \
    git -C "$upstream" archive --format=tar "$pinned_commit" \
    | env -i PATH="$SAFE_PATH" LC_ALL=C tar -x -C "$export_dir"

# Validate inputs, generate Lavender SVGs, patch install.sh, launcher, and SVG namespaces.
env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$home_dir" TMPDIR="$work_tmp" \
    python3 -I "$generator" "$export_dir"

# Run the reviewed upstream installer in a minimal explicit environment (#102, #108).
(
    cd -- "$export_dir"
    env -i \
        PATH="$SAFE_PATH" \
        LC_ALL=C \
        LANG=C \
        TERM=dumb \
        HOME="$home_dir" \
        XDG_DATA_HOME="$xdg_data" \
        XDG_CONFIG_HOME="$xdg_config" \
        XDG_CACHE_HOME="$xdg_cache" \
        XDG_STATE_HOME="$xdg_state" \
        XDG_RUNTIME_DIR="$xdg_runtime" \
        TMPDIR="$work_tmp" \
        /usr/bin/bash --noprofile --norc ./install.sh -d "$stage_dir" -n WhiteSur -t lavender -p
)

# Apply tracked custom icon overrides/additions/aliases and regenerate caches.
env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$home_dir" TMPDIR="$work_tmp" \
    python3 -I "$generator" --apply-custom "$stage_dir" "$custom_dir"

# Verify the complete staged themes before touching OUTPUT_DIR (#101, #102, #105-#109, #111).
env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$home_dir" TMPDIR="$work_tmp" \
    python3 -I "$generator" --verify "$stage_dir" "$export_dir" "$custom_dir"

# Atomically publish with destination lock, ownership check, and rollback (#101).
env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$home_dir" TMPDIR="$work_tmp" \
    python3 -I "$generator" --publish "$stage_dir" "$out" "$project" "$upstream"

printf 'Built WhiteSur-lavender and WhiteSur-lavender-light from WhiteSur %s in %s\n' \
    "$pinned_commit" "$out"
