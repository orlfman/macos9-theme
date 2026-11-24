#!/usr/bin/env python3
"""Verifier for Firefox Milestone 5 (robustness: omni.ja selector checker,
version gate + negative controls, 150%/200% scaling crispness & clipping, and
keyboard focus everywhere).

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import pathlib
import sys
from PIL import Image, ImageChops


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


def count_rgb(im: Image.Image, rgb: tuple[int, int, int]) -> int:
    raw = im.convert("RGB").tobytes()
    tr, tg, tb = rgb
    return sum(1 for i in range(0, len(raw), 3) if raw[i] == tr and raw[i + 1] == tg and raw[i + 2] == tb)


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <m5-report-dir> <shots-dir>", file=sys.stderr)
        return 2

    rdir = pathlib.Path(sys.argv[1])
    shots = pathlib.Path(sys.argv[2])
    s = Suite()

    # 1. Static selector checker + negative controls (recorded by check-firefox-m5.sh).
    gate_path = rdir / "gates.json"
    s.check("gate-results-exist", gate_path.is_file(), str(gate_path))
    if gate_path.is_file():
        g = json.loads(gate_path.read_text(encoding="utf-8"))
        s.check("selector-checker-real-theme-pass", g["real_rc"] == 0, f"rc={g['real_rc']}")
        s.check("selector-checker-rejects-missing-id", g["neg_missing_id_rc"] == 1, f"rc={g['neg_missing_id_rc']}")
        s.check("selector-checker-rejects-missing-part", g["neg_missing_part_rc"] == 1, f"rc={g['neg_missing_part_rc']}")
        s.check("version-gate-warns-on-untested-major", g["neg_untested_ver_rc"] == 3, f"rc={g['neg_untested_ver_rc']}")
        s.check("version-gate-allow-flag-returns-0", g["neg_allow_ver_rc"] == 0, f"rc={g['neg_allow_ver_rc']}")

    # 2. Screenshots exist at 150%, 200%, and keyboard focus.
    kb_png = shots / "firefox-m5-keyboard-focus.png"
    s150_png = shots / "firefox-m5-scale-150.png"
    s200_png = shots / "firefox-m5-scale-200.png"
    for p in (kb_png, s150_png, s200_png):
        s.check(f"shot-exists-{p.stem}", p.is_file() and p.stat().st_size > 10000, str(p))

    # Verify 150% and 200% compositor captures keep full 2400x1600 physical output
    # and render crisp Deep Lavender (#1B1B52 full-width top row + #7A7AE0 specular
    # highlight behind "Address:") chrome.
    for pct, p in [("150", s150_png), ("200", s200_png)]:
        if p.is_file():
            im = Image.open(p)
            deep_px = count_rgb(im, (0x1B, 0x1B, 0x52))
            spec_px = count_rgb(im, (0x7A, 0x7A, 0xE0))
            s.check(
                f"scale-{pct}-compositor-output-and-lavender-band",
                im.size == (2400, 1600) and deep_px > 2000 and spec_px > 200,
                f"size={im.size} #1B1B52_px={deep_px} #7A7AE0_px={spec_px}",
            )

    # 3. Live Marionette report: keyboard focus everywhere + 100%/150%/200% metrics.
    rep_path = rdir / "m5-report.json"
    s.check("m5-report-exists", rep_path.is_file(), str(rep_path))
    if rep_path.is_file():
        rep = json.loads(rep_path.read_text(encoding="utf-8"))
        s.check("rtl-address-label-at-inline-start", rep["rtl"] == {
            "goOnLeft": True, "goHit": True, "rightPadding": "68px", "labelRight": "0px", "separator": "1px"}, str(rep["rtl"]))
        kb = rep["keyboard_focus"]
        width, height = map(round, kb["homeSize"])
        control = rdir / "home-without-focus.png"
        painted = False
        if kb_png.is_file() and control.is_file():
            focused = Image.open(kb_png).convert("RGB")
            unfocused = Image.open(control).convert("RGB")
            # Wayland does not expose the window's compositor origin. Locate
            # the changed pixels in the capture instead of guessing an offset.
            box = ImageChops.difference(focused, unfocused).getbbox()
            if box:
                on, off = focused.crop(box), unfocused.crop(box)
                gained = Image.new("L", on.size)
                lavender = (102, 102, 204)
                a, b = on.load(), off.load()
                gained.putdata([int(a[x, y] == lavender and b[x, y] != lavender)
                                for y in range(on.height) for x in range(on.width)])
                edges = gained.getbbox()
                if edges:
                    ring = gained.crop(edges)
                    expected = Image.new("L", (width, height), 1)
                    expected.paste(0, (2, 2, width - 2, height - 2))
                    painted = ring.size == expected.size and ring.tobytes() == expected.tobytes()
        s.check("home-focus-ring-painted", painted)
        s.check("kb-shift-tab-navigates-toolbar", kb["shiftTabInNavBar"] is True)
        for key in (
            "urlbar",
            "toolbarButton",
            "bookmarkItem",
            "horizontalTab",
            "verticalTab",
            "findbarInput",
            "newTabButton",
            "findbarButton",
        ):
            item = kb.get(key, {})
            s.check(
                f"kb-focus-ring-{key}",
                item.get("width") == "2px" and item.get("color") == "rgb(102, 102, 204)",
                str(item),
            )

        for pct, exp_dpr, exp_kscreen in [("100", 1.0, None), ("150", 1.5, "Scale: 1.5"), ("200", 2.0, "Scale: 2")]:
            sc = rep["scales"][pct]
            m = sc["metrics"]
            if exp_kscreen:
                s.check(f"scale-{pct}-kscreen-reported", exp_kscreen in sc["kscreen"], exp_kscreen)
            s.check(
                f"scale-{pct}-firefox-dpr",
                abs(float(m["dpr"]) - exp_dpr) < 0.01,
                f"dpr={m['dpr']} expected={exp_dpr}",
            )
            s.check(
                f"scale-{pct}-no-clipping-no-overlap-no-false-overflow",
                m["overflowing"] is False
                and m["urlCW"] == m["navW"]
                and m["urlBelowHome"] is True
                and m["urlCH"] == 26
                and m["favH"] == 24
                and m["statusH"] == "16px"
                and not m["clippedButtons"]
                and not m["clippedBookmarks"],
                f"navH={m['navH']} urlC={m['urlCW']}x{m['urlCH']} clippedBtn={m['clippedButtons']} clippedBm={m['clippedBookmarks']}",
            )

    leak_path = rdir / "host-leak.json"
    if leak_path.is_file():
        lk = json.loads(leak_path.read_text(encoding="utf-8"))
        s.check("host-home-untouched", lk["before"] == lk["after"], str(lk))

    total = s.passed + s.failed
    print(f"\nFirefox Milestone 5 summary: {s.passed}/{total} passed, {s.failed} failed")
    return 0 if s.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
