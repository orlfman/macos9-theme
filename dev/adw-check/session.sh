#!/bin/bash
# Runs inside dev/check-adw.sh's disposable session.
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

mode=$1
export GTK_A11Y=none  # This private session has no AT-SPI registry.
cd "$ROOT"
[[ $HOME == "$ROOT/home" && -n ${DBUS_SESSION_BUS_ADDRESS:-} ]]

fixture() { # run-name mode
    timeout 30 python3 -I "$DEV/adw-check/fixture.py" "$2" "$ROOT/$1.png" > "$1.log" 2>&1
    rg -q '^RENDERED ' "$1.log"
}

if [[ $mode == broadway ]]; then
    export GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 GSK_RENDERER=cairo
    gtk4-broadwayd -u "$XDG_RUNTIME_DIR/http5" :5 > broadway.log 2>&1 &
    broadway=$!
    # dbus-run-session doesn't stop it; without this every run leaked one.
    trap 'kill "$broadway" 2> /dev/null || true' EXIT
    for _ in {1..40}; do
        [[ -S $XDG_RUNTIME_DIR/broadway6.socket ]] && break
        sleep 0.05
    done
else
    export GDK_BACKEND=wayland QT_QPA_PLATFORM=wayland
    dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM
    plasma-apply-colorscheme Platinum > colorscheme.log 2>&1
    rg -q '^ColorScheme=Platinum' "$XDG_CONFIG_HOME/kdeglobals"
fi
gsettings set org.gnome.desktop.interface gtk-theme Platinum
gsettings set org.gnome.desktop.wm.preferences button-layout 'close:maximize,minimize'
gsettings get org.gnome.desktop.interface gtk-theme > gsettings-theme.txt

if [[ $mode == plasma ]]; then
    busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop \
        org.freedesktop.portal.Settings ReadAll as 1 org.freedesktop.appearance \
        > portal.txt 2>&1 || true
fi

# Real libadwaita apps (plasma only): screenshot the active window once KWin
# reports the launched app active. ProtonPlus is left out: it fetches release
# lists from the network on start.
apps=(
    "ffmpeg ffmpeg-converter-gtk"
    "missioncenter missioncenter"
    "faugus faugus-launcher"
    "zenity zenity --question --title=Alert --text=Delete_this_file?"
)
capture_apps() { # prefix
    local entry name pid
    [[ $mode == plasma ]] || return 0
    for entry in "${apps[@]}"; do
        read -ra cmd <<< "$entry"
        name=${cmd[0]}
        : > kwin-active.log
        "${cmd[@]:1}" > "$1-app-$name.log" 2>&1 &
        pid=$!
        for _ in {1..100}; do
            rg -q "ACTIVE pid=$pid " session.log && break
            kill -0 "$pid" 2>/dev/null || break
            sleep 0.1
        done
        sleep 1.5
        if rg -q "ACTIVE pid=$pid " session.log; then
            timeout 12 spectacle -b -n -a -o "$ROOT/$1-app-$name.png" || true
        fi
        kill "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
    done
}

if [[ $mode == plasma ]]; then
    cat > active.js <<'JS'
function report() {
    var w = workspace.activeWindow;
    if (w)
        console.warn("ACTIVE pid=" + w.pid + " app=" + w.resourceClass + " ");
}
workspace.windowActivated.connect(report);
JS
    script=$(busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
        loadScript ss "$ROOT/active.js" platinum-adw-active)
    [[ $script =~ ^i[[:space:]]+([0-9]+)$ ]]
    busctl --user call org.kde.KWin "/Scripting/Script${BASH_REMATCH[1]}" org.kde.kwin.Script run
fi

# 1. Stock: Platinum desktop settings, no user CSS beyond what exists.
for m in gallery narrow dialog focus disabled alertwin msgdialog prefs; do
    fixture "stock-$m" "$m"
done

# 2. High contrast through the a11y key the GTK portal backend forwards.
gsettings set org.gnome.desktop.a11y.interface high-contrast true
fixture stock-hc gallery
gsettings set org.gnome.desktop.a11y.interface high-contrast false

capture_apps stock

# 3. Platinum layer: the installed theme's libadwaita.css imported from the
#    user stylesheet, the one desktop-wide CSS libadwaita loads (FINDINGS.md).
layer="$XDG_DATA_HOME/themes/Platinum/gtk-4.0/libadwaita.css"
printf '@import url("file://%s");\n' "$layer" > "$XDG_CONFIG_HOME/gtk-4.0/gtk.css"
for m in gallery narrow dialog focus disabled alertwin msgdialog prefs; do
    fixture "layer-$m" "$m"
done
gsettings set org.gnome.desktop.a11y.interface high-contrast true
fixture layer-hc gallery
gsettings set org.gnome.desktop.a11y.interface high-contrast false
capture_apps layer
rm "$XDG_CONFIG_HOME/gtk-4.0/gtk.css"

touch complete
