#!/usr/bin/env python3
"""Verify Milestone 2 GTK 3 Platinum chrome crops and natural-size dialog checks.

1. Compares 1x fixed-geometry chrome renders against Mac OS 9.2.2 reference
   captures using tools/compare.py diff at tolerance 0 (all 6 rows in
   docs/GTK-PLAN.md plus the additional captured button/check/radio states from
   dev/check-style.sh).
2. Verifies the natural-size dialog:
   - theme=Platinum loaded via normal discovery, css_errors=0
   - zero text clipping (alloc >= nat on every control) and usable hit areas
   - active selection fill contains exact measured #CCCCFF pixels
   - backdrop selection renders readable muted selection pixels (distinct from
     #FFFFFF entry base and #CCCCFF active fill)
   - keyboard focus renders #6666CC focus outline on focused button/checkbox

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


def parse_coords(path: Path) -> tuple[dict[str, str], dict[str, tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int]]]]:
    header: dict[str, str] = {}
    items: dict[str, tuple[tuple[int, int, int, int], tuple[int, int, int, int], tuple[int, int]]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            for tok in line[1:].split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    header[k] = v
            continue
        m = re.match(r"^(\S+)\s+(\d+),(\d+),(\d+),(\d+)\s+alloc=(\d+),(\d+),(\d+),(\d+)\s+nat=(\d+)x(\d+)$", line)
        if m:
            name = m.group(1)
            rect = (int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))
            alloc = (int(m.group(6)), int(m.group(7)), int(m.group(8)), int(m.group(9)))
            nat = (int(m.group(10)), int(m.group(11)))
            items[name] = (rect, alloc, nat)
    return header, items


def count_color(im: Image.Image, box: tuple[int, int, int, int], target: tuple[int, int, int]) -> int:
    x, y, w, h = box
    crop = im.crop((max(0, x), max(0, y), min(im.width, x + w), min(im.height, y + h)))
    pixels = crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata()
    return sum(1 for p in pixels if p == target)


def verify_output(widget_png: Path, output_png: Path, pct: int) -> tuple[bool, str]:
    if not widget_png.is_file() or not output_png.is_file():
        return False, "missing widget or compositor capture"
    widget = Image.open(widget_png).convert("RGB")
    output = Image.open(output_png).convert("RGB")
    if output.size != (1024, 768):
        return False, f"unexpected output dimensions={output.size}"

    def focus_ring_bounds(im: Image.Image) -> tuple[int, int, int, int] | None:
        masks = [channel.point(lambda value: 255 if value == target else 0)
                 for channel, target in zip(im.split(), (0x66, 0x66, 0xCC))]
        return ImageChops.multiply(ImageChops.multiply(masks[0], masks[1]), masks[2]).getbbox()

    # Use the focused entry's measured ring as the same landmark in both images.
    widget_ring = focus_ring_bounds(widget)
    output_ring = focus_ring_bounds(output)
    if widget_ring is None or output_ring is None:
        return False, "entry focus ring missing from capture"
    ratio = pct / 200  # GTK renders into a 2× buffer at both output scales.
    width, height = (round(n * ratio) for n in widget.size)
    x = output_ring[0] - round(widget_ring[0] * ratio)
    y = output_ring[1] - round(widget_ring[1] * ratio)
    if x < 0 or y < 0 or x + width > output.width or y + height > output.height:
        return False, f"dialog {width}x{height} at ({x},{y}) clipped by the compositor"
    actual = output.crop((x, y, x + width, y + height))
    expected = widget.resize((width, height), Image.Resampling.BILINEAR)
    # Permit compositor filtering and subpixel alignment at fractional scale.
    mean_error = max(ImageStat.Stat(ImageChops.difference(actual, expected)).mean)
    limit = 5 if pct == 150 else 1
    return mean_error <= limit, f"output={output.width}x{output.height} dialog={width}x{height} mean_error={mean_error:.2f}"


def main() -> int:
    if len(sys.argv) != 4 or sys.argv[3] not in {"broadway", "plasma"}:
        print("usage: verify.py <evidence_dir> <shots_dir> <broadway|plasma>", file=sys.stderr)
        return 2

    ev = Path(sys.argv[1])
    shots = Path(sys.argv[2])
    shots.mkdir(parents=True, exist_ok=True)
    wayland = sys.argv[3] == "plasma"
    backend = "GdkWaylandDisplay" if wayland else "GdkBroadwayDisplay"

    chrome_png = ev / "gtk3-chrome.png"
    chrome_txt = ev / "gtk3-chrome.txt"
    dlg_active = ev / "gtk3-dialog-active.png"
    dlg_focus = ev / "gtk3-dialog-focus.png"
    dlg_focus_check = ev / "gtk3-dialog-focus-check.png"
    dlg_focus_radio = ev / "gtk3-dialog-focus-radio.png"
    dlg_backdrop = ev / "gtk3-dialog-backdrop.png"
    dlg_txt = ev / "gtk3-dialog.txt"

    failed = 0
    total = 0

    def record(ok: bool, name: str, detail: str) -> None:
        nonlocal failed, total
        total += 1
        tag = "ok  " if ok else "FAIL"
        print(f"{tag}    {name:<34} {detail}")
        if not ok:
            failed += 1

    # --- 1. Header / CSS / Discovery checks ---
    ch_hdr, ch_items = parse_coords(chrome_txt)
    dl_hdr, dl_items = parse_coords(dlg_txt)

    record(
        ch_hdr.get("theme") == "Platinum"
        and ch_hdr.get("css_errors") == "0"
        and ch_hdr.get("png_ok") == "1"
        and ch_hdr.get("backend") == backend
        and ch_hdr.get("scale") == "1",
        "chrome-theme-and-css",
        f"theme={ch_hdr.get('theme')} backend={ch_hdr.get('backend')} css_errors={ch_hdr.get('css_errors')}",
    )
    record(
        dl_hdr.get("theme") == "Platinum"
        and dl_hdr.get("css_errors") == "0"
        and dl_hdr.get("backend") == backend
        and dl_hdr.get("scale") == "1"
        and (not wayland or dl_hdr.get("real_active") == "1")
        and dl_hdr.get("ok_active") == "1"
        and dl_hdr.get("ok_focus") == "1"
        and dl_hdr.get("ok_focus_check") == "1"
        and dl_hdr.get("ok_focus_radio") == "1"
        and dl_hdr.get("ok_backdrop") == "1",
        "dialog-theme-and-css",
        f"theme={dl_hdr.get('theme')} backend={dl_hdr.get('backend')} css_errors={dl_hdr.get('css_errors')} real_backdrop={dl_hdr.get('real_backdrop')}",
    )

    # --- 2. 1x Fixed-Geometry Reference Pixel Comparisons (tolerance 0) ---
    def cmp_crop(name: str, ref_img: str, rx: int, ry: int, ox: int, oy: int, w: int, h: int) -> None:
        out_cmp = shots / f"cmp-gtk3-{name}.png"
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

    def cmp_bands(name: str, ref_img: str, rx: int, ry: int, w: int, h: int, d: int, bw: int) -> None:
        if name not in ch_items:
            record(False, f"ref-{name}", "missing in chrome coords")
            return
        (ox, oy, ow, oh), _, _ = ch_items[name]
        if (ow, oh) != (w, h):
            record(False, f"ref-{name}-size", f"got {ow}x{oh} expected {w}x{h}")
            return
        cmp_crop(f"{name}-top", ref_img, rx, ry, ox, oy, w, d)
        bd = d - 1 if name == "push-default" else d
        cmp_crop(f"{name}-bottom", ref_img, rx, ry + h - bd, ox, oy + h - bd, bw, bd)
        cmp_crop(f"{name}-left", ref_img, rx, ry, ox, oy, d, h)
        rh = h - (d if bw < w else 0)
        cmp_crop(f"{name}-right", ref_img, rx + w - d, ry, ox + w - d, oy, d, rh)

    # Buttons (docs/GTK-PLAN.md:33-35 + check-style.sh:44-49)
    cmp_bands("push-normal", "button-default-pressed.png", 617, 513, 70, 20, 4, 70)
    cmp_bands("push-pressed", "button-push-pressed.png", 641, 469, 70, 20, 4, 56)
    cmp_bands("push-disabled", "dialog-file-open.png", 851, 335, 80, 20, 4, 80)
    cmp_bands("push-default", "dialog-file-open.png", 848, 435, 86, 26, 8, 86)
    cmp_bands("push-default-pressed", "button-default-pressed.png", 697, 510, 78, 26, 8, 56)

    # Entries (docs/GTK-PLAN.md:36 + check-style.sh:172-181; outer 5 px bands)
    for ename, ry in (("entry-normal", 346), ("entry-focused", 432)):
        if ename not in ch_items:
            record(False, f"ref-{ename}", "missing in chrome coords")
            continue
        (ox, oy, ow, oh), _, _ = ch_items[ename]
        if (ow, oh) != (30, 26):
            record(False, f"ref-{ename}-size", f"got {ow}x{oh} expected 30x26")
            continue
        cmp_crop(f"{ename}-top", "appearance-3-fonts-clean.png", 846, ry, ox, oy, 30, 5)
        cmp_crop(f"{ename}-bottom", "appearance-3-fonts-clean.png", 846, ry + 21, ox, oy + 21, 30, 5)
        cmp_crop(f"{ename}-left", "appearance-3-fonts-clean.png", 846, ry, ox, oy, 5, 26)
        cmp_crop(f"{ename}-right", "appearance-3-fonts-clean.png", 846 + 25, ry, ox + 25, oy, 5, 26)

    # Checkboxes & Radios (docs/GTK-PLAN.md:37-38 + check-style.sh:51-58)
    sprite_refs = (
        ("check-off", "controls-general-controls.png", 550, 327, 14, 12),
        ("check-on", "controls-general-controls.png", 550, 280, 14, 12),
        ("check-off-pressed", "checkbox-pressed.png", 550, 327, 14, 10),
        ("check-on-disabled", "controls-memory.png", 553, 511, 14, 12),
        ("radio-off", "controls-general-controls.png", 553, 534, 12, 12),
        ("radio-on", "controls-general-controls.png", 553, 552, 12, 12),
        ("radio-off-pressed", "radio-pressed.png", 553, 534, 12, 8),
        ("radio-off-disabled", "controls-monitors.png", 732, 405, 12, 12),
    )
    for sname, rimg, rx, ry, sw, sh in sprite_refs:
        if sname not in ch_items:
            record(False, f"ref-{sname}", "missing in chrome coords")
            continue
        (ox, oy, _, _), _, _ = ch_items[sname]
        cmp_crop(sname, rimg, rx, ry, ox, oy, sw, sh)

    # --- 3. Natural-size dialog checks (clipping, hit areas, selection, focus) ---
    expected_controls = {
        "entry-selected", "entry-normal", "entry-disabled", "check-off", "check-on",
        "check-mixed", "check-disabled", "radio-one", "radio-two", "radio-disabled",
        "btn-cancel", "btn-disabled", "btn-ok-default",
    }
    clip_errs = [f"missing {name}" for name in sorted(expected_controls - dl_items.keys())]
    im_act = Image.open(dlg_active).convert("RGB")
    for name, (_, alloc, nat) in dl_items.items():
        x, y, aw, ah = alloc
        if x + aw > im_act.width or y + ah > im_act.height:
            clip_errs.append(f"{name} extends outside the dialog image")
        nw, nh = nat
        if aw < nw or ah < nh:
            clip_errs.append(f"{name}(alloc={aw}x{ah}<nat={nw}x{nh})")
        min_h = 20 if (name.startswith("btn-") or name.startswith("entry-")) else 18
        if ah < min_h:
            clip_errs.append(f"{name}(h={ah}<{min_h})")
    record(len(clip_errs) == 0, "dialog-no-clipping-and-hit-areas", "all 13 controls unclipped" if not clip_errs else "; ".join(clip_errs))

    im_foc = Image.open(dlg_focus).convert("RGB")
    im_fchk = Image.open(dlg_focus_check).convert("RGB")
    im_frad = Image.open(dlg_focus_radio).convert("RGB")
    im_bak = Image.open(dlg_backdrop).convert("RGB")

    sel_box = dl_items["entry-selected"][1]
    px_sel_active = count_color(im_act, sel_box, (0xCC, 0xCC, 0xFF))
    px_ring_active = count_color(im_act, sel_box, (0x66, 0x66, 0xCC))
    record(px_sel_active >= 200, "dialog-active-selection-#ccccff", f"px={px_sel_active}")
    record(px_ring_active >= 100, "dialog-entry-focus-ring-#6666cc", f"px={px_ring_active}")

    px_sel_backdrop = count_color(im_bak, sel_box, (0xDC, 0xDC, 0xEF))
    px_sel_active_in_bak = count_color(im_bak, sel_box, (0xCC, 0xCC, 0xFF))
    px_ring_backdrop = count_color(im_bak, sel_box, (0x66, 0x66, 0xCC))
    record(
        px_sel_backdrop >= 200 and px_sel_active_in_bak == 0 and px_ring_backdrop == 0,
        "dialog-backdrop-selection-muted",
        f"muted_#dcdcef_px={px_sel_backdrop} active_#ccccff_px={px_sel_active_in_bak} focus_ring_px={px_ring_backdrop}",
    )

    record(dl_hdr.get("default_class") == "1", "dialog-native-default-button",
           f"GTK .default={dl_hdr.get('default_class')}")
    btn_box = dl_items["btn-cancel"][1]
    chk_box = dl_items["check-off"][1]
    rad_box = dl_items["radio-one"][1]
    px_btn_focus = count_color(im_foc, btn_box, (0x66, 0x66, 0xCC))
    px_chk_focus = count_color(im_fchk, chk_box, (0x66, 0x66, 0xCC))
    px_rad_focus = count_color(im_frad, rad_box, (0x66, 0x66, 0xCC))
    record(px_btn_focus >= 60, "dialog-button-focus-#6666cc", f"px={px_btn_focus}")
    record(px_chk_focus >= 40, "dialog-check-focus-#6666cc", f"px={px_chk_focus}")
    record(px_rad_focus >= 40, "dialog-radio-focus-#6666cc", f"px={px_rad_focus}")

    # Derived/TBD functional presence check on chrome sheet (non-blank, distinct states)
    im_ch = Image.open(chrome_png).convert("RGB")
    mix_box = ch_items["check-mixed"][0]
    px_mix_bar = count_color(im_ch, (mix_box[0] + 3, mix_box[1] + 5, 6, 2), (0, 0, 0))
    record(px_mix_bar == 12, "tbd-check-mixed-6x2-bar", f"bar_black_px={px_mix_bar}/12")

    # Wayland also requires compositor evidence, contrast changes and scale checks.
    hc_txt = ev / "gtk3-hc.txt"
    if wayland:
        hc_hdr = parse_coords(hc_txt)[0] if hc_txt.is_file() else {}
        hc_rest_txt = ev / "gtk3-hc-restored.txt"
        hc_rest_hdr, hc_rest_items = parse_coords(hc_rest_txt) if hc_rest_txt.is_file() else ({}, {})
        hc_png = ev / "gtk3-hc-active.png"
        restored_png = ev / "gtk3-hc-restored-active.png"
        restored_entry = hc_rest_items.get("entry-selected")
        restored_selection = 0
        images_changed = False
        if hc_png.is_file() and restored_png.is_file() and restored_entry:
            with Image.open(hc_png) as contrast, Image.open(restored_png) as restored:
                images_changed = contrast.size != restored.size or contrast.tobytes() != restored.tobytes()
                restored_selection = count_color(restored.convert("RGB"), restored_entry[1], (0xCC, 0xCC, 0xFF))
        record(
            dl_hdr.get("real_backdrop") == "1",
            "wayland-real-backdrop-deactivation",
            f"real_backdrop={dl_hdr.get('real_backdrop')}",
        )
        record(
            hc_hdr.get("theme") == "HighContrast"
            and hc_hdr.get("ok_active") == "1"
            and hc_hdr.get("backend") == backend
            and hc_hdr.get("css_errors") == "0"
            and hc_rest_hdr.get("theme") == "Platinum"
            and hc_rest_hdr.get("css_errors") == "0"
            and hc_rest_hdr.get("backend") == backend
            and hc_rest_hdr.get("ok_active") == "1"
            and images_changed
            and restored_selection >= 200,
            "wayland-high-contrast-roundtrip",
            f"hc_theme={hc_hdr.get('theme')} restored_theme={hc_rest_hdr.get('theme')} "
            f"images_changed={images_changed} restored_selection_px={restored_selection}",
        )
        ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        for pct, exp_scale in (("150", "1.5"), ("200", "2")):
            slog = ev / f"scale-{pct}.log"
            stxt = ev / f"gtk3-dialog-{pct}.txt"
            spng = ev / f"gtk3-dialog-{pct}-active.png"
            stext = ansi_re.sub("", slog.read_text(encoding="utf-8", errors="replace")) if slog.is_file() else ""
            reported_scales = re.findall(r"^\s*Scale: ([0-9.]+)\s*$", stext, re.M)
            s_ok = reported_scales == [exp_scale]
            if stxt.is_file():
                shdr, sitems = parse_coords(stxt)
                s_clip = [
                    nm for nm, (_, a, nt) in sitems.items() if a[2] < nt[0] or a[3] < nt[1]
                ]
                output_png = ev / f"gtk3-output-{pct}.png"
                output_ok, output_detail = verify_output(spng, output_png, int(pct))
                scale_ok = (
                    output_ok
                    and s_ok
                    and shdr.get("theme") == "Platinum"
                    and shdr.get("css_errors") == "0"
                    and shdr.get("scale") == "2"
                    and shdr.get("backend") == backend
                    and shdr.get("real_active") == "1"
                    and shdr.get("ok_active") == "1"
                    and sitems.keys() == dl_items.keys()
                    and not s_clip
                    and spng.is_file()
                )
                if spng.is_file():
                    (shots / f"gtk3-m2-dialog-{pct}.png").write_bytes(spng.read_bytes())
                if output_png.is_file():
                    (shots / f"gtk3-m2-output-{pct}.png").write_bytes(output_png.read_bytes())
                record(
                    scale_ok,
                    f"wayland-scale-{pct}pct",
                    f"kscreen={','.join(reported_scales) or 'missing'} expected={exp_scale} gtk_scale={shdr.get('scale')} clipped={len(s_clip)} {output_detail}",
                )
            else:
                record(False, f"wayland-scale-{pct}pct", "missing dialog output")

    # Save copies into dev/shots/
    for src, dst_name in (
        (chrome_png, "gtk3-m2-chrome.png"),
        (dlg_active, "gtk3-m2-dialog-active.png"),
        (dlg_focus, "gtk3-m2-dialog-focus.png"),
        (dlg_focus_check, "gtk3-m2-dialog-focus-check.png"),
        (dlg_focus_radio, "gtk3-m2-dialog-focus-radio.png"),
        (dlg_backdrop, "gtk3-m2-dialog-backdrop.png"),
    ):
        (shots / dst_name).write_bytes(src.read_bytes())

    print(f"\n{total - failed} of {total} GTK 3 Milestone 2 checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
