#!/usr/bin/env python3
# GTK 3 header bar with app widgets laid out like Lutris (#261): a stretched
# start box around one button, a linked search box as the title, and an end
# box holding a linked pair plus a menu button. Checks that the pinstripes
# show only in the two open stretches, at least 6 px clear of every widget.
# Run by dev/check-gtk3-headerbar.sh inside a disposable Broadway session.
# SPDX-License-Identifier: BSD-2-Clause
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

out = sys.argv[1]
settings = Gtk.Settings.get_default()
settings.props.gtk_theme_name = "Platinum"
settings.props.gtk_decoration_layout = "close:maximize,minimize"


def icon(name):
    return Gtk.Button.new_from_icon_name(name, Gtk.IconSize.BUTTON)


bar = Gtk.HeaderBar(show_close_button=True)
start = Gtk.Box(spacing=6)
start.set_size_request(130, -1)  # stretched around a single button
start.pack_start(icon("list-add-symbolic"), False, False, 0)
bar.pack_start(start)
search = Gtk.Box()
search.get_style_context().add_class("linked")
entry = Gtk.SearchEntry(width_chars=30)
search.pack_start(entry, False, False, 0)
search.pack_start(Gtk.ToggleButton(), False, False, 0)
bar.set_custom_title(search)
end = Gtk.Box(spacing=6)
pair = Gtk.Box()
pair.get_style_context().add_class("linked")
pair.pack_start(icon("view-grid-symbolic"), False, False, 0)
pair.pack_start(Gtk.MenuButton(), False, False, 0)
end.pack_start(pair, False, False, 0)
end.pack_start(Gtk.MenuButton(), False, False, 0)
bar.pack_end(end)

window = Gtk.OffscreenWindow()
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
box.pack_start(bar, False, False, 0)
box.pack_start(Gtk.Label(label="content"), True, True, 0)
window.add(box)
window.set_size_request(960, 80)
window.show_all()


def widgets():
    """Every button, entry and linked group in the bar but the window boxes."""
    found = []

    def walk(w):
        ctx = w.get_style_context()
        if isinstance(w, (Gtk.Button, Gtk.Entry)) and not ctx.has_class("titlebutton"):
            found.append(w)
        if isinstance(w, Gtk.Container):
            for c in w.get_children():
                walk(c)
    walk(bar)
    walk(search)
    return found


def check():
    try:
        run_check()
    finally:
        Gtk.main_quit()
    return False


def run_check():
    window.get_pixbuf().savev(out, "png", [], [])
    pix = window.get_pixbuf()
    w, h, rs, n = pix.get_width(), pix.get_height(), pix.get_rowstride(), pix.get_n_channels()
    data = pix.get_pixels()
    rows = [y for y in range(h)
            if sum(data[y * rs + x * n] == 0x77 and data[y * rs + x * n + 1] == 0x77 for x in range(w)) > 50]
    y = rows[0]
    gray = [x for x in range(w) if data[y * rs + x * n] == 0x77 and data[y * rs + x * n + 1] == 0x77]
    runs = []
    for x in gray:
        if runs and x == runs[-1][1] + 1:
            runs[-1][1] = x
        else:
            runs.append([x, x])
    # single #777777 pixels belong to button bevels and icons, not stripes
    stripes = [x for a, b in runs if b - a > 3 for x in range(a, b + 1)]
    fails = 0
    for wd in widgets():
        x0, _y = wd.translate_coordinates(window, 0, 0)
        x1 = x0 + wd.get_allocated_width()
        near = [x for x in stripes if x0 - 6 <= x < x0 or x1 <= x < x1 + 6]
        if near:
            fails += 1
            print(f"FAIL    stripes within 6 px of {type(wd).__name__} {x0}..{x1}: {near[:6]}")
    long_runs = [r for r in runs if r[1] - r[0] > 20]
    if len(long_runs) != 2:
        fails += 1
        print(f"FAIL    expected two open stretches of stripes, got {long_runs}")
    print(f"{'ok' if not fails else 'FAIL'}    gtk3-headerbar-stripes-only-in-gaps runs={long_runs}")
    sys.exit_code = 1 if fails else 0


sys.exit_code = 1
GLib.timeout_add(700, check)
Gtk.main()
sys.exit(sys.exit_code)
