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
#   - The record keeps a checksum of every file installed. uninstall.sh
#     removes only files that still match; anything you added to or changed
#     in an installed folder or file stays (finding 35). install.sh moves a
#     changed one aside like any other thing in its way.
#   - The config copy has a checksum list; uninstall.sh refuses to restore
#     from a copy that's incomplete or changed (finding 36).
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

# Preflight tools with their Arch Linux package names (cmd:pkg), reporting all
# missing items before taking locks, fetching, or writing files (AUDIT.md #118).
need_pkg() {
    local spec cmd pkg missing=()
    for spec in "$@"; do
        cmd=${spec%%:*}
        pkg=${spec#*:}
        have "$cmd" || missing+=("$cmd (Arch package: $pkg)")
    done
    if ((${#missing[@]})); then
        local joined
        joined=$(printf '%s; ' "${missing[@]}")
        die "missing required tools: ${joined%; }. Install the missing Arch package(s) and try again; nothing was changed"
    fi
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
# Icon theme adoption transaction record (v3 JSON; AUDIT.md #110, #124, #128).
icon_adoption=$state/icon-adoption
# Fallback restore-decision marker when uninstalling a legacy backup with no $icon_adoption.
restore_decision_file=$state/restore-decision
# Retained throughout uninstall until backup, packages, and manifest are retired (#140).
uninstall_marker=$state/uninstall-in-progress
# Fast O(N) manifest helper (format version 4 compatible).
manifest_ops=$here/scripts/manifest_ops.py
# Durable KDE + GTK icon transaction and unified dependency checker.
icon_prefs=$here/scripts/icon_prefs.py

# The compiled plugins live in a folder of their own; the Plasma login
# script puts it on Qt's plugin path (takes a new login). The decoration
# has its own folder so the login script can leave it out after a Plasma
# upgrade it wasn't built for (KWin then falls back to Breeze).
libdir=$home/.local/lib/macos9-theme
plugins=$libdir/style
deco_plugins=$libdir/decoration
# The Qt Quick Controls style (style/quick), and the link Kirigami finds its
# color and size plugin by (named after the style, pointing at KDE's).
quick_qml=$libdir/qml
quick_module=$quick_qml/Platinum
kirigami_link=$plugins/kf6/kirigami/platform/Platinum.so
# The cursor theme (cursors/macOS-cursors.tar.xz), where libXcursor and
# Plasma look for themes in your data folder.
black_cursor_id=macOS-cursors
cursor_theme_dir=$data/icons/$black_cursor_id
# Left by uninstall.sh for the rest of the session (finding 49), removed by
# itself at the next login.
cleanup_script=$config_home/plasma-workspace/env/macos9-theme-cleanup.sh
passthrough_marker="# macos9-theme: pass-through left by uninstall.sh, removed at the next login"

# KDE's Qt Quick style (its version file) and Kirigami's plugin for it,
# where Qt keeps them; empty when not installed.
kde_quick_version_file="" kirigami_desktop=""
find_kde_quick() {
    local qtpaths
    qtpaths=$(pkg-config --variable=bindir Qt6Core 2> /dev/null)/qtpaths6
    [[ -x $qtpaths ]] || qtpaths=$(command -v qtpaths6 || command -v qtpaths || true)
    [[ -n $qtpaths ]] || return 0
    kde_quick_version_file=$("$qtpaths" --query QT_INSTALL_QML 2> /dev/null)/org/kde/desktop/kde-qmlmodule.version
    kirigami_desktop=$("$qtpaths" --query QT_INSTALL_PLUGINS 2> /dev/null)/kf6/kirigami/platform/org.kde.desktop.so
    [[ -f $kde_quick_version_file ]] || kde_quick_version_file=""
    [[ -e $kirigami_desktop ]] || kirigami_desktop=""
    return 0
}
env_script=$config_home/plasma-workspace/env/macos9-theme.sh

scheme_name=Platinum
gtk_theme_dir=$data/themes/Platinum
terminal_scheme=PlatinumLavender.colorscheme
terminal_scheme_path=$data/konsole/$terminal_scheme
plasma_theme=platinum
piece_id=platinum.menubarpiece
trash_id=platinum.trash
lnf_id=platinum.desktop
wallpaper_ids=(platinum-ribbon platinum-lavender platinum-waves platinum-glass)
icon_base_id=WhiteSur-lavender
icon_theme_ids=(WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark)

# Everything install.sh installs: kind and path. uninstall.sh removes
# nothing else.
targets=(
    "file	$plugins/styles/platinumstyle.so"
    "file	$deco_plugins/org.kde.kdecoration3/platinum.so"
    "file	$env_script"
    "file	$data/color-schemes/$scheme_name.colors"
    "file	$terminal_scheme_path"
    "dir	$gtk_theme_dir" # legacy whole-theme installs
    "dir	$gtk_theme_dir/gtk-3.0"
    "file	$gtk_theme_dir/index.theme"
    "dir	$data/plasma/desktoptheme/$plasma_theme"
    "dir	$data/plasma/plasmoids/$piece_id"
    "dir	$data/plasma/plasmoids/$trash_id"
    "dir	$data/plasma/look-and-feel/$lnf_id"
    "dir	$quick_module"
    "link	$kirigami_link"
    "dir	$cursor_theme_dir"
)
for wallpaper_id in "${wallpaper_ids[@]}"; do
    targets+=("dir	$data/wallpapers/$wallpaper_id")
done
for icon_id in "${icon_theme_ids[@]}"; do
    targets+=("dir	$data/icons/$icon_id")
done

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
# Requires flock (Arch package: util-linux); never silently disables exclusion (#135).
take_lock() {
    ((dry_run)) && return 0
    have flock || die "missing required tool: flock (Arch package: util-linux); nothing was changed"
    mkdir -p "$state"
    exec 9> "$state/lock"
    flock -n 9 || die "another install.sh or uninstall.sh is running"
}

# The global theme that's active now (from kdeglobals), or nothing.
active_lnf() {
    [[ -f $config_home/kdeglobals ]] || return 0
    awk -F= '/^\[/ { kde = ($0 == "[KDE]") } kde && $1 == "LookAndFeelPackage" { v = substr($0, index($0, "=") + 1) } END { print v }' \
        "$config_home/kdeglobals"
}

is_managed_icon_id() { # id
    local id
    for id in "${icon_theme_ids[@]}"; do
        [[ $1 == "$id" ]] && return 0
    done
    return 1
}

# Running KDE apps reload their widget style on this signal (2 = style).
notify_style() {
    ((dry_run)) && return 0
    if have dbus-send; then
        dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange int32:2 int32:0 2> /dev/null || true
    fi
}

# Running KDE apps reload their icon theme on this signal (4 = icon).
notify_icons() {
    ((dry_run)) && return 0
    if have dbus-send; then
        dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange int32:4 int32:0 2> /dev/null || true
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
#   dir PATH REAL             folder,
#   link PATH REAL            or symbolic link
#   displaced PATH SAVED REAL what was at PATH before, moved to SAVED
#   temp PATH REAL            a temporary copy being written
#   sum PATH SHA256           a file install.sh installed (also inside an
#                             installed folder) and its content, or
#   sum PATH ->TARGET         a link and where it points; written before
#                             the copy, old ones dropped after it
# REAL is where PATH led when it was recorded (real_path).
manifest_entries=()
record_version=4

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
    [[ -e $manifest || -L $manifest ]] || return 0
    local out err_file
    err_file=$(mktemp)
    if ! out=$(python3 -I "$manifest_ops" load-meta "$manifest" "$record_version" "$home" "$data" "$config_home" 2> "$err_file"); then
        local msg
        msg=$(< "$err_file")
        rm -f "$err_file"
        die "${msg:-could not read $manifest}"
    fi
    rm -f "$err_file"
    if [[ -n $out ]]; then
        mapfile -t manifest_entries <<< "$out"
    fi
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
            madedir | file | dir | link | temp) real=$saved ;;
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

# Writes the record (through a temporary file, so it's never half written),
# preserving any existing sum lines in $manifest.
manifest_write() {
    ((dry_run)) && return 0
    mkdir -p "$state"
    printf '%s\n' "${manifest_entries[@]}" | python3 -I "$manifest_ops" write-meta "$manifest"
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

# --- Checksums of what was installed --------------------------------------

# Records the checksum of every file/link SOURCE (a file or folder) will put at
# TARGET, before it's copied. Saves the key list in $last_sums_file for prune_sums.
last_sums_file=""
record_sums() { # source target
    ((dry_run)) && return 0
    local tmp_base=/tmp
    [[ -n ${build:-} && -d ${build:-} ]] && tmp_base=$build
    last_sums_file=$(mktemp "$tmp_base/m9-sums.XXXXXX")
    python3 -I "$manifest_ops" record-sums "$manifest" "$1" "$2" "$last_sums_file"
}

# After TARGET was replaced: drops the checksums of what was there before.
prune_sums() { # target
    ((dry_run)) && return 0
    [[ -n $last_sums_file && -f $last_sums_file ]] || return 0
    python3 -I "$manifest_ops" prune-sums "$manifest" "$1" "$last_sums_file"
    rm -f "$last_sums_file"
    last_sums_file=""
}

# Drops all recorded checksums under TARGET (after uninstall removes it).
drop_target_sums() { # target
    ((dry_run)) && return 0
    python3 -I "$manifest_ops" drop-sums "$manifest" "$1"
}

# Kept for caller compatibility; manifest_ops queries $manifest directly.
index_sums() {
    return 0
}

# Is PATH a file or a link install.sh put there?
installed_file() { # path
    if [[ -L $1 ]]; then
        installed_link "$1"
        return
    fi
    [[ -f $1 && -f $manifest ]] || return 1
    python3 -I "$manifest_ops" check-file "$manifest" "$1"
}

# Is everything in the folder PATH as install.sh put it (no file or folder
# added, no file changed; files it installed may be missing)?
installed_tree() { # path
    [[ -d $1 && ! -L $1 && -f $manifest ]] || return 1
    python3 -I "$manifest_ops" check-tree "$manifest" "$1"
}

# Is what's at PATH, of KIND, exactly what install.sh installed there?
installed_unchanged() { # kind path
    manifest_lists "$1" "$2" && is_kind "$1" "$2" || return 1
    case $1 in
        file) installed_file "$2" ;;
        dir) installed_tree "$2" ;;
        link) installed_link "$2" ;;
    esac
}

# Is PATH a link pointing where install.sh made it point?
installed_link() { # path
    [[ -L $1 && -f $manifest ]] || return 1
    python3 -I "$manifest_ops" check-link "$manifest" "$1"
}

# Installs a symbolic link: record (with where it points), then make it
# under a temporary name and rename it into place.
place_link() { # points-to target
    local target=$2 staging
    displace_foreign link "$target"
    make_parents "$(dirname "$target")"
    manifest_add link "$target"
    if ((!dry_run)); then
        python3 -I "$manifest_ops" record-single-sum "$manifest" "$target" "->$1"
    fi
    plan "link $target to $1"
    ((dry_run)) && return 0
    make_temp file "$(dirname "$target")"
    staging=$made_temp
    ln -sfn "$1" "$staging"
    mv -fT "$staging" "$target"
    done_temp "$staging"
    python3 -I "$manifest_ops" prune-single-sum "$manifest" "$target" "->$1"
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

# Does the thing at PATH have the kind (file, dir or link), not through a
# link?
is_kind() { # kind path
    [[ $1 == link ]] && { [[ -L $2 ]]; return; }
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
# records where), so it can be put back. Rolls back the record if mv fails
# so an interrupted or failed displacement can never shadow a later real copy
# (AUDIT.md #112).
displace_foreign() { # kind path
    local kind=$1 path=$2 holder saved real
    [[ -e $path || -L $path ]] || return 0
    # Ours and unchanged: replaced in place. Changed since: moved aside.
    installed_unchanged "$kind" "$path" && return 0
    if ((dry_run)); then
        plan "move the existing $path aside (uninstall.sh puts it back)"
        return 0
    fi
    mkdir -p "$displaced"
    holder=$(mktemp -d "$displaced/XXXXXX")
    saved=$holder/$(basename "$path")
    real=$(real_path "$path")
    manifest_add displaced "$path" "$saved"
    if ! mv "$path" "$saved"; then
        manifest_drop "displaced	$path	$saved	$real"
        rmdir "$holder" 2> /dev/null || true
        die "couldn't move the existing $path aside"
    fi
    say "Moved the existing $path aside (uninstall.sh puts it back)"
}

# Installs a file: record, then copy under a temporary name and rename.
place_file() { # source target mode
    local target=$2 staging
    displace_foreign file "$target"
    make_parents "$(dirname "$target")"
    manifest_add file "$target"
    record_sums "$1" "$target"
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
    prune_sums "$target"
}

# Installs a folder: record, copy whole under a temporary name, then swap it
# in (atomically where mv can exchange), so Plasma never reads half a copy.
place_dir() { # source target
    local target=$2 staging old
    displace_foreign dir "$target"
    make_parents "$(dirname "$target")"
    manifest_add dir "$target"
    record_sums "$1" "$target"
    plan "install $target/"
    ((dry_run)) && return 0
    make_temp dir "$(dirname "$target")"
    staging=$made_temp
    if ! cp -RP "$1/." "$staging/"; then
        rm -rf "$staging"
        done_temp "$staging"
        rm -f "${last_sums_file:-}"
        last_sums_file=""
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
    prune_sums "$target"
}

# Leftover temporary copies of an interrupted run: the ones on the record
# (anything else with a similar name is left alone), and half-made config
# copies in the state folder, which is this theme's own.
remove_temporaries() {
    local entry kind path real tmp entries=("${manifest_entries[@]}")
    for entry in "${entries[@]}"; do
        IFS=$'\t' read -r kind path real <<< "$entry"
        [[ $kind == temp ]] || continue
        if [[ -L $path ]]; then
            # (a link being made; removed itself, never followed)
            plan "remove the leftover $path"
            ((dry_run)) || rm -f "$path"
        elif [[ -e $path ]]; then
            plan "remove the leftover $path"
            ((dry_run)) || rm -rf "$path"
        fi
        manifest_drop "$entry"
    done
    for tmp in "$state"/backup.?????? "$state"/.restore-stage.??????; do
        [[ -d $tmp && ! -L $tmp ]] || continue
        plan "remove the leftover $tmp"
        ((dry_run)) || rm -rf "$tmp"
    done
    for tmp in "$state"/.icon-adoption.?????? "$state"/.icon-adoption.tmp.*; do
        [[ -f $tmp && ! -L $tmp ]] || continue
        plan "remove the leftover $tmp"
        ((dry_run)) || rm -f "$tmp"
    done
    return 0
}

# Reconcile any incomplete displaced record left by an abrupt exit between
# manifest_add displaced and mv "$path" "$saved" (AUDIT.md #112).
reconcile_displaced() {
    local entry kind path saved holder entries=("${manifest_entries[@]}")
    local -A has_completed=() has_installed=()
    for entry in "${entries[@]:1}"; do
        IFS=$'\t' read -r kind path saved _ <<< "$entry"
        case $kind in
            file | dir | link) has_installed[$path]=1 ;;
            displaced)
                if [[ $saved == "$displaced"/* && (-e $saved || -L $saved) ]]; then
                    has_completed[$path]=1
                fi
                ;;
        esac
    done
    for entry in "${entries[@]:1}"; do
        IFS=$'\t' read -r kind path saved _ <<< "$entry"
        [[ $kind == displaced ]] || continue
        [[ $saved == "$displaced"/* && ! (-e $saved || -L $saved) ]] || continue
        holder=$(dirname "$saved")
        if [[ -n ${has_completed[$path]:-} ]] ||
            [[ -z ${has_installed[$path]:-} && $holder == "$displaced"/* && -d $holder && ! -L $holder && -z $(ls -A "$holder" 2> /dev/null) ]]; then
            plan "drop incomplete displaced record for $path"
            manifest_drop "$entry"
            if ((!dry_run)) && [[ $holder == "$displaced"/* && -d $holder && ! -L $holder ]]; then
                rmdir "$holder" 2> /dev/null || true
            fi
        fi
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
#   SUMS      sha256sum list of every copied file (checked before restoring)

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
# The same for links inside a copied folder (finding 34): the switch would
# write through them into the file they point to, which no copy covers.
check_backup_links() {
    local base name path link
    while IFS=$'\t' read -r base name; do
        path=$(root_of "$base")/$name
        if [[ -L $path ]]; then
            die "$path is a symbolic link; install.sh can't keep a safe copy of it. Replace it with the file or folder it points to, then run this again; nothing was changed"
        fi
        if [[ -d $path ]]; then
            link=$(find "$path" -type l -print -quit 2> /dev/null)
            if [[ -n $link ]]; then
                die "$link is a symbolic link; install.sh can't keep a safe copy of it. Replace it with the file or folder it points to, then run this again; nothing was changed"
            fi
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
    # (config/ or home/ may not exist: nothing of theirs was there)
    (cd "$tmp" && { find config home -type f -print0 2> /dev/null || true; } | sort -z | xargs -0 -r sha256sum) > "$tmp/SUMS"
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

# --- The pass-through after uninstalling (finding 49) ----------------------
#
# The login script exports QT_QUICK_CONTROLS_STYLE=Platinum into the
# session; whatever still has that environment (Plasma's shell, KRunner,
# open terminals) would start Qt Quick apps that fail without the module.
# So uninstall.sh leaves a module that only forwards to KDE's style, and
# Kirigami's link, until the next login, when a one-shot login script
# removes them (only what it recognizes) and itself.

# Can a folder be made at PATH (the nearest existing folder above is one)?
can_make_dir() { # path
    local dir=$1
    while [[ ! -e $dir && ! -L $dir ]]; do
        dir=$(dirname "$dir")
    done
    [[ -d $dir ]]
}

passthrough_qmldir() {
    printf '%s\n' "$passthrough_marker" 'module Platinum' 'import org.kde.desktop 1.0'
}

# Publish a completed file or folder without replacing a path that appeared
# during uninstall. The install record still owns the temporary on failure.
publish_passthrough_temp() {
    mv -nT "$made_temp" "$1" && [[ ! -e $made_temp ]] ||
        die "couldn't leave the pass-through at $1. Run uninstall.sh again"
    done_temp "$made_temp"
}

# Only into empty places, so nothing of yours is touched (findings 54-56):
# the module only where nothing is, the link only where none is (and only
# a link it made is removed later), the one-shot script under a free name.
# In a dry run what the real run will have removed counts as free (`planned_path`,
# uninstall.sh; finding 58).
leave_passthrough() {
    local made=() dir make_link=0 script n module_sum tmp
    [[ -n $kirigami_desktop ]] || return 0
    # (free: nothing there; in a dry run also what the real run will have
    # removed and not put something back at)
    free() {
        if ((dry_run)); then
            case ${planned_path[$1]:-} in
                removed) return 0 ;;
                restored) return 1 ;;
            esac
        fi
        [[ ! -e $1 && ! -L $1 ]]
    }
    if ! free "$quick_module" || ! can_make_dir "$quick_module"; then
        warn "leaving $quick_module as it is. Qt Quick apps from this session may need you to log out and back in before they start"
        return 0
    fi
    free "$kirigami_link" && can_make_dir "$(dirname "$kirigami_link")" && make_link=1
    script=$cleanup_script
    for ((n = 2; n < 100; n++)); do
        free "$script" && break
        script=${cleanup_script%.sh}-$n.sh
    done
    if ! free "$script" || ! can_make_dir "$(dirname "$script")"; then
        warn "couldn't leave a pass-through for Qt Quick apps started before you log out (no place for its login script); they may not start until you do"
        return 0
    fi
    plan "leave a pass-through in $quick_module for Qt Quick apps started before you log out, removed at your next login by $script"
    ((dry_run)) && return 0
    for dir in "$quick_module" "$(dirname "$script")"; do
        while [[ ! -e $dir && ! -L $dir ]]; do
            made+=("$dir")
            dir=$(dirname "$dir")
        done
    done
    if ((make_link)); then
        dir=$(dirname "$kirigami_link")
        while [[ ! -e $dir && ! -L $dir ]]; do
            made+=("$dir")
            dir=$(dirname "$dir")
        done
    fi
    # Publish the complete hook before creating the files it will clean up.
    make_parents "$(dirname "$script")"
    make_temp file "$(dirname "$script")"
    tmp=$made_temp
    module_sum=$(passthrough_qmldir | sha256sum)
    {
        printf '%s\n' "$passthrough_marker" '# Generated cleanup, format 2' '('
        printf 'self=%s\n' "$(sh_quote "$script")"
        cat <<'CHECK_HOOK'
[ -f "$self" ] && [ ! -L "$self" ] || exit 0
[ "$(tail -n 1 "$self")" = "# checksum $(sed '$d' "$self" | sha256sum)" ] || exit 0
CHECK_HOOK
        printf 'macos9_theme_m=%s\n' "$(sh_quote "$quick_module")"
        printf 'if [ ! -L "$macos9_theme_m" ] && [ ! -L "$macos9_theme_m/qmldir" ] && [ -f "$macos9_theme_m/qmldir" ] && [ "$(sha256sum < "$macos9_theme_m/qmldir")" = %s ]; then\n' "$(sh_quote "$module_sum")"
        printf '    rm -f "$macos9_theme_m/qmldir"\n'
        printf 'fi\n'
        if ((make_link)); then
            printf 'if [ -L %s ] && [ "$(readlink %s)" = %s ] && [ ! -e %s ]; then\n' "$(sh_quote "$kirigami_link")" "$(sh_quote "$kirigami_link")" \
                "$(sh_quote "$kirigami_desktop")" "$(sh_quote "$plugins/styles/platinumstyle.so")"
            printf '    rm -f %s\n' "$(sh_quote "$kirigami_link")"
            printf 'fi\n'
        fi
        printf 'rm -f "$self"\n'
        # The folders it made, deepest first, if empty.
        printf '%s\n' "${made[@]}" | awk '{ print length($0) "\t" $0 }' | sort -rn | cut -f2- | while IFS= read -r dir; do
            printf 'rmdir %s 2> /dev/null\n' "$(sh_quote "$dir")"
        done
        printf ')\ntrue\n'
    } > "$tmp"
    printf '# checksum %s\n' "$(sha256sum < "$tmp")" >> "$tmp"
    publish_passthrough_temp "$script"
    if ((make_link)); then
        mkdir -p "$(dirname "$kirigami_link")"
        ln -s "$kirigami_desktop" "$kirigami_link"
    fi
    mkdir -p "$quick_qml"
    make_temp dir "$quick_qml"
    passthrough_qmldir > "$made_temp/qmldir"
    publish_passthrough_temp "$quick_module"
    say "Left a pass-through in $quick_module, so Qt Quick apps started before you log out keep working (with KDE's look); $script removes it at your next login"
}

# Unchecksummed hooks from the two previous versions. Compare their entire
# body, ignoring only exact rmdir commands for eligible parent directories.
legacy_cleanup_matches() {
    local script=$1 link=$2 description=$3
    shift 3
    local quoted_link dir
    quoted_link=$(sh_quote "$kirigami_link")
    case $description in
        '# started before you logged out (only what it made), then itself.' | \
        '# started before you logged out (only what it recognizes), then itself.') ;;
        *) return 1 ;;
    esac
    cmp -s <(
        printf '%s\n' "$passthrough_marker" "# Removes the pass-through macos9-theme's uninstall.sh left for Qt Quick apps" "$description"
        printf 'macos9_theme_m=%s\n' "$(sh_quote "$quick_module")"
        printf 'if [ -f "$macos9_theme_m/qmldir" ] && [ "$(head -n 1 "$macos9_theme_m/qmldir")" = %s ]; then\n' "$(sh_quote "$passthrough_marker")"
        printf '%s\n' '    rm -f "$macos9_theme_m/qmldir"' fi
        if ((link)); then
            printf 'if [ -L %s ] && [ "$(readlink %s)" = %s ] && [ ! -e %s ]; then\n' "$quoted_link" "$quoted_link" \
                "$(sh_quote "$kirigami_desktop")" "$(sh_quote "$plugins/styles/platinumstyle.so")"
            printf '    rm -f %s\nfi\n' "$quoted_link"
        fi
        printf 'unset macos9_theme_m\nrm -f %s\ntrue\n' "$(sh_quote "$script")"
    ) <(grep -Fvx -f <(for dir in "$@"; do printf 'rmdir %s 2> /dev/null\n' "$(sh_quote "$dir")"; done) "$script")
}

# A reinstall reads pending hooks as data. Only operate on our known paths;
# never execute a program discovered in the user's login folder.
remove_passthrough() {
    local script dir start link description dirs=()
    for script in "$cleanup_script" "${cleanup_script%.sh}"-[2-9].sh "${cleanup_script%.sh}"-[1-9][0-9].sh; do
        [[ -f $script && ! -L $script && $(head -n 1 "$script") == "$passthrough_marker" ]] || continue
        link=0
        grep -Fxq "    rm -f $(sh_quote "$kirigami_link")" "$script" && link=1
        dirs=()
        for start in "$quick_module" "$(dirname "$kirigami_link")" "$(dirname "$script")"; do
            dir=$start
            while [[ $dir != / && $dir != "$home" ]]; do
                grep -Fxq "rmdir $(sh_quote "$dir") 2> /dev/null" "$script" && dirs+=("$dir")
                dir=$(dirname "$dir")
            done
        done
        if [[ $(sed -n '2p' "$script") == '# Generated cleanup, format 2' ]]; then
            grep -Fxq "self=$(sh_quote "$script")" "$script" || continue
            [[ $(tail -n 1 "$script") == "# checksum $(sed '$d' "$script" | sha256sum)" ]] || continue
        else
            description=$(sed -n '3p' "$script")
            legacy_cleanup_matches "$script" "$link" "$description" "${dirs[@]}" || continue
            # The earliest version didn't record whether the link was its own.
            [[ $description == *'what it recognizes'* ]] && link=0
        fi
        plan "remove the pass-through uninstall.sh left ($script)"
        ((dry_run)) && continue
        if [[ ! -L $quick_module && ! -L $quick_module/qmldir && -f $quick_module/qmldir ]] &&
            passthrough_qmldir | cmp -s - "$quick_module/qmldir"; then
            rm -f "$quick_module/qmldir"
        fi
        if ((link)) && [[ -L $kirigami_link && $(readlink "$kirigami_link") == "$kirigami_desktop" && ! -e $plugins/styles/platinumstyle.so ]]; then
            rm -f "$kirigami_link"
        fi
        rm -f "$script"
        # Each branch is deepest first. Shared ancestors may still hold the
        # other branch on the first visit and become empty on the last.
        for dir in "${dirs[@]}"; do rmdir "$dir" 2> /dev/null || true; done
    done
    return 0
}

# --- Plasma's shell ---------------------------------------------------------
#
# plasmashell writes its panel layout when it quits, so the layout file can
# only be put back while it isn't running.

shell_how=""
shell_resumed=0
# Written while uninstall.sh has the shell stopped; a later run starts it
# again if this one couldn't (finding 38).
shell_marker=$state/shell-stopped

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
        if ((!dry_run)); then
            printf 'systemd\n' > "$shell_marker"
            systemctl --user stop plasma-plasmashell.service || return 1
        fi
        shell_how=systemd
    elif shell_running_on_bus; then
        have kquitapp6 || return 1
        plan "stop Plasma's shell (kquitapp6 plasmashell)"
        if ((!dry_run)); then
            printf 'direct\n' > "$shell_marker"
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

# Starts the shell shell_stop stopped; fails if it doesn't come up.
shell_start() {
    local i
    case $shell_how in
        systemd)
            plan "start Plasma's shell again"
            ((dry_run)) && return 0
            systemctl --user start plasma-plasmashell.service || return 1
            ;;
        direct)
            plan "start Plasma's shell again"
            ((dry_run)) && return 0
            setsid -f plasmashell > /dev/null 2>&1 < /dev/null || return 1
            for ((i = 0; i < 100; i++)); do
                shell_running_on_bus && break
                sleep 0.2
            done
            shell_running_on_bus || return 1
            ;;
        *) return 0 ;;
    esac
    rm -f "$shell_marker"
    shell_how=""
}

# Starts the shell if an earlier run stopped it and couldn't start it again.
shell_resume() {
    [[ -f $shell_marker && ! -L $shell_marker ]] || return 0
    shell_how=$(< "$shell_marker")
    case $shell_how in
        systemd) systemctl --user is-active --quiet plasma-plasmashell.service 2> /dev/null && shell_how=done ;;
        direct) shell_running_on_bus && shell_how=done ;;
        *) shell_how=done ;;
    esac
    if [[ $shell_how == done ]]; then
        shell_how=""
        ((dry_run)) || rm -f "$shell_marker"
        return 0
    fi
    plan "start Plasma's shell, which an earlier uninstall.sh stopped"
    shell_start || return 1
    shell_resumed=1
    say "Started Plasma's shell again (an earlier uninstall.sh had stopped it)"
}

shell_failed_message="couldn't start Plasma's shell again. Run uninstall.sh again to retry, or start it yourself: systemctl --user start plasma-plasmashell.service (or: setsid -f plasmashell)"
