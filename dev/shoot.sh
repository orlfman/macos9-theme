#!/bin/bash
# Renders the test galleries into dev/shots/ (builds the test programs first if
# needed). Needs a running Wayland session for the QtQuick renders.
#
# usage: shoot.sh [STYLE] [SCHEME...]
#   STYLE       a Union style id (a folder under ../style/) or breeze (default)
#   SCHEME      platinum, breeze, user or a .colors file (default: breeze)
#   FONT, SCALE, EXTRA_FONT_DIRS passed on to run.sh
#
# Outputs per scheme: STYLE-SCHEME-widgets.png (+ -widgets-menu, -widgets-dialog,
# -widgets-focus), STYLE-SCHEME-quick.png and STYLE-SCHEME-kirigami.png, each
# with a .log. TAG=name adds -name to every file name.
#
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")

style=${1:-breeze}
[[ $# -gt 0 ]] && shift
schemes=("$@")
[[ ${#schemes[@]} -gt 0 ]] || schemes=(breeze)
tag=${TAG:+-$TAG}

if [[ -z ${WAYLAND_DISPLAY:-} ]]; then
    echo "shoot.sh: no Wayland session, QtQuick renders need one" >&2
    exit 1
fi
for tool in gallery quickshot; do
    if [[ ! -x $dev/build/$tool || $dev/$tool.cpp -nt $dev/build/$tool ]]; then
        "$dev/build.sh" > /dev/null
        break
    fi
done
mkdir -p "$dev/shots"

failed=0
render() { # output.png command...
    local out=$1
    shift
    rm -f "$out"
    if ! timeout 30 "$@" > "${out%.png}.log" 2>&1 || [[ ! -s $out ]]; then
        echo "FAILED  $out (see ${out%.png}.log)"
        failed=1
    else
        echo "ok      $out"
    fi
}

for scheme in "${schemes[@]}"; do
    name=$(basename "$scheme" .colors)
    base=$dev/shots/$style-$name$tag
    rm -f "$base-widgets-menu.png" "$base-widgets-dialog.png" "$base-widgets-focus.png"
    render "$base-widgets.png" "$dev/run.sh" "$scheme" "$style" "$dev/build/gallery" "$base-widgets.png"
    render "$base-quick.png" env PLATFORM=wayland "$dev/run.sh" "$scheme" "$style" \
        "$dev/build/quickshot" "$dev/gallery.qml" "$base-quick.png"
    render "$base-kirigami.png" env PLATFORM=wayland "$dev/run.sh" "$scheme" "$style" \
        "$dev/build/quickshot" "$dev/kirigami.qml" "$base-kirigami.png"
done

exit $failed
