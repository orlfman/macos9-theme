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

    # Verify keyboard focus screenshot actually paints abundant #6666CC focus rings!
    if kb_png.is_file():
        im_kb = Image.open(kb_png)
        ring_px = count_rgb(im_kb, (0x66, 0x66, 0xCC))
        s.check("keyboard-focus-rings-visible-in-render", ring_px > 2000, f"#6666CC_px={ring_px}")

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
        kb = rep["keyboard_focus"]
        s.check("kb-shift-tab-navigates-toolbar", kb["shiftTabInNavBar"] is True)
        for key in ("urlbar", "toolbarButton", "bookmarkItem", "horizontalTab", "verticalTab", "findbarInput"):
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
