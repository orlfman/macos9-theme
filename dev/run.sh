#!/bin/bash
# Runs a command against this project's style, sandboxed so nothing touches
# your real setup: its own XDG folders under dev/build/sandbox, no D-Bus, Qt
# logging to stderr instead of the journal, and offscreen rendering. QtQuick
# needs the GPU, so set PLATFORM=wayland for it: the window is rendered and
# grabbed but never shown.
#
# usage: run.sh SCHEME STYLE command...
#   SCHEME  platinum  this project's colors/Platinum.colors (once it exists)
#           breeze    stock Breeze Light, to compare
#           user      a copy of your current ~/.config/kdeglobals
#           or a path to any .colors file
#   STYLE   Union style id: any folder under ../style/, or breeze to compare
#   FONT    optional, e.g. FONT="Some Font,9" renders with that font instead
#           of borrowing yours (TITLEFONT for window titles)
#   EXTRA_FONT_DIRS  optional, colon-separated font folders made visible to
#           the sandbox only (stand-in fonts without installing them)
#   SCALE   optional, Qt scale factor (default 1)
#   QSTYLE  optional, a QStyle instead of Union (e.g. Fusion, Windows)
#
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
sandbox=$dev/build/sandbox

if [[ $# -lt 3 ]]; then
    awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"
    exit 1
fi
scheme=$1 style=$2
shift 2

case $scheme in
    platinum) colors=$project/colors/Platinum.colors ;;
    breeze) colors=/usr/share/color-schemes/BreezeLight.colors ;;
    user) colors=${XDG_CONFIG_HOME:-$HOME/.config}/kdeglobals ;;
    *.colors) colors=$scheme
        scheme=$(basename "$scheme" .colors) ;;
    *) echo "run.sh: unknown scheme '$scheme' (platinum, breeze, user or a .colors file)" >&2; exit 1 ;;
esac
if [[ ! -f $colors ]]; then
    echo "run.sh: no color scheme at $colors" >&2
    exit 1
fi

# Make this project's Union styles visible. The links are refreshed on every
# run, so edits under style/ show up right away and the project can move.
mkdir -p "$sandbox/data/union/styles"
for dir in "$project"/style/*/; do
    [[ -d $dir ]] || continue
    ln -sfn "${dir%/}" "$sandbox/data/union/styles/$(basename "$dir")"
done
# Named icons the style uses go to hicolor, which every icon theme falls back to.
if compgen -G "$project/icons/style/*.svg" > /dev/null; then
    mkdir -p "$sandbox/data/icons/hicolor/scalable/actions"
    for icon in "$project"/icons/style/*.svg; do
        ln -sfn "$icon" "$sandbox/data/icons/hicolor/scalable/actions/$(basename "$icon")"
    done
fi

home=$sandbox/home-$scheme
mkdir -p "$home"/{config,data,cache,state}
cp "$colors" "$home/config/kdeglobals"
globals=$home/config/kdeglobals
if [[ $scheme != user ]]; then
    # Borrow your fonts so the renders match your desktop.
    for key in font fixed menuFont smallestReadableFont toolBarFont; do
        value=$(kreadconfig6 --file kdeglobals --group General --key "$key")
        if [[ -n $value ]]; then
            kwriteconfig6 --file "$globals" --group General --key "$key" "$value"
        fi
    done
    value=$(kreadconfig6 --file kdeglobals --group WM --key activeFont)
    if [[ -n $value ]]; then
        kwriteconfig6 --file "$globals" --group WM --key activeFont "$value"
    fi
fi
if [[ -n ${FONT:-} ]]; then
    for key in font menuFont toolBarFont smallestReadableFont; do
        kwriteconfig6 --file "$globals" --group General --key "$key" "$FONT"
    done
    kwriteconfig6 --file "$globals" --group WM --key activeFont "${TITLEFONT:-$FONT}"
fi
kwriteconfig6 --file "$globals" --group KDE --key widgetStyle Union
kwriteconfig6 --file "$globals" --group KDE --key unionStyle "$style"

# A fontconfig for the sandbox: the system's, plus EXTRA_FONT_DIRS.
mkdir -p "$sandbox/fontconfig"
{
    echo '<?xml version="1.0"?>'
    echo '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">'
    echo '<fontconfig>'
    echo '  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
    IFS=: read -r -a extra <<< "${EXTRA_FONT_DIRS:-}"
    for dir in "${extra[@]}"; do
        [[ -n $dir ]] && echo "  <dir>$dir</dir>"
    done
    echo '</fontconfig>'
} > "$sandbox/fontconfig/fonts.conf"

export XDG_CONFIG_HOME=$home/config XDG_DATA_HOME=$home/data
export XDG_CACHE_HOME=$home/cache XDG_STATE_HOME=$home/state
export XDG_DATA_DIRS=$sandbox/data:/usr/local/share:/usr/share
export FONTCONFIG_FILE=$sandbox/fontconfig/fonts.conf
export DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent
export QT_FORCE_STDERR_LOGGING=1
export QT_QPA_PLATFORM=${PLATFORM:-offscreen} QT_QPA_PLATFORMTHEME=kde QT_STYLE_OVERRIDE=${QSTYLE:-Union}
export QT_SCALE_FACTOR=${SCALE:-1}
export UNION_STYLE_NAME=$style UNION_DISABLE_STYLE_CACHE=1
if [[ $QT_QPA_PLATFORM != wayland ]]; then
    unset WAYLAND_DISPLAY
fi
unset DISPLAY
exec "$@"
