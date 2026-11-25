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
sys.exit(0 if ok else 1)
PYEND
exit "$status"
