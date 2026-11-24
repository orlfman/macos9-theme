#!/usr/bin/env python3
"""Generate crisp 1x and @2x Platinum GTK assets from measured style tables.

Reads measured nine-slice and sprite tables from style/platinum/{slices,sprites}.h
and synthesizes exact field frames and uncaptured derived states (mixed check,
pressed-on check/radio, disabled check-off/radio-on/default-button/entry) using
the same rules as style/platinum/platinumstyle.cpp.

Output:
  gtk/Platinum/gtk-3.0/assets/<name>.png      (1x exact pixel art)
  gtk/Platinum/gtk-3.0/assets/<name>@2.png    (2x nearest-neighbor integer scale)
  gtk/Platinum/gtk-4.0/assets/<name>{,@2}.png (GTK 4 filtered-slice variants)

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SLICES_H = ROOT / "style" / "platinum" / "slices.h"
SPRITES_H = ROOT / "style" / "platinum" / "sprites.h"
PROGRESS_H = ROOT / "style" / "platinum" / "progress.h"
TABS_H = ROOT / "style" / "platinum" / "tabs.h"
OUT_GTK3 = ROOT / "gtk" / "Platinum" / "gtk-3.0" / "assets"
OUT_GTK4 = ROOT / "gtk" / "Platinum" / "gtk-4.0" / "assets"


def rgba(val: int) -> tuple[int, int, int, int]:
    if val < 0:
        return (0, 0, 0, 0)
    return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF, 255)


def parse_ints(text: str) -> list[int]:
    return [int(tok, 0) for tok in re.findall(r"-1|0x[0-9A-Fa-f]+|\d+", text)]


def parse_slices(path: Path) -> dict[str, tuple[int, list[int]]]:
    """Return {name: (K, flat_ints)} for each NineSlice<K> in slices.h."""
    src = path.read_text(encoding="utf-8")
    out: dict[str, tuple[int, list[int]]] = {}
    pat = re.compile(r"constexpr\s+NineSlice<(\d+)>\s+(\w+)\s*=\s*\{(.*?)\n\};", re.S)
    for m in pat.finditer(src):
        k = int(m.group(1))
        name = m.group(2)
        vals = parse_ints(m.group(3))
        expected = 4 * k * k + 4 * k + 1
        if len(vals) != expected:
            raise ValueError(f"{name}: expected {expected} ints, got {len(vals)}")
        out[name] = (k, vals)
    return out


def parse_sprites(path: Path) -> dict[str, tuple[int, int, list[int]]]:
    """Return {name: (w, h, pixels)} for each Sprite in sprites.h."""
    src = path.read_text(encoding="utf-8")
    out: dict[str, tuple[int, int, list[int]]] = {}
    pat = re.compile(r"const\s+Sprite\s+(\w+)\s*=\s*\{(\d+),\s*(\d+),\s*\{(.*?)\}\};", re.S)
    for m in pat.finditer(src):
        name = m.group(1)
        w, h = int(m.group(2)), int(m.group(3))
        vals = parse_ints(m.group(4))
        if len(vals) != w * h:
            raise ValueError(f"{name}: expected {w * h} pixels, got {len(vals)}")
        out[name] = (w, h, vals)
    return out


def slice_to_image(k: int, vals: list[int], fill_center: bool = True) -> Image.Image:
    """Build a (2K+1)x(2K+1) nine-slice RGBA image ready for CSS border-image."""
    size = 2 * k + 1
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()

    off = 0
    tl = [vals[off + r * k : off + (r + 1) * k] for r in range(k)]
    off += k * k
    tr = [vals[off + r * k : off + (r + 1) * k] for r in range(k)]
    off += k * k
    bl = [vals[off + r * k : off + (r + 1) * k] for r in range(k)]
    off += k * k
    br = [vals[off + r * k : off + (r + 1) * k] for r in range(k)]
    off += k * k
    top = vals[off : off + k]
    off += k
    bottom = vals[off : off + k]
    off += k
    left = vals[off : off + k]
    off += k
    right = vals[off : off + k]
    off += k
    fill = vals[off]

    # Corners
    for r in range(k):
        for c in range(k):
            px[c, r] = rgba(tl[r][c])
            px[k + 1 + c, r] = rgba(tr[r][c])
            px[c, k + 1 + r] = rgba(bl[r][c])
            px[k + 1 + c, k + 1 + r] = rgba(br[r][c])

    # 1 px stretched edge strips
    for i in range(k):
        px[k, i] = rgba(top[i])
        px[k, k + 1 + i] = rgba(bottom[i])
        px[i, k] = rgba(left[i])
        px[k + 1 + i, k] = rgba(right[i])

    # Center pixel
    px[k, k] = rgba(fill) if fill_center else (0, 0, 0, 0)
    return im


def sprite_to_image(w: int, h: int, vals: list[int]) -> Image.Image:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = rgba(vals[y * w + x])
    return im


def with_mark(
    base: tuple[int, int, list[int]],
    marked: tuple[int, int, list[int]],
    unmarked: tuple[int, int, list[int]],
    mark_color: int,
) -> Image.Image:
    """Port of style/platinum/platinumstyle.cpp drawWithMark()."""
    w, h, bvals = base
    _, _, mvals = marked
    _, _, uvals = unmarked
    out = list(bvals)
    for i in range(w * h):
        if mvals[i] == 0x000000 and uvals[i] != 0x000000:
            out[i] = mark_color
    return sprite_to_image(w, h, out)


def make_field_image(focused: bool, disabled: bool = False) -> Image.Image:
    """Port of style/platinum/platinumstyle.cpp drawField() as a 9x9 nine-slice (K=4)."""
    size = 9
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    x0, y0, x1, y1 = 0, 0, size - 1, size - 1

    def fill_rect(rx: int, ry: int, rw: int, rh: int, col: int) -> None:
        c = rgba(col)
        for yy in range(ry, ry + rh):
            for xx in range(rx, rx + rw):
                px[xx, yy] = c

    if disabled:
        # Derived/TBD disabled text field: transparent 2px margin, flat #888888 frame, #DDDDDD fill
        fill_rect(2, 2, size - 4, size - 4, 0x888888)
        fill_rect(3, 3, size - 6, size - 6, 0xDDDDDD)
        return im

    if focused:
        ring = 0x6666CC
        fill_rect(x0 + 1, y0, size - 2, 1, ring)
        fill_rect(x0 + 1, y1, size - 2, 1, ring)
        fill_rect(x0, y0 + 1, size, size - 2, ring)
    else:
        fill_rect(x0 + 1, y0 + 1, size - 3, 1, 0x888888)
        fill_rect(x0 + 1, y0 + 1, 1, size - 3, 0x888888)
        fill_rect(x1 - 1, y0 + 2, 1, size - 3, 0xFFFFFF)
        fill_rect(x0 + 2, y1 - 1, size - 3, 1, 0xFFFFFF)

    fill_rect(2, 2, size - 4, size - 4, 0x000000)
    fill_rect(3, 3, size - 6, size - 6, 0xFFFFFF)
    return im


def make_default_disabled_image(push_disabled: Image.Image) -> Image.Image:
    """Derived/TBD disabled default button: 3 px transparent ring slot + PushDisabled inside (17x17, K=8)."""
    # Place 9x9 PushDisabled centered inside 17x17, keeping 3px transparent outer margin
    # and extending the 1px disabled edges/fill across the 1px middle stretch row/col.
    k_in = 4
    k_out = 8
    size = 2 * k_out + 1  # 17
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Build a 11x11 rendered PushDisabled (3px inset -> 17 - 6 = 11)
    # Wait: for border-image slice 8 on 17x17, rows/cols 0..2 are transparent,
    # 3..6 are PushDisabled TL/TR/BL/BR, 7 is inner #DDDDDD, 8 is stretch center #DDDDDD!
    src = push_disabled.load()
    dst = im.load()
    # Map each coordinate in 0..16 to 0..8 of push_disabled (offset by 3px margin)
    for y in range(3, size - 3):
        sy = y - 3 if y < 7 else (4 if y <= 9 else y - 5)
        for x in range(3, size - 3):
            sx = x - 3 if x < 7 else (4 if x <= 9 else x - 5)
            dst[x, y] = src[sx, sy]
    return im


def make_check_off_disabled() -> Image.Image:
    """Derived/TBD disabled unchecked box: 12x12 flat #888888 outline, #DDDDDD fill, inside 14x12 canvas."""
    im = Image.new("RGBA", (14, 12), (0, 0, 0, 0))
    px = im.load()
    for y in range(12):
        for x in range(12):
            if x in (0, 11) or y in (0, 11):
                px[x, y] = rgba(0x888888)
            else:
                px[x, y] = rgba(0xDDDDDD)
    return im


def add_mixed_bar(base_im: Image.Image, bar_color: int) -> Image.Image:
    """Derived/TBD mixed checkbox bar: 6x2 centered at (3, 5) per platinumstyle.cpp:1736."""
    im = base_im.copy()
    px = im.load()
    c = rgba(bar_color)
    for y in range(5, 7):
        for x in range(3, 9):
            px[x, y] = c
    return im


def make_menu_frame() -> Image.Image:
    """Measured 5x5 (K=2) menu frame from docs/REFERENCE.md (menu-file-open.png)."""
    im = Image.new("RGBA", (5, 5), rgba(0xDDDDDD))
    px = im.load()
    for i in range(5):
        px[i, 0] = px[i, 4] = px[0, i] = px[4, i] = rgba(0x000000)
    px[1, 1] = px[2, 1] = px[1, 2] = rgba(0xFFFFFF)
    px[3, 2] = px[2, 3] = px[3, 3] = rgba(0x999999)
    px[3, 1] = px[1, 3] = rgba(0xDDDDDD)
    return im


def make_menu_check(color: int) -> Image.Image:
    """Original procedural 9x8 geometric menu checkmark (no copied font glyph)."""
    im = Image.new("RGBA", (9, 8), (0, 0, 0, 0))
    px = im.load()
    c = rgba(color)
    # Crisp 2px-stroke checkmark spanning 9x8
    pts = [
        (7, 0), (8, 0),
        (6, 1), (7, 1),
        (5, 2), (6, 2),
        (0, 3), (4, 3), (5, 3),
        (0, 4), (1, 4), (3, 4), (4, 4),
        (1, 5), (2, 5), (3, 5), (4, 5),
        (2, 6), (3, 6),
        (2, 7),
    ]
    for x, y in pts:
        px[x, y] = c
    return im


def make_menu_radio(color: int) -> Image.Image:
    """Original procedural 6x6 circular radio dot for menus."""
    im = Image.new("RGBA", (6, 6), (0, 0, 0, 0))
    px = im.load()
    c = rgba(color)
    for y in range(6):
        for x in range(6):
            if (x in (0, 5) and y in (0, 5)):
                continue
            px[x, y] = c
    return im


def make_menu_arrow(color: int) -> Image.Image:
    """Measured 6x11 solid right-pointing submenu triangle (docs/REFERENCE.md)."""
    im = Image.new("RGBA", (6, 11), (0, 0, 0, 0))
    px = im.load()
    c = rgba(color)
    for r in range(11):
        w = min(r + 1, 11 - r)
        for x in range(w):
            px[x, r] = c
    return im


def make_popup_frame(
    body_slice: tuple[int, list[int]],
    arrow_sprite: tuple[int, int, list[int]],
) -> Image.Image:
    """Build a 27x9 nine-slice (L=4, R=22, T=4, B=4) combining PopupBody left/middle
    with the arrowless cap frame from PopupArrow (rows 0..3, 4, 16..19).
    Arrows are drawn separately via popup-arrows-*.png so taller natural comboboxes
    stretch cleanly without distorting the double-arrow triangles."""
    body_im = slice_to_image(*body_slice)  # 9x9
    aw, ah, avals = arrow_sprite
    assert (aw, ah) == (22, 20)
    im = Image.new("RGBA", (4 + 1 + 22, 9), (0, 0, 0, 0))
    bpx = body_im.load()
    px = im.load()
    # Left 4 cols + 1 px horizontal stretch col from PopupBody (rows 0..8)
    for y in range(9):
        for x in range(5):
            px[x, y] = bpx[x, y]
    # Right 22 cols from PopupArrow rows: 0,1,2,3 (top), 4 (middle stretch), 16,17,18,19 (bottom)
    src_rows = (0, 1, 2, 3, 4, 16, 17, 18, 19)
    for dy, sy in enumerate(src_rows):
        for x in range(22):
            px[5 + x, dy] = rgba(avals[sy * 22 + x])
    return im


def make_popup_arrows(color: int) -> Image.Image:
    """Measured 14x10 double-arrow glyph matching PopupArrow rows 5..14 (cols 7..13
    of the 22px cap, placed 4px inset from right edge => cols 3..9 of 14px box)."""
    im = Image.new("RGBA", (14, 10), (0, 0, 0, 0))
    px = im.load()
    c = rgba(color)
    # Up triangle (rows 0..3: 1, 3, 5, 7 px centered at x=6)
    for r in range(4):
        for x in range(6 - r, 6 + r + 1):
            px[x, r] = c
    # Down triangle (rows 6..9: 7, 5, 3, 1 px centered at x=6)
    for r in range(4):
        half = 3 - r
        for x in range(6 - half, 6 + half + 1):
            px[x, 6 + r] = c
    return im


def make_sunken_frame() -> Image.Image:
    """Exact drawSunkenFrame() from style/platinum/platinumstyle.cpp:533 (5x5, K=2)."""
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    px = im.load()
    for x in range(4):
        px[x, 0] = rgba(0x888888)
    for y in range(4):
        px[0, y] = rgba(0x888888)
    for y in range(1, 5):
        px[4, y] = rgba(0xFFFFFF)
    for x in range(1, 5):
        px[x, 4] = rgba(0xFFFFFF)
    for y in range(1, 4):
        for x in range(1, 4):
            px[x, y] = rgba(0x000000)
    px[2, 2] = rgba(0xFFFFFF)
    return im


def make_groupbox_frame() -> Image.Image:
    """Measured etched group box frame (controls-general-controls.png, 5x5, K=2)."""
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    px = im.load()
    # White rect at (1,1)-(4,4) first
    for i in range(1, 5):
        px[i, 1] = px[i, 4] = px[1, i] = px[4, i] = rgba(0xFFFFFF)
    # Gray #888888 rect at (0,0)-(3,3) on top
    for i in range(0, 4):
        px[i, 0] = px[i, 3] = px[0, i] = px[3, i] = rgba(0x888888)
    px[2, 2] = (0, 0, 0, 0)
    return im


def parse_progress(path: Path) -> dict[str, list[int]]:
    """Parse 14-row measured columns from style/platinum/progress.h."""
    src = path.read_text(encoding="utf-8")
    out: dict[str, list[int]] = {}
    for m in re.finditer(r"constexpr\s+int\s+(\w+)\[14\]\s*=\s*\{(.*?)\};", src):
        vals = parse_ints(m.group(2))
        if len(vals) != 14:
            raise ValueError(f"progress {m.group(1)}: expected 14, got {len(vals)}")
        out[m.group(1)] = vals
    return out


def parse_tabs(path: Path) -> dict[str, tuple[list[tuple[int, int, list[int]]], list[tuple[int, int, list[int]]], list[int]]]:
    """Parse 24-row measured tab shapes (Normal, Current, Pressed) from style/platinum/tabs.h."""
    src = path.read_text(encoding="utf-8")
    out = {}
    edge_re = re.compile(r"\{(\d+),\s*(\d+),\s*\{([^}]*)\}\}")
    for m in re.finditer(r"constexpr\s+Shape\s+(\w+)\s*=\s*\{\n(.*?)\n\};", src, re.S):
        name = m.group(1)
        rows = [ln.strip() for ln in m.group(2).strip().splitlines() if ln.strip()]
        if len(rows) != 3:
            raise ValueError(f"tab {name}: expected 3 lines, got {len(rows)}")
        left = [(int(em.group(1)), int(em.group(2)), parse_ints(em.group(3))) for em in edge_re.finditer(rows[0])]
        right = [(int(em.group(1)), int(em.group(2)), parse_ints(em.group(3))) for em in edge_re.finditer(rows[1])]
        fill = parse_ints(rows[2])
        if len(left) != 24 or len(right) != 24 or len(fill) != 24:
            raise ValueError(f"tab {name}: expected 24 rows, got {len(left)}/{len(right)}/{len(fill)}")
        out[name] = (left, right, fill)
    return out


def insert_mid_row(im: Image.Image, split_y: int) -> Image.Image:
    """Insert a 1px vertical-stretch row at split_y so a CSS border-image with
    top=split_y, bottom=(im.height - split_y) renders all original rows 1:1 at
    height == im.height without needing CSS 'fill' (ignored by GTK 3)."""
    out = Image.new("RGBA", (im.width, im.height + 1), (0, 0, 0, 0))
    out.paste(im.crop((0, 0, im.width, split_y)), (0, 0))
    out.paste(im.crop((0, split_y, im.width, split_y + 1)), (0, split_y))
    out.paste(im.crop((0, split_y, im.width, im.height)), (0, split_y + 1))
    return out


def insert_mid_col(im: Image.Image, split_x: int) -> Image.Image:
    """Insert a 1px horizontal-stretch col at split_x (transpose counterpart of insert_mid_row)."""
    tr = Image.Transpose.TRANSPOSE
    return insert_mid_row(im.transpose(tr), split_x).transpose(tr)


def make_tab_image(
    shape: tuple[list[tuple[int, int, list[int]]], list[tuple[int, int, list[int]]], list[int]],
    width: int = 25,
) -> Image.Image:
    """Render a 25x25 nine-slice tab (L=12, R=12, T=12, B=12) matching drawTab()."""
    left, right, fill = shape
    im = Image.new("RGBA", (width, 24), (0, 0, 0, 0))
    px = im.load()
    for row in range(24):
        lo, ll, lpix = left[row]
        ro, rl, rpix = right[row]
        x_from = lo + ll
        x_to = (width - 1) - ro - rl
        if x_to >= x_from:
            fc = rgba(fill[row])
            for x in range(x_from, x_to + 1):
                px[x, row] = fc
        for i in range(ll):
            px[lo + i, row] = rgba(lpix[i])
        for i in range(rl):
            px[(width - 1) - ro - i, row] = rgba(rpix[i])
    return insert_mid_row(im, 12)


def make_scale_trough_h(
    gl: tuple[int, int, list[int]],
    gm: tuple[int, int, list[int]],
    gr: tuple[int, int, list[int]],
) -> Image.Image:
    """Build 7x8 horizontal slider groove nine-slice (L=3, R=3, T=3, B=4)."""
    im = Image.new("RGBA", (7, 7), (0, 0, 0, 0))
    px = im.load()
    for y in range(7):
        for x in range(3):
            px[x, y] = rgba(gl[2][y * 3 + x])
            px[4 + x, y] = rgba(gr[2][y * 3 + x])
        px[3, y] = rgba(gm[2][y])
    return insert_mid_row(im, 3)


def make_scale_tick_h() -> Image.Image:
    """Measured 3x7 slider tick mark (platinumstyle.cpp:1063-1066)."""
    im = Image.new("RGBA", (3, 7), (0, 0, 0, 0))
    px = im.load()
    px[0, 0] = px[1, 0] = rgba(0xFFFFFF)
    for y in range(1, 7):
        px[0, y] = rgba(0xFFFFFF)
        px[1, y] = rgba(0x000000)
        px[2, y] = rgba(0x888888)
    return im


def make_vscroll_trough() -> Image.Image:
    """Measured 16px active scrollbar sunken track (platinumstyle.cpp:136-154).
    Returns 17x5 nine-slice (L=8, R=8, T=2, B=2) so all 16 cols + 2 top shadow rows
    and stretched vertical body draw cleanly via border-image."""
    base = [0x000000, 0x777777, 0x888888] + [0xAAAAAA] * 10 + [0xBBBBBB, 0xCCCCCC, 0x000000]
    r0 = [0x000000] + [0x777777] * 13 + [0xCCCCCC, 0x000000]
    r1 = [0x000000, 0x777777] + [0x888888] * 11 + [0xBBBBBB, 0xCCCCCC, 0x000000]
    im = Image.new("RGBA", (16, 5), (0, 0, 0, 0))
    px = im.load()
    for x in range(16):
        px[x, 0] = rgba(r0[x])
        px[x, 1] = rgba(r1[x])
        for y in (2, 3, 4):
            px[x, y] = rgba(base[x])
    return insert_mid_col(im, 8)


def make_scroll_thumb_frame(pressed: bool) -> Image.Image:
    """6x6 nine-slice (K=2) with transparent center for scroll thumb bevel
    (platinumstyle.cpp:112-125). Symmetric under x<->y transpose."""
    hi = 0x9999FF if pressed else 0xCCCCFF
    fill = 0x6666CC if pressed else 0x9999FF
    lo = 0x333399 if pressed else 0x6666CC
    corner_tl = 0xCCCCFF if pressed else 0xEEEEEE
    im = Image.new("RGBA", (6, 6), (0, 0, 0, 0))
    px = im.load()
    for i in range(6):
        px[i, 0] = px[i, 5] = px[0, i] = px[5, i] = rgba(0x000000)
    # Inner bevel ring at (1..4, 1..4)
    for i in range(1, 4):
        px[i, 1] = rgba(hi)
        px[1, i] = rgba(hi)
    px[1, 1] = rgba(corner_tl)
    px[4, 1] = rgba(fill)
    px[1, 4] = rgba(fill)
    for i in range(2, 5):
        px[4, i] = rgba(lo)
        px[i, 4] = rgba(lo)
    # Center (2..3, 2..3) stays transparent so background-color + centered grip show
    return im


def make_vscroll_grip() -> Image.Image:
    """Measured 16x8 4-bar Lavender grip (platinumstyle.cpp:126-133)."""
    im = Image.new("RGBA", (16, 8), (0, 0, 0, 0))
    px = im.load()
    for i in range(4):
        px[4, 2 * i] = rgba(0xEEEEEE)
        for x in range(5, 11):
            px[x, 2 * i] = rgba(0xCCCCFF)
        for x in range(5, 12):
            px[x, 2 * i + 1] = rgba(0x333399)
    return im


def make_vscroll_arrow(up: bool, pressed: bool, trim_bottom: bool = False) -> Image.Image:
    """Measured 16x16 scroll arrow box (platinumstyle.cpp:90-110).
    When trim_bottom=True (for button.up stacked above button.down), returns 16x15
    so button.down's top black row serves as their shared border with zero negative margins."""
    hi = 0x555555 if pressed else 0xFFFFFF
    fill = 0x777777 if pressed else 0xDDDDDD
    lo = 0x999999 if pressed else 0xBBBBBB
    im = Image.new("RGBA", (16, 16), rgba(fill))
    px = im.load()
    for i in range(16):
        px[i, 0] = px[i, 15] = px[0, i] = px[15, i] = rgba(0x000000)
    for i in range(1, 14):
        px[i, 1] = rgba(hi)
        px[1, i] = rgba(hi)
    for i in range(2, 15):
        px[14, i] = rgba(lo)
        px[i, 14] = rgba(lo)
    cx = 7
    for i in range(4):
        half = i if up else (3 - i)
        for x in range(cx - half, cx + 2 + half):
            px[x, 6 + i] = rgba(0x000000)
    return im.crop((0, 0, 16, 15)) if trim_bottom else im


def make_progress_assets(prog: dict[str, list[int]]) -> dict[str, Image.Image]:
    """Build determinate & indeterminate horizontal/vertical progressbar assets from progress.h."""
    def cols_to_img(cols: list[list[int]], r0: int = 0, r1: int = 14) -> Image.Image:
        im = Image.new("RGBA", (len(cols), r1 - r0), (0, 0, 0, 0))
        px = im.load()
        for x, col in enumerate(cols):
            for y in range(r0, r1):
                px[x, y - r0] = rgba(col[y])
        return im

    trough_h = insert_mid_row(cols_to_img([
        prog["OuterLeft"], prog["FrameLeft"], prog["Divider"], prog["TroughShadow0"], prog["TroughShadow1"],
        prog["TroughMid"],
        prog["TroughRight"], prog["FrameRight"], prog["OuterRight"],
    ]), 7)
    fill_h = insert_mid_row(cols_to_img([
        prog["FillStart0"], prog["FillStart1"],
        prog["FillMid"],
        prog["FillEnd0"], prog["FillEnd1"], prog["FillEnd2"],
        prog["Divider"], prog["TroughShadow0"], prog["TroughShadow1"],
    ], 2, 12), 5)
    fill_full_h = insert_mid_row(cols_to_img([
        prog["FillStart0"], prog["FillStart1"],
        prog["FillMid"],
        prog["FillEnd0"], prog["FillEnd1"], prog["FillEnd2"],
    ], 2, 12), 5)

    # Barber pole 16x10 tile at phase=4 (matching check-style.sh PLATINUM_BARBER_PHASE=4)
    lav = [0x000088, 0x333399, 0x6666CC, 0x9999FF, 0xCCCCFF, 0x9999FF, 0x6666CC, 0x333399, 0x000088, 0x000055]
    grey = [0x555555, 0x777777, 0xAAAAAA, 0xBBBBBB, 0xFFFFFF, 0xDDDDDD, 0xBBBBBB, 0x999999, 0x777777, 0x555555]
    pulse_h = Image.new("RGBA", (16, 10), (0, 0, 0, 0))
    ppx = pulse_h.load()
    phase = 4
    for r in range(10):
        for c in range(16):
            stripe = (c - r - phase + 32) % 16
            ppx[c, r] = rgba(grey[r] if stripe < 8 else lav[r])

    tr = Image.Transpose.TRANSPOSE
    return {
        "progress-trough-h": trough_h,
        "progress-fill-h": fill_h,
        "progress-fill-full-h": fill_full_h,
        "progress-fill-reversed-h": fill_full_h.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        "progress-pulse-h": pulse_h,
        "progress-trough-v": trough_h.transpose(tr),
        "progress-fill-v": fill_h.transpose(tr),
        "progress-fill-full-v": fill_full_h.transpose(tr),
        "progress-fill-reversed-v": fill_full_h.transpose(tr).transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        "progress-pulse-v": pulse_h.transpose(tr),
    }


def make_tooltip_balloon(size: int = 20) -> Image.Image:
    """Exact drawBalloon() from style/platinum/platinumstyle.cpp:600 (20x20, K=7)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = im.load()
    tl = ((0, 0), (3, 5), (2, 3), (1, 2), (1, 1), (0, 1))
    bl = ((0, 0), (0, 0), (2, 4), (1, 2), (1, 1), (0, 1))
    tr = ((0, 0), (6, 3), (4, 2), (3, 1), (2, 1), (2, 0), (1, 0))
    br = ((0, 0), (0, 0), (6, 2), (4, 1), (3, 1), (2, 0), (2, 0))
    x0, x1, y0, y1 = 0, size - 1, 0, size - 1
    for y in range(size):
        t, b = y - y0, y1 - y
        if t == 0:
            for x in range(x0 + 5, x1 - 6 + 1):
                px[x, y] = rgba(0x000000)
            continue
        if b in (0, 1):
            fx = x0 + (5 if b == 0 else 3)
            tx = x1 - (5 if b == 0 else 3)
            for x in range(fx, tx + 1):
                px[x, y] = rgba(0x000000)
            continue
        l0, l1 = tl[t] if t <= 5 else (bl[b] if b <= 5 else (0, 0))
        r0, r1 = tr[t] if t <= 6 else (br[b] if b <= 6 else (1, 0))
        for x in range(x0 + l0, x0 + l1 + 1):
            px[x, y] = rgba(0x000000)
        for x in range(x1 - r0, x1 - r1 + 1):
            px[x, y] = rgba(0x000000)
        for x in range(x0 + l1 + 1, x1 - r0):
            px[x, y] = rgba(0xFFFFFF)
    return im


def make_modal_frame() -> Image.Image:
    """Exact drawModalFrame() from style/platinum/platinumstyle.cpp:399 (9x9, K=4)."""
    im = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    px = im.load()
    x0, y0, x1, y1 = 0, 0, 7, 7
    # Outer 1px black drop shadow right & bottom starting 2px in
    for y in range(y0 + 2, y1 + 2):
        px[x1 + 1, y] = rgba(0x000000)
    for x in range(x0 + 2, x1 + 2):
        px[x, y1 + 1] = rgba(0x000000)
    # 1px black outline
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = rgba(0x000000)
    # Interior fill #FFFFFF (measured dialog-modal-plain.png & styleshot.cpp:420)
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            px[x, y] = rgba(0xFFFFFF)
    for x in range(x0 + 1, x1):
        px[x, y0 + 1] = rgba(0xBBBBBB)
    for y in range(y0 + 1, y1):
        px[x0 + 1, y] = rgba(0xBBBBBB)
    for y in range(y0 + 2, y1):
        px[x1 - 1, y] = rgba(0x555555)
    for x in range(x0 + 2, x1):
        px[x, y1 - 1] = rgba(0x555555)
    for y in range(y0 + 3, y1 - 1):
        px[x1 - 2, y] = rgba(0x999999)
    for x in range(x0 + 3, x1 - 1):
        px[x, y1 - 2] = rgba(0x999999)
    px[x1 - 2, y0 + 2] = rgba(0xBBBBBB)
    px[x0 + 2, y1 - 2] = rgba(0xBBBBBB)
    return im


def make_headerbar_stripes() -> Image.Image:
    """Measured 1x12 Platinum title-bar pinstripe column (6 white + #777777 pairs)."""
    im = Image.new("RGBA", (1, 12), (0, 0, 0, 0))
    px = im.load()
    for i in range(6):
        px[0, 2 * i] = rgba(0xFFFFFF)
        px[0, 2 * i + 1] = rgba(0x777777)
    return im


def make_titlebutton_box(glyph: str, pressed: bool = False, backdrop: bool = False) -> Image.Image:
    """Exact 13x13 Platinum window box from decoration/platinum.cpp:95 (drawBox)."""
    im = Image.new("RGBA", (13, 13), (0, 0, 0, 0))
    px = im.load()
    if backdrop:
        for y in range(1, 12):
            for x in range(1, 12):
                px[x, y] = rgba(0xDDDDDD)
        for i in range(1, 12):
            px[i, 1] = px[i, 11] = px[1, i] = px[11, i] = rgba(0x888888)
        return im
    for x in range(12):
        px[x, 0] = rgba(0x888888)
    for y in range(12):
        px[0, y] = rgba(0x888888)
    px[12, 0] = px[0, 12] = rgba(0xCCCCCC)
    for i in range(1, 13):
        px[i, 12] = px[12, i] = rgba(0xFFFFFF)
    for i in range(1, 12):
        px[i, 1] = px[i, 11] = px[1, i] = px[11, i] = rgba(0x222222)
    if pressed:
        ramp = (0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC)
        for r in range(9):
            for c in range(9):
                v = ramp[(r + c) // 2]
                if r == 8 or c == 8:
                    v = min(v, 0x99)
                px[2 + c, 2 + r] = rgba(v * 0x010101)
    else:
        ramp = (0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF)
        px[2, 2] = rgba(0xFFFFFF)
        for i in range(3, 11):
            px[i, 2] = rgba(0xCCCCCC)
            px[2, i] = rgba(0xCCCCCC)
            px[i, 10] = rgba(0x888888)
        for i in range(3, 10):
            px[10, i] = rgba(0x888888)
        for r in range(7):
            for c in range(7):
                px[3 + c, 3 + r] = rgba(ramp[(r + c) // 2] * 0x010101)
    if glyph == "zoom":
        for y in range(2, 8):
            px[7, y] = rgba(0x222222)
        for x in range(2, 8):
            px[x, 7] = rgba(0x222222)
    elif glyph == "collapse":
        for x in range(2, 11):
            px[x, 5] = px[x, 7] = rgba(0x222222)
    return im


def pad_slice_center(image: Image.Image, stretch_x: int, stretch_y: int) -> Image.Image:
    """Guard both sides of one-pixel stretch strips from GTK 4 texture filtering."""
    xs = (*range(stretch_x), stretch_x, stretch_x, *range(stretch_x, image.width))
    ys = (*range(stretch_y), stretch_y, stretch_y, *range(stretch_y, image.height))
    padded = Image.new(image.mode, (len(xs), len(ys)))
    padded.putdata([image.getpixel((x, y)) for y in ys for x in xs])
    return padded


def save_asset(out_dir: Path, name: str, im: Image.Image) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    im.save(out_dir / f"{name}.png")
    im2 = im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)
    im2.save(out_dir / f"{name}@2.png")


def main() -> int:
    slices = parse_slices(SLICES_H)
    sprites = parse_sprites(SPRITES_H)
    progress = parse_progress(PROGRESS_H)
    tabs = parse_tabs(TABS_H)
    tr = Image.Transpose.TRANSPOSE

    scale_trough_h = make_scale_trough_h(
        sprites["GrooveLeft"], sprites["GrooveMid"], sprites["GrooveRight"]
    )
    scale_trough_hd = make_scale_trough_h(
        sprites["GrooveLeftDisabled"], sprites["GrooveMidDisabled"], sprites["GrooveRightDisabled"]
    )
    scale_tick_h = make_scale_tick_h()
    vscroll_trough = make_vscroll_trough()
    vscroll_grip = make_vscroll_grip()
    vscroll_up = make_vscroll_arrow(up=True, pressed=False, trim_bottom=True)
    vscroll_up_p = make_vscroll_arrow(up=True, pressed=True, trim_bottom=True)
    vscroll_dn = make_vscroll_arrow(up=False, pressed=False, trim_bottom=False)
    vscroll_dn_p = make_vscroll_arrow(up=False, pressed=True, trim_bottom=False)
    tab_top_normal = make_tab_image(tabs["Normal"])
    tab_top_active = make_tab_image(tabs["Current"])
    tab_top_pressed = make_tab_image(tabs["Pressed"])

    # Push buttons (measured 9-slices)
    push_normal = slice_to_image(*slices["PushNormal"])
    push_pressed = slice_to_image(*slices["PushPressed"])
    # PushDisabled fills #DDDDDD on #DDDDDD; keep fill_center=True so it also reads cleanly on #EEEEEE panes
    push_disabled = slice_to_image(*slices["PushDisabled"], fill_center=True)
    push_default = slice_to_image(*slices["PushDefault"])
    push_default_pressed = slice_to_image(*slices["PushDefaultPressed"])
    push_default_disabled = make_default_disabled_image(push_disabled)

    assets: dict[str, Image.Image] = {
        "push-normal": push_normal,
        "push-pressed": push_pressed,
        "push-disabled": push_disabled,
        "push-default": push_default,
        "push-default-pressed": push_default_pressed,
        "push-default-disabled": push_default_disabled,
        # Text entry frames (measured drawField + derived disabled)
        "entry-normal": make_field_image(focused=False),
        "entry-focused": make_field_image(focused=True),
        "entry-disabled": make_field_image(focused=False, disabled=True),
        # Checkboxes (measured sprites + derived states)
        "check-off": sprite_to_image(*sprites["CheckOff"]),
        "check-on": sprite_to_image(*sprites["CheckOn"]),
        "check-off-pressed": sprite_to_image(*sprites["CheckOffPressed"]),
        "check-on-pressed": with_mark(sprites["CheckOffPressed"], sprites["CheckOn"], sprites["CheckOff"], 0x000000),
        "check-off-disabled": make_check_off_disabled(),
        "check-on-disabled": sprite_to_image(*sprites["CheckOnDisabled"]),
        "check-mixed": add_mixed_bar(sprite_to_image(*sprites["CheckOff"]), 0x000000),
        "check-mixed-pressed": add_mixed_bar(sprite_to_image(*sprites["CheckOffPressed"]), 0x000000),
        "check-mixed-disabled": add_mixed_bar(make_check_off_disabled(), 0x888888),
        # Radio buttons (measured sprites + derived states)
        "radio-off": sprite_to_image(*sprites["RadioOff"]),
        "radio-on": sprite_to_image(*sprites["RadioOn"]),
        "radio-off-pressed": sprite_to_image(*sprites["RadioOffPressed"]),
        "radio-on-pressed": with_mark(sprites["RadioOffPressed"], sprites["RadioOn"], sprites["RadioOff"], 0x000000),
        "radio-off-disabled": sprite_to_image(*sprites["RadioOffDisabled"]),
        "radio-on-disabled": with_mark(sprites["RadioOffDisabled"], sprites["RadioOn"], sprites["RadioOff"], 0x888888),
        # Milestone 3 Batch 1: Menus, Pop-ups/ComboBoxes, List Headers, Triangles, Frames
        "menu-frame": make_menu_frame(),
        "menu-check-normal": make_menu_check(0x000000),
        "menu-check-hover": make_menu_check(0xFFFFFF),
        "menu-check-disabled": make_menu_check(0x777777),
        "menu-radio-normal": make_menu_radio(0x000000),
        "menu-radio-hover": make_menu_radio(0xFFFFFF),
        "menu-radio-disabled": make_menu_radio(0x777777),
        "menu-arrow-normal": make_menu_arrow(0x000000),
        "menu-arrow-hover": make_menu_arrow(0xFFFFFF),
        "menu-arrow-disabled": make_menu_arrow(0x777777),
        "popup-frame-normal": make_popup_frame(slices["PopupBody"], sprites["PopupArrow"]),
        "popup-frame-disabled": make_popup_frame(slices["PopupBodyDisabled"], sprites["PopupArrowDisabled"]),
        "popup-frame-pressed": make_popup_frame(slices["PushPressed"], sprites["PopupArrowPressed"]),
        "popup-arrows-normal": make_popup_arrows(0x000000),
        "popup-arrows-disabled": make_popup_arrows(0x888888),
        "popup-arrows-pressed": make_popup_arrows(0xFFFFFF),
        "header-normal": slice_to_image(*slices["HeaderSection"]),
        "header-sorted": slice_to_image(*slices["HeaderSorted"]),
        "triangle-closed": sprite_to_image(*sprites["TriangleClosed"]),
        "triangle-open": sprite_to_image(*sprites["TriangleOpen"]),
        "triangle-pressed": sprite_to_image(*sprites["TrianglePressed"]),
        "sunken-frame": make_sunken_frame(),
        "groupbox-frame": make_groupbox_frame(),
        # Milestone 3 Batch 2: Tabs, Scales, Scrollbars, Progress bars, Tooltips, Dialogs, CSD
        "tab-pane": slice_to_image(*slices["TabPane"]),
        "tab-top-normal": tab_top_normal,
        "tab-top-active": tab_top_active,
        "tab-top-pressed": tab_top_pressed,
        "tab-bottom-normal": tab_top_normal.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        "tab-bottom-active": tab_top_active.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        "tab-bottom-pressed": tab_top_pressed.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
        "scale-trough-h": scale_trough_h,
        "scale-trough-h-disabled": scale_trough_hd,
        "scale-trough-v": scale_trough_h.transpose(tr),
        "scale-trough-v-disabled": scale_trough_hd.transpose(tr),
        "slider-thumb-h": sprite_to_image(*sprites["SliderThumb"]),
        "slider-thumb-h-pressed": sprite_to_image(*sprites["SliderThumbPressed"]),
        "slider-thumb-h-disabled": sprite_to_image(*sprites["SliderThumbDisabled"]),
        "slider-thumb-v": sprite_to_image(*sprites["SliderThumb"]).transpose(tr),
        "slider-thumb-v-pressed": sprite_to_image(*sprites["SliderThumbPressed"]).transpose(tr),
        "slider-thumb-v-disabled": sprite_to_image(*sprites["SliderThumbDisabled"]).transpose(tr),
        "scale-tick-h": scale_tick_h,
        "scale-tick-v": scale_tick_h.transpose(tr),
        "vscroll-trough": vscroll_trough,
        "hscroll-trough": vscroll_trough.transpose(tr),
        "scroll-thumb-frame": make_scroll_thumb_frame(pressed=False),
        "scroll-thumb-frame-pressed": make_scroll_thumb_frame(pressed=True),
        "vscroll-grip": vscroll_grip,
        "hscroll-grip": vscroll_grip.transpose(tr),
        "vscroll-up": vscroll_up,
        "vscroll-up-pressed": vscroll_up_p,
        "vscroll-down": vscroll_dn,
        "vscroll-down-pressed": vscroll_dn_p,
        "hscroll-left": vscroll_up.transpose(tr),
        "hscroll-left-pressed": vscroll_up_p.transpose(tr),
        "hscroll-right": vscroll_dn.transpose(tr),
        "hscroll-right-pressed": vscroll_dn_p.transpose(tr),
        "tooltip-balloon": make_tooltip_balloon(),
        "modal-frame": make_modal_frame(),
        "headerbar-stripes": make_headerbar_stripes(),
        "titlebutton-close": make_titlebutton_box("none", pressed=False),
        "titlebutton-close-pressed": make_titlebutton_box("none", pressed=True),
        "titlebutton-maximize": make_titlebutton_box("zoom", pressed=False),
        "titlebutton-maximize-pressed": make_titlebutton_box("zoom", pressed=True),
        "titlebutton-minimize": make_titlebutton_box("collapse", pressed=False),
        "titlebutton-minimize-pressed": make_titlebutton_box("collapse", pressed=True),
        "titlebutton-backdrop": make_titlebutton_box("none", backdrop=True),
        **make_progress_assets(progress),
    }

    for name, im in assets.items():
        save_asset(OUT_GTK3, name, im)

    for name in ("push-normal", "push-pressed"):
        save_asset(OUT_GTK4, name, pad_slice_center(assets[name], 4, 4))

    for state in ("normal", "pressed", "disabled"):
        name = f"popup-frame-{state}"
        frame = pad_slice_center(assets[name], 4, 4)
        save_asset(OUT_GTK4, name, frame)
        save_asset(OUT_GTK4, name + "-rtl", frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT))

    for name in ("header-normal", "header-sorted"):
        save_asset(OUT_GTK4, name, pad_slice_center(assets[name], 2, 2))

    print(f"Generated GTK 4 button, dropdown and column-header slices in {OUT_GTK4}")
    print(f"Generated {len(assets)} assets (1x + @2x = {len(assets) * 2} PNGs) in {OUT_GTK3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
