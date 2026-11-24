#!/bin/bash
# Milestone 3 Batch 1 GTK 3 Platinum verification:
#   menus, menu bar, pop-ups/comboboxes, treeviews/headers, frames, separators,
#   plus real GTK 3 application (meld) smoke/CSS check.
#
# usage:
#   dev/check-gtk3-m3b1.sh            # sandbox-safe Broadway check (default)
#   dev/check-gtk3-m3b1.sh plasma     # virtual KWin Wayland + spectacle meld capture
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
root=$(mktemp -d "$dev/build/gtk3-m3b1-$mode.XXXXXX")
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'rm -rf "$runtime" 2>/dev/null || true' EXIT

echo "GTK 3 Milestone 3 Batch 1 evidence: $root"
mkdir -p "$root/home/.config/gtk-3.0" "$root/home/.local/share/themes" "$root/home/.cache" "$root/home/.local/state" "$root/bin"
cp -R "$project/gtk/Platinum" "$root/home/.local/share/themes/Platinum"
cat > "$root/home/.config/gtk-3.0/settings.ini" << 'EOF'
[Settings]
gtk-theme-name=Platinum
gtk-font-name=Noto Sans, 10
EOF

# Build fixture with warnings enabled
# shellcheck disable=SC2046
cc -Wall -Wextra "$dev/gtk3-m3b1/m3b1shot.c" $(pkg-config --cflags --libs gtk+-3.0) -o "$root/m3b1shot"

inner="$root/run.sh"
cat > "$inner" << 'EOF'
#!/bin/bash
set -euo pipefail
umask 022
mode=$1
cd "$ROOT"

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

./m3b1shot chrome "$ROOT/m3b1-chrome.png" "$ROOT/m3b1-chrome.txt"
./m3b1shot gallery "$ROOT/m3b1-gallery-active.png" "$ROOT/m3b1-gallery-backdrop.png" "$ROOT/m3b1-menu-open.png" "$ROOT/m3b1-gallery.txt"

# Real GTK 3 application smoke & CSS-error check: meld comparing two sample files
printf 'Mac OS 9.2.2\nPlatinum\nLavender\n' > "$ROOT/a.txt"
printf 'Mac OS 9.2.2\nPlatinum GTK 3\nLavender\n' > "$ROOT/b.txt"
capture_meld() {
    cat > "$ROOT/meld-window.js" << 'JS'
function report() {
    var w = workspace.activeWindow;
    if (!w || w.pid !== MELD_PID) return;
    var g = w.frameGeometry;
    console.warn("MELD_WINDOW pid=" + w.pid + " app=" + w.resourceClass
        + " x=" + Math.round(g.x) + " y=" + Math.round(g.y)
        + " width=" + Math.round(g.width) + " height=" + Math.round(g.height));
}
workspace.windowActivated.connect(report);
report();
JS
    sed -i "s/MELD_PID/$mpid/" "$ROOT/meld-window.js"
    local script row
    script=$(busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
        loadScript ss "$ROOT/meld-window.js" macos9-meld)
    [[ $script =~ ^i[[:space:]]+([0-9]+)$ ]] || return 1
    busctl --user call org.kde.KWin "/Scripting/Script${BASH_REMATCH[1]}" org.kde.kwin.Script run || return 1
    for _ in {1..30}; do
        row=$(sed -n 's/^.*MELD_WINDOW pid=/pid=/p' session.log | tail -1)
        [[ -n $row ]] && break
        sleep 0.1
    done
    [[ -n $row ]] || return 1
    printf 'MELD_WINDOW %s\n' "$row"
    timeout 15 spectacle -b -n -a -o "$ROOT/meld-active.png" && [[ -s $ROOT/meld-active.png ]] \
        && timeout 15 spectacle -b -n -f -o "$ROOT/meld-plasma.png" && [[ -s $ROOT/meld-plasma.png ]]
}

if [[ -x /usr/bin/meld ]]; then
    : > meld.log
    /usr/bin/meld "$ROOT/a.txt" "$ROOT/b.txt" >> meld.log 2>&1 &
    mpid=$!
    echo "MELD_PID=$mpid" >> meld.log
    owner=""
    for _ in {1..40}; do
        owner=$(busctl --user call org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus \
            GetConnectionUnixProcessID s org.gnome.Meld 2>/dev/null || true)
        [[ $owner == "u $mpid" ]] && break
        sleep 0.15
    done
    echo "MELD_OWNER=$owner" >> meld.log
    if [[ $owner == "u $mpid" ]] && kill -0 "$mpid" 2>/dev/null; then
        if [[ $mode == broadway ]] || capture_meld >> meld.log 2>&1; then
            echo "MELD_STATUS=PASS" >> meld.log
        else
            echo "MELD_STATUS=FAIL reason=window-or-capture-missing" >> meld.log
        fi
    else
        echo "MELD_STATUS=FAIL reason=process-or-bus-owner-missing" >> meld.log
    fi
    kill -TERM "$mpid" 2>/dev/null || true
    wait "$mpid" 2>/dev/null || true
else
    echo "MELD_STATUS=FAIL reason=not-installed" > "$ROOT/meld.log"
fi

echo "finished" > "$ROOT/complete"
EOF
chmod +x "$inner"

session=(bash "$inner" "$mode")
if [[ $mode == plasma ]]; then
    session=(kwin_wayland --virtual --width 1280 --height 900 \
        --no-lockscreen --no-global-shortcuts --no-kactivities \
        --socket macos9-gtk3-m3b1 \
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

python3 -I -W error "$dev/gtk3-m3b1/verify.py" "$root" "$dev/shots" "$mode" | tee "$root/verdict.log"
exit "${PIPESTATUS[0]}"
