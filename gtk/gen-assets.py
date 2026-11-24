#!/usr/bin/env python3
"""Generate crisp 1x and @2x Platinum GTK assets from measured style tables.

Reads measured nine-slice and sprite tables from style/platinum/{slices,sprites}.h
and synthesizes exact field frames and uncaptured derived states (mixed check,
pressed-on check/radio, disabled check-off/radio-on/default-button/entry) using
the same rules as style/platinum/platinumstyle.cpp.

Output:
  gtk/Platinum/gtk-3.0/assets/<name>.png      (1x exact pixel art)
  gtk/Platinum/gtk-3.0/assets/<name>@2.png    (2x nearest-neighbor integer scale)

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
OUT_GTK3 = ROOT / "gtk" / "Platinum" / "gtk-3.0" / "assets"


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


def save_asset(out_dir: Path, name: str, im: Image.Image) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    im.save(out_dir / f"{name}.png")
    im2 = im.resize((im.width * 2, im.height * 2), Image.Resampling.NEAREST)
    im2.save(out_dir / f"{name}@2.png")


def main() -> int:
    slices = parse_slices(SLICES_H)
    sprites = parse_sprites(SPRITES_H)

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
    }

    for name, im in assets.items():
        save_asset(OUT_GTK3, name, im)

    print(f"Generated {len(assets)} assets (1x + @2x = {len(assets) * 2} PNGs) in {OUT_GTK3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
