#!/bin/bash
# Runs dev/plasma-test.sh and compares the menu bar with the captures: a
# column of the empty bar (desktop-first-check.png, x=700), the bar's two
# rounded ends and the divider before the Application menu, and a column of
# an open menu title (menu-file-open.png "File", x=40, 3 px into the title).
# The title's x depends on the font, so it's found by its #333399 fill.
#
# usage: check-plasma.sh        (exit 1 if anything differs)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
cd "$project"
dev/plasma-test.sh > /dev/null
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
block = lambda im, x0, w: [im.getpixel((x, y)) for x in range(x0, x0 + w) for y in range(20)]
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
sys.exit(1 if failed else 0)
PYEND
