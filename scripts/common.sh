# shellcheck shell=bash
# Shared by install.sh and uninstall.sh: where things go, what --apply
# backs up, and small helpers. Not meant to be run on its own.
# Adapted from the user's windows2000-union project (BSD-2-Clause).
#
# SPDX-License-Identifier: BSD-2-Clause

data=${XDG_DATA_HOME:-$HOME/.local/share}
config_home=${XDG_CONFIG_HOME:-$HOME/.config}
cache=${XDG_CACHE_HOME:-$HOME/.cache}
state_home=${XDG_STATE_HOME:-$HOME/.local/state}
state=$state_home/macos9-theme
# What install.sh put where, one "kind<TAB>path" per line, so uninstall.sh
# removes exactly that and nothing else.
manifest=$state/installed
# Copies of your config files from before the first --apply.
backup=$state/backup

# The compiled Qt style and KWin decoration live in your home; a Plasma
# login script puts this folder on Qt's plugin path (takes a new login).
plugins=$HOME/.local/lib/qt6/plugins
env_script=$config_home/plasma-workspace/env/macos9-theme.sh

scheme_name=Platinum
plasma_theme=platinum
piece_id=platinum.menubarpiece
lnf_id=platinum.desktop

# The config files (in ~/.config) the global theme and --apply change:
# applying a global theme rewrites the panel layout and moves settings into
# kdedefaults/, so whole files are kept, not single keys.
backup_files=(kdeglobals kwinrc plasmarc kcminputrc ksplashrc
    plasma-org.kde.plasma.desktop-appletsrc plasmashellrc)
backup_dirs=(kdedefaults)

dry_run=0

# What was done. A dry run shows the commands instead (see run).
say() {
    ((dry_run)) || printf '%s\n' "$*"
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

# Runs a command, or with --dry-run only shows it.
run() {
    if ((dry_run)); then
        printf '  would run:'
        printf ' %q' "$@"
        printf '\n'
    else
        "$@"
    fi
}

# Like run, but the command's own output is dropped (not the dry-run line).
run_quiet() {
    if ((dry_run)); then
        run "$@"
    else
        "$@" > /dev/null 2>&1
    fi
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

# Running KDE apps reload their widget style on this signal (2 = style).
notify_style() {
    if have dbus-send; then
        run dbus-send --session --type=signal /KGlobalSettings org.kde.KGlobalSettings.notifyChange int32:2 int32:0 2> /dev/null || true
    fi
}

reconfigure_kwin() {
    if have qdbus6; then
        run_quiet qdbus6 org.kde.KWin /KWin reconfigure || true
    fi
}

# Plasma caches rendered SVG pieces by style name; an update or removal has
# to drop them.
drop_plasma_caches() {
    local file
    for file in "$cache"/plasma_theme_"$plasma_theme"*.kcache "$cache"/plasma-svgelements-"$plasma_theme"* \
        "$cache"/ksvg-elements-"$plasma_theme"* "$cache"/ksvg-"$plasma_theme"*; do
        [[ -e $file ]] && run rm -rf "$file"
    done
    return 0
}

# The install record, kept in the order things were installed.
manifest_entries=()

manifest_load() {
    manifest_entries=()
    if [[ -f $manifest ]]; then
        mapfile -t manifest_entries < "$manifest"
    fi
}

manifest_add() { # kind path
    local entry existing
    entry=$(printf '%s\t%s' "$1" "$2")
    for existing in "${manifest_entries[@]}"; do
        [[ $existing == "$entry" ]] && return 0
    done
    manifest_entries+=("$entry")
}

# Writes the record through a temporary file, so it's never half written.
manifest_save() {
    ((dry_run)) && return 0
    mkdir -p "$state"
    if ((${#manifest_entries[@]} == 0)); then
        rm -f "$manifest"
        return 0
    fi
    printf '%s\n' "${manifest_entries[@]}" > "$manifest.new"
    mv -f "$manifest.new" "$manifest"
}

# Copies a folder in whole under a temporary name, then swaps it in, so
# Plasma never reads half a copy.
install_dir() { # source target
    run mkdir -p "$(dirname "$2")"
    run rm -rf "$2.new"
    run cp -r "$1" "$2.new"
    run rm -rf "$2"
    run mv "$2.new" "$2"
}
