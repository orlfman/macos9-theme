#!/usr/bin/env python3
# Stock row over layer row for a dev/check-adw.sh run: montage.png.
# usage: montage.py <run dir> [mode ...]
# SPDX-License-Identifier: BSD-2-Clause
import pathlib
import sys

from PIL import Image

root = pathlib.Path(sys.argv[1])
modes = sys.argv[2:] or ["gallery", "dialog", "focus"]
rows = [[Image.open(root / f"{pre}-{m}.png") for m in modes]
        for pre in ("stock", "layer")]
w = sum(i.width for i in rows[0])
h = sum(max(i.height for i in r) for r in rows)
out = Image.new("RGBA", (w, h), "white")
y = 0
for r in rows:
    x = 0
    for i in r:
        out.paste(i, (x, y))
        x += i.width
    y += max(i.height for i in r)
out.save(root / "montage.png")
print(root / "montage.png")
