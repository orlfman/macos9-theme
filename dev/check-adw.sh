#!/bin/bash
# GTK Milestone 5: what an unmodified libadwaita app shows under the
# Platinum desktop, in a disposable HOME, XDG tree and private session bus.
#
# usage: dev/check-adw.sh [broadway|plasma]
#   broadway  sandbox-safe: no portal, libadwaita defaults
#   plasma    virtual KWin + KDE/GTK Settings portals + Platinum colors
#
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
root=$(mktemp -d "$dev/build/adw-m5-$mode.XXXXXX")
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'rm -rf "$runtime"' EXIT
echo "libadwaita Milestone 5 evidence: $root"

home="$root/home"
mkdir -p "$home"/{.config/gtk-4.0,.local/share/themes,.local/share/color-schemes,.cache,.local/state} "$root/bin"
cp -R "$project/gtk/Platinum" "$home/.local/share/themes/"
cp "$project/colors/Platinum.colors" "$home/.local/share/color-schemes/"
cat > "$home/.config/gtk-4.0/settings.ini" <<'INI'
[Settings]
gtk-theme-name=Platinum
gtk-font-name=Noto Sans, 10
gtk-enable-animations=false
gtk-decoration-layout=close:maximize,minimize
INI
# Plasma's GTK sync writes this button layout for the Platinum decoration
# (close box left, zoom and collapse right); Wayland reads it from GSettings.
printf '#!/bin/bash\nexit 3\n' > "$root/bin/systemctl"
chmod +x "$root/bin/systemctl"

runner="$dev/adw-check/session.sh"
session=(bash "$runner" "$mode")
if [[ $mode == plasma ]]; then
    session=(kwin_wayland --virtual --width 1024 --height 768
        --no-lockscreen --no-global-shortcuts --no-kactivities
        --socket platinum-adw --exit-with-session "bash '$runner' plasma")
fi

rc=0
env -i PATH="$root/bin:/usr/local/bin:/usr/bin" HOME="$home" USER="${USER:-$(id -un)}" \
    ROOT="$root" PROJECT="$project" DEV="$dev" LANG=C.UTF-8 \
    XDG_CONFIG_HOME="$home/.config" XDG_DATA_HOME="$home/.local/share" \
    XDG_CACHE_HOME="$home/.cache" XDG_STATE_HOME="$home/.local/state" \
    XDG_CONFIG_DIRS="$home/.config/kdedefaults:/etc/xdg" XDG_DATA_DIRS=/usr/local/share:/usr/share \
    XDG_RUNTIME_DIR="$runtime" XDG_CURRENT_DESKTOP=KDE XDG_SESSION_TYPE=wayland \
    KDE_FULL_SESSION=true KDE_SESSION_VERSION=6 QT_FORCE_STDERR_LOGGING=1 \
    timeout 300 dbus-run-session -- "${session[@]}" > "$root/session.log" 2>&1 || rc=$?

if (( rc != 0 )) || [[ ! -f $root/complete ]]; then
    echo "libadwaita session did not complete (rc=$rc)" >&2
    tail -35 "$root/session.log" >&2
    exit "$((rc == 0 ? 1 : rc))"
fi

python3 -I -W error "$dev/adw-check/verify.py" "$root" "$mode" | tee "$root/verdict.log"
