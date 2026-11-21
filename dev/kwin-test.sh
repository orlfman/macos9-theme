#!/bin/bash
# Smoke test in a real KWin: starts a headless nested KWin (virtual backend,
# its own private D-Bus, sandboxed config), opens two windows and screenshots
# them into dev/shots/kwin-SCHEME.png. Nothing on your real desktop is touched.
#
# usage: kwin-test.sh [SCHEME]   (platinum, breeze or user; default breeze)
#   M9_STYLE       Union style (default breeze)
#   M9_DECORATION  KDecoration plugin id (default org.kde.breeze); when
#                  ../decoration/build/plugins exists it's put on QT_PLUGIN_PATH
#   M9_SIZE        virtual screen size (default 1100x620)
#   VT_MAXIMIZED=1 opens one maximized window instead, into kwin-SCHEME-max.png
#
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
scheme=${1:-breeze}

mkdir -p "$dev/shots"
suffix=
[[ ${VT_MAXIMIZED:-0} == 1 ]] && suffix=-max
export VT_OUT=$dev/shots/kwin-$scheme$suffix.png
rm -f "$VT_OUT"

# run.sh puts the config under this folder; give KWin its own kwinrc there.
config=$dev/build/sandbox/home-$scheme/config
mkdir -p "$config"
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key library "${M9_DECORATION:-org.kde.breeze}"
kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key theme ""

if [[ -d $project/decoration/build/plugins ]]; then
    export QT_PLUGIN_PATH=$project/decoration/build/plugins
fi
size=${M9_SIZE:-1100x620}
log=${VT_OUT%.png}.log
PLATFORM=wayland timeout 60 "$dev/run.sh" "$scheme" "${M9_STYLE:-breeze}" \
    env -u WAYLAND_DISPLAY dbus-run-session -- \
    kwin_wayland --virtual --width "${size%x*}" --height "${size#*x}" \
    --no-lockscreen --no-global-shortcuts --no-kactivities \
    --socket macos9-kwin-test --exit-with-session "$dev/kwin-session.sh" \
    > "$log" 2>&1 || true

if [[ -s $VT_OUT ]]; then
    echo "ok      $VT_OUT"
else
    echo "FAILED  $VT_OUT (see $log)"
    exit 1
fi
