#!/bin/bash
# Renders the Firefox Milestone 2 visual mockups and side-by-side comparison
# sheets inside isolated nested virtual KWin (Platinum decoration + Platinum
# GTK 3 theme, never touches ~/.mozilla or ~/.config/mozilla).
#
# Output PNGs: dev/shots/firefox-m2-*.png
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(readlink -f "$0")")
mkdir -p "$dev/build" "$dev/shots"

work=$(mktemp -d "$dev/build/firefox-m2.XXXXXX")
trap 'rm -rf "$work" 2>/dev/null || true' EXIT

M9_M2_WORK="$work" python3 -I -W error "$dev/firefox-m2/render_mockups.py"
