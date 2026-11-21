#!/bin/bash
# Builds the test programs into dev/build/:
#   gallery    QtWidgets gallery, renders itself plus a menu and a dialog to PNG
#   quickshot  loads a QML file in a QApplication and saves the window to PNG
#   decoshot   renders decoration.qml (KWin's decoration preview) with hover and press states
#   tabdemo    presses Tab on itself inside a nested KWin (keyboard focus)
#   fakeinput  real pointer and key input inside the nested KWin
#
# Adapted from the user's windows2000-union project (BSD-2-Clause).
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
out=$dev/build
mkdir -p "$out"

# pkg-config output is meant to be word split here.
# shellcheck disable=SC2046
g++ -std=c++17 -O1 -fPIC "$dev/gallery.cpp" -o "$out/gallery" \
    $(pkg-config --cflags --libs Qt6Widgets)
# shellcheck disable=SC2046
g++ -std=c++17 -O1 -fPIC "$dev/quickshot.cpp" -o "$out/quickshot" \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Quick Qt6QuickControls2 Qt6Qml)
# shellcheck disable=SC2046
g++ -std=c++20 -O1 -fPIC "$dev/decoshot.cpp" -o "$out/decoshot" \
    -I/usr/include/KDecoration3 \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Quick Qt6Qml) -lkdecorations3
# shellcheck disable=SC2046
g++ -std=c++20 -O1 -fPIC "$dev/tabdemo.cpp" -o "$out/tabdemo" $(pkg-config --cflags --libs Qt6Widgets)

# The fake input client: protocol code from wayland-scanner, then the
# .desktop file listing the restricted interface for its exact path, which
# KWin checks before it offers the protocol.
wayland-scanner client-header "$dev/protocols/fake-input.xml" "$out/fake-input-client-protocol.h"
wayland-scanner private-code "$dev/protocols/fake-input.xml" "$out/fake-input-protocol.c"
# shellcheck disable=SC2046
gcc -O1 -Wall -Wextra -I"$out" "$dev/fakeinput.c" "$out/fake-input-protocol.c" -o "$out/fakeinput" \
    $(pkg-config --cflags --libs wayland-client)
mkdir -p "$out/sandbox/data/applications"
printf '%s\n' '[Desktop Entry]' 'Type=Application' 'Name=macos9-theme test input' \
    "Exec=$out/fakeinput" 'NoDisplay=true' 'X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input' \
    > "$out/sandbox/data/applications/m9-fakeinput.desktop"

echo "Built gallery, quickshot, decoshot, tabdemo and fakeinput in $out"
