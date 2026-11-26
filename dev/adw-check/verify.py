#!/usr/bin/env python3
# Summarise a dev/check-adw.sh run: AdwStyleManager state per run and the
# rendered accent on the suggested button.
# SPDX-License-Identifier: BSD-2-Clause
import pathlib
import re
import sys

root, mode = pathlib.Path(sys.argv[1]), sys.argv[2]
fails = 0


def check(ok, what):
    global fails
    print(("PASS " if ok else "FAIL ") + what)
    fails += not ok


states = {}
for log in sorted([*root.glob("stock-*.log"), *root.glob("layer-*.log")]):
    m = re.search(r"^STATE (.*)$", log.read_text(), re.M)
    if m:
        states[log.stem] = dict(kv.split("=", 1) for kv in m.group(1).split())
for name, st in states.items():
    print("STATE %s accent=%s rgba=%s dark=%s hc=%s theme=%s" % (
        name, st["accent"], st["accent_rgba"], st["adw_dark"], st["adw_hc"],
        st["theme"]))
    check((root / f"{name}.png").is_file(), f"{name} rendered")
    check(st["adw_dark"] == "0", f"{name} light")
    check(st["theme"] != "Platinum",
          f"{name} libadwaita keeps its own stylesheet ({st['theme']})")
    if mode == "plasma":
        check(st["adw_sys_acc"] == "1", f"{name} portal advertises accent")
        check(st["accent"] == "purple", f"{name} accent purple from #CCCCFF")
check("stock-hc" in states and states["stock-hc"]["adw_hc"] == "1",
      "high contrast reaches AdwStyleManager")
check(all(k in states for k in ("stock-gallery", "stock-narrow",
                                "stock-dialog", "stock-focus",
                                "stock-disabled", "stock-alertwin",
                                "stock-msgdialog", "stock-prefs")),
      "all stock runs present")
for log in root.glob("layer-*.log"):
    stock = root / log.name.replace("layer-", "stock-", 1)
    extra = (log.read_text().count("CRITICAL") -
             (stock.read_text().count("CRITICAL") if stock.is_file() else 0))
    check(extra <= 0, f"{log.stem} adds no GTK criticals ({extra})")


def count(name, rgb):
    from PIL import Image
    data = Image.open(root / f"{name}.png").convert("RGB").tobytes()
    want = bytes(rgb)
    return sum(data[k:k + 3] == want for k in range(0, len(data), 3))


if (root / "layer-gallery.png").is_file():
    lav, gray = (204, 204, 255), (221, 221, 221)
    for name in ("stock-gallery", "layer-gallery"):
        print("PIXELS %s lavender=%d gray=%d" % (name, count(name, lav),
                                                 count(name, gray)))
    check(count("layer-gallery", lav) > 300 and
          count("stock-gallery", lav) < 100,
          "layer paints #CCCCFF selection")
    check(count("layer-gallery", gray) > 50000, "layer paints #DDDDDD window")
    from PIL import Image
    same = (Image.open(root / "layer-hc.png").convert("RGBA").tobytes() ==
            Image.open(root / "stock-hc.png").convert("RGBA").tobytes())
    check(states["layer-hc"]["adw_hc"] == "1" and same,
          "high contrast keeps libadwaita's own look under the layer")
# AdwHeaderBar under the layer: box.start at the row's left edge and box.end
# at its right edge, as in the plain GTK 4 bar, so no pinstripes show
# outside them (#256).
log = root / "layer-gallery.log"
if log.is_file():
    tree = re.findall(r"^TREE( *)(\S+) (\d+)x(\d+) @(-?\d+)$", log.read_text(), re.M)
    row = start = end = None
    for indent, name, w, h, x in tree:
        if name == "box" and h == "34" and row is None:
            row = (int(x), int(w))
        elif name.startswith("box.horizontal.start") and start is None:
            start = int(x)
        elif name.startswith("windowcontrols.end") or (
                name.startswith("box.horizontal.end") and end is None):
            # the right edge of whatever the end box shows last
            end = max(end or 0, int(x) + int(w))
    ok = row is not None and start == row[0] and end == row[0] + row[1]
    check(ok, f"header bar boxes reach the bar's edges (row {row}, start {start}, end {end})")

# Close boxes 4 px from the frame's outer edge (docs/REFERENCE.md "Boxes",
# the decoration): in the main window the content origin is that column
# (the frame's left border is 4 px), and in a floating dialog the box sits
# one 4 px border in from the sheet.
def nodes(name):
    path = root / f"{name}.log"
    if not path.is_file():
        return []
    return re.findall(r"^TREE( *)(\S+) (\d+)x(\d+) @(-?\d+)$", path.read_text(), re.M)

closes = [int(x) for _, n, w, h, x in nodes("layer-gallery") if n.startswith("button.image-button.close")]
check(bool(closes) and closes[0] == 0,
      f"main window close box at the frame's column 4 (x={closes[:1]})")
prefs = nodes("layer-prefs")
sheet = next((int(x) for _, n, *_, x in prefs if n.startswith("sheet")), None)
dclose = [int(x) for _, n, *_, x in prefs if n.startswith("button.image-button.close")]
check(sheet is not None and len(dclose) >= 2 and dclose[-1] - sheet == 4,
      f"dialog close box 4 px inside its frame (sheet {sheet}, box {dclose[-1:]})")

# Both parentless alert kinds are the movable alert (#257): a white body
# and, in the 22-row strip, alternating light and dark pinstripe rows.
for name in ("layer-alertwin", "layer-msgdialog"):
    if not (root / f"{name}.png").is_file():
        continue
    from PIL import Image
    im = Image.open(root / f"{name}.png").convert("RGB")
    w, h = im.size
    body = im.crop((10, 30, w - 10, h - 10)).tobytes()
    white = sum(body[k:k + 3] == b"\xff\xff\xff" for k in range(0, len(body), 3))
    column = [im.getpixel((w // 2, y)) for y in range(2, 22)]
    shades = {px for px in column}
    check(white > 0.5 * len(body) / 3 and len(shades) >= 2,
          f"{name} is the movable alert ({white * 3 * 100 // len(body)}% white body, "
          f"{len(shades)} strip shades)")
for png in sorted(root.glob("*-app-*.png")):
    print("APP %s" % png.name)
print("VERDICT=%s fails=%d" % ("PASS" if not fails else "FAIL", fails))
sys.exit(1 if fails else 0)
