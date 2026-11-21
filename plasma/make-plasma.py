#!/usr/bin/env python3
"""Writes the Platinum Plasma style into ./platinum.

Plasma styles are SVGs cut into 9-patch pieces (topleft, top, ..., center)
with hint rectangles for content margins. Platinum is all square pixel
lines, so every frame is a list of 1 px-aligned rectangles cut into pieces
exactly. The 9-patch writer comes from the user's windows2000-union project
(plasma/make-plasma.py, BSD-2-Clause); colors here are the measured
Platinum values (docs/REFERENCE.md) rather than color scheme classes, and
the push button and text field come from the style's own measured data
(style/platinum/slices.h).

Parts:
  widgets/panel-background  the menu bar (top panel, 20 px)
  widgets/menubaritem       global menu titles: the open title's Lavender bevel
  dialogs/background        popups: the Mac OS 9 menu frame with its shadow
  widgets/tooltip           help balloons (no tail)
  widgets/viewitem          list highlights in popups (#333399, white text
                            via this style's own colors file)
  widgets/button, lineedit, frame, tabbar, plasmoidheading
  colors                    Platinum.colors with the menu highlight as the
                            selection (Plasma only; apps keep #CCCCFF)

usage: python3 -I plasma/make-plasma.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BLACK, WHITE = "#000000", "#ffffff"
GRAY = {v: f"#{v:02x}{v:02x}{v:02x}" for v in range(256)}
FACE = GRAY[0xDD]
LAV_LIGHT, LAV, LAV_DARK = "#6666cc", "#333399", "#000088"
SELECTION = "#ccccff"


class Sheet:
    """One SVG file: frames and hints laid out in rows, without overlaps."""

    def __init__(self):
        self.parts = []
        self.y = 0

    @staticmethod
    def rect(x, y, w, h, color=None, ident=None):
        attrs = f'x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"'
        idattr = f'id="{ident}" ' if ident else ""
        if color is None:
            # Invisible, but gives a piece or a hint its size.
            return f'<rect {idattr}{attrs} style="fill:#000000;fill-opacity:0"/>'
        return f'<rect {idattr}{attrs} style="fill:{color}"/>'

    def frame(self, prefix, borders, shapes, center=(2, 2), center_shapes=None):
        """A 9-patch frame. borders = (top, right, bottom, left); shapes is a
        function (w, h) -> [(x, y, w, h, color)] in frame coordinates."""
        top, right, bottom, left = borders
        cw, ch = center
        w, h = left + cw + right, top + ch + bottom
        oy = self.y
        regions = {
            "topleft": (0, 0, left, top), "top": (left, 0, cw, top), "topright": (left + cw, 0, right, top),
            "left": (0, top, left, ch), "center": (left, top, cw, ch), "right": (left + cw, top, right, ch),
            "bottomleft": (0, top + ch, left, bottom), "bottom": (left, top + ch, cw, bottom),
            "bottomright": (left + cw, top + ch, right, bottom),
        }
        items = shapes(w, h)
        for name, (rx, ry, rw, rh) in regions.items():
            if rw <= 0 or rh <= 0:
                continue
            ident = f"{prefix}-{name}" if prefix else name
            body = [self.rect(rx, oy + ry, rw, rh)]
            pieces = items
            if name == "center" and center_shapes is not None:
                pieces = [(rx + x, ry + y, pw, ph, c) for (x, y, pw, ph, c) in center_shapes]
            for (sx, sy, sw, sh, color) in pieces:
                x0, y0 = max(sx, rx), max(sy, ry)
                x1, y1 = min(sx + sw, rx + rw), min(sy + sh, ry + rh)
                if x1 > x0 and y1 > y0 and color:
                    body.append(self.rect(x0, oy + y0, x1 - x0, y1 - y0, color))
            self.parts.append(f'<g id="{ident}">{"".join(body)}</g>')
        self.y += h + 4

    def hints(self, prefix, margins, insets=False):
        """Margin hints (top, right, bottom, left): rectangles whose size is
        the content margin. A zero margin is a hair-thin rectangle."""
        top, right, bottom, left = (m if m else 1e-8 for m in margins)
        p = f"{prefix}-" if prefix else ""
        y = self.y
        self.parts += [
            self.rect(0, y, 4, top, ident=f"{p}hint-top-margin"),
            self.rect(6, y, 4, bottom, ident=f"{p}hint-bottom-margin"),
            self.rect(12, y, left, 4, ident=f"{p}hint-left-margin"),
            self.rect(30, y, right, 4, ident=f"{p}hint-right-margin"),
        ]
        if insets:
            # Zero insets: no shadow or glow outside the frame.
            self.parts += [
                self.rect(50, y, 4, 1e-8, ident=f"{p}hint-top-inset"),
                self.rect(56, y, 4, 1e-8, ident=f"{p}hint-bottom-inset"),
                self.rect(62, y, 1e-8, 4, ident=f"{p}hint-left-inset"),
                self.rect(64, y, 1e-8, 4, ident=f"{p}hint-right-inset"),
            ]
        self.y += max(margins[0], margins[2], 4) + 4

    def flag(self, ident):
        """A marker element like hint-tile-center: present means on."""
        self.parts.append(self.rect(80, self.y, 2, 2, ident=ident))
        self.y += 6

    def svg(self):
        body = "\n  ".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="{self.y}" viewBox="0 0 200 {self.y}">\n'
                "<!-- Generated by plasma/make-plasma.py from measured Mac OS 9.2.2 values. "
                "SPDX-License-Identifier: BSD-2-Clause -->\n"
                f"  {body}\n</svg>\n")


def nineslice(name):
    """A measured 9-slice from style/platinum/slices.h as a shapes function
    (corners pixel by pixel, edges stretched, center filled)."""
    text = (ROOT / "style/platinum/slices.h").read_text()
    m = re.search(r"const NineSlice<(\d+)> %s = \{(.*?)\n\};" % name, text, re.S)
    k = int(m[1])
    vals = [None if v == "-1" else "#" + v[2:].lower() for v in re.findall(r"-1|0x[0-9A-Fa-f]{6}", m[2])]
    corners = [vals[i * k * k:(i + 1) * k * k] for i in range(4)]  # tl, tr, bl, br
    edges = [vals[4 * k * k + i * k:4 * k * k + (i + 1) * k] for i in range(4)]  # top, bottom, left, right
    fill = vals[4 * k * k + 4 * k]

    def shapes(w, h):
        out = [(k, k, w - 2 * k, h - 2 * k, fill)]
        for i in range(k):
            out += [(k, i, w - 2 * k, 1, edges[0][i]), (k, h - k + i, w - 2 * k, 1, edges[1][i]),
                    (i, k, 1, h - 2 * k, edges[2][i]), (w - k + i, k, 1, h - 2 * k, edges[3][i])]
        for (cx, cy), c in zip(((0, 0), (w - k, 0), (0, h - k), (w - k, h - k)), corners):
            for r in range(k):
                for col in range(k):
                    out.append((cx + col, cy + r, 1, 1, c[r * k + col]))
        return out
    return k, shapes


def menu_frame(w, h):
    """The Mac OS 9 menu frame (style/platinum/platinumstyle.cpp,
    drawMenuPanel): #222222 shadow right and bottom from 2 px in, black
    outline, white top/left and #999999 right/bottom bevel, the two corners
    where they meet in the #DDDDDD fill."""
    ix, iy, iw, ih = 1, 1, w - 3, h - 3
    return [
        (w - 1, 2, 1, h - 2, GRAY[0x22]), (2, h - 1, w - 2, 1, GRAY[0x22]),
        (0, 0, w - 1, h - 1, BLACK),
        (ix, iy, iw, ih, FACE),
        (ix, iy, iw - 1, 1, WHITE), (ix, iy, 1, ih - 1, WHITE),
        (ix + iw - 1, iy + 1, 1, ih - 1, GRAY[0x99]), (ix + 1, iy + ih - 1, iw - 1, 1, GRAY[0x99]),
    ]


def balloon(w, h):
    """Help balloon rows as spans (style/platinum/platinumstyle.cpp,
    drawBalloon): 1 px black top/left, 2 px right/bottom, rounded."""
    tl = [(0, 0), (3, 5), (2, 3), (1, 2), (1, 1), (0, 1)]
    bl = [(0, 0), (0, 0), (2, 4), (1, 2), (1, 1), (0, 1)]
    tr = [(0, 0), (6, 3), (4, 2), (3, 1), (2, 1), (2, 0), (1, 0)]
    br = [(0, 0), (0, 0), (6, 2), (4, 1), (3, 1), (2, 0), (2, 0)]
    x1, y1 = w - 1, h - 1
    out = []
    for y in range(h):
        t, b = y, y1 - y
        if t == 0:
            out.append((5, y, (x1 - 6) - 5 + 1, 1, BLACK))
            continue
        if b in (0, 1):
            a = 5 if b == 0 else 3
            out.append((a, y, (x1 - a) - a + 1, 1, BLACK))
            continue
        l0, l1 = tl[t] if t <= 5 else bl[b] if b <= 5 else (0, 0)
        r0, r1 = tr[t] if t <= 6 else br[b] if b <= 6 else (1, 0)
        out.append((l0, y, l1 - l0 + 1, 1, BLACK))
        out.append((x1 - r0, y, r0 - r1 + 1, 1, BLACK))
        if x1 - r0 - 1 >= l1 + 1:
            out.append((l1 + 1, y, (x1 - r0 - 1) - (l1 + 1) + 1, 1, WHITE))
    return out


def lavender_title(w, h):
    """An open menu title (menu-file-open.png "File"): #6666CC top row,
    #333399, #000088, then the bar's black bottom line (Plasma gives panel
    applets the panel's full height, so the title covers that row too); no
    side bevel."""
    return [(0, 0, w, h - 1, LAV), (0, 0, w, 1, LAV_LIGHT), (0, h - 2, w, 1, LAV_DARK), (0, h - 1, w, 1, BLACK)]


def field(focused):
    """A text field (style drawField): 1 px margin, sunken #888888 / white
    edge (or the 2 px #6666CC ring), black line, white inside."""
    def shapes(w, h):
        out = []
        if focused:
            out += [(1, 0, w - 2, 1, LAV_LIGHT), (1, h - 1, w - 2, 1, LAV_LIGHT), (0, 1, w, h - 2, LAV_LIGHT)]
        else:
            out += [(1, 1, w - 3, 1, GRAY[0x88]), (1, 1, 1, h - 3, GRAY[0x88]),
                    (w - 2, 2, 1, h - 3, WHITE), (2, h - 2, w - 3, 1, WHITE)]
        out += [(2, 2, w - 4, h - 4, BLACK), (3, 3, w - 6, h - 6, WHITE)]
        return out
    return shapes


def panel():
    """The menu bar (desktop-first-check.png, column x=700): white top row,
    #DDDDDD, #999999, black bottom row; 20 px. On a top panel Plasma drops
    the top, left and right borders (they touch the screen edges), so the
    white row is the center's first row and the center is exactly 18 rows:
    the panel must be 20 px thick to stay pixel exact."""
    s = Sheet()
    s.frame(None, (0, 0, 2, 0), lambda w, h: [(0, 0, w, h - 2, FACE), (0, 0, w, 1, WHITE),
                                              (0, h - 2, w, 1, GRAY[0x99]), (0, h - 1, w, 1, BLACK)],
            center=(2, 18))
    s.frame("mask", (0, 0, 2, 0), lambda w, h: [(0, 0, w, h, FACE)], center=(2, 18))
    # Plasma gives applets the full height anyway (an open title draws the
    # black row itself, see lavender_title).
    s.hints(None, (0, 0, 0, 0), insets=True)
    s.hints("thick", (0, 0, 0, 0))
    return s


def menubaritem():
    s = Sheet()
    s.frame("normal", (1, 1, 2, 1), lambda w, h: [])
    # Mac OS 9 highlights a title only while its menu is open; Plasma's
    # global menu draws hovered titles in the highlighted text color, so
    # hover gets the same bevel to stay readable.
    for prefix in ("hover", "pressed"):
        s.frame(prefix, (1, 1, 2, 1), lavender_title, center_shapes=[(0, 0, 2, 2, LAV)])
    # Label padding: Mac OS 9's ink sits 7 / 8 px inside the highlight.
    for prefix in ("normal", "hover", "pressed"):
        s.hints(prefix, (0, 6, 0, 6))
    return s


def dialog():
    """Popups (launcher menus, calendar, tray): the menu frame."""
    s = Sheet()
    s.frame(None, (2, 3, 3, 2), menu_frame)
    s.frame("mask", (2, 3, 3, 2), lambda w, h: [(0, 0, w - 1, h - 1, FACE)])
    s.hints(None, (4, 5, 5, 4), insets=True)
    return s


def tooltip():
    s = Sheet()
    s.frame(None, (6, 7, 7, 6), balloon)
    s.frame("mask", (6, 7, 7, 6), lambda w, h: [(1, 1, w - 3, h - 3, FACE)])
    s.hints(None, (10, 11, 11, 10), insets=True)
    return s


def viewitem():
    """List highlights: the menu highlight (#333399; the style's colors file
    makes the text white)."""
    s = Sheet()
    s.frame("normal", (1, 1, 1, 1), lambda w, h: [])
    for prefix in ("hover", "selected", "selected+hover"):
        s.frame(prefix, (1, 1, 1, 1), lambda w, h: [(0, 0, w, h, LAV)], center_shapes=[(0, 0, 2, 2, LAV)])
    s.flag("hint-tile-center")
    return s


def button():
    """Push buttons (measured 9-slices), tool buttons (Mac Help's small
    bevel)."""
    s = Sheet()
    k, normal = nineslice("PushNormal")
    _, pressed = nineslice("PushPressed")
    kt, tool = nineslice("ToolNormal")
    s.frame("normal", (k,) * 4, normal)
    s.frame("hover", (k,) * 4, normal)
    s.frame("pressed", (k,) * 4, pressed)
    s.frame("focus", (k,) * 4, normal)
    s.frame("toolbutton-hover", (kt,) * 4, tool)
    s.frame("toolbutton-focus", (kt,) * 4, tool)
    s.frame("toolbutton-pressed", (k,) * 4, pressed)
    for prefix in ("normal", "hover", "pressed", "focus"):
        s.hints(prefix, (3, 10, 3, 10))
    for prefix in ("toolbutton-hover", "toolbutton-focus", "toolbutton-pressed"):
        s.hints(prefix, (4, 4, 4, 4))
    return s


def lineedit():
    s = Sheet()
    s.frame("base", (3, 3, 3, 3), field(False))
    s.frame("hover", (3, 3, 3, 3), field(False))
    s.frame("focus", (3, 3, 3, 3), field(True))
    for prefix in ("base", "hover", "focus"):
        s.hints(prefix, (4, 5, 4, 5))
    return s


def frame():
    s = Sheet()

    def sunken(w, h):
        return [(0, 0, w - 1, 1, GRAY[0x88]), (0, 0, 1, h - 1, GRAY[0x88]), (w - 1, 1, 1, h - 1, WHITE),
                (1, h - 1, w - 1, 1, WHITE), (1, 1, w - 2, h - 2, BLACK), (2, 2, w - 4, h - 4, WHITE)]
    s.frame("sunken", (2, 2, 2, 2), sunken)
    s.frame("raised", (2, 3, 3, 2), menu_frame)
    s.frame("plain", (1, 1, 1, 1), lambda w, h: [(0, 0, w, h, GRAY[0x88]), (1, 1, w - 2, h - 2, FACE)])
    s.hints("sunken", (3, 3, 3, 3))
    s.hints("raised", (4, 5, 5, 4))
    s.hints("plain", (2, 2, 2, 2))
    return s


def tabbar():
    """The current tab, and an open panel applet (Plasma reuses the frame):
    #CCCCFF, the selection Lavender, with #9999FF / #6666CC top and bottom
    lines (derived: Mac OS 9 has no open-applet look; the menu title bevel
    would put the clock's black text on #333399)."""
    s = Sheet()
    for edge in ("north", "south", "west", "east"):
        s.frame(f"{edge}-active-tab", (1, 1, 1, 1),
                lambda w, h: [(0, 0, w, h, SELECTION), (0, 0, w, 1, "#9999ff"), (0, h - 1, w, 1, LAV_LIGHT)],
                center_shapes=[(0, 0, 2, 2, SELECTION)])
        s.hints(f"{edge}-active-tab", (2, 7, 2, 7))
    s.flag("hint-tile-center")
    return s


def plasmoidheading():
    """Popup header and footer: the etched #888888 / white separator."""
    s = Sheet()
    s.frame("header", (0, 0, 2, 0), lambda w, h: [(0, h - 2, w, 1, GRAY[0x88]), (0, h - 1, w, 1, WHITE)])
    s.frame("footer", (2, 0, 0, 0), lambda w, h: [(0, 0, w, 1, GRAY[0x88]), (0, 1, w, 1, WHITE)])
    s.hints(None, (4, 4, 4, 4))
    s.flag("hint-stretch-borders")
    return s


def colors():
    """Platinum.colors for Plasma only, with the menu highlight as the
    selection: #333399 behind white text (menu-view-checked.png)."""
    text = (ROOT / "colors/Platinum.colors").read_text()
    out, group = [], None
    for line in text.splitlines():
        if line.startswith("["):
            group = line.strip()
        if group == "[Colors:Selection]":
            if line.startswith("BackgroundNormal=") or line.startswith("BackgroundAlternate="):
                line = line.split("=")[0] + "=51,51,153"
            elif line.startswith("ForegroundNormal=") or line.startswith("ForegroundActive="):
                line = line.split("=")[0] + "=255,255,255"
        out.append(line)
    return "# Generated by plasma/make-plasma.py from colors/Platinum.colors: the\n" \
           "# selection is the menu highlight here (Plasma only).\n" + "\n".join(out) + "\n"


def main():
    out = Path(__file__).resolve().parent / "platinum"
    files = {
        "widgets/panel-background.svg": panel(),
        "widgets/menubaritem.svg": menubaritem(),
        "dialogs/background.svg": dialog(),
        "widgets/tooltip.svg": tooltip(),
        "widgets/viewitem.svg": viewitem(),
        "widgets/button.svg": button(),
        "widgets/lineedit.svg": lineedit(),
        "widgets/frame.svg": frame(),
        "widgets/tabbar.svg": tabbar(),
        "widgets/plasmoidheading.svg": plasmoidheading(),
    }
    for name, sheet in files.items():
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sheet.svg())
    metadata = {
        "KPlugin": {
            "Authors": [{"Name": "orlfman"}],
            "Category": "",
            "Description": "Platinum: a 20 px menu bar with Lavender open titles, menu-frame popups and help-balloon tooltips, from measured pixels. Anything it doesn't style comes from Breeze.",
            "EnabledByDefault": True,
            "Id": "platinum",
            "License": "BSD-2-Clause",
            "Name": "Platinum",
            "Version": "0.1",
        },
        "X-Plasma-API": "5.0",
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=4) + "\n")
    # Solid panels and popups: no blur, contrast or adaptive transparency.
    (out / "plasmarc").write_text("[AdaptiveTransparency]\nenabled=false\n\n[ContrastEffect]\nenabled=false\n\n[BlurBehindEffect]\nenabled=false\n")
    (out / "colors").write_text(colors())
    print(f"wrote {len(files)} SVGs, metadata.json, plasmarc and colors into {out}")


if __name__ == "__main__":
    main()
