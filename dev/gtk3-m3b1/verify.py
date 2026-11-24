#!/usr/bin/env python3
"""Verify Milestone 3 Batch 1 GTK 3 Platinum checks:
  - 27 fixed-geometry 1x reference crops at tolerance 0 (menubar, pop-up combos,
    list headers normal & sorted, separator, etched group box)
  - Natural-size gallery checks (zero clipping, #333399 menu highlight,
    #CCCCFF active treeview selection, #DCDCEF muted backdrop selection)
  - Real GTK 3 application (meld) launch & zero CSS errors check

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
        m = re.match(r"^(\S+)\s+(\d+),(\d+),(\d+),(\d+)\s+alloc=\d+,\d+,\d+,\d+\s+nat=(\d+)x(\d+)$", line)
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
    # The 4×4 opaque portion of the original button corner survives in Meld's
    # toolbar buttons regardless of their labels or width.
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
        # Compare the central content and leave shadows and decorations outside the crop.
        left, top, right, bottom = w // 16, h // 8, w - w // 16, h * 7 // 8
        ax, ay = (active.width - w) // 2, (active.height - h) // 2
        crop = output.convert("RGB").crop((x + left, y + top, x + right, y + bottom))
        active_rgb = active.convert("RGB")
        window = active_rgb.crop((ax + left, ay + top, ax + right, ay + bottom))
        difference = max(ImageStat.Stat(ImageChops.difference(crop, window)).mean)
        varied = max(ImageStat.Stat(window).stddev) > 5
        buttons = platinum_button_count(active_rgb)
    return varied and difference <= 1 and buttons >= 2, (
        f"pid={pids[0]} active={w}x{h} crop_mean_error={difference:.2f} platinum_buttons={buttons}"
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

    chrome_png = ev / "m3b1-chrome.png"
    chrome_txt = ev / "m3b1-chrome.txt"
    gal_act = ev / "m3b1-gallery-active.png"
    gal_bak = ev / "m3b1-gallery-backdrop.png"
    gal_menu = ev / "m3b1-menu-open.png"
    gal_txt = ev / "m3b1-gallery.txt"

    failed = 0
    total = 0

    def record(ok: bool, name: str, detail: str) -> None:
        nonlocal failed, total
        total += 1
        print(f"{'ok  ' if ok else 'FAIL'}    {name:<34} {detail}")
        if not ok:
            failed += 1

    ch_hdr, ch_items = parse_coords(chrome_txt)
    gl_hdr, gl_items = parse_coords(gal_txt)

    record(
        ch_hdr.get("theme") == "Platinum"
        and ch_hdr.get("backend") == expected_backend
        and ch_hdr.get("css_errors") == "0"
        and ch_hdr.get("png_ok") == "1"
        and ch_hdr.get("scale") == "1",
        "chrome-theme-and-css",
        f"theme={ch_hdr.get('theme')} backend={ch_hdr.get('backend')} css_errors={ch_hdr.get('css_errors')}",
    )
    record(
        gl_hdr.get("theme") == "Platinum"
        and gl_hdr.get("backend") == expected_backend
        and gl_hdr.get("css_errors") == "0"
        and gl_hdr.get("ok_active") == "1"
        and gl_hdr.get("ok_menu") == "1"
        and gl_hdr.get("ok_backdrop") == "1"
        and gl_hdr.get("scale") == "1"
        and (mode == "broadway" or gl_hdr.get("real_active") == "1"),
        "gallery-theme-and-css",
        f"theme={gl_hdr.get('theme')} backend={gl_hdr.get('backend')} css_errors={gl_hdr.get('css_errors')} real_backdrop={gl_hdr.get('real_backdrop')}",
    )

    def cmp_crop(name: str, ref_img: str, rx: int, ry: int, ox: int, oy: int, w: int, h: int) -> None:
        out_cmp = shots / f"cmp-gtk3-m3b1-{name}.png"
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

    # 1. Menu bar (menu-file-open.png: empty stretch + 35x20 open title bands)
    mb_x, mb_y, mb_w, mb_h = ch_items["menubar"][0]
    mt_x, mt_y, mt_w, mt_h = ch_items["menubar-title"][0]
    cmp_crop("menubar-empty", "menu-file-open.png", 72, 0, mb_x + mt_w + 10, mb_y, 7, 20)
    cmp_crop("menubar-title-top", "menu-file-open.png", 37, 0, mt_x, mb_y, 35, 2)
    cmp_crop("menubar-title-bottom", "menu-file-open.png", 37, 17, mt_x, mb_y + 17, 35, 3)
    cmp_crop("menubar-title-left", "menu-file-open.png", 37, 0, mt_x, mb_y, 7, 20)
    cmp_crop("menubar-title-right", "menu-file-open.png", 64, 0, mt_x + mt_w - 8, mb_y, 8, 20)

    # 2. Pop-up / ComboBox (appearance-2-appearance.png, appearance-4-desktop.png, popup-open*.png)
    def cmp_popup(name: str, ref_img: str, rx: int, ry: int, exp_w: int) -> None:
        ox, oy, ow, oh = ch_items[name][0]
        if (ow, oh) != (exp_w, 20):
            record(False, f"ref-{name}-size", f"got {ow}x{oh} expected {exp_w}x20")
            return
        cmp_crop(f"{name}-top", ref_img, rx, ry, ox, oy, exp_w, 3)
        cmp_crop(f"{name}-bottom", ref_img, rx, ry + 17, ox, oy + 17, exp_w, 3)
        cmp_crop(f"{name}-left", ref_img, rx, ry, ox, oy, 6, 20)
        cmp_crop(f"{name}-arrow", ref_img, rx + exp_w - 22, ry, ox + exp_w - 22, oy, 22, 20)

    cmp_popup("popup-normal", "appearance-2-appearance.png", 591, 257, 180)
    cmp_popup("popup-disabled", "appearance-4-desktop.png", 710, 451, 194)
    px, py, pw, ph = ch_items["popup-pressed"][0]
    if (pw, ph) == (180, 20):
        cmp_crop("popup-pressed-arrow-a", "popup-open.png", 751, 298, px + pw - 20, py, 20, 20)
        cmp_crop("popup-pressed-arrow-b", "popup-open-no-hover.png", 749, 298, px + pw - 22, py, 12, 20)
    else:
        record(False, "ref-popup-pressed-size", f"got {pw}x{ph} expected 180x20")

    # 3. TreeView Headers (disclosure-triangles.png)
    def cmp_header(name: str, rx: int, ry: int, exp_w: int) -> None:
        ox, oy, ow, oh = ch_items[name][0]
        if (ow, oh) != (exp_w, 21):
            record(False, f"ref-{name}-size", f"got {ow}x{oh} expected {exp_w}x21")
            return
        cmp_crop(f"{name}-top", "disclosure-triangles.png", rx, ry, ox, oy, exp_w, 3)
        cmp_crop(f"{name}-bottom", "disclosure-triangles.png", rx, ry + 18, ox, oy + 18, exp_w, 3)
        cmp_crop(f"{name}-left", "disclosure-triangles.png", rx, ry, ox, oy, 3, 21)
        cmp_crop(f"{name}-right", "disclosure-triangles.png", rx + exp_w - 3, ry, ox + exp_w - 3, oy, 3, 21)

    cmp_header("header-sorted", 105, 154, 238)
    cmp_header("header-normal", 343, 154, 149)

    # 4. Separator (appearance-3-fonts-clean.png@600,400,100,4)
    sx, sy, sw, sh = ch_items["separator"][0]
    cmp_crop("separator", "appearance-3-fonts-clean.png", 600, 400, sx, sy - 1, 100, 4)

    # 5. Etched Group Box (controls-general-controls.png: unbroken left 9 cols before title gap, right 8, bottom 2)
    gx, gy, gw, gh = ch_items["groupbox"][0]
    if (gw, gh) == (326, 109):
        cmp_crop("groupbox-left", "controls-general-controls.png", 538, 259, gx, gy, 9, 109)
        cmp_crop("groupbox-right", "controls-general-controls.png", 856, 259, gx + 318, gy, 8, 109)
        cmp_crop("groupbox-bottom", "controls-general-controls.png", 538, 366, gx, gy + 107, 326, 2)
    else:
        record(False, "ref-groupbox-size", f"got {gw}x{gh} expected 326x109")

    # 6. Natural-size gallery checks (clipping, menu highlight, treeview active & backdrop selection)
    im_act = Image.open(gal_act).convert("RGB")
    im_bak = Image.open(gal_bak).convert("RGB")
    im_menu = Image.open(gal_menu).convert("RGB")
    controls = {"menubar", "mi-file", "frame", "combo-normal", "combo-disabled", "separator", "scrolledwindow", "treeview", "list"}
    clip_errs = [f"missing {name}" for name in sorted(controls - gl_items.keys())]
    for name, ((x, y, w, h), (nw, nh)) in gl_items.items():
        if w < nw or h < nh or x + w > im_act.width or y + h > im_act.height:
            clip_errs.append(name)
    record(not clip_errs, "gallery-no-clipping", "all 9 controls unclipped" if not clip_errs else "; ".join(clip_errs))
    record(gl_hdr.get("native_sort") == "1", "gallery-native-sort", f"column toggled to ascending={gl_hdr.get('native_sort')}")
    session_log = ev / "session.log"
    layout_errors = (
        session_log.read_text(encoding="utf-8", errors="replace").count("Drawing a gadget with negative dimensions")
        if session_log.is_file() else None
    )
    record(
        gl_hdr.get("combo_open") == gl_hdr.get("combo_closed") == "1"
        and (mode == "broadway" or gl_hdr.get("combo_overflow") == "1")
        and gl_hdr.get("short_roundtrip") == "1" and layout_errors == 0,
        "gallery-combo-roundtrip",
        f"popup opened={gl_hdr.get('combo_open')} closed={gl_hdr.get('combo_closed')} "
        f"overflow={gl_hdr.get('combo_overflow')} short_roundtrip={gl_hdr.get('short_roundtrip')} layout_errors={layout_errors}",
    )

    tv_box = gl_items["treeview"][0]
    px_tv_sel = count_color(im_act, tv_box, (0xCC, 0xCC, 0xFF))
    px_tv_bak = count_color(im_bak, tv_box, (0xDC, 0xDC, 0xEF))
    px_tv_act_in_bak = count_color(im_bak, tv_box, (0xCC, 0xCC, 0xFF))
    record(px_tv_sel >= 1000, "gallery-treeview-selection-#ccccff", f"px={px_tv_sel}")
    record(
        px_tv_bak >= 1000 and px_tv_act_in_bak == 0,
        "gallery-treeview-backdrop-muted",
        f"muted_#dcdcef_px={px_tv_bak} active_#ccccff_px={px_tv_act_in_bak}",
    )

    tv_focus = count_color(im_act, tv_box, (0x66, 0x66, 0xCC))
    tv_focus_in_backdrop = count_color(im_bak, tv_box, (0x66, 0x66, 0xCC))
    record(
        tv_focus >= 100 and tv_focus_in_backdrop == 0,
        "gallery-treeview-keyboard-focus",
        f"active={tv_focus} backdrop={tv_focus_in_backdrop}",
    )

    list_box, _ = gl_items.get("list", ((0, 0, 0, 0), (0, 0)))
    list_active = count_color(im_act, list_box, (0xCC, 0xCC, 0xFF))
    list_muted = count_color(im_bak, list_box, (0xDC, 0xDC, 0xEF))
    list_active_in_backdrop = count_color(im_bak, list_box, (0xCC, 0xCC, 0xFF))
    record(
        list_active >= 1000 and list_muted >= 1000 and list_active_in_backdrop == 0,
        "gallery-listbox-selection",
        f"active={list_active} muted={list_muted} active_in_backdrop={list_active_in_backdrop}",
    )

    px_menu_hl = count_color(im_menu, (0, 0, im_menu.width, im_menu.height), (0x33, 0x33, 0x99))
    px_menu_bevel = count_color(im_menu, (0, 0, im_menu.width, im_menu.height), (0x66, 0x66, 0xCC))
    px_menu_bg = count_color(im_menu, (0, 0, im_menu.width, im_menu.height), (0xDD, 0xDD, 0xDD))
    record(
        px_menu_hl >= 500 and px_menu_bevel >= 16 and px_menu_bg >= 1000,
        "gallery-menu-highlight-and-frame",
        f"hl_#333399={px_menu_hl} bevel_#6666cc={px_menu_bevel} bg_#dddddd={px_menu_bg}",
    )

    if mode == "plasma":
        record(gl_hdr.get("real_backdrop") == "1", "wayland-real-backdrop", f"real_backdrop={gl_hdr.get('real_backdrop')}")

    meld_ok, meld_detail = verify_meld(ev, mode)
    record(meld_ok, "real-app-meld", meld_detail)
    if mode == "plasma" and meld_ok:
        (shots / "gtk3-m3b1-meld.png").write_bytes((ev / "meld-plasma.png").read_bytes())

    for src, dst in (
        (chrome_png, "gtk3-m3b1-chrome.png"),
        (gal_act, "gtk3-m3b1-gallery-active.png"),
        (gal_bak, "gtk3-m3b1-gallery-backdrop.png"),
        (gal_menu, "gtk3-m3b1-menu-open.png"),
    ):
        (shots / dst).write_bytes(src.read_bytes())

    print(f"\n{total - failed} of {total} GTK 3 Milestone 3 Batch 1 checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
