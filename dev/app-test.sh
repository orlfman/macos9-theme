#!/bin/bash
# Runs a real application with this project's style and decoration inside a
# headless nested KWin (virtual backend, private D-Bus, sandboxed config,
# nothing installed) and screenshots it into dev/shots/app-NAME.png.
#
# usage: app-test.sh NAME COMMAND [SCHEME]
#   e.g. app-test.sh dolphin "dolphin --new-window /usr/share"
#   SCHEME         platinum, breeze (default) or user
#   FONT, TITLEFONT, EXTRA_FONT_DIRS, SCALE as for run.sh
#   M9_WAIT        seconds before the shot (default 6)
#   M9_SIZE        virtual screen size (default 1280x800)
#   M9_STYLE       Union style (default breeze)
#   M9_DECORATION  KDecoration plugin id (default org.kde.breeze)
#
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
name=$1 app=$2 scheme=${3:-breeze}

mkdir -p "$dev/shots"
export M9_OUT=$dev/shots/app-$name.png M9_APP=$app
rm -f "$M9_OUT"

config=$dev/build/sandbox/home-$scheme/config
mkdir -p "$config"
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key library "${M9_DECORATION:-org.kde.breeze}"
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key theme ""
if [[ ${M9_DECORATION:-} == platinum ]]; then
    # Mac OS 9 layout: close box on the left, zoom and collapse on the right
    # (collapse = minimize: Wayland windows can't be shaded in KWin 6.8).
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft X
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight AI
else
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft --delete
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight --delete
fi

if [[ -d $project/decoration/build/plugins ]]; then
    export QT_PLUGIN_PATH=$project/decoration/build/plugins
fi
size=${M9_SIZE:-1280x800}
log=${M9_OUT%.png}.log
PLATFORM=wayland timeout 90 "$dev/run.sh" "$scheme" "${M9_STYLE:-breeze}" \
    env -u WAYLAND_DISPLAY dbus-run-session -- \
    kwin_wayland --virtual --width "${size%x*}" --height "${size#*x}" \
    --no-lockscreen --no-global-shortcuts --no-kactivities \
    --socket macos9-app-test --exit-with-session "$dev/app-session.sh" \
    > "$log" 2>&1 || true

if [[ -s $M9_OUT ]]; then
    echo "ok      $M9_OUT"
else
    echo "FAILED  $M9_OUT (see $log)"
    exit 1
fi
