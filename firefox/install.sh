#!/bin/bash
# Installs the optional Platinum Lavender theme (IE5 Mac layout) into a single
# chosen Firefox profile inside your home (no root, separate from ./install.sh).
#
# Discovers profiles from ~/.config/mozilla/firefox/profiles.ini (XDG) and
# ~/.mozilla/firefox/profiles.ini, prioritizing [Install*] Default= over legacy
# [Profile*] Default=1, lists them, and requires selecting one profile.
# Refuses while that profile is in use (lock / .parentlock). Journals and backs
# up existing chrome/, user.js, and prefs.js values before touching anything;
# firefox/uninstall.sh restores untouched files byte for byte and keeps later
# user edits outside its markers.
#
# usage: firefox/install.sh [--profile PROFILE] [--list] [--dry-run]
#   --profile PROFILE  target profile (index from --list, Name, folder name, or path)
#   --list             list discovered Firefox profiles and exit
#   --dry-run          only show what would be done
#   -h, --help         show this help
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
umask 022
program=firefox/install.sh
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

usage() {
    sed -n '/^# usage:/,/^# *-h, --help/s/^# \{0,1\}//p' "$0"
}

die() {
    printf '%s: %s\n' "$program" "$*" >&2
    exit 1
}

if ((EUID == 0)); then
    die "run this as your own user, not as root (everything goes into your home)"
fi

profile_arg=""
has_profile=0
list_only=0
dry_run=0

while (($# > 0)); do
    case $1 in
        --profile)
            (($# >= 2)) || { usage >&2; exit 2; }
            profile_arg=$2
            has_profile=1
            shift 2
            ;;
        --profile=*)
            profile_arg=${1#--profile=}
            has_profile=1
            shift
            ;;
        --list)
            list_only=1
            shift
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            usage >&2
            exit 2
            ;;
    esac
done

for spec in python3:python flock:util-linux; do
    cmd=${spec%%:*}
    pkg=${spec#*:}
    command -v "$cmd" > /dev/null 2>&1 ||
        die "missing required tool: $cmd (Arch package: $pkg); nothing was changed"
done

xdg_dir() {
    if [[ $1 == /* ]]; then printf '%s' "${1%/}"; else printf '%s' "$2"; fi
}

[[ ${HOME:-} == /* && -d ${HOME:-} ]] ||
    die "HOME must be your home folder (an absolute path); it's '${HOME:-}'"
home=${HOME%/}
config_home=$(xdg_dir "${XDG_CONFIG_HOME:-}" "$home/.config")
state_home=$(xdg_dir "${XDG_STATE_HOME:-}" "$home/.local/state")
for p in "$home" "$config_home" "$state_home"; do
    [[ $p != *[$'\t\n']* ]] || die "a tab or line break in '$p' isn't supported"
done
state_dir=$state_home/macos9-theme-firefox

if ((!dry_run && !list_only)); then
    [[ ! -L $state_dir ]] || die "$state_dir is a symbolic link; nothing was changed"
    mkdir -p "$state_dir"
    exec 9> "$state_dir/lock"
    flock -n 9 || die "another firefox/install.sh or firefox/uninstall.sh is running"
fi

py_args=(
    install
    --home "$home"
    --config-home "$config_home"
    --state-dir "$state_dir"
    --repo-firefox-dir "$here"
)
((has_profile)) && py_args+=(--profile "$profile_arg")
((list_only)) && py_args+=(--list)
((dry_run)) && py_args+=(--dry-run)

exec python3 -I "$here/profile_ops.py" "${py_args[@]}"
