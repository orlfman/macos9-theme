#!/usr/bin/env python3
"""Verify Milestone 3 Batch 2 GTK 3 Platinum checks:
  - 45 fixed-geometry 1x reference crops at tolerance 0 (Smart Scrolling
    scrollbars, sliders + ticks, determinate + barber-pole progress bars,
    notebook tab rows + pane, modal dialog frame, Help Balloon tooltip outline)
  - Natural-size gallery checks (zero clipping, real classic scrollbar stepper
    clicks, keyboard focus on scale, mapped tooltip, native GtkMessageDialog
    default button & action-area button spacing, backdrop muting)
  - Separate overlay scrolling probe (compact indicator, no 16px steppers)
  - Client-side HeaderBar probe (active pinstripes + 13x13 Mac boxes + app
    button, flat #DDDDDD backdrop, narrow width, maximized state)
  - Real GTK 3 application (meld) D-Bus/KWin window + Platinum chrome check

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

PROJECT = Path(__file__).resolve().parent.parent.parent
COMPARE = PROJECT / "tools" / "compare.py"


def parse_coords(path: Path) -> tuple[dict[str, str], dict[str, tuple[tuple[int, int, int, int], tuple[int, int]]]]:
    hdr: dict[str, str] = {}
    items: dict[str, tuple[tuple[int, int, int, int], tuple[int, int]]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            for tok in line[1:].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    hdr[k] = v
            continue
        m = re.match(r"^(\S+)\s+(-?\d+),(-?\d+),(\d+),(\d+)\s+alloc=-?\d+,-?\d+,\d+,\d+\s+nat=(\d+)x(\d+)$", line)
        if m:
            items[m.group(1)] = (
                (int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))),
                (int(m.group(6)), int(m.group(7))),
            )
    return hdr, items


def count_color(im: Image.Image, box: tuple[int, int, int, int], target: tuple[int, int, int]) -> int:
    x, y, w, h = box
    crop = im.crop((max(0, x), max(0, y), min(im.width, x + w), min(im.height, y + h)))
    pixels = crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata()
    return sum(1 for p in pixels if p == target)


def platinum_button_count(window: Image.Image) -> int:
    asset = PROJECT / "gtk" / "Platinum" / "gtk-3.0" / "assets" / "push-normal.png"
    with Image.open(asset) as image:
        corner = image.convert("RGBA").crop((0, 0, 4, 4)).load()
        samples = [(x, y, corner[x, y][:3]) for y in range(4) for x in range(4) if corner[x, y][3] == 255]
    pixels = window.load()
    return sum(
        all(pixels[x + dx, y + dy] == color for dx, dy, color in samples)
        for y in range(window.height // 4) for x in range(window.width - 3)
    )


def verify_meld(ev: Path, mode: str) -> tuple[bool, str]:
    log = ev / "meld.log"
    if not log.is_file():
        return False, "missing meld.log"
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    if [line for line in lines if line.startswith("MELD_STATUS=")] != ["MELD_STATUS=PASS"]:
        return False, "missing or failed Meld status"
    if any(re.search(r"Theme parsing error|CSS_(?:LOG|LOAD|PARSE)_ERROR", line, re.I) for line in lines):
        return False, "Meld reported a CSS error"
    pids = [line.removeprefix("MELD_PID=") for line in lines if line.startswith("MELD_PID=")]
    owners = [line.removeprefix("MELD_OWNER=u ") for line in lines if line.startswith("MELD_OWNER=")]
    if len(pids) != 1 or not pids[0].isdigit() or owners != pids:
        return False, "Meld process and D-Bus owner do not match"
    if mode == "broadway":
        return True, f"process and D-Bus owner={pids[0]} css_errors=0"

    pattern = (
        rf"MELD_WINDOW pid={pids[0]} app=org\.gnome\.Meld "
        r"x=(-?\d+) y=(-?\d+) width=(\d+) height=(\d+)"
    )
    windows = [row for line in lines if (row := re.fullmatch(pattern, line))]
    if len(windows) != 1:
        return False, "missing active KWin window for Meld PID"
    x, y, w, h = map(int, windows[0].groups())
    output_path, active_path = ev / "meld-plasma.png", ev / "meld-active.png"
    if not output_path.is_file() or not active_path.is_file():
        return False, "missing desktop or active window capture"
    with Image.open(output_path) as output, Image.open(active_path) as active:
        if output.size != (1280, 900) or min(x, y) < 0 or x + w > output.width or y + h > output.height:
            return False, f"unexpected output dimensions or window bounds ({x},{y},{w},{h})"
        if w < 400 or h < 300 or not (0 <= active.width - w <= 160 and 0 <= active.height - h <= 160):
            return False, "active capture does not fit KWin window geometry"
        left, top, right, bottom = w // 16, h // 8, w - w // 16, h * 7 // 8
        ax, ay = (active.width - w) // 2, (active.height - h) // 2
        crop = output.convert("RGB").crop((x + left, y + top, x + right, y + bottom))
        active_rgb = active.convert("RGB")
        window = active_rgb.crop((ax + left, ay + top, ax + right, ay + bottom))
        difference = max(ImageStat.Stat(ImageChops.difference(crop, window)).mean)
        varied = max(ImageStat.Stat(window).stddev) > 5
        buttons = platinum_button_count(active_rgb)
        # Verify Meld's CSD header bar renders Platinum #CCCCCC + pinstripes (not unstyled black)
        top_band = (ax + 4, ay + 1, w - 8, 36)
        hb_ccc = count_color(active_rgb, top_band, (0xCC, 0xCC, 0xCC))
        hb_stripe = count_color(active_rgb, top_band, (0x77, 0x77, 0x77))
    return varied and difference <= 1 and buttons >= 2 and hb_ccc >= 500 and hb_stripe >= 200, (
        f"pid={pids[0]} active={w}x{h} crop_err={difference:.2f} buttons={buttons} hb_ccc={hb_ccc} hb_stripe={hb_stripe}"
    )


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[3] not in {"broadway", "plasma"}:
        print("usage: verify.py <evidence_dir> <shots_dir> <broadway|plasma>", file=sys.stderr)
        return 2

    ev = Path(sys.argv[1])
    shots = Path(sys.argv[2])
    mode = sys.argv[3]
    shots.mkdir(parents=True, exist_ok=True)
    expected_backend = "GdkBroadwayDisplay" if mode == "broadway" else "GdkWaylandDisplay"

    chrome_png = ev / "m3b2-chrome.png"
    chrome_txt = ev / "m3b2-chrome.txt"
    gal_act = ev / "m3b2-gallery-active.png"
    gal_foc = ev / "m3b2-gallery-focus.png"
    gal_bak = ev / "m3b2-gallery-backdrop.png"
    gal_dlg = ev / "m3b2-dialog.png"
    gal_tip = ev / "m3b2-tooltip.png"
    gal_txt = ev / "m3b2-gallery.txt"
    ovl_png = ev / "m3b2-overlay.png"
    ovl_txt = ev / "m3b2-overlay.txt"
    csd_act = ev / "m3b2-csd-active.png"
    csd_bak = ev / "m3b2-csd-backdrop.png"
    csd_nar = ev / "m3b2-csd-narrow.png"
    csd_max = ev / "m3b2-csd-max.png"
    csd_txt = ev / "m3b2-csd.txt"

    failed = 0
    total = 0

    def record(ok: bool, name: str, detail: str) -> None:
        nonlocal failed, total
        total += 1
        print(f"{'ok  ' if ok else 'FAIL'}    {name:<36} {detail}")
        if not ok:
            failed += 1

    ch_hdr, ch_items = parse_coords(chrome_txt)
    gl_hdr, gl_items = parse_coords(gal_txt)
    ov_hdr, _ = parse_coords(ovl_txt)
    cs_hdr, _ = parse_coords(csd_txt)

    session_log = ev / "session.log"
    sess_txt = session_log.read_text(encoding="utf-8", errors="replace") if session_log.is_file() else ""
    gadget_errs = (
        sess_txt.count("Drawing a gadget with negative dimensions")
        + sess_txt.count("smaller than min-size")
        + sess_txt.count("_gtk_css_image_get_")
    )

    record(
        ch_hdr.get("theme") == "Platinum"
        and ch_hdr.get("backend") == expected_backend
        and ch_hdr.get("css_errors") == "0"
        and ch_hdr.get("png_ok") == "1"
        and ch_hdr.get("scale") == "1"
        and session_log.is_file()
        and gadget_errs == 0
        and "Gtk-CRITICAL" not in sess_txt,
        "chrome-theme-and-css",
        f"theme={ch_hdr.get('theme')} backend={ch_hdr.get('backend')} css_errors={ch_hdr.get('css_errors')} gadget_errs={gadget_errs}",
    )

    def cmp_crop(name: str, ref_img: str, rx: int, ry: int, ox: int, oy: int, w: int, h: int) -> None:
        out_cmp = shots / f"cmp-gtk3-m3b2-{name}.png"
        p = subprocess.run(
            [
                sys.executable,
                "-I",
                str(COMPARE),
                "diff",
                f"{PROJECT / 'reference' / ref_img}@{rx},{ry},{w},{h}",
                f"{chrome_png}@{ox},{oy},{w},{h}",
                "--tolerance",
                "0",
                "--zoom",
                "6",
                "--out",
                str(out_cmp),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        diff_line = ""
        for ln in p.stdout.splitlines():
            if ln.startswith("differing"):
                diff_line = " ".join(ln.split()[1:])
                break
        record(p.returncode == 0, f"ref-{name}", diff_line or p.stderr.strip())

    # 1. Scrollbars (check-style.sh lines 61-64; vbar-mid split outside 8-row Cairo 0.5px grip)
    vt_x, vt_y, _, _ = ch_items["vbar-top"][0]
    vm_x, vm_y, _, _ = ch_items["vbar-mid"][0]
    hb_x, hb_y, _, _ = ch_items["hbar"][0]
    cmp_crop("vbar-top", "scroll-vertical-inactive.png", 787, 249, vt_x, vt_y + 1, 16, 346)
    cmp_crop("vbar-mid-upper", "disclosure-triangles.png", 492, 175, vm_x, vm_y + 1, 16, 97)
    cmp_crop("vbar-mid-lower", "disclosure-triangles.png", 492, 175 + 107, vm_x, vm_y + 1 + 107, 16, 215)
    cmp_crop("hbar", "disclosure-triangles.png", 105, 496, hb_x + 1, hb_y, 388, 16)

    # 2. Sliders / Scales (check-style.sh lines 82-84)
    sl_x, sl_y, _, _ = ch_items["slider"][0]
    sp_x, sp_y, _, _ = ch_items["slider-pressed"][0]
    sd_x, sd_y, _, _ = ch_items["slider-disabled"][0]
    cmp_crop("slider", "controls-general-controls.png", 726, 438, sl_x, sl_y, 91, 23)
    cmp_crop("slider-pressed-thumb", "slider-pressed.png", 764, 438, sp_x + 38, sp_y, 15, 16)
    cmp_crop("slider-disabled", "controls-memory.png", 672, 483, sd_x, sd_y, 140, 16)

    # 3. Progress bars (check-style.sh lines 88-90)
    p55_x, p55_y, _, _ = ch_items["progress-55"][0]
    p0_x, p0_y, _, _ = ch_items["progress-0"][0]
    pb_x, pb_y, _, _ = ch_items["progress-busy"][0]
    cmp_crop("progress-55", "progress-determinate-55.png", 590, 276, p55_x, p55_y, 188, 14)
    cmp_crop("progress-0", "progress-copy-window.png", 590, 276, p0_x, p0_y, 188, 14)
    cmp_crop("progress-busy-stripes", "progress-indeterminate-a.png", 1077, 473, pb_x + 2, pb_y + 2, 60, 10)

    # At the leading edge of a reversed fill, the shadow runs into the
    # unfilled area. Sample the interior to exclude the trough's edge bevel.
    chrome = Image.open(chrome_png).convert("RGB")
    reverse_edge = [(v, v, v) for v in (187, 136, 85, 0)]
    for name, vertical in (("progress-reversed", False), ("progress-vertical-reversed", True)):
        x, y, w, h = ch_items[name][0]
        if vertical:
            line = [chrome.getpixel((x + w // 2, y + n)) for n in range(8, h - 8)]
        else:
            line = [chrome.getpixel((x + n, y + h // 2)) for n in range(8, w - 8)]
        record(
            any(line[i:i + len(reverse_edge)] == reverse_edge for i in range(len(line))),
            f"{name}-leading-shadow",
            "expected divider and three shadow tones before the fill",
        )

    vx, vy, _, _ = ch_items["progress-vertical-busy"][0]
    pattern_path = PROJECT / "gtk" / "Platinum" / "gtk-3.0" / "assets" / "progress-pulse-v.png"
    with Image.open(pattern_path) as pattern:
        tile = pattern.convert("RGB")
        rendered = chrome.crop((vx + 2, vy + 2, vx + 2 + tile.width, vy + 2 + tile.height))
    record(
        ImageChops.difference(rendered, tile).getbbox() is None,
        "progress-vertical-pulse-pattern",
        "first painted stripe tile matches the generated pattern",
    )

    # 4. Notebook tabs & pane (check-style.sh lines 98-126)
    tab_widths = (72, 101, 57, 74, 62, 71)

    def tabs_check(name: str, ref_img: str, rx: int, ry: int, ox: int, oy: int, s0: int | None = None, s1: int | None = None) -> None:
        ty = ry - 21
        oty = oy - 21
        cmp_crop(f"{name}-top", ref_img, rx + 2, ty, ox + 2, oty, 462, 6)
        if s0 is not None and s1 is not None:
            cmp_crop(f"{name}-bottom-a", ref_img, rx + 2, ty + 17, ox + 2, oty + 17, s0 - 2, 10)
            cmp_crop(f"{name}-bottom-b", ref_img, rx + s1, ty + 17, ox + s1, oty + 17, 464 - s1, 10)
        else:
            cmp_crop(f"{name}-bottom", ref_img, rx + 2, ty + 17, ox + 2, oty + 17, 462, 10)
        x = 5
        cmp_crop(f"{name}-sides-0", ref_img, rx + 2, ty + 6, ox + 2, oty + 6, 15, 11)
        for i in range(5):
            x += tab_widths[i]
            cmp_crop(f"{name}-sides-{i + 1}", ref_img, rx + x - 12, ty + 6, ox + x - 12, oty + 6, 24, 11)
        x += tab_widths[5]
        cmp_crop(f"{name}-sides-6", ref_img, rx + x - 12, ty + 6, ox + x - 12, oty + 6, 464 - x + 12, 11)

    pt_x, pt_y, pt_w, pt_h = ch_items["pane-themes"][0]
    pa_x, pa_y, _, _ = ch_items["pane-appearance"][0]
    po_x, po_y, _, _ = ch_items["pane-options"][0]
    tabs_check("tabs-themes", "appearance-1-themes.png", 469, 235, pt_x, pt_y)
    cmp_crop("tabs-pane-left", "appearance-1-themes.png", 469, 235, pt_x, pt_y, 4, 280)
    cmp_crop("tabs-pane-right", "appearance-1-themes.png", 931, 235, pt_x + 462, pt_y, 4, 280)
    cmp_crop("tabs-pane-bottom", "appearance-1-themes.png", 469, 511, pt_x, pt_y + 276, 466, 4)
    tabs_check("tabs-appearance", "appearance-2-appearance.png", 469, 235, pa_x, pa_y)
    tabs_check("tabs-options", "appearance-6-options.png", 469, 235, po_x, po_y)

    # 5. Modal dialog frame (check-style.sh lines 161-164)
    mf_x, mf_y, _, _ = ch_items["modal-frame"][0]
    cmp_crop("modal-frame-top", "dialog-modal-plain.png", 766, 194, mf_x, mf_y, 386, 4)
    cmp_crop("modal-frame-left", "dialog-modal-plain.png", 766, 194, mf_x, mf_y, 4, 189)
    cmp_crop("modal-frame-right", "dialog-modal-plain.png", 1149, 196, mf_x + 383, mf_y + 2, 4, 188)
    cmp_crop("modal-frame-bottom", "dialog-modal-plain.png", 768, 380, mf_x + 2, mf_y + 186, 385, 4)

    # 6. Tooltip Help Balloon outline (check-style.sh lines 223-240)
    bl_x, bl_y, _, _ = ch_items["balloon"][0]
    ref_bal = Image.open(PROJECT / "reference" / "help-balloon.png").convert("RGB")
    ours_chr = Image.open(chrome_png).convert("RGB")

    def bal_cls(p: tuple[int, int, int]) -> str:
        return "B" if p == (0, 0, 0) else "W" if p == (255, 255, 255) else "-"

    bal_n = bal_bad = 0
    for y in range(121):
        for x in range(160):
            if not (x < 10 or y < 10 or x >= 150 or y >= 111) or (x >= 130 and y < 14):
                continue
            bal_n += 1
            bal_bad += bal_cls(ref_bal.getpixel((1690 + x, 149 + y))) != bal_cls(ours_chr.getpixel((bl_x + x, bl_y + y)))
    record(bal_bad == 0, "ref-balloon-outline", f"{bal_bad} of {bal_n} px")

    # 7. Natural-size gallery, stepper clicks, focus, tooltip, dialog, and backdrop
    record(
        gl_hdr.get("theme") == "Platinum"
        and gl_hdr.get("backend") == expected_backend
        and gl_hdr.get("css_errors") == "0"
        and gl_hdr.get("scale") == "1"
        and all(gl_hdr.get(k) == "1" for k in ("ok_active", "ok_focus", "ok_backdrop", "ok_dlg", "ok_tip"))
        and (mode == "broadway" or gl_hdr.get("real_active") == "1"),
        "gallery-theme-and-css",
        f"theme={gl_hdr.get('theme')} backend={gl_hdr.get('backend')} css_errors={gl_hdr.get('css_errors')} real_backdrop={gl_hdr.get('real_backdrop')}",
    )

    im_act = Image.open(gal_act).convert("RGB")
    im_foc = Image.open(gal_foc).convert("RGB")
    im_bak = Image.open(gal_bak).convert("RGB")
    im_dlg = Image.open(gal_dlg).convert("RGB")
    im_tip = Image.open(gal_tip).convert("RGB")

    req_controls = {"notebook", "scale", "progress", "progress-pulse", "scrolledwindow", "vscrollbar", "hscrollbar"}
    clip_errs = [f"missing {c}" for c in sorted(req_controls - gl_items.keys())]
    for nm, ((x, y, w, h), (nw, nh)) in gl_items.items():
        if w < nw or h < nh or x < 0 or y < 0 or x + w > im_act.width or y + h > im_act.height:
            clip_errs.append(nm)
    record(not clip_errs, "gallery-no-clipping", "all 7 controls unclipped" if not clip_errs else "; ".join(clip_errs))

    v0, vdown, vup, h0, hright, hleft = (
        float(gl_hdr.get(key, "nan")) for key in ("v0", "v_down", "v_up", "h0", "h_right", "h_left")
    )
    record(
        gl_hdr.get("stepper_ok") == "1" and v0 == h0 == 0 and 0 <= vup < vdown and 0 <= hleft < hright,
        "gallery-classic-stepper-clicks",
        f"vertical={v0:.1f}→{vdown:.1f}→{vup:.1f} horizontal={h0:.1f}→{hright:.1f}→{hleft:.1f}",
    )

    sc_box = gl_items["scale"][0]
    sc_pad_box = (sc_box[0] - 4, sc_box[1] - 4, sc_box[2] + 8, sc_box[3] + 8)
    sc_foc_on = count_color(im_foc, sc_pad_box, (0x66, 0x66, 0xCC))
    sc_foc_act = count_color(im_act, sc_pad_box, (0x66, 0x66, 0xCC))
    sc_foc_bak = count_color(im_bak, sc_pad_box, (0x66, 0x66, 0xCC))
    record(
        gl_hdr.get("focus_reached") == "1" and sc_foc_on > sc_foc_act and sc_foc_bak <= sc_foc_act,
        "gallery-scale-keyboard-focus",
        f"focus_reached={gl_hdr.get('focus_reached')} active={sc_foc_act} focused={sc_foc_on} backdrop={sc_foc_bak}",
    )

    vsb_box = gl_items["vscrollbar"][0]
    vsb_lav_act = count_color(im_act, vsb_box, (0x99, 0x99, 0xFF))
    vsb_lav_bak = count_color(im_bak, vsb_box, (0x99, 0x99, 0xFF))
    record(
        vsb_lav_act >= 100 and vsb_lav_bak == 0,
        "gallery-scrollbar-backdrop-muted",
        f"active_lav_px={vsb_lav_act} backdrop_lav_px={vsb_lav_bak}",
    )

    px, py, pw, ph = gl_items["progress-pulse"][0]
    pulse_box = (px + 8, py + 2, px + pw - 8, py + ph - 2)
    pulse_diff = ImageStat.Stat(ImageChops.difference(im_act.crop(pulse_box), im_foc.crop(pulse_box))).mean
    record(max(pulse_diff) >= 4, "gallery-progress-pulse-moves", f"mean channel change={max(pulse_diff):.2f}")

    tip_white = count_color(im_tip, (0, 0, im_tip.width, im_tip.height), (0xFF, 0xFF, 0xFF))
    tip_black = count_color(im_tip, (0, 0, im_tip.width, im_tip.height), (0x00, 0x00, 0x00))
    record(
        im_tip.width >= 60 and im_tip.height >= 18 and tip_white >= 500 and tip_black >= 200,
        "gallery-tooltip-balloon",
        f"size={im_tip.width}x{im_tip.height} white={tip_white} black={tip_black}",
    )

    dlg_bg = count_color(im_dlg, (0, 0, im_dlg.width, im_dlg.height), (0xDD, 0xDD, 0xDD))
    dlg_gap = int(gl_hdr.get("dlg_btn_gap", "0"))
    record(
        gl_hdr.get("dlg_default") == "1" and dlg_gap >= 6 and dlg_bg >= 2000,
        "gallery-message-dialog",
        f"default={gl_hdr.get('dlg_default')} btn_gap={dlg_gap}px bg_#dddddd={dlg_bg}",
    )

    # 8. Separate overlay scrolling probe (opacity 0.85 blends #9999ff over white -> b >= 200, b - r >= 30)
    im_ovl = Image.open(ovl_png).convert("RGB")
    ovl_crop = im_ovl.crop((im_ovl.width - 20, 0, im_ovl.width, im_ovl.height))
    ovl_px = ovl_crop.get_flattened_data() if hasattr(ovl_crop, "get_flattened_data") else ovl_crop.getdata()
    ovl_lav = sum(1 for (r, g, b) in ovl_px if b >= 200 and b - r >= 30)
    ovl_vsb_w = int(ov_hdr.get("vsb_w", "99"))
    record(
        ov_hdr.get("theme") == "Platinum"
        and ov_hdr.get("backend") == expected_backend
        and ov_hdr.get("css_errors") == "0"
        and ov_hdr.get("scale") == "1"
        and ov_hdr.get("png_ok") == "1"
        and float(ov_hdr.get("scroll_val", "nan")) > float(ov_hdr.get("scroll_before", "nan"))
        and ov_hdr.get("overlay_enabled") == "1"
        and ov_hdr.get("has_overlay_class") == "1"
        and 1 <= ovl_vsb_w <= 12
        and ovl_lav >= 50,
        "overlay-scrollbar-probe",
        f"overlay_class={ov_hdr.get('has_overlay_class')} vsb_w={ovl_vsb_w}px lav_px={ovl_lav} scroll={ov_hdr.get('scroll_before')}→{ov_hdr.get('scroll_val')}",
    )

    # 9. Client-side HeaderBar probe (active, backdrop, narrow, maximized)
    im_csd_act = Image.open(csd_act).convert("RGB")
    im_csd_bak = Image.open(csd_bak).convert("RGB")
    im_csd_nar = Image.open(csd_nar).convert("RGB")
    im_csd_max = Image.open(csd_max).convert("RGB")

    hbx, hby, hbw, hbh = map(int, cs_hdr.get("hb_rect", "0,0,0,0").split(","))
    hb_box = (hbx, hby, hbw, hbh)
    # Pinstripe zone between centered title and right-side window boxes (free of "Filter" button)
    stripe_zone = (hbx + hbw - 90, hby + 4, 32, max(8, hbh - 8))
    csd_act_stripes = count_color(im_csd_act, stripe_zone, (0x77, 0x77, 0x77))
    csd_act_face = count_color(im_csd_act, hb_box, (0xCC, 0xCC, 0xCC))
    csd_bak_face = count_color(im_csd_bak, hb_box, (0xDD, 0xDD, 0xDD))
    csd_bak_stripes = count_color(im_csd_bak, stripe_zone, (0x77, 0x77, 0x77))
    csd_bak_stripes_white = count_color(im_csd_bak, stripe_zone, (0xFF, 0xFF, 0xFF))
    record(
        cs_hdr.get("theme") == "Platinum"
        and cs_hdr.get("backend") == expected_backend
        and cs_hdr.get("css_errors") == "0"
        and cs_hdr.get("scale") == "1"
        and cs_hdr.get("ok_active") == cs_hdr.get("ok_backdrop") == "1"
        and csd_act_stripes >= 60
        and csd_act_face >= 500
        and csd_bak_face >= 1000
        and csd_bak_stripes == 0
        and csd_bak_stripes_white == 0
        and (mode == "broadway" or (cs_hdr.get("real_active") == "1" and cs_hdr.get("real_backdrop") == "1")),
        "csd-headerbar-active-and-backdrop",
        f"act_stripes={csd_act_stripes} act_#ccc={csd_act_face} bak_#ddd={csd_bak_face} bak_stripes={csd_bak_stripes}",
    )

    nar_w = int(cs_hdr.get("narrow_w", "0"))
    nar_btn_w = int(cs_hdr.get("narrow_btn_w", "0"))
    max_w = int(cs_hdr.get("max_w", "0"))
    nar_stripes = count_color(im_csd_nar, (0, 0, im_csd_nar.width, min(hbh, im_csd_nar.height)), (0x77, 0x77, 0x77))
    max_stripes = count_color(im_csd_max, (0, 0, im_csd_max.width, 40), (0x77, 0x77, 0x77))
    record(
        200 <= nar_w <= 360
        and nar_btn_w >= 36
        and cs_hdr.get("ok_narrow") == cs_hdr.get("ok_max") == "1"
        and cs_hdr.get("narrow_btn_fits") == "1"
        and im_csd_nar.width == nar_w
        and nar_stripes >= 60
        and im_csd_max.width == max_w
        and max_stripes >= 500
        and (mode == "broadway" or (cs_hdr.get("is_max") == "1" and max_w == 1280)),
        "csd-headerbar-narrow-and-maximized",
        f"narrow_w={nar_w} app_btn_w={nar_btn_w} narrow_stripes={nar_stripes} is_max={cs_hdr.get('is_max')} max_w={max_w} max_stripes={max_stripes}",
    )

    if mode == "plasma":
        record(
            gl_hdr.get("real_backdrop") == "1" and cs_hdr.get("real_backdrop") == "1",
            "wayland-real-backdrop",
            f"gallery={gl_hdr.get('real_backdrop')} csd={cs_hdr.get('real_backdrop')}",
        )

    # 10. Real GTK 3 application check (meld)
    meld_ok, meld_detail = verify_meld(ev, mode)
    record(meld_ok, "real-app-meld", meld_detail)
    if mode == "plasma" and meld_ok:
        (shots / "gtk3-m3b2-meld.png").write_bytes((ev / "meld-plasma.png").read_bytes())

    for src, dst in (
        (chrome_png, "gtk3-m3b2-chrome.png"),
        (gal_act, "gtk3-m3b2-gallery-active.png"),
        (gal_foc, "gtk3-m3b2-gallery-focus.png"),
        (gal_bak, "gtk3-m3b2-gallery-backdrop.png"),
        (gal_dlg, "gtk3-m3b2-dialog.png"),
        (gal_tip, "gtk3-m3b2-tooltip.png"),
        (ovl_png, "gtk3-m3b2-overlay.png"),
        (csd_act, "gtk3-m3b2-csd-active.png"),
        (csd_bak, "gtk3-m3b2-csd-backdrop.png"),
        (csd_nar, "gtk3-m3b2-csd-narrow.png"),
        (csd_max, "gtk3-m3b2-csd-max.png"),
    ):
        (shots / dst).write_bytes(src.read_bytes())

    print(f"\n{total - failed} of {total} GTK 3 Milestone 3 Batch 2 checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
