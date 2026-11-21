#!/bin/bash
# Runs inside the nested KWin started by live-test.sh: with M9_PLASMA=1
# starts the Plasma shell with plasma/layout.js first, then the apps in
# $M9_APPS, and waits until all apps are closed, which ends the nested KWin.
if [[ ${M9_PLASMA:-0} == 1 ]]; then
    # Plasma needs the activity manager (started directly: this private bus
    # has no systemd) and kded6 (the global menu's registrar).
    /usr/lib/kactivitymanagerd > "$M9_LOGDIR/live-activities.log" 2>&1 &
    kded6 > "$M9_LOGDIR/live-kded.log" 2>&1 &
    sleep 1
    plasmashell --no-respawn > "$M9_LOGDIR/live-plasmashell.log" 2>&1 &
    sleep 6
    qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat "$M9_LAYOUT")" > "$M9_LOGDIR/live-layout.log" 2>&1
    sleep 2
fi
services=" $(jobs -p | tr '\n' ' ') "
eval "$M9_APPS &"
apps=()
for pid in $(jobs -p); do
    [[ $services == *" $pid "* ]] || apps+=("$pid")
done
wait "${apps[@]}"
