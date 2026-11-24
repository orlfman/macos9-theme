/* SPDX-License-Identifier: BSD-2-Clause */
#include <gtk/gtk.h>
#include <stdio.h>

static void
settle(unsigned milliseconds)
{
    gint64 end = g_get_monotonic_time() + milliseconds * G_TIME_SPAN_MILLISECOND;
    do {
        while (g_main_context_iteration(NULL, FALSE))
            ;
        g_usleep(5000);
    } while (g_get_monotonic_time() < end);
}

static void
painted(GdkFrameClock *clock, gpointer data)
{
    (void)clock;
    gboolean *ready = data;
    *ready = TRUE;
}

/* Read the last painted frame without scheduling another surface commit. */
static gboolean
save_frame(GtkWidget *window, const char *path)
{
    GdkPaintable *paintable = gtk_widget_paintable_new(window);
    GtkSnapshot *snapshot = gtk_snapshot_new();
    gdk_paintable_snapshot(paintable, snapshot, gtk_widget_get_width(window),
                          gtk_widget_get_height(window));
    GskRenderNode *node = gtk_snapshot_free_to_node(snapshot);
    g_object_unref(paintable);
    if (!node) {
        fprintf(stderr, "No render node for %s\n", path);
        return FALSE;
    }

    GskRenderer *renderer = gtk_native_get_renderer(GTK_NATIVE(window));
    GdkTexture *texture = gsk_renderer_render_texture(renderer, node, NULL);
    gboolean saved = texture && gdk_texture_save_to_png(texture, path);
    if (!saved)
        fprintf(stderr, "Could not save %s\n", path);
    g_clear_object(&texture);
    gsk_render_node_unref(node);
    return saved;
}

static gboolean
snapshot(GtkWidget *window, const char *path)
{
    /* Broadway can throttle paints for one second without a browser. */
    GdkFrameClock *clock = gtk_widget_get_frame_clock(window);
    gboolean ready = FALSE;
    gulong handler = g_signal_connect_after(clock, "after-paint", G_CALLBACK(painted), &ready);
    gtk_widget_queue_draw(window);
    gint64 deadline = g_get_monotonic_time() + 3 * G_TIME_SPAN_SECOND;
    while (!ready && g_get_monotonic_time() < deadline)
        settle(20);
    g_signal_handler_disconnect(clock, handler);
    if (!ready) {
        fprintf(stderr, "No frame for %s\n", path);
        return FALSE;
    }
    return save_frame(window, path);
}

static void
report_renderer(GtkWidget *window)
{
    GtkNative *native = GTK_NATIVE(window);
    const char *override = g_getenv("GSK_RENDERER");
    printf("renderer=%s renderer_override=%s surface_scale=%g\n",
           G_OBJECT_TYPE_NAME(gtk_native_get_renderer(native)), override ? override : "none",
           gdk_surface_get_scale(gtk_native_get_surface(native)));
}

static GtkWidget *
entry(const char *value)
{
    GtkWidget *widget = gtk_entry_new();
    gtk_editable_set_text(GTK_EDITABLE(widget), value);
    return widget;
}

static GtkWidget *
check(const char *label, gboolean active)
{
    GtkWidget *widget = gtk_check_button_new_with_label(label);
    gtk_check_button_set_active(GTK_CHECK_BUTTON(widget), active);
    return widget;
}

static void
place(GtkFixed *fixed, GtkWidget *widget, int x, int y, int width, int height)
{
    gtk_widget_set_size_request(widget, width, height);
    gtk_fixed_put(fixed, widget, x, y);
}

static gboolean
report_widget(const char *name, GtkWidget *widget, GtkWidget *window)
{
    graphene_rect_t bounds;
    if (!gtk_widget_compute_bounds(widget, window, &bounds) ||
        !gtk_widget_get_mapped(widget))
        return FALSE;

    int minimum, width, height;
    gtk_widget_measure(widget, GTK_ORIENTATION_HORIZONTAL, -1, &minimum, &width, NULL, NULL);
    /* compute_bounds() excludes CSS margins, whereas measure() includes them. */
    gtk_widget_measure(widget, GTK_ORIENTATION_VERTICAL, MAX(minimum, (int)bounds.size.width),
                       NULL, &height, NULL, NULL);
    printf("%s %.0f %.0f %.0f %.0f %d %d\n", name,
           bounds.origin.x, bounds.origin.y, bounds.size.width, bounds.size.height,
           width, height);
    return TRUE;
}

static void
report_label_color(const char *name, GtkWidget *label)
{
    g_assert(GTK_IS_LABEL(label));
    GdkRGBA color;
    gtk_widget_get_color(label, &color);
    g_autofree char *value = gdk_rgba_to_string(&color);
    printf("%s=%s\n", name, value);
}

static gboolean
report_indicator(const char *name, GtkWidget *check_button, GtkWidget *window)
{
    GtkWidget *child = gtk_widget_get_first_child(check_button);
    return child && report_widget(name, child, window);
}

static GtkWidget *
window_new(const char *title)
{
    GtkWidget *window = gtk_window_new();
    gtk_window_set_title(GTK_WINDOW(window), title);
    gtk_window_set_decorated(GTK_WINDOW(window), FALSE);
    return window;
}

static void
chrome_surfaces(GtkDrawingArea *area, cairo_t *cr, int width, int height, gpointer data)
{
    (void)area;
    (void)width;
    (void)height;
    (void)data;
    /* The source captures place these buttons on white and the entries on #eeeeee. */
    cairo_set_source_rgb(cr, 1, 1, 1);
    cairo_rectangle(cr, 12, 12, 142, 20);
    cairo_rectangle(cr, 112, 38, 78, 26);
    cairo_fill(cr);
    cairo_set_source_rgb(cr, 238 / 255.0, 238 / 255.0, 238 / 255.0);
    cairo_rectangle(cr, 12, 76, 66, 26);
    cairo_fill(cr);
}

static gboolean
chrome(void)
{
    GtkWidget *window = window_new("Platinum GTK 4 chrome");
    GtkWidget *fixed = gtk_fixed_new();
    gtk_window_set_child(GTK_WINDOW(window), fixed);
    gtk_window_set_default_size(GTK_WINDOW(window), 244, 116);

    GtkWidget *surfaces = gtk_drawing_area_new();
    gtk_drawing_area_set_draw_func(GTK_DRAWING_AREA(surfaces), chrome_surfaces, NULL, NULL);
    place(GTK_FIXED(fixed), surfaces, 0, 0, 244, 116);

    GtkWidget *normal = gtk_button_new();
    /* A custom child exercises the framed button without GTK's .text-button class. */
    gtk_button_set_child(GTK_BUTTON(normal), gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0));
    GtkWidget *pressed = gtk_button_new();
    GtkWidget *disabled = gtk_button_new();
    GtkWidget *default_button = gtk_button_new();
    GtkWidget *default_pressed = gtk_button_new();
    gtk_widget_set_sensitive(disabled, FALSE);
    gtk_widget_set_state_flags(pressed, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_set_state_flags(default_pressed, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_add_css_class(default_pressed, "suggested-action");
    place(GTK_FIXED(fixed), normal, 12, 12, 70, 20);
    place(GTK_FIXED(fixed), pressed, 84, 12, 70, 20);
    place(GTK_FIXED(fixed), disabled, 156, 12, 80, 20);
    place(GTK_FIXED(fixed), default_button, 12, 38, 86, 26);
    place(GTK_FIXED(fixed), default_pressed, 112, 38, 78, 26);
    gtk_window_set_default_widget(GTK_WINDOW(window), default_button);

    GtkWidget *normal_entry = entry("");
    GtkWidget *focused_entry = entry("");
    /* A blank entry's caret can cross the measured inner border bands. */
    gtk_widget_set_name(focused_entry, "chrome-focus");
    g_autoptr(GtkCssProvider) chrome_css = gtk_css_provider_new();
    gtk_css_provider_load_from_string(chrome_css,
        "#chrome-focus > text { caret-color: transparent; -gtk-secondary-caret-color: transparent; }");
    GdkDisplay *display = gtk_widget_get_display(window);
    gtk_style_context_add_provider_for_display(display, GTK_STYLE_PROVIDER(chrome_css),
                                              GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    gtk_editable_set_width_chars(GTK_EDITABLE(normal_entry), 0);
    gtk_editable_set_width_chars(GTK_EDITABLE(focused_entry), 0);
    place(GTK_FIXED(fixed), normal_entry, 12, 76, 30, 26);
    place(GTK_FIXED(fixed), focused_entry, 48, 76, 30, 26);

    GtkWidget *off_check = check(NULL, FALSE);
    GtkWidget *on_check = check(NULL, TRUE);
    GtkWidget *pressed_check = check(NULL, FALSE);
    GtkWidget *disabled_check = check(NULL, TRUE);
    gtk_widget_set_state_flags(pressed_check, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_set_sensitive(disabled_check, FALSE);

    GtkWidget *off_radio = check(NULL, FALSE);
    GtkWidget *on_radio = check(NULL, FALSE);
    GtkWidget *pressed_radio = check(NULL, FALSE);
    GtkWidget *disabled_radio = check(NULL, FALSE);
    gtk_check_button_set_group(GTK_CHECK_BUTTON(on_radio), GTK_CHECK_BUTTON(off_radio));
    gtk_check_button_set_group(GTK_CHECK_BUTTON(pressed_radio), GTK_CHECK_BUTTON(off_radio));
    gtk_check_button_set_group(GTK_CHECK_BUTTON(disabled_radio), GTK_CHECK_BUTTON(off_radio));
    gtk_check_button_set_active(GTK_CHECK_BUTTON(on_radio), TRUE);
    gtk_widget_set_state_flags(pressed_radio, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_set_sensitive(disabled_radio, FALSE);

    GtkWidget *indicators[] = {off_check, on_check, pressed_check, disabled_check,
                               off_radio, on_radio, pressed_radio, disabled_radio};
    const char *indicator_names[] = {"check-off", "check-on", "check-off-pressed",
                                     "check-on-disabled", "radio-off", "radio-on",
                                     "radio-off-pressed", "radio-off-disabled"};
    for (guint i = 0; i < G_N_ELEMENTS(indicators); i++)
        place(GTK_FIXED(fixed), indicators[i], 84 + 18 * i, 76, 18, 20);

    gtk_window_present(GTK_WINDOW(window));
    gtk_entry_grab_focus_without_selecting(GTK_ENTRY(focused_entry));
    settle(350);

    gboolean ok = snapshot(window, "chrome.png");
    report_renderer(window);
    ok &= report_widget("push-normal", normal, window);
    ok &= report_widget("push-pressed", pressed, window);
    ok &= report_widget("push-disabled", disabled, window);
    ok &= report_widget("push-default", default_button, window);
    ok &= report_widget("push-default-pressed", default_pressed, window);
    ok &= report_widget("entry-normal", normal_entry, window);
    ok &= report_widget("entry-focused", focused_entry, window);
    for (guint i = 0; i < G_N_ELEMENTS(indicators); i++)
        ok &= report_indicator(indicator_names[i], indicators[i], window);

    gtk_window_destroy(GTK_WINDOW(window));
    gtk_style_context_remove_provider_for_display(display, GTK_STYLE_PROVIDER(chrome_css));
    return ok;
}

static void
clicked(GtkButton *button, gpointer data)
{
    (void)button;
    unsigned *count = data;
    (*count)++;
}

static gboolean
capture_output(const char *path)
{
    if (!path)
        return TRUE;

    char *cmd[] = {"timeout", "12", "spectacle", "-b", "-n", "-f", "-o", (char *)path, NULL};
    int status = 0;
    g_autoptr(GError) error = NULL;
    if (!g_spawn_sync(NULL, cmd, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL,
                      NULL, NULL, &status, &error) ||
        !g_spawn_check_wait_status(status, &error)) {
        fprintf(stderr, "Compositor capture failed: %s\n", error->message);
        return FALSE;
    }
    return g_file_test(path, G_FILE_TEST_IS_REGULAR);
}

static gboolean
tab_to(GtkWidget *window, GtkWidget *control)
{
    for (unsigned step = 0; step < 24; step++) {
        gtk_widget_child_focus(window, GTK_DIR_TAB_FORWARD);
        if (gtk_window_get_focus(GTK_WINDOW(window)) == control)
            return TRUE;
    }
    return FALSE;
}

static gboolean
snapshot_backdrop(GtkWidget *window, const char *path, const char *label)
{
    GtkWindow *dialog = GTK_WINDOW(window);
    GtkWidget *focus = gtk_window_get_focus(dialog);
    gboolean was_active = gtk_window_is_active(dialog);
    GtkWidget *other = window_new("Platinum GTK 4 deactivation witness");
    gtk_window_set_default_size(GTK_WINDOW(other), 160, 80);
    gtk_window_present(GTK_WINDOW(other));
    settle(450);
    gboolean backdrop = was_active && gtk_window_is_active(GTK_WINDOW(other)) &&
                        !gtk_window_is_active(dialog) && gtk_window_get_focus(dialog) == focus;
    printf("backdrop-%s=%d\n", label, backdrop);
    gboolean ok = backdrop && snapshot(window, path);
    if (backdrop && !g_str_equal(label, "entry")) {
        /* Applications can update their focus target while their window is inactive. */
        gtk_window_set_focus(dialog, NULL);
        gtk_window_set_focus(dialog, focus);
        GtkStateFlags expected = GTK_STATE_FLAG_BACKDROP | GTK_STATE_FLAG_FOCUSED |
                                 GTK_STATE_FLAG_FOCUS_VISIBLE;
        gboolean reassigned = !gtk_window_is_active(dialog) && gtk_window_get_focus(dialog) == focus;
        GtkStateFlags prior = gtk_widget_get_state_flags(focus);
        gboolean focus_flags = (prior & expected) == expected;
        /* Some GTK versions clear the visible focus flags on reassignment.
         * Still exercise the CSS state before accepting a ring-free image. */
        if (!focus_flags)
            gtk_widget_set_state_flags(focus, GTK_STATE_FLAG_FOCUSED | GTK_STATE_FLAG_FOCUS_VISIBLE, FALSE);
        gboolean covered = (gtk_widget_get_state_flags(focus) & expected) == expected;
        printf("backdrop-reassigned-%s=%d backdrop-focus-flags-%s=%d backdrop-covered-%s=%d\n",
               label, reassigned, label, focus_flags, label, covered);
        g_autofree char *reassigned_path = g_strdup_printf("backdrop-reassigned-%s.png", label);
        ok &= reassigned && covered && snapshot(window, reassigned_path);
        if (!focus_flags)
            gtk_widget_unset_state_flags(focus, (GTK_STATE_FLAG_FOCUSED | GTK_STATE_FLAG_FOCUS_VISIBLE) & ~prior);
    }
    gtk_window_destroy(GTK_WINDOW(other));
    gtk_window_present(dialog);
    settle(300);
    return ok;
}

static void
set_indicator_state(GtkWidget *const *controls, gsize count, GtkStateFlags flag, gboolean enabled)
{
    for (gsize i = 0; i < count; i++) {
        GtkWidget *indicator = gtk_widget_get_first_child(controls[i]);
        if (enabled) {
            gtk_widget_set_state_flags(controls[i], flag, FALSE);
            gtk_widget_set_state_flags(indicator, flag, FALSE);
        } else {
            gtk_widget_unset_state_flags(controls[i], flag);
            gtk_widget_unset_state_flags(indicator, flag);
        }
    }
}

static gboolean
gallery(gboolean wayland)
{
    GtkWidget *window = window_new("Platinum GTK 4 dialog");
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
    gtk_widget_set_margin_start(box, 14);
    gtk_widget_set_margin_end(box, 14);
    gtk_widget_set_margin_top(box, 12);
    gtk_widget_set_margin_bottom(box, 12);
    gtk_window_set_child(GTK_WINDOW(window), box);

    GtkWidget *selected = entry("The selected text is Lavender.");
    gtk_entry_set_activates_default(GTK_ENTRY(selected), TRUE);
    GtkWidget *plain_entry = entry("Editable text");
    GtkWidget *disabled_entry = entry("Disabled entry");
    gtk_widget_set_sensitive(disabled_entry, FALSE);
    GtkWidget *empty_check = check("Checkbox", FALSE);
    GtkWidget *checked = check("Checked checkbox", TRUE);
    GtkWidget *mixed = check("Mixed checkbox", FALSE);
    gtk_check_button_set_inconsistent(GTK_CHECK_BUTTON(mixed), TRUE);
    GtkWidget *disabled_check = check("Disabled checkbox", TRUE);
    gtk_widget_set_sensitive(disabled_check, FALSE);
    GtkWidget *radio_one = check("Radio choice one", FALSE);
    GtkWidget *radio_two = check("Radio choice two", FALSE);
    GtkWidget *radio_mixed = check("Mixed radio choice", FALSE);
    gtk_check_button_set_group(GTK_CHECK_BUTTON(radio_two), GTK_CHECK_BUTTON(radio_one));
    gtk_check_button_set_group(GTK_CHECK_BUTTON(radio_mixed), GTK_CHECK_BUTTON(radio_one));
    gtk_check_button_set_inconsistent(GTK_CHECK_BUTTON(radio_mixed), TRUE);
    gtk_check_button_set_active(GTK_CHECK_BUTTON(radio_one), TRUE);

    GtkWidget *buttons = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    GtkWidget *normal = gtk_button_new();
    GtkWidget *button_child = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 4);
    gtk_box_append(GTK_BOX(button_child), gtk_image_new_from_icon_name("edit-undo-symbolic"));
    gtk_box_append(GTK_BOX(button_child), gtk_label_new("Cancel"));
    gtk_button_set_child(GTK_BUTTON(normal), button_child);
    gtk_widget_set_receives_default(normal, FALSE);
    GtkWidget *disabled = gtk_button_new_with_label("Disabled");
    gtk_widget_set_sensitive(disabled, FALSE);
    GtkWidget *default_button = gtk_button_new_with_label("Continue");
    gtk_window_set_default_widget(GTK_WINDOW(window), default_button);

    GtkWidget *controls[] = {selected, plain_entry, disabled_entry, empty_check, checked, mixed,
                             disabled_check, radio_one, radio_two, radio_mixed, normal, disabled, default_button};
    const char *names[] = {"selected", "entry", "entry-disabled", "check", "checked", "mixed",
                           "check-disabled", "radio-one", "radio-two", "radio-mixed", "cancel",
                           "button-disabled", "continue"};
    for (guint i = 0; i < G_N_ELEMENTS(controls); i++)
        gtk_box_append(GTK_BOX(i < G_N_ELEMENTS(controls) - 3 ? box : buttons), controls[i]);
    gtk_box_append(GTK_BOX(box), buttons);

    unsigned click_count = 0, cancel_click_count = 0;
    g_signal_connect(normal, "clicked", G_CALLBACK(clicked), &cancel_click_count);
    g_signal_connect(default_button, "clicked", G_CALLBACK(clicked), &click_count);
    gtk_window_present(GTK_WINDOW(window));
    gtk_window_set_focus_visible(GTK_WINDOW(window), TRUE);
    gtk_widget_grab_focus(selected);
    gtk_editable_select_region(GTK_EDITABLE(selected), 0, -1);
    settle(300);
    GtkEditable *delegate = gtk_editable_get_delegate(GTK_EDITABLE(selected));
    g_signal_emit_by_name(delegate, "activate");
    settle(400);
    gboolean ok = snapshot(window, "dialog.png");
    report_renderer(window);

    const char *output = g_getenv("GTK4_CHECK_OUTPUT");
    if (output) {
        gboolean active = gtk_window_is_active(GTK_WINDOW(window));
        printf("real_active=%d\n", active);
        ok &= wayland && active && capture_output(output);
    }

    for (guint i = 0; i < G_N_ELEMENTS(controls); i++)
        ok &= report_widget(names[i], controls[i], window);
    GtkWidget *indicators[] = {empty_check, checked, mixed, radio_two, radio_one, radio_mixed};
    const char *indicator_names[] = {"check-off-indicator", "check-on-indicator", "mixed-indicator",
                                     "radio-off-indicator", "radio-on-indicator", "mixed-radio-indicator"};
    gsize indicator_count = G_N_ELEMENTS(indicators);
    for (gsize i = 0; i < indicator_count; i++)
        ok &= report_indicator(indicator_names[i], indicators[i], window);

    if (!output) {
        if (wayland)
            ok &= snapshot_backdrop(window, "dialog-backdrop.png", "entry");

        /* Broadway has no pointer. Set the same GTK states on each indicator
         * so the hover and pressed/hover selectors are exercised on both backends. */
        set_indicator_state(indicators, indicator_count, GTK_STATE_FLAG_PRELIGHT, TRUE);
        ok &= snapshot(window, "hover.png");
        set_indicator_state(indicators, indicator_count, GTK_STATE_FLAG_ACTIVE, TRUE);
        ok &= snapshot(window, "pressed-hover.png");
        set_indicator_state(indicators, indicator_count, GTK_STATE_FLAG_PRELIGHT, FALSE);
        ok &= snapshot(window, "pressed.png");
        set_indicator_state(indicators, indicator_count, GTK_STATE_FLAG_ACTIVE, FALSE);

        GtkWidget *focus_widgets[] = {normal, default_button, empty_check, radio_one};
        const char *focus_names[] = {"button", "default", "check", "radio"};
        for (gsize i = 0; i < G_N_ELEMENTS(focus_widgets); i++) {
            ok &= tab_to(window, focus_widgets[i]);
            gtk_window_set_focus_visible(GTK_WINDOW(window), TRUE);
            settle(180);
            gboolean focused = gtk_widget_has_visible_focus(focus_widgets[i]);
            printf("focus-%s=%d\n", focus_names[i], focused);
            g_autofree char *path = g_strdup_printf("focus-%s.png", focus_names[i]);
            ok &= focused && snapshot(window, path);
            if (wayland) {
                g_autofree char *backdrop_path = g_strdup_printf("backdrop-%s.png", focus_names[i]);
                ok &= snapshot_backdrop(window, backdrop_path, focus_names[i]);
            }
        }
    }

    gboolean cancel_activated = gtk_widget_activate(normal);
    settle(350);
    gboolean toggled = gtk_widget_activate(empty_check) &&
                       gtk_check_button_get_active(GTK_CHECK_BUTTON(empty_check));
    gboolean radio_changed = gtk_widget_activate(radio_two) &&
                             gtk_check_button_get_active(GTK_CHECK_BUTTON(radio_two)) &&
                             !gtk_check_button_get_active(GTK_CHECK_BUTTON(radio_one));
    printf("default_clicks=%u cancel_clicks=%u toggle=%d radio_changed=%d\n",
           click_count, cancel_click_count, toggled, radio_changed);

    gtk_widget_set_sensitive(normal, FALSE);
    gtk_widget_set_sensitive(radio_two, FALSE);
    report_label_color("disabled-custom-label", gtk_widget_get_last_child(button_child));
    report_label_color("disabled-push-label", gtk_button_get_child(GTK_BUTTON(disabled)));
    report_label_color("disabled-check-label", gtk_widget_get_last_child(disabled_check));
    report_label_color("disabled-radio-label", gtk_widget_get_last_child(radio_two));
    gtk_window_destroy(GTK_WINDOW(window));
    return ok && click_count == 1 && cancel_activated && cancel_click_count == 1 && toggled && radio_changed;
}

/* Compare stock composite controls on the same canvas in two named themes. */
static gboolean
composites(void)
{
    GtkWidget *window = window_new("GTK 4 button roles");
    GtkWidget *fixed = gtk_fixed_new();
    gtk_window_set_child(GTK_WINDOW(window), fixed);
    gtk_window_set_default_size(GTK_WINDOW(window), 372, 317);

    g_autoptr(GtkCssProvider) canvas = gtk_css_provider_new();
    gtk_css_provider_load_from_string(canvas, "window.background { background-color: white; color: black; }");
    GdkDisplay *display = gtk_widget_get_display(window);
    gtk_style_context_add_provider_for_display(display, GTK_STYLE_PROVIDER(canvas),
                                              GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);

    GtkWidget *stack = gtk_stack_new();
    gtk_stack_add_titled(GTK_STACK(stack), gtk_label_new("One"), "one", "A");
    gtk_stack_add_titled(GTK_STACK(stack), gtk_label_new("Two"), "two", "B");
    GtkWidget *switcher = gtk_stack_switcher_new();
    gtk_stack_switcher_set_stack(GTK_STACK_SWITCHER(switcher), GTK_STACK(stack));
    gtk_fixed_put(GTK_FIXED(fixed), stack, 300, 8);
    gtk_fixed_put(GTK_FIXED(fixed), switcher, 12, 8);

    const char *roles[] = {"linked", "toolbar", "toolbar", "osd"};
    const char *names[] = {"linked", "toolbar", "nested-toolbar", "osd"};
    GtkWidget *groups[G_N_ELEMENTS(roles)];
    for (guint i = 0; i < G_N_ELEMENTS(roles); i++) {
        GtkWidget *group = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
        groups[i] = group;
        gtk_widget_add_css_class(group, roles[i]);
        gtk_fixed_put(GTK_FIXED(fixed), group, 12, 68 + 60 * i);
        if (i == 2) {
            GtkWidget *inner = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
            gtk_box_append(GTK_BOX(group), inner);
            group = inner;
        }
        gtk_box_append(GTK_BOX(group), gtk_button_new_with_label("A"));
        if (i == 0)
            gtk_box_append(GTK_BOX(group), gtk_button_new_with_label("B"));
    }
    gtk_window_present(GTK_WINDOW(window));
    gtk_window_set_focus(GTK_WINDOW(window), NULL);
    settle(350);
    gboolean ok = snapshot(window, "composites.png");
    report_renderer(window);
    ok &= report_widget("switcher", switcher, window);
    for (guint i = 0; i < G_N_ELEMENTS(groups); i++)
        ok &= report_widget(names[i], groups[i], window);
    gtk_window_destroy(GTK_WINDOW(window));
    gtk_style_context_remove_provider_for_display(display, GTK_STYLE_PROVIDER(canvas));
    return ok;
}

static gboolean
contrast(void)
{
    GtkWidget *window = window_new("Platinum GTK 4 contrast");
    gtk_window_set_default_size(GTK_WINDOW(window), 242, 68);
    GtkWidget *field = entry("Contrast preference");
    gtk_window_set_child(GTK_WINDOW(window), field);
    gtk_window_present(GTK_WINDOW(window));
    gtk_window_set_focus_visible(GTK_WINDOW(window), TRUE);
    gtk_widget_grab_focus(field);
    gtk_editable_select_region(GTK_EDITABLE(field), 0, -1);
    settle(300);

    /* The private session changes the preference while this window stays mapped. */
    GtkSettings *settings = gtk_settings_get_default();
    gboolean ok = TRUE;
    const char *states[] = {"initial", "high", "restored"};
    for (guint i = 0; i < G_N_ELEMENTS(states); i++) {
        gboolean high = i == 1;
        GtkInterfaceContrast target = high ? GTK_INTERFACE_CONTRAST_MORE : GTK_INTERFACE_CONTRAST_NO_PREFERENCE;
        GtkInterfaceContrast preference;
        gint64 deadline = g_get_monotonic_time() + 5 * G_TIME_SPAN_SECOND;
        do {
            settle(30);
            g_object_get(settings, "gtk-interface-contrast", &preference, NULL);
        } while (preference != target && g_get_monotonic_time() < deadline);
        if (preference != target) {
            g_printerr("Contrast %s did not reach %d (got %d)\n", states[i], target, preference);
            ok = FALSE;
        }
        /* A preference notification can precede the final focus transition. */
        settle(500);
        g_autofree char *path = g_strdup_printf("%s.png", states[i]);
        ok &= snapshot(window, path);
        printf("contrast-%s=%d\n", states[i], preference);
        fflush(stdout);
    }
    report_renderer(window);
    gtk_window_destroy(GTK_WINDOW(window));
    return ok;
}

static GtkWidget *
find_node(GtkWidget *root, const char *name)
{
    if (!root)
        return NULL;
    if (g_str_equal(gtk_widget_get_css_name(root), name))
        return root;
    for (GtkWidget *child = gtk_widget_get_first_child(root); child; child = gtk_widget_get_next_sibling(child)) {
        GtkWidget *found = find_node(child, name);
        if (found)
            return found;
    }
    return NULL;
}

static GtkWidget *
menu_row(GtkWidget *node, const char *text)
{
    if (GTK_IS_LABEL(node) && g_str_equal(gtk_label_get_text(GTK_LABEL(node)), text)) {
        for (GtkWidget *row = node; row; row = gtk_widget_get_parent(row))
            if (g_str_equal(gtk_widget_get_css_name(row), "modelbutton"))
                return row;
    }
    for (GtkWidget *child = gtk_widget_get_first_child(node); child; child = gtk_widget_get_next_sibling(child)) {
        GtkWidget *row = menu_row(child, text);
        if (row)
            return row;
    }
    return NULL;
}

static void
setup_string(GtkSignalListItemFactory *factory, GtkListItem *item, gpointer data)
{
    (void)factory;
    (void)data;
    gtk_list_item_set_child(item, gtk_label_new(NULL));
}

static void
bind_string(GtkSignalListItemFactory *factory, GtkListItem *item, gpointer data)
{
    (void)factory;
    (void)data;
    GtkStringObject *value = gtk_list_item_get_item(item);
    gtk_label_set_text(GTK_LABEL(gtk_list_item_get_child(item)), gtk_string_object_get_string(value));
}

static GtkListItemFactory *
string_factory(void)
{
    GtkListItemFactory *factory = gtk_signal_list_item_factory_new();
    g_signal_connect(factory, "setup", G_CALLBACK(setup_string), NULL);
    g_signal_connect(factory, "bind", G_CALLBACK(bind_string), NULL);
    return factory;
}

static void
toggle_action(GSimpleAction *action, GVariant *parameter, gpointer data)
{
    (void)parameter;
    (void)data;
    g_autoptr(GVariant) value = g_action_get_state(G_ACTION(action));
    g_simple_action_set_state(action, g_variant_new_boolean(!g_variant_get_boolean(value)));
}

static gboolean
menus_lists(gboolean wayland)
{
    GtkWidget *window = window_new("Platinum menus and lists");
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    gtk_window_set_child(GTK_WINDOW(window), box);

    g_autoptr(GMenu) menu = g_menu_new();
    g_menu_append(menu, "Show details", "view.details");
    g_menu_append(menu, "Unavailable", "view.unavailable");
    g_autoptr(GMenu) modes = g_menu_new();
    g_menu_append(modes, "List", "view.mode::list");
    g_menu_append(modes, "Icons", "view.mode::icons");
    g_menu_append_section(menu, NULL, G_MENU_MODEL(modes));
    g_autoptr(GMenu) more = g_menu_new();
    g_menu_append(more, "Details", "view.details");
    g_menu_append_submenu(menu, "More", G_MENU_MODEL(more));
    g_autoptr(GSimpleActionGroup) actions = g_simple_action_group_new();
    g_autoptr(GSimpleAction) details = g_simple_action_new_stateful("details", NULL, g_variant_new_boolean(TRUE));
    g_autoptr(GSimpleAction) mode = g_simple_action_new_stateful("mode", G_VARIANT_TYPE_STRING,
                                                                g_variant_new_string("list"));
    g_action_map_add_action(G_ACTION_MAP(actions), G_ACTION(mode));
    g_signal_connect(details, "activate", G_CALLBACK(toggle_action), NULL);
    g_action_map_add_action(G_ACTION_MAP(actions), G_ACTION(details));
    gtk_widget_insert_action_group(window, "view", G_ACTION_GROUP(actions));
    g_autoptr(GMenu) titles = g_menu_new();
    g_menu_append_submenu(titles, "File", G_MENU_MODEL(menu));
    GtkWidget *bar = gtk_popover_menu_bar_new_from_model(G_MENU_MODEL(titles));
    gtk_box_append(GTK_BOX(box), bar);
    GtkWidget *menu_button = gtk_menu_button_new();
    gtk_menu_button_set_label(GTK_MENU_BUTTON(menu_button), "Options");
    gtk_menu_button_set_menu_model(GTK_MENU_BUTTON(menu_button), G_MENU_MODEL(menu));
    gtk_box_append(GTK_BOX(box), menu_button);

    const char *values[] = {"Birch", "Alder", "Cedar", NULL};
    GtkWidget *drop = gtk_drop_down_new_from_strings(values);
    gtk_drop_down_set_enable_search(GTK_DROP_DOWN(drop), TRUE);
    gtk_box_append(GTK_BOX(box), drop);
    GtkWidget *disabled = gtk_drop_down_new_from_strings(values);
    gtk_widget_set_sensitive(disabled, FALSE);
    gtk_box_append(GTK_BOX(box), disabled);
    GtkWidget *rtl = gtk_drop_down_new_from_strings(values);
    gtk_widget_set_direction(rtl, GTK_TEXT_DIR_RTL);
    gtk_widget_set_direction(gtk_widget_get_first_child(rtl), GTK_TEXT_DIR_RTL);
    gtk_widget_set_direction(find_node(rtl, "box"), GTK_TEXT_DIR_RTL);
    gtk_box_append(GTK_BOX(box), rtl);
    GtkStringList *strings = gtk_string_list_new(values);
    for (int i = 0; i < 40; i++) {
        g_autofree char *name = g_strdup_printf("Tree %02d", i);
        gtk_string_list_append(strings, name);
    }
    g_autoptr(GtkExpression) dropdown_text = gtk_property_expression_new(GTK_TYPE_STRING_OBJECT, NULL, "string");
    gtk_drop_down_set_expression(GTK_DROP_DOWN(drop), dropdown_text);
    gtk_drop_down_set_model(GTK_DROP_DOWN(drop), G_LIST_MODEL(strings));
    GtkSingleSelection *selection = gtk_single_selection_new(G_LIST_MODEL(g_object_ref(strings)));
    GtkWidget *view = gtk_list_view_new(GTK_SELECTION_MODEL(selection), string_factory());
    GtkWidget *scroller = gtk_scrolled_window_new();
    gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(scroller), view);
    gtk_widget_set_size_request(scroller, 270, 100);
    gtk_box_append(GTK_BOX(box), scroller);

    GtkSortListModel *sorted = gtk_sort_list_model_new(G_LIST_MODEL(strings), NULL);
    GtkSingleSelection *columns = gtk_single_selection_new(G_LIST_MODEL(sorted));
    GtkWidget *table = gtk_column_view_new(GTK_SELECTION_MODEL(columns));
    g_autoptr(GtkColumnViewColumn) col = gtk_column_view_column_new("Name", string_factory());
    GtkExpression *key = gtk_property_expression_new(GTK_TYPE_STRING_OBJECT, NULL, "string");
    g_autoptr(GtkStringSorter) sorter = gtk_string_sorter_new(key);
    gtk_column_view_column_set_sorter(col, GTK_SORTER(sorter));
    gtk_column_view_append_column(GTK_COLUMN_VIEW(table), col);
    gtk_sort_list_model_set_sorter(sorted, gtk_column_view_get_sorter(GTK_COLUMN_VIEW(table)));
    GtkWidget *table_scroll = gtk_scrolled_window_new();
    gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(table_scroll), table);
    gtk_widget_set_size_request(table_scroll, 270, 100);
    gtk_box_append(GTK_BOX(box), table_scroll);
    gtk_column_view_sort_by_column(GTK_COLUMN_VIEW(table), col, GTK_SORT_ASCENDING);
    gtk_single_selection_set_selected(columns, 1);
    gtk_window_present(GTK_WINDOW(window));
    gtk_widget_grab_focus(view);
    settle(400);
    GtkWidget *header = find_node(table, "header");
    GtkWidget *listrow = find_node(view, "row");
    GtkWidget *table_list = find_node(table, "listview");
    if (!header || !listrow || !table_list)
        return FALSE;
    GtkWidget *columnrow = gtk_widget_get_first_child(table_list);
    while (columnrow && !(gtk_widget_get_state_flags(columnrow) & GTK_STATE_FLAG_SELECTED))
        columnrow = gtk_widget_get_next_sibling(columnrow);
    gboolean ok = snapshot(window, "menus-lists.png");
    report_renderer(window);
    ok &= report_widget("bar", bar, window);
    ok &= report_widget("dropdown", drop, window);
    ok &= report_widget("dropdown-disabled", disabled, window);
    ok &= report_widget("dropdown-rtl", rtl, window);
    ok &= report_widget("list-row", listrow, window);
    ok &= columnrow && report_widget("column-row", columnrow, window);
    ok &= report_widget("header", gtk_widget_get_first_child(header), window);
    g_autoptr(GtkStringObject) first = g_list_model_get_item(G_LIST_MODEL(sorted), 0);
    gboolean ordered = g_str_equal(gtk_string_object_get_string(first), "Alder");
    printf("sorted=%d\n", ordered);
    ok &= ordered;

    const char *output = g_getenv("GTK4_CHECK_OUTPUT");
    if (output) {
        ok &= wayland && gtk_window_is_active(GTK_WINDOW(window)) && capture_output(output);
        gtk_window_destroy(GTK_WINDOW(window));
        return ok;
    }
    if (wayland) {
        GtkWidget *other = window_new("Inactive list witness");
        gtk_window_present(GTK_WINDOW(other));
        settle(350);
        ok &= gtk_window_is_active(GTK_WINDOW(other)) && !gtk_window_is_active(GTK_WINDOW(window));
        ok &= snapshot(window, "lists-backdrop.png");
        gtk_window_destroy(GTK_WINDOW(other));
        gtk_window_present(GTK_WINDOW(window));
        settle(250);
    }

    gtk_list_view_scroll_to(GTK_LIST_VIEW(view), 40, GTK_LIST_SCROLL_FOCUS | GTK_LIST_SCROLL_SELECT, NULL);
    settle(wayland ? 350 : 1500);
    GtkAdjustment *scroll = gtk_scrolled_window_get_vadjustment(GTK_SCROLLED_WINDOW(scroller));
    printf("position=%u scrolled=%d\n", gtk_single_selection_get_selected(selection), gtk_adjustment_get_value(scroll) > 0);
    ok &= gtk_single_selection_get_selected(selection) == 40 && gtk_adjustment_get_value(scroll) > 0;

    /* Exercise popup grabs and focus transitions in the nested Wayland session. */
    if (!wayland) {
        printf("interactions=%d\n", ok);
        gtk_window_destroy(GTK_WINDOW(window));
        return ok;
    }

    GtkWidget *drop_button = gtk_widget_get_first_child(drop);
    GtkWidget *popup = find_node(drop, "popover");
    GtkWidget *choices = find_node(popup, "listview");
    if (!popup || !choices)
        return FALSE;
    GtkWidget *choice_scroll = gtk_widget_get_ancestor(choices, GTK_TYPE_SCROLLED_WINDOW);
    if (!choice_scroll)
        return FALSE;
    /* Set a reproducible overflow viewport for the 43-item search test. */
    gtk_scrolled_window_set_max_content_height(GTK_SCROLLED_WINDOW(choice_scroll), 231);
    gtk_scrolled_window_set_min_content_height(GTK_SCROLLED_WINDOW(choice_scroll), 231);
    gtk_widget_activate(drop_button);
    settle(400);
    if (!gtk_widget_get_mapped(popup))
        return FALSE;
    ok &= save_frame(popup, "dropdown-open.png");
    ok &= save_frame(window, "dropdown-pressed.png");
    GtkAdjustment *range = gtk_scrolled_window_get_vadjustment(GTK_SCROLLED_WINDOW(choice_scroll));
    gboolean overflow = gtk_adjustment_get_upper(range) > gtk_adjustment_get_page_size(range);
    GtkWidget *search = find_node(popup, "entry");
    if (!GTK_IS_EDITABLE(search))
        return FALSE;
    gtk_editable_set_text(GTK_EDITABLE(search), "Cedar");
    settle(450);
    GtkSelectionModel *filtered = gtk_list_view_get_model(GTK_LIST_VIEW(choices));
    gboolean filtered_one = g_list_model_get_n_items(G_LIST_MODEL(filtered)) == 1;
    printf("overflow=%d filtered=%d\n", overflow, filtered_one);
    ok &= overflow && filtered_one;
    gtk_selection_model_select_item(filtered, 0, TRUE);
    g_signal_emit_by_name(choices, "activate", 0u);
    settle(300);
    printf("chosen=%u dropdown_closed=%d\n", gtk_drop_down_get_selected(GTK_DROP_DOWN(drop)), !gtk_widget_get_mapped(popup));
    ok &= gtk_drop_down_get_selected(GTK_DROP_DOWN(drop)) == 2 && !gtk_widget_get_mapped(popup);

    gtk_menu_button_popup(GTK_MENU_BUTTON(menu_button));
    settle(350);
    GtkWidget *popover = GTK_WIDGET(gtk_menu_button_get_popover(GTK_MENU_BUTTON(menu_button)));
    GtkWidget *item = find_node(popover, "modelbutton");
    if (!item || !gtk_widget_get_mapped(popover))
        return FALSE;
    gtk_widget_grab_focus(item);
    settle(200);
    ok &= save_frame(popover, "action-menu.png");
    ok &= report_widget("menu-item", item, popover);
    GtkWidget *checkmark = find_node(item, "check");
    ok &= checkmark && report_widget("menu-check", checkmark, popover);
    GtkWidget *radio = find_node(popover, "radio");
    GtkWidget *separator = find_node(popover, "separator");
    ok &= radio && report_widget("menu-radio", radio, popover);
    ok &= separator && report_widget("menu-separator", separator, popover);
    GtkWidget *more_row = menu_row(popover, "More");
    GtkWidget *arrow = more_row ? find_node(more_row, "arrow") : NULL;
    ok &= arrow && report_widget("submenu-arrow", arrow, popover);
    GtkWidget *next = gtk_widget_get_next_sibling(item);
    ok &= next && !gtk_widget_is_sensitive(next) && report_widget("menu-disabled", next, popover);
    ok &= gtk_widget_activate(item);
    settle(250);
    g_autoptr(GVariant) state = g_action_get_state(G_ACTION(details));
    printf("toggled=%d menu_closed=%d\n", !g_variant_get_boolean(state), !gtk_widget_get_mapped(popover));
    ok &= !g_variant_get_boolean(state) && !gtk_widget_get_mapped(popover);
    gtk_menu_button_popup(GTK_MENU_BUTTON(menu_button));
    settle(300);
    GtkWidget *icons_row = menu_row(popover, "Icons");
    ok &= icons_row && gtk_widget_activate(icons_row);
    settle(250);
    g_autoptr(GVariant) choice = g_action_get_state(G_ACTION(mode));
    ok &= g_str_equal(g_variant_get_string(choice, NULL), "icons");
    gtk_menu_button_popup(GTK_MENU_BUTTON(menu_button));
    settle(300);
    ok &= more_row && gtk_widget_activate(more_row);
    settle(250);
    GtkWidget *subitem = menu_row(popover, "Details");
    gboolean submenu_open = subitem && gtk_widget_get_mapped(subitem);
    printf("radio_changed=%d submenu_open=%d\n", g_str_equal(g_variant_get_string(choice, NULL), "icons"), submenu_open);
    ok &= submenu_open;
    gtk_menu_button_popdown(GTK_MENU_BUTTON(menu_button));
    printf("interactions=%d\n", ok);
    gtk_window_destroy(GTK_WINDOW(window));
    return ok;
}

int
main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s chrome|gallery|contrast|composites|menus\n", argv[0]);
        return 2;
    }

    gtk_init();
    g_autofree char *theme = NULL;
    g_object_get(gtk_settings_get_default(), "gtk-theme-name", &theme, NULL);
    const char *backend = G_OBJECT_TYPE_NAME(gdk_display_get_default());
    const char *override = g_getenv("GTK_THEME");
    printf("theme=%s backend=%s theme_override=%s gtk=%u.%u.%u\n",
           theme, backend, override ? override : "none",
           gtk_get_major_version(), gtk_get_minor_version(), gtk_get_micro_version());
    gboolean stock = g_str_equal(theme, "Adwaita");
    if (g_str_equal(argv[1], "composites") && (stock || g_str_equal(theme, "Platinum")))
        return composites() ? 0 : 1;
    if (g_str_equal(argv[1], "contrast") && (stock || g_str_equal(theme, "Platinum")))
        return contrast() ? 0 : 1;
    if (!g_str_equal(theme, "Platinum"))
        return 1;
    if (g_str_equal(argv[1], "menus"))
        return menus_lists(g_str_equal(backend, "GdkWaylandDisplay")) ? 0 : 1;
    if (g_str_equal(argv[1], "chrome"))
        return chrome() ? 0 : 1;
    if (g_str_equal(argv[1], "gallery"))
        return gallery(g_str_equal(backend, "GdkWaylandDisplay")) ? 0 : 1;
    return 2;
}
