#!/usr/bin/env python3
"""Cut a widget capture into a 9-slice and print it as C++ tables.

The style draws bevelled widgets (push buttons, default rings, ...) from
measured slices: four KxK corners, four edge profiles K deep, and a center
fill. This tool measures them from a reference capture and checks that the
edges really are uniform (so stretching them is exact), ignoring a label
area in the middle if given.

usage: nineslice.py IMAGE X Y W H K NAME [--bg RRGGBB] [--skip X0,Y0,X1,Y1]
  X Y W H   the widget's bounding box in IMAGE
  K         corner size (also edge depth)
  NAME      C++ identifier prefix for the tables
  --bg      background color: pixels of this color in the corners are
            written as -1 (not drawn), so the window shows through
  --skip    a rectangle (widget coordinates) to ignore when checking edge
            and fill uniformity, e.g. the label

Output: a C++ snippet with `const NineSlice NAME = {...};` (values are
0xRRGGBB, or -1 for "don't draw") and a report on stderr.
"""

import argparse
import sys
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    for k in ("x", "y", "w", "h", "k"):
        ap.add_argument(k, type=int)
    ap.add_argument("name")
    ap.add_argument("--bg")
    ap.add_argument("--skip")
    a = ap.parse_args()

    im = Image.open(a.image).convert("RGB")
    x0, y0, W, H, K = a.x, a.y, a.w, a.h, a.k
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4)) if a.bg else None
    skip = tuple(int(v) for v in a.skip.split(",")) if a.skip else None

    def px(x, y):
        return im.getpixel((x0 + x, y0 + y))

    def skipped(x, y):
        return skip and skip[0] <= x <= skip[2] and skip[1] <= y <= skip[3]

    def val(p, allow_bg):
        if allow_bg and bg is not None and p == bg:
            return -1
        return (p[0] << 16) | (p[1] << 8) | p[2]

    problems = []
    # Edge profiles: rows 0..K-1 (top), H-K..H-1 (bottom) across the middle;
    # cols 0..K-1 (left), W-K..W-1 (right) down the middle.
    top = [px(W // 2, r) for r in range(K)]
    bottom = [px(W // 2, H - K + r) for r in range(K)]
    left = [px(c, H // 2) for c in range(K)]
    right = [px(W - K + c, H // 2) for c in range(K)]
    for r in range(K):
        for x in range(K, W - K):
            if not skipped(x, r) and px(x, r) != top[r]:
                problems.append(f"top row {r} not uniform at x={x}")
                break
            if not skipped(x, H - K + r) and px(x, H - K + r) != bottom[r]:
                problems.append(f"bottom row {r} not uniform at x={x}")
                break
    for c in range(K):
        for y in range(K, H - K):
            if not skipped(c, y) and px(c, y) != left[c]:
                problems.append(f"left col {c} not uniform at y={y}")
                break
            if not skipped(W - K + c, y) and px(W - K + c, y) != right[c]:
                problems.append(f"right col {c} not uniform at y={y}")
                break
    fill = px(W // 2, H // 2) if not skipped(W // 2, H // 2) else px(K, K)
    for y in range(K, H - K):
        for x in range(K, W - K):
            if not skipped(x, y) and px(x, y) != fill:
                problems.append(f"fill not uniform at {x},{y}: {px(x, y)}")
                break
        else:
            continue
        break

    def corner(cx, cy, ox, oy):
        """KxK block at (cx, cy); background pixels connected (4-way) to its
        outer corner (ox, oy in block coordinates) become -1."""
        rows = [[val(px(cx + c, cy + r), False) for c in range(K)] for r in range(K)]
        if bg is not None:
            bgv = (bg[0] << 16) | (bg[1] << 8) | bg[2]
            todo, seen = [(ox, oy)], set()
            while todo:
                c, r = todo.pop()
                if (c, r) in seen or not (0 <= c < K and 0 <= r < K) or rows[r][c] != bgv:
                    continue
                seen.add((c, r))
                todo += [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
            for c, r in seen:
                rows[r][c] = -1
        return rows

    tl, tr = corner(0, 0, 0, 0), corner(W - K, 0, K - 1, 0)
    bl, br = corner(0, H - K, 0, K - 1), corner(W - K, H - K, K - 1, K - 1)

    def fmt(v):
        return "-1" if v < 0 else f"0x{v:06X}"

    def table(rows):
        return "{" + ", ".join("{" + ", ".join(fmt(v) for v in row) + "}" for row in rows) + "}"

    def prof(ps):
        return "{" + ", ".join(fmt(val(p, False)) for p in ps) + "}"

    print(f"// {a.name}: measured from {a.image.split('/')[-1]} at {x0},{y0} ({W}x{H}), K={K}")
    print(f"const NineSlice<{K}> {a.name} = {{")
    print(f"    {table(tl)},\n    {table(tr)},\n    {table(bl)},\n    {table(br)},")
    print(f"    {prof(top)}, {prof(bottom)}, {prof(left)}, {prof(right)},")
    print(f"    {fmt(val(fill, False))},")
    print("};")
    for p in problems:
        print("warning:", p, file=sys.stderr)
    print(f"{a.name}: {len(problems)} uniformity warnings", file=sys.stderr)


if __name__ == "__main__":
    main()
