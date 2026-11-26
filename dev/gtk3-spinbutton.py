#!/usr/bin/env python3
# GTK 3 spin buttons (#267): the field is the Platinum entry, and the two
# buttons are standalone Platinum scroll arrow boxes (down for -, up for +),
# drawn pixel for pixel, 2 px right of the field.
# Run by dev/check-gtk3-headerbar.sh inside a disposable Broadway session.
# SPDX-License-Identifier: BSD-2-Clause
import pathlib
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402
from PIL import Image  # noqa: E402

out, theme = sys.argv[1], pathlib.Path(sys.argv[2])
Gtk.Settings.get_default().props.gtk_theme_name = "Platinum"
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=10)
spin = Gtk.SpinButton.new_with_range(-1, 1, 0.01)
spin.set_digits(2)
spin.set_value(-0.24)
off = Gtk.SpinButton.new_with_range(0, 2, 0.01)
off.set_digits(2)
off.set_value(1)
off.set_sensitive(False)
tall = Gtk.SpinButton.new_with_range(0, 10, 1)
tall.set_orientation(Gtk.Orientation.VERTICAL)
# Spin button packed in a header bar (#271): gap shadows must not clip its down arrow.
bar = Gtk.HeaderBar(show_close_button=True, title="Spin")
hb_spin = Gtk.SpinButton.new_with_range(0, 100, 1)
hb_spin.set_value(42)
bar.pack_start(hb_spin)
box.pack_start(bar, False, False, 0)
for s in (spin, off, tall):
    s.set_halign(Gtk.Align.START)
    box.pack_start(s, False, False, 0)
window = Gtk.OffscreenWindow()
window.add(box)
window.show_all()
code = [1]


def find(hay, art, region):
    x0, y0, x1, y1 = region
    hp, ap = hay.load(), art.load()
    aw, ah = art.size
    solid = [(i, j, ap[i, j][:3]) for j in range(ah) for i in range(aw) if ap[i, j][3] == 255]
    for y in range(y0, y1 - ah + 1):
        for x in range(x0, x1 - aw + 1):
            if all(hp[x + i, y + j] == rgb for i, j, rgb in solid):
                return x, y
    return None


def check():
    try:
        window.get_pixbuf().savev(out, "png", [], [])
        shot = Image.open(out).convert("RGB")
        a = spin.get_allocation()
        region = (a.x, a.y, a.x + a.width, a.y + a.height)
        ok = True
        found = {}
        for name in ("vscroll-down", "arrow-box-up"):
            art = Image.open(theme / f"gtk-3.0/assets/{name}.png").convert("RGBA")
            found[name] = find(shot, art, region)
            ok &= found[name] is not None
            print(f"{'ok' if found[name] else 'FAIL'}    gtk3-spin-{name} at={found[name]}")
        gap = None
        if found["vscroll-down"]:
            x, y = found["vscroll-down"]
            gap = 0
            while shot.getpixel((x - 1 - gap, y + 8)) == (0xDD, 0xDD, 0xDD):
                gap += 1
        ok &= gap == 2
        print(f"{'ok' if gap == 2 else 'FAIL'}    gtk3-spin-arrows-2px-right-of-field gap={gap}")
        # The disabled spin button: flat gray arrow boxes.
        b = off.get_allocation()
        for name in ("arrow-box-down-disabled", "arrow-box-up-disabled"):
            art = Image.open(theme / f"gtk-3.0/assets/{name}.png").convert("RGBA")
            at = find(shot, art, (b.x, b.y, b.x + b.width, b.y + b.height))
            ok &= at is not None
            print(f"{'ok' if at else 'FAIL'}    gtk3-spin-{name} at={at}")
        # Spin button inside a header bar (#271): both arrow boxes intact.
        hx, hy = hb_spin.translate_coordinates(window, 0, 0)
        ha = hb_spin.get_allocation()
        for name in ("vscroll-down", "arrow-box-up"):
            art = Image.open(theme / f"gtk-3.0/assets/{name}.png").convert("RGBA")
            at = find(shot, art, (hx, hy, hx + ha.width, hy + ha.height))
            ok &= at is not None
            print(f"{'ok' if at else 'FAIL'}    gtk3-headerbar-spin-{name} at={at}")
        code[0] = 0 if ok else 1
    finally:
        Gtk.main_quit()
    return False


GLib.timeout_add(700, check)
GLib.timeout_add(15000, Gtk.main_quit)
Gtk.main()
sys.exit(code[0])
