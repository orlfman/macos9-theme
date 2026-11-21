#!/bin/bash
# Removes what install.sh installed, puts back anything it moved aside, and,
# if you switched to the theme, puts back the config files copied before the
# switch (panels, colors, style, decoration, GTK settings, ...).
#
# Your config files as they are right now are kept first, together with the
# copy that was put back, in ~/.local/state/macos9-theme-uninstalled-DATE,
# so nothing is lost even if you changed settings while the theme was on.
# Plasma's shell is stopped while its panel layout is put back (it writes
# that file when it quits) and started again afterwards.
#
# If something can't be removed or put back (it's yours now, or in the
# way), it's left alone, the install record keeps it, and this exits 1:
# sort it out and run this again. Finished steps are never done twice.
#
# usage: uninstall.sh [--dry-run]
#   --dry-run  only show what would be done
#   -h, --help show this help
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
program=uninstall.sh
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

usage() {
    sed -n '/^# usage:/,/^# *-h, --help/s/^# \{0,1\}//p' "$0"
}

dry=0
for arg in "$@"; do
    case $arg in
        --dry-run) dry=1 ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

# shellcheck source=scripts/common.sh
source "$here/scripts/common.sh"
dry_run=$dry

refuse_root
((dry_run)) && note "Dry run: nothing is changed."
if [[ ! -e $state && ! -L $state ]]; then
    note "Nothing to remove: there's no install record in $state."
    exit 0
fi
take_lock
manifest_load
check_record_paths
remove_temporaries

if [[ ! -d $backup && ${#manifest_entries[@]} -eq 0 ]]; then
    note "Nothing to remove: there's no install record in $state."
    if ((!dry_run)); then
        # What an earlier run stopped just before removing.
        rm -f "$state/lock"
        rmdir "$state" 2> /dev/null || true
    fi
    exit 0
fi
keep_base=$state_home/macos9-theme-uninstalled-$(date +%Y%m%d-%H%M%S)
keep=$keep_base
for ((i = 2; i < 100; i++)); do
    [[ -e $keep || -L $keep ]] || break
    keep=$keep_base-$i
done

# --- 1. Config files --------------------------------------------------------

# The root a backup entry belongs to, as it was when the copy was taken.
backup_root() { # config|home
    local root
    root=$(awk -F'\t' -v base="$1" '$1 == base { print $2 }' "$backup/ROOTS" 2> /dev/null)
    [[ $root == /* && $root != *[$'\t\n']* ]] || die "$backup/ROOTS is damaged; nothing was changed"
    printf '%s' "$root"
}

# Replaces PATH with a copy of SOURCE (file or folder) under a temporary
# name first, so a failed copy never leaves PATH half written.
put_back() { # source path
    local source=$1 path=$2 parent tmp
    parent=$(dirname "$path")
    mkdir -p "$parent"
    make_temp dir "$parent"
    tmp=$made_temp
    cp -a "$source" "$tmp/item"
    rm -rf "$path"
    mv -T "$tmp/item" "$path"
    rmdir "$tmp"
    done_temp "$tmp"
}

restored=0
if [[ -d $backup ]]; then
    [[ -f $backup/ENTRIES && -f $backup/ABSENT && ! -L $backup ]] || die "$backup is damaged; nothing was changed"
    config_root=$(backup_root config)
    home_root=$(backup_root home)
    [[ $config_root == "$config_home" ]] ||
        warn "the copy was taken with the config folder $config_root (now $config_home); putting it back there"
    taken=$(backup_taken || true)
    active=$(active_lnf)
    if [[ $taken == apply || ($taken == install && $active == "$lnf_id") ]]; then
        # Each entry must lead where it did when it was copied (finding 29).
        moved=()
        while IFS=$'\t' read -r base name real; do
            case $base in config) root=$config_root ;; home) root=$home_root ;; *) die "$backup/ENTRIES is damaged; nothing was changed" ;; esac
            [[ -n $real ]] || die "$backup was made by an older version; nothing was changed"
            [[ $real == "$(real_path "$root/$name")" ]] || moved+=("$root/$name (was $real)")
        done < "$backup/ENTRIES"
        if ((${#moved[@]})); then
            printf '  %s\n' "${moved[@]}" >&2
            die "these lead somewhere else now than when your config files were copied (a folder link above them was changed). Point the link back, then run this again; nothing was changed"
        fi
        shell_stop || die "couldn't stop Plasma's shell, which has to be stopped while your panel layout is put back; nothing was changed. Try again, or log out and run uninstall.sh from a text console (Ctrl+Alt+F3)"
        # If anything below fails, Plasma's shell still comes back.
        trap 'shell_start' EXIT

        plan "keep your current config files in $keep/current"
        while IFS=$'\t' read -r base name _; do
            case $base in config) root=$config_root ;; home) root=$home_root ;; *) die "$backup/ENTRIES is damaged" ;; esac
            path=$root/$name
            if [[ -L $path ]]; then
                warn "$path is a symbolic link now; left alone"
                continue
            fi
            if [[ -e $path ]] && ((!dry_run)); then
                mkdir -p "$(dirname "$keep/current/$base/$name")"
                cp -a "$path" "$keep/current/$base/$name"
            fi
            if grep -qxF "$base	$name" "$backup/ABSENT"; then
                if [[ -e $path ]]; then
                    plan "remove $path (it wasn't there before)"
                    ((dry_run)) || rm -rf "$path"
                fi
            elif [[ -e $backup/$base/$name || -L $backup/$base/$name ]]; then
                plan "put back $path"
                ((dry_run)) || put_back "$backup/$base/$name" "$path"
            fi
        done < "$backup/ENTRIES"
        plan "move the copy that was put back to $keep/original"
        if ((!dry_run)); then
            mkdir -p "$keep"
            mv -T "$backup" "$keep/original"
        fi
        say "Put back your config files from before the switch (the copy is in $keep/original, your files from just now in $keep/current)"
        restored=1
        shell_start
        trap - EXIT
        shell_how=""
        reconfigure_kwin
        notify_style
    else
        # Never switched (or switched away again): leave the config alone.
        plan "move the unused copy of your config files to $keep/unused"
        if ((!dry_run)); then
            mkdir -p "$keep"
            mv -T "$backup" "$keep/unused"
        fi
        say "The theme isn't active, so your config files were left as they are (the copy from install time is in $keep/unused)"
    fi
fi

# --- 2. Installed files, newest first ---------------------------------------
#
# Each entry leaves the record as soon as it's done, so a second run after
# a failure never redoes a step: a file put back is never taken for the
# installed one (finding 27). What's left alone stays on the record.

entries=("${manifest_entries[@]}")
had_plasma_style=0
for ((i = ${#entries[@]} - 1; i >= 1; i--)); do
    entry=${entries[i]}
    IFS=$'\t' read -r kind path _ <<< "$entry"
    case $kind in
        file | dir)
            if ! is_target "$kind" "$path"; then
                warn "the record lists $path, which isn't a place install.sh installs to; left alone"
                continue
            fi
            if is_kind "$kind" "$path"; then
                [[ $path == */desktoptheme/* ]] && had_plasma_style=1
                plan "remove $path"
                ((dry_run)) || rm -rf "$path"
            elif [[ -e $path || -L $path ]]; then
                # Replaced since: not the installed one, so not removed.
                warn "$path isn't the $kind install.sh put there any more; left alone as yours"
            fi
            manifest_drop "$entry"
            ;;
    esac
done

# What was in the way of an install target goes back.
for entry in "${entries[@]:1}"; do
    IFS=$'\t' read -r kind path saved _ <<< "$entry"
    [[ $kind == displaced ]] || continue
    if ! is_target file "$path" && ! is_target dir "$path"; then
        warn "the record lists $path as moved aside, which isn't a place install.sh installs to; left alone"
    elif [[ $saved != "$displaced"/* || ! (-e $saved || -L $saved) ]]; then
        warn "the moved-aside copy of $path isn't in $displaced any more"
        manifest_drop "$entry"
    elif [[ -e $path || -L $path ]]; then
        warn "$path is taken by something else, so the earlier one stays in $saved; move that away and run uninstall.sh again"
    else
        plan "put back the earlier $path"
        ((dry_run)) || mv -T "$saved" "$path"
        manifest_drop "$entry"
        say "Put back the earlier $path"
    fi
done

((had_plasma_style)) && drop_plasma_caches

# Folders install.sh created, deepest first, if nothing else is in them now.
for ((i = ${#entries[@]} - 1; i >= 1; i--)); do
    entry=${entries[i]}
    IFS=$'\t' read -r kind path _ <<< "$entry"
    [[ $kind == madedir ]] || continue
    is_target_parent "$path" || continue
    if [[ ! -e $path && ! -L $path ]]; then
        manifest_drop "$entry"
    elif [[ -d $path && ! -L $path ]] && [[ -z $(ls -A "$path" 2> /dev/null) ]]; then
        plan "remove the empty folder $path"
        ((dry_run)) || rmdir "$path"
        manifest_drop "$entry"
    fi
done

if ((!dry_run)); then
    for dir in "$displaced"/*/; do
        [[ -d $dir ]] && { rmdir "$dir" 2> /dev/null || true; }
    done
    rmdir "$displaced" 2> /dev/null || true
fi

# Anything still to do keeps the record for another run.
left=0
for entry in "${manifest_entries[@]:1}"; do
    case ${entry%%	*} in file | dir | displaced | temp) left=1 ;; esac
done
if ((left)); then
    if ((dry_run)); then
        note "Dry run done: some things would be left (see the warnings above)."
        exit 0
    fi
    warn "some things were left alone (see the warnings above). The install record stays in $manifest with just those; sort them out, then run uninstall.sh again (it won't redo what's done)"
    exit 1
fi

if ((!dry_run)); then
    rm -f "$manifest" "$state/lock"
    rmdir "$state" 2> /dev/null || true
else
    plan "remove the install record $manifest"
fi
say "Removed the Platinum style, decoration, color scheme, Plasma style, global theme and login script"

if ((restored)); then
    note "Log out and back in once to finish (the window decoration, the login script and GTK apps)."
elif ((!dry_run)); then
    note "Log out and back in once to finish (the login script is gone)."
fi
((dry_run)) && note "Dry run done."
exit 0
