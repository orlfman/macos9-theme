#!/usr/bin/env python3
# GTK 3 popover menu as Lutris builds it (#262): a GtkPopover holding a
# box of GtkModelButtons (one checked, one disabled, one hovered) and a
# separator. Checks the Platinum menu look: #DDDDDD face, black outline,
# #333399 highlight, the menu separator and the menu check mark.
# Run by dev/check-gtk3-headerbar.sh inside a disposable Broadway session.
# SPDX-License-Identifier: BSD-2-Clause
import sys

import cairo
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

out = sys.argv[1]
Gtk.Settings.get_default().props.gtk_theme_name = "Platinum"
window = Gtk.Window()
anchor = Gtk.Button(label="...")
window.add(anchor)
window.set_default_size(400, 300)
window.show_all()

pop = Gtk.Popover(relative_to=anchor, position=Gtk.PositionType.BOTTOM)
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, border_width=9)
items = {}
for name in ("Installed Games Only", "Show Side Panel", "Show Hidden Games", "Preferences", "-", "About"):
    if name == "-":
        box.pack_start(Gtk.Separator(), False, False, 0)
        continue
    items[name] = Gtk.ModelButton(text=name)
    box.pack_start(items[name], False, False, 0)
items["Show Side Panel"].props.role = Gtk.ButtonRole.CHECK
items["Show Side Panel"].props.active = True
items["Show Hidden Games"].set_sensitive(False)
pop.add(box)
box.show_all()
code = [1]


def count(data, w, h, rs, rgb, region=None):
    x0, y0, x1, y1 = region or (0, 0, w, h)
    return sum(1 for y in range(y0, y1) for x in range(x0, x1)
               if tuple(data[y * rs + x * 4 + i] for i in (2, 1, 0)) == rgb)


def draw():
    try:
        items["Preferences"].set_state_flags(Gtk.StateFlags.PRELIGHT, False)
        a = pop.get_allocation()
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, a.width, a.height)
        cr = cairo.Context(surf)
        cr.set_source_rgb(0.2, 0.6, 0.9)  # a backdrop that no theme color matches
        cr.paint()
        pop.draw(cr)
        surf.write_to_png(out)
        surf.flush()
        data, w, h, rs = surf.get_data(), a.width, a.height, surf.get_stride()
        face = count(data, w, h, rs, (0xDD, 0xDD, 0xDD))
        black = count(data, w, h, rs, (0, 0, 0))
        hl = count(data, w, h, rs, (0x33, 0x33, 0x99))
        sep_dark = count(data, w, h, rs, (0x88, 0x88, 0x88))
        side = items["Show Side Panel"].get_allocation()
        ok, sx, sy = True, *items["Show Side Panel"].translate_coordinates(pop, 0, 0)
        check_black = count(data, w, h, rs, (0, 0, 0),
                            (sx + side.width // 2, sy, sx + side.width, sy + side.height))
        results = {
            "face": face > 0.4 * w * h,
            "outline": black > w + h,
            "highlight": hl > 300,
            "separator": sep_dark > 50,
            "check-mark": check_black > 5,
        }
        for k, v in results.items():
            print(f"{'ok' if v else 'FAIL'}    gtk3-popover-menu-{k}")
        print(f"info    face={face} black={black} highlight={hl} separator={sep_dark} check={check_black} size={w}x{h}")
        code[0] = 0 if all(results.values()) else 1
    finally:
        Gtk.main_quit()
    return False


def show():
    pop.popup()
    GLib.timeout_add(600, draw)
    return False


GLib.timeout_add(400, show)
GLib.timeout_add(15000, Gtk.main_quit)
Gtk.main()
sys.exit(code[0])
