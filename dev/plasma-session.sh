#!/bin/bash
# Runs inside the nested KWin started by plasma-test.sh: starts plasmashell,
# applies plasma/layout.js, starts the demo app, and takes the screenshots.
# M9_MENU_X (default 60) is where the first global menu title is clicked.
dev=$(dirname "$(readlink -f "$0")")
# Plasma needs the activity manager; its D-Bus service starts it through
# systemd, which this private bus doesn't have, so start it directly.
/usr/lib/kactivitymanagerd > "$M9_OUT.activities.log" 2>&1 &
# kded6 runs the global menu's registrar (its appmenu module), which apps
# need before they hand their menus to the panel.
kded6 > "$M9_OUT.kded.log" 2>&1 &
sleep 1
plasmashell --no-respawn > "$M9_OUT.plasmashell.log" 2>&1 &
sleep 8
if [[ ${M9_APPLY:-} == lnf ]]; then
    plasma-apply-lookandfeel --apply platinum.desktop --resetLayout > "$M9_OUT.layout.log" 2>&1
    sleep 2
    # A newly applied decoration and button order take a reconfigure.
    qdbus6 org.kde.KWin /KWin reconfigure >> "$M9_OUT.layout.log" 2>&1
else
    # The pixel comparisons use a solid backdrop to isolate panel artwork.
    qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat "$M9_LAYOUT")
        desktops().forEach(function (d) {
            d.wallpaperPlugin = 'org.kde.color';
            d.currentConfigGroup = ['Wallpaper', 'org.kde.color', 'General'];
            d.writeConfig('Color', '99,99,156');
        });" > "$M9_OUT.layout.log" 2>&1
fi
sleep 3
# A second window first, so the dock shows a running app that isn't the
# active one (raised bevel) next to the active one (selected bevel).
/usr/lib/qt6/bin/qml "$dev/kwin-window.qml" -- "Background" &
sleep 2
"$dev/build/livedemo" &
sleep 4
spectacle -b -n -f -o "$M9_OUT-desktop.png"
# Open the first global menu title with a real click (Wayland menus need
# a real input event).
"$dev/build/fakeinput" move "${M9_MENU_X:-60}" 9 sleep 300 click "${M9_MENU_X:-60}" 9 > /dev/null 2>&1
sleep 2
spectacle -b -n -f -o "$M9_OUT-menu.png"
"$dev/build/fakeinput" key 1 > /dev/null 2>&1
sleep 1
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.activateLauncherMenu
sleep 2
spectacle -b -n -f -o "$M9_OUT-launcher.png"
if [[ ${M9_CHECK_RESIZE:-0} == 1 ]]; then
    "$dev/build/fakeinput" key 1 move 200 200
    for height in 32 34 38 40; do
        qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript \
            "panels().filter(p => p.location == 'top').forEach(p => p.height = $height)"
        sleep 2
        spectacle -b -n -f -o "$M9_OUT-resized-$height.png"
    done
fi
kill $(jobs -p) 2> /dev/null
sleep 1
kill -9 $(jobs -p) 2> /dev/null
