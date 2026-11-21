# shellcheck shell=bash
# Shared by install.sh and uninstall.sh: where things go, what gets backed
# up, the install record, and small helpers. Not meant to be run on its own.
# Adapted from the user's windows2000-union project (BSD-2-Clause).
#
# Safety rules both scripts keep (AUDIT.md findings 4-14, 27-31):
#   - Nothing that was there before is deleted: a file or folder in the way
#     of an install target is moved aside and put back by uninstall.sh.
#   - The install record is written BEFORE each change, so an interrupted
#     run (Ctrl+C, full disk) still leaves a record uninstall.sh can use.
#     uninstall.sh takes each entry off as soon as it's done, so running it
#     again never redoes a step (a file it put back is never removed).
#   - uninstall.sh only removes paths that are on the record AND are one of
#     the places install.sh installs to, of the recorded kind, never through
#     a symbolic link.
#   - The record and the config copy keep where each path really led (links
#     above it followed). If a folder link was pointed elsewhere since,
#     both scripts stop before changing anything.
#   - Temporary copies are recorded before they're made; leftovers are found
#     by the record, never by their names.
#   - Config files are copied before the first switch, and the copy is never
#     deleted: uninstall.sh moves it into its dated folder after restoring.
#   - One run at a time (a lock in the state folder).
#
# SPDX-License-Identifier: BSD-2-Clause

dry_run=0

# What was done (not shown in a dry run; see plan).
say() {
    ((dry_run)) || printf '%s\n' "$*"
}

# What a dry run would do (only shown in a dry run).
plan() {
    ((dry_run)) && printf '  would %s\n' "$*"
    return 0
}

# Always shown.
note() {
    printf '%s\n' "$*"
}

warn() {
    printf '%s: warning: %s\n' "$program" "$*" >&2
}

die() {
    printf '%s: %s\n' "$program" "$*" >&2
    exit 1
}

have() {
    command -v "$1" > /dev/null 2>&1
}

need() {
    local command
    for command in "$@"; do
        have "$command" || die "needs '$command', which isn't installed"
    done
}

refuse_root() {
    if ((EUID == 0)); then
        die "run this as your own user, not as root (everything goes into your home)"
    fi
}

# An XDG base directory: the variable's value if it's an absolute path (the
# spec says to ignore relative ones), otherwise the default.
xdg_dir() { # value default
    if [[ $1 == /* ]]; then printf '%s' "${1%/}"; else printf '%s' "$2"; fi
}

[[ ${HOME:-} == /* && -d ${HOME:-} ]] || die "HOME must be your home folder (an absolute path); it's '${HOME:-}'"
home=${HOME%/}
data=$(xdg_dir "${XDG_DATA_HOME:-}" "$home/.local/share")
config_home=$(xdg_dir "${XDG_CONFIG_HOME:-}" "$home/.config")
cache=$(xdg_dir "${XDG_CACHE_HOME:-}" "$home/.cache")
state_home=$(xdg_dir "${XDG_STATE_HOME:-}" "$home/.local/state")
for path in "$home" "$data" "$config_home" "$cache" "$state_home"; do
    [[ $path != *[$'\t\n']* ]] || die "a tab or line break in '$path' isn't supported"
done
state=$state_home/macos9-theme
# What install.sh put where (format: manifest_save).
manifest=$state/installed
# Copies of your config files from before the switch.
backup=$state/backup
# Things that were in the way of an install target, to be put back.
displaced=$state/displaced

# The compiled plugins live in a folder of their own; the Plasma login
# script puts it on Qt's plugin path (takes a new login). The decoration
# has its own folder so the login script can leave it out after a Plasma
# upgrade it wasn't built for (KWin then falls back to Breeze).
libdir=$home/.local/lib/macos9-theme
plugins=$libdir/style
deco_plugins=$libdir/decoration
env_script=$config_home/plasma-workspace/env/macos9-theme.sh

scheme_name=Platinum
plasma_theme=platinum
piece_id=platinum.menubarpiece
lnf_id=platinum.desktop

# Everything install.sh installs: kind and path. uninstall.sh removes
# nothing else.
targets=(
    "file	$plugins/styles/platinumstyle.so"
    "file	$deco_plugins/org.kde.kdecoration3/platinum.so"
    "file	$env_script"
    "file	$data/color-schemes/$scheme_name.colors"
    "dir	$data/plasma/desktoptheme/$plasma_theme"
    "dir	$data/plasma/plasmoids/$piece_id"
    "dir	$data/plasma/look-and-feel/$lnf_id"
)

# What applying the global theme (and --apply) changes, copied whole before
# the switch. In ~/.config: the files the theme and the panel layout reset
# write, kdedefaults/ (where a global theme's values go), and what Plasma's
# GTK sync (kded's gtkconfig) rewrites when the colors change. In your
# home: the GTK 2 settings file the same sync writes.
backup_config=(kdeglobals kwinrc plasmarc kcminputrc ksplashrc kscreenlockerrc
    plasma-org.kde.plasma.desktop-appletsrc plasmashellrc kdedefaults
    gtk-3.0/settings.ini gtk-3.0/gtk.css gtk-3.0/colors.css gtk-3.0/window_decorations.css gtk-3.0/assets
    gtk-4.0/settings.ini gtk-4.0/gtk.css gtk-4.0/colors.css gtk-4.0/window_decorations.css gtk-4.0/assets
    xsettingsd/xsettingsd.conf)
backup_home=(.gtkrc-2.0)

# Single-quotes a string for sh.
sh_quote() {
    printf "'%s'" "${1//\'/\'\\\'\'}"
}

# One run at a time. The lock is released when the script exits.
take_lock() {
    ((dry_run)) && return 0
    mkdir -p "$state"
    exec 9> "$state/lock"
    have flock || return 0
    flock -n 9 || die "another install.sh or uninstall.sh is running"
}

# The global theme that's active now (from kdeglobals), or nothing.
active_lnf() {
    [[ -f $config_home/kdeglobals ]] || return 0
    awk -F= '/^\[/ { kde = ($0 == "[KDE]") } kde && $1 == "LookAndFeelPackage" { v = substr($0, index($0, "=") + 1) } END { print v }' \
        "$config_home/kdeglobals"
}

# Running KDE apps reload their widget style on this signal (2 = style).
notify_style() {
    ((dry_run)) && return 0
    if have dbus-send; then
        dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange int32:2 int32:0 2> /dev/null || true
    fi
}

reconfigure_kwin() {
    ((dry_run)) && return 0
    if have qdbus6; then
        qdbus6 org.kde.KWin /KWin reconfigure > /dev/null 2>&1 || true
    fi
}

# Plasma caches rendered SVG pieces by style name; an update or removal has
# to drop them. Only the names Plasma uses for this style.
drop_plasma_caches() {
    local file
    for file in "$cache/plasma_theme_$plasma_theme.kcache" "$cache/plasma_theme_${plasma_theme}_v"*.kcache \
        "$cache/plasma-svgelements-$plasma_theme" "$cache/plasma-svgelements-${plasma_theme}_v"* \
        "$cache/ksvg-elements-$plasma_theme" "$cache/ksvg-elements-${plasma_theme}_v"*; do
        if [[ -f $file && ! -L $file ]]; then
            plan "remove the cache $file"
            ((dry_run)) || rm -f "$file"
        fi
    done
    return 0
}

# --- The install record ---------------------------------------------------
#
# $state/installed, one entry per line, fields separated by tabs:
#   macos9-theme-record 3     format version (first line)
#   home PATH                 the home it was made for,
#   data PATH, config PATH    and the data and config folders
#   madedir PATH REAL         a folder install.sh created
#   file PATH REAL            an installed file,
#   dir PATH REAL             or folder
#   displaced PATH SAVED REAL what was at PATH before, moved to SAVED
#   temp PATH REAL            a temporary copy being written
# REAL is where PATH led when it was recorded (real_path).
manifest_entries=()
record_version=3

# Where PATH leads: the folders above it with every link followed, then its
# own name (PATH itself isn't followed). Recorded next to each path so a
# folder link pointed elsewhere later is noticed, not followed (finding 29).
real_path() { # path
    local parent
    parent=$(realpath -m -- "$(dirname -- "$1")")
    printf '%s/%s' "${parent%/}" "$(basename -- "$1")"
}

manifest_load() {
    manifest_entries=()
    [[ -e $manifest ]] || return 0
    [[ -f $manifest && ! -L $manifest ]] || die "$manifest isn't a regular file"
    mapfile -t manifest_entries < "$manifest"
    local first=${manifest_entries[0]:-}
    [[ $first == "macos9-theme-record	$record_version" ]] ||
        die "$manifest has a format this version doesn't know; nothing was changed"
    local entry kind value
    for entry in "${manifest_entries[@]:1}"; do
        kind=${entry%%	*}
        value=${entry#*	}
        case $kind in
            home) [[ $value == "$home" ]] || die "$manifest was made for the home $value, not $home; nothing was changed" ;;
            data) [[ $value == "$data" ]] || die "$manifest was made with the data folder $value (XDG_DATA_HOME), not $data; run this again with XDG_DATA_HOME=$value; nothing was changed" ;;
            config) [[ $value == "$config_home" ]] || die "$manifest was made with the config folder $value (XDG_CONFIG_HOME), not $config_home; run this again with XDG_CONFIG_HOME=$value; nothing was changed" ;;
            madedir | file | dir | displaced | temp) ;;
            *) die "$manifest has an entry this version doesn't know ($kind); nothing was changed" ;;
        esac
    done
}

# Every path on the record must still lead where it did. If not, a folder
# link above it was pointed elsewhere, and following it would touch some
# other folder's files: stop before changing anything (finding 29).
check_record_paths() {
    local entry kind path saved real moved=()
    for entry in "${manifest_entries[@]:1}"; do
        IFS=$'\t' read -r kind path saved real <<< "$entry"
        case $kind in
            displaced) ;;
            madedir | file | dir | temp) real=$saved ;;
            *) continue ;;
        esac
        [[ $real == "$(real_path "$path")" ]] || moved+=("$path (was $real)")
    done
    if ((${#moved[@]})); then
        printf '  %s\n' "${moved[@]}" >&2
        die "these lead somewhere else now than when they were installed (a folder link above them was changed). Point the link back, then run this again; nothing was changed"
    fi
}

manifest_has() { # entry
    local existing
    for existing in "${manifest_entries[@]}"; do
        [[ $existing == "$1" ]] && return 0
    done
    return 1
}

# Is KIND PATH on the record, for where PATH leads now?
manifest_lists() { # kind path
    manifest_has "$1	$2	$(real_path "$2")"
}

# Writes the record (through a temporary file, so it's never half written).
manifest_write() {
    ((dry_run)) && return 0
    mkdir -p "$state"
    printf '%s\n' "${manifest_entries[@]}" > "$manifest.new"
    mv -f "$manifest.new" "$manifest"
}

# Adds an entry (with where PATH leads now) and writes the record at once.
manifest_add() { # kind path [saved]
    local entry
    entry=$(IFS=$'\t'; printf '%s' "$*") # kind, path, saved
    entry+=$'\t'$(real_path "$2")
    manifest_has "$entry" && return 0
    if ((${#manifest_entries[@]} == 0)); then
        manifest_entries=("macos9-theme-record	$record_version" "home	$home" "data	$data" "config	$config_home")
    fi
    manifest_entries+=("$entry")
    manifest_write
}

# Takes an entry off the record and writes it at once.
manifest_drop() { # entry
    local kept=() existing
    for existing in "${manifest_entries[@]}"; do
        [[ $existing == "$1" ]] || kept+=("$existing")
    done
    manifest_entries=("${kept[@]}")
    manifest_write
}

# Creates a new temporary file or folder in DIR, recorded first, so the
# leftovers of an interrupted run are known by the record, never guessed
# from their names (finding 30). The path is left in $made_temp.
made_temp=""
make_temp() { # file|dir dir
    local i tmp made
    for ((i = 0; i < 100; i++)); do
        tmp=$2/.macos9-theme.$(printf '%08x' "${SRANDOM:-$((RANDOM * 32768 + RANDOM))}")
        [[ -e $tmp || -L $tmp ]] && continue
        manifest_add temp "$tmp"
        made=1
        if [[ $1 == dir ]]; then
            mkdir "$tmp" 2> /dev/null || made=0
        else
            (set -o noclobber; : > "$tmp") 2> /dev/null || made=0
        fi
        if ((made)); then
            made_temp=$tmp
            return 0
        fi
        manifest_drop "temp	$tmp	$(real_path "$tmp")"
    done
    die "couldn't create a temporary file in $2"
}

# A temporary copy is gone (renamed into place or removed).
done_temp() { # path
    manifest_drop "temp	$1	$(real_path "$1")"
}

# Is TARGET (kind<TAB>path) one of the install targets, or a folder above
# one inside the home?
is_target() { # kind path
    local entry
    for entry in "${targets[@]}"; do
        [[ $entry == "$1	$2" ]] && return 0
    done
    return 1
}

is_target_parent() { # path
    local entry
    [[ $1 == "$home"/* ]] || return 1
    for entry in "${targets[@]}"; do
        [[ ${entry#*	} == "$1"/* ]] && return 0
    done
    return 1
}

# Does the thing at PATH have the kind (file or dir), not through a link?
is_kind() { # kind path
    [[ -L $2 ]] && return 1
    case $1 in
        file) [[ -f $2 ]] ;;
        dir) [[ -d $2 ]] ;;
        *) return 1 ;;
    esac
}

# Before any change: every folder above every target must be a folder (or
# not exist yet), so install can't stop halfway on that.
check_target_parents() {
    local entry path
    for entry in "${targets[@]}"; do
        path=${entry#*	}
        path=$(dirname "$path")
        while [[ ! -e $path && ! -L $path ]]; do
            path=$(dirname "$path")
        done
        [[ -d $path ]] || die "$path is in the way (install needs a folder there); nothing was changed"
    done
}

# Creates the folders above PATH that are missing, recording each first.
make_parents() { # path
    local parent=$1 missing=()
    while [[ ! -e $parent && ! -L $parent ]]; do
        missing=("$parent" "${missing[@]}")
        parent=$(dirname "$parent")
    done
    for parent in "${missing[@]}"; do
        manifest_lists madedir "$parent" && continue # a dry run made it already
        manifest_add madedir "$parent"
        plan "create the folder $parent"
        ((dry_run)) || mkdir "$parent"
    done
}

# If something install.sh didn't install is at PATH, moves it aside (and
# records where), so it can be put back.
displace_foreign() { # kind path
    local kind=$1 path=$2 saved
    [[ -e $path || -L $path ]] || return 0
    manifest_lists "$kind" "$path" && is_kind "$kind" "$path" && return 0
    if ((dry_run)); then
        plan "move the existing $path aside (uninstall.sh puts it back)"
        return 0
    fi
    mkdir -p "$displaced"
    saved=$(mktemp -d "$displaced/XXXXXX")/$(basename "$path")
    manifest_add displaced "$path" "$saved"
    mv "$path" "$saved"
    say "Moved the existing $path aside (uninstall.sh puts it back)"
}

# Installs a file: record, then copy under a temporary name and rename.
place_file() { # source target mode
    local target=$2 staging
    displace_foreign file "$target"
    make_parents "$(dirname "$target")"
    manifest_add file "$target"
    plan "install $target"
    ((dry_run)) && return 0
    make_temp file "$(dirname "$target")"
    staging=$made_temp
    if ! install -m "$3" "$1" "$staging"; then
        rm -f "$staging"
        done_temp "$staging"
        die "couldn't write $target"
    fi
    mv -f "$staging" "$target"
    done_temp "$staging"
}

# Installs a folder: record, copy whole under a temporary name, then swap it
# in (atomically where mv can exchange), so Plasma never reads half a copy.
place_dir() { # source target
    local target=$2 staging old
    displace_foreign dir "$target"
    make_parents "$(dirname "$target")"
    manifest_add dir "$target"
    plan "install $target/"
    ((dry_run)) && return 0
    make_temp dir "$(dirname "$target")"
    staging=$made_temp
    if ! cp -R "$1/." "$staging/"; then
        rm -rf "$staging"
        done_temp "$staging"
        die "couldn't write $target"
    fi
    chmod 755 "$staging"
    if [[ ! -e $target ]]; then
        mv -T "$staging" "$target"
    elif mv --exchange -T "$staging" "$target" 2> /dev/null; then
        rm -rf "$staging"
    else
        make_temp dir "$(dirname "$target")"
        old=$made_temp
        mv -T "$target" "$old/old"
        mv -T "$staging" "$target"
        rm -rf "$old"
        done_temp "$old"
    fi
    done_temp "$staging"
}

# Leftover temporary copies of an interrupted run: the ones on the record
# (anything else with a similar name is left alone), and half-made config
# copies in the state folder, which is this theme's own.
remove_temporaries() {
    local entry kind path real tmp entries=("${manifest_entries[@]}")
    for entry in "${entries[@]}"; do
        IFS=$'\t' read -r kind path real <<< "$entry"
        [[ $kind == temp ]] || continue
        if [[ -e $path && ! -L $path ]]; then
            plan "remove the leftover $path"
            ((dry_run)) || rm -rf "$path"
        fi
        manifest_drop "$entry"
    done
    for tmp in "$state"/backup.??????; do
        [[ -d $tmp && ! -L $tmp ]] || continue
        plan "remove the leftover $tmp"
        ((dry_run)) || rm -rf "$tmp"
    done
    return 0
}

# --- Config backup ----------------------------------------------------------
#
# $backup/ holds config/<name> and home/<name> copies plus:
#   ENTRIES   the "config<TAB>name<TAB>real" / "home<TAB>name<TAB>real" list
#             that was copied (real: where it led then, see real_path)
#   ABSENT    the entries that didn't exist (removed again on restore)
#   ROOTS     "config<TAB>path" and "home<TAB>path" at the time
#   TAKEN     "install" (copied by a plain install, before any switch) or
#             "apply" (the switch happened, or happens now)

backup_entries() {
    local name
    for name in "${backup_config[@]}"; do printf 'config\t%s\n' "$name"; done
    for name in "${backup_home[@]}"; do printf 'home\t%s\n' "$name"; done
}

root_of() { # config|home
    case $1 in
        config) printf '%s' "$config_home" ;;
        home) printf '%s' "$home" ;;
    esac
}

# A symbolic link in the backup list would make the copy and the live file
# the same thing; refuse before changing anything.
check_backup_links() {
    local base name path
    while IFS=$'\t' read -r base name; do
        path=$(root_of "$base")/$name
        if [[ -L $path ]]; then
            die "$path is a symbolic link; install.sh can't keep a safe copy of it. Replace it with the file or folder it points to, then run this again; nothing was changed"
        fi
    done < <(backup_entries)
}

# Copies the config files into a new backup (replacing an existing one).
take_backup() { # install|apply
    local tmp base name path old
    if ((dry_run)); then
        plan "copy your config files to $backup"
        return 0
    fi
    mkdir -p "$state"
    tmp=$(mktemp -d "$state/backup.XXXXXX")
    : > "$tmp/ABSENT"
    while IFS=$'\t' read -r base name; do
        printf '%s\t%s\t%s\n' "$base" "$name" "$(real_path "$(root_of "$base")/$name")"
    done < <(backup_entries) > "$tmp/ENTRIES"
    printf 'config\t%s\nhome\t%s\n' "$config_home" "$home" > "$tmp/ROOTS"
    printf '%s\n' "$1" > "$tmp/TAKEN"
    while IFS=$'\t' read -r base name _; do
        path=$(root_of "$base")/$name
        if [[ -e $path ]]; then
            mkdir -p "$(dirname "$tmp/$base/$name")"
            cp -a "$path" "$tmp/$base/$name" || { rm -rf "$tmp"; die "couldn't copy $path; nothing was changed"; }
        else
            printf '%s\t%s\n' "$base" "$name" >> "$tmp/ABSENT"
        fi
    done < "$tmp/ENTRIES"
    if [[ -d $backup ]]; then
        old=$(mktemp -d "$state/backup.XXXXXX")
        mv -T "$backup" "$old/old"
        mv -T "$tmp" "$backup"
        rm -rf "$old"
    else
        mv -T "$tmp" "$backup"
    fi
    say "Copied your current config files to $backup"
}

backup_taken() {
    [[ -f $backup/TAKEN ]] && cat "$backup/TAKEN"
}

mark_backup() { # install|apply
    plan "mark the copy in $backup as taken before the switch"
    ((dry_run)) || printf '%s\n' "$1" > "$backup/TAKEN"
}

# --- Plasma's shell ---------------------------------------------------------
#
# plasmashell writes its panel layout when it quits, so the layout file can
# only be put back while it isn't running.

shell_how=""

shell_running_on_bus() {
    have dbus-send || return 1
    dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.NameHasOwner \
        string:org.kde.plasmashell 2> /dev/null | grep -q 'boolean true'
}

shell_pid() {
    dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetConnectionUnixProcessID \
        string:org.kde.plasmashell 2> /dev/null | awk '/uint32/ { print $2 }'
}

# Stops Plasma's shell if it runs; fails if it can't.
shell_stop() {
    local pid i
    shell_how=""
    if have systemctl && systemctl --user is-active --quiet plasma-plasmashell.service 2> /dev/null; then
        plan "stop Plasma's shell (systemctl --user stop plasma-plasmashell.service)"
        ((dry_run)) || systemctl --user stop plasma-plasmashell.service || return 1
        shell_how=systemd
    elif shell_running_on_bus; then
        have kquitapp6 || return 1
        plan "stop Plasma's shell (kquitapp6 plasmashell)"
        if ((!dry_run)); then
            pid=$(shell_pid)
            kquitapp6 plasmashell > /dev/null 2>&1 || true
            for ((i = 0; i < 100; i++)); do
                if [[ -n $pid ]]; then
                    kill -0 "$pid" 2> /dev/null || break
                else
                    shell_running_on_bus || break
                fi
                sleep 0.2
            done
            ((i < 100)) || return 1
        fi
        shell_how=direct
    fi
    return 0
}

shell_start() {
    case $shell_how in
        systemd)
            plan "start Plasma's shell again"
            ((dry_run)) || systemctl --user start plasma-plasmashell.service
            ;;
        direct)
            plan "start Plasma's shell again"
            ((dry_run)) || setsid -f plasmashell > /dev/null 2>&1 < /dev/null
            ;;
        *) return 0 ;;
    esac
}
