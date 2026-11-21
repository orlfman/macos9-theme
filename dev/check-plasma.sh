#!/bin/bash
# Runs dev/plasma-test.sh and compares the menu bar with the captures: a
# column of the empty bar (desktop-first-check.png, x=700) and a column of an
# open menu title (menu-file-open.png "File", x=40, 3 px into the title).
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
xs = [x for x in range(desk.width) if menu.getpixel((x, 10)) == (0x33, 0x33, 0x99)]
if not xs:
    print("DIFF    menubar-open-title            no open title found")
    sys.exit(1)
report("menubar-open-title", col(menu, xs[0] + 3), col(ref_title, 40))
sys.exit(1 if failed else 0)
PYEND
