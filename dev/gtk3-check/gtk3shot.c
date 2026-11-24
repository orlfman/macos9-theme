/*
 * Milestone 2 GTK 3 Platinum screenshot & metric capture tool.
 *
 * Modes:
 *   gtk3shot chrome <out.png> <coords.txt>
 *       Fixed-geometry 1x chrome sheet matching Mac OS 9.2.2 reference dimensions.
 *   gtk3shot dialog <active.png> <focus.png> <focus-check.png> <focus-radio.png> <backdrop.png> <metrics.txt> [output.png]
 *       Natural-size dialog testing text clipping, hit areas, active #CCCCFF
 *       selection, keyboard focus, and backdrop selection.
 *
 * Loads the named GTK 3 theme through normal GtkSettings discovery (no
 * process-local GTK_THEME override) and fails if any CSS parsing warning occurs.
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */
#include <gtk/gtk.h>
#include <sys/wait.h>
#include <cairo.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_css_errors = 0;

static void on_gtk_log(const gchar *domain, GLogLevelFlags level,
                       const gchar *message, gpointer user_data) {
    (void)domain;
    (void)user_data;
    if ((level & (G_LOG_LEVEL_WARNING | G_LOG_LEVEL_CRITICAL | G_LOG_LEVEL_ERROR)) &&
        message && (strstr(message, "Theme parsing error") || strstr(message, "CSS"))) {
        g_css_errors++;
        fprintf(stderr, "CSS_LOG_ERROR: %s\n", message);
    }
    g_log_default_handler(domain, level, message, user_data);
}

static void on_parse_error(GtkCssProvider *provider, GtkCssSection *section,
                           const GError *error, gpointer user_data) {
    (void)provider;
    (void)user_data;
    g_css_errors++;
    unsigned line = section ? gtk_css_section_get_start_line(section) + 1 : 0;
    unsigned col = section ? gtk_css_section_get_start_position(section) + 1 : 0;
    fprintf(stderr, "CSS_PARSE_ERROR: line %u col %u: %s\n",
            line, col, error ? error->message : "unknown");
}

static void validate_theme_css_file(const char *theme_name) {
    const char *xdg_data = g_getenv("XDG_DATA_HOME");
    if (!xdg_data || !*xdg_data)
        return;
    char *path = g_build_filename(xdg_data, "themes", theme_name, "gtk-3.0", "gtk.css", NULL);
    if (g_file_test(path, G_FILE_TEST_IS_REGULAR)) {
        GtkCssProvider *prov = gtk_css_provider_new();
        g_signal_connect(prov, "parsing-error", G_CALLBACK(on_parse_error), NULL);
        GError *err = NULL;
        if (!gtk_css_provider_load_from_path(prov, path, &err)) {
            g_css_errors++;
            fprintf(stderr, "CSS_LOAD_ERROR: %s: %s\n", path, err ? err->message : "failed");
            g_clear_error(&err);
        }
        g_object_unref(prov);
    } else if (strcmp(theme_name, "Platinum") == 0) {
        g_css_errors++;
        fprintf(stderr, "CSS_MISSING_ERROR: %s\n", path);
    }
    g_free(path);
}

static void pump_events(int ms) {
    gint64 end = g_get_monotonic_time() + (gint64)ms * 1000;
    while (g_get_monotonic_time() < end) {
        while (gtk_events_pending())
            gtk_main_iteration_do(FALSE);
        g_usleep(10000);
    }
    while (gtk_events_pending())
        gtk_main_iteration_do(FALSE);
}

static int save_widget_png(GtkWidget *w, const char *path) {
    GtkAllocation a;
    gtk_widget_get_allocation(w, &a);
    if (a.width <= 0 || a.height <= 0)
        return 0;
    int scale = gtk_widget_get_scale_factor(w);
    if (scale < 1)
        scale = 1;
    cairo_surface_t *surf = cairo_image_surface_create(
        CAIRO_FORMAT_ARGB32, a.width * scale, a.height * scale);
    cairo_surface_set_device_scale(surf, scale, scale);
    cairo_t *cr = cairo_create(surf);
    gtk_widget_draw(w, cr);
    cairo_destroy(cr);
    cairo_status_t st = cairo_surface_write_to_png(surf, path);
    cairo_surface_destroy(surf);
    return st == CAIRO_STATUS_SUCCESS ? 1 : 0;
}

typedef struct {
    const char *name;
    GtkWidget *w;
    int ind_w;
    int ind_h;
    int pad_x;
} Item;

static void record_item(FILE *fp, GtkWidget *root, const Item *it) {
    GtkAllocation a;
    gtk_widget_get_allocation(it->w, &a);
    gint rx = 0, ry = 0;
    gtk_widget_translate_coordinates(it->w, root, 0, 0, &rx, &ry);
    GtkRequisition min_r, nat_r;
    gtk_widget_get_preferred_size(it->w, &min_r, &nat_r);
    if (it->ind_w > 0 && it->ind_h > 0) {
        int ix = rx + it->pad_x;
        int iy = ry + (a.height - it->ind_h) / 2;
        fprintf(fp, "%s %d,%d,%d,%d alloc=%d,%d,%d,%d nat=%dx%d\n",
                it->name, ix, iy, it->ind_w, it->ind_h,
                rx, ry, a.width, a.height, nat_r.width, nat_r.height);
    } else {
        fprintf(fp, "%s %d,%d,%d,%d alloc=%d,%d,%d,%d nat=%dx%d\n",
                it->name, rx, ry, a.width, a.height,
                rx, ry, a.width, a.height, nat_r.width, nat_r.height);
    }
}

static GtkWidget *make_fixed_button(const char *cls, int w, int h,
                                    gboolean active, gboolean sensitive) {
    GtkWidget *b = gtk_button_new();
    gtk_widget_set_can_focus(b, FALSE);
    gtk_widget_set_size_request(b, w, h);
    if (cls)
        gtk_style_context_add_class(gtk_widget_get_style_context(b), cls);
    if (active)
        gtk_widget_set_state_flags(b, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_set_sensitive(b, sensitive);
    return b;
}

static GtkWidget *make_fixed_entry(int w, int h, gboolean focused, gboolean sensitive) {
    GtkWidget *e = gtk_entry_new();
    gtk_entry_set_width_chars(GTK_ENTRY(e), 1);
    gtk_widget_set_size_request(e, w, h);
    gtk_widget_set_can_focus(e, focused);
    if (focused) {
        /* The chrome comparison uses a blank field. GTK's Wayland caret
         * overlaps the inner white band, so hide it in this fixture only. */
        GtkCssProvider *provider = gtk_css_provider_new();
        gtk_css_provider_load_from_data(provider, "entry { caret-color: transparent; }", -1, NULL);
        gtk_style_context_add_provider(gtk_widget_get_style_context(e),
                                       GTK_STYLE_PROVIDER(provider),
                                       GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
        g_object_unref(provider);
        gtk_widget_set_state_flags(e, GTK_STATE_FLAG_FOCUSED, FALSE);
    }
    gtk_widget_set_sensitive(e, sensitive);
    return e;
}

static GtkWidget *make_fixed_check(gboolean checked, gboolean inconsistent,
                                   gboolean active, gboolean sensitive) {
    GtkWidget *c = gtk_check_button_new();
    gtk_widget_set_can_focus(c, FALSE);
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(c), checked);
    gtk_toggle_button_set_inconsistent(GTK_TOGGLE_BUTTON(c), inconsistent);
    if (active)
        gtk_widget_set_state_flags(c, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_set_sensitive(c, sensitive);
    return c;
}

static GtkWidget *make_fixed_radio(GSList **group, gboolean checked,
                                   gboolean active, gboolean sensitive) {
    GtkWidget *r = gtk_radio_button_new(*group);
    *group = gtk_radio_button_get_group(GTK_RADIO_BUTTON(r));
    gtk_widget_set_can_focus(r, FALSE);
    if (checked)
        gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(r), TRUE);
    if (active)
        gtk_widget_set_state_flags(r, GTK_STATE_FLAG_ACTIVE, FALSE);
    gtk_widget_set_sensitive(r, sensitive);
    return r;
}

static gboolean on_chrome_draw(GtkWidget *w, cairo_t *cr, gpointer data) {
    (void)w;
    (void)data;
    /* Match reference capture backdrops (same as dev/styleshot.cpp:173-174,295):
     * push-normal/pressed/default-pressed sit on white dialogs; entries on #EEEEEE tab pane. */
    cairo_set_source_rgb(cr, 1.0, 1.0, 1.0);
    cairo_rectangle(cr, 5, 2, 160, 36);
    cairo_rectangle(cr, 355, 2, 90, 36);
    cairo_fill(cr);

    cairo_set_source_rgb(cr, 0xEE / 255.0, 0xEE / 255.0, 0xEE / 255.0);
    cairo_rectangle(cr, 5, 44, 150, 38);
    cairo_fill(cr);
    return FALSE;
}

static int run_chrome(const char *out_png, const char *coords_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_decorated(GTK_WINDOW(win), FALSE);
    gtk_window_set_resizable(GTK_WINDOW(win), FALSE);
    gtk_window_set_default_size(GTK_WINDOW(win), 560, 200);

    GtkWidget *fixed = gtk_fixed_new();
    gtk_widget_set_size_request(fixed, 560, 200);
    g_signal_connect(fixed, "draw", G_CALLBACK(on_chrome_draw), NULL);
    gtk_container_add(GTK_CONTAINER(win), fixed);

    Item items[32];
    int n = 0;

    #define PUT(nm, wid, x, y, iw, ih, px) do { \
        GtkWidget *_w = (wid); \
        gtk_fixed_put(GTK_FIXED(fixed), _w, (x), (y)); \
        items[n++] = (Item){ (nm), _w, (iw), (ih), (px) }; \
    } while (0)

    /* Row 1: Push buttons (measured sizes from check-style.sh:44-49) */
    PUT("push-normal",          make_fixed_button(NULL,      70, 20, FALSE, TRUE),  10,  10, 0, 0, 0);
    PUT("push-pressed",         make_fixed_button(NULL,      70, 20, TRUE,  TRUE),  90,  10, 0, 0, 0);
    PUT("push-disabled",        make_fixed_button(NULL,      80, 20, FALSE, FALSE), 170, 10, 0, 0, 0);
    PUT("push-default",         make_fixed_button("default", 86, 26, FALSE, TRUE),  260,  7, 0, 0, 0);
    PUT("push-default-pressed", make_fixed_button("default", 78, 26, TRUE,  TRUE),  360,  7, 0, 0, 0);
    PUT("push-default-disabled",make_fixed_button("default", 86, 26, FALSE, FALSE), 450,  7, 0, 0, 0);

    /* Row 2: Text entries (measured 30x26 from appearance-3-fonts-clean.png) */
    GtkWidget *e_norm = make_fixed_entry(30, 26, FALSE, TRUE);
    GtkWidget *e_foc  = make_fixed_entry(30, 26, TRUE,  TRUE);
    GtkWidget *e_dis  = make_fixed_entry(30, 26, FALSE, FALSE);
    PUT("entry-normal",   e_norm, 10, 50, 0, 0, 0);
    PUT("entry-focused",  e_foc,  60, 50, 0, 0, 0);
    PUT("entry-disabled", e_dis, 110, 50, 0, 0, 0);

    /* Row 3: Checkboxes (14x12 indicator sprites; checkbutton padding-left=2px) */
    PUT("check-off",          make_fixed_check(FALSE, FALSE, FALSE, TRUE),   10, 100, 14, 12, 2);
    PUT("check-on",           make_fixed_check(TRUE,  FALSE, FALSE, TRUE),   40, 100, 14, 12, 2);
    PUT("check-off-pressed",  make_fixed_check(FALSE, FALSE, TRUE,  TRUE),   70, 100, 14, 12, 2);
    PUT("check-on-pressed",   make_fixed_check(TRUE,  FALSE, TRUE,  TRUE),  100, 100, 14, 12, 2);
    PUT("check-mixed",        make_fixed_check(FALSE, TRUE,  FALSE, TRUE),  130, 100, 14, 12, 2);
    PUT("check-off-disabled", make_fixed_check(FALSE, FALSE, FALSE, FALSE), 160, 100, 14, 12, 2);
    PUT("check-on-disabled",  make_fixed_check(TRUE,  FALSE, FALSE, FALSE), 190, 100, 14, 12, 2);

    /* Row 4: Radio buttons (12x12 indicator sprites; separate groups so each state is independent) */
    GSList *g_off = NULL, *g_on = NULL, *g_op = NULL, *g_onp = NULL, *g_od = NULL, *g_ond = NULL;
    GtkWidget *dummy;
    /* Dummy active leaders off-canvas for each "off" group */
    dummy = gtk_radio_button_new(NULL); g_off = gtk_radio_button_get_group(GTK_RADIO_BUTTON(dummy));
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(dummy), TRUE);
    dummy = gtk_radio_button_new(NULL); g_op  = gtk_radio_button_get_group(GTK_RADIO_BUTTON(dummy));
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(dummy), TRUE);
    dummy = gtk_radio_button_new(NULL); g_od  = gtk_radio_button_get_group(GTK_RADIO_BUTTON(dummy));
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(dummy), TRUE);

    PUT("radio-off",          make_fixed_radio(&g_off, FALSE, FALSE, TRUE),   10, 140, 12, 12, 2);
    PUT("radio-on",           make_fixed_radio(&g_on,  TRUE,  FALSE, TRUE),   40, 140, 12, 12, 2);
    PUT("radio-off-pressed",  make_fixed_radio(&g_op,  FALSE, TRUE,  TRUE),   70, 140, 12, 12, 2);
    PUT("radio-on-pressed",   make_fixed_radio(&g_onp, TRUE,  TRUE,  TRUE),  100, 140, 12, 12, 2);
    PUT("radio-off-disabled", make_fixed_radio(&g_od,  FALSE, FALSE, FALSE), 130, 140, 12, 12, 2);
    PUT("radio-on-disabled",  make_fixed_radio(&g_ond, TRUE,  FALSE, FALSE), 160, 140, 12, 12, 2);

    #undef PUT

    gtk_widget_show_all(win);
    gtk_widget_grab_focus(e_foc);
    pump_events(250);

    /* Ensure pressed/focused flags didn't clear during realize */
    for (int i = 0; i < n; i++) {
        if (strstr(items[i].name, "pressed"))
            gtk_widget_set_state_flags(items[i].w, GTK_STATE_FLAG_ACTIVE, FALSE);
        if (strcmp(items[i].name, "entry-focused") == 0)
            gtk_widget_set_state_flags(items[i].w, GTK_STATE_FLAG_FOCUSED, FALSE);
    }
    pump_events(120);

    int ok = save_widget_png(win, out_png);

    FILE *fp = fopen(coords_txt, "w");
    if (!fp) {
        perror(coords_txt);
        return 1;
    }
    GtkSettings *st = gtk_settings_get_default();
    gchar *theme = NULL;
    g_object_get(st, "gtk-theme-name", &theme, NULL);
    GdkDisplay *disp = gdk_display_get_default();
    fprintf(fp, "# theme=%s backend=%s scale=%d css_errors=%d png_ok=%d\n",
            theme ? theme : "",
            disp ? G_OBJECT_TYPE_NAME(disp) : "none",
            gtk_widget_get_scale_factor(win),
            g_css_errors,
            ok);
    g_free(theme);
    for (int i = 0; i < n; i++)
        record_item(fp, win, &items[i]);
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok && g_css_errors == 0) ? 0 : 1;
}

static void set_backdrop_recursive(GtkWidget *w, gboolean backdrop) {
    if (backdrop)
        gtk_widget_set_state_flags(w, GTK_STATE_FLAG_BACKDROP, FALSE);
    else
        gtk_widget_unset_state_flags(w, GTK_STATE_FLAG_BACKDROP);
    if (GTK_IS_CONTAINER(w)) {
        GList *children = gtk_container_get_children(GTK_CONTAINER(w));
        for (GList *l = children; l; l = l->next)
            set_backdrop_recursive(GTK_WIDGET(l->data), backdrop);
        g_list_free(children);
    }
}

static gboolean tab_to(GtkWidget *window, GtkWidget *target) {
    for (int step = 0; step < 16; step++) {
        gtk_widget_child_focus(window, GTK_DIR_TAB_FORWARD);
        if (gtk_window_get_focus(GTK_WINDOW(window)) == target)
            return TRUE;
    }
    fprintf(stderr, "Tab traversal failed to reach %s\n", G_OBJECT_TYPE_NAME(target));
    return FALSE;
}

static gboolean capture_output(const char *path) {
    if (!path)
        return TRUE;
    gchar *args[] = {"timeout", "15", "spectacle", "-b", "-n", "-f", "-o", (char *)path, NULL};
    gint status = 0;
    GError *error = NULL;
    if (g_spawn_sync(NULL, args, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL,
                     NULL, NULL, &status, &error) && WIFEXITED(status) && WEXITSTATUS(status) == 0)
        return TRUE;
    fprintf(stderr, "Compositor capture failed: %s\n", error ? error->message : path);
    g_clear_error(&error);
    return FALSE;
}

static int run_dialog(const char *active_png, const char *focus_png,
                      const char *focus_check_png, const char *focus_radio_png,
                      const char *backdrop_png, const char *metrics_txt, const char *output_png) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(win), "Platinum Dialog");
    gtk_window_set_resizable(GTK_WINDOW(win), FALSE);
    gtk_container_set_border_width(GTK_CONTAINER(win), 10);

    GtkWidget *vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
    gtk_container_add(GTK_CONTAINER(win), vbox);

    GtkWidget *hdr = gtk_label_new("Platinum GTK 3 Vertical Slice");
    gtk_widget_set_halign(hdr, GTK_ALIGN_START);
    gtk_box_pack_start(GTK_BOX(vbox), hdr, FALSE, FALSE, 0);

    GtkWidget *e_sel = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(e_sel), "Selected Platinum text");
    gtk_entry_set_width_chars(GTK_ENTRY(e_sel), 24);
    gtk_box_pack_start(GTK_BOX(vbox), e_sel, FALSE, FALSE, 0);

    GtkWidget *e_norm = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(e_norm), "Unfocused entry");
    gtk_box_pack_start(GTK_BOX(vbox), e_norm, FALSE, FALSE, 0);

    GtkWidget *e_dis = gtk_entry_new();
    gtk_entry_set_text(GTK_ENTRY(e_dis), "Disabled entry");
    gtk_widget_set_sensitive(e_dis, FALSE);
    gtk_box_pack_start(GTK_BOX(vbox), e_dis, FALSE, FALSE, 0);

    GtkWidget *c_off = gtk_check_button_new_with_label("Unchecked option");
    GtkWidget *c_on  = gtk_check_button_new_with_label("Checked option");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(c_on), TRUE);
    GtkWidget *c_mix = gtk_check_button_new_with_label("Mixed option");
    gtk_toggle_button_set_inconsistent(GTK_TOGGLE_BUTTON(c_mix), TRUE);
    GtkWidget *c_dis = gtk_check_button_new_with_label("Disabled checked");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(c_dis), TRUE);
    gtk_widget_set_sensitive(c_dis, FALSE);
    gtk_box_pack_start(GTK_BOX(vbox), c_off, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), c_on,  FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), c_mix, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), c_dis, FALSE, FALSE, 0);

    GtkWidget *r_one = gtk_radio_button_new_with_label(NULL, "Lavender accent");
    GSList *rgrp = gtk_radio_button_get_group(GTK_RADIO_BUTTON(r_one));
    GtkWidget *r_two = gtk_radio_button_new_with_label(rgrp, "Classic choice");
    rgrp = gtk_radio_button_get_group(GTK_RADIO_BUTTON(r_two));
    GtkWidget *r_dis = gtk_radio_button_new_with_label(rgrp, "Disabled radio");
    gtk_widget_set_sensitive(r_dis, FALSE);
    gtk_box_pack_start(GTK_BOX(vbox), r_one, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), r_two, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(vbox), r_dis, FALSE, FALSE, 0);

    GtkWidget *hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    gtk_widget_set_halign(hbox, GTK_ALIGN_END);
    gtk_widget_set_margin_top(hbox, 6);
    gtk_box_pack_start(GTK_BOX(vbox), hbox, FALSE, FALSE, 0);

    GtkWidget *b_cancel = gtk_button_new_with_label("Cancel");
    gtk_widget_set_receives_default(b_cancel, FALSE);
    GtkWidget *b_dis    = gtk_button_new_with_label("Apply");
    gtk_widget_set_sensitive(b_dis, FALSE);
    GtkWidget *b_ok     = gtk_button_new_with_label("OK");
    gtk_widget_set_can_default(b_ok, TRUE);
    gtk_box_pack_start(GTK_BOX(hbox), b_cancel, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(hbox), b_dis,    FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(hbox), b_ok,     FALSE, FALSE, 0);

    gtk_widget_show_all(win);
    gtk_widget_grab_default(b_ok);
    gtk_widget_grab_focus(e_sel);
    pump_events(250);

    /* Ensure window has focus on WM-less Broadway so :focus CSS is exercised */
    if (strcmp(G_OBJECT_TYPE_NAME(gdk_display_get_default()), "GdkBroadwayDisplay") == 0 &&
        !gtk_window_has_toplevel_focus(GTK_WINDOW(win))) {
        GdkEvent *ev = gdk_event_new(GDK_FOCUS_CHANGE);
        ev->focus_change.window = g_object_ref(gtk_widget_get_window(win));
        ev->focus_change.send_event = TRUE;
        ev->focus_change.in = TRUE;
        gtk_main_do_event(ev);
        gdk_event_free(ev);
        pump_events(100);
    }

    /* Select text after the compositor has delivered initial focus. */
    gtk_editable_select_region(GTK_EDITABLE(e_sel), 0, 17);
    pump_events(100);
    /* 1. Active dialog with focused entry + #CCCCFF active text selection */
    gboolean real_active = gtk_window_is_active(GTK_WINDOW(win));
    int ok_active = save_widget_png(win, active_png) && capture_output(output_png);

    /* 2a. Keyboard focus on normal button ("Cancel") */
    gtk_window_set_focus_visible(GTK_WINDOW(win), TRUE);
    if (!tab_to(win, b_cancel)) {
        gtk_widget_destroy(win);
        return 1;
    }
    pump_events(120);
    int ok_focus = save_widget_png(win, focus_png);

    /* 2b. Keyboard focus on checkbutton ("Unchecked option") */
    if (!tab_to(win, c_off)) {
        gtk_widget_destroy(win);
        return 1;
    }
    pump_events(120);
    int ok_focus_check = save_widget_png(win, focus_check_png);

    /* 2c. Keyboard focus on radiobutton ("Lavender accent") */
    if (!tab_to(win, r_one)) {
        gtk_widget_destroy(win);
        return 1;
    }
    pump_events(120);
    int ok_focus_radio = save_widget_png(win, focus_radio_png);
    gtk_window_set_focus_visible(GTK_WINDOW(win), FALSE);

    /* 3. Backdrop / inactive window with selected text in e_sel.
     * On Wayland/KWin, open a second top-level window to trigger real compositor
     * deactivation; also ensure GTK_STATE_FLAG_BACKDROP is active on Broadway. */
    gtk_widget_grab_focus(e_sel);
    gtk_editable_select_region(GTK_EDITABLE(e_sel), 0, 17);
    pump_events(100);
    GtkWidget *other = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(other), "Other Window");
    gtk_window_set_default_size(GTK_WINDOW(other), 120, 80);
    gtk_widget_show_all(other);
    gtk_window_present(GTK_WINDOW(other));
    pump_events(250);
    gboolean real_backdrop = (gtk_widget_get_state_flags(win) & GTK_STATE_FLAG_BACKDROP) != 0;
    if (!real_backdrop && strcmp(G_OBJECT_TYPE_NAME(gdk_display_get_default()), "GdkBroadwayDisplay") == 0) {
        set_backdrop_recursive(win, TRUE);
        pump_events(100);
    }
    int ok_backdrop = save_widget_png(win, backdrop_png);
    gtk_widget_destroy(other);

    Item items[] = {
        { "entry-selected", e_sel, 0, 0, 0 },
        { "entry-normal",   e_norm, 0, 0, 0 },
        { "entry-disabled", e_dis, 0, 0, 0 },
        { "check-off",      c_off, 0, 0, 0 },
        { "check-on",       c_on, 0, 0, 0 },
        { "check-mixed",    c_mix, 0, 0, 0 },
        { "check-disabled", c_dis, 0, 0, 0 },
        { "radio-one",      r_one, 0, 0, 0 },
        { "radio-two",      r_two, 0, 0, 0 },
        { "radio-disabled", r_dis, 0, 0, 0 },
        { "btn-cancel",     b_cancel, 0, 0, 0 },
        { "btn-disabled",   b_dis, 0, 0, 0 },
        { "btn-ok-default", b_ok, 0, 0, 0 },
    };

    FILE *fp = fopen(metrics_txt, "w");
    if (!fp) {
        perror(metrics_txt);
        return 1;
    }
    GtkSettings *st = gtk_settings_get_default();
    gchar *theme = NULL;
    g_object_get(st, "gtk-theme-name", &theme, NULL);
    GdkDisplay *disp = gdk_display_get_default();
    fprintf(fp, "# theme=%s backend=%s scale=%d css_errors=%d default_class=%d real_active=%d real_backdrop=%d ok_active=%d ok_focus=%d ok_focus_check=%d ok_focus_radio=%d ok_backdrop=%d\n",
            theme ? theme : "",
            disp ? G_OBJECT_TYPE_NAME(disp) : "none",
            gtk_widget_get_scale_factor(win),
            g_css_errors,
            gtk_style_context_has_class(gtk_widget_get_style_context(b_ok), "default") ? 1 : 0,
            real_active ? 1 : 0,
            real_backdrop ? 1 : 0,
            ok_active, ok_focus, ok_focus_check, ok_focus_radio, ok_backdrop);
    g_free(theme);
    for (size_t i = 0; i < G_N_ELEMENTS(items); i++)
        record_item(fp, win, &items[i]);
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok_active && ok_focus && ok_focus_check && ok_focus_radio && ok_backdrop && g_css_errors == 0) ? 0 : 1;
}

int main(int argc, char **argv) {
    g_log_set_handler("Gtk", G_LOG_LEVEL_MASK | G_LOG_FLAG_FATAL | G_LOG_FLAG_RECURSION,
                      on_gtk_log, NULL);
    gtk_init(&argc, &argv);

    GtkSettings *st = gtk_settings_get_default();
    gchar *theme = NULL;
    g_object_get(st, "gtk-theme-name", &theme, NULL);
    if (theme && *theme)
        validate_theme_css_file(theme);
    g_free(theme);

    if (argc == 4 && strcmp(argv[1], "chrome") == 0)
        return run_chrome(argv[2], argv[3]);
    if ((argc == 8 || argc == 9) && strcmp(argv[1], "dialog") == 0)
        return run_dialog(argv[2], argv[3], argv[4], argv[5], argv[6], argv[7], argc == 9 ? argv[8] : NULL);

    fprintf(stderr, "usage: %s chrome <out.png> <coords.txt> | dialog <active.png> <focus.png> <focus-check.png> <focus-radio.png> <backdrop.png> <metrics.txt> [output.png]\n", argv[0]);
    return 2;
}
