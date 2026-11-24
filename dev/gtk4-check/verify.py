#!/usr/bin/env python3
"""Compare the GTK 4 control slice with 1× references and verify native behavior."""
# SPDX-License-Identifier: BSD-2-Clause

import configparser
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

PROJECT = Path(__file__).resolve().parents[2]
CHROME_BANDS = (
    ("push-normal", "button-default-pressed.png", 617, 513, 70, 20, 4, 4, 70),
    ("push-pressed", "button-push-pressed.png", 641, 469, 70, 20, 4, 4, 56),
    ("push-disabled", "dialog-file-open.png", 851, 335, 80, 20, 4, 4, 80),
    ("push-default", "dialog-file-open.png", 848, 435, 86, 26, 8, 7, 86),
    ("push-default-pressed", "button-default-pressed.png", 697, 510, 78, 26, 8, 8, 56),
    ("entry-normal", "appearance-3-fonts-clean.png", 846, 346, 30, 26, 5, 5, 30),
    ("entry-focused", "appearance-3-fonts-clean.png", 846, 432, 30, 26, 5, 5, 30),
)
INDICATORS = (
    ("check-off", "controls-general-controls.png", 550, 327, 14, 12),
    ("check-on", "controls-general-controls.png", 550, 280, 14, 12),
    ("check-off-pressed", "checkbox-pressed.png", 550, 327, 14, 10),
    ("check-on-disabled", "controls-memory.png", 553, 511, 14, 12),
    ("radio-off", "controls-general-controls.png", 553, 534, 12, 12),
    ("radio-on", "controls-general-controls.png", 553, 552, 12, 12),
    ("radio-off-pressed", "radio-pressed.png", 553, 534, 12, 8),
    ("radio-off-disabled", "controls-monitors.png", 732, 405, 12, 12),
)
CONTROLS = {
    "selected", "entry", "entry-disabled", "check", "checked", "mixed", "check-disabled",
    "radio-one", "radio-two", "radio-mixed", "cancel", "button-disabled", "continue",
}
INDICATOR_STATES = {
    "check-off-indicator": "check-off", "check-on-indicator": "check-on",
    "mixed-indicator": "check-mixed", "radio-off-indicator": "radio-off",
    "radio-on-indicator": "radio-on", "mixed-radio-indicator": "radio-mixed",
}
FOCUS_CONTROLS = (("button", "cancel"), ("default", "continue"), ("check", "check"), ("radio", "radio-one"))
ACTIVE_SELECTION = (204, 204, 255)
INACTIVE_SELECTION = (220, 220, 239)
FOCUS = (102, 102, 204)
PARSER_DIAGNOSTIC = re.compile(r"Theme parser (?:error|warning)|(?:Gtk|Gdk|Gsk|GLib(?:-GObject)?)-(?:CRITICAL|WARNING)", re.I)


def read_report(path):
    props = {}
    controls = {}
    for line in path.read_text().splitlines():
        name, *fields = line.split()
        if "=" in name:
            props.update(field.split("=", 1) for field in line.split())
        else:
            controls[name] = tuple(map(int, fields))
    return props, controls


def crop(image, bounds):
    x, y, width, height = bounds[:4]
    assert 0 <= x < x + width <= image.width
    assert 0 <= y < y + height <= image.height
    return image.crop((x, y, x + width, y + height))


def color_count(image, color):
    return sum(count for count, pixel in image.getcolors(image.width * image.height) if pixel == color)


def clipped_controls(image, controls):
    clipped = []
    for name in sorted(CONTROLS):
        x, y, w, h, natural_w, natural_h = controls.get(name, (0,) * 6)
        if (w < max(18, natural_w) or h < max(18, natural_h)
                or x < 0 or y < 0 or x + w > image.width or y + h > image.height):
            clipped.append(name)
    return clipped


def indicator_artwork(sprite, pressed=False):
    name = "radio-off" if sprite == "radio-mixed" else sprite
    suffix = "-pressed" if pressed else ""
    assets = PROJECT / "gtk/Platinum/gtk-3.0/assets"
    with Image.open(assets / f"{name}{suffix}.png") as asset:
        ink = asset.convert("RGBA")
    expected = Image.new("RGB", ink.size, "#dddddd")
    expected.paste(ink, mask=ink.getchannel("A"))
    if sprite == "radio-mixed":
        expected.paste("black", (3, 5, 9, 7))
    return expected


def verify_scale(root, scale):
    props, controls = read_report(root / "dialog.txt")
    widget = Image.open(root / "dialog.png").convert("RGB")
    output = Image.open(root / "output.png").convert("RGB")
    scale_match = re.search(r"^\s*Scale:\s*([0-9.]+)\s*$", (root / "output.txt").read_text(), re.M)
    bounds = output.getbbox()
    clipped = clipped_controls(widget, controls)
    if (not scale_match or float(scale_match[1]) != scale or props.get("surface_scale") != str(scale)
            or props.get("real_active") != "1" or props.get("renderer_override") != "none"
            or props.get("theme") != "Platinum" or props.get("theme_override") != "none"
            or props.get("backend") != "GdkWaylandDisplay" or not props.get("renderer")
            or output.size != (1024, 768) or not bounds or clipped):
        return False, f"surface={props.get('surface_scale')} output={output.size} clipped={clipped}"

    x, y, right, bottom = bounds
    actual = (right - x, bottom - y)
    if (any(abs(pixels - logical * scale) > 1 for pixels, logical in zip(actual, widget.size))
            or x <= 0 or y <= 0 or right >= output.width or bottom >= output.height):
        return False, f"dialog bounds={bounds}, logical size={widget.size}"

    if scale == 2:
        for control, sprite in INDICATOR_STATES.items():
            sx, sy, w, h = controls[control][:4]
            actual_sprite = crop(output, (x + 2 * sx, y + 2 * sy, 2 * w, 2 * h))
            expected = indicator_artwork(sprite)
            expected = expected.resize((2 * expected.width, 2 * expected.height), Image.Resampling.NEAREST)
            if expected.size != actual_sprite.size or ImageChops.difference(expected, actual_sprite).getbbox():
                return False, f"{control} differs on the 2× compositor output"

    sx, sy, width, height = controls["selected"][:4]
    selected = crop(output, (x + round(sx * scale), y + round(sy * scale),
                             round(width * scale), round(height * scale)))
    lavender = color_count(selected, ACTIVE_SELECTION)
    focus = color_count(selected, FOCUS)
    return lavender > 200 and focus > 100, f"surface={scale} dialog={actual} {lavender=} {focus=}"


def main(root, wayland):
    checks = []

    def record(passed, name, detail=""):
        checks.append(bool(passed))
        print(f"{'ok' if passed else 'FAIL':<5} {name:<34} {detail}")

    def compare(name, reference, rx, ry, ox, oy, width, height):
        size = f"{width},{height}"
        args = [
            sys.executable, "-I", str(PROJECT / "tools/compare.py"), "diff",
            f"{PROJECT / 'reference' / reference}@{rx},{ry},{size}",
            f"{root / 'chrome.png'}@{ox},{oy},{size}", "--tolerance", "0",
            "--out", str(root / (name + ".png")),
        ]
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        result = next((line for line in proc.stdout.splitlines() if line.startswith("differing")), "")
        record(proc.returncode == 0, name, result or proc.stderr.strip())

    if not (root / "complete").is_file():
        record(False, "session-completed", "missing completion marker")
        return 1
    record(True, "session-completed")

    chrome, samples = read_report(root / "chrome.txt")
    dialog, controls = read_report(root / "dialog.txt")
    backend = "GdkWaylandDisplay" if wayland else "GdkBroadwayDisplay"
    for state, report in (("chrome", chrome), ("dialog", dialog)):
        record(report.get("theme") == "Platinum" and report.get("backend") == backend
               and report.get("theme_override") == "none",
               state + "-named-theme", f"{report.get('theme')} / {report.get('backend')}")
    session_log = (root / "session.log").read_text()
    app_logs = [path.read_text() for path in root.glob("factory-*.log")]
    diagnostics = [line.strip() for log in [session_log, *app_logs]
                   for line in log.splitlines() if PARSER_DIAGNOSTIC.search(line)]
    record(not diagnostics, "gtk-css-and-runtime-diagnostics", " | ".join(diagnostics) or "0")

    for name, ref, rx, ry, width, height, edge, bottom, safe_width in CHROME_BANDS:
        ox, oy, w, h, *_ = samples.get(name, (0, 0, 0, 0))
        if (w, h) != (width, height):
            record(False, name + "-geometry", f"{w}×{h}, expected {width}×{height}")
            continue
        right_height = height - edge if safe_width < width else height
        for side, x, y, sw, sh in (
            ("top", 0, 0, width, edge),
            ("bottom", 0, height - bottom, safe_width, bottom),
            ("left", 0, 0, edge, height),
            ("right", width - edge, 0, edge, right_height),
        ):
            compare(f"ref-{name}-{side}", ref, rx + x, ry + y, ox + x, oy + y, sw, sh)

    for name, ref, rx, ry, width, height in INDICATORS:
        ox, oy, w, h, *_ = samples.get(name, (0, 0, 0, 0))
        if w != width or h != 12:
            record(False, name + "-geometry", f"{w}×{h}, expected {width}×12")
            continue
        compare("ref-" + name, ref, rx, ry, ox, oy, width, height)

    image = Image.open(root / "dialog.png").convert("RGB")
    clipped = clipped_controls(image, controls)
    record(not clipped, "dialog-natural-allocations", ", ".join(clipped) or f"{len(CONTROLS)} controls")
    record(all(dialog.get(key) == "1" for key in ("default_clicks", "cancel_clicks", "toggle", "radio_changed")),
           "dialog-native-control-activation")

    disabled_labels = [dialog.get(f"disabled-{role}-label") for role in ("custom", "push", "check", "radio")]
    record(all(color == "rgb(119,119,119)" for color in disabled_labels),
           "dialog-disabled-label-colors", str(disabled_labels))

    selected = crop(image, controls["selected"])
    lav = color_count(selected, ACTIVE_SELECTION)
    ring = color_count(selected, FOCUS)
    record(lav > 200 and ring > 100, "dialog-selection-and-entry-focus", f"{lav=} {ring=}")

    for name in ("mixed-indicator", "mixed-radio-indicator"):
        indicator = crop(image, controls[name])
        bar = indicator.crop((3, 5, 9, 7))
        record(color_count(bar, (0, 0, 0)) == 12, "dialog-" + name + "-6x2-bar")

    shots = {state: Image.open(root / (state + ".png")).convert("RGB")
             for state in ("dialog", "hover", "pressed", "pressed-hover")}
    for control, sprite in INDICATOR_STATES.items():
        failed = []
        for state, shot in shots.items():
            expected = indicator_artwork(sprite, pressed=state.startswith("pressed"))
            observed = crop(shot, controls[control])
            if observed.size != expected.size or ImageChops.difference(expected, observed).getbbox():
                failed.append(state)
        record(not failed, control + "-artwork", ", ".join(failed) or "4 states exact")

    for state, control in FOCUS_CONTROLS:
        focus_image = Image.open(root / f"focus-{state}.png").convert("RGB")
        focus_pixels = color_count(crop(focus_image, controls[control]), FOCUS)
        record(dialog.get(f"focus-{state}") == "1" and focus_pixels > 20,
               f"dialog-{state}-keyboard-focus", f"{focus_pixels} focus pixels")
        if wayland:
            inactive = Image.open(root / f"backdrop-{state}.png").convert("RGB")
            reassigned = Image.open(root / f"backdrop-reassigned-{state}.png").convert("RGB")
            remaining = color_count(crop(inactive, controls[control]), FOCUS)
            after_reassignment = color_count(crop(reassigned, controls[control]), FOCUS)
            record(dialog.get(f"backdrop-{state}") == "1"
                   and dialog.get(f"backdrop-reassigned-{state}") == "1"
                   and dialog.get(f"backdrop-covered-{state}") == "1"
                   and remaining == after_reassignment == 0,
                   f"dialog-{state}-backdrop-focus",
                   f"{remaining=} {after_reassignment=} focus_flags={dialog.get(f'backdrop-focus-flags-{state}')}")

    if wayland:
        backdrop = Image.open(root / "dialog-backdrop.png").convert("RGB")
        selected = crop(backdrop, controls["selected"])
        muted = color_count(selected, INACTIVE_SELECTION)
        record(dialog.get("backdrop-entry") == "1" and muted == lav
               and color_count(selected, ACTIVE_SELECTION) == color_count(selected, FOCUS) == 0,
               "dialog-real-backdrop-selection", f"{muted} muted pixels")

        platinum = Image.open(root / "factory-Platinum.png").convert("RGB")
        stock = Image.open(root / "factory-Adwaita.png").convert("RGB")
        p_lav = color_count(platinum, ACTIVE_SELECTION)
        s_lav = color_count(stock, ACTIVE_SELECTION)
        p_bg = color_count(platinum, (221, 221, 221)) / (platinum.width * platinum.height)
        s_bg = color_count(stock, (221, 221, 221)) / (stock.width * stock.height)
        record(p_lav > 20 and p_lav > 5 * s_lav and p_bg > s_bg + 0.1,
               "widget-factory-named-theme", f"lavender {p_lav}/{s_lav}; gray {p_bg:.1%}/{s_bg:.1%}")

        settings = configparser.ConfigParser(interpolation=None)
        with (root / "home/.config/gtk-4.0/settings.ini").open() as settings_file:
            settings.read_file(settings_file)
        selected_theme = (root / "gsettings-theme.txt").read_text().strip()
        record(not settings.has_option("Settings", "gtk-theme-name") and selected_theme == "'Platinum'",
               "wayland-gsettings-only", selected_theme)

        captures = {}
        geometry = {}
        native_reports = [chrome, dialog]
        for theme in ("Adwaita", "Platinum"):
            directory = root / ("controls-" + theme)
            for probe in ("contrast", "composites"):
                props, samples = read_report(directory / (probe + ".txt"))
                if probe == "composites":
                    geometry[theme] = samples
                else:
                    preference = props
                native_reports.append(props)
                record(props.get("theme") == theme and props.get("backend") == backend,
                       f"{theme}-{probe}-discovery")
            states = ("initial", "high", "restored")
            for state in states:
                captures[theme, state] = Image.open(directory / (state + ".png")).convert("RGB")
            record(all(preference.get("contrast-" + state) == ("2" if state == "high" else "1")
                       for state in states), theme + "-live-contrast-preference")
            captures[theme, "composites"] = Image.open(directory / "composites.png").convert("RGB")

        def identical(a, b):
            return a.size == b.size and ImageChops.difference(a, b).getbbox() is None

        p = captures["Platinum", "composites"]
        stock = captures["Adwaita", "composites"]
        for role in ("switcher", "linked", "toolbar", "nested-toolbar", "osd"):
            expected = crop(stock, geometry["Adwaita"][role])
            observed = crop(p, geometry["Platinum"][role])
            ink = expected.width * expected.height - color_count(expected, (255, 255, 255))
            record(geometry["Platinum"][role] == geometry["Adwaita"][role]
                   and identical(observed, expected) and ink > 10,
                   f"stock-{role}-button-role", f"{expected.width}×{expected.height}, {ink} painted pixels")

        initial, high, restored = (captures["Platinum", state] for state in ("initial", "high", "restored"))
        stock_high = captures["Adwaita", "high"]
        record(identical(high, stock_high) and len(high.getcolors(high.width * high.height)) > 8
               and color_count(high, FOCUS) == color_count(high, ACTIVE_SELECTION) == 0
               and identical(initial, restored) and min(color_count(restored, ACTIVE_SELECTION),
                                                        color_count(restored, FOCUS)) > 100,
               "wayland-high-contrast-roundtrip", "live window and stock high-contrast control")

        record(all(report.get("renderer") and report.get("renderer_override") == "none"
                   and report.get("theme_override") == "none" and report.get("surface_scale") == "1"
                   for report in native_reports),
               "wayland-native-renderer-1x",
               ", ".join(report.get("renderer", "missing") for report in native_reports))

        for scale in (1.5, 2):
            passed, detail = verify_scale(root / f"scale-{scale}", scale)
            record(passed, f"wayland-scale-{scale * 100:g}pct", detail)

    print(f"\n{sum(checks)} of {len(checks)} GTK 4 Milestone 4 slice checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in {"broadway", "plasma"}:
        raise SystemExit(f"usage: {sys.argv[0]} EVIDENCE broadway|plasma")
    raise SystemExit(main(Path(sys.argv[1]), sys.argv[2] == "plasma"))
