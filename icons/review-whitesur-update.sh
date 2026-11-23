#!/usr/bin/env bash
# Reviews a candidate upstream WhiteSur tag or commit without executing its
# install.sh and writes a proposed pin file for manual review.
#   usage: review-whitesur-update.sh TAG_OR_COMMIT [UPSTREAM_CLONE] [PROPOSED_PIN_OUT]
#
# Never modifies the upstream clone, never executes the candidate install.sh,
# and never modifies icons/whitesur-pin.json.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
umask 022

SAFE_PATH="/usr/local/bin:/usr/bin:/bin"

die() {
    printf 'review-whitesur-update: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
usage: review-whitesur-update.sh TAG_OR_COMMIT [UPSTREAM_CLONE] [PROPOSED_PIN_OUT]

Exports TAG_OR_COMMIT from UPSTREAM_CLONE into a private disposable directory,
reports changes in install.sh, the 25 purple color inputs, launcher files,
license files, symlinks, and SVG namespace exceptions, and writes a proposed
pin JSON to PROPOSED_PIN_OUT (default: dev/build/whitesur-pin-proposed.json).

Never executes the candidate upstream install.sh and never modifies
icons/whitesur-pin.json.
EOF
}

if [[ $# -eq 1 && ( $1 == "-h" || $1 == "--help" ) ]]; then
    usage
    exit 0
fi

if [[ $# -lt 1 || $# -gt 3 ]]; then
    usage >&2
    exit 2
fi

for arg in "$@"; do
    [[ -n $arg ]] || die "arguments must not be empty"
    [[ $arg != -* ]] || die "unrecognized option: $arg"
    [[ $arg != *[$'\t\n\r']* ]] || die "arguments containing tabs or line breaks are not supported"
done

ref=$1
script_path=$(env -i PATH="$SAFE_PATH" LC_ALL=C readlink -f -- "$0")
here=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$script_path")
project=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$here")
generator="$here/whitesur-lavender.py"

if [[ $# -ge 2 ]]; then
    upstream_arg=$2
else
    upstream_arg="$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$project")/WhiteSur-icon-theme"
fi

if [[ $# -ge 3 ]]; then
    out_arg=$3
else
    out_arg="$project/dev/build/whitesur-pin-proposed.json"
fi

upstream=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$upstream_arg")
proposed_out=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$out_arg")
custom_arg=${M9_ICON_CUSTOM_DIR:-$here/custom}
[[ $custom_arg != *[$'\t\n\r']* ]] || die "M9_ICON_CUSTOM_DIR containing tabs or line breaks is not supported"
custom_dir=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$custom_arg")

[[ -d $upstream ]] || die "upstream clone directory does not exist: $upstream"
target_commit=$(env -i PATH="$SAFE_PATH" LC_ALL=C git -C "$upstream" rev-parse --verify "${ref}^{commit}" 2>/dev/null) \
    || die "could not resolve ref '$ref' to a commit in $upstream"

pinned_commit=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I "$generator" --print-pin)

tmp_base_arg=${TMPDIR:-/tmp}
tmp_base=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$tmp_base_arg")
[[ -d $tmp_base ]] || die "TMPDIR is not an existing directory: $tmp_base"

work=$(env -i PATH="$SAFE_PATH" LC_ALL=C mktemp -d "$tmp_base/whitesur-review.XXXXXX")
chmod 0700 -- "$work"
trap 'rm -rf -- "$work"' EXIT

cand_dir="$work/candidate"
old_dir="$work/pinned"
home_dir="$work/home"
work_tmp="$work/tmp"
mkdir -p -- "$cand_dir" "$home_dir" "$work_tmp"
chmod 0700 -- "$home_dir" "$work_tmp"

env -i PATH="$SAFE_PATH" LC_ALL=C \
    git -C "$upstream" archive --format=tar "$target_commit" \
    | env -i PATH="$SAFE_PATH" LC_ALL=C tar -x -C "$cand_dir"

extra_args=()
if env -i PATH="$SAFE_PATH" LC_ALL=C git -C "$upstream" cat-file -e "${pinned_commit}^{commit}" 2>/dev/null; then
    mkdir -p -- "$old_dir"
    env -i PATH="$SAFE_PATH" LC_ALL=C \
        git -C "$upstream" archive --format=tar "$pinned_commit" \
        | env -i PATH="$SAFE_PATH" LC_ALL=C tar -x -C "$old_dir"
    extra_args=("$old_dir")
fi

env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$home_dir" TMPDIR="$work_tmp" \
    python3 -I "$generator" --review-update \
    "$cand_dir" "$target_commit" "$ref" "$proposed_out" "$project" "$upstream" "$custom_dir" "${extra_args[@]}"
