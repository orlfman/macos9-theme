#!/bin/bash
# Runs dev/plasma-test.sh and compares the menu bar with the captures: a
# column of the empty bar (desktop-first-check.png, x=700), the bar's two
# rounded ends and the divider before the Application menu, and a column of
# an open menu title (menu-file-open.png "File", x=40, 3 px into the title),
# and the dock's top corners against the pop-up window tab.
# The title's x depends on the font, so it's found by its #333399 fill.
#
# usage: check-plasma.sh        (exit 1 if anything differs)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
cd "$project"
M9_CHECK_RESIZE=1 dev/plasma-test.sh > /dev/null
python3 -I - << 'PYEND'
import sys
from PIL import Image
desk = Image.open("dev/shots/plasma-platinum-desktop.png").convert("RGB")
menu = Image.open("dev/shots/plasma-platinum-menu.png").convert("RGB")
ref_bar = Image.open("reference/desktop-first-check.png").convert("RGB")
ref_title = Image.open("reference/menu-file-open.png").convert("RGB")
col = lambda im, x: [im.getpixel((x, y)) for y in range(20)]
failed = 0
def report(name, a, b):
    global failed
    bad = sum(p != q for p, q in zip(a, b))
    print(f"{'ok' if not bad else 'DIFF':<8}{name:<30}{bad} of {len(a)}")
    failed += bool(bad)
report("menubar-column", col(desk, 700), col(ref_bar, 700))
# The rounded ends (8 px each) and the divider before the Application menu
# (6 px, found by its white column and grip), all 20 rows.
def block(im, x0, width, height=20):
    return [im.getpixel((x, y)) for y in range(height) for x in range(x0, x0 + width)]
report("menubar-left-end", block(desk, 0, 8), block(ref_bar, 0, 8))
report("menubar-right-end", block(desk, desk.width - 8, 8), block(ref_bar, ref_bar.width - 8, 8))
div = next((x for x in range(desk.width - 400, desk.width - 8)
            if all(desk.getpixel((x, y)) == (255, 255, 255) for y in range(18))
            and desk.getpixel((x + 2, 4)) == (0x88, 0x88, 0x88)), None)
if div is None:
    print("DIFF    menubar-divider               not found")
    failed += 1
else:
    report("menubar-divider", block(desk, div, 6), block(ref_bar, 1349, 6))
xs = [x for x in range(desk.width) if menu.getpixel((x, 10)) == (0x33, 0x33, 0x99)]
if not xs:
    print("DIFF    menubar-open-title            no open title found")
    sys.exit(1)
report("menubar-open-title", col(menu, xs[0] + 3), col(ref_title, 40))
# The dock against Mac OS 9's pop-up window tab (finder-popup-tab.png, outline
# from x=632, y=1061): its top corners, 8 columns x 8 rows each, where the
# capture shows the tab (gray pixels; the desktop shows around it). The dock
# is found by its top black row at the screen's bottom.
tab = Image.open("reference/finder-popup-tab.png").convert("RGB")
H = desk.height
top = next(y for y in range(H - 120, H) if desk.getpixel((desk.width // 2, y)) == (0, 0, 0))
row = [x for x in range(desk.width) if desk.getpixel((x, top)) == (0, 0, 0)]
x0, x1 = row[0] - 2, row[-1] + 2
gray = lambda p: p[0] == p[1] == p[2]
def masked(name, rx, ox):
    a = [(desk.getpixel((ox + i, top + j)), tab.getpixel((rx + i, 1061 + j))) for i in range(8) for j in range(8)]
    a = [(o, r) for o, r in a if gray(r)]
    report(name, [o for o, _ in a], [r for _, r in a])
masked("dock-top-left", 632, x0)
masked("dock-top-right", 811, x1 - 6)
# The native bar supplies the colors. For taller bars, compare every pixel
# in each piece at the expected width, including all the bevel and grip rows.
def resized_rows(x, width, height, rows):
    scaled_width = (width * height + 10) // 20
    # Nearest pixel boundaries, with ties rounding up.
    edges = [(i * scaled_width * 2 + width) // (2 * width) for i in range(width + 1)]
    scaled_rows = []
    for y in range(20):
        row = []
        for i in range(width):
            row.extend([ref_bar.getpixel((x + i, y))] * (edges[i + 1] - edges[i]))
        scaled_rows.append(row)
    return [pixel for y in rows for pixel in scaled_rows[y]]

for height in (32, 34, 38, 40):
    large = Image.open(f"dev/shots/plasma-platinum-resized-{height}.png").convert("RGB")
    corner_width = (8 * height + 10) // 20
    corner_rows = [y * 18 // (height - 2) for y in range(height - 2)] + [18, 19]
    report(f"resized-{height}-left-end", block(large, 0, corner_width, height),
           resized_rows(0, 8, height, corner_rows))
    report(f"resized-{height}-right-end", block(large, large.width - corner_width, corner_width, height),
           resized_rows(ref_bar.width - 8, 8, height, corner_rows))

    # Locate the divider by its tall white leading stripe. The grip itself
    # is checked below, even if the dots are missing.
    white = (255, 255, 255)
    starts = [x for x in range(large.width - 400, large.width - 12)
              if all(large.getpixel((x, y)) == white for y in (1, 2, height - 4))
              and large.getpixel((x - 1, height - 4)) != white]
    if len(starts) != 1:
        print(f"DIFF    resized-{height}-divider             {len(starts)} locations found")
        failed += 1
        continue
    div = starts[0]
    divider_rows = [0, 1, 2, 3] + [15] * (height - 6) + [18, 19]
    for y in range(4, height - 6, 3):
        divider_rows[y:y + 2] = [4, 5]
    divider_width = (6 * height + 10) // 20
    report(f"resized-{height}-divider", block(large, div, divider_width, height),
           resized_rows(1349, 6, height, divider_rows))
sys.exit(1 if failed else 0)
PYEND
