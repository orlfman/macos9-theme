#!/usr/bin/env python3
"""Verify Milestone 1 GTK discovery evidence and compute an observed verdict.

Never assumes pass because the shell script finished: inspects isolation logs,
per-layer/per-store marker colors, PNG pixel variance, KDE reapply exit codes
and snapshots, ordered preference-change step traces and watcher transitions
(including return to baseline), portal backend/frontend replies, and KWin
window identity + pixel evidence for FFmpeg Converter GTK.

Exit codes:
  0  PASS (all checks in this mode passed, or broadway standalone passed with
     virtual-KWin/portal checks explicitly reported as BLOCKED)
  1  FAIL (one or more observed checks failed or had unexplained precedence)
  2  BLOCKED (requested mode's own prerequisites failed to start)

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import configparser
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def parse_kv_line(line: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for tok in line.strip().split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out


def load_results(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        kv = parse_kv_line(line)
        if "trial" in kv and "stack" in kv:
            rows[(kv["trial"], kv["stack"])] = kv
    return rows


def load_watch(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    return [
        parse_kv_line(ln)
        for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if ln.strip()
    ]


def collapse_runs(values: list[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        if not out or out[-1] != v:
            out.append(v)
    return out


def check_png(path: Path) -> tuple[bool, str, tuple[int, int] | None]:
    if not path.is_file() or path.stat().st_size == 0:
        return False, "missing-or-empty", None
    try:
        im = Image.open(path).convert("RGB")
        st = ImageStat.Stat(im)
        max_sd = max(st.stddev)
        if im.width < 100 or im.height < 80:
            return False, f"too-small({im.width}x{im.height})", (im.width, im.height)
        if max_sd < 1.0:
            return False, f"blank-or-uniform(stddev={max_sd:.2f})", (im.width, im.height)
        return True, f"{im.width}x{im.height},stddev={max_sd:.1f}", (im.width, im.height)
    except Exception as exc:
        return False, f"unreadable({exc})", None


def parse_kde_snapshot(path: Path) -> dict[str, object] | None:
    """Parse snapshot_kde_files() output into structured sections and per-file text."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    section = ""
    lnf: dict[str, str] = {}
    gsettings: dict[str, str] = {}
    paths: list[str] = []
    files: dict[str, tuple[str, str]] = {}  # suffix_key -> (meta, content)
    cur_file_key: str | None = None
    cur_meta = ""
    cur_lines: list[str] = []

    def flush_file() -> None:
        nonlocal cur_file_key, cur_meta, cur_lines
        if cur_file_key is not None:
            files[cur_file_key] = (cur_meta, "\n".join(cur_lines))
            cur_file_key = None
            cur_meta = ""
            cur_lines = []

    file_hdr_re = re.compile(r"^--- (.+?) \((.+)\) ---$")
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("=== ") and line.endswith(" ==="):
            flush_file()
            section = line.strip("= ").strip()
            continue
        if section == "LOOK AND FEEL" and "=" in line:
            k, v = line.split("=", 1)
            lnf[k.strip()] = v.strip()
        elif section == "PATHS AND SYMLINKS" and line.strip():
            paths.append(line.strip())
        elif section == "GSETTINGS" and "=" in line:
            k, v = line.split("=", 1)
            gsettings[k.strip()] = v.strip()
        elif section == "FILE CONTENTS":
            m = file_hdr_re.match(line)
            if m:
                flush_file()
                fpath, meta = m.group(1), m.group(2)
                for suffix in (
                    "gtk-3.0/settings.ini",
                    "gtk-3.0/gtk.css",
                    "gtk-3.0/colors.css",
                    "gtk-4.0/settings.ini",
                    "gtk-4.0/gtk.css",
                    "gtk-4.0/colors.css",
                    "xsettingsd/xsettingsd.conf",
                    ".gtkrc-2.0",
                ):
                    if fpath.endswith(suffix):
                        cur_file_key = suffix
                        cur_meta = meta
                        break
            elif cur_file_key is not None:
                cur_lines.append(line)
    flush_file()
    return {"lnf": lnf, "paths": paths, "gsettings": gsettings, "files": files}


def has_setting(filename: str, content: str, directive: str) -> bool:
    if filename.endswith(".ini"):
        key, value = directive.split("=", 1)
        ini = configparser.ConfigParser(interpolation=None)
        try:
            ini.read_string(content)
            return ini.get("Settings", key, fallback=None) == value
        except configparser.Error:
            return False

    # KWin serializes gtkrc key="value" and XSettings key "value".
    separator = " " if filename.endswith(".conf") else "="
    key, value = directive.split(separator, 1)
    values = []
    for line in content.splitlines():
        name, _, setting = line.strip().partition(separator)
        if name.strip() == key:
            values.append(setting.strip())
    return values == [value]


def css_directives(text: str) -> list[str]:
    return [line.strip() for line in re.sub(r"/\*.*?(?:\*/|$)", "", text, flags=re.S).splitlines()]


def check_kde_stores_and_files(
    snap: dict[str, object] | None,
    *,
    expect_theme: str,
    expect_lnf: str | None = None,
    expect_platinum_colors: bool = False,
    expect_user_gtk4_rule: str | None = None,
    expect_icon_cursor: tuple[str, str] | None = None,
) -> tuple[bool, list[str]]:
    if snap is None:
        return False, ["snapshot-missing"]
    errs: list[str] = []
    lnf = snap["lnf"]  # type: ignore[assignment]
    paths = snap["paths"]  # type: ignore[assignment]
    gsettings = snap["gsettings"]  # type: ignore[assignment]
    files = snap["files"]  # type: ignore[assignment]

    # Reject any symlinks among GTK config paths
    for p in paths:
        if p.startswith("l ") and ("gtk-3.0" in p or "gtk-4.0" in p or "xsettingsd" in p or ".gtkrc-2.0" in p):
            errs.append(f"unexpected-symlink({p})")

    if expect_lnf is not None:
        if lnf.get("kdedefaults_package") != expect_lnf:
            errs.append(f"kdedefaults_package={lnf.get('kdedefaults_package')}!={expect_lnf}")
        if lnf.get("kreadconfig_lnf") != expect_lnf:
            errs.append(f"kreadconfig_lnf={lnf.get('kreadconfig_lnf')}!={expect_lnf}")

    # Verify all 5 theme stores
    if gsettings.get("gtk-theme") != f"'{expect_theme}'":
        errs.append(f"gsettings={gsettings.get('gtk-theme')}")

    expected_lines = {
        "gtk-3.0/settings.ini": f"gtk-theme-name={expect_theme}",
        "gtk-4.0/settings.ini": f"gtk-theme-name={expect_theme}",
        "xsettingsd/xsettingsd.conf": f'Net/ThemeName "{expect_theme}"',
        ".gtkrc-2.0": f'gtk-theme-name="{expect_theme}"',
    }
    for key, needle in expected_lines.items():
        entry = files.get(key)
        if not entry or entry[0] == "ABSENT" or entry[0].startswith("SYMLINK"):
            errs.append(f"{key}:{entry[0] if entry else 'missing'}")
        elif not has_setting(key, entry[1], needle):
            errs.append(f"{key}:missing({needle})")

    for ver in ("3", "4"):
        gcss = files.get(f"gtk-{ver}.0/gtk.css")
        if not gcss or gcss[0] == "ABSENT" or gcss[0].startswith("SYMLINK"):
            errs.append(f"gtk-{ver}.0/gtk.css:{gcss[0] if gcss else 'missing'}")
        elif "@import 'colors.css';" not in css_directives(gcss[1]):
            errs.append(f"gtk-{ver}.0/gtk.css:missing-import")

        ccss = files.get(f"gtk-{ver}.0/colors.css")
        if not ccss or ccss[0] == "ABSENT" or ccss[0].startswith("SYMLINK"):
            errs.append(f"gtk-{ver}.0/colors.css:{ccss[0] if ccss else 'missing'}")
        elif expect_platinum_colors:
            if "@define-color borders_breeze #b1b1b1;" not in css_directives(ccss[1]) or "@define-color error_color_breeze #cc0000;" not in css_directives(ccss[1]):
                errs.append(f"gtk-{ver}.0/colors.css:not-platinum")

    if expect_user_gtk4_rule is not None:
        g4 = files.get("gtk-4.0/gtk.css")
        if not g4 or expect_user_gtk4_rule not in css_directives(g4[1]):
            errs.append("gtk-4.0/gtk.css:user-rule-lost")

    if expect_icon_cursor is not None:
        icon, cursor = expect_icon_cursor
        for key, needles in (
            ("gtk-3.0/settings.ini", (f"gtk-icon-theme-name={icon}", f"gtk-cursor-theme-name={cursor}")),
            ("gtk-4.0/settings.ini", (f"gtk-icon-theme-name={icon}", f"gtk-cursor-theme-name={cursor}")),
            ("xsettingsd/xsettingsd.conf", (f'Net/IconThemeName "{icon}"', f'Gtk/CursorThemeName "{cursor}"')),
            (".gtkrc-2.0", (f'gtk-icon-theme-name="{icon}"', f'gtk-cursor-theme-name="{cursor}"')),
        ):
            entry = files.get(key)
            for n in needles:
                if not entry or not has_setting(key, entry[1], n):
                    errs.append(f"{key}:missing({n})")

    return (len(errs) == 0), errs


def parse_step_sections(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    sections: dict[str, list[str]] = {}
    cur: str | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^=== (STEP \d+):.*===$", raw.strip())
        if m:
            cur = m.group(1)
            if cur in sections:
                return {}
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(raw)
    return {k: "\n".join(v) for k, v in sections.items()}


def check_trace_values(step: str, body: str, requirements: tuple[str, ...], errors: list[str]) -> None:
    for expected in requirements:
        prefix = expected.partition("=")[0] + "="
        matches = [line for line in body.splitlines() if line.startswith(prefix)]
        if matches != [expected]:
            errors.append(f"{step}:missing-or-conflicting({expected})")


def check_step_polls(events: list[dict[str, str]], expected: dict[str, str], errors: list[str]) -> None:
    # session.sh signals each watcher once after each source change.
    polls = [row for row in events if row.get("tag") == "poll"]
    for key, values in expected.items():
        if [row.get(key) for row in polls] != values.split():
            errors.append(f"wrong-step-polls({key})")


def check_rc_log(path: Path, key: str) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"missing({path.name})"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    matches = [ln.strip() for ln in lines if ln.strip().startswith(f"{key}=")]
    if not matches:
        return False, f"missing-key({key})"
    if matches[-1] != f"{key}=0" or any(m != f"{key}=0" for m in matches):
        return False, f"nonzero({','.join(matches)})"
    return True, f"{key}=0"


def check_ffmpeg_evidence(
    root: Path,
    shots_dir: Path,
    stock_pngs: list[Path],
) -> tuple[str, str]:
    flog = root / "ffmpeg.log"
    if not flog.is_file():
        return "FAIL", "missing ffmpeg.log"
    ftxt = flog.read_text(encoding="utf-8", errors="replace")
    if "FFMPEG_STATUS=BLOCKED" in ftxt:
        return "BLOCKED", ftxt.strip()
    if "FFMPEG_STATUS=PASS" not in ftxt:
        return "FAIL", ftxt.strip()[:200] or "FFMPEG_STATUS!=PASS"

    errs: list[str] = []
    m_pid = re.search(r"^FFMPEG_PID=(\d+)$", ftxt, re.M)
    m_dbus = re.search(r"^DBUS_OWNER_PID=(\S+)$", ftxt, re.M)
    m_theme = re.search(r"^ACTIVE_GTK_THEME=(.+)$", ftxt, re.M)
    if not m_pid:
        errs.append("missing-FFMPEG_PID")
        ff_pid = ""
    else:
        ff_pid = m_pid.group(1)
    if not m_dbus or m_dbus.group(1) != ff_pid:
        errs.append(f"dbus-owner-pid-mismatch({m_dbus.group(1) if m_dbus else 'missing'}!={ff_pid})")
    if not m_theme or m_theme.group(1).strip() != "'DiscoveryKde'":
        errs.append(f"active-theme={m_theme.group(1).strip() if m_theme else 'missing'}!='DiscoveryKde'")

    expected_settings = {
        "ACTIVE_COLOR_SCHEME": "v v u 2",
        "ACTIVE_ACCENT": "v v (ddd) 0.8 0.8 1",
        "ACTIVE_CONTRAST": "v v u 0",
    }
    for key, value in expected_settings.items():
        if re.findall(rf"^{key}=(.*)$", ftxt, re.M) != [value]:
            errs.append(f"incorrect-launch-setting({key})")

    # Verify mapped window identity from KWin (AUDIT.md #155)
    wlog = root / "ffmpeg-window.log"
    win_geom: tuple[int, int, int, int] | None = None
    if not wlog.is_file():
        errs.append("missing-ffmpeg-window.log")
    else:
        wtxt = wlog.read_text(encoding="utf-8", errors="replace")
        matched_line = None
        for ln in wtxt.splitlines():
            if "KWIN_WINDOW_INFO" in ln and f"pid={ff_pid} " in ln:
                matched_line = ln
                break
        if not matched_line:
            if "KWIN_PROBE_READY" not in wtxt:
                errs.append("missing-kwin-script-output")
            errs.append(f"no-kwin-window-for-pid({ff_pid})")
        else:
            if "active=1" not in matched_line:
                errs.append("kwin-window-not-active")
            if "class=com.github.pieman.FFmpegConverterGTK" not in matched_line and "class=ffmpeg-converter-gtk" not in matched_line:
                errs.append("kwin-window-class-mismatch")
            if "FFmpeg Converter GTK" not in matched_line:
                errs.append("kwin-window-caption-mismatch")
            mg = re.search(r"\bx=(-?\d+)\s+y=(-?\d+)\s+w=(\d+)\s+h=(\d+)\b", matched_line)
            if not mg:
                errs.append("kwin-window-geom-missing")
            else:
                wx, wy, ww, wh = (int(mg.group(i)) for i in range(1, 5))
                if ww < 600 or wh < 400:
                    errs.append(f"kwin-window-too-small({ww}x{wh})")
                win_geom = (wx, wy, ww, wh)

        gw_part = wtxt.split("=== KWIN GETWINDOWINFO ===", 1)[-1] if "=== KWIN GETWINDOWINFO ===" in wtxt else ""
        if matched_line:
            uuid = re.search(r" uuid=(\{[a-fA-F0-9-]+\}) ", matched_line)
            if not uuid or f"FFMPEG_UUID={uuid[1]}" not in gw_part.splitlines() or f'"uuid" s "{uuid[1]}"' not in gw_part:
                errs.append("getWindowInfo-uuid-mismatch")
        if "FFMPEG_UUID=NONE" in gw_part or "FFMPEG_UUID=" not in gw_part:
            errs.append("missing-kwin-getWindowInfo-uuid")
        else:
            if f'"pid" i {ff_pid}' not in gw_part and f'"pid" u {ff_pid}' not in gw_part:
                errs.append("getWindowInfo-pid-mismatch")
            if "FFmpeg Converter GTK" not in gw_part:
                errs.append("getWindowInfo-caption-mismatch")

    # Verify full-screen capture dimensions, non-identity with stock PNGs, and window-rect pixels
    fpng = root / "ffmpeg-plasma.png"
    ok_fp, fp_det, fp_size = check_png(fpng)
    if not ok_fp or fp_size is None:
        errs.append(f"png-invalid({fp_det})")
    else:
        if fp_size != (1024, 768):
            errs.append(f"wrong-size({fp_size[0]}x{fp_size[1]}!=1024x768)")
        fbytes = fpng.read_bytes()
        for sp in stock_pngs:
            if sp.is_file() and sp.read_bytes() == fbytes:
                errs.append(f"identical-to-stock({sp.name})")

        im = Image.open(fpng).convert("RGB")
        x0, y0, x1, y1 = 0, 0, im.width, im.height
        if win_geom is not None:
            wx, wy, ww, wh = win_geom
            x0 = max(0, wx)
            y0 = max(0, wy)
            x1 = min(im.width, wx + ww)
            y1 = min(im.height, wy + wh)
        crop = im.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1)))
        total = crop.width * crop.height
        light = 0
        purple = 0
        pixels = crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata()
        for r, g, b in pixels:
            if r >= 230 and g >= 230 and b >= 230:
                light += 1
            if b > g + 18 and r > g + 12 and r >= 120 and b >= 140:
                purple += 1
        light_pct = (100.0 * light / total) if total else 0.0
        if light_pct < 40.0:
            errs.append(f"window-not-light-chrome({light_pct:.1f}%)")
        if purple < 1000:
            errs.append(f"missing-rendered-purple-accent(px={purple})")

    # Match the visible window interior in both captures, excluding shadow and corners.
    apng = root / "ffmpeg-active.png"
    active_note = "active_png=absent"
    if not apng.is_file() or apng.stat().st_size == 0:
        errs.append("missing-active-capture")
    else:
        ok_ap, ap_det, ap_size = check_png(apng)
        if not ok_ap or ap_size is None:
            errs.append(f"active-png-invalid({ap_det})")
        else:
            if ap_size[0] < 600 or ap_size[1] < 400:
                errs.append(f"active-png-too-small({ap_size[0]}x{ap_size[1]})")
            if win_geom is not None:
                _, _, ww, wh = win_geom
                if abs(ap_size[0] - ww) > 160 or abs(ap_size[1] - wh) > 160:
                    errs.append(f"active-png-geom-mismatch({ap_size[0]}x{ap_size[1]} vs {ww}x{wh})")
                elif ok_fp and fp_size == (1024, 768):
                    wx, wy, _, _ = win_geom
                    ax = (ap_size[0] - ww) // 2
                    ay = (ap_size[1] - wh) // 2
                    left, top = max(16, -wx), max(16, -wy)
                    right, bottom = min(ww - 16, im.width - wx), min(wh - 16, im.height - wy)
                    if right <= left or bottom <= top:
                        errs.append("no-visible-window-interior")
                    else:
                        desktop = im.crop((wx + left, wy + top, wx + right, wy + bottom))
                        with Image.open(apng) as active:
                            window = active.convert("RGB").crop((ax + left, ay + top, ax + right, ay + bottom))
                        if ImageChops.difference(desktop, window).getbbox():
                            errs.append("active-capture-content-mismatch")
            active_note = f"active_png={ap_det}"

    if errs:
        return "FAIL", "; ".join(errs)

    shutil.copy2(fpng, shots_dir / "gtk-discovery-ffmpeg-plasma.png")
    if apng.is_file() and apng.stat().st_size > 0:
        shutil.copy2(apng, shots_dir / "gtk-discovery-ffmpeg-active.png")
    geom_s = f"{win_geom[0]},{win_geom[1]},{win_geom[2]}x{win_geom[3]}" if win_geom else "none"
    return (
        "PASS",
        f"pid={ff_pid} active_theme=DiscoveryKde kwin_geom={geom_s} png={fp_det} {active_note} "
        f"light={light_pct:.1f}% purple_px={purple} visual_review=manual-inspection-required",
    )


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: verify.py <root> <mode:broadway|plasma> <shots_dir>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    mode = sys.argv[2]
    shots_dir = Path(sys.argv[3])
    shots_dir.mkdir(parents=True, exist_ok=True)

    checks: list[tuple[str, str, str, str]] = []  # (area, check_name, status, detail)

    def add(area: str, name: str, status: str, detail: str) -> None:
        checks.append((area, name, status, detail))

    # 1. Isolation check
    iso_text = (
        (root / "isolation.log").read_text(encoding="utf-8", errors="replace").strip()
        if (root / "isolation.log").is_file()
        else ""
    )
    if iso_text.startswith("ISOLATION=PASS"):
        add("session", "disposable-home-and-dconf", "PASS", iso_text)
    else:
        add("session", "disposable-home-and-dconf", "FAIL", iso_text or "missing isolation.log")

    rows = load_results(root / "results.log")
    stacks = ("gtk3", "gtk4", "adw")
    expected_backend = "GdkBroadwayDisplay" if mode == "broadway" else "GdkWaylandDisplay"

    # 2. Stock screenshots & cold-launch baselines
    stock_probe: dict[str, str] = {}
    stock_pngs: list[Path] = []
    for stack in stacks:
        r = rows.get(("stock", stack))
        png = root / f"stock-{stack}.png"
        stock_pngs.append(png)
        ok_png, png_detail, _ = check_png(png)
        if not r:
            add(stack, "stock-baseline", "FAIL", "no result row")
            continue
        stock_probe[stack] = r.get("probe", "")
        ok_backend = r.get("backend") == expected_backend
        ok_err = r.get("css_errors") == "0"
        ok_theme = (r.get("theme") == "Adwaita-empty") if stack == "adw" else (r.get("theme", "") != "")
        if ok_png:
            shutil.copy2(png, shots_dir / f"gtk-discovery-stock-{stack}.png")
        status = "PASS" if (ok_png and ok_backend and ok_err and ok_theme) else "FAIL"
        extra = ""
        if stack == "adw":
            extra = (
                f" adw_dark={r.get('adw_dark')} adw_hc={r.get('adw_hc')} "
                f"accent={r.get('adw_accent_nick')}({r.get('adw_accent_enum')})/{r.get('adw_accent_rgba')}"
            )
        add(
            stack,
            "stock-baseline",
            status,
            f"backend={r.get('backend')} theme={r.get('theme')} probe={r.get('probe')} png={png_detail}{extra}",
        )

    # 3. Per-store trials: settings.ini, GSettings, XSettings
    for stack in stacks:
        r = rows.get(("theme-ini", stack))
        if not r:
            add(stack, "store-settings-ini", "FAIL", "missing row")
        elif stack in ("gtk3", "gtk4"):
            if mode == "broadway":
                ok = r.get("theme") == "DiscoveryIni" and r.get("probe") == "#112233" and r.get("ind_theme") == "#11aa33"
                add(
                    stack,
                    "store-settings-ini",
                    "PASS" if ok else "FAIL",
                    f"theme={r.get('theme')} probe={r.get('probe')} ind_theme={r.get('ind_theme')}",
                )
            else:
                ok = r.get("theme") == "Adwaita" and r.get("probe") == stock_probe.get(stack)
                add(
                    stack,
                    "store-settings-ini",
                    "PASS" if ok else "FAIL",
                    f"overridden-by-gsettings-default theme={r.get('theme')} probe={r.get('probe')}",
                )
        else:
            ok = r.get("theme") == "Adwaita-empty" and r.get("probe") != "#112233" and r.get("ind_theme") != "#11aa33"
            add(
                stack,
                "store-settings-ini",
                "PASS" if ok else "FAIL",
                f"theme={r.get('theme')} probe={r.get('probe')} (expected Adwaita-empty ignoring named theme)",
            )

        rg = rows.get(("theme-gsettings", stack))
        if not rg:
            add(stack, "store-gsettings", "FAIL", "missing row")
        else:
            loaded_gs = (
                rg.get("theme") == "DiscoveryGSettings"
                and rg.get("probe") == "#223344"
                and rg.get("ind_theme") == "#22bb44"
            )
            stayed_stock = rg.get("probe") == stock_probe.get(stack) and rg.get("ind_theme") == stock_probe.get(stack)
            if stack == "adw":
                ok = rg.get("theme") == "Adwaita-empty" and stayed_stock
                note = "ignored-adwaita-empty"
            elif mode == "plasma":
                ok = loaded_gs
                note = "loaded-via-gsettings" if loaded_gs else "UNEXPECTED"
            else:
                ok = stayed_stock
                note = "ignored-on-broadway" if stayed_stock else "UNEXPECTED"
            add(
                stack,
                "store-gsettings",
                "PASS" if ok else "FAIL",
                f"{note} theme={rg.get('theme')} probe={rg.get('probe')} ind_theme={rg.get('ind_theme')}",
            )

        rx = rows.get(("theme-xsettings", stack))
        if not rx:
            add(stack, "store-xsettings", "FAIL", "missing row")
        else:
            ok = rx.get("probe") != "#445566" and rx.get("ind_theme") != "#44dd66"
            add(
                stack,
                "store-xsettings",
                "PASS" if ok else "FAIL",
                f"theme={rx.get('theme')} probe={rx.get('probe')} (X11-only store ignored on {rx.get('backend')})",
            )

    # 4. Isolated & competing CSS layers
    for stack in stacks:
        ra = rows.get(("app-only", stack))
        ok_a = bool(
            ra and ra.get("probe") == "#654321" and ra.get("ind_app") == "#ee8811" and ra.get("css_errors") == "0"
        )
        add(
            stack,
            "layer-app-only",
            "PASS" if ok_a else "FAIL",
            f"probe={ra.get('probe') if ra else 'none'} ind_app={ra.get('ind_app') if ra else 'none'}",
        )

        ru = rows.get(("user-only", stack))
        ok_u = bool(
            ru and ru.get("probe") == "#abcdef" and ru.get("ind_user") == "#cc11aa" and ru.get("css_errors") == "0"
        )
        add(
            stack,
            "layer-user-only",
            "PASS" if ok_u else "FAIL",
            f"probe={ru.get('probe') if ru else 'none'} ind_user={ru.get('ind_user') if ru else 'none'}",
        )

        rta = rows.get(("conflict-theme-app", stack))
        if not rta:
            add(stack, "conflict-theme-vs-app", "FAIL", "missing row")
        elif stack in ("gtk3", "gtk4"):
            ok = rta.get("probe") == "#654321" and rta.get("ind_theme") == "#11aa33" and rta.get("ind_app") == "#ee8811"
            add(
                stack,
                "conflict-theme-vs-app",
                "PASS" if ok else "FAIL",
                f"probe={rta.get('probe')} ind_theme={rta.get('ind_theme')} ind_app={rta.get('ind_app')}",
            )
        else:
            ok = rta.get("probe") == "#654321" and rta.get("ind_theme") != "#11aa33" and rta.get("ind_app") == "#ee8811"
            add(
                stack,
                "conflict-theme-vs-app",
                "PASS" if ok else "FAIL",
                f"probe={rta.get('probe')} ind_theme={rta.get('ind_theme')}(stock) ind_app={rta.get('ind_app')}",
            )

        rca = rows.get(("conflict-all", stack))
        if not rca:
            add(stack, "conflict-all-layers", "FAIL", "missing row")
        elif stack in ("gtk3", "gtk4"):
            ok = (
                rca.get("probe") == "#abcdef"
                and rca.get("ind_theme") == "#11aa33"
                and rca.get("ind_app") == "#ee8811"
                and rca.get("ind_user") == "#cc11aa"
            )
            add(
                stack,
                "conflict-all-layers",
                "PASS" if ok else "FAIL",
                f"probe={rca.get('probe')} ind_theme={rca.get('ind_theme')} ind_app={rca.get('ind_app')} ind_user={rca.get('ind_user')}",
            )
        else:
            ok = (
                rca.get("probe") == "#abcdef"
                and rca.get("ind_theme") != "#11aa33"
                and rca.get("ind_app") == "#ee8811"
                and rca.get("ind_user") == "#cc11aa"
            )
            add(
                stack,
                "conflict-all-layers",
                "PASS" if ok else "FAIL",
                f"probe={rca.get('probe')} ind_theme={rca.get('ind_theme')}(stock) ind_app={rca.get('ind_app')} ind_user={rca.get('ind_user')}",
            )

    # 5. KDE kded6 selection & global-theme reapply (AUDIT.md #154)
    kded_st = (
        (root / "kded-status.log").read_text(encoding="utf-8", errors="replace").strip()
        if (root / "kded-status.log").is_file()
        else ""
    )
    ok_setgtk_rc, setgtk_det = check_rc_log(root / "setgtktheme.log", "SETGTKTHEME_RC")
    snap_sel = parse_kde_snapshot(root / "kde-files-selected.log")
    ok_sel_files, sel_errs = check_kde_stores_and_files(snap_sel, expect_theme="DiscoveryKde")
    sel_all_errs: list[str] = []
    if "KDED_GTKCONFIG_LOADED=1" not in kded_st:
        sel_all_errs.append(kded_st or "missing-kded-status")
    if not ok_setgtk_rc:
        sel_all_errs.append(setgtk_det)
    sel_all_errs.extend(sel_errs)
    add(
        "kde",
        "kded6-setGtkTheme-files",
        "PASS" if not sel_all_errs else "FAIL",
        f"{kded_st} {setgtk_det} 5-stores=DiscoveryKde regular-files-only"
        if not sel_all_errs
        else "; ".join(sel_all_errs),
    )

    ok_lnf1, lnf1_det = check_rc_log(root / "lnf-apply.log", "LNF_APPLY_RC")
    snap_re1 = parse_kde_snapshot(root / "kde-files-reapplied.log")
    ok_re1, re1_errs = check_kde_stores_and_files(
        snap_re1,
        expect_theme="DiscoveryKde",
        expect_lnf="platinum.desktop",
        expect_platinum_colors=True,
    )
    re1_all_errs = ([] if ok_lnf1 else [lnf1_det]) + re1_errs
    add(
        "kde",
        "platinum-lnf-reapply",
        "PASS" if not re1_all_errs else "FAIL",
        f"{lnf1_det} active=platinum.desktop 5-stores=DiscoveryKde platinum-colors=OK"
        if not re1_all_errs
        else "; ".join(re1_all_errs),
    )

    ok_lnf2, lnf2_det = check_rc_log(root / "lnf-reapply2.log", "LNF_REAPPLY2_RC")
    snap_re2 = parse_kde_snapshot(root / "kde-files-reapplied-with-user-gtk4.log")
    ok_re2, re2_errs = check_kde_stores_and_files(
        snap_re2,
        expect_theme="DiscoveryKde",
        expect_lnf="platinum.desktop",
        expect_platinum_colors=True,
        expect_user_gtk4_rule="#ind-user { color: #aa4499; }",
        expect_icon_cursor=("WhiteSur-lavender-light", "macOS-cursors"),
    )
    re2_all_errs = ([] if ok_lnf2 else [lnf2_det]) + re2_errs
    for stack in ("gtk4", "adw"):
        row = rows.get(("kde-reapplied-user", stack), {})
        if (row.get("ind_user"), row.get("ind_app")) != ("#aa4499", "#cc0000"):
            re2_all_errs.append(f"{stack}:user-rule-or-import-inactive")
    add(
        "kde",
        "platinum-lnf-reapply-user-gtk4",
        "PASS" if not re2_all_errs else "FAIL",
        f"{lnf2_det} active=platinum.desktop user-gtk4-css-preserved+@import icons=WhiteSur-lavender-light cursors=macOS-cursors"
        if not re2_all_errs
        else "; ".join(re2_all_errs),
    )

    for trial in ("kde-selected", "kde-reapplied"):
        for stack in stacks:
            r = rows.get((trial, stack))
            if not r:
                add(stack, trial, "FAIL", "missing row")
            elif stack in ("gtk3", "gtk4"):
                ok = r.get("theme") == "DiscoveryKde" and r.get("probe") == "#123456" and r.get("ind_theme") == "#1188ee"
                add(
                    stack,
                    trial,
                    "PASS" if ok else "FAIL",
                    f"theme={r.get('theme')} probe={r.get('probe')} ind_theme={r.get('ind_theme')}",
                )
            else:
                ok = r.get("theme") == "Adwaita-empty" and r.get("probe") != "#123456" and r.get("ind_theme") != "#1188ee"
                add(
                    stack,
                    trial,
                    "PASS" if ok else "FAIL",
                    f"theme={r.get('theme')} probe={r.get('probe')} (clean Adw unaffected by named theme)",
                )

    # 6. Live preference changes & portal backend checks (AUDIT.md #153)
    if mode == "broadway":
        btrace = parse_step_sections(root / "broadway-trace.log")
        bt_errs: list[str] = []
        if list(btrace) != [f"STEP {i}" for i in range(1, 5)]:
            bt_errs.append("missing-or-out-of-order-broadway-steps")
        else:
            for step, reqs in (
                ("STEP 1", ("STEP1_RC=0", "gsettings_gtk_theme='DiscoveryGSettingsLive'")),
                ("STEP 2", ("STEP2_RC=0", "gsettings_color_scheme='prefer-dark'")),
                ("STEP 3", ("STEP3_RC=0", "gsettings_high_contrast=true")),
                ("STEP 4", ("STEP4_RC=0", "gsettings_gtk_theme='DiscoveryKde'", "gsettings_high_contrast=false", "gsettings_color_scheme='prefer-light'")),
            ):
                check_trace_values(step, btrace[step], reqs, bt_errs)
        add(
            "session",
            "broadway-gsettings-step-trace",
            "PASS" if not bt_errs else "FAIL",
            "4/4 GSettings steps + return-to-baseline verified" if not bt_errs else "; ".join(bt_errs),
        )

        for stack in stacks:
            evs = load_watch(root / f"watch-broadway-{stack}.log")
            tags = [e.get("tag", "") for e in evs]
            polls = sum(1 for t in tags if t == "poll")
            has_init = bool(evs and tags[0] == "init")
            has_final = bool(evs and tags[-1] == "final" and evs[-1].get("png_ok") == "1")
            w_errs: list[str] = []
            if not has_init:
                w_errs.append("missing-init")
            if polls < 4:
                w_errs.append(f"polls={polls}<4")
            if not has_final:
                w_errs.append("missing-final-png")
            if any(e.get("css_errors") != "0" for e in evs):
                w_errs.append("css-errors")

            if stack == "adw":
                check_step_polls(evs, {"adw_hc": "0 0 1 0", "adw_dark": "0 0 0 0"}, w_errs)
                hc_seq = collapse_runs([e.get("adw_hc", "") for e in evs])
                c_seq = collapse_runs([e.get("gtk4_contrast", "") for e in evs])
                if hc_seq != ["0", "1", "0"]:
                    w_errs.append(f"adw_hc={hc_seq}!=0->1->0")
                if c_seq != ["1", "2", "1"]:
                    w_errs.append(f"gtk4_contrast={c_seq}!=1->2->1")
                if "notify:adw:high-contrast" not in tags:
                    w_errs.append("missing-notify:adw:high-contrast")
                if any(e.get("theme") != "Adwaita-empty" for e in evs):
                    w_errs.append("theme!=Adwaita-empty")
                add(
                    stack,
                    "live-watch-broadway",
                    "PASS" if not w_errs else "FAIL",
                    f"events={len(evs)} polls={polls} adw_hc=0->1->0 gtk4_contrast=1->2->1 (broadway-no-portal-cs/accent)"
                    if not w_errs
                    else "; ".join(w_errs),
                )
            else:
                if any(e.get("theme") != "DiscoveryKde" or e.get("probe") != "#123456" for e in evs):
                    w_errs.append("unexpected-theme-drift-on-broadway")
                add(
                    stack,
                    "live-watch-broadway",
                    "PASS" if not w_errs else "FAIL",
                    f"events={len(evs)} polls={polls} theme=DiscoveryKde steady (measured-broadway-gsettings-ignored)"
                    if not w_errs
                    else "; ".join(w_errs),
                )

        add(
            "portal",
            "wayland-kwin-and-portal-backends",
            "BLOCKED",
            "broadway mode has no virtual KWin/Wayland compositor; run `dev/gtk-discovery.sh plasma` in user terminal",
        )
        add(
            "portal",
            "live-portal-color-scheme-and-contrast",
            "BLOCKED",
            "requires virtual KWin + dbus-update-activation-environment WAYLAND_DISPLAY",
        )
        add(
            "ffmpeg",
            "ffmpeg-converter-gtk-wayland",
            "BLOCKED",
            "requires virtual KWin Wayland session (`dev/gtk-discovery.sh plasma`)",
        )
    else:
        ptxt = (root / "portal.log").read_text(encoding="utf-8", errors="replace") if (root / "portal.log").is_file() else ""
        fe_out = (
            (root / "portal-frontend.out").read_text(encoding="utf-8", errors="replace")
            if (root / "portal-frontend.out").is_file()
            else ""
        )
        kde_up = "BACKEND_kde_READALL=OK" in ptxt and "BACKEND_kde_OWNER=boolean true" in ptxt
        gtk_up = "BACKEND_gtk_READALL=OK" in ptxt and "BACKEND_gtk_OWNER=boolean true" in ptxt
        fe_up = (
            "FRONTEND_READALL=OK" in ptxt
            and '"org.freedesktop.appearance"' in fe_out
            and '"color-scheme"' in fe_out
            and '"accent-color"' in fe_out
            and '"contrast"' in fe_out
        )
        if kde_up and gtk_up and fe_up:
            add("portal", "dual-backends-and-frontend", "PASS", "kde=OK gtk=OK frontend=OK appearance={color-scheme,accent-color,contrast}")
        else:
            add(
                "portal",
                "dual-backends-and-frontend",
                "BLOCKED",
                f"kde_up={kde_up} gtk_up={gtk_up} frontend_up={fe_up}",
            )

        # Verify source -> backend -> frontend step trace including return to baseline (AUDIT.md #153)
        ptrace = parse_step_sections(root / "portal-trace.log")
        pt_errs: list[str] = []
        if list(ptrace) != [f"STEP {i}" for i in range(7)]:
            pt_errs.append("missing-or-out-of-order-portal-steps")
        else:
            step_reqs = (
                (
                    "STEP 0",
                    (
                        "kde_backend_cs=v u 2",
                        "frontend_cs=v v u 2",
                        "kde_backend_accent=v (ddd) 0.8 0.8 1",
                        "frontend_accent=v v (ddd) 0.8 0.8 1",
                        "gtk_backend_contrast=v u 0",
                        "frontend_contrast=v v u 0",
                        "gsettings_gtk_theme='DiscoveryKde'",
                    ),
                ),
                (
                    "STEP 1",
                    (
                        "STEP1_APPLY_RC=0",
                        "kde_backend_cs=v u 1",
                        "frontend_cs=v v u 1",
                        "kde_backend_accent=v (ddd) 0.239216 0.682353 0.913725",
                        "frontend_accent=v v (ddd) 0.239216 0.682353 0.913725",
                    ),
                ),
                (
                    "STEP 2",
                    (
                        "STEP2_APPLY_RC=0",
                        "kde_backend_cs=v u 2",
                        "frontend_cs=v v u 2",
                        "kde_backend_accent=v (ddd) 0.8 0.8 1",
                        "frontend_accent=v v (ddd) 0.8 0.8 1",
                    ),
                ),
                (
                    "STEP 3",
                    (
                        "STEP3_RC=0",
                        "gtk_backend_contrast=v u 1",
                        "frontend_contrast=v v u 1",
                    ),
                ),
                (
                    "STEP 4",
                    (
                        "STEP4_RC=0",
                        "gtk_backend_contrast=v u 0",
                        "frontend_contrast=v v u 0",
                    ),
                ),
                (
                    "STEP 5",
                    (
                        "STEP5_RC=0",
                        "gsettings_gtk_theme='DiscoveryGSettingsLive'",
                    ),
                ),
                (
                    "STEP 6",
                    (
                        "STEP6_RC=0",
                        "gsettings_gtk_theme='DiscoveryKde'",
                    ),
                ),
            )
            for step, reqs in step_reqs:
                check_trace_values(step, ptrace[step], reqs, pt_errs)
        add(
            "portal",
            "preference-step-trace",
            "PASS" if not pt_errs else ("FAIL" if (kde_up and gtk_up and fe_up) else "BLOCKED"),
            "7/7 steps (baseline->dark->platinum->hc-on->hc-off->live-theme->baseline) source+backend+frontend verified"
            if not pt_errs
            else "; ".join(pt_errs),
        )

        # Verify ordered Adw live transitions + accent assertion + return to baseline
        adw_evs = load_watch(root / "watch-plasma-adw.log")
        adw_tags = [e.get("tag", "") for e in adw_evs]
        adw_polls = sum(1 for t in adw_tags if t == "poll")
        adw_cs_errs: list[str] = []
        if not adw_evs or adw_tags[0] != "init":
            adw_cs_errs.append("missing-init")
        if adw_polls < 6:
            adw_cs_errs.append(f"polls={adw_polls}<6")
        if not adw_evs or adw_tags[-1] != "final" or adw_evs[-1].get("png_ok") != "1":
            adw_cs_errs.append("missing-final-png")
        if any(e.get("theme") != "Adwaita-empty" for e in adw_evs):
            adw_cs_errs.append("theme!=Adwaita-empty")
        if any(e.get("adw_sys_cs") != "1" or e.get("adw_sys_acc") != "1" for e in adw_evs):
            adw_cs_errs.append("portal-support-flag!=1")
        if any(e.get("css_errors") != "0" for e in adw_evs):
            adw_cs_errs.append("css-errors")

        check_step_polls(adw_evs, {
            "adw_dark": "1 0 0 0 0 0",
            "adw_accent_enum": "0 7 7 7 7 7",
            "adw_hc": "0 0 1 0 0 0",
            "gtk4_color_scheme": "2 3 3 3 3 3",
            "gtk4_contrast": "1 1 2 1 1 1",
        }, adw_cs_errs)
        dark_seq = collapse_runs([e.get("adw_dark", "") for e in adw_evs])
        g4cs_seq = collapse_runs([e.get("gtk4_color_scheme", "") for e in adw_evs])
        acc_seq = collapse_runs(
            [
                f"{e.get('adw_accent_nick')}({e.get('adw_accent_enum')})/{e.get('adw_accent_rgba')}"
                for e in adw_evs
            ]
        )
        if dark_seq != ["0", "1", "0"]:
            adw_cs_errs.append(f"adw_dark={dark_seq}!=0->1->0")
        if g4cs_seq != ["3", "2", "3"]:
            adw_cs_errs.append(f"gtk4_cs={g4cs_seq}!=3->2->3")
        expected_acc = [
            "purple(7)/rgb(145,65,172)",
            "blue(0)/rgb(53,132,228)",
            "purple(7)/rgb(145,65,172)",
        ]
        if acc_seq != expected_acc:
            adw_cs_errs.append(f"accent={acc_seq}!={expected_acc}")
        if "notify:adw:dark" not in adw_tags:
            adw_cs_errs.append("missing-notify:adw:dark")
        if "notify:adw:accent-color" not in adw_tags:
            adw_cs_errs.append("missing-notify:adw:accent-color")

        add(
            "adw",
            "live-portal-color-scheme-and-accent",
            "PASS" if not adw_cs_errs else ("FAIL" if (kde_up and fe_up) else "BLOCKED"),
            "adw_dark=0->1->0 accent=purple(7)/rgb(145,65,172)->blue(0)/rgb(53,132,228)->purple(7)/rgb(145,65,172)"
            if not adw_cs_errs
            else "; ".join(adw_cs_errs),
        )

        adw_hc_errs: list[str] = []
        hc_seq = collapse_runs([e.get("adw_hc", "") for e in adw_evs])
        g4c_seq = collapse_runs([e.get("gtk4_contrast", "") for e in adw_evs])
        if hc_seq != ["0", "1", "0"]:
            adw_hc_errs.append(f"adw_hc={hc_seq}!=0->1->0")
        if g4c_seq != ["1", "2", "1"]:
            adw_hc_errs.append(f"gtk4_contrast={g4c_seq}!=1->2->1")
        if "notify:adw:high-contrast" not in adw_tags:
            adw_hc_errs.append("missing-notify:adw:high-contrast")
        add(
            "adw",
            "live-portal-high-contrast",
            "PASS" if not adw_hc_errs else ("FAIL" if (gtk_up and fe_up) else "BLOCKED"),
            "adw_hc=0->1->0 gtk4_contrast=1->2->1 notify=OK" if not adw_hc_errs else "; ".join(adw_hc_errs),
        )

        # Verify ordered plain GTK 4 live transitions + return to baseline
        g4_evs = load_watch(root / "watch-plasma-gtk4.log")
        g4_tags = [e.get("tag", "") for e in g4_evs]
        g4_polls = sum(1 for t in g4_tags if t == "poll")
        g4_errs: list[str] = []
        check_step_polls(g4_evs, {
            "gtk4_color_scheme": "2 3 3 3 3 3",
            "gtk4_contrast": "1 1 2 1 1 1",
            "theme": "DiscoveryKde DiscoveryKde DiscoveryKde DiscoveryKde DiscoveryGSettingsLive DiscoveryKde",
            "probe": "#123456 #123456 #123456 #123456 #334455 #123456",
        }, g4_errs)
        if not g4_evs or g4_tags[0] != "init":
            g4_errs.append("missing-init")
        if g4_polls < 6:
            g4_errs.append(f"polls={g4_polls}<6")
        if not g4_evs or g4_tags[-1] != "final" or g4_evs[-1].get("png_ok") != "1":
            g4_errs.append("missing-final-png")
        if any(e.get("css_errors") != "0" for e in g4_evs):
            g4_errs.append("css-errors")
        if collapse_runs([e.get("gtk4_color_scheme", "") for e in g4_evs]) != ["3", "2", "3"]:
            g4_errs.append(f"gtk4_cs={collapse_runs([e.get('gtk4_color_scheme', '') for e in g4_evs])}!=3->2->3")
        if collapse_runs([e.get("gtk4_contrast", "") for e in g4_evs]) != ["1", "2", "1"]:
            g4_errs.append(f"gtk4_contrast={collapse_runs([e.get('gtk4_contrast', '') for e in g4_evs])}!=1->2->1")
        if collapse_runs([e.get("theme", "") for e in g4_evs]) != ["DiscoveryKde", "DiscoveryGSettingsLive", "DiscoveryKde"]:
            g4_errs.append(f"theme={collapse_runs([e.get('theme', '') for e in g4_evs])}")
        if collapse_runs([e.get("probe", "") for e in g4_evs]) != ["#123456", "#334455", "#123456"]:
            g4_errs.append(f"probe={collapse_runs([e.get('probe', '') for e in g4_evs])}")
        if collapse_runs([e.get("ind_theme", "") for e in g4_evs]) != ["#1188ee", "#33cc55", "#1188ee"]:
            g4_errs.append(f"ind_theme={collapse_runs([e.get('ind_theme', '') for e in g4_evs])}")
        for req_notify in (
            "notify:settings:gtk-interface-color-scheme",
            "notify:settings:gtk-interface-contrast",
            "notify:settings:gtk-theme-name",
        ):
            if req_notify not in g4_tags:
                g4_errs.append(f"missing-{req_notify}")
        add(
            "gtk4",
            "live-watch-plasma",
            "PASS" if not g4_errs else "FAIL",
            f"events={len(g4_evs)} polls={g4_polls} cs=3->2->3 contrast=1->2->1 theme=DiscoveryKde->DiscoveryGSettingsLive->DiscoveryKde"
            if not g4_errs
            else "; ".join(g4_errs),
        )

        # Verify ordered GTK 3 live transitions + explicit prefer_dark=0 limitation check
        g3_evs = load_watch(root / "watch-plasma-gtk3.log")
        g3_tags = [e.get("tag", "") for e in g3_evs]
        g3_polls = sum(1 for t in g3_tags if t == "poll")
        g3_errs: list[str] = []
        check_step_polls(g3_evs, {
            "theme": "DiscoveryKde DiscoveryKde HighContrast DiscoveryKde DiscoveryGSettingsLive DiscoveryKde",
        }, g3_errs)
        if not g3_evs or g3_tags[0] != "init":
            g3_errs.append("missing-init")
        if g3_polls < 6:
            g3_errs.append(f"polls={g3_polls}<6")
        if not g3_evs or g3_tags[-1] != "final" or g3_evs[-1].get("png_ok") != "1":
            g3_errs.append("missing-final-png")
        if any(e.get("css_errors") != "0" for e in g3_evs):
            g3_errs.append("css-errors")
        expected_g3_themes = [
            "DiscoveryKde",
            "HighContrast",
            "DiscoveryKde",
            "DiscoveryGSettingsLive",
            "DiscoveryKde",
        ]
        g3_themes = collapse_runs([e.get("theme", "") for e in g3_evs])
        if g3_themes != expected_g3_themes:
            g3_errs.append(f"theme={g3_themes}!={expected_g3_themes}")
        g3_probes = collapse_runs([e.get("probe", "") for e in g3_evs])
        if (
            len(g3_probes) != 5
            or g3_probes[0] != "#123456"
            or g3_probes[1] in ("", "#123456", "#334455")
            or g3_probes[2] != "#123456"
            or g3_probes[3] != "#334455"
            or g3_probes[4] != "#123456"
        ):
            g3_errs.append(f"probe={g3_probes}")
        g3_inds = collapse_runs([e.get("ind_theme", "") for e in g3_evs])
        if (
            len(g3_inds) != 5
            or g3_inds[0] != "#1188ee"
            or g3_inds[1] in ("", "#1188ee", "#33cc55")
            or g3_inds[2] != "#1188ee"
            or g3_inds[3] != "#33cc55"
            or g3_inds[4] != "#1188ee"
        ):
            g3_errs.append(f"ind_theme={g3_inds}")
        if "notify:settings:gtk-theme-name" not in g3_tags:
            g3_errs.append("missing-notify:settings:gtk-theme-name")
        if any("prefer_dark" not in e for e in g3_evs):
            g3_errs.append("missing-prefer_dark-field")
        pd_vals = sorted({e.get("prefer_dark", "") for e in g3_evs})
        if pd_vals != ["0"]:
            g3_errs.append(f"unexpected-prefer_dark={pd_vals}")
        hc_probe = g3_probes[1] if len(g3_probes) >= 2 else "?"
        add(
            "gtk3",
            "live-watch-plasma",
            "PASS" if not g3_errs else "FAIL",
            f"events={len(g3_evs)} polls={g3_polls} theme=DiscoveryKde->HighContrast({hc_probe})->DiscoveryKde->DiscoveryGSettingsLive->DiscoveryKde "
            f"prefer_dark=0_all_rows(gtk3-portal-limitation)"
            if not g3_errs
            else "; ".join(g3_errs),
        )

        ff_status, ff_detail = check_ffmpeg_evidence(root, shots_dir, stock_pngs)
        add("ffmpeg", "ffmpeg-converter-gtk-wayland", ff_status, ff_detail)

    # Summary & observed verdict
    n_pass = sum(1 for _, _, s, _ in checks if s == "PASS")
    n_fail = sum(1 for _, _, s, _ in checks if s == "FAIL")
    n_blocked = sum(1 for _, _, s, _ in checks if s == "BLOCKED")

    print(f"=== GTK Milestone 1 Verification ({mode}) ===")
    for area, name, status, detail in checks:
        print(f"{status:<7} {area:<7} {name:<36} {detail}")
    print()
    if n_fail > 0:
        verdict = "FAIL"
        rc = 1
    elif n_blocked > 0:
        verdict = "BLOCKED" if mode == "plasma" else "PARTIAL_BROADWAY_ONLY"
        rc = 2 if mode == "plasma" else 0
    else:
        verdict = "PASS"
        rc = 0
    print(f"VERDICT={verdict} pass={n_pass} fail={n_fail} blocked={n_blocked} evidence={root}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
