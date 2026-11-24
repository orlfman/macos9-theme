#!/usr/bin/env python3
"""Verifier for Firefox Milestone 3 (the three IE5-inspired Platinum top bands).

Performs exact whole-pixel sampling on the cold normal-launch render
(firefox-m3-cold.png, zero --marionette) plus state verification on hover,
pressed, urlbar focus/selection, urlbar dropdown, overflow, Customize Mode,
and theme/dark/HighContrast gating.

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import pathlib
import sys
from PIL import Image


class Suite:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, cond: bool, detail: str = "") -> None:
        if cond:
            self.passed += 1
            print(f"PASS  {name}" + (f" ({detail})" if detail else ""))
        else:
            self.failed += 1
            print(f"FAIL  {name}" + (f" ({detail})" if detail else ""))


def hx(im: Image.Image, x: int, y: int) -> str:
    r, g, b = im.getpixel((x, y))[:3]
    return f"#{r:02X}{g:02X}{b:02X}"


def count_rgb(im: Image.Image, rgb: tuple[int, int, int], box: tuple[int, int, int, int]) -> int:
    raw = im.crop(box).convert("RGB").tobytes()
    tr, tg, tb = rgb
    n = 0
    for i in range(0, len(raw), 3):
        if raw[i] == tr and raw[i + 1] == tg and raw[i + 2] == tb:
            n += 1
    return n


def find_titlebar_top(im: Image.Image, x: int = 220) -> int | None:
    for y in range(0, min(200, im.height - 30)):
        if (
            hx(im, x, y) == "#000000"
            and hx(im, x, y + 1) == "#FFFFFF"
            and hx(im, x, y + 2) == "#CCCCCC"
            and hx(im, x, y + 20) == "#999999"
            and hx(im, x, y + 21) == "#000000"
        ):
            return y
    return None


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <m3-report-dir> <shots-dir>", file=sys.stderr)
        return 2

    rdir = pathlib.Path(sys.argv[1])
    shots = pathlib.Path(sys.argv[2])
    s = Suite()

    cold_png = shots / "firefox-m3-cold.png"
    hover_png = shots / "firefox-m3-btn-hover.png"
    pressed_png = shots / "firefox-m3-btn-pressed.png"
    focused_png = shots / "firefox-m3-urlbar-focused.png"
    open_png = shots / "firefox-m3-urlbar-open.png"

    for p in (cold_png, hover_png, pressed_png, focused_png, open_png):
        s.check(f"shot-exists-{p.stem}", p.is_file() and p.stat().st_size > 5000, str(p))

    # 1. Exact whole-pixel row sampling on cold normal-launch screenshot (no --marionette).
    if cold_png.is_file():
        im = Image.open(cold_png).convert("RGB")
        ty = find_titlebar_top(im, 220)
        s.check("cold-kwin-titlebar-found", ty is not None, f"top_y={ty}")
        if ty is not None:
            # Window client top starts at y0 = ty + 22 (immediately below KWin's #000000 row ty+21).
            y0 = ty + 22
            # Sample x = 600 (clean unobstructed pinstripe column between left & right toolbar button groups).
            col_x = 600
            # Band 1: Toolbar (42 px: y0 = #FFFFFF, y0+1..y0+40 = 3-row pinstripe #DEDEDE/#CCCCCC/#E8E6E8, y0+41 = #ADADAD)
            s.check(
                "band1-kwin-join-and-top-highlight",
                hx(im, col_x, y0 - 1) == "#000000" and hx(im, col_x, y0) == "#FFFFFF",
                f"kwin_bottom={hx(im, col_x, y0 - 1)} toolbar_top={hx(im, col_x, y0)}",
            )
            pinstripe_12 = [hx(im, col_x, y0 + 1 + i) for i in range(12)]
            expected_cycle = ["#DEDEDE", "#CCCCCC", "#E8E6E8"] * 4
            s.check("band1-toolbar-pinstripe-whole-pixel", pinstripe_12 == expected_cycle, f"rows={pinstripe_12[:6]}")

            # Locate the Deep Lavender address tube top (#ADADAD followed by #1B1B52) at x = 86 (left of "Address:" text).
            tube_x = 84
            tube_top = None
            for yy in range(y0 + 35, y0 + 55):
                if hx(im, tube_x, yy) == "#ADADAD" and hx(im, tube_x, yy + 1) == "#1B1B52":
                    tube_top = yy
                    break
            s.check("band2-address-tube-top-border", tube_top is not None, f"tube_top={tube_top} toolbar_h={tube_top - y0 if tube_top else None}")
            if tube_top is not None:
                # Sample full 26-row address band on the clean left margin x=84!
                tube_rows = [hx(im, tube_x, tube_top + i) for i in range(26)]
                expected_tube = [
                    "#ADADAD",
                    "#1B1B52", "#212162", "#282874", "#2E2E85", "#333399", "#3F3FA5",
                    "#4C4CB2", "#5959BF", "#6666CC", "#7070D6", "#7A7AE0", "#7A7AE0",
                    "#7A7AE0", "#7A7AE0", "#7070D6", "#6666CC", "#5959BF", "#4C4CB2",
                    "#3F3FA5", "#333399", "#2B2B7E", "#222266", "#1A1A4F", "#111138",
                    "#000000",
                ]
                s.check("band2-deep-lavender-tube-26-rows-exact", tube_rows == expected_tube, f"matched={sum(a==b for a,b in zip(tube_rows, expected_tube))}/26")

                # Check white address field framed by 1 px #000000 centered inside the 24 px tube (x=950, empty white area).
                field_col = [hx(im, 950, tube_top + 1 + i) for i in range(24)]
                s.check(
                    "band2-address-field-frame-and-white-fill",
                    field_col[2] == "#000000" and field_col[21] == "#000000" and field_col[10] == "#FFFFFF" and field_col[1] == "#212162",
                    f"top_margin={field_col[:4]} bot_margin={field_col[20:]}",
                )

                # Band 3: Favorites bar starts immediately below tube bottom (#000000 at tube_top+25) -> fav_top = tube_top+26.
                fav_top = tube_top + 26
                fav_col = [hx(im, 700, fav_top + i) for i in range(24)]
                s.check(
                    "band3-favorites-bar-24-rows-pinstripe",
                    fav_col[0] == "#FFFFFF"
                    and fav_col[1:7] == ["#DEDEDE", "#CCCCCC", "#E8E6E8", "#DEDEDE", "#CCCCCC", "#E8E6E8"]
                    and fav_col[23] == "#ADADAD",
                    f"top={fav_col[:4]} bot={fav_col[21:]}",
                )

            # Check enabled Lavender icon pixels (#333399) and desaturated Lavender disabled icon strokes on Back/Forward.
            lav_icon_px = count_rgb(im, (0x33, 0x33, 0x99), (80, y0, 1180, y0 + 40))
            dis_crop = im.crop((130, y0 + 2, 245, y0 + 24)).convert("RGB")
            dis_raw = dis_crop.tobytes()
            dis_lav_px = sum(
                1 for i in range(0, len(dis_raw), 3)
                if dis_raw[i + 2] >= dis_raw[i] + 10 and dis_raw[i + 2] >= dis_raw[i + 1] + 10 and dis_raw[i] >= 0x90
            )
            s.check("band1-lavender-enabled-and-disabled-icons", lav_icon_px > 200 and dis_lav_px > 20, f"enabled_#333399={lav_icon_px} disabled_lav_px={dis_lav_px}")

    # 2. Rendered button hover & pressed pixel verification.
    if hover_png.is_file():
        im_h = Image.open(hover_png).convert("RGB")
        # Hovering Home button + bookmark renders #666666 top/left and #333333 bottom/right ToolNormal border.
        tl_px = count_rgb(im_h, (0x66, 0x66, 0x66), (80, 60, 420, 170))
        br_px = count_rgb(im_h, (0x33, 0x33, 0x33), (80, 60, 420, 170))
        s.check("state-hover-toolnormal-bevel-pixels", tl_px > 80 and br_px > 80, f"#666666={tl_px} #333333={br_px}")

    if pressed_png.is_file():
        im_p = Image.open(pressed_png).convert("RGB")
        # Pressing Home button + bookmark fills interior with #666666 (> 1500 px on 56x38 button + bookmark).
        pressed_fill_px = count_rgb(im_p, (0x66, 0x66, 0x66), (80, 60, 420, 170))
        s.check("state-pressed-dark-platinum-fill-pixels", pressed_fill_px > 1500, f"#666666_px={pressed_fill_px}")

    # 3. Rendered URL bar focus ring (#6666CC, 2 px outside black frame) + text selection (#CCCCFF).
    if focused_png.is_file():
        im_f = Image.open(focused_png).convert("RGB")
        ty = find_titlebar_top(im_f, 220)
        if ty is not None:
            ring_px = count_rgb(im_f, (0x66, 0x66, 0xCC), (140, ty + 62, 1190, ty + 90))
            sel_px = count_rgb(im_f, (0xCC, 0xCC, 0xFF), (140, ty + 64, 1190, ty + 88))
            s.check("urlbar-focused-ring-and-selection-pixels", ring_px > 3500 and sel_px > 1500, f"#6666CC_ring={ring_px} #CCCCFF_sel={sel_px}")

    # 3B. Verify open urlbar autocomplete popup paints opaque white + #333399 selected row (not transparent over page!).
    if open_png.is_file():
        im_o = Image.open(open_png).convert("RGB")
        ty = find_titlebar_top(im_o, 220)
        if ty is not None:
            # Sample right over the Favorites/Tabs/heading region covered by .urlbarView: must have #333399 selected row + #FFFFFF background!
            sel_row_px = count_rgb(im_o, (0x33, 0x33, 0x99), (150, ty + 88, 1160, ty + 160))
            bg_white_px = count_rgb(im_o, (0xFF, 0xFF, 0xFF), (150, ty + 95, 1160, ty + 200))
            s.check("urlbar-open-opaque-platinum-popup", sel_row_px > 5000 and bg_white_px > 20000, f"#333399_row={sel_row_px} #FFFFFF_bg={bg_white_px}")

    # 4. Interactive Marionette JSON report checks.
    rep_path = rdir / "m3-report.json"
    s.check("m3-report-exists", rep_path.is_file(), str(rep_path))
    if rep_path.is_file():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        g = rep["geom"]
        s.check("geom-button-pitch-56px", g["homeRect"]["w"] >= 56 and g["backRect"]["w"] >= 56, f"home={g['homeRect']} back={g['backRect']}")
        s.check(
            "geom-disabled-and-enabled-label-colors",
            g["backDisabled"]
            and g["backColor"] == "rgb(119, 119, 119)"
            and g["backFill"] == "rgb(153, 153, 204)"
            and g["homeColor"] == "rgb(17, 17, 17)"
            and g["homeFill"] == "rgb(51, 51, 153)",
            f"back={g['backColor']}/{g['backFill']} home={g['homeColor']}/{g['homeFill']}",
        )
        s.check("geom-address-band-26px-full-width", g["urlContainerRect"]["h"] == 26 and g["urlContainerRect"]["w"] == g["navRect"]["w"] and g["overflowingWide"] is False, f"urlC={g['urlContainerRect']} nav={g['navRect']}")
        s.check("go-click-navigates-to-entered-address", rep["go_navigated"])
        gb = g.get("goButton") or {}
        s.check(
            "geom-address-band-go-button-visible",
            gb.get("hit") is True and gb.get("display") == "block"
            and gb.get("w") == 48
            and gb.get("h") == 24
            and gb.get("x", 0) >= g["urlbarRect"]["x"] + g["urlbarRect"]["w"],
            str(gb),
        )
        s.check("geom-favorites-bar-24px", g["favRect"]["h"] == 24, f"fav={g['favRect']}")

        hv = rep["hover"]
        pr = rep["pressed"]
        s.check("computed-hover-bevel", hv["homeHoverBg"] == "rgb(204, 204, 204)" and hv["homeHoverBorderTop"] == "rgb(102, 102, 102)" and hv["homeHoverBorderBottom"] == "rgb(51, 51, 51)", str(hv))
        s.check("computed-pressed-button", pr["homePressedBg"] == "rgb(102, 102, 102)" and pr["homePressedColor"] == "rgb(255, 255, 255)", str(pr))

        uf = rep["url_focus"]
        s.check(
            "computed-urlbar-focus-and-selection",
            uf["hasFocusedAttr"] is True
            and uf["bgOutlineWidth"] == "2px"
            and uf["bgOutlineColor"] == "rgb(102, 102, 204)"
            and uf["selectionBg"] == "rgb(204, 204, 255)"
            and uf["selectionEnd"] > uf["selectionStart"],
            str(uf),
        )

        uo = rep["url_open"]
        s.check(
            "urlbar-autocomplete-dropdown-visible",
            uo["goHit"] is True and uo["isOpen"] is True and uo["viewRect"] is not None and uo["viewRect"]["h"] > 40 and uo["viewRect"]["w"] >= 900,
            str(uo),
        )

        nc = rep["narrow_and_customize"]
        s.check("narrow-overflow-and-customize-roundtrip", nc["narrowOverflow"] is True and nc["narrowUrlW"] == 520 and nc["urlPosInCust"] == "static" and nc["urlPosAfterCust"] == "absolute" and nc["overflowAfterCust"] is False, str(nc))

        tm = {r["label"]: r["platinumActive"] for r in rep["theme_matrix"]}
        s.check("theme-gate-active-only-on-default-light", tm.get("default-theme@mozilla.org") is True and tm.get("default-theme-restored") is True, str(tm))
        for off in (
            "firefox-compact-light@mozilla.org",
            "firefox-compact-dark@mozilla.org",
            "firefox-alpenglow@mozilla.org",
            "default-theme+dark",
            "default-theme+high-contrast",
        ):
            s.check(f"theme-gate-off-{off}", tm.get(off) is False, f"{off}={tm.get(off)}")

    leak_path = rdir / "host-leak.json"
    if leak_path.is_file():
        lk = json.loads(leak_path.read_text(encoding="utf-8"))
        s.check("host-home-untouched", lk["before"] == lk["after"], str(lk))

    total = s.passed + s.failed
    print(f"\nFirefox Milestone 3 summary: {s.passed}/{total} passed, {s.failed} failed")
    return 0 if s.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
