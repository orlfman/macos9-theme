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
#          segments grouped toggles and page switchers
#          prefs    floating AdwPreferencesDialog (header bar, close box)
#          msgdialog the deprecated AdwMessageDialog (zenity 4)
#          alertwin AdwAlertDialog with no parent (its own window, as zenity)
#          selections raised toolbar view + listbox/sidebar/grid/flow/textview/link (#292, #293)
#          selections-border same controls with the solid toolbar separators (#298)
#          bars-wrapped   selections-border with the header bar inside a GtkBox (#303)
#          bars-closed    selections-border, header + closed GtkSearchBar (#303, #304)
#          bars-open      selections-border, header + open GtkSearchBar (#304)
#          bars-custom    selections-border, header + plain custom box + closed GtkSearchBar (#305)
#          bars-wrapped-search selections-border, header + open GtkSearchBar inside a GtkBox (#305)
#          bars-opaque    selections-border, header + `.toolbar` box with an opaque #EEEEEE application background, 4 px CSS and 4 px widget bottom margins (#307, #309–311)
#          bars-margin    selections-border, header + plain box with a 4 px GtkWidget bottom margin (#311)
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
BARS = MODE in ("bars-wrapped", "bars-closed", "bars-open", "bars-custom",
                "bars-wrapped-search", "bars-opaque", "bars-margin")
SELECTIONS = MODE in ("selections", "selections-border") or BARS


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


def find_top_bar(w):
    """The raised top bar's revealer, or None."""
    if w.get_css_name() == "revealer" and w.has_css_class("top-bar"):
        return w
    c = w.get_first_child()
    while c:
        r = find_top_bar(c)
        if r:
            return r
        c = c.get_next_sibling()
    return None


def top_bar_layout(window):
    """The raised top bar's children as `name:height`, a box's own children in
    brackets, so the verifier can tell which layout was rendered (#308)."""
    def find(w):
        if w.get_css_name() == "revealer" and w.has_css_class("top-bar"):
            return w
        c = w.get_first_child()
        while c:
            r = find(c)
            if r:
                return r
            c = c.get_next_sibling()
        return None
    bar = find(window)
    if bar is None:
        return "none"
    box = bar.get_first_child().get_first_child()  # revealer > windowhandle > box
    parts = []
    c = box.get_first_child()
    while c:
        inner = ""
        if c.get_css_name() == "box":
            names, g = [], c.get_first_child()
            while g:
                names.append("%s:%d" % (g.get_css_name(), g.get_height()))
                g = g.get_next_sibling()
            inner = "[" + ",".join(names) + "]"
        parts.append("%s%s:%d" % (c.get_css_name(), inner, c.get_height()))
        c = c.get_next_sibling()
    return " ".join(parts)


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


def selections_body():
    """Widgets exercising #292 (selections & links) under a raised toolbar (#293)."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                  margin_top=8, margin_bottom=8,
                  margin_start=8, margin_end=8)
    lb = Gtk.ListBox()
    r1 = Gtk.ListBoxRow()
    r1.set_child(Gtk.Label(label="ListBox Selected Row", xalign=0,
                           margin_top=4, margin_bottom=4, margin_start=6))
    lb.append(r1)
    lb.select_row(r1)
    box.append(lb)

    sb = Gtk.ListBox()
    sb.add_css_class("navigation-sidebar")
    sr1 = Gtk.ListBoxRow()
    sr1.set_child(Gtk.Label(label="Sidebar Selected Row", xalign=0,
                            margin_top=4, margin_bottom=4, margin_start=6))
    sb.append(sr1)
    sb.select_row(sr1)
    box.append(sb)

    model = Gtk.StringList.new(["Grid Selected", "Grid Other"])
    sel = Gtk.SingleSelection(model=model, selected=0)
    factory = Gtk.SignalListItemFactory()
    factory.connect(
        "setup",
        lambda _f, item: item.set_child(
            Gtk.Label(margin_top=6, margin_bottom=6,
                      margin_start=10, margin_end=10)))
    factory.connect(
        "bind",
        lambda _f, item: item.get_child().set_label(
            item.get_item().get_string()))
    gv = Gtk.GridView(model=sel, factory=factory)
    box.append(gv)

    fb = Gtk.FlowBox()
    fb.append(Gtk.Label(label="FlowBox Selected",
                        margin_top=6, margin_bottom=6,
                        margin_start=10, margin_end=10))
    fb_child = fb.get_child_at_index(0)
    fb.select_child(fb_child)
    box.append(fb)

    tv = Gtk.TextView()
    tv.set_size_request(-1, 32)
    buf = tv.get_buffer()
    buf.set_text("Selected text view content")
    buf.select_range(buf.get_start_iter(), buf.get_end_iter())
    box.append(tv)

    link = Gtk.LinkButton(uri="https://example.com", label="Platinum Link",
                          halign=Gtk.Align.START)
    box.append(link)
    return box, tv, {"lb": r1, "sb": sr1, "gv": gv, "fb": fb_child,
                     "tv": tv, "link": link}


def segment_controls():
    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                   margin_top=16, margin_start=16, margin_end=16)
    linked = Gtk.Box(halign=Gtk.Align.CENTER)
    linked.add_css_class("linked")
    browse = Gtk.ToggleButton(label="Browse", active=True)
    installed = Gtk.ToggleButton(label="Installed", group=browse)
    linked.append(browse)
    linked.append(installed)
    body.append(linked)

    units = Adw.ToggleGroup(homogeneous=True, halign=Gtk.Align.CENTER)
    units.add(Adw.Toggle(label="Bytes"))
    units.add(Adw.Toggle(label="Bits"))
    units.add(Adw.Toggle(label="Unavailable", enabled=False))
    units.set_active(0)
    body.append(units)

    stack = Adw.ViewStack()
    stack.add_titled_with_icon(Gtk.Label(label="General page"), "general",
                              "General", "preferences-system-symbolic")
    stack.add_titled_with_icon(Gtk.Label(label="Units page"), "units",
                              "Units", "system-run-symbolic")
    switcher = Adw.ViewSwitcher(stack=stack, policy=Adw.ViewSwitcherPolicy.WIDE,
                               halign=Gtk.Align.CENTER)
    body.append(switcher)
    body.append(stack)

    def buttons(widget):
        child = widget.get_first_child()
        while child is not None:
            if isinstance(child, Gtk.ToggleButton):
                yield child
            child = child.get_next_sibling()

    first_unit, second_unit, disabled_unit = buttons(units)
    general, units_page = buttons(switcher)
    widgets = {
        "browse": browse, "installed": installed,
        "bytes": first_unit, "bits": second_unit, "unavailable": disabled_unit,
        "general": general, "units": units_page,
    }

    def exercise():
        for button in (installed, second_unit, units_page):
            button.emit("clicked")
        print(f"SEGMENTS linked={int(installed.get_active() and not browse.get_active())} "
              f"toggle={units.get_active()} page={stack.get_visible_child_name()}", flush=True)

    return body, widgets, exercise


def activate(app):
    win = Adw.ApplicationWindow(application=app, title="Adw Fixture",
                                default_width=WIDTH, default_height=HEIGHT)
    header = Adw.HeaderBar()
    header.pack_start(Gtk.Button(icon_name="list-add-symbolic"))
    menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
    header.pack_end(menu)
    sel_widgets = {}
    if MODE == "segments":
        body, sel_widgets, exercise_segments = segment_controls()
        view = Adw.ToolbarView(content=body)
        view.add_top_bar(header)
        win.set_content(view)
    elif SELECTIONS:
        body, focus_tv, sel_widgets = selections_body()
        suggested = selected = None
        view = Adw.ToolbarView(content=body)
        style = (Adw.ToolbarStyle.RAISED_BORDER if MODE == "selections-border" or BARS
                 else Adw.ToolbarStyle.RAISED)
        bottom = Gtk.Box()
        bottom.append(Gtk.Label(label="Bottom toolbar", margin_start=8, margin_bottom=4, margin_top=4))
        view.set_top_bar_style(style)
        view.set_bottom_bar_style(style)
        if MODE == "bars-wrapped":
            wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            wrap.append(header)
            view.add_top_bar(wrap)
        else:
            view.add_top_bar(header)
        if MODE in ("bars-closed", "bars-open"):
            search = Gtk.SearchBar(child=Gtk.SearchEntry(),
                                   search_mode_enabled=MODE == "bars-open")
            view.add_top_bar(search)
            sel_widgets.update(search=search)
        if MODE == "bars-custom":
            custom = Gtk.Box(spacing=6)
            custom.append(Gtk.Button(label="Custom bar"))
            view.add_top_bar(custom)
            view.add_top_bar(Gtk.SearchBar(child=Gtk.SearchEntry()))
            sel_widgets.update(extra=custom)
        if MODE == "bars-opaque":
            # The one application CSS in the fixture: an app's opaque toolbar.
            css = Gtk.CssProvider()
            # #EEEEEE so the verifier can see the bar is really opaque (#310);
            # the margin is the app's own, which the layer drops (#309).
            css.load_from_string(".toolbar { background-color: #eeeeee; margin-bottom: 4px; }")
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            # Plus a GtkWidget margin, which CSS can't clear (#311).
            opaque = Gtk.Box(spacing=6, margin_bottom=4)
            opaque.add_css_class("toolbar")
            opaque.append(Gtk.Button(label="Opaque bar"))
            view.add_top_bar(opaque)
            sel_widgets.update(extra=opaque)
        if MODE == "bars-margin":
            spaced = Gtk.Box(spacing=6, margin_bottom=4)
            spaced.append(Gtk.Button(label="Spaced bar"))
            view.add_top_bar(spaced)
            sel_widgets.update(extra=spaced)
        if MODE == "bars-wrapped-search":
            wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            wrap.append(Gtk.SearchBar(child=Gtk.SearchEntry(), search_mode_enabled=True))
            view.add_top_bar(wrap)
            sel_widgets.update(extra=wrap)
        view.add_bottom_bar(bottom)
        sel_widgets.update(header=header, bottom=bottom)
        win.set_content(view)
    else:
        body, suggested, selected = controls()
        focus_tv = None
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
        if MODE == "segments":
            exercise_segments()
            win.set_focus(None)
        elif SELECTIONS:
            focus_tv.grab_focus()
        else:
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
                if MODE in ("gallery", "dialog", "alertwin", "msgdialog", "prefs", "segments"):
                    print("\n".join(dump(shown)), flush=True)
                if SELECTIONS:
                    print("TOPBAR " + top_bar_layout(shown), flush=True)
                    # The bar's bounds and the widget margin, so the verifier
                    # can tell a margin was really applied (#312).
                    bar = find_top_bar(shown)
                    if bar is not None:
                        sel_widgets.setdefault("topbar", bar)
                    if "extra" in sel_widgets:
                        print("MARGIN extra %d" % sel_widgets["extra"].get_margin_bottom(),
                              flush=True)
                if SELECTIONS or MODE == "segments":
                    for name, widget in sel_widgets.items():
                        ok, b = widget.compute_bounds(shown)
                        if ok:
                            print("BOX %s %d %d %d %d" % (
                                name, int(b.get_x()), int(b.get_y()),
                                int(b.get_width()), int(b.get_height())),
                                flush=True)
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
