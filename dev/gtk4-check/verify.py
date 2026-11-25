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
# The nested virtual KWin output sometimes reports a presentation time one
# frame off. GDK's frame clock warns; it is compositor timing, not styling.
COMPOSITOR_TIMING = re.compile(r"Gdk-WARNING \*\*: [0-9:.]+: Duplicate call to gdk_frame_timings_presented\(\) "
                               r"with different values: presentation time is [0-9.]+ms off from expected$")


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


def contains_artwork(image, artwork):
    """Locate an exact RGB crop, including its position within each scanline."""
    pixels = image.tobytes()
    first = artwork.crop((0, 0, artwork.width, 1)).tobytes()
    start = 0
    while (offset := pixels.find(first, start)) >= 0:
        start = offset + 1
        y, x = divmod(offset // 3, image.width)
        if offset % 3 or x + artwork.width > image.width or y + artwork.height > image.height:
            continue
        region = image.crop((x, y, x + artwork.width, y + artwork.height))
        if ImageChops.difference(artwork, region).getbbox() is None:
            return True
    return False


def verify_scaled_lists(root, scale):
    directory = root / f"scale-{scale}"
    props, controls = read_report(directory / "menus.txt")
    window = Image.open(directory / "menus-lists.png").convert("RGB")
    screen = Image.open(directory / "lists-output.png").convert("RGB")
    bounds = screen.getbbox()
    if not bounds or props.get("surface_scale") != str(scale) or props.get("renderer_override") != "none":
        return False
    left, top, right, bottom = bounds
    if (min(left, top) <= 0 or right >= screen.width or bottom >= screen.height
            or abs(right - left - window.width * scale) > 1 or abs(bottom - top - window.height * scale) > 1):
        return False
    for name in ("list-row", "column-row"):
        x, y, w, h = controls[name][:4]
        row = crop(screen, (left + round(x * scale), top + round(y * scale), round(w * scale), round(h * scale)))
        if color_count(row, ACTIVE_SELECTION) < row.width * row.height / 2:
            return False
    if scale == 2:
        x, y, w, h = controls["dropdown"][:4]
        glyph = crop(screen, (left + (x + w - 18) * 2, top + (y + (h - 10) // 2) * 2, 28, 20))
        reference = Image.open(PROJECT / "reference/appearance-2-appearance.png").convert("RGB")
        expected = reference.crop((753, 262, 767, 272)).resize(glyph.size, Image.Resampling.NEAREST)
        return ImageChops.difference(glyph, expected).getbbox() is None
    return True


def verify_menus(root, wayland, record, compare):
    props, controls = read_report(root / "menus.txt")
    backend = "GdkWaylandDisplay" if wayland else "GdkBroadwayDisplay"
    record(props.get("backend") == backend and props.get("theme") == "Platinum"
           and props.get("theme_override") == "none" and props.get("surface_scale") == "1"
           and (not wayland or props.get("renderer_override") == "none"), "menus-named-theme")
    record(props.get("interactions") == props.get("sorted") == props.get("scrolled") == "1"
           and props.get("position") == "40", "list-scroll-selection-and-column-sort")
    active = Image.open(root / "menus-lists.png").convert("RGB")
    bx, by, *_ = controls["bar"]
    compare("ref-native-menubar", "menu-file-open.png", 72, 0, bx + 100, by, 7, 20, "menus-lists.png")
    for name, ref, rx, ry, rw in (
        ("dropdown", "appearance-2-appearance.png", 591, 257, 180),
        ("dropdown-disabled", "appearance-4-desktop.png", 710, 451, 194),
    ):
        x, y, w, h = controls[name][:4]
        for side, u, v, dx, dy, width, height in (
            ("top", 8, 0, 8, 0, 36, 3),
            ("bottom", 8, 17, 8, h - 3, 36, 3),
            ("left", 0, 4, 0, 4, 4, 8),
            ("cap", rw - 22, 0, w - 22, 0, 18, 4),
            ("arrows", rw - 18, 5, w - 18, (h - 10) // 2, 14, 10),
        ):
            compare(f"ref-{name}-{side}", ref, rx + u, ry + v, x + dx, y + dy, width, height,
                    "menus-lists.png")
    x, y, w, h = controls["dropdown-rtl"][:4]
    compare("ref-rtl-dropdown-arrows", "appearance-2-appearance.png", 753, 262,
            x + 4, y + (h - 10) // 2, 14, 10, "menus-lists.png")
    x, y, w, h = controls["header"][:4]
    compare("ref-column-header-top", "disclosure-triangles.png", 351, 154,
            x + 8, y, 36, 3, "menus-lists.png")
    compare("ref-column-header-bottom", "disclosure-triangles.png", 351, 172,
            x + 8, y + h - 3, 36, 3, "menus-lists.png")

    for name in ("list-row", "column-row"):
        row = crop(active, controls[name])
        selected = color_count(row, ACTIVE_SELECTION)
        record(selected > row.width * row.height / 2 and color_count(row, (0, 0, 0)) > 0,
               name + "-active", f"{selected} lavender pixels")
        if wayland:
            background = Image.open(root / "lists-backdrop.png").convert("RGB")
            inactive = crop(background, controls[name])
            record(color_count(inactive, INACTIVE_SELECTION) > row.width * row.height / 2
                   and color_count(inactive, ACTIVE_SELECTION) == 0, name + "-backdrop")

    if wayland:
        x, y, w, h = controls["dropdown"][:4]
        compare("ref-open-dropdown-arrows", "popup-open.png", 753, 303, x + w - 18,
                y + (h - 10) // 2, 14, 10, "dropdown-pressed.png")
        menu = Image.open(root / "action-menu.png").convert("RGB")
        selected = crop(menu, controls["menu-item"])
        disabled = crop(menu, controls["menu-disabled"])
        record(color_count(selected, (51, 51, 153)) > selected.width * selected.height / 2
               and color_count(selected, (255, 255, 255)) > 10
               and color_count(disabled, (119, 119, 119)) > 5 and props.get("toggled") == "1"
               and props.get("menu_closed") == "1", "popover-menu-activation-and-colors")
        mark = crop(menu, controls["menu-check"])
        with Image.open(PROJECT / "gtk/Platinum/gtk-3.0/assets/menu-check-hover.png") as ink:
            expected = Image.new("RGB", ink.size, (51, 51, 153))
            expected.paste(ink, mask=ink.getchannel("A"))
        record(mark.size == expected.size and ImageChops.difference(mark, expected).getbbox() is None,
               "popover-menu-checked-artwork")
        radio = crop(menu, controls["menu-radio"])
        with Image.open(PROJECT / "gtk/Platinum/gtk-3.0/assets/menu-radio-normal.png") as ink:
            expected = Image.new("RGB", ink.size, (221, 221, 221))
            expected.paste(ink, mask=ink.getchannel("A"))
        record(radio.size == expected.size and ImageChops.difference(radio, expected).getbbox() is None
               and props.get("radio_changed") == "1", "popover-radio-artwork-and-choice")
        x, y, w, h = controls["menu-separator"][:4]
        compare("ref-menu-separator", "menu-file-open.png", 60, 102, x + 16, y, 20, 2, "action-menu.png")
        x, y, w, h = controls["submenu-arrow"][:4]
        compare("ref-submenu-arrow", "menu-view-checked.png", 275, 130, x + (w - 6) // 2,
                y + (h - 11) // 2, 6, 11, "action-menu.png")
        record(props.get("submenu_open") == "1", "popover-submenu-navigation")
        corner = Image.open(PROJECT / "reference/disclosure-triangles.png").convert("RGB").crop((343, 154, 349, 160))
        app = Image.open(root / "settings-Platinum.png").convert("RGB")
        stock = Image.open(root / "settings-Adwaita.png").convert("RGB")
        record(contains_artwork(app, corner) and not contains_artwork(stock, corner)
               and color_count(app, ACTIVE_SELECTION) > 200 and color_count(stock, ACTIVE_SELECTION) == 0,
               "settings-app-column-header-and-selection")
        for scale in (1.5, 2):
            record(verify_scaled_lists(root, scale), f"list-and-dropdown-output-{scale * 100:g}pct")
        popup = Image.open(root / "dropdown-open.png").convert("RGB")
        record(color_count(popup, (51, 51, 153)) > 100 and props.get("chosen") == "2"
               and props.get("dropdown_closed") == props.get("overflow") == props.get("filtered") == "1",
               "dropdown-search-overflow-and-selection")


TAB_WIDTHS = (72, 101, 57, 74, 62, 71)


def blue_count(image):
    """Count Lavender-family pixels, including translucent or scaled blends."""
    return sum(n for n, (r, g, b) in image.getcolors(image.width * image.height) if b > r + 40)
LAVENDER = (153, 153, 255)


def tab_crops(name, ref, rx, ry, ox, oy):
    """Yield the GTK 3 Batch 2 tab-row crops for a pane whose top is at (ox, oy)."""
    ty, oty = ry - 21, oy - 21
    yield f"{name}-top", ref, rx + 2, ty, ox + 2, oty, 462, 6
    yield f"{name}-bottom", ref, rx + 2, ty + 17, ox + 2, oty + 17, 462, 10
    yield f"{name}-sides-0", ref, rx + 2, ty + 6, ox + 2, oty + 6, 15, 11
    x = 5
    for i, width in enumerate(TAB_WIDTHS[:5]):
        x += width
        yield f"{name}-sides-{i + 1}", ref, rx + x - 12, ty + 6, ox + x - 12, oty + 6, 24, 11
    x += TAB_WIDTHS[5]
    yield f"{name}-sides-6", ref, rx + x - 12, ty + 6, ox + x - 12, oty + 6, 464 - x + 12, 11


def verify_scaled_ranges(root, scale):
    directory = root / f"scale-{scale}"
    props, controls = read_report(directory / "ranges.txt")
    window = Image.open(directory / "ranges-scaled.png").convert("RGB")
    screen = Image.open(directory / "ranges-output.png").convert("RGB")
    bounds = screen.getbbox()
    if (not bounds or props.get("surface_scale") != str(scale) or props.get("renderer_override") != "none"
            or props.get("real_active") != "1"):
        return False, f"surface={props.get('surface_scale')} active={props.get('real_active')}"
    left, top, right, bottom = bounds
    if (min(left, top) <= 0 or right >= screen.width or bottom >= screen.height
            or abs(right - left - window.width * scale) > 1 or abs(bottom - top - window.height * scale) > 1):
        return False, f"bounds={bounds} logical={window.size}"

    def physical(name):
        x, y, w, h = controls[name][:4]
        return crop(screen, (left + round(x * scale), top + round(y * scale), round(w * scale), round(h * scale)))

    lavender = color_count(physical("progress"), LAVENDER) + color_count(physical("scrollbar"), LAVENDER)
    if lavender < 400 * scale:
        return False, f"{lavender} lavender pixels"
    if scale != 2:
        return True, f"{lavender} lavender pixels"

    # @2 artwork is the 1× artwork doubled, so 200% must equal the doubled reference.
    def doubled(ref, x, y, w, h):
        image = Image.open(PROJECT / "reference" / ref).convert("RGB").crop((x, y, x + w, y + h))
        return image.resize((2 * w, 2 * h), Image.Resampling.NEAREST)

    px, py = controls["pane"][:2]
    py -= 3
    sx, sy = controls["slider"][:2]
    bx, by = controls["progress"][:2]
    failed = []
    regions = [
        ("slider", doubled("controls-general-controls.png", 726, 438, 91, 23), sx, sy),
        ("progress", doubled("progress-determinate-55.png", 590, 276, 188, 14), bx, by),
    ]
    for name, ref, rx, ry, ox, oy, w, h in tab_crops("tabs", "appearance-2-appearance.png", 469, 235, px, py):
        regions.append((name, doubled(ref, rx, ry, w, h), ox, oy))
    for name, expected, x, y in regions:
        actual = crop(screen, (left + 2 * x, top + 2 * y, expected.width, expected.height))
        if ImageChops.difference(actual, expected).getbbox():
            failed.append(name)
    return not failed, ", ".join(failed) or f"{len(regions)} regions equal the doubled reference"


def verify_ranges(root, wayland, record, compare):
    props, controls = read_report(root / "ranges.txt")
    backend = "GdkWaylandDisplay" if wayland else "GdkBroadwayDisplay"
    record(props.get("backend") == backend and props.get("theme") == "Platinum"
           and props.get("theme_override") == "none" and props.get("surface_scale") == "1"
           and (not wayland or props.get("renderer_override") == "none"), "ranges-named-theme")
    sizes = {name: controls[name][2:4] for name in (
        "vbar-top", "vbar-mid", "hbar", "vbar-disabled", "slider", "slider-pressed", "slider-disabled",
        "progress-55", "progress-busy", "progress-vertical-reversed")}
    expected = {"vbar-top": (16, 316), "vbar-mid": (16, 292), "hbar": (358, 16), "vbar-disabled": (16, 160),
                "slider": (91, 23), "slider-pressed": (91, 23), "slider-disabled": (140, 16),
                "progress-55": (188, 14), "progress-busy": (310, 14), "progress-vertical-reversed": (14, 188)}
    natural = all(controls[name][4:6] == expected[name] for name in ("slider", "slider-disabled", "vbar-disabled"))
    record(sizes == expected and natural, "range-natural-sizes",
           ", ".join(f"{n}={w}×{h}" for n, (w, h) in sizes.items() if (w, h) != expected[n]) or "11 controls")

    def at(name, dx=0, dy=0):
        x, y, *_ = controls[name]
        return x + dx, y + dy

    # The GTK 3 crops minus the 31 px of Smart Scrolling arrows GTK 4 lacks.
    for name, ref, rx, ry, (ox, oy), w, h in (
        ("vbar-top", "scroll-vertical-inactive.png", 787, 249, at("vbar-top", 0, 1), 16, 315),
        ("vbar-mid", "disclosure-triangles.png", 492, 175, at("vbar-mid", 0, 1), 16, 291),
        ("hbar", "disclosure-triangles.png", 105, 496, at("hbar", 1), 357, 16),
        ("slider", "controls-general-controls.png", 726, 438, at("slider"), 91, 23),
        ("slider-pressed-thumb", "slider-pressed.png", 764, 438, at("slider-pressed", 38), 15, 16),
        ("slider-disabled", "controls-memory.png", 672, 483, at("slider-disabled"), 140, 16),
        ("progress-55", "progress-determinate-55.png", 590, 276, at("progress-55"), 188, 14),
        ("progress-0", "progress-copy-window.png", 590, 276, at("progress-0"), 188, 14),
        ("progress-busy-stripes", "progress-indeterminate-a.png", 1077, 473, at("progress-busy", 2, 2), 60, 10),
    ):
        compare("ref-gtk4-" + name, ref, rx, ry, ox, oy, w, h, "ranges.png")

    # Top panes start 3 px above the stack: the header draws their first rows.
    for name, ref in (("themes", "appearance-1-themes.png"), ("appearance", "appearance-2-appearance.png"),
                      ("options", "appearance-6-options.png")):
        x, y = at("pane-" + name, 0, -3)
        for crop_args in tab_crops("ref-gtk4-tabs-" + name, ref, 469, 235, x, y):
            compare(*crop_args, "ranges.png")
    x, y = at("pane-themes", 0, -3)
    compare("ref-gtk4-pane-left", "appearance-1-themes.png", 469, 235, x, y, 4, 280, "ranges.png")
    compare("ref-gtk4-pane-right", "appearance-1-themes.png", 931, 235, x + 462, y, 4, 280, "ranges.png")
    compare("ref-gtk4-pane-bottom", "appearance-1-themes.png", 469, 511, x, y + 276, 466, 4, "ranges.png")

    compare("ref-gtk4-level-55", "progress-determinate-55.png", 590, 276, *at("level-55"), 188, 14, "ranges.png")

    image = Image.open(root / "ranges.png").convert("RGB")
    stock = ((0xF5, 0x79, 0x00), (0x35, 0x84, 0xE4), (0x33, 0xD1, 0x7A), (0xEB, 0xE8, 0xE6))
    for name in ("level-low", "level-discrete", "level-vertical"):
        region = crop(image, controls[name])
        record(color_count(region, LAVENDER) > 20 and color_count(region, (187, 187, 187)) > 100
               and sum(color_count(region, c) for c in stock) == 0, name + "-platinum-tube")
    for name, art, face in (("menu-arrow", "normal", (221, 221, 221)), ("menu-open-arrow", "pressed", (102, 102, 102))):
        with Image.open(PROJECT / f"gtk/Platinum/gtk-4.0/assets/menu-arrow-down-{art}.png") as ink:
            expected = Image.new("RGB", ink.size, face)
            expected.paste(ink.convert("RGBA"), mask=ink.convert("RGBA").getchannel("A"))
        x, y, w, h = controls[name][:4]
        observed = crop(image, (x, y + (h - 6) // 2, 11, 6))
        record(ImageChops.difference(observed, expected).getbbox() is None, name + "-artwork")
    # Audit #241: full and inverted level bars draw exactly like progress bars
    # with the same fill, and nothing lands outside the widget.
    def same_as(a, b):
        return ImageChops.difference(crop(image, controls[a]), crop(image, controls[b])).getbbox() is None
    fx, fy, fw, fh = controls["level-full"][:4]
    outside = image.crop((fx + fw, fy, fx + fw + 2, fy + fh))
    record(same_as("level-full", "progress-full")
           and color_count(outside, (221, 221, 221)) == outside.width * outside.height, "level-full-matches-progress")
    record(same_as("level-inverted", "progress-reversed"), "level-inverted-matches-progress")

    # Audit #240 and #243: disabled bars are flat at every level and mode.
    for name in ("level-disabled-low", "level-disabled-high", "level-disabled-full",
                 "progress-disabled-reversed", "progress-disabled-pulse"):
        region = crop(image, controls[name])
        # A full disabled bar is face color across; the others show the trough.
        trough_ok = name.endswith("-full") or color_count(region, (187, 187, 187)) > 100
        record(blue_count(region) == 0 and trough_ok and color_count(region, (221, 221, 221)) > 0, name + "-flat",
               f"{blue_count(region)} blue pixels")

    # Audit #242: each direction gets its own triangle; no direction keeps GTK's icon.
    for direction in ("up", "left", "right"):
        with Image.open(PROJECT / f"gtk/Platinum/gtk-4.0/assets/menu-arrow-{direction}-disabled.png") as ink:
            ink = ink.convert("RGBA")
            expected = Image.new("RGB", ink.size, (221, 221, 221))
            expected.paste(ink, mask=ink.getchannel("A"))
        x, y, w, h = controls[f"menu-{direction}-arrow"][:4]
        observed = crop(image, (x + (w - ink.width) // 2, y + (h - ink.height) // 2, ink.width, ink.height))
        whole = crop(image, controls[f"menu-{direction}-arrow"])
        record(ImageChops.difference(observed, expected).getbbox() is None
               and len(whole.getcolors(whole.width * whole.height)) <= 3, f"menu-{direction}-arrow-artwork")
    none_arrow = crop(image, controls["menu-none-arrow"])
    record(controls["menu-none-arrow"][2:4] == (16, 16) and color_count(none_arrow, (119, 119, 119)) > 20,
           "menu-none-keeps-gtk-icon", f"{controls['menu-none-arrow'][2:4]}")

    # Bottom tabs are the measured top tabs flipped; compare above the pane line.
    tx, ty = at("pane-appearance", 0, -24)
    bx, by = at("pane-bottom", 0, 43)
    top_row = image.crop((tx, ty, tx + 466, ty + 18)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    bottom_row = image.crop((bx, by, bx + 466, by + 18))
    record(ImageChops.difference(top_row, bottom_row).getbbox() is None, "bottom-tabs-mirror-top-tabs")

    edge = [(v, v, v) for v in (187, 136, 85, 0)]
    for name, vertical in (("progress-reversed", False), ("progress-vertical-reversed", True)):
        x, y, w, h = controls[name][:4]
        if vertical:
            line = [image.getpixel((x + w // 2, y + n)) for n in range(8, h - 8)]
        else:
            line = [image.getpixel((x + n, y + h // 2)) for n in range(8, w - 8)]
        record(any(line[i:i + 4] == edge for i in range(len(line))), name + "-leading-shadow")
    # A one-pixel fill cannot hold the 5 px tube artwork; GTK scales it into a blue line.
    for name in ("progress-tiny", "progress-vertical-tiny"):
        bar = crop(image, controls[name])
        blue = blue_count(bar)
        record(blue > 0 and color_count(bar, (0, 0, 0)) > 20, name + "-visible-fill", f"{blue} blue pixels")
    x, y, *_ = controls["progress-vertical-busy"]
    with Image.open(PROJECT / "gtk/Platinum/gtk-3.0/assets/progress-pulse-v.png") as tile:
        tile = tile.convert("RGB")
        record(ImageChops.difference(image.crop((x + 2, y + 2, x + 2 + tile.width, y + 2 + tile.height)), tile)
               .getbbox() is None, "progress-vertical-pulse-pattern")

    disabled = crop(image, controls["vbar-disabled"])
    well = color_count(disabled, (238, 238, 238)) + color_count(disabled, (221, 221, 221))
    record(well > disabled.width * disabled.height * 0.8 and color_count(disabled, (85, 85, 85)) > 200
           and color_count(disabled, (136, 136, 136)) > 100 and color_count(disabled, LAVENDER) == 0,
           "scrollbar-disabled-well")

    ox, oy, ow, oh = controls["overlay-thumb"][:4]
    hover = Image.open(root / "ranges-hover.png").convert("RGB")
    expanded = crop(hover, controls["overlay-hover-vbar"])
    indicator = crop(image, controls["overlay-thumb"])
    record(props.get("overlay_indicator") == "1" and ow <= 8
           and blue_count(indicator) > ow * oh / 2
           and controls["overlay-hover-vbar"][2] == 16 and color_count(expanded, LAVENDER) > 300
           and color_count(expanded, (51, 51, 153)) >= 28, "overlay-indicator-and-hover",
           f"indicator {ow} px, hovered {controls['overlay-hover-vbar'][2]} px")
    record(props.get("scale_value") == "2" and props.get("vscale_value") == "10"
           and props.get("notebook_page") == "2" and props.get("classic_scrolled") == "1",
           "native-scale-notebook-scroll")

    if wayland:
        backdrop = Image.open(root / "ranges-backdrop.png").convert("RGB")
        well = crop(backdrop, controls["vbar-top"])
        gray = color_count(well, (238, 238, 238)) + color_count(well, (221, 221, 221))
        record(props.get("ranges_backdrop") == "1" and color_count(well, LAVENDER) == 0
               and gray > well.width * well.height * 0.8 and color_count(well, (85, 85, 85)) > 300,
               "scrollbar-real-backdrop")
        for scale in (1.5, 2):
            passed, detail = verify_scaled_ranges(root, scale)
            record(passed, f"tabs-and-ranges-output-{scale * 100:g}pct", detail)


REF_WINDOW = (426, 410, 416, 246)  # window-document-*.png: x, y, visible width, height
ETCH = (136, 136, 136)


def find_run(image, color, length, scale=1):
    """Top-left of the first horizontal run of COLOR at least LENGTH long."""
    width = image.width
    pixels = image.load()
    for y in range(image.height):
        run = 0
        for x in range(width):
            run = run + 1 if pixels[x, y] == color else 0
            if run == length * scale:
                return x - run + 1, y
    return None


def window_origin(image, active, scale=1):
    """Our CSD window's top-left: the close box's etched row is 4 px in."""
    if active:
        hit = find_run(image, ETCH, 12, scale)
        return hit and (hit[0] - 4 * scale, hit[1] - 4 * scale)
    return find_run(image, (85, 85, 85), 40, scale)


def frame_crops(rw, rh, ow, oh):
    """(name, ref x, ref y, our x, our y, w, h) relative to each window's origin.

    Skips the two shadow pixels left of and above the shadow's start (the
    desktop shows there) and the reference's size box at the bottom right."""
    return (
        ("title-left", 0, 0, 0, 0, 40, 16),
        ("title-right", rw - 50, 0, ow - 50, 0, 50, 16),
        ("bar-bottom-left", 0, 18, 0, 18, 40, 4),
        ("bar-bottom-right", rw - 40, 18, ow - 40, 18, 41, 4),
        ("side-left", 0, 40, 0, 40, 6, 40),
        ("side-right", rw - 6, 40, ow - 6, 40, 7, 40),
        ("bottom-left", 2, rh - 6, 2, oh - 6, 38, 7),
        ("bottom-right", rw - 2, rh - 6, ow - 2, oh - 6, 3, 7),
        ("bottom-edge", rw - 60, rh - 5, ow - 60, oh - 5, 40, 6),
    )


def stripe_ends(ref, y):
    """Last white column before the title gap and first one after it on row Y."""
    x0, y0, rw, _ = REF_WINDOW
    row = [ref.getpixel((x0 + x, y0 + y)) for x in range(rw)]
    white = (255, 255, 255)
    start = next(x for x in range(rw) if x > 20 and row[x] == white)
    end = next(x for x in range(start, rw) if row[x] != white) - 1
    resume = next(x for x in range(end + 2, rw) if row[x] == white)
    return end, resume


def verify_windows(root, wayland, record, compare):
    props, geometry = read_report(root / "windows.txt")
    backend = "GdkWaylandDisplay" if wayland else "GdkBroadwayDisplay"
    record(props.get("theme") == "Platinum" and props.get("backend") == backend
           and props.get("plain_csd") == "1", "windows-named-theme-and-csd")

    # Help Balloon outline: black and white pixels of the frame and its corners.
    shot = Image.open(root / "balloon.png").convert("RGB")
    ref = Image.open(PROJECT / "reference/help-balloon.png").convert("RGB")
    bx, by, bw, bh, *_ = geometry["balloon"]

    def tone(pixel):
        return "B" if pixel == (0, 0, 0) else "W" if pixel == (255, 255, 255) else "-"

    checked = bad = 0
    for y in range(121):
        for x in range(160):
            interior = 10 <= x < 150 and 10 <= y < 111
            if interior or (x >= 130 and y < 14):  # the reference's tail is top right
                continue
            checked += 1
            bad += tone(ref.getpixel((1690 + x, 149 + y))) != tone(shot.getpixel((bx + x, by + y)))
    record((bw, bh) == (160, 121) and bad == 0, "ref-gtk4-balloon-outline", f"{bad} of {checked} px")

    # The title bar's layout matches the decoration's metrics.
    fx, fy, fw, fh = geometry["frame"]
    visible = fw - 1
    expected = {
        "headerbar": (4, 1, visible - 8, 21),
        "close": (4, 4, 13, 13),
        "minimize": (visible - 17, 4, 13, 13),
        "maximize": (visible - 33, 4, 13, 13),
    }
    actual = {name: geometry[name][:4] for name in expected}
    record((fx, fy) == (0, 0) and actual == expected, "csd-title-bar-metrics",
           ", ".join(f"{n}={actual[n]}" for n in expected if actual[n] != expected[n]) or "22 rows, boxes 4 px in, 3 px apart")
    if not wayland:
        return

    rx, ry, rw, rh = REF_WINDOW
    oh = fh - 1
    title_x = geometry["title"][0]
    for state in ("active", "inactive"):
        image = Image.open(root / f"csd-{'active' if state == 'active' else 'backdrop'}.png").convert("RGB")
        origin = window_origin(image, state == "active")
        if not origin:
            record(False, f"ref-gtk4-csd-{state}", "window not found")
            continue
        ox, oy = origin
        ref_image = f"window-document-{state}.png"
        for name, ax, ay, bx2, by2, w, h in frame_crops(rw, rh, visible, oh):
            compare(f"ref-gtk4-csd-{state}-{name}", ref_image, rx + ax, ry + ay, ox + bx2, oy + by2, w, h,
                    f"csd-{'active' if state == 'active' else 'backdrop'}.png")
        if state == "active":
            # The stripes stop 5 px before the title and resume 5 px after it.
            reference = Image.open(PROJECT / "reference" / ref_image).convert("RGB")
            end, resume = stripe_ends(reference, 4)
            label_w = geometry["title"][2]
            for side, ref_col, our_col in (("before", end, title_x - 1), ("after", resume, title_x + label_w - 1)):
                compare(f"ref-gtk4-csd-stripes-{side}-title", ref_image, rx + ref_col - 3, ry + 4,
                        ox + our_col - 3, oy + 4, 7, 12, "csd-active.png")

    # An app's bar: the boxes, stripes and caps stay on the same rows.
    app = Image.open(root / "csd-app.png").convert("RGB")
    origin = window_origin(app, True)
    if origin:
        ox, oy = origin
        _, close_y, _, _ = geometry["app-close"]
        hit = find_run(app.crop((ox, oy, ox + 40, oy + 60)), ETCH, 12)
        box_row = hit[1] if hit else -1
        ax = geometry["app-title"][0]
        stripes = [app.getpixel((ox + x, oy + box_row + r)) for r in range(12) for x in range(ax - 25, ax - 8)]
        pattern = [(255, 255, 255) if r % 2 == 0 else (119, 119, 119) for r in range(12) for _ in range(ax - 25, ax - 8)]
        bar_h = geometry["app-headerbar"][3]
        record(stripes == pattern and bar_h <= 34 and box_row >= 4, "csd-app-bar-aligned",
               f"bar {bar_h} px, boxes and stripes from row {box_row}")
    else:
        record(False, "csd-app-bar-aligned", "window not found")

    # GtkAlertDialog: the movable alert (dialog-save-changes.png, frame
    # x=536-901, y=195-344 plus the shadow), with a white body.
    alert = Image.open(root / "alert.png").convert("RGB")
    _, _, aw, ah = geometry["alert-frame"]
    width, height = aw - 1, ah - 1
    pixels = alert.load()
    hit = next(((x, y) for y in range(alert.height - 24) for x in range(alert.width - 3)
                if pixels[x, y] == (0, 0, 0) and pixels[x + 1, y + 1] == (255, 255, 255)
                and pixels[x + 2, y + 2] == (204, 204, 204) and pixels[x + 1, y + 20] == (204, 204, 204)
                and pixels[x + 2, y + 20] == (153, 153, 153) and pixels[x + 1, y + 22] == (221, 221, 221)), None)
    if hit:
        x0, y0 = hit
        rl, rt, rw2, rh2 = 536, 195, 366, 150
        for name, ax, ay, w, h in (
            ("strip-left", 0, 0, 40, 24),
            ("strip-right", -40, 0, 40, 24),
            ("left-edge", 0, 30, 3, 50),
            ("right-edge", -4, 30, 5, 50),
            ("bottom-left", 2, -3, 38, 4),
            ("bottom-right", -4, -3, 5, 4),
        ):
            rx2 = rl + (ax if ax >= 0 else rw2 + ax)
            ox2 = x0 + (ax if ax >= 0 else width + ax)
            ry2 = rt + (ay if ay >= 0 else rh2 + ay)
            oy2 = y0 + (ay if ay >= 0 else height + ay)
            compare(f"ref-gtk4-alert-{name}", "dialog-save-changes.png", rx2, ry2, ox2, oy2, w, h, "alert.png")
        body = alert.crop((x0 + 2, y0 + 23, x0 + width - 3, y0 + height - 3))
        white = color_count(body, (255, 255, 255))
        record(white > body.width * body.height / 2, "alert-white-body", f"{white} white pixels")
    else:
        record(False, "alert-window-found")

    # Maximized: no side frame, the boxes 4 px in from the screen's edges.
    maxed = "csd-max.png"
    mw = geometry["max-frame"][2]
    compare("ref-gtk4-csd-max-left", "window-document-active.png", rx + 4, ry + 1, 4, 1, 36, 15, maxed)
    compare("ref-gtk4-csd-max-right", "window-document-active.png", rx + rw - 40, ry + 1, mw - 40, 1, 36, 15, maxed)
    compare("ref-gtk4-csd-max-bottom", "window-document-active.png", rx + 10, ry + 20, 10, 20, 30, 2, maxed)
    record(props.get("maximized") == "1" and props.get("close_activated") == "1" and props.get("closed") == "1"
           and props.get("csd_backdrop") == "1" and props.get("plain_window_csd") == "0",
           "csd-controls-act-and-plain-windows-use-kwin")

    for scale in (1.5, 2):
        directory = root / f"scale-{scale}"
        sprops, sgeo = read_report(directory / "windows.txt")
        screen = Image.open(directory / "windows-output.png").convert("RGB")
        origin = window_origin(screen, True, 2 if scale == 2 else 1)
        passed = sprops.get("surface_scale") == str(scale) and sprops.get("real_active") == "1" and origin
        detail = f"surface={sprops.get('surface_scale')} origin={origin}"
        if passed and scale == 2:
            ox, oy = origin
            reference = Image.open(PROJECT / "reference/window-document-active.png").convert("RGB")
            wanted = reference.crop((rx, ry, rx + 40, ry + 16)).resize((80, 32), Image.Resampling.NEAREST)
            got = screen.crop((ox, oy, ox + 80, oy + 32))
            passed = ImageChops.difference(wanted, got).getbbox() is None
            detail = "title bar left equals the doubled reference" if passed else f"differs at {origin}"
        record(passed, f"csd-output-{scale * 100:g}pct", detail)


def main(root, wayland):
    checks = []

    def record(passed, name, detail=""):
        checks.append(bool(passed))
        print(f"{'ok' if passed else 'FAIL':<5} {name:<34} {detail}")

    def compare(name, reference, rx, ry, ox, oy, width, height, shot="chrome.png"):
        size = f"{width},{height}"
        args = [
            sys.executable, "-I", str(PROJECT / "tools/compare.py"), "diff",
            f"{PROJECT / 'reference' / reference}@{rx},{ry},{size}",
            f"{root / shot}@{ox},{oy},{size}", "--tolerance", "0",
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
    app_logs = [path.read_text() for pattern in ("factory-*.log", "settings-*.log") for path in root.glob(pattern)]
    diagnostics = [line.strip() for log in [session_log, *app_logs] for line in log.splitlines()
                   if PARSER_DIAGNOSTIC.search(line) and not (wayland and COMPOSITOR_TIMING.search(line.strip()))]
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

    verify_menus(root, wayland, record, compare)
    verify_ranges(root, wayland, record, compare)
    verify_windows(root, wayland, record, compare)

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
