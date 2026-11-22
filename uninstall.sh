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
# A shell an earlier run stopped and couldn't start again (finding 38).
shell_failed=0
if ! shell_resume; then
    warn "$shell_failed_message"
    shell_failed=1
fi

if [[ ! -d $backup && ${#manifest_entries[@]} -eq 0 ]]; then
    ((shell_failed)) && exit 1
    ((shell_resumed)) || note "Nothing to remove: there's no install record in $state."
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
        # The copy must be whole and unchanged (finding 36).
        # Every file in it, inside copied folders too (finding 40), and the
        # checksum list itself must be readable.
        damaged=()
        declare -A missing=()
        while IFS=$'\t' read -r base name _; do
            grep -qxF "$base	$name" "$backup/ABSENT" && continue
            if [[ ! -e $backup/$base/$name ]]; then
                damaged+=("$backup/$base/$name is missing")
                missing[$base/$name]=1
            fi
        done < "$backup/ENTRIES"
        if [[ ! -f $backup/SUMS ]]; then
            damaged+=("$backup/SUMS is missing")
        else
            # Every file in the copy is on the list (a cut-short list is
            # caught), every listed one is there and unchanged. An empty list
            # is right when none of the files existed (finding 50).
            declare -A listed=()
            sums_line='^(\\?)[0-9a-f]{64}  (.+)$'
            while IFS= read -r line; do
                [[ -n $line ]] || continue
                # (sha256sum escapes a name with \ or a line break in it:
                # a \ before the line, \\ and \n in the name; finding 57)
                if [[ $line =~ $sums_line ]]; then
                    name=${BASH_REMATCH[2]}
                    [[ -n ${BASH_REMATCH[1]} ]] && printf -v name '%b' "$name"
                    listed[$name]=1
                else
                    damaged+=("$backup/SUMS has a damaged line")
                fi
            done < "$backup/SUMS"
            while IFS= read -r -d '' file; do
                [[ -n ${listed[$file]:-} ]] || damaged+=("$backup/$file isn't on the checksum list")
            done < <(cd "$backup" && find config home -type f -print0 2> /dev/null)
            if ((${#listed[@]})); then
                if ! sums_out=$(cd "$backup" && LC_ALL=C sha256sum --strict --quiet -c SUMS 2> /dev/null); then
                    [[ -n $sums_out ]] || damaged+=("$backup/SUMS could not be verified")
                fi
                while IFS= read -r line; do
                    case $line in
                        '') ;;
                        *': FAILED open or read') [[ -n ${missing[${line%: FAILED open or read}]:-} ]] ||
                            damaged+=("$backup/${line%: FAILED open or read} is missing") ;;
                        *': FAILED') damaged+=("$backup/${line%: FAILED} was changed") ;;
                        *) damaged+=("$backup/SUMS: $line") ;;
                    esac
                done <<< "$sums_out"
            fi
        fi
        if ((${#damaged[@]})); then
            printf '  %s\n' "${damaged[@]}" >&2
            die "the copy of your config files is incomplete or was changed; nothing was changed. To remove the theme without putting back your config files, move $backup somewhere else and run uninstall.sh again"
        fi
        shell_stop || die "couldn't stop Plasma's shell, which has to be stopped while your panel layout is put back; nothing was changed. Try again, or log out and run uninstall.sh from a text console (Ctrl+Alt+F3)"
        # If anything below fails, Plasma's shell still comes back (or the
        # next run starts it).
        trap 'shell_start || warn "$shell_failed_message"' EXIT

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
        shell_start || shell_failed=1 # (said at the end)
        trap - EXIT
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

# Read the selected image in each desktop's active wallpaper plugin. The
# running shell may have a selection it has not written to disk yet.
desktop_wallpaper_images() {
    local file=$1 id ids plugin image
    if ((!restored)) && shell_running_on_bus; then
        qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript '
            print(desktops().map(function (d) {
                var plugin = d.wallpaperPlugin;
                if (plugin !== "org.kde.image" && plugin !== "org.kde.slideshow") return "";
                d.currentConfigGroup = ["Wallpaper", plugin, "General"];
                return d.readConfig("Image", "");
            }).filter(Boolean).join("\n"));'
        return
    fi
    [[ -e $file || -L $file ]] || return 0
    [[ -f $file && -r $file ]] && have kreadconfig6 || return 1
    ids=$(sed -nE 's/^\[Containments\]\[([0-9]+)\]\[Wallpaper\].*/\1/p' "$file" | sort -u) || return 1
    for id in $ids; do
        plugin=$(kreadconfig6 --file "$file" --group Containments --group "$id" --key wallpaperplugin) || return 1
        case $plugin in
            org.kde.image | org.kde.slideshow)
                image=$(kreadconfig6 --file "$file" --group Containments --group "$id" \
                    --group Wallpaper --group "$plugin" --group General --key Image) || return 1
                printf '%s\n' "$image"
                ;;
        esac
    done
}

# The picker can store a package directory or an individual image. Convert
# local file URLs (including percent escapes) before comparing paths.
local_wallpaper_path() {
    local value=$1 tail="" decoded="" escape char
    case $value in
        file:///*) tail=${value#file://} ;;
        file://localhost/*) tail=${value#file://localhost} ;;
        file://*) return 1 ;;
        file:/*) tail=${value#file:} ;;
        /*) realpath -m -- "$value"; return ;;
        *) return 1 ;;
    esac
    tail=${tail%%[?#]*}
    while [[ $tail =~ %[[:xdigit:]]{2} ]]; do
        escape=${BASH_REMATCH[0]}
        [[ $escape != %00 ]] || return 1
        printf -v char '%b' "\\x${escape:1}"
        decoded+=${tail%%"$escape"*}$char
        tail=${tail#*"$escape"}
    done
    realpath -m -- "$decoded$tail"
}

declare -A kept_wallpapers=()
wallpaper_config=$config_home/plasma-org.kde.plasma.desktop-appletsrc
if ((restored && dry_run)) && [[ $config_root == "$config_home" && ! -L $wallpaper_config ]]; then
    wallpaper_config=$backup/config/plasma-org.kde.plasma.desktop-appletsrc
fi
wallpaper_targets=()
for wallpaper_id in "${wallpaper_ids[@]}"; do
    path=$data/wallpapers/$wallpaper_id
    if [[ -d $path && ! -L $path ]] && manifest_lists dir "$path"; then
        wallpaper_targets+=("$path")
    fi
done
if ((${#wallpaper_targets[@]})); then
    if selections=$(desktop_wallpaper_images "$wallpaper_config"); then
        while IFS= read -r selection; do
            selected_path=$(local_wallpaper_path "$selection") || continue
            for path in "${wallpaper_targets[@]}"; do
                package_path=$(realpath -m -- "$path")
                if [[ $selected_path == "$package_path" || $selected_path == "$package_path"/* ]]; then
                    kept_wallpapers[$path]=selected
                fi
            done
        done <<< "$selections"
    else
        for path in "${wallpaper_targets[@]}"; do
            kept_wallpapers[$path]=unknown
        done
    fi
fi
for path in "${!kept_wallpapers[@]}"; do
    if [[ ${kept_wallpapers[$path]} == selected ]]; then
        warn "$path is still selected in Plasma. Change that wallpaper in Plasma and run uninstall.sh again."
    else
        warn "couldn't check Plasma's wallpaper selections. Keeping $path. Run uninstall.sh again when Plasma's selection can be read."
    fi
done

# --- 2. Installed files, newest first ---------------------------------------
#
# Each entry leaves the record as soon as it's done, so a second run after
# a failure never redoes a step: a file put back is never taken for the
# installed one (finding 27). What's left alone stays on the record.

entries=("${manifest_entries[@]}")
had_plasma_style=0
# Only files whose content is what install.sh put there are removed; what
# you added or changed stays (finding 35). Track the simulated occupancy
# of targets through removal and restoration for a dry run.
index_sums
declare -A planned_path=()
for ((i = ${#entries[@]} - 1; i >= 1; i--)); do
    entry=${entries[i]}
    IFS=$'\t' read -r kind path _ <<< "$entry"
    [[ $kind == file || $kind == dir || $kind == link ]] || continue
    [[ -z ${kept_wallpapers[$path]:-} ]] || continue
    if ! is_target "$kind" "$path"; then
        warn "the record lists $path, which isn't a place install.sh installs to; left alone"
        continue
    fi
    if [[ ! -e $path && ! -L $path ]]; then
        manifest_drop "$entry"
        continue
    fi
    if ! is_kind "$kind" "$path"; then
        warn "$path isn't the $kind install.sh put there any more; left alone as yours"
        manifest_drop "$entry"
        continue
    fi
    [[ $path == */desktoptheme/* ]] && had_plasma_style=1
    if [[ $kind == link ]]; then
        # Removed only while it points where install.sh made it point.
        if installed_link "$path"; then
            plan "remove the link $path"
            ((dry_run)) || rm -f "$path"
            planned_path[$path]=removed
        else
            warn "$path points somewhere else now; left alone as yours"
        fi
        manifest_drop "$entry"
        continue
    fi
    if [[ $kind == file ]]; then
        if installed_file "$path"; then
            plan "remove $path"
            ((dry_run)) || rm -f "$path"
            planned_path[$path]=removed
        else
            warn "$path was changed since it was installed; left alone as yours"
        fi
        manifest_drop "$entry"
        continue
    fi
    # A folder: its installed files, then the folders that held them.
    our_dirs "$path"
    kept=()
    while IFS= read -r -d '' item; do
        if installed_file "$item"; then
            ((dry_run)) || rm -f "$item"
        else
            kept+=("${item#"$path"/}")
        fi
    done < <(find "$path" -mindepth 1 ! -type d -print0)
    while IFS= read -r -d '' item; do
        [[ -n ${our_dir[$item]:-} ]] || kept+=("${item#"$path"/}/")
    done < <(find "$path" -mindepth 1 -type d -print0)
    if ((${#kept[@]} == 0)); then
        plan "remove $path"
        ((dry_run)) || rm -rf "$path"
        planned_path[$path]=removed
    else
        plan "remove the installed files in $path"
        if ((!dry_run)); then
            while IFS= read -r -d '' item; do
                [[ -n ${our_dir[$item]:-} ]] && rmdir "$item" 2> /dev/null || true
            done < <(find "$path" -mindepth 1 -depth -type d -print0)
        fi
        warn "kept what you added or changed in $path: ${kept[*]:0:5}$( ((${#kept[@]} > 5)) && printf ' ...')"
    fi
    manifest_drop "$entry"
done

# What was in the way of an install target goes back. If more than one
# thing was moved aside from the same place (you changed the installed file
# and installed again), the one from before the first install goes back and
# the later ones are kept in the dated folder; the later ones go first, so
# a second run after an interruption can't mix them up (finding 39).
declare -A first_aside=()
for entry in "${entries[@]:1}"; do
    IFS=$'\t' read -r kind path saved _ <<< "$entry"
    [[ $kind == displaced && -z ${first_aside[$path]:-} ]] && first_aside[$path]=$entry
done
for entry in "${entries[@]:1}"; do
    IFS=$'\t' read -r kind path saved _ <<< "$entry"
    [[ $kind == displaced && ${first_aside[$path]} != "$entry" ]] || continue
    [[ -z ${kept_wallpapers[$path]:-} ]] || continue
    if [[ $saved != "$displaced"/* || ! (-e $saved || -L $saved) ]]; then
        manifest_drop "$entry"
        continue
    fi
    later=$keep/later-versions/${saved#"$displaced"/}
    plan "keep the later version of $path (moved aside by a reinstall) in $later"
    if ((!dry_run)); then
        mkdir -p "$(dirname "$later")"
        mv -T "$saved" "$later"
    fi
    manifest_drop "$entry"
    warn "a later version of $path (yours, moved aside when install.sh ran again) is kept in $later"
done
for entry in "${entries[@]:1}"; do
    IFS=$'\t' read -r kind path saved _ <<< "$entry"
    [[ $kind == displaced && ${first_aside[$path]} == "$entry" ]] || continue
    [[ -z ${kept_wallpapers[$path]:-} ]] || continue
    if ! is_target file "$path" && ! is_target dir "$path" && ! is_target link "$path"; then
        warn "the record lists $path as moved aside, which isn't a place install.sh installs to; left alone"
    elif [[ $saved != "$displaced"/* || ! (-e $saved || -L $saved) ]]; then
        warn "the moved-aside copy of $path isn't in $displaced any more"
        manifest_drop "$entry"
    elif [[ (-e $path || -L $path) && ${planned_path[$path]:-} != removed ]]; then
        warn "$path is taken by something else, so the earlier one stays in $saved; move that away and run uninstall.sh again"
    else
        plan "put back the earlier $path"
        ((dry_run)) || mv -T "$saved" "$path"
        planned_path[$path]=restored
        manifest_drop "$entry"
        say "Put back the earlier $path"
    fi
done

((had_plasma_style)) && drop_plasma_caches

# A previous run may have published its cleanup hook and link, then failed
# before publishing the module. Retire them before collecting empty parents.
find_kde_quick
if [[ ! -e $quick_module && ! -L $quick_module ]]; then
    remove_passthrough
fi

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

# Qt Quick apps started from the session's environment (it still names the
# Platinum Qt Quick style until the next login) keep working (finding 49).
leave_passthrough

# Anything still to do keeps the record for another run.
left=0
for entry in "${manifest_entries[@]:1}"; do
    case ${entry%%	*} in file | dir | link | displaced | temp) left=1 ;; esac
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
say "Removed the Platinum style (widgets and Qt Quick), decoration, color scheme, Plasma style, global theme, wallpapers and login script"
if ((shell_failed)); then
    warn "$shell_failed_message"
    exit 1
fi

if ((restored)); then
    note "Log out and back in once to finish (the window decoration, the login script and GTK apps)."
elif ((!dry_run)); then
    note "Log out and back in once to finish (the login script is gone)."
fi
((dry_run)) && note "Dry run done."
exit 0
