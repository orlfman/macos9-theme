#!/usr/bin/env python3
"""Cut a small fixed-size widget part (check box, radio button) out of a
capture and print it as a C++ table.

Background-colored pixels connected to the block's border become -1 (not
drawn); background-colored pixels enclosed by the shape (a box's inside)
are kept. Prints `const Sprite NAME = {W, H, {...}};`.

usage: sprite.py IMAGE X Y W H NAME --bg RRGGBB
"""

import argparse
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    for k in ("x", "y", "w", "h"):
        ap.add_argument(k, type=int)
    ap.add_argument("name")
    ap.add_argument("--bg", required=True)
    a = ap.parse_args()
    im = Image.open(a.image).convert("RGB")
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4))
    W, H = a.w, a.h
    px = [[im.getpixel((a.x + c, a.y + r)) for c in range(W)] for r in range(H)]
    outside = set()
    todo = [(c, r) for c in range(W) for r in (0, H - 1)] + [(c, r) for r in range(H) for c in (0, W - 1)]
    while todo:
        c, r = todo.pop()
        if (c, r) in outside or not (0 <= c < W and 0 <= r < H) or px[r][c] != bg:
            continue
        outside.add((c, r))
        todo += [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
    vals = []
    for r in range(H):
        for c in range(W):
            if (c, r) in outside:
                vals.append("-1")
            else:
                p = px[r][c]
                vals.append(f"0x{(p[0] << 16) | (p[1] << 8) | p[2]:06X}")
    rows = [", ".join(vals[r * W:(r + 1) * W]) for r in range(H)]
    print(f"// {a.name}: measured from {a.image.split('/')[-1]} at {a.x},{a.y} ({W}x{H})")
    print(f"const Sprite {a.name} = {{{W}, {H}, {{")
    for row in rows:
        print(f"    {row},")
    print("}};")


if __name__ == "__main__":
    main()
