#!/bin/bash
# Compares the Platinum Qt Quick Controls style's pieces with their widget
# counterparts pixel for pixel: menus (first / last row selected), the
# combo box's open list, the menu bar, a switch's indicator (a check box)
# and a tooltip. Both sides draw through the same QStyle, so any difference
# is a layout or context difference (PLAN.md "Plan: Qt Quick menus,
# tooltips and switches", step 7). Then the same pieces after the app is
# switched to Fusion while running must equal KDE's own style under Fusion. Sandboxed like dev/run.sh, offscreen,
# with Qt Quick's software renderer.
#
# usage: check-quick.sh    (exit 1 if a region differs)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
out=$dev/build/check-quick
rm -rf "$out"
mkdir -p "$out"

"$project/style/build.sh" > /dev/null
"$project/style/quick/build.sh" > /dev/null
[[ -x $dev/build/quickshot && $dev/build/quickshot -nt $dev/quickshot.cpp ]] || "$dev/build.sh" > /dev/null
g++ -std=c++17 -O1 -fPIC "$dev/quickref.cpp" -o "$dev/build/quickref" $(pkg-config --cflags --libs Qt6Widgets)

QSTYLE=Platinum "$dev/run.sh" platinum breeze "$dev/build/quickref" "$out/widget" > "$out/widget.log" 2>&1
M9_QUICK=1 QSTYLE=Platinum "$dev/run.sh" platinum breeze env QT_QUICK_BACKEND=software \
    "$dev/build/quickshot" "$dev/quick-regions.qml" "$out/quick.png" > "$out/quick.log" 2>&1

# The fallback: switched to another style while running, the pieces must
# look exactly like KDE's own style under that style.
M9_QUICK=1 QSTYLE=Platinum "$dev/run.sh" platinum breeze env QT_QUICK_BACKEND=software M9_QUICK_TEST=1 \
    "$dev/build/quickshot" "$dev/quick-regions.qml" "$out/fallback.png" --switch-to-fusion > "$out/fallback.log" 2>&1
QSTYLE=Fusion "$dev/run.sh" platinum breeze env QT_QUICK_BACKEND=software QT_QUICK_CONTROLS_STYLE=org.kde.desktop \
    "$dev/build/quickshot" "$dev/quick-regions.qml" "$out/kde.png" > "$out/kde.log" 2>&1

python3 -I - "$out" << 'PY'
import re, sys
from PIL import Image, ImageChops
out = sys.argv[1]
steps = {"menu-0": 0, "menu-1": 1, "combo": 2, "menubar": 3, "checkbox": 4, "tooltip": 5}
where = {}
for line in open(f"{out}/quick.log"):
    m = re.search(r"REGION (\S+) (-?[\d.]+) (-?[\d.]+)", line)
    if m:
        where[m.group(1)] = (round(float(m.group(2))), round(float(m.group(3))))
failed = 0
for name, step in steps.items():
    try:
        widget = Image.open(f"{out}/widget-{name}.png").convert("RGBA")
    except FileNotFoundError:
        print(f"FAIL    {name:10} no widget render"); failed += 1; continue
    if name not in where:
        print(f"FAIL    {name:10} the Qt Quick scene didn't say where it is"); failed += 1; continue
    x, y = where[name]
    quick = Image.open(f"{out}/quick-{step}.png").convert("RGB").crop((x, y, x + widget.width, y + widget.height))
    # See-through widget pixels show the window's magenta on the Qt Quick side.
    magenta = Image.new("RGBA", widget.size, (255, 0, 255, 255))
    expected = Image.alpha_composite(magenta, widget).convert("RGB")
    diff = ImageChops.difference(expected, quick)
    n = sum(1 for p in diff.get_flattened_data() if p != (0, 0, 0))
    # The Qt Quick piece must really be there (not just magenta).
    drawn = sum(1 for p in quick.get_flattened_data() if p != (255, 0, 255))
    if n == 0 and drawn > 0:
        print(f"ok      {name:10} {widget.width}x{widget.height} at {x},{y}")
    else:
        failed += 1
        print(f"FAIL    {name:10} {n} of {widget.width * widget.height} px differ (bbox {diff.getbbox()}), {drawn} drawn")
        diff.point(lambda v: 255 if v else 0).save(f"{out}/diff-{name}.png")
for name, step in steps.items():
    a = Image.open(f"{out}/fallback-{step}.png").convert("RGB")
    b = Image.open(f"{out}/kde-{step}.png").convert("RGB")
    diff = ImageChops.difference(a, b)
    n = sum(1 for p in diff.get_flattened_data() if p != (0, 0, 0))
    if n == 0:
        print(f"ok      {name:10} after switching to Fusion: the same as KDE's style")
    else:
        failed += 1
        print(f"FAIL    {name:10} after switching to Fusion: {n} px differ from KDE's style (bbox {diff.getbbox()})")
        diff.point(lambda v: 255 if v else 0).save(f"{out}/diff-fallback-{name}.png")
total = 2 * len(steps)
print(f"\n{total - failed} of {total} Qt Quick checks pixel exact" + (f" (diffs in {out})" if failed else ""))
sys.exit(1 if failed else 0)
PY
