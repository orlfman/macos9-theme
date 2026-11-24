#!/bin/bash
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

mode=$1
export GTK_A11Y=none  # This private session has no AT-SPI registry.
cd "$ROOT"
child=
cleanup() {
    if [[ -n $child ]]; then
        kill "$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
}
trap cleanup EXIT

capture_app() {
    local probe=$1 theme=$2 app_id=$3
    shift 3
    "$@" > "$probe-$theme.log" 2>&1 &
    child=$!
    printf '%s\n' "$child" > "$probe-$theme.pid"
    local witness="GTK4_WINDOW pid=$child app=$app_id "
    for _ in {1..80}; do
        kill -0 "$child"
        rg -Fq "$witness" session.log && break
        sleep 0.1
    done
    rg -Fq "$witness" session.log
    timeout 12 spectacle -b -n -a -o "$ROOT/$probe-$theme.png"
    [[ -s $probe-$theme.png ]]
    cleanup
    child=
}

if [[ $mode == broadway ]]; then
    export GDK_BACKEND=broadway BROADWAY_DISPLAY=:4 GSK_RENDERER=cairo
    gtk4-broadwayd -u "$XDG_RUNTIME_DIR/http4" :4 > broadway.log 2>&1 &
    child=$!
    for _ in {1..30}; do
        [[ -S $XDG_RUNTIME_DIR/broadway5.socket ]] && break
        kill -0 "$child"
        sleep 0.05
    done
else
    export GDK_BACKEND=wayland QT_QPA_PLATFORM=wayland
    dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM
    gsettings set org.gnome.desktop.interface gtk-theme Platinum
    gsettings get org.gnome.desktop.interface gtk-theme > gsettings-theme.txt
    [[ $(<gsettings-theme.txt) == "'Platinum'" ]]
fi

./fixture chrome > chrome.txt
./fixture gallery > dialog.txt
./fixture menus > menus.txt

if [[ $mode == plasma ]]; then
    # KWin confirms that the screenshot is of the launched app's active window.
    cat > factory.js <<'JS'
function report() {
    var w = workspace.activeWindow;
    if (w)
        console.warn("GTK4_WINDOW pid=" + w.pid + " app=" + w.resourceClass + " title=" + w.caption);
}
workspace.windowActivated.connect(report);
report();
JS
    script=$(busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting \
        loadScript ss "$ROOT/factory.js" platinum-gtk4-factory)
    [[ $script =~ ^i[[:space:]]+([0-9]+)$ ]]
    busctl --user call org.kde.KWin "/Scripting/Script${BASH_REMATCH[1]}" org.kde.kwin.Script run

    for theme in Platinum Adwaita; do
        gsettings set org.gnome.desktop.interface gtk-theme "$theme"
        mkdir "controls-$theme"
        (
            cd "controls-$theme"
            ../fixture composites > composites.txt
            ../fixture contrast > contrast.txt &
            child=$!
            trap cleanup EXIT
            for state in initial high; do
                for _ in {1..100}; do
                    rg -q "^contrast-$state=" contrast.txt && break
                    kill -0 "$child"
                    sleep 0.05
                done
                rg -q "^contrast-$state=" contrast.txt
                if [[ $state == initial ]]; then contrast=true; else contrast=false; fi
                gsettings set org.gnome.desktop.a11y.interface high-contrast "$contrast"
            done
            wait "$child"
            child=
        )
        capture_app factory "$theme" org.gtk.WidgetFactory4 gtk4-widget-factory
        capture_app settings "$theme" gtk4-demo gtk4-demo --run=listview_settings

    done

    gsettings set org.gnome.desktop.interface gtk-theme Platinum
    output=$(kscreen-doctor -o | sed -r 's/\x1b\[[0-9;]*m//g' | awk '/Output:/ {print $3}')
    [[ -n $output ]]
    for scale in 1.5 2; do
        mkdir "scale-$scale"
        kscreen-doctor "output.$output.scale.$scale"
        kscreen-doctor -o | sed -r 's/\x1b\[[0-9;]*m//g' > "scale-$scale/output.txt"
        (
            cd "scale-$scale"
            GTK4_CHECK_OUTPUT="$PWD/output.png" ../fixture gallery > dialog.txt
            GTK4_CHECK_OUTPUT="$PWD/lists-output.png" ../fixture menus > menus.txt
        )
    done
fi

touch complete
