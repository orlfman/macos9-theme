#!/usr/bin/env python3
# GTK 3 notebook too narrow for its tabs (Audacious settings, #263): the tab
# scroll arrows must be the Platinum horizontal scroll bar arrows, found
# pixel for pixel in the render, not empty boxes.
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
book = Gtk.Notebook(scrollable=True)
pages = []
for name in ("General", "Effect", "Visualization", "Input", "Playlist"):
    pages.append(Gtk.Label(label=name + " page"))
    book.append_page(pages[-1], Gtk.Label(label=name))
# Audacious's new-playlist button in the tab row (an action widget).
plus = Gtk.Button.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU)
book.set_action_widget(plus, Gtk.PackType.END)
plus.show()
# Two notebooks, one with a close button in its tab (Audacious's playlist
# tabs): the button must not make the tab row taller (#265).
def tab_row_height(with_close):
    nb = Gtk.Notebook()
    tab = Gtk.Box(spacing=0)
    tab.pack_start(Gtk.Label(label="Music Library"), False, False, 0)
    if with_close:
        tab.pack_start(Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU), False, False, 0)
    tab.show_all()
    page = Gtk.Label(label="page")
    nb.append_page(page, tab)
    return nb, page


plain_book, plain_page = tab_row_height(False)
close_book, close_page = tab_row_height(True)
column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
column.pack_start(book, False, False, 0)
column.pack_start(plain_book, False, False, 0)
column.pack_start(close_book, False, False, 0)
window = Gtk.OffscreenWindow()
window.add(column)
window.set_size_request(300, 300)
window.show_all()
code = [1]


def find(hay, art):
    """Where every opaque pixel of the art appears unchanged."""
    hw, hh = hay.size
    nw, nh = art.size
    hp, ap = hay.load(), art.load()
    solid = [(i, j, ap[i, j][:3]) for j in range(nh) for i in range(nw) if ap[i, j][3] == 255]
    for y in range(hh - nh + 1):
        for x in range(hw - nw + 1):
            if all(hp[x + i, y + j] == rgb for i, j, rgb in solid):
                return x, y
    return None


def check():
    try:
        window.get_pixbuf().savev(out, "png", [], [])
        shot = Image.open(out).convert("RGB").crop((0, 0, 300, 40))
        ok = True
        for name in ("hscroll-left", "hscroll-right"):
            art = Image.open(theme / f"gtk-3.0/assets/{name}.png").convert("RGBA")
            at = find(shot, art)
            ok &= at is not None
            print(f"{'ok' if at else 'FAIL'}    gtk3-notebook-arrow-{name} at={at}")
            if name == "hscroll-left" and at:
                # the edge the scroll bar's trough normally supplies
                edge = [shot.getpixel((at[0] + 15, at[1] + j)) for j in range(16)]
                closed = all(px == (0, 0, 0) for px in edge)
                ok &= closed
                print(f"{'ok' if closed else 'FAIL'}    gtk3-notebook-left-arrow-closed-right-edge")
        # The tab row overlaps the pane by 3 px: an action widget stays above it.
        _x, by = plus.translate_coordinates(window, 0, 0)
        # GTK 3 allocations include CSS margins: the drawn frame ends above them.
        margin = plus.get_style_context().get_margin(plus.get_state_flags())
        bottom = by + plus.get_allocated_height() - margin.bottom
        _x, py = pages[0].translate_coordinates(window, 0, 0)
        pane_top = py - 3
        fits = bottom <= pane_top
        ok &= fits
        print(f"{'ok' if fits else 'FAIL'}    gtk3-notebook-action-button-above-pane bottom={bottom} pane_top={pane_top}")
        rows = []
        for nb, page in ((plain_book, plain_page), (close_book, close_page)):
            _x, ny = nb.translate_coordinates(window, 0, 0)
            _x, py = page.translate_coordinates(window, 0, 0)
            rows.append(py - ny)
        same = rows[0] == rows[1]
        ok &= same
        print(f"{'ok' if same else 'FAIL'}    gtk3-notebook-close-button-keeps-tab-height plain={rows[0]} with_close={rows[1]}")
        code[0] = 0 if ok else 1
    finally:
        Gtk.main_quit()
    return False


GLib.timeout_add(700, check)
GLib.timeout_add(15000, Gtk.main_quit)
Gtk.main()
sys.exit(code[0])
