#!/usr/bin/env python3
# Stock libadwaita fixture for GTK Milestone 5 (appearance integration).
#
# usage: fixture.py <mode> <out.png>
#   modes: gallery  wide window with header bar, buttons, rows, entries
#          narrow   the same content at 360 px (breakpoint collapses the bar)
#          dialog   AdwAlertDialog with a destructive response
#          focus    gallery with keyboard focus on the suggested button
#          disabled gallery with every control insensitive
#          live     gallery that stays open (dev/live-adw.sh; out.png unused)
#          prefs    floating AdwPreferencesDialog (header bar, close box)
#          msgdialog the deprecated AdwMessageDialog (zenity 4)
#          alertwin AdwAlertDialog with no parent (its own window, as zenity)
#
# Zero application CSS: whatever appears comes from libadwaita, the desktop
# settings it reads (portal color scheme, accent, contrast) and the user's
# ~/.config/gtk-4.0/gtk.css. The fixture prints one STATE line with what
# AdwStyleManager and GtkSettings report, renders its own window to a PNG at
# the surface scale and quits.
#
# SPDX-License-Identifier: BSD-2-Clause
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Graphene, Gtk  # noqa: E402

MODE, OUT = sys.argv[1], sys.argv[2]
WIDTH = 360 if MODE == "narrow" else 720
HEIGHT = 560


def state(app):
    sm = Adw.StyleManager.get_default()
    s = Gtk.Settings.get_default()
    rgba = sm.get_accent_color_rgba()
    print(
        "STATE mode=%s adw_sys_cs=%d adw_dark=%d adw_hc=%d adw_sys_acc=%d "
        "accent=%s accent_rgba=%s theme=%s color_scheme=%s contrast=%s "
        "display=%s" % (
            MODE,
            sm.get_system_supports_color_schemes(),
            sm.get_dark(),
            sm.get_high_contrast(),
            sm.get_system_supports_accent_colors(),
            sm.get_accent_color().value_nick,
            rgba.to_string(),
            s.props.gtk_theme_name,
            s.props.gtk_interface_color_scheme,
            s.props.gtk_interface_contrast,
            type(Gdk.Display.get_default()).__name__,
        ),
        flush=True,
    )


def row_group():
    group = Adw.PreferencesGroup(title="Preferences group",
                                 description="Boxed list rows")
    row = Adw.ActionRow(title="Action row", subtitle="Subtitle text")
    row.add_suffix(Gtk.Button(label="Button", valign=Gtk.Align.CENTER))
    group.add(row)
    group.add(Adw.SwitchRow(title="Switch row", active=True))
    group.add(Adw.EntryRow(title="Entry row", text="Text"))
    group.add(Adw.SpinRow.new_with_range(0, 100, 1))
    combo = Adw.ComboRow(title="Combo row",
                         model=Gtk.StringList.new(["Platinum", "Graphite"]))
    group.add(combo)
    return group


def controls():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                  margin_top=12, margin_bottom=12,
                  margin_start=12, margin_end=12)
    buttons = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE,
                          max_children_per_line=4, column_spacing=6,
                          row_spacing=6)
    normal = Gtk.Button(label="Normal")
    suggested = Gtk.Button(label="Suggested", name="suggested")
    suggested.add_css_class("suggested-action")
    destructive = Gtk.Button(label="Destructive")
    destructive.add_css_class("destructive-action")
    flat = Gtk.Button(label="Flat")
    flat.add_css_class("flat")
    pill = Gtk.Button(label="Pill")
    pill.add_css_class("pill")
    icon = Gtk.Button(icon_name="list-add-symbolic")
    for b in (normal, suggested, destructive, flat, pill, icon):
        buttons.append(b)
    box.append(buttons)

    line = Gtk.Box(spacing=12)
    line.append(Gtk.Entry(text="Entry text", hexpand=True))
    line.append(Gtk.CheckButton(label="Check", active=True))
    line.append(Gtk.Switch(active=True, valign=Gtk.Align.CENTER))
    box.append(line)

    radios = Gtk.Box(spacing=12)
    r1 = Gtk.CheckButton(label="Radio one", active=True)
    r2 = Gtk.CheckButton(label="Radio two", group=r1)
    radios.append(r1)
    radios.append(r2)
    progress = Gtk.ProgressBar(fraction=0.6, hexpand=True,
                               valign=Gtk.Align.CENTER)
    radios.append(progress)
    box.append(radios)
    box.append(Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1))
    box.get_last_child().set_value(40)

    selected = Gtk.Entry(text="Selected text")
    box.append(selected)

    # Plain GTK 4 spin buttons: normal, disabled, vertical (#267).
    spins = Gtk.Box(spacing=12)
    spin = Gtk.SpinButton.new_with_range(-1, 1, 0.01)
    spin.set_digits(2)
    spin.set_value(-0.24)
    spin.set_name("spin")
    off = Gtk.SpinButton.new_with_range(0, 2, 0.01)
    off.set_digits(2)
    off.set_value(1)
    off.set_sensitive(False)
    tall = Gtk.SpinButton.new_with_range(0, 10, 1)
    tall.set_orientation(Gtk.Orientation.VERTICAL)
    for s in (spin, off, tall):
        s.set_valign(Gtk.Align.START)
        spins.append(s)
    box.append(spins)
    box.append(row_group())
    return box, suggested, selected


def dump(widget, depth=0, out=None):
    """CSS node tree (name, classes, allocation) for picking selectors."""
    out = out if out is not None else []
    ok, bounds = widget.compute_bounds(widget.get_root() or widget)
    x = int(bounds.get_x()) if ok else -1
    out.append("TREE %s%s%s %dx%d @%d" % (
        "  " * depth, widget.get_css_name(),
        "".join("." + c for c in widget.get_css_classes()),
        widget.get_width(), widget.get_height(), x))
    child = widget.get_first_child()
    while child:
        dump(child, depth + 1, out)
        child = child.get_next_sibling()
    return out


class EmptySnapshot(Exception):
    pass


def render(win):
    paintable = Gtk.WidgetPaintable(widget=win)
    # The paintable's own size (the window's frame margin included): drawn
    # at any other size GTK scales it, which blurs every pixel (#267).
    w, h = paintable.get_intrinsic_width(), paintable.get_intrinsic_height()
    snap = Gtk.Snapshot()
    paintable.snapshot(snap, w, h)
    node = snap.to_node()
    if node is None:
        raise EmptySnapshot("EMPTY snapshot %dx%d" % (w, h))
    scale = win.get_native().get_surface().get_scale()
    snap2 = Gtk.Snapshot()
    snap2.scale(scale, scale)
    snap2.append_node(node)
    node = snap2.to_node()
    tex = win.get_native().get_renderer().render_texture(
        node, Graphene.Rect().init(0, 0, w * scale, h * scale))
    tex.save_to_png(OUT)
    print("RENDERED %s %dx%d scale=%s" % (OUT, tex.get_width(),
                                         tex.get_height(), scale), flush=True)


def activate(app):
    win = Adw.ApplicationWindow(application=app, title="Adw Fixture",
                                default_width=WIDTH, default_height=HEIGHT)
    header = Adw.HeaderBar()
    header.pack_start(Gtk.Button(icon_name="list-add-symbolic"))
    menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
    header.pack_end(menu)
    body, suggested, selected = controls()
    if MODE == "disabled":
        body.set_sensitive(False)
    scroller = Gtk.ScrolledWindow(child=body, vexpand=True)
    view = Adw.ToolbarView(content=scroller)
    view.add_top_bar(header)
    win.set_content(view)

    bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 400sp"))
    bp.add_setter(header, "show-title", False)
    win.add_breakpoint(bp)
    win.set_size_request(360, 294)  # required with breakpoints
    win.present()

    def after_map():
        state(app)
        if MODE == "live":
            return False
        if MODE == "focus":
            suggested.grab_focus()
            win.set_focus_visible(True)
        selected.grab_focus()
        selected.select_region(0, 8)
        if MODE == "focus":
            suggested.grab_focus()
        if MODE == "alertwin":
            # Parentless, as zenity shows it: libadwaita gives it a window.
            win.set_visible(False)
            dlg = Adw.AlertDialog(heading="Delete file?",
                                  body="This cannot be undone.")
            dlg.add_response("cancel", "Cancel")
            dlg.add_response("delete", "Delete")
            dlg.set_default_response("delete")
            dlg.present(None)
            target[0] = None
        if MODE == "msgdialog":
            # The deprecated AdwMessageDialog, a window of its own (zenity 4).
            win.set_visible(False)
            dlg = Adw.MessageDialog(heading="Delete file?",
                                    body="This cannot be undone.")
            dlg.add_response("cancel", "Cancel")
            dlg.add_response("delete", "Delete")
            dlg.set_default_response("delete")
            dlg.present()
            target[0] = None
        if MODE == "prefs":
            # A floating AdwDialog with its own header bar and close box
            # (preferences, about): the document window frame.
            dlg = Adw.PreferencesDialog()
            page = Adw.PreferencesPage(title="General",
                                       icon_name="preferences-system-symbolic")
            group = Adw.PreferencesGroup(title="Updates")
            group.add(Adw.SwitchRow(title="Check automatically", active=True))
            page.add(group)
            dlg.add(page)
            dlg.set_content_width(420)
            dlg.set_content_height(300)
            dlg.present(win)
        if MODE == "dialog":
            dlg = Adw.AlertDialog(heading="Delete file?",
                                  body="This cannot be undone.")
            dlg.add_response("cancel", "Cancel")
            dlg.add_response("delete", "Delete")
            dlg.set_response_appearance("delete",
                                        Adw.ResponseAppearance.DESTRUCTIVE)
            dlg.set_default_response("cancel")
            dlg.present(win)
        GLib.timeout_add(700, finish)
        return False

    tries = [0]
    target = [win]

    def finish():
        # Render after a real frame has been painted; an unpainted window
        # snapshots to nothing.
        if target[0] is None:
            for w in Gtk.Window.list_toplevels():
                if w.get_visible() and w is not win:
                    target[0] = w
        shown = target[0]
        clock = shown.get_frame_clock()

        def painted(_clock):
            clock.disconnect(handler)
            try:
                if MODE in ("gallery", "dialog", "alertwin", "msgdialog", "prefs"):
                    print("\n".join(dump(shown)), flush=True)
                render(shown)
                app.quit()
            except EmptySnapshot:
                tries[0] += 1
                if tries[0] > 20:
                    app.quit()
                    raise
                GLib.timeout_add(100, finish)
        handler = clock.connect("after-paint", painted)
        shown.queue_draw()
        return False

    GLib.timeout_add(500, after_map)


app = Adw.Application(application_id="org.macos9theme.AdwFixture")
app.connect("activate", activate)
sys.exit(app.run([sys.argv[0]]))
