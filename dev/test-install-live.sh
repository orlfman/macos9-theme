#!/bin/bash
# Tests install.sh --apply and uninstall.sh against a RUNNING Plasma shell,
# kded6 (with its GTK settings sync) and KWin, in a throwaway home: a
# headless nested KWin with two virtual screens, a private D-Bus session,
# its own runtime folder, and a stand-in systemctl (so the shell is handled
# the way uninstall.sh does it outside systemd: kquitapp6, then started
# again). Nothing reaches your real desktop.
#
# Checks (AUDIT.md findings 5, 12 and 33): the user's panels (one per
# screen) are replaced by the menu bar and the dock and come back after
# uninstall, with their widgets and a widget setting of the user's; every
# config and GTK file the GTK sync rewrote is put back byte for byte;
# uninstall stopped the shell and a new one runs afterwards.
#
# usage: test-install-live.sh [--appearance]    (exit 1 if anything failed; ~1 minute)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")

if [[ -z ${M9_TEST_INNER:-} ]]; then
    appearance=0
    case ${1:-} in
        --appearance) appearance=1 ;;
        "") ;;
        *) echo "usage: $0 [--appearance]" >&2; exit 2 ;;
    esac
    root=$dev/build/test-home-live
    rm -rf "$root"
    mkdir -p "$root/home" "$root/runtime" "$root/bin" "$root/prebuilt"
    chmod 700 "$root/runtime"
    cat > "$root/bin/systemctl" << EOF
#!/bin/bash
echo "systemctl \$*" >> "$root/systemctl.log"
exit 3
EOF
    chmod +x "$root/bin/systemctl"
    "$project/style/build.sh" "$root/prebuilt/style" > /dev/null
    "$project/decoration/build.sh" "$root/prebuilt/decoration" > /dev/null
    "$project/style/quick/build.sh" "$root/prebuilt/quick" > /dev/null
    "$project/plasma/build-global-menu.sh" "$root/prebuilt/global-menu" > /dev/null
    "$project/icons/build-whitesur-lavender.sh" "${M9_WHITESUR_UPSTREAM:-$(dirname "$project")/WhiteSur-icon-theme}" "$root/prebuilt/icons" > /dev/null
    rm -f "$root/prebuilt/icons"/WhiteSur-lavender{,-light}/.macos9-whitesur-lavender-build
    if ((appearance)); then
        read -ra qt_flags <<< "$(pkg-config --cflags --libs Qt6Core)"
        c++ -std=c++20 -fPIC -Wall -Wextra -Werror "$dev/light-theme.cpp"             -I/usr/include/KF6/KPackage -I/usr/include/KF6/KCoreAddons -I/usr/include/klookandfeel             "${qt_flags[@]}" -lKF6Package -lklookandfeel -o "$root/light-theme"
    fi
    status=0
    env -i HOME="$root/home" USER="$USER" PATH="$root/bin:/usr/local/bin:/usr/bin" \
        XDG_CONFIG_HOME="$root/home/.config" XDG_DATA_HOME="$root/home/.local/share" \
        XDG_CACHE_HOME="$root/home/.cache" XDG_STATE_HOME="$root/home/.local/state" \
        XDG_DATA_DIRS=/usr/local/share:/usr/share XDG_CONFIG_DIRS="$root/home/.config/kdedefaults:/etc/xdg" \
        XDG_RUNTIME_DIR="$root/runtime" M9_TEST_INNER="$root" M9_TEST_APPEARANCE="$appearance" LANG=C.UTF-8 \
        M9_PREBUILT="$root/prebuilt" XDG_SESSION_TYPE=wayland KDE_FULL_SESSION=true XDG_CURRENT_DESKTOP=KDE \
        KDE_SESSION_VERSION=6 \
        timeout 420 dbus-run-session -- kwin_wayland --virtual --output-count 2 --width 1280 --height 800 \
        --no-lockscreen --no-global-shortcuts --no-kactivities --socket macos9-install-live \
        --exit-with-session "bash $0" > "$root/kwin.log" 2>&1 || status=$?
    cat "$root/result.log" 2> /dev/null || { echo "test-install-live: no result (see $root/kwin.log)"; exit 1; }
    grep -q '^test-install-live: all' "$root/result.log" || exit 1
    exit 0
fi

root=$M9_TEST_INNER
home=$HOME
config=$XDG_CONFIG_HOME
export QT_QPA_PLATFORM=wayland
if ((${M9_TEST_APPEARANCE:-0})); then
    export QT_QPA_PLATFORMTHEME=kde
    dbus-update-activation-environment WAYLAND_DISPLAY QT_QPA_PLATFORM QT_QPA_PLATFORMTHEME XDG_CURRENT_DESKTOP
fi
exec > "$root/result.log" 2>&1
failed=0
passed=0
pass() { printf 'ok      %s\n' "$*"; passed=$((passed + 1)); }
fail() { printf 'FAIL    %s\n' "$*"; failed=$((failed + 1)); }
check() {
    local what=$1
    shift
    if "$@"; then pass "$what"; else fail "$what"; fi
}
same() {
    [[ $1 == "$2" ]] && return 0
    diff <(printf '%s\n' "$1") <(printf '%s\n' "$2") | head -8 | sed 's/^/        /'
    return 1
}
on_bus() {
    dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.NameHasOwner \
        string:"$1" 2> /dev/null | grep -q 'boolean true'
}
wait_bus() { # name seconds
    local i
    for ((i = 0; i < $2 * 5; i++)); do
        on_bus "$1" && return 0
        sleep 0.2
    done
    return 1
}
shell_js() {
    qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$1" 2>&1
}
# Each panel as "screen:location:height", sorted.
panels() {
    shell_js 'print(panels().map(function (p) { return p.screen + ":" + p.location + ":" + p.height; }).sort().join(" "))'
}
# Each panel's widgets in order, with the clock's seconds setting.
widgets() {
    shell_js 'print(panels().map(function (p) { return p.screen + ":" + p.location + "=" + p.widgets().map(function (w) {
        w.currentConfigGroup = ["Appearance"];
        var s = w.readConfig("showSeconds", "");
        return w.type + (s ? "(showSeconds=" + s + ")" : "");
    }).join(","); }).sort().join(" "))'
}
desktop_backgrounds() {
    shell_js 'print(desktops().filter(function (d) { return d.screen >= 0; }).map(function (d) {
        d.currentConfigGroup = ["Wallpaper", d.wallpaperPlugin, "General"];
        return d.screen + ":" + d.wallpaperPlugin + ":" + d.readConfig("Color", "");
    }).sort().join(" "))'
}
shell_pid() {
    dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetConnectionUnixProcessID \
        string:org.kde.plasmashell 2> /dev/null | awk '/uint32/ { print $2 }'
}
restart_plasma_at_login() {
    kquitapp6 plasmashell > /dev/null 2>&1 || return 1
    for _ in {1..100}; do
        on_bus org.kde.plasmashell || break
        sleep 0.2
    done
    ! on_bus org.kde.plasmashell || return 1
    (
        unset QT_PLUGIN_PATH
        source "$config/plasma-workspace/env/macos9-theme.sh"
        exec plasmashell --no-respawn
    ) > "$root/plasmashell-login.log" 2>&1 &
    wait_bus org.kde.plasmashell 30 || return 1
    sleep 3
}
knows_platinum_menu() {
    shell_js 'print(knownWidgetTypes.indexOf("platinum.globalmenu") >= 0 ? "ready" : "missing")'
}
menu_slot() {
    shell_js 'var slots = [];
    panels().forEach(function (p) { p.widgets().forEach(function (w) {
        if (w.type !== "org.kde.plasma.appmenu" && w.type !== "platinum.globalmenu") return;
        w.currentConfigGroup = ["Appearance"];
        slots.push([p.id, w.id, w.index, w.type, w.readConfig("compactView", false), w.readConfig("allScreens", true)].join(":"));
    }); });
    print(slots.sort().join(" "));'
}
# The config and GTK files a switch may change (the shell's own layout
# files aside: they're compared through the running shell).
files_state() {
    (cd "$home" && find .config/kdeglobals .config/kwinrc .config/plasmarc .config/kcminputrc .config/ksplashrc \
        .config/kscreenlockerrc .config/kdedefaults .config/gtk-3.0 .config/gtk-4.0 .config/xsettingsd .gtkrc-2.0 \
        -printf '%y %m %p -> %l\n' 2> /dev/null | sort
    find .config/kdeglobals .config/kwinrc .config/plasmarc .config/kcminputrc .config/ksplashrc \
        .config/kscreenlockerrc .config/kdedefaults .config/gtk-3.0 .config/gtk-4.0 .config/xsettingsd .gtkrc-2.0 \
        -type f -print0 2> /dev/null | sort -z | xargs -0 -r sha256sum) || true
}

# The user's own setup: GTK files of their own and Breeze, as a session
# makes them.
mkdir -p "$config/gtk-4.0" "$config/gtk-3.0" "$home/.local/state"
printf '/* user css */\n@import url("mine.css");\n' > "$config/gtk-4.0/gtk.css"
printf '[Settings]\ngtk-theme-name=Breeze\n' > "$config/gtk-3.0/settings.ini"
/usr/lib/kactivitymanagerd > "$root/activities.log" 2>&1 &
kded6 > "$root/kded.log" 2>&1 &
sleep 1
plasmashell --no-respawn > "$root/plasmashell-1.log" 2>&1 &
check "Plasma's shell started" wait_bus org.kde.plasmashell 30
sleep 6
# A panel of the user's own on the second screen too: the scripting API
# puts new panels on screen 0, so it's moved in the config and the shell
# restarted.
shell_js "var p = new Panel; p.location = 'left'; p.height = 48;
    var w = p.addWidget('org.kde.plasma.digitalclock'); w.currentConfigGroup = ['Appearance'];
    w.writeConfig('showSeconds', 2); print(p.id);" > "$root/second-panel.log"
sleep 3
kquitapp6 plasmashell > /dev/null 2>&1 || true
for ((i = 0; i < 50; i++)); do on_bus org.kde.plasmashell || break; sleep 0.2; done
kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group Containments --group "$(tr -dc 0-9 < "$root/second-panel.log")" \
    --key lastScreen 1
plasmashell --no-respawn > "$root/plasmashell-2.log" 2>&1 &
wait_bus org.kde.plasmashell 30 || true
sleep 6
sleep 3
before_panels=$(panels)
before_widgets=$(widgets)
echo "info    the user's panels: $before_panels"
echo "info    their widgets: $before_widgets"
check "the user's second panel has its clock with seconds" bash -c "[[ '$before_widgets' == *'1:left=org.kde.plasma.digitalclock(showSeconds=2)'* ]]"
shell_js 'desktops().filter(function (d) { return d.screen >= 0; }).forEach(function (d) {
    d.wallpaperPlugin = "org.kde.color";
    d.currentConfigGroup = ["Wallpaper", "org.kde.color", "General"];
    d.writeConfig("Color", d.screen === 0 ? "27,73,109" : "45,99,67");
});' > "$root/seed-wallpaper.log"
before_backgrounds=$(desktop_backgrounds)
check "the two screens start with their own solid wallpapers" same \
    "0:org.kde.color:27,73,109 1:org.kde.color:45,99,67" "$before_backgrounds"
# The cursor in effect: the user's own value, else the global theme's
# default (kdedefaults).
cursor_theme() {
    local v
    v=$(kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme)
    [[ -n $v ]] || v=$(kreadconfig6 --file "$config/kdedefaults/kcminputrc" --group Mouse --key cursorTheme)
    printf '%s' "$v"
}
icon_theme() {
    XDG_CONFIG_HOME="$config" XDG_CONFIG_DIRS="$config/kdedefaults:/etc/xdg" \
        kreadconfig6 --file kdeglobals --group Icons --key Theme
}
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme Breeze_Light
before_files=$(files_state)
if ((${M9_TEST_APPEARANCE:-0})); then
    before_gtk_icon=$(gsettings get org.gnome.desktop.interface icon-theme)
fi

check "install exits 0" bash -c "'$project/install.sh' > '$root/install.log' 2>&1"
check "a running pre-install shell cannot discover the staged menu" same missing "$(knows_platinum_menu)"
check "install alone keeps both wallpapers" same "$before_backgrounds" "$(desktop_backgrounds)"
check "install installed the cursor theme" test -r "$XDG_DATA_HOME/icons/macOS-cursors/cursors/left_ptr"
check "install installed the WhiteSur Lavender icon themes" bash -c '
    test -r "$1/icons/WhiteSur-lavender/places/scalable/folder.svg" &&
    test -r "$1/icons/WhiteSur-lavender-light/index.theme" &&
    test ! -e "$1/icons/WhiteSur-lavender-dark"
' _ "$XDG_DATA_HOME"
if ((${M9_TEST_APPEARANCE:-0})); then
    scheme="$XDG_DATA_HOME/plasma/look-and-feel/platinum.desktop/contents/colors"
    check "Plasma classifies installed Platinum as light from its bundled palette" "$root/light-theme" "$scheme"
    check "bundled palette matches the standalone scheme" cmp "$scheme" "$XDG_DATA_HOME/color-schemes/Platinum.colors"
    check "Platinum Window and View backgrounds stay light" python3 -I "$dev/light-theme.py" "$scheme"
fi
check "install --apply exits 0" bash -c "'$project/install.sh' --apply > '$root/apply.log' 2>&1"
check "apply selects the Platinum cursors (macOS-cursors)" same macOS-cursors "$(cursor_theme)"
check "apply selects the WhiteSur Lavender icons (WhiteSur-lavender-light)" same WhiteSur-lavender-light "$(icon_theme)"
sleep 6
if ((${M9_TEST_APPEARANCE:-0})); then
    check "the real Settings portal reports prefer-light" same "v v u 2" "$(busctl --user call         org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings         Read ss org.freedesktop.appearance color-scheme)"
    check "kde-gtk-config publishes prefer-light to GSettings" same "'prefer-light'"         "$(gsettings get org.gnome.desktop.interface color-scheme)"
    for _ in {1..30}; do
        [[ $(gsettings get org.gnome.desktop.interface icon-theme) == "'WhiteSur-lavender-light'" ]] && break
        sleep 0.1
    done
    check "kde-gtk-config selects the light icons in Wayland GTK" same "'WhiteSur-lavender-light'"         "$(gsettings get org.gnome.desktop.interface icon-theme)"
    for version in 3 4; do
        check "GTK $version settings have prefer-dark=false" grep -Fxq             'gtk-application-prefer-dark-theme=false' "$config/gtk-$version.0/settings.ini"
    done
    check "Firefox with the installed userChrome follows System light, dark and light"         python3 -I "$dev/light-theme.py" "$root" "$project"
fi
after_panels=$(panels)
echo "info    after --apply: $after_panels"
check "--apply replaced the panels with the menu bar and the dock" \
    bash -c "[[ '$after_panels' == *':top:20'* && '$after_panels' == *':bottom:52'* && '$after_panels' != *'left'* ]]"
applied_widgets=$(widgets)
echo "info    dock widgets after --apply: $applied_widgets"
check "the new layout uses stock Global Menu before the next login" grep -Fq 'org.kde.plasma.appmenu' <<< "$applied_widgets"
check "--apply puts the Platinum Trash at the dock's end" \
    bash -c "[[ '$applied_widgets' == *'bottom=org.kde.plasma.icontasks,platinum.trash'* && '$applied_widgets' != *'org.kde.plasma.trash'* ]]"
check "--apply switches both screens to image wallpaper" same \
    "0:org.kde.image: 1:org.kde.image:" "$(desktop_backgrounds)"
# Compare the wallpaper that was actually rendered on both screens with
# the installed image, cropped the same way Plasma's image plugin crops it.
cat > "$root/wallpaper.qml" << 'QML'
import QtQuick
Window {
    width: 1280
    height: 800
    Image {
        anchors.fill: parent
        source: "file://" + Qt.application.arguments[3]
        fillMode: Image.PreserveAspectCrop
    }
}
QML
wallpaper_matches() {
    QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software "$dev/build/quickshot" \
        "$root/wallpaper.qml" "$root/wallpaper-expected.png" \
        "$XDG_DATA_HOME/wallpapers/platinum-lavender/contents/images/3840x2160.jxl" || return 1
    spectacle -b -n -f -o "$root/wallpaper-desktop.png" || return 1
    python3 -I - "$root" << 'PYEND'
from pathlib import Path
import sys
from PIL import Image, ImageChops, ImageStat

root = Path(sys.argv[1])
expected = Image.open(root / "wallpaper-expected.png").convert("RGB")
actual = Image.open(root / "wallpaper-desktop.png").convert("RGB")
assert expected.size == (1280, 800) and actual.size == (2560, 800)
# (The Lavender Desktop Pattern is subtle: its spread is about 9, a blank
# image's 0.)
assert max(ImageStat.Stat(expected).stddev) > 5, "reference wallpaper did not load"
for screen in (0, 1):
    for box in ((80, 230, 200, 350), (1090, 470, 1210, 590)):
        x0, y0, x1, y1 = box
        offset = screen * expected.width
        sample = actual.crop((x0 + offset, y0, x1 + offset, y1))
        error = ImageStat.Stat(ImageChops.difference(sample, expected.crop(box))).mean
        assert max(error) < 4, (screen, box, error)
PYEND
}
check "--apply renders Lavender Desktop Pattern on both screens" wallpaper_matches
# With the real GTK sync (kded) running through the switch, the libadwaita
# import stays first and the user's own rules stay (decision 15).
cp "$config/gtk-4.0/gtk.css" "$root/gtk4-after-apply.css"
check "after --apply gtk-4.0/gtk.css starts with the libadwaita import" bash -c "
    head -1 '$config/gtk-4.0/gtk.css' | grep -Fq 'macos9-theme: Platinum for libadwaita' &&
    sed -n 2p '$config/gtk-4.0/gtk.css' | grep -Fq '/gtk-4.0/libadwaita.css\");'"
check "  once, with the user's rules kept" bash -c "
    [[ \$(grep -cF 'macos9-theme: Platinum for libadwaita' '$config/gtk-4.0/gtk.css') == 1 ]] &&
    grep -Fqx '@import url(\"mine.css\");' '$config/gtk-4.0/gtk.css'"
after_files=$(files_state)
check "install.sh again after the switch exits 0 (an update; no links in the copied folders)" \
    bash -c "'$project/install.sh' > '$root/install-2.log' 2>&1"
check "restart with the generated login script" restart_plasma_at_login
check "Plasma discovers the user-scope binary after login" same ready "$(knows_platinum_menu)"
# Emulate a version that applied the full layout before recording menu modes.
legacy_menu_slot=$(menu_slot)
rm "$XDG_STATE_HOME/macos9-theme/global-menu-layout"
check "legacy full-layout upgrade switches the stock slot" bash -c "'$project/install.sh' --apply > '$root/legacy-menu-upgrade.log' 2>&1"
check "legacy upgrade keeps the same menu slot" same "${legacy_menu_slot/org.kde.plasma.appmenu/platinum.globalmenu}" "$(menu_slot)"
check "legacy upgrade retains full layout restore policy (#321)" grep -Fxq reset "$XDG_STATE_HOME/macos9-theme/global-menu-layout"

runtime_stamp=$home/.local/lib/macos9-theme/global-menu/runtime.json
cp "$runtime_stamp" "$root/runtime-original.json"
# Simulate the same SONAME with changed contents, without upgrading the host.
python3 -I - "$runtime_stamp" <<'PYEND'
import json, sys
from pathlib import Path
stamp = Path(sys.argv[1])
data = json.loads(stamp.read_text())
key = next(path for path in data["runtime"] if "/libPlasma.so." in path)
data["runtime"][key] = "0" * 64
stamp.write_text(json.dumps(data))
PYEND
check "login after a Plasma library change starts the shell" restart_plasma_at_login
check "login hides the stale plugin from Plasma" same missing "$(knows_platinum_menu)"
check "stale login restores stock in the same applet slot" same "$legacy_menu_slot" "$(menu_slot)"
check "stock Global Menu owns the service after fallback" wait_bus org.kde.kappmenuview 6
# Undo the synthetic file edit. A real library update leaves the installed
# stamp byte-for-byte intact, so the manifest would not displace it.
cp "$root/runtime-original.json" "$runtime_stamp"
check "reinstall publishes a compatible applet" bash -c "'$project/install.sh' > '$root/menu-rebuild.log' 2>&1"
check "next login discovers the rebuilt applet" restart_plasma_at_login
check "the rebuilt applet is discoverable" same ready "$(knows_platinum_menu)"
check "reapply enables the rebuilt applet in the same slot" bash -c "'$project/install.sh' --apply > '$root/menu-rebuild-apply.log' 2>&1"
check "reapply keeps the saved menu settings and position" same "${legacy_menu_slot/org.kde.plasma.appmenu/platinum.globalmenu}" "$(menu_slot)"
check "a new layout in a ready shell uses Platinum Global Menu" \
    shell_js "$(cat "$project/plasma/layout.js")"
ready_slot=$(menu_slot)
check "the fresh ready layout loads only the Platinum menu" \
    grep -Eq '^[0-9]+:[0-9]+:[0-9]+:platinum\.globalmenu:false:true$' <<< "$ready_slot"
check "the loaded menu owns the app-menu service" wait_bus org.kde.kappmenuview 6
# A Qt Quick app started with the login script's environment (as after the
# next login) gets the Platinum Qt Quick style.
cat > "$root/quick-probe.qml" << 'QML'
import QtQuick
import QtQuick.Controls as QQC2
QQC2.ApplicationWindow { width: 100; height: 60; visible: false; QQC2.Button { id: b; text: "x" }
    Component.onCompleted: console.log("PROBE style ok", b.background !== null) }
QML
quick_style() {
    sh -c ". '$config/plasma-workspace/env/macos9-theme.sh'; QT_FORCE_STDERR_LOGGING=1 exec '$dev/build/quickshot' '$root/quick-probe.qml' '$root/quick-probe.png'" 2>&1 |
        sed -n 's/^QtQuick style: "\(.*\)"$/\1/p'
}
check "after the switch, a Qt Quick app gets the Platinum Qt Quick style" bash -c "[[ \$($(declare -f quick_style); root='$root' config='$config' dev='$dev'; quick_style) == Platinum ]]"
if [[ $after_files != "$before_files" ]]; then
    echo "info    the switch changed these config/GTK files (incl. Plasma's GTK sync):"
    diff <(printf '%s\n' "$before_files" | grep -v '^[0-9a-f]\{64\}') <(printf '%s\n' "$after_files" | grep -v '^[0-9a-f]\{64\}') |
        grep '^[<>]' | sed 's/^/          /' | head -20 || true
    diff <(printf '%s\n' "$before_files" | grep '^[0-9a-f]\{64\}') <(printf '%s\n' "$after_files" | grep '^[0-9a-f]\{64\}') |
        grep '^>' | awk '{ print "          changed " $3 }' | head -20 || true
fi

# A launcher that lives across the uninstall with the session's
# environment (like Plasma's shell or a terminal), starting a Qt Quick app
# only afterwards (finding 49).
rm -f "$root/go"
sh -c ". '$config/plasma-workspace/env/macos9-theme.sh'; touch '$root/launcher-ready'; while [ ! -e '$root/go' ]; do sleep 0.2; done
    QT_FORCE_STDERR_LOGGING=1 exec '$dev/build/quickshot' '$root/quick-probe.qml' '$root/quick-probe-late.png'" > "$root/launcher.log" 2>&1 &
launcher=$!
for _ in {1..50}; do
    [[ ! -e $root/launcher-ready ]] || break
    sleep 0.1
done
check "the test launcher sourced the login hook before uninstall" test -e "$root/launcher-ready"
old_pid=$(shell_pid)
check "uninstall exits 0" bash -c "'$project/uninstall.sh' > '$root/uninstall.log' 2>&1"
check "uninstall put the config files back" grep -q "Put back your config files" "$root/uninstall.log"
check "uninstall stopped the shell (its process is gone)" bash -c "[[ -n '$old_pid' ]] && ! kill -0 '$old_pid' 2> /dev/null"
check "Plasma's shell runs again" wait_bus org.kde.plasmashell 30
new_pid=$(shell_pid)
check "  as a new process" bash -c "[[ -n '$new_pid' && '$new_pid' != '$old_pid' ]]"
sleep 6
restored_panels=$(panels)
echo "info    after uninstall: $restored_panels"
check "the user's panels are back" same "$before_panels" "$restored_panels"
restored_widgets=$(widgets)
echo "info    their widgets after uninstall: $restored_widgets"
check "  with their widgets and the clock's setting" same "$before_widgets" "$restored_widgets"
check "both original wallpapers are back" same "$before_backgrounds" "$(desktop_backgrounds)"
for id in platinum-ribbon platinum-lavender platinum-waves platinum-glass platinum-nebula platinum-finder-waves platinum-ripples; do
    check "uninstall removed $id" test ! -e "$XDG_DATA_HOME/wallpapers/$id"
done
check "every config and GTK file is back byte for byte" same "$before_files" "$(files_state)"
if ((${M9_TEST_APPEARANCE:-0})); then
    check "uninstall restored the prior Wayland GTK icon preference" same "$before_gtk_icon" \
        "$(gsettings get org.gnome.desktop.interface icon-theme)"
fi
check "uninstall restored the previous cursor" same Breeze_Light "$(cursor_theme)"
check "uninstall removed the cursor theme" test ! -e "$XDG_DATA_HOME/icons/macOS-cursors"
check "uninstall removed the WhiteSur Lavender icon themes" bash -c '
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        [[ ! -e "$1/icons/$id" && ! -L "$1/icons/$id" ]] || exit 1
    done
' _ "$XDG_DATA_HOME"
touch "$root/go"
launcher_status=0
wait "$launcher" || launcher_status=$?
check "a launcher from before the uninstall still starts Qt Quick apps (exit $launcher_status)" \
    bash -c "[[ $launcher_status == 0 ]] && grep -q 'QtQuick style: \"Platinum\"' '$root/launcher.log'"
# The next login: the one-shot script uninstall.sh left runs.
if [[ -f $config/plasma-workspace/env/macos9-theme-cleanup.sh ]]; then
    sh -c '. "$1"' _ "$config/plasma-workspace/env/macos9-theme-cleanup.sh"
fi
check "after the next login, nothing of the theme is left" bash -c "[[ ! -e '$home/.local/lib/macos9-theme' && ! -e '$config/plasma-workspace/env/macos9-theme-cleanup.sh' ]]"
check "after uninstall, Qt Quick apps get KDE's style again" bash -c "[[ ! -e '$config/plasma-workspace/env/macos9-theme.sh' ]] &&
    [[ \$(QT_FORCE_STDERR_LOGGING=1 '$dev/build/quickshot' '$root/quick-probe.qml' '$root/quick-probe.png' 2>&1 | sed -n 's/^QtQuick style: \"\\(.*\\)\"\$/\\1/p') == org.kde.desktop ]]"
# Select both wallpapers from the picker without switching away from Breeze.
check "picker-only install exits 0" bash -c "'$project/install.sh' > '$root/picker-install.log' 2>&1"
shell_js "desktops().filter(function (d) { return d.screen >= 0; }).forEach(function (d) {
    d.wallpaperPlugin = 'org.kde.image';
    d.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
    d.writeConfig('Image', 'file://$XDG_DATA_HOME/wallpapers/' + (d.screen === 0
        ? 'platinum-ribbon/' : 'platinum-lavender/contents/images/3840x2160.jxl'));
});" > "$root/picker-selection.log"
check "dry run keeps the selected packages" bash -c "'$project/uninstall.sh' --dry-run > '$root/picker-dry.log' 2>&1 &&
    [[ \$(grep -c 'is still selected in Plasma' '$root/picker-dry.log') == 2 ]]"
check "picker-only uninstall reports the deferred removal" bash -c "'$project/uninstall.sh' > '$root/picker-undo.log' 2>&1; [[ \$? == 1 ]]"
check "both selected wallpaper files are kept" bash -c "[[ -s '$XDG_DATA_HOME/wallpapers/platinum-ribbon/contents/images/3840x2160.jxl' &&
    -s '$XDG_DATA_HOME/wallpapers/platinum-lavender/contents/images/3840x2160.jxl' ]]"
check "the five unselected wallpaper packages are removed" bash -c "[[ ! -e '$XDG_DATA_HOME/wallpapers/platinum-waves' &&
    ! -e '$XDG_DATA_HOME/wallpapers/platinum-glass' && ! -e '$XDG_DATA_HOME/wallpapers/platinum-nebula' &&
    ! -e '$XDG_DATA_HOME/wallpapers/platinum-finder-waves' && ! -e '$XDG_DATA_HOME/wallpapers/platinum-ripples' ]]"
check "picker-only uninstall keeps the panel layout" same "$before_panels" "$(panels)"
shell_js 'desktops().forEach(function (d) { d.wallpaperPlugin = "org.kde.color"; });' > "$root/picker-clear.log"
check "picker-only uninstall can finish after changing the wallpapers" bash -c "'$project/uninstall.sh' > '$root/picker-undo-2.log' 2>&1"
check "both no-longer-selected packages are removed" bash -c "[[ ! -e '$XDG_DATA_HOME/wallpapers/platinum-ribbon' &&
    ! -e '$XDG_DATA_HOME/wallpapers/platinum-lavender' ]]"

# A Platinum layout from before the bundled menu. The selected theme and
# panel are already the user's, so --apply changes only the menu slot.
kwriteconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage platinum.desktop
shell_js 'var bar = new Panel;
    bar.location = "top"; bar.height = 37;
    bar.addWidget("org.kde.plasma.digitalclock");
    var menu = bar.addWidget("org.kde.plasma.appmenu");
    menu.currentConfigGroup = ["Appearance"];
    menu.writeConfig("compactView", true); menu.writeConfig("allScreens", false);
    bar.addWidget("org.kde.plasma.panelspacer");' > "$root/old-platinum-bar.log"
sleep 1
legacy_slot=$(menu_slot)
legacy_panels=$(panels)
check "the customized stock slot has its settings" grep -Eq ':org\.kde\.plasma\.appmenu:true:false$' <<< "$legacy_slot"
check "install for an existing Platinum panel" bash -c "'$project/install.sh' > '$root/custom-install.log' 2>&1"
check "restart the existing layout with its login script" restart_plasma_at_login
check "the previous menu remains until explicitly applied" same "$legacy_slot" "$(menu_slot)"

# Interrupt the swap after the layout reaches disk and before the shell
# comes back. The next apply resumes the stopped shell and the same slot.
mkdir "$root/restart-failure"
printf '#!/bin/sh\nexit 1\n' > "$root/restart-failure/setsid"
chmod +x "$root/restart-failure/setsid"
if PATH="$root/restart-failure:$PATH" "$project/install.sh" --apply > "$root/custom-interrupted.log" 2>&1; then
    fail "the interrupted migration is reported"
else
    check "the interrupted migration is reported" grep -Fq 'finish the global menu panel change' "$root/custom-interrupted.log"
fi
check "the interrupted migration records the stopped shell" grep -Fxq direct "$XDG_STATE_HOME/macos9-theme/shell-stopped"
check "retry completes the interrupted migration" bash -c "'$project/install.sh' --apply > '$root/custom-apply.log' 2>&1"
check "in-place apply preserves panel positions and heights" same "$legacy_panels" "$(panels)"
check "in-place apply keeps the applet ID, index, and settings" same \
    "${legacy_slot/org.kde.plasma.appmenu/platinum.globalmenu}" "$(menu_slot)"
check "the migrated menu owns the app-menu service" wait_bus org.kde.kappmenuview 6
check "the in-place restore policy survives retry" grep -Fxq in-place "$XDG_STATE_HOME/macos9-theme/global-menu-layout"
check "the restarted shell does not hold the installer lock" flock -n "$XDG_STATE_HOME/macos9-theme/lock" true

# Move the menu after migration and change an unrelated widget before undo.
shell_js 'var top = panels().filter(function (p) { return p.location === "top"; })[0];
    var target = panels().filter(function (p) { return p.location === "left"; })[0];
    target.addWidget(top.widgets("platinum.globalmenu")[0]);
    var clock = top.widgets("org.kde.plasma.digitalclock")[0];
    clock.currentConfigGroup = ["Appearance"]; clock.writeConfig("showSeconds", 2);' > "$root/custom-move.log"
sleep 2
moved_slot=$(menu_slot)
moved_widgets=$(widgets)
check "the menu is now in a different panel" bash -c '[[ ${1%%:*} != ${2%%:*} ]]' _ "$moved_slot" "$legacy_slot"
check "in-place uninstall succeeds" bash -c "'$project/uninstall.sh' > '$root/custom-uninstall.log' 2>&1"
check "in-place uninstall leaves the moved slot in place as stock" same \
    "${moved_slot/platinum.globalmenu/org.kde.plasma.appmenu}" "$(menu_slot)"
check "in-place uninstall keeps the other widgets and later clock change" same \
    "${moved_widgets/platinum.globalmenu/org.kde.plasma.appmenu}" "$(widgets)"
check "in-place uninstall removes the menu binary" test ! -e "$home/.local/lib/macos9-theme/global-menu/plasma/applets/platinum.globalmenu.so"
check "in-place uninstall removes its catalog" test ! -e "$XDG_DATA_HOME/locale/fr/LC_MESSAGES/plasma_applet_platinum.globalmenu.mo"

check "nothing touched a real systemd session" bash -c "! grep -qv 'is-active' '$root/systemctl.log' 2> /dev/null"

echo
if ((failed)); then
    echo "test-install-live: $failed FAILED, $passed passed (logs in $root)"
else
    echo "test-install-live: all $passed passed (logs in $root)"
fi
pid=$(dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetConnectionUnixProcessID \
    string:org.kde.plasmashell 2> /dev/null | awk '/uint32/ { print $2 }')
[[ -n $pid ]] && kill "$pid" 2> /dev/null
kill $(jobs -p) 2> /dev/null || true
exit 0
