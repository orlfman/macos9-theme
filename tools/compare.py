#!/usr/bin/env python3
"""Measure reference captures and compare our renders with them, pixel exact.

Every IMAGE argument may carry a crop: file.png@X,Y,W,H. Coordinates are
image pixels (captures and sandbox renders are both 1x).

Subcommands:
  diff REF OURS [--zoom N] [--out FILE] [--tolerance T]
      Compare two same-size regions. Prints differing pixel count, percent,
      max channel difference, and the bounding box of the differences.
      Writes a side-by-side PNG (reference | ours | differences in magenta),
      enlarged N times without smoothing (default 4), to --out
      (default dev/shots/compare-<ours>.png). Exit 1 if anything differs
      by more than T (default 0) in any channel.
  row IMAGE Y X0 X1        runs of colors along a row:    x-range  #RRGGBB
  col IMAGE X Y0 Y1        runs of colors down a column:  y-range  #RRGGBB
  colors IMAGE [--top N]   most common colors in the image or crop
  bbox IMAGE [--bg RRGGBB] bounding box of everything that isn't the
                           background color (default: the top-left pixel)
  zoom IMAGE [--zoom N] [--out FILE]   enlarged copy without smoothing

Examples:
  tools/compare.py col reference/controls-general-controls.png 805 313 358
  tools/compare.py diff reference/controls-general-controls.png@546,276,20,20 \\
      dev/shots/platinum-platinum-widgets.png@20,40,20,20
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
CROP = re.compile(r"^(?P<path>.+?)@(?P<x>\d+),(?P<y>\d+),(?P<w>\d+),(?P<h>\d+)$")


def load(spec):
    """Open 'file.png' or 'file.png@X,Y,W,H' as an RGB image."""
    m = CROP.match(spec)
    path = m["path"] if m else spec
    try:
        im = Image.open(path).convert("RGB")
    except FileNotFoundError:
        sys.exit(f"no such image: {path}")
    if m:
        x, y, w, h = (int(m[k]) for k in "xywh")
        if x + w > im.width or y + h > im.height:
            sys.exit(f"crop {x},{y},{w},{h} is outside {path} ({im.width}x{im.height})")
        im = im.crop((x, y, x + w, y + h))
    return im, Path(path)


def pixels(im):
    """All pixels as a flat sequence (Pillow 12+ renamed getdata)."""
    get = getattr(im, "get_flattened_data", None)
    return get() if get else im.getdata()


def hexc(p):
    return "#%02X%02X%02X" % p


def runs(pixels, start):
    out = []
    prev, first = None, start
    for i, p in enumerate(pixels):
        if p != prev:
            if prev is not None:
                out.append((first, start + i - 1, prev))
            prev, first = p, start + i
    if prev is not None:
        out.append((first, start + len(pixels) - 1, prev))
    return out


def print_runs(rs):
    for a, b, p in rs:
        span = f"{a}" if a == b else f"{a}-{b}"
        print(f"{span:>11}  {hexc(p)}  ({b - a + 1} px)")


def cmd_row(a):
    im, _ = load(a.image)
    if not (0 <= a.y < im.height and 0 <= a.x0 <= a.x1 < im.width):
        sys.exit("row out of range")
    print_runs(runs([im.getpixel((x, a.y)) for x in range(a.x0, a.x1 + 1)], a.x0))


def cmd_col(a):
    im, _ = load(a.image)
    if not (0 <= a.x < im.width and 0 <= a.y0 <= a.y1 < im.height):
        sys.exit("column out of range")
    print_runs(runs([im.getpixel((a.x, y)) for y in range(a.y0, a.y1 + 1)], a.y0))


def cmd_colors(a):
    im, _ = load(a.image)
    total = im.width * im.height
    for p, n in Counter(pixels(im)).most_common(a.top):
        print(f"{hexc(p)}  {n:>8}  {100 * n / total:6.2f} %")


def cmd_bbox(a):
    im, _ = load(a.image)
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4)) if a.bg else im.getpixel((0, 0))
    box = ImageChops.difference(im, Image.new("RGB", im.size, bg)).getbbox()
    if not box:
        print(f"nothing but {hexc(bg)}")
    else:
        x0, y0, x1, y1 = box
        print(f"x {x0}-{x1 - 1}  y {y0}-{y1 - 1}  size {x1 - x0}x{y1 - y0}  (background {hexc(bg)})")


def enlarge(im, n):
    return im.resize((im.width * n, im.height * n), Image.NEAREST)


def cmd_zoom(a):
    im, path = load(a.image)
    out = Path(a.out) if a.out else ROOT / "dev" / "shots" / f"zoom-{path.stem}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    enlarge(im, a.zoom).save(out)
    print(out)


def cmd_diff(a):
    ref, _ = load(a.ref)
    ours, ours_path = load(a.ours)
    if ref.size != ours.size:
        sys.exit(f"sizes differ: reference {ref.width}x{ref.height}, ours {ours.width}x{ours.height}")
    diff = ImageChops.difference(ref, ours)
    worst = max(max(px) for px in pixels(diff))
    # a pixel differs if any channel is over the tolerance
    over = Image.new("L", ref.size, 0)
    for band in diff.split():
        over = ImageChops.lighter(over, band.point(lambda v: 255 if v > a.tolerance else 0))
    count = sum(1 for v in pixels(over) if v)
    total = ref.width * ref.height
    box = over.getbbox()

    vis = ours.copy()
    vis.paste((255, 0, 255), mask=over)
    gap = 4
    sheet = Image.new("RGB", (ref.width * 3 + gap * 2, ref.height), (128, 128, 128))
    for i, part in enumerate((ref, ours, vis)):
        sheet.paste(part, (i * (ref.width + gap), 0))
    out = Path(a.out) if a.out else ROOT / "dev" / "shots" / f"compare-{ours_path.stem}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    enlarge(sheet, a.zoom).save(out)

    print(f"size        {ref.width}x{ref.height}")
    print(f"differing   {count} of {total} px ({100 * count / total:.2f} %), tolerance {a.tolerance}")
    print(f"max diff    {worst} (per channel, 0-255)")
    if box:
        print(f"diff bbox   x {box[0]}-{box[2] - 1}  y {box[1]}-{box[3] - 1} (in the compared region)")
    print(f"picture     {out}  (reference | ours | differences in magenta)")
    sys.exit(1 if count else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("diff")
    p.add_argument("ref")
    p.add_argument("ours")
    p.add_argument("--zoom", type=int, default=4)
    p.add_argument("--out")
    p.add_argument("--tolerance", type=int, default=0)
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("row")
    p.add_argument("image")
    p.add_argument("y", type=int)
    p.add_argument("x0", type=int)
    p.add_argument("x1", type=int)
    p.set_defaults(func=cmd_row)

    p = sub.add_parser("col")
    p.add_argument("image")
    p.add_argument("x", type=int)
    p.add_argument("y0", type=int)
    p.add_argument("y1", type=int)
    p.set_defaults(func=cmd_col)

    p = sub.add_parser("colors")
    p.add_argument("image")
    p.add_argument("--top", type=int, default=12)
    p.set_defaults(func=cmd_colors)

    p = sub.add_parser("bbox")
    p.add_argument("image")
    p.add_argument("--bg")
    p.set_defaults(func=cmd_bbox)

    p = sub.add_parser("zoom")
    p.add_argument("image")
    p.add_argument("--zoom", type=int, default=8)
    p.add_argument("--out")
    p.set_defaults(func=cmd_zoom)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
