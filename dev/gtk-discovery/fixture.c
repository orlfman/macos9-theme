/* Minimal GTK 3 / plain GTK 4 / stock libadwaita discovery fixture for Milestone 1.
 *
 * Modes:
 *   fixture <out.png>
 *       One-shot mode: settle 450 ms, log GtkSettings / AdwStyleManager / CSS
 *       markers, save PNG screenshot, exit 0 on success.
 *   fixture --watch <ready-file> <log-file> [final.png]
 *       Live watch mode: stay open while preference changes occur, log initial
 *       state + every GtkSettings/AdwStyleManager notify + SIGUSR1 polls, and
 *       exit cleanly on SIGTERM (optionally saving final.png).
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */
#include <cairo.h>
#include <glib-unix.h>
#include <gtk/gtk.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#ifdef USE_ADW
#include <adwaita.h>
#endif

static GtkWidget *window;
static GtkWidget *probe_lbl, *ind_theme_lbl, *ind_app_lbl, *ind_user_lbl;
static const char *out_png;
static const char *ready_path;
static const char *log_path;
static FILE *log_fp;
static gboolean watch_mode;
static gboolean captured;
static int css_parse_errors;
static int settle_retries;
static GMainLoop *loop;
#ifdef USE_ADW
static AdwApplication *adw_app;
#endif

static void quit_app(void)
{
#ifdef USE_ADW
    if (adw_app) {
        g_application_quit(G_APPLICATION(adw_app));
        return;
    }
#endif
    if (loop)
        g_main_loop_quit(loop);
}

static const char *stack_name(void)
{
#if GTK_MAJOR_VERSION == 3
    return "gtk3";
#elif defined(USE_ADW)
    return "adw";
#else
    return "gtk4";
#endif
}

static void read_fg_hex(GtkWidget *w, char buf[8])
{
    GdkRGBA c = {0, 0, 0, 1};
#if GTK_MAJOR_VERSION == 3
    gtk_style_context_get_color(gtk_widget_get_style_context(w),
                                gtk_widget_get_state_flags(w), &c);
#else
    gtk_widget_get_color(w, &c);
#endif
    snprintf(buf, 8, "#%02x%02x%02x",
             (int)(255.0 * c.red + 0.5),
             (int)(255.0 * c.green + 0.5),
             (int)(255.0 * c.blue + 0.5));
}

static gboolean save_window_png(const char *path)
{
    if (!path || !*path)
        return TRUE;
#if GTK_MAJOR_VERSION == 3
    int w = gtk_widget_get_allocated_width(window);
    int h = gtk_widget_get_allocated_height(window);
    if (w <= 0) w = 320;
    if (h <= 0) h = 240;
    cairo_surface_t *surf = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, w, h);
    cairo_t *cr = cairo_create(surf);
    gtk_widget_draw(window, cr);
    cairo_destroy(cr);
    cairo_surface_flush(surf);
    cairo_status_t st = cairo_surface_write_to_png(surf, path);
    cairo_surface_destroy(surf);
    return st == CAIRO_STATUS_SUCCESS;
#else
    int w = gtk_widget_get_width(window);
    int h = gtk_widget_get_height(window);
    if (w <= 0) w = 320;
    if (h <= 0) h = 240;
    GdkPaintable *paintable = gtk_widget_paintable_new(window);
    GtkSnapshot *snapshot = gtk_snapshot_new();
    gdk_paintable_snapshot(paintable, snapshot, (double)w, (double)h);
    GskRenderNode *node = gtk_snapshot_free_to_node(snapshot);
    gboolean ok = FALSE;
    if (node) {
        GskRenderer *renderer = gtk_native_get_renderer(GTK_NATIVE(window));
        if (renderer) {
            GdkTexture *tex = gsk_renderer_render_texture(renderer, node, NULL);
            if (tex) {
                ok = gdk_texture_save_to_png(tex, path);
                g_object_unref(tex);
            }
        }
        if (!ok) {
            cairo_surface_t *surf = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, w, h);
            cairo_t *cr = cairo_create(surf);
            gsk_render_node_draw(node, cr);
            cairo_destroy(cr);
            cairo_surface_flush(surf);
            ok = (cairo_surface_write_to_png(surf, path) == CAIRO_STATUS_SUCCESS);
            cairo_surface_destroy(surf);
        }
        gsk_render_node_unref(node);
    }
    g_object_unref(paintable);
    return ok;
#endif
}

static void log_state(const char *tag, int png_ok)
{
    FILE *fp = log_fp ? log_fp : stdout;
    GtkSettings *settings = gtk_settings_get_default();
    char *theme = NULL, *icon_theme = NULL, *deco = NULL;
    g_object_get(settings,
                 "gtk-theme-name", &theme,
                 "gtk-icon-theme-name", &icon_theme,
                 "gtk-decoration-layout", &deco,
                 NULL);

    char probe[8], itheme[8], iapp[8], iuser[8];
    read_fg_hex(probe_lbl, probe);
    read_fg_hex(ind_theme_lbl, itheme);
    read_fg_hex(ind_app_lbl, iapp);
    read_fg_hex(ind_user_lbl, iuser);

    fprintf(fp,
            "tag=%s stack=%s backend=%s theme=%s icon_theme=%s deco=%s "
            "probe=%s ind_theme=%s ind_app=%s ind_user=%s css_errors=%d",
            tag,
            stack_name(),
            G_OBJECT_TYPE_NAME(gdk_display_get_default()),
            theme ? theme : "",
            icon_theme ? icon_theme : "",
            deco ? deco : "",
            probe, itheme, iapp, iuser, css_parse_errors);

#if GTK_MAJOR_VERSION == 3
    gboolean prefer_dark = FALSE;
    g_object_get(settings, "gtk-application-prefer-dark-theme", &prefer_dark, NULL);
    fprintf(fp, " prefer_dark=%d", prefer_dark ? 1 : 0);
#else
    int color_scheme = 0, contrast = 0;
    g_object_get(settings,
                 "gtk-interface-color-scheme", &color_scheme,
                 "gtk-interface-contrast", &contrast,
                 NULL);
    fprintf(fp, " gtk4_color_scheme=%d gtk4_contrast=%d", color_scheme, contrast);
#endif

#ifdef USE_ADW
    AdwStyleManager *sm = adw_style_manager_get_default();
    AdwAccentColor acc = adw_style_manager_get_accent_color(sm);
    GEnumClass *ec = g_type_class_ref(ADW_TYPE_ACCENT_COLOR);
    GEnumValue *ev = g_enum_get_value(ec, acc);
    const char *acc_nick = ev ? ev->value_nick : "unknown";
    GdkRGBA *acc_rgba = adw_style_manager_get_accent_color_rgba(sm);
    char *rgba_str = acc_rgba ? gdk_rgba_to_string(acc_rgba) : g_strdup("none");
    fprintf(fp,
            " adw_sys_cs=%d adw_dark=%d adw_hc=%d adw_sys_acc=%d "
            "adw_accent_enum=%d adw_accent_nick=%s adw_accent_rgba=%s",
            adw_style_manager_get_system_supports_color_schemes(sm) ? 1 : 0,
            adw_style_manager_get_dark(sm) ? 1 : 0,
            adw_style_manager_get_high_contrast(sm) ? 1 : 0,
            adw_style_manager_get_system_supports_accent_colors(sm) ? 1 : 0,
            (int)acc,
            acc_nick,
            rgba_str);
    g_type_class_unref(ec);
    if (acc_rgba) gdk_rgba_free(acc_rgba);
    g_free(rgba_str);
#endif

    if (png_ok >= 0)
        fprintf(fp, " png_ok=%d", png_ok);
    fprintf(fp, "\n");
    fflush(fp);

    g_free(theme);
    g_free(icon_theme);
    g_free(deco);
}

static void on_css_error(GtkCssProvider *p, GtkCssSection *sec, GError *err, gpointer data)
{
    (void)p;
    (void)sec;
    (void)data;
    css_parse_errors++;
    fprintf(stderr, "fixture(%s): CSS parse error: %s\n", stack_name(), err ? err->message : "unknown");
}

static gboolean emit_notify_idle(gpointer data)
{
    char *tag = (char *)data;
    log_state(tag, -1);
    g_free(tag);
    return G_SOURCE_REMOVE;
}

static void on_prop_notify(GObject *obj, GParamSpec *pspec, gpointer prefix)
{
    (void)obj;
    char *tag = g_strdup_printf("notify:%s:%s", (const char *)prefix, g_param_spec_get_name(pspec));
    g_idle_add(emit_notify_idle, tag);
}

static gboolean on_sigusr1(gpointer unused)
{
    (void)unused;
    log_state("poll", -1);
    return G_SOURCE_CONTINUE;
}

static gboolean on_sigterm(gpointer unused)
{
    (void)unused;
    int ok = out_png ? (save_window_png(out_png) ? 1 : 0) : -1;
    log_state("final", ok);
    captured = (ok != 0);
    quit_app();
    return G_SOURCE_REMOVE;
}

static gboolean on_initial_settle(gpointer unused)
{
    (void)unused;
#if GTK_MAJOR_VERSION >= 4
    if ((gtk_widget_get_width(window) <= 0 || gtk_widget_get_height(window) <= 0) && settle_retries < 25) {
        settle_retries++;
        g_timeout_add(100, on_initial_settle, NULL);
        return G_SOURCE_REMOVE;
    }
#endif
    if (!watch_mode) {
        captured = save_window_png(out_png);
        if (!captured && settle_retries < 25) {
            settle_retries++;
            g_timeout_add(100, on_initial_settle, NULL);
            return G_SOURCE_REMOVE;
        }
        log_state("shot", captured ? 1 : 0);
        quit_app();
        return G_SOURCE_REMOVE;
    }

    log_state("init", -1);

    GtkSettings *settings = gtk_settings_get_default();
    g_signal_connect(settings, "notify::gtk-theme-name", G_CALLBACK(on_prop_notify), (gpointer)"settings");
#if GTK_MAJOR_VERSION == 3
    g_signal_connect(settings, "notify::gtk-application-prefer-dark-theme", G_CALLBACK(on_prop_notify), (gpointer)"settings");
#else
    g_signal_connect(settings, "notify::gtk-interface-color-scheme", G_CALLBACK(on_prop_notify), (gpointer)"settings");
    g_signal_connect(settings, "notify::gtk-interface-contrast", G_CALLBACK(on_prop_notify), (gpointer)"settings");
#endif
#ifdef USE_ADW
    AdwStyleManager *sm = adw_style_manager_get_default();
    g_signal_connect(sm, "notify::dark", G_CALLBACK(on_prop_notify), (gpointer)"adw");
    g_signal_connect(sm, "notify::high-contrast", G_CALLBACK(on_prop_notify), (gpointer)"adw");
    g_signal_connect(sm, "notify::accent-color", G_CALLBACK(on_prop_notify), (gpointer)"adw");
    g_signal_connect(sm, "notify::accent-color-rgba", G_CALLBACK(on_prop_notify), (gpointer)"adw");
#endif

    g_unix_signal_add(SIGUSR1, on_sigusr1, NULL);
    g_unix_signal_add(SIGTERM, on_sigterm, NULL);
    g_unix_signal_add(SIGINT, on_sigterm, NULL);

    if (ready_path) {
        FILE *rf = fopen(ready_path, "w");
        if (rf) {
            fprintf(rf, "ready\n");
            fclose(rf);
        }
    }
    captured = TRUE;
    return G_SOURCE_REMOVE;
}

static void build_and_present_ui(void)
{
    GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 6);
    probe_lbl = gtk_label_new("Platinum discovery");
    gtk_widget_set_name(probe_lbl, "probe");
    ind_theme_lbl = gtk_label_new("Layer: named theme");
    gtk_widget_set_name(ind_theme_lbl, "ind-theme");
    ind_app_lbl = gtk_label_new("Layer: app provider");
    gtk_widget_set_name(ind_app_lbl, "ind-app");
    ind_user_lbl = gtk_label_new("Layer: user gtk.css");
    gtk_widget_set_name(ind_user_lbl, "ind-user");

    GtkWidget *btn_row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
    GtkWidget *btn_norm = gtk_button_new_with_label("Normal");
    GtkWidget *btn_def = gtk_button_new_with_label("Default");
    GtkWidget *btn_dis = gtk_button_new_with_label("Disabled");
    gtk_widget_set_sensitive(btn_dis, FALSE);

    GtkWidget *entry = gtk_entry_new();
    GtkWidget *check = gtk_check_button_new_with_label("Checkbox");
    GtkWidget *sw = gtk_switch_new();
    gtk_switch_set_active(GTK_SWITCH(sw), TRUE);
    gtk_widget_set_halign(sw, GTK_ALIGN_START);

    const char *css = g_getenv("PROBE_APP_CSS");
#if GTK_MAJOR_VERSION == 3
    gtk_style_context_add_class(gtk_widget_get_style_context(btn_def), "suggested-action");
    gtk_entry_set_text(GTK_ENTRY(entry), "Sample text");
    gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(check), TRUE);
    gtk_container_set_border_width(GTK_CONTAINER(box), 10);
    if (css && *css) {
        GtkCssProvider *provider = gtk_css_provider_new();
        g_signal_connect(provider, "parsing-error", G_CALLBACK(on_css_error), NULL);
        gtk_css_provider_load_from_path(provider, css, NULL);
        gtk_style_context_add_provider_for_screen(
            gdk_screen_get_default(),
            GTK_STYLE_PROVIDER(provider),
            GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    }
    gtk_box_pack_start(GTK_BOX(btn_row), btn_norm, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(btn_row), btn_def, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(btn_row), btn_dis, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), probe_lbl, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), ind_theme_lbl, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), ind_app_lbl, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), ind_user_lbl, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), btn_row, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), entry, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), check, FALSE, FALSE, 0);
    gtk_box_pack_start(GTK_BOX(box), sw, FALSE, FALSE, 0);
    gtk_container_add(GTK_CONTAINER(window), box);
    gtk_widget_show_all(window);
#else
    gtk_widget_add_css_class(btn_def, "suggested-action");
    gtk_editable_set_text(GTK_EDITABLE(entry), "Sample text");
    gtk_check_button_set_active(GTK_CHECK_BUTTON(check), TRUE);
    gtk_widget_set_margin_top(box, 10);
    gtk_widget_set_margin_bottom(box, 10);
    gtk_widget_set_margin_start(box, 10);
    gtk_widget_set_margin_end(box, 10);
    if (css && *css) {
        GtkCssProvider *provider = gtk_css_provider_new();
        g_signal_connect(provider, "parsing-error", G_CALLBACK(on_css_error), NULL);
        gtk_css_provider_load_from_path(provider, css);
        gtk_style_context_add_provider_for_display(
            gdk_display_get_default(),
            GTK_STYLE_PROVIDER(provider),
            GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
    }
    gtk_box_append(GTK_BOX(btn_row), btn_norm);
    gtk_box_append(GTK_BOX(btn_row), btn_def);
    gtk_box_append(GTK_BOX(btn_row), btn_dis);
    gtk_box_append(GTK_BOX(box), probe_lbl);
    gtk_box_append(GTK_BOX(box), ind_theme_lbl);
    gtk_box_append(GTK_BOX(box), ind_app_lbl);
    gtk_box_append(GTK_BOX(box), ind_user_lbl);
    gtk_box_append(GTK_BOX(box), btn_row);
    gtk_box_append(GTK_BOX(box), entry);
    gtk_box_append(GTK_BOX(box), check);
    gtk_box_append(GTK_BOX(box), sw);
#ifdef USE_ADW
    GtkWidget *toolbar = adw_toolbar_view_new();
    GtkWidget *hb = adw_header_bar_new();
    adw_toolbar_view_add_top_bar(ADW_TOOLBAR_VIEW(toolbar), hb);
    adw_toolbar_view_set_content(ADW_TOOLBAR_VIEW(toolbar), box);
    adw_application_window_set_content(ADW_APPLICATION_WINDOW(window), toolbar);
#else
    gtk_window_set_child(GTK_WINDOW(window), box);
#endif
    gtk_window_present(GTK_WINDOW(window));
#endif
    g_timeout_add(450, on_initial_settle, NULL);
}

#ifdef USE_ADW
static void on_adw_activate(GApplication *app, gpointer unused)
{
    (void)unused;
    window = adw_application_window_new(GTK_APPLICATION(app));
    gtk_window_set_title(GTK_WINDOW(window), "Platinum libadwaita Discovery");
    gtk_window_set_default_size(GTK_WINDOW(window), 340, 280);
    build_and_present_ui();
}
#endif

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--watch") != 0) {
        watch_mode = FALSE;
        out_png = argv[1];
    } else if ((argc == 4 || argc == 5) && strcmp(argv[1], "--watch") == 0) {
        watch_mode = TRUE;
        ready_path = argv[2];
        log_path = argv[3];
        out_png = (argc == 5) ? argv[4] : NULL;
        log_fp = fopen(log_path, "w");
        if (!log_fp) {
            perror("fopen log_path");
            return 2;
        }
    } else {
        fprintf(stderr, "usage: %s <out.png> | --watch <ready> <log> [final.png]\n", argv[0]);
        return 2;
    }

#ifdef USE_ADW
    adw_app = adw_application_new("org.example.PlatinumDiscovery", G_APPLICATION_NON_UNIQUE);
    g_signal_connect(adw_app, "activate", G_CALLBACK(on_adw_activate), NULL);
    g_application_run(G_APPLICATION(adw_app), 0, NULL);
    g_object_unref(adw_app);
#else
#if GTK_MAJOR_VERSION == 3
    gtk_init(NULL, NULL);
    window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "Platinum GTK 3 Discovery");
    gtk_window_set_default_size(GTK_WINDOW(window), 340, 260);
#else
    gtk_init();
    window = gtk_window_new();
    gtk_window_set_title(GTK_WINDOW(window), "Platinum GTK 4 Discovery");
    gtk_window_set_default_size(GTK_WINDOW(window), 340, 260);
#endif
    loop = g_main_loop_new(NULL, FALSE);
    build_and_present_ui();
    g_main_loop_run(loop);
#endif
    if (log_fp)
        fclose(log_fp);
    return captured ? 0 : 1;
}
