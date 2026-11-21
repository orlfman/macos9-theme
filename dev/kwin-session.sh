#!/bin/bash
# Runs inside the nested KWin started by kwin-test.sh: opens two windows (or
# one maximized window when VT_MAXIMIZED=1), screenshots the whole virtual
# screen into $VT_OUT, then exits, which ends the nested KWin.
dev=$(dirname "$(readlink -f "$0")")
qml=/usr/lib/qt6/bin/qml
if [[ ${VT_SINGLE:-0} == 1 ]]; then
    "$qml" "$dev/kwin-window.qml" -- "Mac OS" &
elif [[ ${VT_MAXIMIZED:-0} == 1 ]]; then
    "$qml" "$dev/kwin-window.qml" -- maximized "Home — Dolphin" &
else
    "$qml" "$dev/kwin-window.qml" -- "Konsole" &
    sleep 1
    "$qml" "$dev/kwin-window.qml" -- "Home — Dolphin" &
fi
sleep 2
spectacle -b -n -f -o "$VT_OUT"
sleep 1
kill $(jobs -p) 2> /dev/null
