#!/bin/bash
# Bottom tabs (Konsole, Kwi): checks that they are the measured top tabs
# upside down (dev/tabcheck.cpp), offscreen, and that a Qt Quick footer
# TabBar (dev/tabs-quick.qml, through KDE's bridge) is the header upside down.
#   usage: check-tabs.sh   (exit 1 on a failure)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
"$project/style/build.sh" > /dev/null
mkdir -p "$dev/build"
g++ -std=c++20 -O1 -fPIC "$dev/tabcheck.cpp" -o "$dev/build/tabcheck" $(pkg-config --cflags --libs Qt6Widgets)
status=0
QT_PLUGIN_PATH=$project/style/build/plugins QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME= \
    QT_SCALE_FACTOR=1 "$dev/build/tabcheck" || status=1

# Qt Quick (Kwi): a footer TabBar through KDE's bridge is the header upside
# down. Sandboxed like dev/check-quick.sh.
"$project/style/quick/build.sh" > /dev/null
[[ -x $dev/build/quickshot && $dev/build/quickshot -nt $dev/quickshot.cpp ]] || "$dev/build.sh" > /dev/null
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
M9_QUICK=1 QSTYLE=Platinum "$dev/run.sh" platinum breeze env QT_QUICK_BACKEND=software \
    "$dev/build/quickshot" "$dev/tabs-quick.qml" "$work/tabs.png" > "$work/tabs.log" 2>&1 || true
python3 -I - "$work" << 'PYEND' || status=1
import re, sys
from PIL import Image, ImageChops, ImageOps
work = sys.argv[1]
bars = None
for line in open(f"{work}/tabs.log"):
    m = re.search(r"BARS (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)", line)
    if m:
        bars = [int(v) for v in m.groups()]
ok = False
if bars:
    x, ty, w, th, by, bh = bars
    img = Image.open(f"{work}/tabs.png").convert("RGB")
    top = img.crop((x, ty, x + w, ty + th))
    bottom = img.crop((x, by, x + w, by + bh))
    ok = th == bh and ImageChops.difference(ImageOps.flip(top), bottom).getbbox() is None \
        and ImageChops.difference(top, bottom).getbbox() is not None
print(("ok      " if ok else "FAIL    ") + "Qt Quick footer TabBar is the header upside down")
# Kwi's taller tabs (#266): the measured rows, the last tab row repeated,
# then the 3 pane rows at the bar's edge; the footer is the header flipped.
tall = None
for line in open(f"{work}/tabs.log"):
    m = re.search(r"TALL (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)", line)
    if m:
        tall = [int(v) for v in m.groups()]
tall_ok = False
detail = "no TALL line"
if tall:
    x, ty, w, th, by, bh = tall
    img = Image.open(f"{work}/tabs.png").convert("RGB")
    top = img.crop((x, ty, x + w, ty + th))
    bottom = img.crop((x, by, x + w, by + bh))
    normal = [0x00, 0xCC, 0xDD] + [0xCC] * 18 + [0x00, 0xCC, 0xFF]
    current = [0x00, 0xCC, 0xFF] + [0xEE] * 21
    def expected(fill):
        extra = th - len(fill)
        return fill[:21] + [fill[20]] * extra + fill[21:]
    cols = {name: [top.getpixel((cx, y))[0] for y in range(th)]
            for name, cx in (("normal", 50), ("current", 150))}  # 100 px tabs
    tall_ok = (th == bh and th > 24
               and cols["normal"] == expected(normal) and cols["current"] == expected(current)
               and ImageChops.difference(ImageOps.flip(top), bottom).getbbox() is None)
    detail = f"height {th}, normal {cols['normal'][-5:]}, current {cols['current'][-5:]}"
print(("ok      " if tall_ok else "FAIL    ") + f"Qt Quick taller tabs reach the pane edge ({detail})")
sys.exit(0 if ok and tall_ok else 1)
PYEND
exit "$status"
