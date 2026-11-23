#!/usr/bin/env bash
# Safely manages the local bare git cache of upstream WhiteSur at the exact
# reviewed commit, without running any upstream code or git hooks.
#
# usage:
#   fetch-whitesur.sh [--check-only] PINNED_COMMIT CACHE_DIR [REMOTE_URL]
#
# Behaviour:
#   - If CACHE_DIR exists: verifies it is a non-symlink valid git repo at
#     PINNED_COMMIT and passes full `git fsck --full --no-progress` (#121).
#     Prints CACHED and exits 0. Refuses corrupt caches, symlinked caches, or
#     caches at the wrong commit with a clear error (exit 1).
#   - If CACHE_DIR does not exist:
#       * With --check-only: prints NEEDS_FETCH and exits 0 without writing
#         anything or touching the network.
#       * Otherwise: acquires a per-cache flock (#116), cleans only verifiably
#         owned abandoned temp dirs recorded by this script, fetches ONLY
#         PINNED_COMMIT into a private sibling bare temp dir, verifies
#         FETCH_HEAD == PINNED_COMMIT and `git fsck --full --no-progress`, sets
#         detached HEAD, and atomically moves into CACHE_DIR. Prints FETCHED.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
umask 022

SAFE_PATH="/usr/local/bin:/usr/bin:/bin"
DEFAULT_REMOTE="https://github.com/vinceliuice/WhiteSur-icon-theme.git"

die() {
    printf 'fetch-whitesur: %s\n' "$*" >&2
    exit 1
}

check_only=0
if [[ $# -ge 1 && $1 == "--check-only" ]]; then
    check_only=1
    shift
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
    die "usage: fetch-whitesur.sh [--check-only] PINNED_COMMIT CACHE_DIR [REMOTE_URL]"
fi

pinned_commit=$1
cache_arg=$2
remote_url=${3:-$DEFAULT_REMOTE}

[[ $pinned_commit =~ ^[0-9a-f]{40}$ ]] || die "invalid pinned commit: $pinned_commit"
[[ -n $cache_arg && $cache_arg != *[$'\t\n\r']* ]] || die "invalid cache path"
[[ -n $remote_url && $remote_url != *[$'\t\n\r']* ]] || die "invalid remote URL"

PATH="$SAFE_PATH" command -v python3 >/dev/null 2>&1 ||
    die "missing required dependency: python3 (Arch package: python); nothing was changed"
PATH="$SAFE_PATH" command -v git >/dev/null 2>&1 ||
    die "missing required dependency: git (Arch package: git); nothing was changed"
PATH="$SAFE_PATH" command -v flock >/dev/null 2>&1 ||
    die "missing required dependency: flock (Arch package: util-linux); nothing was changed"

cache_dir=$(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I -c 'import os, sys; print(os.path.abspath(sys.argv[1]))' "$cache_arg")

# Reject any symlink in the existing ancestor chain or at cache_dir itself.
env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I - "$cache_dir" <<'PY'
import os, sys
from pathlib import Path
p = Path(sys.argv[1])
cur = Path("/")
for part in p.parts[1:]:
    cur = cur / part
    if os.path.lexists(cur):
        if cur.is_symlink():
            print(f"fetch-whitesur: cache path traverses symbolic link {cur}; nothing was changed", file=sys.stderr)
            raise SystemExit(1)
    else:
        break
PY

verify_existing_cache() {
    local target=$1
    if [[ -L $target || ! -d $target ]]; then
        die "cached WhiteSur path $target is not a directory (corrupt cache). Remove it (rm -rf '$target') and try again; nothing was changed"
    fi
    local cache_ceiling git_dir_resolved actual_head
    cache_ceiling=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$target")
    git_dir_resolved=$(env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$cache_ceiling" \
        git -C "$target" rev-parse --absolute-git-dir 2> /dev/null || true)
    if [[ -z $git_dir_resolved || ( $git_dir_resolved != "$target" && $git_dir_resolved != "$target/.git" ) ]]; then
        die "cached WhiteSur repository at $target is corrupt (not a valid git repository). Remove it (rm -rf '$target') and try again; nothing was changed"
    fi
    actual_head=$(env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$cache_ceiling" \
        git -C "$target" rev-parse --verify "HEAD^{commit}" 2> /dev/null || true)
    if [[ -z $actual_head ]]; then
        die "cached WhiteSur repository at $target is corrupt or empty (missing HEAD commit). Remove it (rm -rf '$target') and try again; nothing was changed"
    fi
    if [[ $actual_head != "$pinned_commit" ]]; then
        die "cached WhiteSur repository at $target is at commit $actual_head, expected reviewed pin $pinned_commit. Remove the cache (rm -rf '$target') to fetch the reviewed commit, or set M9_WHITESUR_UPSTREAM; nothing was changed"
    fi
    # Full object/blob/tree/commit integrity verification (#121).
    if ! env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$cache_ceiling" \
        git -C "$target" fsck --full --no-progress > /dev/null 2>&1; then
        die "cached WhiteSur repository at $target failed full git object integrity check (corrupt cache). Remove it (rm -rf '$target') and try again; nothing was changed"
    fi
    if ! env -i PATH="$SAFE_PATH" LC_ALL=C GIT_CEILING_DIRECTORIES="$cache_ceiling" \
        git -C "$target" cat-file -e "${pinned_commit}^{tree}" 2> /dev/null; then
        die "cached WhiteSur repository at $target is missing commit tree objects (corrupt cache). Remove it (rm -rf '$target') and try again; nothing was changed"
    fi
}

if [[ -e $cache_dir || -L $cache_dir ]]; then
    verify_existing_cache "$cache_dir"
    printf 'CACHED\n'
    exit 0
fi

if ((check_only)); then
    printf 'NEEDS_FETCH\n'
    exit 0
fi

# Validate TMPDIR BEFORE locking or allocating any persistent cache entries (#137).
tmp_base=${TMPDIR:-/tmp}
[[ -n $tmp_base && $tmp_base != *[$'\t\n\r']* && -d $tmp_base && -w $tmp_base ]] ||
    die "TMPDIR is not an existing writable directory: ${tmp_base:-empty}; nothing was changed"

# Acquire mandatory per-cache flock in a private uid-owned lock directory (#116, #135).
# Never delete unrelated sibling directories such as .WhiteSur-fetch.mydata.
read -r lock_file pending_file < <(env -i PATH="$SAFE_PATH" LC_ALL=C python3 -I - "$cache_dir" <<'PY'
import hashlib, os, stat, sys
from pathlib import Path
uid = os.getuid()
key = hashlib.sha256(sys.argv[1].encode("utf-8")).hexdigest()
lock_dir = Path(f"/tmp/macos9-whitesur-locks-{uid}")
if not os.path.lexists(lock_dir):
    os.mkdir(lock_dir, 0o700)
st = os.lstat(lock_dir)
if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode) or st.st_uid != uid:
    print(f"fetch-whitesur: unsafe lock directory {lock_dir}", file=sys.stderr)
    raise SystemExit(1)
os.chmod(lock_dir, 0o700)
print(lock_dir / f"fetch-{key}.lock", lock_dir / f"fetch-{key}.pending")
PY
)

exec 8> "$lock_file"
env -i PATH="$SAFE_PATH" LC_ALL=C flock 8 || die "couldn't acquire cache lock $lock_file; nothing was changed"

# Re-check under the lock in case a concurrent run just populated the cache.
if [[ -e $cache_dir || -L $cache_dir ]]; then
    verify_existing_cache "$cache_dir"
    printf 'CACHED\n'
    exit 0
fi

parent_dir=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$cache_dir")

# Clean ONLY an abandoned temp dir previously recorded in our uid-owned pending
# file under this lock (and carrying our own marker), never arbitrary globs (#116).
if [[ -f $pending_file && ! -L $pending_file ]]; then
    stale_path=$(< "$pending_file")
    if [[ -n $stale_path && $(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$stale_path") == "$parent_dir" ]]; then
        stale_base=$(env -i PATH="$SAFE_PATH" LC_ALL=C basename -- "$stale_path")
        if [[ $stale_base == .WhiteSur-fetch.* && -d $stale_path && ! -L $stale_path && -f $stale_path/.macos9-whitesur-fetch-tmp && ! -L $stale_path/.macos9-whitesur-fetch-tmp ]]; then
            rm -rf -- "$stale_path"
        fi
    fi
    rm -f -- "$pending_file"
fi

# Install cleanup trap BEFORE the first persistent allocation (#137).
work_home=""
fetch_tmp=""
created_dirs=()
published=0
cleanup() {
    [[ -z ${work_home:-} ]] || rm -rf -- "$work_home"
    if ((!published)); then
        [[ -z ${fetch_tmp:-} ]] || rm -rf -- "$fetch_tmp"
        rm -f -- "$pending_file"
        local i
        for ((i = ${#created_dirs[@]} - 1; i >= 0; i--)); do
            rmdir -- "${created_dirs[i]}" 2> /dev/null || true
        done
    fi
}
trap cleanup EXIT

work_home=$(env -i PATH="$SAFE_PATH" LC_ALL=C mktemp -d "$tmp_base/whitesur-fetch-home.XXXXXX")
chmod 0700 -- "$work_home"

# Record any directories we create so a failed fetch leaves zero footprint.
cur_dir=$parent_dir
while [[ -n $cur_dir && $cur_dir != / && ! -e $cur_dir && ! -L $cur_dir ]]; do
    created_dirs=("$cur_dir" "${created_dirs[@]}")
    cur_dir=$(env -i PATH="$SAFE_PATH" LC_ALL=C dirname -- "$cur_dir")
done
for d in "${created_dirs[@]}"; do
    mkdir -- "$d"
done

fetch_tmp=$(env -i PATH="$SAFE_PATH" LC_ALL=C mktemp -d "$parent_dir/.WhiteSur-fetch.XXXXXX")
chmod 0700 -- "$fetch_tmp"
printf 'macos9-fetch-tmp\n' > "$fetch_tmp/.macos9-whitesur-fetch-tmp"
printf '%s\n' "$fetch_tmp" > "$pending_file"

env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$work_home" GIT_TERMINAL_PROMPT=0 \
    git -c core.hooksPath=/dev/null -c core.symlinks=false init --bare --quiet "$fetch_tmp" \
    || die "failed to initialize temporary WhiteSur cache; nothing was changed"

fetch_err="$work_home/fetch.err"
if ! env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$work_home" GIT_TERMINAL_PROMPT=0 \
    git -C "$fetch_tmp" -c core.hooksPath=/dev/null -c core.symlinks=false \
    fetch --depth 1 --no-tags --quiet -- "$remote_url" "$pinned_commit" 2> "$fetch_err"; then
    err_detail=$(head -n 3 "$fetch_err" 2> /dev/null | tr '\n' ' ')
    die "could not fetch WhiteSur commit $pinned_commit from $remote_url (offline or unreachable: ${err_detail:-fetch failed}). Connect to the network or point M9_WHITESUR_UPSTREAM at a local WhiteSur clone; nothing was changed"
fi

fetched=$(env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$work_home" \
    git -C "$fetch_tmp" rev-parse --verify "FETCH_HEAD^{commit}" 2> /dev/null || true)
if [[ $fetched != "$pinned_commit" ]]; then
    die "fetched commit (${fetched:-none}) does not match reviewed pin $pinned_commit; refusing to cache; nothing was changed"
fi

if ! env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$work_home" \
    git -C "$fetch_tmp" fsck --full --no-progress > /dev/null 2>&1; then
    die "fetched WhiteSur commit $pinned_commit failed full git object integrity check (corrupt remote object); nothing was changed"
fi

env -i PATH="$SAFE_PATH" LC_ALL=C HOME="$work_home" \
    git -C "$fetch_tmp" update-ref --no-deref HEAD "$pinned_commit" \
    || die "failed to set HEAD in WhiteSur cache; nothing was changed"

rm -f -- "$fetch_tmp/.macos9-whitesur-fetch-tmp"
chmod 0755 -- "$fetch_tmp"
mv -T -- "$fetch_tmp" "$cache_dir"
published=1
rm -f -- "$pending_file"
printf 'FETCHED\n'
