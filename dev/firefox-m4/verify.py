#!/usr/bin/env python3
"""Verifier for Firefox Milestone 4 full Platinum coverage.

Checks cold normal-launch renders (1A horizontal tabs + 5A permanent status
band + neutral activity indicator), live 1C vertical tabs switch, busy activity
indicator, Platinum menus/panels/urlbar popup, find & notification bars,
legacy sidebar, real inactive window flattening, Private window, popup window,
fullscreen status suppression, Customize Mode, theme/dark/HighContrast gating,
and host home isolation.

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
    return sum(1 for i in range(0, len(raw), 3) if raw[i] == tr and raw[i + 1] == tg and raw[i + 2] == tb)


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <m4-report-dir> <shots-dir>", file=sys.stderr)
        return 2

    rdir = pathlib.Path(sys.argv[1])
    shots = pathlib.Path(sys.argv[2])
    s = Suite()

    required_shots = [
        "firefox-m4-cold-1a.png",
        "firefox-m4-activity-busy.png",
        "firefox-m4-vertical-1c.png",
        "firefox-m4-menu-file.png",
        "firefox-m4-panel-appmenu.png",
        "firefox-m4-urlbar-popup.png",
        "firefox-m4-bars-sidebar.png",
        "firefox-m4-inactive-and-popup.png",
        "firefox-m4-private.png",
    ]
    for fname in required_shots:
        p = shots / fname
        s.check(f"shot-exists-{p.stem}", p.is_file() and p.stat().st_size > 5000, str(p))

    # Cold normal-launch pixel checks on 1A horizontal tabs + 5A permanent 16 px status band.
    cold_p = shots / "firefox-m4-cold-1a.png"
    if cold_p.is_file():
        im = Image.open(cold_p).convert("RGB")
        # Active tab (#EEEEEE) and inactive tabs (#CCCCCC) sit around y=160..186 below Favorites.
        ee_px = count_rgb(im, (0xEE, 0xEE, 0xEE), (80, 158, 420, 186))
        cc_px = count_rgb(im, (0xCC, 0xCC, 0xCC), (260, 158, 760, 186))
        s.check("cold-1a-platinum-tabs-pixels", ee_px > 1200 and cc_px > 2000, f"active_#EEEEEE={ee_px} inactive_#CCCCCC={cc_px}")

        # Permanent 16 px status band near bottom of window (around y=785..805): check pinstripe rows #DEDEDE/#CCCCCC/#E8E6E8!
        band_de = count_rgb(im, (0xDE, 0xDE, 0xDE), (100, 770, 1180, 815))
        band_e8 = count_rgb(im, (0xE8, 0xE6, 0xE8), (100, 770, 1180, 815))
        s.check("cold-5a-permanent-status-band-pinstripe", band_de > 2000 and band_e8 > 2000, f"#DEDEDE={band_de} #E8E6E8={band_e8}")

    # Menu popup screenshot check: verify #333399 Lavender highlight and #DDDDDD Platinum menu body.
    menu_p = shots / "firefox-m4-menu-file.png"
    if menu_p.is_file():
        im_m = Image.open(menu_p).convert("RGB")
        m_hi = count_rgb(im_m, (0x33, 0x33, 0x99), (80, 80, 380, 420))
        m_bg = count_rgb(im_m, (0xDD, 0xDD, 0xDD), (80, 80, 380, 420))
        s.check("menu-file-platinum-pixels", m_hi > 2000 and m_bg > 20000, f"#333399={m_hi} #DDDDDD={m_bg}")

    rep_path = rdir / "m4-report.json"
    s.check("m4-report-exists", rep_path.is_file(), str(rep_path))
    if not rep_path.is_file():
        print(f"\nFirefox Milestone 4 summary: {s.passed}/{s.passed + s.failed} passed, {s.failed} failed")
        return 1

    rep = json.loads(rep_path.read_text(encoding="utf-8"))

    # 1A horizontal tabs & 5A status band
    t1a = rep["tabs_1a"]
    s.check(
        "tabs-1a-below-favs-and-colors",
        t1a["tabsBelowFavs"] is True
        and t1a["selBg"] == "rgb(238, 238, 238)"
        and t1a["inactBg"] == "rgb(204, 204, 204)"
        and t1a["pressedBg"] == "rgb(102, 102, 102)"
        and t1a["pressedLabel"] == "rgb(255, 255, 255)",
        str(t1a),
    )
    s.check("status-5a-permanent-16px", t1a["statusBandDisplay"] == "block" and t1a["statusBandHeight"] == "16px", f"{t1a['statusBandDisplay']} {t1a['statusBandHeight']}")

    # Neutral Platinum activity indicator (:has(.tabbrowser-tab[selected][busy]))
    act = rep["activity"]
    s.check(
        "activity-indicator-idle-and-busy",
        act["idleW"] == "24px"
        and act["idleBg"] == "rgb(238, 238, 238)"
        and act["busyBg"] == "rgb(51, 51, 153)"
        and "repeating-linear-gradient" in act["busyImg"],
        str(act),
    )

    # 1C live vertical tabs switch
    t1c = rep["tabs_1c"]
    s.check(
        "tabs-1c-live-vertical-switch",
        t1c["orient"] == "vertical"
        and t1c["tabsHiddenAttr"] is True
        and t1c["sidebarWidth"] >= 150
        and "repeating-linear-gradient" in t1c["sidebarContainerBgImg"]
        and t1c["selBg"] == "rgb(238, 238, 238)"
        and t1c["inactBg"] == "rgb(204, 204, 204)",
        str(t1c),
    )

    # Menus & panels & square urlbar popup
    mn = rep["menu"]
    s.check(
        "menu-platinum-frame-and-highlight",
        mn["popupState"] == "open"
        and mn["panelBg"] == "rgb(221, 221, 221)"
        and mn["panelBorderRadius"] == "0px"
        and mn["panelBorderColor"] == "rgb(0, 0, 0)"
        and mn["activeItemBg"] == "rgb(51, 51, 153)"
        and mn["activeItemColor"] == "rgb(255, 255, 255)",
        str(mn),
    )

    pn = rep["panel"]
    s.check(
        "appmenu-panel-platinum-frame",
        pn["state"] == "open" and pn["bg"] == "rgb(221, 221, 221)" and pn["radius"] == "0px" and pn["border"] == "rgb(0, 0, 0)",
        str(pn),
    )

    up = rep["url_popup"]
    s.check(
        "urlbar-popup-square-platinum",
        up["isOpen"] is True
        and up["viewRadius"] == "0px"
        and up["viewBorder"] == "rgb(0, 0, 0)"
        and up["viewBg"] == "rgb(255, 255, 255)"
        and up["selRowBg"] == "rgb(51, 51, 153)"
        and up["selRowColor"] == "rgb(255, 255, 255)",
        str(up),
    )

    # Find bar, notification bar, legacy sidebar
    br = rep["bars"]
    s.check(
        "findbar-platinum",
        br["findbarHidden"] is False
        and br["findbarBg"] == "rgb(221, 221, 221)"
        and br["findFieldBg"] == "rgb(255, 255, 255)"
        and br["findFieldBorder"] == "rgb(0, 0, 0)"
        and br["findFieldRadius"] == "0px",
        str(br),
    )
    s.check(
        "notification-and-sidebar-platinum",
        br["notifVisible"] is True
        and br["notifBg"] == "rgb(238, 238, 238)"
        and "repeating-linear-gradient" in br["sidebarHeaderBgImg"],
        f"notif={br['notifBg']} sidebarHeader={br['sidebarHeaderBgImg'][:40]}",
    )

    # Real inactive window flattening + popup window
    ip = rep["inactive_and_popup"]
    s.check(
        "inactive-window-flattens-and-clears-focus",
        ip["mainInactive"] is True
        and ip["inactiveNavBgImg"] == "none"
        and ip["inactiveNavBg"] == "rgb(221, 221, 221)"
        and ip["inactiveUrlCBg"] == "rgb(142, 142, 184)"
        and ip["inactiveUrlOutline"] == "none"
        and ip["inactiveHomeColor"] == "rgb(119, 119, 119)",
        str(ip),
    )
    s.check(
        "popup-window-compact-no-status-band",
        ip["popupHasAttr"] is True and ip["popupNavHeight"] <= 44 and ip["popupStatusAfterContent"] == "none",
        f"popupAttr={ip['popupHasAttr']} navH={ip['popupNavHeight']} statusContent={ip['popupStatusAfterContent']}",
    )

    # Private window cleanly delegates to Firefox's built-in dark-purple Private theme,
    # fullscreen suppresses the permanent status band, and Customize Mode stays Platinum.
    pr = rep["private"]
    s.check(
        "private-window-delegates-cleanly-to-dark-private-theme",
        pr["privateAttr"] == "temporary"
        and pr["prefersDark"] is True
        and pr["privateUrlTube"] == "none"
        and pr["privateStatusContent"] == "none",
        str(pr),
    )

    fs = rep["fullscreen"]
    s.check(
        "fullscreen-hides-status-band-and-restores",
        fs["inFs"] is True and fs["statusAfterContentInFullscreen"] == "none" and fs["restoredStatus"] == "block",
        str(fs),
    )

    cu = rep["customize"]
    s.check(
        "customize-mode-platinum-and-clean-exit",
        cu["custBg"] == "rgb(221, 221, 221)" and cu["urlPosInCustomize"] == "static" and cu["cleared"] is True,
        str(cu),
    )

    # Theme / dark-mode / HighContrast gating matrix
    tm = {row["label"]: row["platinumActive"] for row in rep["theme_matrix"]}
    s.check("theme-gate-active-default-light", tm.get("default-theme@mozilla.org") is True and tm.get("default-theme-restored") is True, str(tm))
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
    print(f"\nFirefox Milestone 4 summary: {s.passed}/{total} passed, {s.failed} failed")
    return 0 if s.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
