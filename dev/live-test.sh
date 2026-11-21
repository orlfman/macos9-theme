#!/bin/bash
# Try the theme by hand: opens a nested KWin as a normal window on your
# desktop (windowed Wayland backend) with this project's decoration, style
# and colors, and starts apps in it. Everything is sandboxed like run.sh
# (own XDG folders under dev/build/sandbox, private D-Bus, nothing
# installed); your own desktop, config and running apps are not touched.
# Close the apps (or the nested KWin window) to end it.
#
# usage: live-test.sh [COMMAND...]
#   default: dev/build/livedemo (every themed control), Dolphin and Kate
#   M9_SIZE   nested screen size (default 1600x1000, drawn at 1x)
#   M9_SCHEME platinum (default), breeze or user, as for run.sh
#   FONT, TITLEFONT, EXTRA_FONT_DIRS as for run.sh
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
if [[ -z ${WAYLAND_DISPLAY:-} ]]; then
    echo "live-test.sh: needs a Wayland session (WAYLAND_DISPLAY is not set)" >&2
    exit 1
fi

"$project/style/build.sh" > /dev/null
"$project/decoration/build.sh" > /dev/null
mkdir -p "$dev/build"
# shellcheck disable=SC2046
g++ -std=c++17 -O1 -fPIC "$dev/livedemo.cpp" -o "$dev/build/livedemo" $(pkg-config --cflags --libs Qt6Widgets)

scheme=${M9_SCHEME:-platinum}
config=$dev/build/sandbox/home-$scheme/config
mkdir -p "$config"
# Platinum decoration with the Mac OS 9 button layout: close box left, zoom
# and collapse right (collapse = minimize: KWin 6.8 can't shade Wayland
# windows).
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key library platinum
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key theme ""
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft X
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight AI

if [[ $# -gt 0 ]]; then
    M9_APPS=$(printf '%q ' "$@")
else
    M9_APPS="$(printf '%q' "$dev/build/livedemo") & dolphin --new-window /usr/share & kate"
fi
export M9_APPS
size=${M9_SIZE:-1600x1000}
log=$dev/build/live-test.log
echo "Starting the nested KWin (log: $log). Close its window to end."
# run.sh sandboxes the environment; PLATFORM=wayland keeps WAYLAND_DISPLAY,
# which the nested KWin needs to open its window on your desktop. Apps
# inside get the nested KWin's own socket.
QSTYLE=Platinum PLATFORM=wayland "$dev/run.sh" "$scheme" breeze \
    dbus-run-session -- \
    kwin_wayland --width "${size%x*}" --height "${size#*x}" \
    --no-lockscreen --no-global-shortcuts --no-kactivities \
    --socket macos9-live --exit-with-session "$dev/live-session.sh" \
    > "$log" 2>&1
