#!/bin/bash
# Review the libadwaita layer by hand: dev/live-test.sh's nested KWin window
# with the Platinum GTK theme and gtk-4.0/libadwaita.css loaded from the
# sandbox's user stylesheet (dev/build/sandbox, nothing installed; your own
# ~/.config/gtk-4.0 is not touched).
#
# usage: live-adw.sh [COMMAND...]
#   default: the stock libadwaita fixture, FFmpeg Converter GTK, Mission
#   Center and gtk4-widget-factory (plain GTK 4, for comparison)
#   M9_PLASMA defaults to 0 here (no Plasma shell); other M9_* as live-test.sh
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
scheme=${M9_SCHEME:-platinum}
home=$dev/build/sandbox/home-$scheme
mkdir -p "$home/data/themes" "$home/config/gtk-4.0"
ln -sfn "$project/gtk/Platinum" "$home/data/themes/Platinum"
printf '@import url("file://%s");\n' "$home/data/themes/Platinum/gtk-4.0/libadwaita.css" \
    > "$home/config/gtk-4.0/gtk.css"
printf '[Settings]\ngtk-theme-name=Platinum\n' > "$home/config/gtk-4.0/settings.ini"
if [[ $# -eq 0 ]]; then
    set -- bash -c "python3 -I '$dev/adw-check/fixture.py' live /dev/null & ffmpeg-converter-gtk & missioncenter & gtk4-widget-factory & wait"
fi
M9_PLASMA=${M9_PLASMA:-0} exec "$dev/live-test.sh" "$@"
