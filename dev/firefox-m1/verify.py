#!/usr/bin/env python3
"""Verifier for Firefox Milestone 1 discovery & harness evidence.

Validates:
1. Static omni.ja MozJar extraction & required Firefox 160 chrome IDs.
2. Normal-launch screenshots (stock KWin SSD join, userChrome.css marker load,
   stylesheets=false negative control, cold two-row URL bar wrap, and cold
   legacy sidebar with sidebar.revamp=false).
3. Live Marionette report (DOM/Shadow-DOM inventory, GTK 3 Platinum inheritance,
   revamped sidebar & vertical tabs, two-row URL bar wrap + labels + narrow
   overflow + Customize Mode + keyboard focus, and built-in theme / dark-mode /
   forced-colors gating).
4. Host home isolation (no ~/.mozilla or ~/.config/mozilla leakage when absent
   before the run).

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import pathlib
import subprocess
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


def hex_px(im: Image.Image, x: int, y: int) -> str:
    r, g, b = im.getpixel((x, y))[:3]
    return f"#{r:02X}{g:02X}{b:02X}"


def count_color(im: Image.Image, target_rgb: tuple[int, int, int], box: tuple[int, int, int, int] | None = None) -> int:
    region = im.crop(box) if box else im
    rgb = region.convert("RGB")
    raw = rgb.tobytes()
    tr, tg, tb = target_rgb
    total = 0
    for i in range(0, len(raw), 3):
        if raw[i] == tr and raw[i + 1] == tg and raw[i + 2] == tb:
            total += 1
    return total


def find_platinum_titlebar_top(im: Image.Image, x_probe: int = 300) -> int | None:
    """Locate the top black row of the 22px Platinum KWin SSD title bar."""
    rgb = im.convert("RGB")
    h = rgb.height
    # Platinum active title bar vertical signature (22 rows):
    # +0 #000000, +1 #FFFFFF, +2 #CCCCCC, +3 #CCCCCC, +4..+15 alternating #FFFFFF/#777777,
    # +16..+19 #CCCCCC, +20 #999999, +21 #000000
    for y in range(0, min(200, h - 25)):
        if (
            hex_px(rgb, x_probe, y) == "#000000"
            and hex_px(rgb, x_probe, y + 1) == "#FFFFFF"
            and hex_px(rgb, x_probe, y + 2) == "#CCCCCC"
            and hex_px(rgb, x_probe, y + 20) == "#999999"
            and hex_px(rgb, x_probe, y + 21) == "#000000"
        ):
            return y
    return None


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <m1-report-dir> <shots-dir>", file=sys.stderr)
        return 2

    rdir = pathlib.Path(sys.argv[1])
    shots = pathlib.Path(sys.argv[2])
    s = Suite()

    # 1. Static omni.ja check (MozJar via unzip -p).
    proc = subprocess.run(
        ["unzip", "-p", "/usr/lib/firefox/browser/omni.ja", "chrome/browser/content/browser/browser.xhtml"],
        capture_output=True,
        text=True,
    )
    # Note: unzip exits 2 on MozJar header compensation while outputting full file.
    bx = proc.stdout
    s.check("omni.ja-browser-xhtml-readable", len(bx) > 200000 and proc.returncode in (0, 1, 2), f"bytes={len(bx)} rc={proc.returncode}")
    required_ids = [
        "navigator-toolbox",
        "toolbar-menubar",
        "TabsToolbar",
        "nav-bar",
        "nav-bar-customization-target",
        "urlbar-container",
        "urlbar",
        "PersonalToolbar",
        "PlacesToolbarItems",
        "sidebar-box",
        "sidebar-splitter",
        "statuspanel",
        "PanelUI-button",
    ]
    missing_ids = [cid for cid in required_ids if f'id="{cid}"' not in bx]
    s.check("omni.ja-required-chrome-ids", not missing_ids, f"checked={len(required_ids)} missing={missing_ids}")

    # 2. Cold normal-launch screenshot checks (without --marionette).
    stock_png = shots / "firefox-m1-stock.png"
    marker_png = shots / "firefox-m1-marker.png"
    neg_png = shots / "firefox-m1-neg-pref.png"
    wrap_cold_png = shots / "firefox-m1-wrap-cold.png"
    legacy_png = shots / "firefox-m1-sidebar-legacy.png"

    for p in (stock_png, marker_png, neg_png, wrap_cold_png, legacy_png):
        s.check(f"shot-exists-{p.stem}", p.is_file() and p.stat().st_size > 5000, str(p))

    if stock_png.is_file():
        im_stock = Image.open(stock_png).convert("RGB")
        ty = find_platinum_titlebar_top(im_stock, 220)
        s.check("stock-kwin-platinum-titlebar", ty is not None, f"top_y={ty}")
        if ty is not None:
            # Row ty+21 is KWin's bottom 1px #000000 border; ty+22 is the very first row of Firefox's #navigator-toolbox!
            join_rows = [hex_px(im_stock, 220, ty + 20 + k) for k in range(6)]
            s.check(
                "stock-kwin-toolbox-join-no-double-black",
                join_rows[0] == "#999999" and join_rows[1] == "#000000" and join_rows[2] != "#000000",
                f"rows[+20..+25]={join_rows}",
            )

    if marker_png.is_file() and neg_png.is_file() and stock_png.is_file():
        im_marker = Image.open(marker_png).convert("RGB")
        im_neg = Image.open(neg_png).convert("RGB")
        im_stock = Image.open(stock_png).convert("RGB")
        # Marker CSS paints #PersonalToolbar rgb(204, 204, 255) (#CCCCFF).
        marker_px = count_color(im_marker, (0xCC, 0xCC, 0xFF), (60, 40, 1180, 260))
        neg_px = count_color(im_neg, (0xCC, 0xCC, 0xFF), (60, 40, 1180, 260))
        stock_px = count_color(im_stock, (0xCC, 0xCC, 0xFF), (60, 40, 1180, 260))
        s.check("normal-launch-userchrome-marker-loaded", marker_px > 10000, f"#CCCCFF_px={marker_px}")
        s.check("negative-control-stylesheets-false", neg_px == 0 and stock_px == 0, f"neg_px={neg_px} stock_px={stock_px}")

    if wrap_cold_png.is_file():
        im_wc = Image.open(wrap_cold_png).convert("RGB")
        ty = find_platinum_titlebar_top(im_wc, 220)
        # Cold wrap CSS puts a #333399/#6666CC/#9999FF Lavender address band and #DEDEDE/#CCCCCC/#E8E6E8 pinstripe toolbar!
        lav_px = count_color(im_wc, (0x66, 0x66, 0xCC), (60, 40, 1180, 280))
        s.check("cold-launch-two-row-wrap-rendered", ty is not None and lav_px > 2000, f"top_y={ty} #6666CC_px={lav_px}")
        if ty is not None:
            # Cold wrap CSS sets 1px #FFFFFF top highlight on first toolbar row right below KWin's #000000 bottom line!
            r21 = hex_px(im_wc, 220, ty + 21)
            r22 = hex_px(im_wc, 220, ty + 22)
            s.check("cold-wrap-kwin-join-exact", r21 == "#000000" and r22 == "#FFFFFF", f"kwin_bottom={r21} toolbox_top={r22}")

    # 3. Live Marionette probe report checks.
    report_path = rdir / "probe-report.json"
    s.check("probe-report-exists", report_path.is_file(), str(report_path))
    if not report_path.is_file():
        print(f"\nSummary: {s.passed} passed, {s.failed} failed")
        return 1

    rep = json.loads(report_path.read_text(encoding="utf-8"))
    st = rep["startup"]
    s.check("firefox-version-recorded", st["appVersion"].startswith("160."), f"version={st['appVersion']} nova={st['novaEnabled']}")
    s.check("ssd-titlebar-active", st["inTitlebar"] == 0 and "customtitlebar" not in rep["dom_inventory"]["rootAttrs"], f"inTitlebar={st['inTitlebar']} rootAttrs={list(rep['dom_inventory']['rootAttrs'].keys())}")

    nodes = rep["dom_inventory"]["nodes"]
    for sel in (
        "#navigator-toolbox",
        "#TabsToolbar",
        "#nav-bar",
        "#nav-bar-customization-target",
        "#urlbar-container",
        "#urlbar",
        "#PersonalToolbar",
        "#sidebar-box",
        "sidebar-main",
        "#statuspanel",
        "#appMenu-popup",
        "#contentAreaContextMenu",
    ):
        s.check(f"live-dom-{sel}", nodes.get(sel, {}).get("exists") is True, f"tag={nodes.get(sel, {}).get('tag')} shadow={bool(nodes.get(sel, {}).get('shadow'))}")

    # Verify light DOM vs shadow DOM facts.
    sm_shadow = nodes["sidebar-main"]["shadow"]
    sr_parts = rep["sidebar_revamp"].get("shadowParts", [])
    s.check(
        "sidebar-main-is-shadow-dom",
        sm_shadow is not None and sm_shadow["mode"] == "open" and rep["sidebar_revamp"]["sidebarMainVisible"] is True,
        f"parts={sr_parts} buttons={len(rep['sidebar_revamp']['shadowButtons'])}",
    )
    s.check(
        "toolbars-and-urlbar-are-light-dom",
        all(nodes[k]["shadow"] is None for k in ("#navigator-toolbox", "#TabsToolbar", "#nav-bar", "#urlbar", "#PersonalToolbar")),
        "light DOM confirmed",
    )

    # Verify vertical tabs light-DOM slotting fact.
    vt = rep["vertical_tabs"]
    s.check(
        "vertical-tabs-light-dom-slotted",
        vt["tabsLightDom"] is True and vt["tabsOrient"] == "vertical" and vt["toolboxTabsHiddenAttr"] is True,
        f"parent={vt['tabsParentId']} orient={vt['tabsOrient']} rect={vt['tabsRect']}",
    )

    # Verify legacy sidebar (sidebar.revamp=false) still exists & is light DOM.
    ls = rep["legacy_sidebar"]
    s.check(
        "legacy-sidebar-exists-and-stylable",
        ls["sidebarMainHidden"] is True
        and ls["sidebarBoxVisible"] is True
        and ls["sidebarHeaderVisible"] is True
        and ls["sidebarHeaderLightDom"] is True
        and ls["innerHasSearchAndTree"] is True,
        f"url={ls['innerDocURL']} rect={ls['sidebarBoxRect']}",
    )

    # Verify naive flex-wrap false-overflow and right-side gap under #PanelUI-button vs clean row-2 band fix.
    nf = rep["naive_flex_wrap"]
    s.check(
        "naive-flex-wrap-causes-false-overflow-and-gap",
        nf["falseOverflowAtWide"] is True and nf["urlbarWidthGapPx"] >= 40,
        f"falseOverflow={nf['falseOverflowAtWide']} gapPx={nf['urlbarWidthGapPx']}",
    )

    # Verify two-row URL bar wrap, button labels, narrow overflow, customize mode, and keyboard focus.
    ww = rep["wrap_wide"]
    wn = rep["wrap_narrow"]
    s.check(
        "urlbar-row2-full-width-no-false-overflow",
        ww["urlbarBelowButtons"] is True
        and ww["urlbarFullWidth"] is True
        and ww["overflowingWide"] is False
        and ww["urlbarContainerRect"]["w"] >= 1000,
        f"urlbar={ww['urlbarContainerRect']} overflowingWide={ww['overflowingWide']}",
    )
    s.check(
        "narrow-resize-triggers-real-overflow",
        wn["navOverflowingAttr"] is True and wn["urlbarFullWidth"] is True and wn["overflowCount"] >= 1,
        f"innerW={wn['innerWidth']} overflowCount={wn['overflowCount']}",
    )
    non_empty_labels = [b["id"] for b in ww["labels"] if b["textRendered"]]
    s.check(
        "toolbarbutton-labels-render-under-icons",
        "back-button" in non_empty_labels and "home-button" in non_empty_labels,
        f"labeled={non_empty_labels}",
    )
    s.check(
        "wrapped-keyboard-focus-works",
        ww["urlFocused"] is True and ww["toolbarBtnFocused"] is True,
        f"shiftTabFocused={ww['activeAfterShiftTab']}",
    )
    s.check(
        "customize-mode-roundtrip",
        rep["customize_enter"]["customizingAttr"] is True
        and rep["customize_enter"]["paletteVisible"] is True
        and rep["customize_enter"]["urlPosInCustomize"] != "absolute"
        and rep["customize_exit"]["customizingCleared"] is True
        and rep["customize_exit"]["stillWrappedAfterExit"] is True
        and rep["customize_exit"]["overflowingAfterExit"] is False,
    )

    # Verify GTK 3 Platinum inheritance & menu popup capture.
    gi = rep["gtk_inheritance"]
    s.check(
        "gtk3-system-colors-resolved",
        bool(gi["resolvedColors"].get("-moz-headerbar")) and gi["menuPopup"]["state"] == "open",
        f"-moz-headerbar={gi['resolvedColors'].get('-moz-headerbar')} SelectedItem={gi['resolvedColors'].get('SelectedItem')}",
    )

    # Verify theme / dark-mode / forced-colors gating matrix.
    tm = {row["label"]: row for row in rep["theme_matrix"] if not row.get("missing")}
    s.check(
        "theme-gate-active-on-default-light",
        tm.get("default-theme@mozilla.org", {}).get("platinumGateActive") is True
        and tm.get("default-theme-restored", {}).get("platinumGateActive") is True,
    )
    for other in (
        "firefox-compact-light@mozilla.org",
        "firefox-compact-dark@mozilla.org",
        "firefox-alpenglow@mozilla.org",
        "default-theme+systemUsesDarkTheme=1",
        "default-theme+gtk-high-contrast",
    ):
        s.check(
            f"theme-gate-off-on-{other}",
            tm.get(other, {}).get("platinumGateActive") is False,
            f"row={tm.get(other)}",
        )

    # 4. Host home isolation check.
    leak_file = rdir / "host-leak-check.json"
    if leak_file.is_file():
        lk = json.loads(leak_file.read_text(encoding="utf-8"))
        s.check("host-home-untouched", lk["before"] == lk["after"], f"before={lk['before']} after={lk['after']}")

    total = s.passed + s.failed
    print(f"\nFirefox Milestone 1 summary: {s.passed}/{total} passed, {s.failed} failed")
    return 0 if s.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
