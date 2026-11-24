/*
 * Milestone 3 Batch 1 GTK 3 Platinum capture tool:
 *   - Menus, menu bar, pop-ups/comboboxes, treeview headers & selection,
 *     disclosure triangles, etched group boxes, and separators.
 *
 * Modes:
 *   m3b1shot chrome <out.png> <coords.txt>
 *   m3b1shot gallery <active.png> <backdrop.png> <menu.png> <metrics.txt>
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

static gboolean on_chrome_draw(GtkWidget *w, cairo_t *cr, gpointer data) {
    (void)w;
    (void)data;
    /* Pop-ups and separator sit on #EEEEEE (Appearance control panel), matching styleshot.cpp */
    cairo_set_source_rgb(cr, 0xEE / 255.0, 0xEE / 255.0, 0xEE / 255.0);
    cairo_rectangle(cr, 5, 36, 650, 44);
    cairo_rectangle(cr, 355, 118, 120, 14);
    cairo_fill(cr);
    return FALSE;
}

static GtkWidget *make_combo_fixed(int w, int h, gboolean pressed, gboolean sensitive) {
    GtkWidget *cb = gtk_combo_box_new();
    gtk_widget_set_size_request(cb, w, h);
    gtk_widget_set_can_focus(cb, FALSE);
    gtk_widget_set_sensitive(cb, sensitive);
    if (pressed)
        gtk_widget_set_state_flags(cb, GTK_STATE_FLAG_ACTIVE, FALSE);
    return cb;
}

static void mark_descendant_button_active(GtkWidget *w, gpointer data) {
    (void)data;
    if (GTK_IS_TOGGLE_BUTTON(w)) {
        gtk_widget_set_state_flags(w, GTK_STATE_FLAG_ACTIVE | GTK_STATE_FLAG_CHECKED, FALSE);
        return;
    }
    if (GTK_IS_BUTTON(w)) {
        gtk_widget_set_state_flags(w, GTK_STATE_FLAG_ACTIVE, FALSE);
        return;
    }
    if (GTK_IS_CONTAINER(w)) {
        gtk_container_forall(GTK_CONTAINER(w), mark_descendant_button_active, NULL);
    }
}

static int run_chrome(const char *out_png, const char *coords_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_decorated(GTK_WINDOW(win), FALSE);
    gtk_window_set_resizable(GTK_WINDOW(win), FALSE);
    gtk_window_set_default_size(GTK_WINDOW(win), 660, 280);

    GtkWidget *fixed = gtk_fixed_new();
    gtk_widget_set_size_request(fixed, 660, 280);
    g_signal_connect(fixed, "draw", G_CALLBACK(on_chrome_draw), NULL);
    gtk_container_add(GTK_CONTAINER(win), fixed);

    Item items[32];
    int n = 0;
    #define PUT(nm, wid, x, y) do { \
        GtkWidget *_w = (wid); \
        gtk_fixed_put(GTK_FIXED(fixed), _w, (x), (y)); \
        items[n++] = (Item){ (nm), _w }; \
    } while (0)

    /* Row 1: Menu bar (20px tall; empty + hovered 35px title) */
    GtkWidget *mb = gtk_menu_bar_new();
    gtk_widget_set_size_request(mb, 200, 20);
    GtkWidget *mi_title = gtk_menu_item_new_with_label(" ");
    gtk_widget_set_size_request(mi_title, 35, 19);
    gtk_menu_shell_append(GTK_MENU_SHELL(mb), mi_title);
    PUT("menubar", mb, 10, 10);
    items[n++] = (Item){ "menubar-title", mi_title };

    /* Row 2: Pop-up / ComboBoxes on #EEEEEE (180x20 normal, 180x20 pressed, 194x20 disabled) */
    GtkWidget *cb_norm = make_combo_fixed(180, 20, FALSE, TRUE);
    GtkWidget *cb_prs  = make_combo_fixed(180, 20, TRUE,  TRUE);
    GtkWidget *cb_dis  = make_combo_fixed(194, 20, FALSE, FALSE);
    PUT("popup-normal",   cb_norm, 10, 48);
    PUT("popup-pressed",  cb_prs,  200, 48);
    PUT("popup-disabled", cb_dis,  390, 48);

    /* Row 3: TreeView headers (sorted 238x21 + normal 149x21) */
    GtkListStore *store = gtk_list_store_new(2, G_TYPE_STRING, G_TYPE_STRING);
    GtkWidget *tv = gtk_tree_view_new_with_model(GTK_TREE_MODEL(store));
    g_object_unref(store);
    gtk_widget_set_size_request(tv, 387, 25);
    gtk_widget_set_can_focus(tv, FALSE);

    GtkTreeViewColumn *c_sorted = gtk_tree_view_column_new();
    GtkWidget *empty1 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
    gtk_widget_show(empty1);
    gtk_tree_view_column_set_widget(c_sorted, empty1);
    gtk_tree_view_column_set_sizing(c_sorted, GTK_TREE_VIEW_COLUMN_FIXED);
    gtk_tree_view_column_set_fixed_width(c_sorted, 238);
    gtk_tree_view_append_column(GTK_TREE_VIEW(tv), c_sorted);

    GtkTreeViewColumn *c_norm = gtk_tree_view_column_new();
    GtkWidget *empty2 = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
    gtk_widget_show(empty2);
    gtk_tree_view_column_set_widget(c_norm, empty2);
    gtk_tree_view_column_set_sizing(c_norm, GTK_TREE_VIEW_COLUMN_FIXED);
    gtk_tree_view_column_set_fixed_width(c_norm, 149);
    gtk_tree_view_append_column(GTK_TREE_VIEW(tv), c_norm);

    GtkWidget *hb_sorted = gtk_tree_view_column_get_button(c_sorted);
    GtkWidget *hb_norm   = gtk_tree_view_column_get_button(c_norm);
    gtk_style_context_add_class(gtk_widget_get_style_context(hb_sorted), "sorted");
    gtk_widget_set_size_request(hb_sorted, 238, 21);
    gtk_widget_set_size_request(hb_norm, 149, 21);
    PUT("treeview-hdr", tv, 10, 88);
    items[n++] = (Item){ "header-sorted", hb_sorted };
    items[n++] = (Item){ "header-normal", hb_norm };

    /* Row 4: Separator (100x2 on #EEEEEE at 360,124; compared as 100x4 at 360,123) */
    GtkWidget *sep = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
    gtk_widget_set_size_request(sep, 100, 2);
    PUT("separator", sep, 360, 124);

    /* Row 5: Etched Group Box (326x109 on #DDDDDD at 10,140) */
    GtkWidget *frm = gtk_frame_new(NULL);
    gtk_widget_set_size_request(frm, 326, 109);
    PUT("groupbox", frm, 10, 140);

    #undef PUT

    gtk_widget_show_all(win);
    pump_events(200);
    gtk_widget_set_state_flags(mi_title, GTK_STATE_FLAG_PRELIGHT, FALSE);
    mark_descendant_button_active(cb_prs, NULL);
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

static int run_gallery(const char *active_png, const char *backdrop_png,
                       const char *menu_png, const char *metrics_txt) {
    GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(win), "Platinum Batch 1 Gallery");
    gtk_window_set_resizable(GTK_WINDOW(win), FALSE);
    gtk_window_set_default_size(GTK_WINDOW(win), 420, 420);

    GtkWidget *root_box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
    gtk_container_add(GTK_CONTAINER(win), root_box);

    /* Menu bar */
    GtkWidget *mb = gtk_menu_bar_new();
    GtkWidget *mi_file = gtk_menu_item_new_with_label("File");
    GtkWidget *mi_edit = gtk_menu_item_new_with_label("Edit");
    GtkWidget *mi_view = gtk_menu_item_new_with_label("View");
    gtk_menu_shell_append(GTK_MENU_SHELL(mb), mi_file);
    gtk_menu_shell_append(GTK_MENU_SHELL(mb), mi_edit);
    gtk_menu_shell_append(GTK_MENU_SHELL(mb), mi_view);
    gtk_box_pack_start(GTK_BOX(root_box), mb, FALSE, FALSE, 0);

    /* Build real GtkMenu attached to File item */
    GtkWidget *m_file = gtk_menu_new();
    GtkWidget *m_icons = gtk_check_menu_item_new_with_label("as Icons");
    gtk_check_menu_item_set_active(GTK_CHECK_MENU_ITEM(m_icons), TRUE);
    GtkWidget *m_list  = gtk_check_menu_item_new_with_label("as List");
    GtkWidget *m_sep   = gtk_separator_menu_item_new();
    GtkWidget *m_sub   = gtk_menu_item_new_with_label("Sort By");
    GtkWidget *m_subm  = gtk_menu_new();
    gtk_menu_shell_append(GTK_MENU_SHELL(m_subm), gtk_menu_item_new_with_label("Name"));
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(m_sub), m_subm);
    GtkWidget *m_dis   = gtk_menu_item_new_with_label("Close Window");
    gtk_widget_set_sensitive(m_dis, FALSE);
    gtk_menu_shell_append(GTK_MENU_SHELL(m_file), m_icons);
    gtk_menu_shell_append(GTK_MENU_SHELL(m_file), m_list);
    gtk_menu_shell_append(GTK_MENU_SHELL(m_file), m_sep);
    gtk_menu_shell_append(GTK_MENU_SHELL(m_file), m_sub);
    gtk_menu_shell_append(GTK_MENU_SHELL(m_file), m_dis);
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(mi_file), m_file);

    /* Body with groupbox, comboboxes, separator, and treeview */
    GtkWidget *body = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
    gtk_container_set_border_width(GTK_CONTAINER(body), 10);
    gtk_box_pack_start(GTK_BOX(root_box), body, TRUE, TRUE, 0);

    GtkWidget *frm = gtk_frame_new("Appearance");
    GtkWidget *fbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    gtk_container_set_border_width(GTK_CONTAINER(fbox), 8);
    gtk_container_add(GTK_CONTAINER(frm), fbox);

    GtkWidget *cb_row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
    GtkWidget *cb_norm = gtk_combo_box_text_new();
    gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(cb_norm), "Lavender");
    gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(cb_norm), "Blue");
    for (int n = 2; n < 80; n++) {
        char label[32];
        g_snprintf(label, sizeof label, "Appearance option %d", n);
        gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(cb_norm), label);
    }
    gtk_combo_box_set_active(GTK_COMBO_BOX(cb_norm), 0);
    GtkWidget *cb_dis = gtk_combo_box_text_new();
    gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(cb_dis), "Disabled");
    gtk_combo_box_text_append_text(GTK_COMBO_BOX_TEXT(cb_dis), "Alternate");
    gtk_combo_box_set_active(GTK_COMBO_BOX(cb_dis), 0);
    gtk_widget_set_sensitive(cb_dis, FALSE);
    gtk_box_pack_start(GTK_BOX(cb_row), cb_norm, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(cb_row), cb_dis,  TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(fbox), cb_row, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(body), frm, FALSE, FALSE, 0);

    GtkWidget *sep = gtk_separator_new(GTK_ORIENTATION_HORIZONTAL);
    gtk_box_pack_start(GTK_BOX(body), sep, FALSE, FALSE, 0);

    /* TreeView with sorted + normal columns, disclosure triangles, and selected row */
    GtkTreeStore *ts = gtk_tree_store_new(2, G_TYPE_STRING, G_TYPE_STRING);
    GtkTreeIter p1, c1, p2;
    gtk_tree_store_append(ts, &p1, NULL);
    gtk_tree_store_set(ts, &p1, 0, "System Folder", 1, "Today", -1);
    gtk_tree_store_append(ts, &c1, &p1);
    gtk_tree_store_set(ts, &c1, 0, "Appearance", 1, "Yesterday", -1);
    gtk_tree_store_append(ts, &p2, NULL);
    gtk_tree_store_set(ts, &p2, 0, "Documents", 1, "Nov 23", -1);

    GtkWidget *tv = gtk_tree_view_new_with_model(GTK_TREE_MODEL(ts));
    g_object_unref(ts);
    GtkTreeViewColumn *col1 = gtk_tree_view_column_new_with_attributes("Name", gtk_cell_renderer_text_new(), "text", 0, NULL);
    gtk_tree_view_column_set_expand(col1, TRUE);
    gtk_tree_view_append_column(GTK_TREE_VIEW(tv), col1);
    GtkTreeViewColumn *col2 = gtk_tree_view_column_new_with_attributes("Date Modified", gtk_cell_renderer_text_new(), "text", 1, NULL);
    gtk_tree_view_append_column(GTK_TREE_VIEW(tv), col2);
    gtk_tree_view_column_set_sort_column_id(col1, 0);
    gtk_tree_view_column_set_sort_column_id(col2, 1);
    gtk_tree_sortable_set_sort_column_id(GTK_TREE_SORTABLE(ts), 0, GTK_SORT_DESCENDING);

    GtkTreePath *p_open = gtk_tree_path_new_from_indices(0, -1);
    gtk_tree_view_expand_row(GTK_TREE_VIEW(tv), p_open, FALSE);
    gtk_tree_path_free(p_open);

    GtkWidget *sw = gtk_scrolled_window_new(NULL, NULL);
    gtk_scrolled_window_set_shadow_type(GTK_SCROLLED_WINDOW(sw), GTK_SHADOW_IN);
    gtk_widget_set_size_request(sw, 380, 140);
    gtk_container_add(GTK_CONTAINER(sw), tv);
    gtk_box_pack_start(GTK_BOX(body), sw, TRUE, TRUE, 0);

    GtkWidget *list = gtk_list_box_new();
    gtk_container_add(GTK_CONTAINER(list), gtk_label_new("Selected list row"));
    gtk_container_add(GTK_CONTAINER(list), gtk_label_new("Another list row"));
    gtk_list_box_select_row(GTK_LIST_BOX(list), gtk_list_box_get_row_at_index(GTK_LIST_BOX(list), 0));
    gtk_box_pack_start(GTK_BOX(body), list, FALSE, FALSE, 0);

    gtk_widget_show_all(win);
    pump_events(200);

    /* Ensure window active focus on WM-less Broadway only (never mask Wayland focus) */
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

    gtk_tree_view_column_clicked(col1);
    gint sort_id;
    GtkSortType sort_order;
    gboolean native_sort = gtk_tree_sortable_get_sort_column_id(GTK_TREE_SORTABLE(ts), &sort_id, &sort_order)
        && sort_id == 0 && sort_order == GTK_SORT_ASCENDING
        && gtk_tree_view_column_get_sort_indicator(col1)
        && !gtk_tree_view_column_get_sort_indicator(col2);
    GtkTreePath *expanded = gtk_tree_model_get_path(GTK_TREE_MODEL(ts), &p1);
    gtk_tree_view_expand_row(GTK_TREE_VIEW(tv), expanded, FALSE);
    gtk_tree_path_free(expanded);
    gtk_widget_grab_focus(tv);
    gtk_window_set_focus_visible(GTK_WINDOW(win), TRUE);
    GtkTreePath *cursor = gtk_tree_model_get_path(GTK_TREE_MODEL(ts), &c1);
    gtk_tree_view_set_cursor(GTK_TREE_VIEW(tv), cursor, NULL, FALSE);
    gtk_tree_path_free(cursor);
    gtk_widget_set_state_flags(mi_file, GTK_STATE_FLAG_PRELIGHT, FALSE);
    pump_events(150);

    gboolean real_active = gtk_window_is_active(GTK_WINDOW(win));
    int ok_active = save_widget_png(win, active_png);

    gboolean combo_open = FALSE, combo_closed = FALSE;
    GdkSeat *seat = gdk_display_get_default_seat(gdk_display_get_default());
    gtk_combo_box_popup_for_device(GTK_COMBO_BOX(cb_norm), gdk_seat_get_pointer(seat));
    pump_events(150);
    g_object_get(cb_norm, "popup-shown", &combo_open, NULL);
    gboolean combo_overflow = FALSE;
    GList *menus = gtk_menu_get_for_attach_widget(cb_norm);
    for (GList *link = menus; link; link = link->next) {
        GtkWidget *menu = GTK_WIDGET(link->data);
        if (!gtk_widget_get_mapped(menu))
            continue;
        GList *items = gtk_container_get_children(GTK_CONTAINER(menu));
        int total_height = 0;
        for (GList *item = items; item; item = item->next)
            total_height += gtk_widget_get_allocated_height(GTK_WIDGET(item->data));
        combo_overflow = total_height > gtk_widget_get_allocated_height(menu);
        g_list_free(items);
        break;
    }
    gtk_combo_box_popdown(GTK_COMBO_BOX(cb_norm));
    pump_events(120);
    gboolean popup_shown;
    g_object_get(cb_norm, "popup-shown", &popup_shown, NULL);
    combo_closed = !popup_shown;

    /* A short popup also exercises GTK's hidden overflow arrow allocations. */
    gtk_widget_set_sensitive(cb_dis, TRUE);
    gtk_combo_box_popup_for_device(GTK_COMBO_BOX(cb_dis), gdk_seat_get_pointer(seat));
    pump_events(150);
    gboolean short_open;
    g_object_get(cb_dis, "popup-shown", &short_open, NULL);
    gtk_combo_box_popdown(GTK_COMBO_BOX(cb_dis));
    pump_events(120);
    g_object_get(cb_dis, "popup-shown", &popup_shown, NULL);
    gboolean short_roundtrip = short_open && !popup_shown;
    gtk_widget_set_sensitive(cb_dis, FALSE);

    /* Pop up real GtkMenu on File item and capture it directly */
    gtk_widget_show_all(m_file);
    gtk_menu_popup_at_widget(GTK_MENU(m_file), mi_file, GDK_GRAVITY_SOUTH_WEST, GDK_GRAVITY_NORTH_WEST, NULL);
    pump_events(200);
    gtk_menu_shell_select_item(GTK_MENU_SHELL(m_file), m_icons);
    pump_events(120);
    int ok_menu = gtk_widget_get_mapped(m_file)
        && gtk_menu_shell_get_selected_item(GTK_MENU_SHELL(m_file)) == m_icons
        && save_widget_png(m_file, menu_png);
    gtk_menu_popdown(GTK_MENU(m_file));
    gtk_widget_unset_state_flags(mi_file, GTK_STATE_FLAG_PRELIGHT);
    pump_events(120);

    /* Backdrop window check */
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
        { "menubar", mb },
        { "mi-file", mi_file },
        { "frame", frm },
        { "combo-normal", cb_norm },
        { "combo-disabled", cb_dis },
        { "separator", sep },
        { "scrolledwindow", sw },
        { "treeview", tv },
        { "list", list },
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
    fprintf(fp, "# theme=%s backend=%s scale=%d css_errors=%d real_active=%d real_backdrop=%d native_sort=%d combo_open=%d combo_closed=%d combo_overflow=%d short_roundtrip=%d ok_active=%d ok_menu=%d ok_backdrop=%d\n",
            theme ? theme : "",
            disp ? G_OBJECT_TYPE_NAME(disp) : "none",
            gtk_widget_get_scale_factor(win),
            g_css_errors,
            real_active, real_backdrop, native_sort, combo_open, combo_closed, combo_overflow, short_roundtrip,
            ok_active, ok_menu, ok_backdrop);
    g_free(theme);
    for (size_t i = 0; i < G_N_ELEMENTS(items); i++)
        record_item(fp, win, &items[i]);
    fclose(fp);

    gtk_widget_destroy(win);
    return (ok_active && ok_menu && ok_backdrop && g_css_errors == 0) ? 0 : 1;
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
    if (argc == 6 && strcmp(argv[1], "gallery") == 0)
        return run_gallery(argv[2], argv[3], argv[4], argv[5]);

    fprintf(stderr, "usage: %s chrome <out.png> <coords.txt> | gallery <active.png> <backdrop.png> <menu.png> <metrics.txt>\n", argv[0]);
    return 2;
}
