#!/bin/bash
# Milestone 1 GTK 3 / plain GTK 4 / stock libadwaita discovery harness.
#
# usage:
#   dev/gtk-discovery.sh broadway   # sandbox-safe standalone + offscreen kded6 checks
#   dev/gtk-discovery.sh plasma     # full disposable virtual KWin + KDE/GTK portal checks
#
# Never touches the user's real HOME, XDG dirs, dconf, or live desktop.
# Verdict is computed from observed logs and PNGs by dev/gtk-discovery/verify.py.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(realpath "$0")")
project=$(dirname "$dev")
mode=${1:-broadway}
case "$mode" in
    broadway | plasma) ;;
    *)
        echo "usage: $0 [broadway|plasma]" >&2
        exit 2
        ;;
esac

mkdir -p "$dev/build" "$dev/shots"
root=$(mktemp -d "$dev/build/gtk-discovery-$mode.XXXXXX")
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'rm -rf "$runtime" 2>/dev/null || true' EXIT

echo "Discovery evidence: $root"
mkdir -p "$root/home/.config" "$root/home/.local/share" "$root/home/.cache" "$root/home/.local/state" "$root/bin"
cat > "$root/bin/systemctl" << 'EOF'
#!/bin/bash
exit 3
EOF
chmod +x "$root/bin/systemctl"

# Build the three minimal fixtures with warnings enabled.
for stack in gtk3 gtk4 adw; do
    case $stack in
        gtk3) pkg=gtk+-3.0 ;;
        gtk4) pkg=gtk4 ;;
        adw)  pkg=libadwaita-1 ;;
    esac
    flags=()
    [[ $stack == adw ]] && flags+=(-DUSE_ADW)
    # shellcheck disable=SC2046
    cc -Wall -Wextra "$dev/gtk-discovery/fixture.c" "${flags[@]}" $(pkg-config --cflags --libs "$pkg") -o "$root/$stack"
done

session=(bash "$dev/gtk-discovery/session.sh" "$mode")
if [[ $mode == plasma ]]; then
    session=(kwin_wayland --virtual --width 1024 --height 768 \
        --no-lockscreen --no-global-shortcuts --no-kactivities \
        --socket macos9-gtk-discovery \
        --exit-with-session "bash '$dev/gtk-discovery/session.sh' plasma")
fi

# Export disposable HOME and all XDG directories BEFORE starting dbus-run-session
# so dconf-service and portal backends inherit the isolated paths (AUDIT.md #148).
session_rc=0
env -i \
    PATH="$root/bin:/usr/local/bin:/usr/bin" \
    HOME="$root/home" \
    USER="${USER:-$(id -un)}" \
    ROOT="$root" \
    RUNTIME="$runtime" \
    PROJECT="$project" \
    LANG=C.UTF-8 \
    XDG_CONFIG_HOME="$root/home/.config" \
    XDG_DATA_HOME="$root/home/.local/share" \
    XDG_CACHE_HOME="$root/home/.cache" \
    XDG_STATE_HOME="$root/home/.local/state" \
    XDG_CONFIG_DIRS="$root/home/.config/kdedefaults:/etc/xdg" \
    XDG_DATA_DIRS="/usr/local/share:/usr/share" \
    XDG_RUNTIME_DIR="$runtime" \
    XDG_CURRENT_DESKTOP=KDE \
    XDG_SESSION_TYPE=wayland \
    QT_FORCE_STDERR_LOGGING=1 \
    KDE_FULL_SESSION=true \
    KDE_SESSION_VERSION=6 \
    timeout 240 dbus-run-session -- "${session[@]}" > "$root/session.log" 2>&1 || session_rc=$?

if [[ $session_rc -ne 0 || ! -s $root/complete ]]; then
    echo "Session did not complete (rc=$session_rc); tail of $root/session.log:" >&2
    tail -25 "$root/session.log" >&2 || true
    if ((session_rc != 0)); then
        exit "$session_rc"
    fi
    exit 1
fi

python3 -I "$dev/gtk-discovery/verify.py" "$root" "$mode" "$dev/shots" | tee "$root/verdict.log"
exit "${PIPESTATUS[0]}"
