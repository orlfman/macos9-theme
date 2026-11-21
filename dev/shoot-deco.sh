#!/bin/bash
# Builds the window decoration and renders dev/decoration.qml with it into
# dev/shots/deco-SCHEME.png. Needs a running Wayland session (the preview is
# QtQuick); nothing is installed, the plugin is loaded from decoration/build.
#
# usage: shoot-deco.sh [SCHEME...]
#   SCHEME      platinum (default), breeze, user or a .colors file
#
# The sandbox's kwinrc gets the Mac OS 9 button layout: close on the left,
# zoom (maximize) and collapse (shade) on the right.
#
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")

schemes=("$@")
[[ ${#schemes[@]} -gt 0 ]] || schemes=(platinum)

if [[ -z ${WAYLAND_DISPLAY:-} ]]; then
    echo "shoot-deco.sh: no Wayland session, the preview needs one" >&2
    exit 1
fi
"$project/decoration/build.sh" > /dev/null
if [[ ! -x $dev/build/decoshot || $dev/decoshot.cpp -nt $dev/build/decoshot ]]; then
    "$dev/build.sh" > /dev/null
fi
mkdir -p "$dev/shots"

failed=0
for scheme in "${schemes[@]}"; do
    out=$dev/shots/deco-$scheme.png
    rm -f "$out"
    config=$dev/build/sandbox/home-$(basename "$scheme" .colors)/config
    mkdir -p "$config"
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft X
    kwriteconfig6 --file "$config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight AL
    if ! QT_PLUGIN_PATH=$project/decoration/build/plugins PLATFORM=wayland timeout 30 \
        "$dev/run.sh" "$scheme" breeze "$dev/build/decoshot" "$dev/decoration.qml" "$out" \
        > "${out%.png}.log" 2>&1 || [[ ! -s $out ]]; then
        echo "FAILED  $out (see ${out%.png}.log)"
        failed=1
        continue
    fi
    echo "ok      $out"
done
exit $failed
