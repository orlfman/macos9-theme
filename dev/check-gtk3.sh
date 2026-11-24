#!/bin/bash
# Milestone 2 GTK 3 Platinum pixel-exact chrome and natural-size dialog check.
#
# usage:
#   dev/check-gtk3.sh            # sandbox-safe Broadway 1x check (default)
#   dev/check-gtk3.sh plasma     # virtual KWin Wayland 1x + 150%/200% + HighContrast check
#
# Loads gtk/Platinum via normal named-theme discovery in a disposable HOME/XDG
# session (never touches the user's real desktop or dconf).
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
root=$(mktemp -d "$dev/build/gtk3-m2-$mode.XXXXXX")
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'rm -rf "$runtime" 2>/dev/null || true' EXIT

echo "GTK 3 Milestone 2 evidence: $root"
mkdir -p "$root/home/.config/gtk-3.0" "$root/home/.local/share/themes" "$root/home/.cache" "$root/home/.local/state" "$root/bin"
cp -R "$project/gtk/Platinum" "$root/home/.local/share/themes/Platinum"
cat > "$root/home/.config/gtk-3.0/settings.ini" << 'EOF'
[Settings]
gtk-theme-name=Platinum
gtk-font-name=Noto Sans, 10
EOF

# Build fixture with warnings enabled
# shellcheck disable=SC2046
cc -Wall -Wextra "$dev/gtk3-check/gtk3shot.c" $(pkg-config --cflags --libs gtk+-3.0) -o "$root/gtk3shot"

inner="$root/run.sh"
cat > "$inner" << 'EOF'
#!/bin/bash
set -euo pipefail
umask 022
mode=$1
cd "$ROOT"

# Confirm disposable dconf isolation
gsettings set org.gnome.desktop.interface gtk-theme Platinum
[[ $(gsettings get org.gnome.desktop.interface gtk-theme) == "'Platinum'" ]]

if [[ $mode == broadway ]]; then
    export GDK_BACKEND=broadway
    export BROADWAY_DISPLAY=:3
    broadwayd -u "$XDG_RUNTIME_DIR/http3" :3 > broadway3.log 2>&1 &
    BP=$!
    trap 'kill $BP 2>/dev/null || true' EXIT
    sleep 0.4
else
    export GDK_BACKEND=wayland
    export QT_QPA_PLATFORM=wayland
    dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM
fi

./gtk3shot chrome "$ROOT/gtk3-chrome.png" "$ROOT/gtk3-chrome.txt"
./gtk3shot dialog "$ROOT/gtk3-dialog-active.png" "$ROOT/gtk3-dialog-focus.png" "$ROOT/gtk3-dialog-focus-check.png" "$ROOT/gtk3-dialog-focus-radio.png" "$ROOT/gtk3-dialog-backdrop.png" "$ROOT/gtk3-dialog.txt"

if [[ $mode == plasma ]]; then
    # Check HighContrast theme switching and return to Platinum on GTK 3 (docs/GTK-PLAN.md:42)
    gsettings set org.gnome.desktop.a11y.interface high-contrast true
    sleep 0.5
    ./gtk3shot dialog "$ROOT/gtk3-hc-active.png" "$ROOT/gtk3-hc-focus.png" "$ROOT/gtk3-hc-focus-check.png" "$ROOT/gtk3-hc-focus-radio.png" "$ROOT/gtk3-hc-backdrop.png" "$ROOT/gtk3-hc.txt"
    gsettings set org.gnome.desktop.a11y.interface high-contrast false
    sleep 0.5
    ./gtk3shot dialog "$ROOT/gtk3-hc-restored-active.png" "$ROOT/gtk3-hc-restored-focus.png" "$ROOT/gtk3-hc-restored-focus-check.png" "$ROOT/gtk3-hc-restored-focus-radio.png" "$ROOT/gtk3-hc-restored-backdrop.png" "$ROOT/gtk3-hc-restored.txt"

    # Check 150% and 200% virtual output scaling via kscreen-doctor (docs/GTK-PLAN.md:42)
    out_name=$(kscreen-doctor -o 2>/dev/null | sed 's/\x1b\[[0-9;]*m//g' | awk '/Output:/ {print $3; exit}')
    out_name=${out_name:-Virtual-1}
    for pct in 150 200; do
        scale_val=$( [[ $pct == 150 ]] && echo "1.5" || echo "2" )
        kscreen-doctor "output.${out_name}.scale.${scale_val}" > "$ROOT/scale-$pct.log" 2>&1
        sleep 0.6
        kscreen-doctor -o >> "$ROOT/scale-$pct.log" 2>&1
        ./gtk3shot dialog "$ROOT/gtk3-dialog-${pct}-active.png" "$ROOT/gtk3-dialog-${pct}-focus.png" "$ROOT/gtk3-dialog-${pct}-focus-check.png" "$ROOT/gtk3-dialog-${pct}-focus-radio.png" "$ROOT/gtk3-dialog-${pct}-backdrop.png" "$ROOT/gtk3-dialog-${pct}.txt" "$ROOT/gtk3-output-${pct}.png"
    done
    kscreen-doctor "output.${out_name}.scale.1" > /dev/null 2>&1 || true
fi

echo "finished" > "$ROOT/complete"
EOF
chmod +x "$inner"

session=(bash "$inner" "$mode")
if [[ $mode == plasma ]]; then
    session=(kwin_wayland --virtual --width 1024 --height 768 \
        --no-lockscreen --no-global-shortcuts --no-kactivities \
        --socket macos9-gtk3-m2 \
        --exit-with-session "bash '$inner' plasma")
fi

session_rc=0
env -i \
    PATH="$root/bin:/usr/local/bin:/usr/bin" \
    HOME="$root/home" \
    USER="${USER:-$(id -un)}" \
    ROOT="$root" \
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
    timeout 180 dbus-run-session -- "${session[@]}" > "$root/session.log" 2>&1 || session_rc=$?

if [[ $session_rc -ne 0 || ! -s $root/complete ]]; then
    echo "Session did not complete (rc=$session_rc); tail of $root/session.log:" >&2
    tail -25 "$root/session.log" >&2 || true
    if ((session_rc != 0)); then
        exit "$session_rc"
    fi
    exit 1
fi

python3 -I -W error "$dev/gtk3-check/verify.py" "$root" "$dev/shots" "$mode" | tee "$root/verdict.log"
exit "${PIPESTATUS[0]}"
