#!/bin/bash
# Removes Platinum for Firefox from a profile, restores untouched files
# (chrome/, user.js, prefs.js) byte for byte, preserves any edits you made
# outside the macos9-theme-firefox markers, restores each managed pref's
# original value or absence directly in prefs.js, and refuses without
# overwriting if a conflict is detected.
#
# usage: firefox/uninstall.sh [--profile PROFILE] [--list] [--dry-run]
#   --profile PROFILE  installed profile to restore (index, Name, folder name, or path)
#   --list             list profiles where Platinum is currently installed
#   --dry-run          only show what would be done
#   -h, --help         show this help
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
umask 022
program=firefox/uninstall.sh
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

if [[ ! -e $state_dir && ! -L $state_dir ]]; then
    ((dry_run)) && printf 'Dry run: nothing is changed.\n'
    if ((list_only)); then
        printf 'Platinum for Firefox is not installed in any profile.\n'
    else
        printf 'Nothing to remove: Platinum for Firefox is not installed in any profile.\n'
    fi
    exit 0
fi

if ((!dry_run && !list_only)); then
    [[ ! -L $state_dir ]] || die "$state_dir is a symbolic link; nothing was changed"
    exec 9> "$state_dir/lock"
    flock -n 9 || die "another firefox/install.sh or firefox/uninstall.sh is running"
fi

py_args=(
    uninstall
    --home "$home"
    --config-home "$config_home"
    --state-dir "$state_dir"
    --state-home "$state_home"
)
((has_profile)) && py_args+=(--profile "$profile_arg")
((list_only)) && py_args+=(--list)
((dry_run)) && py_args+=(--dry-run)

rc=0
python3 -I "$here/profile_ops.py" "${py_args[@]}" || rc=$?

# If no installed profiles remain after a real uninstall, clean up the lock & empty state dir.
if ((rc == 0 && !dry_run && !list_only)); then
    exec 9>&-
    if [[ -d $state_dir && ! -d $state_dir/profiles ]]; then
        rm -f "$state_dir/lock"
        rmdir "$state_dir" 2> /dev/null || true
    fi
fi
exit "$rc"
