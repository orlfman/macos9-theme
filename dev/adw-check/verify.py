#!/usr/bin/env python3
# Summarise a dev/check-adw.sh run: AdwStyleManager state per run and the
# rendered accent on the suggested button.
# SPDX-License-Identifier: BSD-2-Clause
import pathlib
import re
import sys

from PIL import Image

PROJECT = pathlib.Path(__file__).resolve().parents[2]

root, mode = pathlib.Path(sys.argv[1]), sys.argv[2]
fails = 0


def check(ok, what):
    global fails
    print(("PASS " if ok else "FAIL ") + what)
    fails += not ok


def finish():
    print("VERDICT=%s fails=%d" % ("PASS" if not fails else "FAIL", fails))
    sys.exit(1 if fails else 0)


states = {}
modes = ("gallery", "narrow", "dialog", "focus", "disabled", "alertwin",
         "msgdialog", "prefs", "segments", "segments-hc", "selections", "selections-border",
         "bars-wrapped", "bars-closed", "bars-open", "bars-custom",
         "bars-wrapped-search", "bars-opaque", "bars-margin", "hc")
for prefix in ("stock", "layer"):
    for run in modes:
        name = f"{prefix}-{run}"
        log = root / f"{name}.log"
        png = root / f"{name}.png"
        state = re.search(r"^STATE (.+)$", log.read_text(), re.M) if log.is_file() else None
        check(state is not None and png.is_file() and png.stat().st_size > 0,
              f"{name} has a state log and render")
        if state:
            states[name] = dict(kv.split("=", 1) for kv in state.group(1).split())
if fails:
    finish()

for name, st in states.items():
    print("STATE %s accent=%s rgba=%s dark=%s hc=%s theme=%s" % (
        name, st["accent"], st["accent_rgba"], st["adw_dark"], st["adw_hc"],
        st["theme"]))
    check(st["adw_dark"] == "0", f"{name} light")
    check(st["theme"] != "Platinum",
          f"{name} libadwaita keeps its own stylesheet ({st['theme']})")
    if mode == "plasma":
        check(st["adw_sys_acc"] == "1", f"{name} portal advertises accent")
        check(st["accent"] == "purple", f"{name} accent purple from #CCCCFF")
check(states["stock-hc"]["adw_hc"] == "1",
      "high contrast reaches AdwStyleManager")
for log in root.glob("layer-*.log"):
    stock = root / log.name.replace("layer-", "stock-", 1)
    extra = (log.read_text().count("CRITICAL") -
             (stock.read_text().count("CRITICAL") if stock.is_file() else 0))
    check(extra <= 0, f"{log.stem} adds no GTK criticals ({extra})")


def count(name, rgb):
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

# Equal insets (user decision #268): as many columns between the outer black
# edge and the close box on the left as between the last box and the edge
# on the right, measured on the boxes' top row.
def box_insets(png):
    img = Image.open(root / f"{png}.png").convert("RGB")
    for y in range(4, 40):
        row = [img.getpixel((x, y))[0] for x in range(img.width)]
        if row.count(0x22) > 12:
            break
    edge_l = next(i for i, v in enumerate(row) if v < 0x20)
    edge_r = len(row) - 1 - next(i for i, v in enumerate(reversed(row)) if v < 0x20)
    while row[edge_r - 1] < 0x20:  # black edge plus shadow column
        edge_r -= 1
    first = next(i for i in range(edge_l + 1, len(row)) if row[i] == 0x88)
    last = max(i for i in range(len(row)) if row[i] == 0xFF and row[i - 1] == 0x22 and i < edge_r)
    return first - edge_l - 1, edge_r - last - 1


left, right = box_insets("layer-gallery")
check(left == right, f"window boxes equally far from both edges (left {left}, right {right})")
prefs = nodes("layer-prefs")
sheet = next((int(x) for _, n, *_, x in prefs if n.startswith("sheet")), None)
dclose = [int(x) for _, n, *_, x in prefs if n.startswith("button.image-button.close")]
# The frame's 4 px border plus the same 8 px as in windows (#268).
check(sheet is not None and len(dclose) >= 2 and dclose[-1] - sheet == 12,
      f"dialog close box as far in as in windows (sheet {sheet}, box {dclose[-1:]})")

# Spin buttons (#267): the field, then the Platinum scroll arrow buttons
# (down for -, up for +), drawn pixel for pixel; libadwaita's stock look
# has none of them.
def find_art(name, png):
    hay = Image.open(root / png).convert("RGB")
    art = Image.open(PROJECT / f"gtk/Platinum/gtk-3.0/assets/{name}.png").convert("RGBA")
    hw, hh = hay.size
    aw, ah = art.size
    hp, ap = hay.load(), art.load()
    solid = [(i, j, ap[i, j][:3]) for j in range(ah) for i in range(aw) if ap[i, j][3] == 255]
    for y in range(hh - ah + 1):
        for x in range(hw - aw + 1):
            if all(hp[x + i, y + j] == rgb for i, j, rgb in solid):
                return x, y
    return None


if (root / "layer-gallery.png").is_file():
    for name in ("vscroll-down", "arrow-box-up", "arrow-box-down-disabled", "arrow-box-up-disabled"):
        at = find_art(name, "layer-gallery.png")
        stock = find_art(name, "stock-gallery.png")
        check(at is not None and stock is None, f"spin button {name} arrow drawn in Platinum (at {at})")
    # Face columns between the field's outer edge and the down arrow, measured
    # in pixels across the arrow's middle row.
    at = find_art("vscroll-down", "layer-gallery.png")
    gap = None
    if at:
        img = Image.open(root / "layer-gallery.png").convert("RGB")
        gap = 0
        while img.getpixel((at[0] - 1 - gap, at[1] + 8)) == (0xDD, 0xDD, 0xDD):
            gap += 1
    check(gap == 2, f"spin button arrows start 2 px right of the field (gap {gap})")

# Both parentless alert kinds are the movable alert (#257): a white body
# and, in the 22-row strip, alternating light and dark pinstripe rows.
for name in ("layer-alertwin", "layer-msgdialog"):
    if not (root / f"{name}.png").is_file():
        continue
    im = Image.open(root / f"{name}.png").convert("RGB")
    w, h = im.size
    body = im.crop((10, 30, w - 10, h - 10)).tobytes()
    white = sum(body[k:k + 3] == b"\xff\xff\xff" for k in range(0, len(body), 3))
    column = [im.getpixel((w // 2, y)) for y in range(2, 22)]
    shades = {px for px in column}
    check(white > 0.5 * len(body) / 3 and len(shades) >= 2,
          f"{name} is the movable alert ({white * 3 * 100 // len(body)}% white body, "
          f"{len(shades)} strip shades)")
# The fixture reports bounds per render so pixel checks follow the layout.
def widget_boxes(name):
    return {
        m.group(1): tuple(int(m.group(i)) for i in range(2, 6))
        for m in re.finditer(
            r"^BOX (\S+) (-?\d+) (-?\d+) (\d+) (\d+)$",
            (root / f"{name}.log").read_text(), re.M)
    }


def verify_segments():
    stock = widget_boxes("stock-segments")
    layer = widget_boxes("layer-segments")
    expected = {"browse", "installed", "bytes", "bits", "unavailable", "general", "units"}
    check(stock.keys() == layer.keys() == expected, "all segmented button allocations recorded")
    image = Image.open(root / "layer-segments.png").convert("RGB")
    for name in sorted(expected):
        if name not in stock or name not in layer:
            continue
        x, y, w, h = layer[name]
        check((w, h) == stock[name][2:], f"{name} retains stock button size")
        background = ((102, 102, 102) if name in ("installed", "bits", "units")
                      else (238, 238, 238) if name == "unavailable" else (221, 221, 221))
        pixels = image.crop((x + 3, y + 3, x + w - 3, y + h - 3))
        colors = pixels.getcolors(w * h) or []
        check(any(color == background and n > pixels.width * pixels.height / 2
                  for n, color in colors), f"{name} draws its Platinum face")

    # The three straight edge rows of BevelNormal and BevelPressed (slices.h).
    # Sample across the middle third so rounded reference corners and button
    # labels do not enter the comparison. The edge rows run from outside in.
    bevels = {
        "browse": ((0x00, 0xDD, 0xFF), (0x00, 0x77, 0xAA)),
        "installed": ((0x00, 0x44, 0x55), (0x00, 0x88, 0x77)),
    }
    for name, (top, bottom) in bevels.items():
        if name not in layer:
            continue
        x, y, w, h = layer[name]
        # The PNG includes the window's 1 px top frame. Widget bounds are
        # relative to the window contents, so account for it in the row probes.
        y += 1
        left, right = x + w // 3, x + 2 * w // 3
        for side, rows, shades in (
            ("top", range(y, y + 3), top),
            ("bottom", range(y + h - 1, y + h - 4, -1), bottom),
        ):
            observed = [image.crop((left, row, right, row + 1)).tobytes() for row in rows]
            want = [bytes([shade]) * (3 * (right - left)) for shade in shades]
            sample = " ".join(row[:3].hex() for row in observed)
            check(observed == want, f"{name} {side} bevel rows (observed {sample})")

    for prefix in ("stock", "layer"):
        log = (root / f"{prefix}-segments.log").read_text()
        check("SEGMENTS linked=1 toggle=1 page=units" in log,
              f"{prefix} grouped buttons activate their choice or page")
    hc_images = [Image.open(root / f"{prefix}-segments-hc.png").convert("RGBA")
                 for prefix in ("stock", "layer")]
    check(all(states[f"{prefix}-segments-hc"]["adw_hc"] == "1" for prefix in ("stock", "layer"))
          and hc_images[0].size == hc_images[1].size
          and hc_images[0].tobytes() == hc_images[1].tobytes(),
          "segmented controls keep stock high contrast")


verify_segments()

lim = Image.open(root / "layer-selections.png").convert("RGB")
boxes = widget_boxes("layer-selections")
for wname, want, min_px in (
    ("lb", (0xCC, 0xCC, 0xFF), 5000),
    ("sb", (0xCC, 0xCC, 0xFF), 5000),
    ("gv", (0xCC, 0xCC, 0xFF), 1000),
    ("fb", (0xCC, 0xCC, 0xFF), 1000),
    ("tv", (0xCC, 0xCC, 0xFF), 500),
    ("link", (0x00, 0x00, 0xFF), 10),
):
    b = boxes.get(wname)
    n = 0
    if b:
        x, y, w, h = b
        data = lim.crop((max(0, x), max(0, y),
                         min(lim.width, x + w),
                         min(lim.height, y + h))).tobytes()
        wb = bytes(want)
        n = sum(data[k:k + 3] == wb for k in range(0, len(data), 3))
    check(n >= min_px,
          f"selections {wname} paints #{want[0]:02X}{want[1]:02X}{want[2]:02X} ({n} px)")


def bar_pixels(image, bounds, top):
    if bounds is None:
        return []
    x, y, w, h = bounds
    cx = x + w // 2
    # The header's own black edge occupies y + h; it is sampled too, so a
    # separator stacked under it shows as a second black row (#301). The
    # bottom bar starts at y + 1.
    rows = range(y + h, y + h + 5) if top else range(y, y - 4, -1)
    if not (0 <= cx < image.width and all(0 <= row < image.height for row in rows)):
        return []
    return [image.getpixel((cx, row)) for row in rows]


# Ordinary raised bars leave the content clear. Raised-border bars add one line.
border = Image.open(root / "layer-selections-border.png").convert("RGB")
border_boxes = widget_boxes("layer-selections-border")
gray = (221, 221, 221)
for bar in ("header", "bottom"):
    plain = bar_pixels(lim, boxes.get(bar), top=bar == "header")
    edged = bar_pixels(border, border_boxes.get(bar), top=bar == "header")
    # The header keeps its one black edge row in both styles; the bottom bar
    # has none of its own.
    edge = [(0, 0, 0)] if bar == "header" else []
    check(plain == edge + [gray] * 4, f"raised {bar} has no drop shadow ({plain})")
    check(edged == [(0, 0, 0)] + [gray] * (4 if bar == "header" else 3),
          f"raised-border {bar} has a single one-pixel black line ({edged})")

# A wrapped header and a header over a closed search bar keep one black
# edge (#303); an open search bar draws the one line under itself. libadwaita's
# collapse padding no longer moves the header down (#304).
direct_y = border_boxes.get("header", (0, -1))[1]
# The fixture reports the top bar's real children; each mode must render the
# layout it is named for, or its pixel checks cover nothing (#308).
LAYOUTS = {
    "bars-wrapped": r"box\[headerbar:[1-9]\d*\]:\d+",
    "bars-closed": r"headerbar:[1-9]\d* searchbar:0",
    "bars-open": r"headerbar:[1-9]\d* searchbar:[1-9]\d*",
    "bars-custom": r"headerbar:[1-9]\d* box\[button:[1-9]\d*\]:[1-9]\d* searchbar:0",
    "bars-wrapped-search": r"headerbar:[1-9]\d* box\[searchbar:[1-9]\d*\]:[1-9]\d*",
    "bars-opaque": r"headerbar:[1-9]\d* box\[button:[1-9]\d*\]:[1-9]\d*",
    "bars-margin": r"headerbar:[1-9]\d* box\[button:[1-9]\d*\]:[1-9]\d*",
}
for run in ("bars-wrapped", "bars-closed", "bars-open", "bars-custom",
            "bars-wrapped-search", "bars-opaque", "bars-margin"):
    img = Image.open(root / f"layer-{run}.png").convert("RGB")
    bxs = widget_boxes(f"layer-{run}")
    m = re.search(r"^TOPBAR (.*)$", (root / f"layer-{run}.log").read_text(), re.M)
    layout = m.group(1) if m else "missing"
    check(re.fullmatch(LAYOUTS[run], layout) is not None, f"{run} renders its layout ({layout})")
    hdr = bar_pixels(img, bxs.get("header"), top=True)
    below = run in ("bars-open", "bars-custom", "bars-wrapped-search", "bars-opaque",
                    "bars-margin")
    # Below the header comes window gray, or the opaque bar's own #EEEEEE.
    after = (0xEE, 0xEE, 0xEE) if run == "bars-opaque" else gray
    want = [(0, 0, 0)] + [after] * (1 if below else 4)
    check(hdr[:len(want)] == want, f"{run} header ends in one black row ({hdr})")
    check(bxs.get("header", (0, -2))[1] == direct_y,
          f"{run} header starts where a lone header does (y {bxs.get('header', (0, None))[1]} vs {direct_y})")
    # The search bar must really be open or closed, or its bottom is the
    # header's edge and the line check samples that instead (#306).
    if run in ("bars-open", "bars-closed"):
        sh = bxs.get("search", (0, 0, 0, -1))[3]
        check(sh > 0 if run == "bars-open" else sh == 0,
              f"{run} search bar is {'open' if run == 'bars-open' else 'closed'} (height {sh})")
    if run == "bars-open":
        sx, sy, sw, sh = bxs.get("search", (0, 0, 0, 0))
        under = bar_pixels(img, (sx, sy, sw, sh), top=True)[:4] if sh > 0 else []
        check(under == [(0, 0, 0)] + [gray] * 3, f"{run} search bar ends in one black row ({under})")
    # A plain custom bar (closed search bar under it) and a wrapped open search
    # bar keep the line at the bottom of the bar stack (#305).
    if run in ("bars-custom", "bars-wrapped-search"):
        ex = bxs.get("extra", (0, 0, 0, 0))
        under = bar_pixels(img, ex, top=True)[:4] if ex[3] > 0 else []
        check(under == [(0, 0, 0)] + [gray] * 3, f"{run} bar stack ends in one black row ({under})")
    if run in ("bars-opaque", "bars-margin"):
        # The fixture must really carry its 4 px GtkWidget margin (#312): the
        # widget reports it, and the top bar ends that far (plus the opaque
        # bar's 4 px CSS margin) below the bar.
        mm = re.search(r"^MARGIN extra (-?\d+)$", (root / f"layer-{run}.log").read_text(), re.M)
        widget_margin = int(mm.group(1)) if mm else None
        check(widget_margin == 4, f"{run} bar has a 4 px widget margin ({widget_margin})")
        ex, tb = bxs.get("extra"), bxs.get("topbar")
        gap = (tb[1] + tb[3]) - (ex[1] + ex[3]) if ex and tb else None
        want_gap = 8 if run == "bars-opaque" else 4
        check(gap == want_gap, f"{run} top bar ends {want_gap} px below the bar ({gap})")

        x, y, w, h = ex or (0, 0, 0, 0)
        cx, last = x + w // 2, y + h
        if run == "bars-opaque":
            # Confirm the application background in the row above the line (#310).
            inside = None
            if h > 1 and 0 <= cx < img.width and 0 < last <= img.height:
                inside = img.getpixel((cx, last - 1))
            check(inside == (0xEE, 0xEE, 0xEE), f"{run} bar is opaque #EEEEEE ({inside})")

        # Sample the parent edge as well, where a duplicate line can land (#313).
        rows = max(7, want_gap + 1)
        under = []
        if w > 0 and h > 0 and 0 <= cx < img.width and 0 <= last <= img.height - rows:
            under = [img.getpixel((cx, r)) for r in range(last, last + rows)]
        check(under == [(0, 0, 0)] + [gray] * (rows - 1),
              f"{run} bar stack ends in one black row ({under})")

for png in sorted(root.glob("*-app-*.png")):
    print("APP %s" % png.name)
finish()
