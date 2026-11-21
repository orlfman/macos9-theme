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
# usage: test-install-live.sh    (exit 1 if anything failed; ~1 minute)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")

if [[ -z ${M9_TEST_INNER:-} ]]; then
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
    status=0
    env -i HOME="$root/home" USER="$USER" PATH="$root/bin:/usr/local/bin:/usr/bin" \
        XDG_CONFIG_HOME="$root/home/.config" XDG_DATA_HOME="$root/home/.local/share" \
        XDG_CACHE_HOME="$root/home/.cache" XDG_STATE_HOME="$root/home/.local/state" \
        XDG_DATA_DIRS=/usr/local/share:/usr/share XDG_CONFIG_DIRS=/etc/xdg \
        XDG_RUNTIME_DIR="$root/runtime" M9_TEST_INNER="$root" LANG=C.UTF-8 \
        M9_PREBUILT="$root/prebuilt" XDG_SESSION_TYPE=wayland KDE_FULL_SESSION=true XDG_CURRENT_DESKTOP=KDE \
        KDE_SESSION_VERSION=6 \
        timeout 300 dbus-run-session -- kwin_wayland --virtual --output-count 2 --width 1280 --height 800 \
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
shell_pid() {
    dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetConnectionUnixProcessID \
        string:org.kde.plasmashell 2> /dev/null | awk '/uint32/ { print $2 }'
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
before_files=$(files_state)

check "install exits 0" bash -c "'$project/install.sh' > '$root/install.log' 2>&1"
check "install --apply exits 0" bash -c "'$project/install.sh' --apply > '$root/apply.log' 2>&1"
sleep 6
after_panels=$(panels)
echo "info    after --apply: $after_panels"
check "--apply replaced the panels with the menu bar and the dock" \
    bash -c "[[ '$after_panels' == *':top:20'* && '$after_panels' == *':bottom:52'* && '$after_panels' != *'left'* ]]"
after_files=$(files_state)
if [[ $after_files != "$before_files" ]]; then
    echo "info    the switch changed these config/GTK files (incl. Plasma's GTK sync):"
    diff <(printf '%s\n' "$before_files" | grep -v '^[0-9a-f]\{64\}') <(printf '%s\n' "$after_files" | grep -v '^[0-9a-f]\{64\}') |
        grep '^[<>]' | sed 's/^/          /' | head -20 || true
    diff <(printf '%s\n' "$before_files" | grep '^[0-9a-f]\{64\}') <(printf '%s\n' "$after_files" | grep '^[0-9a-f]\{64\}') |
        grep '^>' | awk '{ print "          changed " $3 }' | head -20 || true
fi

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
check "every config and GTK file is back byte for byte" same "$before_files" "$(files_state)"
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
