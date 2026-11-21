#!/bin/bash
# Removes what install.sh installed and, if install.sh --apply switched to
# the theme, puts back the config files it copied before (panels, colors,
# style, decoration, ...). Your config files as they are right now are kept
# in ~/.local/state/macos9-theme-uninstalled-DATE first, so nothing is lost
# even if you changed settings while the theme was on.
#
# usage: uninstall.sh [--dry-run]
#   --dry-run  only show what would be done
#   -h, --help show this help
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
program=uninstall.sh
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=scripts/common.sh
source "$here/scripts/common.sh"

usage() {
    sed -n '/^# usage:/,/^# *-h, --help/s/^# \{0,1\}//p' "$0"
}

for arg in "$@"; do
    case $arg in
        --dry-run) dry_run=1 ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

refuse_root
((dry_run)) && note "Dry run: nothing is changed."
manifest_load

restored=0
if [[ -d $backup ]]; then
    keep=$state_home/macos9-theme-uninstalled-$(date +%Y%m%d-%H%M%S)
    if ((dry_run)); then
        say "  would keep your current config files in $keep"
    else
        mkdir -p "$keep"
        for file in "${backup_files[@]}" "${backup_dirs[@]}"; do
            [[ -e $config_home/$file ]] && cp -a "$config_home/$file" "$keep/$file"
        done
        say "Kept your current config files in $keep"
    fi
    for file in "${backup_files[@]}" "${backup_dirs[@]}"; do
        if grep -qx "$file" "$backup/ABSENT" 2> /dev/null; then
            [[ -e $config_home/$file ]] && run rm -rf "${config_home:?}/$file"
        elif [[ -e $backup/$file ]]; then
            run rm -rf "${config_home:?}/$file"
            run cp -a "$backup/$file" "$config_home/$file"
        fi
    done
    run rm -rf "$backup"
    restored=1
    say "Put back your config files from before install.sh --apply"
fi

# Remove what the record lists, newest first.
for ((i = ${#manifest_entries[@]} - 1; i >= 0; i--)); do
    IFS=$'\t' read -r kind path <<< "${manifest_entries[i]}"
    case $kind in
        file | dir) [[ -e $path ]] && run rm -rf "$path" ;;
        *) warn "unknown record entry: ${manifest_entries[i]}" ;;
    esac
done
drop_plasma_caches
if ((!dry_run)); then
    rm -f "$manifest"
    rmdir "$state" 2> /dev/null || true
    # Folders install.sh made, if nothing else is in them now.
    rmdir "$plugins/styles" "$plugins/org.kde.kdecoration3" "$plugins" "$(dirname "$plugins")" \
        "$(dirname "$env_script")" "$(dirname "$(dirname "$env_script")")" 2> /dev/null || true
fi
say "Removed the Platinum style, decoration, color scheme, Plasma style, global theme and login script"

if ((restored)); then
    reconfigure_kwin
    notify_style
    # Plasma reads the restored panel layout when it starts again.
    if have systemctl && systemctl --user is-active --quiet plasma-plasmashell.service 2> /dev/null; then
        run systemctl --user restart plasma-plasmashell.service
        say "Restarted Plasma's shell for your panels"
    else
        note "Restart Plasma (or log out and back in) to get your panels back."
    fi
fi
if ((dry_run)); then
    note "Dry run done."
else
    say "Done. Log out and back in once to finish (the login script is gone)."
fi
