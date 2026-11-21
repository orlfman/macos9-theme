#!/bin/bash
# Shows the Plasma style and the menu bar layout in a real Plasma shell
# without touching your desktop: a headless nested KWin (virtual screen,
# private D-Bus, sandbox config) with this project's decoration and style
# runs plasmashell with a FRESH layout (plasma/layout.js; your own panel
# files aren't read), starts dev/build/livedemo (its menus go to the global
# menu), and screenshots dev/shots/plasma-*.png: the desktop, an open menu
# title, the open launcher.
#
# usage: plasma-test.sh [THEME]
#   THEME   platinum (default) or default (Breeze, for comparison)
#   M9_SIZE  virtual screen size (default 1440x900)
#   M9_APPLY=lnf  apply the look-and-feel package (plasma-apply-lookandfeel
#            --resetLayout, inside the sandbox) instead of evaluating
#            plasma/layout.js directly; the sandbox's kdeglobals, kwinrc and
#            plasmarc are reset to Breeze values first, so the check below
#            shows what the package set
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
theme=${1:-platinum}

python3 -I "$project/plasma/make-plasma.py" > /dev/null
"$project/style/build.sh" > /dev/null
"$project/decoration/build.sh" > /dev/null
# shellcheck disable=SC2046
g++ -std=c++17 -O1 -fPIC "$dev/livedemo.cpp" -o "$dev/build/livedemo" $(pkg-config --cflags --libs Qt6Widgets)
sandbox=$dev/build/sandbox
mkdir -p "$sandbox/data/plasma/desktoptheme" "$dev/shots"
ln -sfn "$project/plasma/platinum" "$sandbox/data/plasma/desktoptheme/platinum"
mkdir -p "$sandbox/data/plasma/plasmoids" "$sandbox/data/plasma/look-and-feel"
ln -sfn "$project/plasma/look-and-feel/platinum.desktop" "$sandbox/data/plasma/look-and-feel/platinum.desktop"
ln -sfn "$project/plasma/plasmoids/platinum.menubarpiece" "$sandbox/data/plasma/plasmoids/platinum.menubarpiece"

# run.sh keeps the platinum scheme's config here. Start from a clean
# layout every time (sandbox files only).
config=$sandbox/home-platinum/config
mkdir -p "$config"
rm -f "$config/plasma-org.kde.plasma.desktop-appletsrc" "$config/plasmashellrc"
# Its own empty Desktop folder (the desktop would show yours otherwise).
mkdir -p "$sandbox/desktop"
printf 'XDG_DESKTOP_DIR="%s"\n' "$sandbox/desktop" > "$config/user-dirs.dirs"
kwriteconfig6 --file "$config/plasmarc" --group Theme --key name "$theme"
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key library platinum
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key theme ""
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft X
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight AI

if [[ ${M9_APPLY:-} == lnf ]]; then
    kwriteconfig6 --file "$config/plasmarc" --group Theme --key name default
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key library org.kde.breeze
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft --delete
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight --delete
fi
export M9_APPLY=${M9_APPLY:-}
# A Plasma session reads a global theme's values from kdedefaults (startplasma
# puts it on the config search path); so does this one.
export XDG_CONFIG_DIRS=$config/kdedefaults:/etc/xdg
size=${M9_SIZE:-1440x900}
export M9_OUT=$dev/shots/plasma-$theme M9_LAYOUT=$project/plasma/layout.js
rm -f "$M9_OUT"-*.png
QSTYLE=Platinum PLATFORM=wayland timeout 150 "$dev/run.sh" platinum breeze \
    env -u WAYLAND_DISPLAY dbus-run-session -- \
    kwin_wayland --virtual --width "${size%x*}" --height "${size#*x}" \
    --no-lockscreen --no-global-shortcuts --no-kactivities \
    --socket macos9-plasma-test --exit-with-session "$dev/plasma-session.sh" \
    > "$M9_OUT.kwin.log" 2>&1 || true

if [[ $M9_APPLY == lnf ]]; then
    for f in "kdeglobals KDE widgetStyle" "kdeglobals General ColorScheme" "plasmarc Theme name" \
        "kwinrc org.kde.kdecoration2 library" "kdeglobals Icons Theme" "kcminputrc Mouse cursorTheme"; do
        set -- $f
        printf 'applied %-12s %-24s %s\n' "$1" "[$2] $3" "$(XDG_CONFIG_HOME=$config kreadconfig6 --file "$1" --group "$2" --key "$3")"
    done
fi
for shot in desktop menu launcher; do
    if [[ -s $M9_OUT-$shot.png ]]; then
        echo "ok      $M9_OUT-$shot.png"
    else
        echo "FAILED  $M9_OUT-$shot.png (see $M9_OUT.plasmashell.log)"
    fi
done
