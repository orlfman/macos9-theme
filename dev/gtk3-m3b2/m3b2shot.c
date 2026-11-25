/*
 * Milestone 3 Batch 2 GTK 3 Platinum capture & interaction tool:
 *   - Notebook tabs & pane, scales/sliders + ticks, classic Smart Scrolling
 *     scrollbars (with real stepper button press/release clicks), overlay
 *     scrollbars, determinate + barber-pole progress bars, Help Balloon
 *     tooltips, dialogs + modal frame, and CSD HeaderBars (active, backdrop,
 *     narrow, and maximized).
 *
 * Modes:
 *   m3b2shot chrome  <out.png> <coords.txt>
 *   m3b2shot gallery <active.png> <focus.png> <backdrop.png> <dialog.png> <tooltip.png> <metrics.txt>
 *   m3b2shot overlay <overlay.png> <metrics.txt>
 *   m3b2shot csd     <active.png> <backdrop.png> <narrow.png> <max.png> <metrics.txt>
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */
#include <gtk/gtk.h>
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
} Item;

static void record_item(FILE *fp, GtkWidget *root, const Item *it) {
    GtkAllocation a;
    gtk_widget_get_allocation(it->w, &a);
    gint rx = 0, ry = 0;
    gtk_widget_translate_coordinates(it->w, root, 0, 0, &rx, &ry);
    GtkRequisition min_r, nat_r;
    gtk_widget_get_preferred_size(it->w, &min_r, &nat_r);
    fprintf(fp, "%s %d,%d,%d,%d alloc=%d,%d,%d,%d nat=%dx%d\n",
            it->name, rx, ry, a.width, a.height,
            rx, ry, a.width, a.height, nat_r.width, nat_r.height);
}

static void set_backdrop_cb(GtkWidget *w, gpointer data) {
    gboolean backdrop = GPOINTER_TO_INT(data) != 0;
    if (backdrop)
        gtk_widget_set_state_flags(w, GTK_STATE_FLAG_BACKDROP, FALSE);
    else
        gtk_widget_unset_state_flags(w, GTK_STATE_FLAG_BACKDROP);
    if (GTK_IS_CONTAINER(w))
        gtk_container_forall(GTK_CONTAINER(w), set_backdrop_cb, data);
}

static void set_backdrop_recursive(GtkWidget *w, gboolean backdrop) {
    set_backdrop_cb(w, GINT_TO_POINTER(backdrop ? 1 : 0));
}

static GtkWidget *make_notebook_6tabs(int pane_w, int pane_h, int current_idx) {
    static const int widths[6] = {72, 101, 57, 74, 62, 71};
    GtkWidget *nb = gtk_notebook_new();
    gtk_notebook_set_show_border(GTK_NOTEBOOK(nb), TRUE);
    gtk_widget_set_can_focus(nb, FALSE);
    /* stack has 3px border on left/right/top/bottom -> page inside stack is (pane_w - 6) x (pane_h - 6) */
    for (int i = 0; i < 6; i++) {
        GtkWidget *page = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
        gtk_widget_set_size_request(page, pane_w - 6, pane_h - 6);
        GtkWidget *tab_box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
        /* tab has padding: 3px 12px -> content box is (widths[i] - 24) x 18 */
        gtk_widget_set_size_request(tab_box, widths[i] - 24, 18);
        gtk_notebook_append_page(GTK_NOTEBOOK(nb), page, tab_box);
    }
    gtk_widget_show_all(nb);
    gtk_notebook_set_current_page(GTK_NOTEBOOK(nb), current_idx);
    return nb;
}

static void mark_scale_slider_active(GtkWidget *scale) {
    /* Setting ACTIVE on GtkScale propagates or let's set ACTIVE on scale's StyleContext;
     * actually GtkScale draws its slider subnode with ACTIVE when GTK_STATE_FLAG_ACTIVE
     * is set on the GtkScale widget or via button press! Let's synthesize a real button press
     * on the center of the scale thumb so GtkRange sets slider ACTIVE natively! */
    GtkAllocation a;
    gtk_widget_get_allocation(scale, &a);
    GdkWindow *gw = gtk_widget_get_window(scale);
    if (!gw)
        return;
    GdkDisplay *disp = gdk_window_get_display(gw);
    GdkSeat *seat = gdk_display_get_default_seat(disp);
    GdkDevice *ptr = gdk_seat_get_pointer(seat);
    /* Find event window at center of scale */
    gint wx = 0, wy = 0;
    gtk_widget_translate_coordinates(scale, gtk_widget_get_toplevel(scale), a.width / 2, 8, &wx, &wy);
    GdkEvent *ev = gdk_event_new(GDK_BUTTON_PRESS);
    ev->button.window = g_object_ref(gw);
    /* GtkRange uses its own input-only event window child if present */
    GList *children = gdk_window_get_children(gw);
    for (GList *l = children; l; l = l->next) {
        GdkWindow *cw = GDK_WINDOW(l->data);
        int cx, cy, cw_w, cw_h;
        gdk_window_get_geometry(cw, &cx, &cy, &cw_w, &cw_h);
        if (wx >= cx && wx < cx + cw_w && wy >= cy && wy < cy + cw_h) {
            g_object_unref(ev->button.window);
            ev->button.window = g_object_ref(cw);
            wx -= cx;
            wy -= cy;
            break;
        }
    }
    g_list_free(children);
    ev->button.send_event = TRUE;
    ev->button.time = GDK_CURRENT_TIME;
    ev->button.x = wx;
    ev->button.y = wy;
    ev->button.button = 1;
    gdk_event_set_device(ev, ptr);
    gtk_main_do_event(ev);
    gdk_event_free(ev);
}

static int run_chrome(const char *out_png, const char *coords_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_decorated(GTK_WINDOW(win), FALSE);
    gtk_window_set_resizable(GTK_WINDOW(win), FALSE);
    gtk_window_set_default_size(GTK_WINDOW(win), 1040, 960);

    GtkWidget *fixed = gtk_fixed_new();
    gtk_widget_set_size_request(fixed, 1040, 960);
    gtk_container_add(GTK_CONTAINER(win), fixed);

    Item items[32];
    int n = 0;
    #define PUT(nm, wid, x, y) do { \
        GtkWidget *_w = (wid); \
        gtk_fixed_put(GTK_FIXED(fixed), _w, (x), (y)); \
        items[n++] = (Item){ (nm), _w }; \
    } while (0)

    /* 1. Classic Smart Scrolling scrollbars (exact check-style.sh dimensions & adjustments) */
    GtkAdjustment *adj_vtop = gtk_adjustment_new(0, 0, 1975, 20, 975, 975);
    GtkWidget *sb_vtop = gtk_scrollbar_new(GTK_ORIENTATION_VERTICAL, adj_vtop);
    gtk_widget_set_size_request(sb_vtop, 16, 347);
    PUT("vbar-top", sb_vtop, 560, 10);

    GtkAdjustment *adj_vmid = gtk_adjustment_new(252, 0, 1708, 20, 708, 708);
    GtkWidget *sb_vmid = gtk_scrollbar_new(GTK_ORIENTATION_VERTICAL, adj_vmid);
    gtk_widget_set_size_request(sb_vmid, 16, 323);
    PUT("vbar-mid", sb_vmid, 600, 10);

    GtkAdjustment *adj_hbar = gtk_adjustment_new(0, 0, 2266, 20, 1266, 1266);
    GtkWidget *sb_hbar = gtk_scrollbar_new(GTK_ORIENTATION_HORIZONTAL, adj_hbar);
    gtk_widget_set_size_request(sb_hbar, 389, 16);
    PUT("hbar", sb_hbar, 10, 380);

    /* 2. Scales / Sliders (91x23 with 3 ticks at 0,1,2 value=1; 91x23 pressed; 140x16 disabled) */
    GtkWidget *sc_norm = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 2, 1);
    gtk_scale_set_draw_value(GTK_SCALE(sc_norm), FALSE);
    gtk_range_set_value(GTK_RANGE(sc_norm), 1);
    gtk_scale_add_mark(GTK_SCALE(sc_norm), 0, GTK_POS_BOTTOM, NULL);
    gtk_scale_add_mark(GTK_SCALE(sc_norm), 1, GTK_POS_BOTTOM, NULL);
    gtk_scale_add_mark(GTK_SCALE(sc_norm), 2, GTK_POS_BOTTOM, NULL);
    gtk_widget_set_size_request(sc_norm, 91, 23);
    gtk_widget_set_can_focus(sc_norm, FALSE);
    PUT("slider", sc_norm, 10, 50);

    GtkWidget *sc_prs = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 2, 1);
    gtk_scale_set_draw_value(GTK_SCALE(sc_prs), FALSE);
    gtk_range_set_value(GTK_RANGE(sc_prs), 1);
    gtk_scale_add_mark(GTK_SCALE(sc_prs), 0, GTK_POS_BOTTOM, NULL);
    gtk_scale_add_mark(GTK_SCALE(sc_prs), 1, GTK_POS_BOTTOM, NULL);
    gtk_scale_add_mark(GTK_SCALE(sc_prs), 2, GTK_POS_BOTTOM, NULL);
    gtk_widget_set_size_request(sc_prs, 91, 23);
    gtk_widget_set_can_focus(sc_prs, FALSE);
    PUT("slider-pressed", sc_prs, 120, 50);

    GtkWidget *sc_dis = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 2, 1);
    gtk_scale_set_draw_value(GTK_SCALE(sc_dis), FALSE);
    gtk_range_set_value(GTK_RANGE(sc_dis), 0);
    gtk_widget_set_sensitive(sc_dis, FALSE);
    gtk_widget_set_size_request(sc_dis, 140, 16);
    PUT("slider-disabled", sc_dis, 230, 50);

    /* 3. Progress bars (188x14 at 101/184, 0/184, and indeterminate barber pole) */
    GtkWidget *pb_55 = gtk_progress_bar_new();
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_55), 101.0 / 184.0);
    gtk_widget_set_size_request(pb_55, 188, 14);
    PUT("progress-55", pb_55, 10, 100);

    GtkWidget *pb_0 = gtk_progress_bar_new();
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_0), 0.0);
    gtk_widget_set_size_request(pb_0, 188, 14);
    PUT("progress-0", pb_0, 220, 100);

    GtkWidget *pb_busy = gtk_progress_bar_new();
    gtk_progress_bar_set_pulse_step(GTK_PROGRESS_BAR(pb_busy), 0.0);
    gtk_progress_bar_pulse(GTK_PROGRESS_BAR(pb_busy));
    gtk_widget_set_size_request(pb_busy, 310, 14);
    PUT("progress-busy", pb_busy, 10, 130);

    GtkWidget *pb_reverse = gtk_progress_bar_new();
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_reverse), 101.0 / 184.0);
    gtk_progress_bar_set_inverted(GTK_PROGRESS_BAR(pb_reverse), TRUE);
    gtk_widget_set_size_request(pb_reverse, 188, 14);
    PUT("progress-reversed", pb_reverse, 345, 130);

    GtkWidget *pb_vertical = gtk_progress_bar_new();
    gtk_orientable_set_orientation(GTK_ORIENTABLE(pb_vertical), GTK_ORIENTATION_VERTICAL);
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_vertical), 101.0 / 184.0);
    gtk_progress_bar_set_inverted(GTK_PROGRESS_BAR(pb_vertical), TRUE);
    gtk_widget_set_size_request(pb_vertical, 14, 188);
    PUT("progress-vertical-reversed", pb_vertical, 475, 160);

    GtkWidget *pb_tiny = gtk_progress_bar_new();
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_tiny), 0.001);
    gtk_widget_set_size_request(pb_tiny, 188, 14);
    PUT("progress-tiny", pb_tiny, 220, 145);

    GtkWidget *pb_tiny_vertical = gtk_progress_bar_new();
    gtk_orientable_set_orientation(GTK_ORIENTABLE(pb_tiny_vertical), GTK_ORIENTATION_VERTICAL);
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_tiny_vertical), 0.001);
    gtk_widget_set_size_request(pb_tiny_vertical, 14, 188);
    PUT("progress-vertical-tiny", pb_tiny_vertical, 505, 160);

    GtkWidget *pb_full = gtk_progress_bar_new();
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb_full), 1.0);
    gtk_widget_set_size_request(pb_full, 188, 14);
    PUT("progress-full", pb_full, 420, 380);

    GtkWidget *pb_busy_vertical = gtk_progress_bar_new();
    gtk_orientable_set_orientation(GTK_ORIENTABLE(pb_busy_vertical), GTK_ORIENTATION_VERTICAL);
    gtk_progress_bar_pulse(GTK_PROGRESS_BAR(pb_busy_vertical));
    gtk_widget_set_size_request(pb_busy_vertical, 14, 188);
    PUT("progress-vertical-busy", pb_busy_vertical, 530, 160);

    /* 4. Modal dialog frame (386x189 outline + 1px shadow = 387x190, dialog-modal-plain.png) */
    GtkWidget *modal_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
    gtk_style_context_add_class(gtk_widget_get_style_context(modal_box), "platinum-modal-frame");
    gtk_widget_set_size_request(modal_box, 387, 190);
    PUT("modal-frame", modal_box, 10, 165);

    /* 5. Tooltip Help Balloon (160x121, help-balloon.png) */
    GtkWidget *balloon_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
    gtk_style_context_add_class(gtk_widget_get_style_context(balloon_box), "tooltip");
    gtk_widget_set_size_request(balloon_box, 160, 121);
    PUT("balloon", balloon_box, 650, 10);

    /* 6. Notebook tabs (exact 6-tab Appearance row + 466x280 pane; tabs 0, 1, and 5 current) */
    GtkWidget *nb_themes = make_notebook_6tabs(466, 280, 0);
    PUT("tabs-themes", nb_themes, 5, 420);

    GtkWidget *nb_appearance = make_notebook_6tabs(466, 40, 1);
    PUT("tabs-appearance", nb_appearance, 520, 420);

    GtkWidget *nb_options = make_notebook_6tabs(466, 40, 5);
    PUT("tabs-options", nb_options, 520, 510);

    #undef PUT

    gtk_widget_show_all(win);
    pump_events(250);

    /* Press slider-pressed thumb natively via GDK button press */
    mark_scale_slider_active(sc_prs);

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

    /* Also record the exact pane (stack) coordinates of each notebook */
    struct { const char *nm; GtkWidget *nb; int idx; } panes[3] = {
        { "pane-themes", nb_themes, 0 },
        { "pane-appearance", nb_appearance, 1 },
        { "pane-options", nb_options, 5 },
    };
    for (int i = 0; i < 3; i++) {
        GtkWidget *pg = gtk_notebook_get_nth_page(GTK_NOTEBOOK(panes[i].nb), panes[i].idx);
        GtkAllocation a;
        gtk_widget_get_allocation(pg, &a);
        gint rx = 0, ry = 0;
        gtk_widget_translate_coordinates(pg, win, 0, 0, &rx, &ry);
        /* stack border is 3px around page */
        fprintf(fp, "%s %d,%d,%d,%d alloc=%d,%d,%d,%d nat=%dx%d\n",
                panes[i].nm, rx - 3, ry - 3, a.width + 6, a.height + 6,
                rx - 3, ry - 3, a.width + 6, a.height + 6, a.width + 6, a.height + 6);
    }
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok && g_css_errors == 0) ? 0 : 1;
}

static void click_widget_point(GtkWidget *target, double rel_x, double rel_y) {
    GtkWidget *top = gtk_widget_get_toplevel(target);
    GdkWindow *top_w = gtk_widget_get_window(top);
    if (!top_w)
        return;
    gint tx = 0, ty = 0;
    gtk_widget_translate_coordinates(target, top, (gint)rel_x, (gint)rel_y, &tx, &ty);

    /* Find deepest GdkWindow containing (tx, ty) relative to top_w */
    GdkWindow *dest = top_w;
    double lx = tx, ly = ty;
    gboolean descended = TRUE;
    while (descended) {
        descended = FALSE;
        GList *ch = gdk_window_get_children(dest);
        for (GList *l = ch; l; l = l->next) {
            GdkWindow *cw = GDK_WINDOW(l->data);
            if (!gdk_window_is_visible(cw))
                continue;
            int cx, cy, cw_w, cw_h;
            gdk_window_get_geometry(cw, &cx, &cy, &cw_w, &cw_h);
            if (lx >= cx && lx < cx + cw_w && ly >= cy && ly < cy + cw_h) {
                dest = cw;
                lx -= cx;
                ly -= cy;
                descended = TRUE;
                break;
            }
        }
        g_list_free(ch);
    }

    GdkDisplay *disp = gdk_window_get_display(top_w);
    GdkDevice *ptr = gdk_seat_get_pointer(gdk_display_get_default_seat(disp));
    for (int phase = 0; phase < 2; phase++) {
        GdkEvent *ev = gdk_event_new(phase == 0 ? GDK_BUTTON_PRESS : GDK_BUTTON_RELEASE);
        ev->button.window = g_object_ref(dest);
        ev->button.send_event = TRUE;
        ev->button.time = GDK_CURRENT_TIME;
        ev->button.x = lx;
        ev->button.y = ly;
        ev->button.button = 1;
        ev->button.state = phase == 0 ? 0 : GDK_BUTTON1_MASK;
        gdk_event_set_device(ev, ptr);
        gtk_main_do_event(ev);
        gdk_event_free(ev);
        pump_events(60);
    }
}

static gboolean tab_to(GtkWidget *window, GtkWidget *target) {
    for (int step = 0; step < 24; step++) {
        gtk_widget_child_focus(window, GTK_DIR_TAB_FORWARD);
        if (gtk_window_get_focus(GTK_WINDOW(window)) == target)
            return TRUE;
    }
    return FALSE;
}

static int run_gallery(const char *active_png, const char *focus_png,
                       const char *backdrop_png, const char *dialog_png,
                       const char *tooltip_png, const char *metrics_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(win), "Platinum Batch 2 Gallery");
    gtk_window_set_resizable(GTK_WINDOW(win), FALSE);
    gtk_window_set_default_size(GTK_WINDOW(win), 460, 400);

    GtkWidget *body = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
    gtk_container_set_border_width(GTK_CONTAINER(body), 10);
    gtk_container_add(GTK_CONTAINER(win), body);

    /* Notebook with two real labeled tabs */
    GtkWidget *nb = gtk_notebook_new();
    GtkWidget *tab_body1 = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
    gtk_container_set_border_width(GTK_CONTAINER(tab_body1), 10);
    GtkWidget *tab_body2 = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
    gtk_container_set_border_width(GTK_CONTAINER(tab_body2), 10);
    gtk_box_pack_start(GTK_BOX(tab_body2), gtk_label_new("Options page"), FALSE, FALSE, 0);

    GtkWidget *sc = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 100, 10);
    gtk_scale_set_draw_value(GTK_SCALE(sc), FALSE);
    gtk_widget_set_tooltip_text(sc, "Balloon Help explains controls without opening Mac Help.");
    gtk_range_set_value(GTK_RANGE(sc), 50);
    gtk_scale_add_mark(GTK_SCALE(sc), 0, GTK_POS_BOTTOM, NULL);
    gtk_scale_add_mark(GTK_SCALE(sc), 50, GTK_POS_BOTTOM, NULL);
    gtk_scale_add_mark(GTK_SCALE(sc), 100, GTK_POS_BOTTOM, NULL);
    gtk_box_pack_start(GTK_BOX(tab_body1), sc, FALSE, FALSE, 0);

    GtkWidget *pb = gtk_progress_bar_new();
    gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb), 0.65);
    gtk_box_pack_start(GTK_BOX(tab_body1), pb, FALSE, FALSE, 0);

    GtkWidget *pb_pulse = gtk_progress_bar_new();
    gtk_progress_bar_pulse(GTK_PROGRESS_BAR(pb_pulse));
    gtk_box_pack_start(GTK_BOX(tab_body1), pb_pulse, FALSE, FALSE, 0);

    gtk_notebook_append_page(GTK_NOTEBOOK(nb), tab_body1, gtk_label_new("Controls"));
    gtk_notebook_append_page(GTK_NOTEBOOK(nb), tab_body2, gtk_label_new("Options"));
    gtk_box_pack_start(GTK_BOX(body), nb, FALSE, FALSE, 0);

    /* Classic ScrolledWindow with overflowing content + non-overlay classic scrollbars */
    GtkWidget *sw = gtk_scrolled_window_new(NULL, NULL);
    gtk_scrolled_window_set_overlay_scrolling(GTK_SCROLLED_WINDOW(sw), FALSE);
    gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sw), GTK_POLICY_ALWAYS, GTK_POLICY_ALWAYS);
    gtk_scrolled_window_set_shadow_type(GTK_SCROLLED_WINDOW(sw), GTK_SHADOW_IN);
    gtk_widget_set_size_request(sw, 400, 150);

    GtkWidget *tall_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 4);
    gtk_widget_set_size_request(tall_box, 600, 500);
    for (int i = 0; i < 16; i++) {
        char buf[64];
        g_snprintf(buf, sizeof buf, "Scrollable Platinum item row %d", i + 1);
        GtkWidget *lbl = gtk_label_new(buf);
        gtk_widget_set_halign(lbl, GTK_ALIGN_START);
        gtk_box_pack_start(GTK_BOX(tall_box), lbl, FALSE, FALSE, 0);
    }
    gtk_container_add(GTK_CONTAINER(sw), tall_box);
    gtk_box_pack_start(GTK_BOX(body), sw, TRUE, TRUE, 0);

    gtk_widget_show_all(win);
    pump_events(250);

    gboolean is_broadway = strcmp(G_OBJECT_TYPE_NAME(gdk_display_get_default()), "GdkBroadwayDisplay") == 0;
    if (is_broadway && !gtk_window_has_toplevel_focus(GTK_WINDOW(win))) {
        GdkEvent *ev = gdk_event_new(GDK_FOCUS_CHANGE);
        ev->focus_change.window = g_object_ref(gtk_widget_get_window(win));
        ev->focus_change.send_event = TRUE;
        ev->focus_change.in = TRUE;
        gtk_main_do_event(ev);
        gdk_event_free(ev);
        pump_events(100);
    }

    gboolean real_active = gtk_window_is_active(GTK_WINDOW(win));
    int ok_active = save_widget_png(win, active_png);

    /* Real stepper click test on classic vertical scrollbar (both steppers stacked at bottom!) */
    GtkWidget *vsb = gtk_scrolled_window_get_vscrollbar(GTK_SCROLLED_WINDOW(sw));
    GtkAdjustment *vadj = gtk_scrolled_window_get_vadjustment(GTK_SCROLLED_WINDOW(sw));
    GtkAllocation vsb_a;
    gtk_widget_get_allocation(vsb, &vsb_a);
    double v0 = gtk_adjustment_get_value(vadj);
    /* Bottom-most 16px is button.down; 15px above it is button.up */
    click_widget_point(vsb, vsb_a.width / 2.0, vsb_a.height - 8.0);
    double v_after_down = gtk_adjustment_get_value(vadj);
    click_widget_point(vsb, vsb_a.width / 2.0, vsb_a.height - 23.0);
    double v_after_up = gtk_adjustment_get_value(vadj);
    gboolean stepper_ok = (v0 == 0.0) && (v_after_down > v0) && (v_after_up < v_after_down);

    GtkWidget *hsb = gtk_scrolled_window_get_hscrollbar(GTK_SCROLLED_WINDOW(sw));
    GtkAdjustment *hadj = gtk_scrolled_window_get_hadjustment(GTK_SCROLLED_WINDOW(sw));
    GtkAllocation hsb_a;
    gtk_widget_get_allocation(hsb, &hsb_a);
    double h0 = gtk_adjustment_get_value(hadj);
    click_widget_point(hsb, hsb_a.width - 8.0, hsb_a.height / 2.0);
    double h_after_right = gtk_adjustment_get_value(hadj);
    click_widget_point(hsb, hsb_a.width - 23.0, hsb_a.height / 2.0);
    double h_after_left = gtk_adjustment_get_value(hadj);
    stepper_ok = stepper_ok && h0 == 0 && h_after_right > h0 && h_after_left < h_after_right;

    /* Keyboard focus traversal onto GtkScale */
    gtk_window_set_focus_visible(GTK_WINDOW(win), TRUE);
    gboolean focus_reached = tab_to(win, sc);
    pump_events(120);
    for (int pulse = 0; pulse < 5; pulse++) {
        gtk_progress_bar_pulse(GTK_PROGRESS_BAR(pb_pulse));
        pump_events(75);
    }
    int ok_focus = save_widget_png(win, focus_png);
    gtk_window_set_focus_visible(GTK_WINDOW(win), FALSE);

    /* A motion event also supplies GTK's tooltip subsystem with a source window. */
    GdkWindow *surface = gtk_widget_get_window(win);
    GdkDevice *pointer = gdk_seat_get_pointer(gdk_display_get_default_seat(gdk_display_get_default()));
    gint tip_x, tip_y;
    gtk_widget_translate_coordinates(sc, win, 10, 5, &tip_x, &tip_y);
    GdkEvent *motion = gdk_event_new(GDK_MOTION_NOTIFY);
    motion->motion.window = g_object_ref(surface);
    motion->motion.x = tip_x;
    motion->motion.y = tip_y;
    gdk_event_set_device(motion, pointer);
    gdk_event_set_source_device(motion, pointer);
    gtk_main_do_event(motion);
    gdk_event_free(motion);

    /* Ask GTK to open its native keyboard tooltip on the focused scale. */
    gboolean tip_handled = FALSE;
    g_signal_emit_by_name(sc, "show-help", GTK_WIDGET_HELP_TOOLTIP, &tip_handled);
    pump_events(650);
    int ok_tip = 0;
    GList *toplevels = gtk_window_list_toplevels();
    for (GList *item = toplevels; item; item = item->next) {
        GtkWidget *tip = item->data;
        if (gtk_widget_get_mapped(tip) &&
            gtk_window_get_type_hint(GTK_WINDOW(tip)) == GDK_WINDOW_TYPE_HINT_TOOLTIP) {
            ok_tip = save_widget_png(tip, tooltip_png);
            break;
        }
    }
    g_list_free(toplevels);
    if (!ok_tip)
        fprintf(stderr, "Native tooltip did not map (show-help=%d)\n", tip_handled);
    if (tip_handled)
        g_signal_emit_by_name(sc, "show-help", GTK_WIDGET_HELP_TOOLTIP, &tip_handled);

    /* Native GtkMessageDialog with default button & action area */
    GtkWidget *dlg = gtk_message_dialog_new(
        GTK_WINDOW(win),
        GTK_DIALOG_MODAL,
        GTK_MESSAGE_QUESTION,
        GTK_BUTTONS_NONE,
        "Save changes to the Platinum Appearance document before closing?");
    gtk_message_dialog_format_secondary_text(
        GTK_MESSAGE_DIALOG(dlg),
        "If you don't save, your changes will be lost.");
    GtkWidget *btn_cancel = gtk_dialog_add_button(GTK_DIALOG(dlg), "Cancel", GTK_RESPONSE_CANCEL);
    GtkWidget *btn_save = gtk_dialog_add_button(GTK_DIALOG(dlg), "Save", GTK_RESPONSE_ACCEPT);
    gtk_widget_set_can_default(btn_save, TRUE);
    gtk_dialog_set_default_response(GTK_DIALOG(dlg), GTK_RESPONSE_ACCEPT);
    gtk_widget_show_all(dlg);
    pump_events(200);
    gint cancel_x = 0, cancel_y = 0, save_x = 0, save_y = 0;
    GtkAllocation ca, sa;
    gtk_widget_get_allocation(btn_cancel, &ca);
    gtk_widget_get_allocation(btn_save, &sa);
    gtk_widget_translate_coordinates(btn_cancel, dlg, 0, 0, &cancel_x, &cancel_y);
    gtk_widget_translate_coordinates(btn_save, dlg, 0, 0, &save_x, &save_y);
    GtkBorder save_margin;
    gtk_style_context_get_margin(gtk_widget_get_style_context(btn_save),
                                 gtk_widget_get_state_flags(btn_save), &save_margin);
    int btn_gap = (save_x + save_margin.left) - (cancel_x + ca.width);
    gboolean dlg_default = gtk_style_context_has_class(gtk_widget_get_style_context(btn_save), "default");
    int ok_dlg = save_widget_png(dlg, dialog_png);
    gtk_widget_destroy(dlg);
    pump_events(120);

    /* Backdrop transition */
    GtkWidget *other = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(other), "Other");
    gtk_window_set_default_size(GTK_WINDOW(other), 120, 80);
    gtk_widget_show_all(other);
    gtk_window_present(GTK_WINDOW(other));
    pump_events(250);
    gboolean real_backdrop = (gtk_widget_get_state_flags(win) & GTK_STATE_FLAG_BACKDROP) != 0;
    if (!real_backdrop && is_broadway) {
        GdkEvent *ev = gdk_event_new(GDK_FOCUS_CHANGE);
        ev->focus_change.window = g_object_ref(gtk_widget_get_window(win));
        ev->focus_change.send_event = TRUE;
        ev->focus_change.in = FALSE;
        gtk_main_do_event(ev);
        gdk_event_free(ev);
        pump_events(80);
        set_backdrop_recursive(win, TRUE);
        pump_events(100);
    }
    int ok_backdrop = save_widget_png(win, backdrop_png);
    gtk_widget_destroy(other);

    Item items[] = {
        { "notebook", nb },
        { "scale", sc },
        { "progress", pb },
        { "progress-pulse", pb_pulse },
        { "scrolledwindow", sw },
        { "vscrollbar", vsb },
        { "hscrollbar", hsb },
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
    fprintf(fp, "# theme=%s backend=%s scale=%d css_errors=%d real_active=%d real_backdrop=%d stepper_ok=%d v0=%.1f v_down=%.1f v_up=%.1f h0=%.1f h_right=%.1f h_left=%.1f focus_reached=%d dlg_default=%d dlg_btn_gap=%d ok_active=%d ok_focus=%d ok_backdrop=%d ok_dlg=%d ok_tip=%d\n",
            theme ? theme : "",
            disp ? G_OBJECT_TYPE_NAME(disp) : "none",
            gtk_widget_get_scale_factor(win),
            g_css_errors,
            real_active ? 1 : 0,
            real_backdrop ? 1 : 0,
            stepper_ok ? 1 : 0,
            v0, v_after_down, v_after_up, h0, h_after_right, h_after_left,
            focus_reached ? 1 : 0,
            dlg_default ? 1 : 0,
            btn_gap,
            ok_active, ok_focus, ok_backdrop, ok_dlg, ok_tip);
    g_free(theme);
    for (size_t i = 0; i < G_N_ELEMENTS(items); i++)
        record_item(fp, win, &items[i]);
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok_active && ok_focus && ok_backdrop && ok_dlg && ok_tip && g_css_errors == 0) ? 0 : 1;
}

static int run_overlay(const char *overlay_png, const char *metrics_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(win), "Overlay Scrollbar Probe");
    gtk_window_set_default_size(GTK_WINDOW(win), 320, 200);

    GtkWidget *sw = gtk_scrolled_window_new(NULL, NULL);
    gtk_scrolled_window_set_overlay_scrolling(GTK_SCROLLED_WINDOW(sw), TRUE);
    gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(sw), GTK_POLICY_AUTOMATIC, GTK_POLICY_AUTOMATIC);
    gtk_scrolled_window_set_shadow_type(GTK_SCROLLED_WINDOW(sw), GTK_SHADOW_IN);

    GtkWidget *tv = gtk_text_view_new();
    GString *s = g_string_new("");
    for (int i = 0; i < 40; i++)
        g_string_append_printf(s, "Overlay scrolling content line %d — Mac OS 9 Platinum GTK 3\n", i + 1);
    gtk_text_buffer_set_text(gtk_text_view_get_buffer(GTK_TEXT_VIEW(tv)), s->str, -1);
    g_string_free(s, TRUE);
    gtk_container_add(GTK_CONTAINER(sw), tv);
    gtk_container_add(GTK_CONTAINER(win), sw);

    gtk_widget_show_all(win);
    pump_events(200);

    GtkAdjustment *vadj = gtk_scrolled_window_get_vadjustment(GTK_SCROLLED_WINDOW(sw));
    double scroll_before = gtk_adjustment_get_value(vadj);
    GdkEvent *scroll = gdk_event_new(GDK_SCROLL);
    scroll->scroll.window = g_object_ref(gtk_widget_get_window(sw));
    scroll->scroll.direction = GDK_SCROLL_DOWN;
    GdkDevice *device = gdk_seat_get_pointer(gdk_display_get_default_seat(gdk_display_get_default()));
    gdk_event_set_device(scroll, device);
    gdk_event_set_source_device(scroll, device);
    gtk_widget_event(sw, scroll);
    gdk_event_free(scroll);
    pump_events(150);

    GtkWidget *vsb = gtk_scrolled_window_get_vscrollbar(GTK_SCROLLED_WINDOW(sw));
    gboolean has_overlay_class = gtk_style_context_has_class(gtk_widget_get_style_context(vsb), "overlay-indicator");
    GtkAllocation va;
    gtk_widget_get_allocation(vsb, &va);
    int ok = save_widget_png(win, overlay_png);

    FILE *fp = fopen(metrics_txt, "w");
    if (!fp)
        return 1;
    GtkSettings *st = gtk_settings_get_default();
    gchar *theme = NULL;
    g_object_get(st, "gtk-theme-name", &theme, NULL);
    GdkDisplay *disp = gdk_display_get_default();
    fprintf(fp, "# theme=%s backend=%s scale=%d css_errors=%d overlay_enabled=%d has_overlay_class=%d vsb_w=%d vsb_h=%d scroll_before=%.3f scroll_val=%.3f png_ok=%d\n",
            theme ? theme : "",
            disp ? G_OBJECT_TYPE_NAME(disp) : "none",
            gtk_widget_get_scale_factor(win),
            g_css_errors,
            gtk_scrolled_window_get_overlay_scrolling(GTK_SCROLLED_WINDOW(sw)) ? 1 : 0,
            has_overlay_class ? 1 : 0,
            va.width, va.height,
            scroll_before, gtk_adjustment_get_value(vadj),
            ok);
    g_free(theme);
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok && g_css_errors == 0) ? 0 : 1;
}

static int run_csd(const char *active_png, const char *backdrop_png,
                   const char *narrow_png, const char *max_png, const char *metrics_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_default_size(GTK_WINDOW(win), 480, 220);

    GtkWidget *hb = gtk_header_bar_new();
    gtk_header_bar_set_title(GTK_HEADER_BAR(hb), "Platinum CSD Document");
    gtk_header_bar_set_subtitle(GTK_HEADER_BAR(hb), "Client-side HeaderBar");
    gtk_header_bar_set_show_close_button(GTK_HEADER_BAR(hb), TRUE);
    gtk_header_bar_set_decoration_layout(GTK_HEADER_BAR(hb), "close:minimize,maximize");

    GtkWidget *app_btn = gtk_button_new_with_label("Filter");
    gtk_header_bar_pack_start(GTK_HEADER_BAR(hb), app_btn);
    gtk_window_set_titlebar(GTK_WINDOW(win), hb);

    GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
    gtk_container_set_border_width(GTK_CONTAINER(content), 12);
    gtk_box_pack_start(GTK_BOX(content), gtk_label_new("Client-side decorated window body"), TRUE, TRUE, 0);
    gtk_container_add(GTK_CONTAINER(win), content);

    gtk_widget_show_all(win);
    pump_events(250);

    gboolean is_broadway = strcmp(G_OBJECT_TYPE_NAME(gdk_display_get_default()), "GdkBroadwayDisplay") == 0;
    if (is_broadway && !gtk_window_has_toplevel_focus(GTK_WINDOW(win))) {
        GdkEvent *ev = gdk_event_new(GDK_FOCUS_CHANGE);
        ev->focus_change.window = g_object_ref(gtk_widget_get_window(win));
        ev->focus_change.send_event = TRUE;
        ev->focus_change.in = TRUE;
        gtk_main_do_event(ev);
        gdk_event_free(ev);
        pump_events(100);
    }

    gboolean real_active = gtk_window_is_active(GTK_WINDOW(win));
    int ok_active = save_widget_png(win, active_png);

    GtkAllocation hba_act, btn_a;
    gtk_widget_get_allocation(hb, &hba_act);
    gtk_widget_get_allocation(app_btn, &btn_a);
    gint hbx = 0, hby = 0;
    gtk_widget_translate_coordinates(hb, win, 0, 0, &hbx, &hby);

    /* Backdrop CSD check */
    GtkWidget *other = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(other), "Other");
    gtk_window_set_default_size(GTK_WINDOW(other), 120, 80);
    gtk_widget_show_all(other);
    gtk_window_present(GTK_WINDOW(other));
    pump_events(250);
    gboolean real_backdrop = (gtk_widget_get_state_flags(win) & GTK_STATE_FLAG_BACKDROP) != 0;
    if (!real_backdrop && is_broadway) {
        set_backdrop_recursive(win, TRUE);
        pump_events(100);
    }
    int ok_backdrop = save_widget_png(win, backdrop_png);
    gtk_widget_destroy(other);
    if (is_broadway)
        set_backdrop_recursive(win, FALSE);
    gtk_window_present(GTK_WINDOW(win));
    pump_events(180);

    /* Narrow width CSD check (240px) */
    gtk_window_resize(GTK_WINDOW(win), 240, 180);
    pump_events(200);
    GtkAllocation win_narrow_a, btn_narrow_a;
    gtk_widget_get_allocation(win, &win_narrow_a);
    gtk_widget_get_allocation(app_btn, &btn_narrow_a);
    gint btn_x = -1, btn_y = -1;
    gboolean narrow_button_fits = gtk_widget_get_mapped(app_btn)
        && gtk_widget_translate_coordinates(app_btn, win, 0, 0, &btn_x, &btn_y)
        && btn_x >= 0 && btn_y >= 0
        && btn_x + btn_narrow_a.width <= win_narrow_a.width
        && btn_narrow_a.height >= 20;
    int ok_narrow = save_widget_png(win, narrow_png);

    /* Maximized CSD check */
    gtk_window_maximize(GTK_WINDOW(win));
    pump_events(250);
    gboolean is_max = gtk_window_is_maximized(GTK_WINDOW(win));
    GtkAllocation win_max_a;
    gtk_widget_get_allocation(win, &win_max_a);
    int ok_max = save_widget_png(win, max_png);

    FILE *fp = fopen(metrics_txt, "w");
    if (!fp)
        return 1;
    GtkSettings *st = gtk_settings_get_default();
    gchar *theme = NULL;
    g_object_get(st, "gtk-theme-name", &theme, NULL);
    GdkDisplay *disp = gdk_display_get_default();
    fprintf(fp, "# theme=%s backend=%s scale=%d css_errors=%d real_active=%d real_backdrop=%d is_max=%d hb_rect=%d,%d,%d,%d app_btn=%dx%d narrow_w=%d narrow_btn_w=%d narrow_btn_fits=%d max_w=%d ok_active=%d ok_backdrop=%d ok_narrow=%d ok_max=%d\n",
            theme ? theme : "",
            disp ? G_OBJECT_TYPE_NAME(disp) : "none",
            gtk_widget_get_scale_factor(win),
            g_css_errors,
            real_active ? 1 : 0,
            real_backdrop ? 1 : 0,
            is_max ? 1 : 0,
            hbx, hby, hba_act.width, hba_act.height,
            btn_a.width, btn_a.height,
            win_narrow_a.width, btn_narrow_a.width,
            narrow_button_fits, win_max_a.width,
            ok_active, ok_backdrop, ok_narrow, ok_max);
    g_free(theme);
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok_active && ok_backdrop && ok_narrow && ok_max && g_css_errors == 0) ? 0 : 1;
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
    if (argc == 8 && strcmp(argv[1], "gallery") == 0)
        return run_gallery(argv[2], argv[3], argv[4], argv[5], argv[6], argv[7]);
    if (argc == 4 && strcmp(argv[1], "overlay") == 0)
        return run_overlay(argv[2], argv[3]);
    if (argc == 7 && strcmp(argv[1], "csd") == 0)
        return run_csd(argv[2], argv[3], argv[4], argv[5], argv[6]);

    fprintf(stderr, "usage: %s chrome|gallery|overlay|csd ...\n", argv[0]);
    return 2;
}
