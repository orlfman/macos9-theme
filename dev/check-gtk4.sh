#!/bin/bash
# Verify the Platinum GTK 4 control slice in a disposable named-theme session.
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(realpath "$0")")
project=$(dirname "$dev")
mode=${1:-broadway}
case "$mode" in
    broadway | plasma) ;;
    *) echo "usage: $0 [broadway|plasma]" >&2; exit 2 ;;
esac

mkdir -p "$dev/build"
root=$(mktemp -d "$dev/build/gtk4-m4-$mode.XXXXXX")
runtime=$(mktemp -d)
trap 'rm -rf "$runtime"' EXIT
echo "GTK 4 Milestone 4 evidence: $root"

home="$root/home"
mkdir -p "$home"/{.config/gtk-4.0,.local/share/themes,.cache,.local/state}
cp -R "$project/gtk/Platinum" "$home/.local/share/themes/"
cat > "$home/.config/gtk-4.0/settings.ini" <<'INI'
[Settings]
gtk-font-name=Noto Sans, 10
gtk-enable-animations=false
INI
if [[ $mode == broadway ]]; then
    printf 'gtk-theme-name=Platinum\n' >> "$home/.config/gtk-4.0/settings.ini"
fi
# GTK4_CHECK_ADW_LAYER=1: also load the libadwaita layer from the user
# stylesheet, as an installed layer would, to prove plain GTK 4 is unchanged.
if [[ ${GTK4_CHECK_ADW_LAYER:-0} == 1 ]]; then
    printf '@import url("file://%s");\n' \
        "$home/.local/share/themes/Platinum/gtk-4.0/libadwaita.css" > "$home/.config/gtk-4.0/gtk.css"
    echo "with the libadwaita layer in the user stylesheet"
fi

read -ra flags <<< "$(pkg-config --cflags --libs gtk4)"
cc -Wall -Wextra -Werror "$dev/gtk4-check/fixture.c" "${flags[@]}" -o "$root/fixture"

runner="$dev/gtk4-check/session.sh"
session=(bash "$runner" "$mode")
if [[ $mode == plasma ]]; then
    session=(kwin_wayland --virtual --width 1024 --height 768
        --no-lockscreen --no-global-shortcuts --no-kactivities
        --socket platinum-gtk4 --exit-with-session "bash '$runner' plasma")
fi

rc=0
env -i PATH=/usr/local/bin:/usr/bin HOME="$home" USER="${USER:-$(id -un)}" ROOT="$root" \
    LANG=C.UTF-8 XDG_CONFIG_HOME="$home/.config" XDG_DATA_HOME="$home/.local/share" \
    XDG_CACHE_HOME="$home/.cache" XDG_STATE_HOME="$home/.local/state" \
    XDG_CONFIG_DIRS="$home/.config/kdedefaults:/etc/xdg" XDG_DATA_DIRS=/usr/local/share:/usr/share \
    XDG_RUNTIME_DIR="$runtime" XDG_CURRENT_DESKTOP=KDE XDG_SESSION_TYPE=wayland \
    KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 QT_FORCE_STDERR_LOGGING=1 \
    timeout 120 dbus-run-session -- "${session[@]}" > "$root/session.log" 2>&1 || rc=$?

if (( rc != 0 )) || [[ ! -f $root/complete ]]; then
    echo "GTK 4 session did not complete (rc=$rc)" >&2
    tail -35 "$root/session.log" >&2
    exit "$((rc == 0 ? 1 : rc))"
fi

python3 -I -W error "$dev/gtk4-check/verify.py" "$root" "$mode" | tee "$root/verdict.log"
