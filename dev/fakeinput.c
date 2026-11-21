/*
 * Real pointer and keyboard input for tests inside the nested KWin, through
 * KWin's fake input protocol: unlike synthesized Qt events, these reach
 * clients as real Wayland input, so popups that need an input serial (native
 * menus) open, and hover works.
 *
 * usage: fakeinput COMMAND...   commands run in order:
 *   move X Y     pointer to X,Y (screen pixels)
 *   click X Y    move there, then press and release the left button
 *   key CODE     press and release a Linux key code (e.g. 125 = Meta)
 *   sleep MS     wait
 *
 * KWin only offers the protocol to programs whose .desktop file lists it in
 * X-KDE-Wayland-Interfaces; dev/build.sh writes one for the sandbox.
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */
#include "fake-input-client-protocol.h"

#include <linux/input-event-codes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <wayland-client.h>

static struct org_kde_kwin_fake_input *input;

static void global(void *data, struct wl_registry *registry, uint32_t name, const char *interface, uint32_t version)
{
    (void)data;
    if (strcmp(interface, org_kde_kwin_fake_input_interface.name) == 0) {
        input = wl_registry_bind(registry, name, &org_kde_kwin_fake_input_interface, version < 4 ? version : 4);
    }
}

static void global_remove(void *data, struct wl_registry *registry, uint32_t name)
{
    (void)data, (void)registry, (void)name;
}

static const struct wl_registry_listener listener = {global, global_remove};

static void pause_ms(long ms)
{
    struct timespec t = {ms / 1000, (ms % 1000) * 1000000L};
    nanosleep(&t, NULL);
}

int main(int argc, char **argv)
{
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) {
        fprintf(stderr, "fakeinput: no Wayland display\n");
        return 1;
    }
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &listener, NULL);
    wl_display_roundtrip(display);
    if (!input) {
        fprintf(stderr, "fakeinput: the compositor doesn't offer org_kde_kwin_fake_input to this program\n");
        return 2;
    }
    org_kde_kwin_fake_input_authenticate(input, "fakeinput", "macos9-theme tests");

    for (int i = 1; i < argc; ++i) {
        const char *command = argv[i];
        if ((strcmp(command, "move") == 0 || strcmp(command, "click") == 0) && i + 2 < argc) {
            const double x = atof(argv[i + 1]), y = atof(argv[i + 2]);
            i += 2;
            org_kde_kwin_fake_input_pointer_motion_absolute(input, wl_fixed_from_double(x), wl_fixed_from_double(y));
            wl_display_roundtrip(display);
            if (command[0] == 'c') {
                pause_ms(80);
                org_kde_kwin_fake_input_button(input, BTN_LEFT, WL_POINTER_BUTTON_STATE_PRESSED);
                wl_display_roundtrip(display);
                pause_ms(60);
                org_kde_kwin_fake_input_button(input, BTN_LEFT, WL_POINTER_BUTTON_STATE_RELEASED);
            }
        } else if (strcmp(command, "key") == 0 && i + 1 < argc) {
            const uint32_t code = (uint32_t)atoi(argv[++i]);
            org_kde_kwin_fake_input_keyboard_key(input, code, WL_KEYBOARD_KEY_STATE_PRESSED);
            wl_display_roundtrip(display);
            pause_ms(40);
            org_kde_kwin_fake_input_keyboard_key(input, code, WL_KEYBOARD_KEY_STATE_RELEASED);
        } else if (strcmp(command, "sleep") == 0 && i + 1 < argc) {
            pause_ms(atol(argv[++i]));
        } else {
            fprintf(stderr, "fakeinput: can't read '%s'\n", command);
            return 3;
        }
        wl_display_roundtrip(display);
    }
    wl_display_roundtrip(display);
    wl_display_disconnect(display);
    return 0;
}
