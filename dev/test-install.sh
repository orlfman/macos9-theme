#!/bin/bash
# Tests install.sh and uninstall.sh in a throwaway home (dev/build/test-home)
# that starts out as a Breeze setup with its own panel layout, without
# touching your real one:
#   - HOME and every XDG folder point into the throwaway home
#   - a private D-Bus session (dbus-run-session) and its own runtime folder,
#     so nothing reaches your Plasma, KWin or systemd user session
#   - a stand-in systemctl on PATH that only logs what it was asked
# Checks: a dry run changes nothing; install puts every file in place and
# records it; --apply copies the config files once and switches; a second
# --apply keeps the first copies; uninstall puts every config file back
# byte for byte, removes every installed file and the record, and keeps the
# config files it replaced.
#
# usage: test-install.sh        (exit 1 on the first failure)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")

if [[ -z ${M9_TEST_INNER:-} ]]; then
    root=$dev/build/test-home
    rm -rf "$root"
    mkdir -p "$root/home" "$root/runtime" "$root/bin"
    chmod 700 "$root/runtime"
    cat > "$root/bin/systemctl" << EOF
#!/bin/bash
echo "systemctl \$*" >> "$root/systemctl.log"
exit 3
EOF
    chmod +x "$root/bin/systemctl"
    exec env -i HOME="$root/home" USER="$USER" PATH="$root/bin:/usr/local/bin:/usr/bin" \
        XDG_CONFIG_HOME="$root/home/.config" XDG_DATA_HOME="$root/home/.local/share" \
        XDG_CACHE_HOME="$root/home/.cache" XDG_STATE_HOME="$root/home/.local/state" \
        XDG_DATA_DIRS=/usr/local/share:/usr/share XDG_CONFIG_DIRS=/etc/xdg \
        XDG_RUNTIME_DIR="$root/runtime" M9_TEST_INNER="$root" M9_PROJECT_BUILD="$dev/build" LANG=C.UTF-8 \
        QT_QPA_PLATFORM=offscreen \
        dbus-run-session -- bash "$0"
fi

root=$M9_TEST_INNER
home=$HOME
config=$XDG_CONFIG_HOME
failed=0
pass() { printf 'ok      %s\n' "$*"; }
fail() { printf 'FAIL    %s\n' "$*"; failed=1; }
check() { # description command...
    local what=$1
    shift
    if "$@"; then pass "$what"; else fail "$what"; fi
}
snapshot() { # a listing of every file in the home with its checksum
    (cd "$home" && find . -type f -print0 | sort -z | xargs -0 -r sha256sum)
}

# A Breeze user with a panel layout of their own (made-up contents).
mkdir -p "$config"
printf '[KDE]\nwidgetStyle=Breeze\n\n[General]\nColorScheme=BreezeLight\n' > "$config/kdeglobals"
printf '[org.kde.kdecoration2]\nlibrary=org.kde.breeze\ntheme=Breeze\n' > "$config/kwinrc"
printf '[Theme]\nname=default\n' > "$config/plasmarc"
printf '[Containments][1]\nplugin=org.kde.panel\nlocation=4\n# the user'"'"'s own panel\n' > "$config/plasma-org.kde.plasma.desktop-appletsrc"
printf '[PlasmaViews][Panel 1]\nthickness=44\n' > "$config/plasmashellrc"
# (no kcminputrc, ksplashrc or kdedefaults: they must stay absent afterwards)
mkdir -p "$root/seed"
cp -a "$config/." "$root/seed/"

before=$(snapshot)
"$project/install.sh" --dry-run > "$root/dry-run.log" 2>&1
check "install --dry-run changes nothing" test "$before" == "$(snapshot)"
"$project/install.sh" --apply --dry-run > "$root/dry-run-apply.log" 2>&1
check "install --apply --dry-run changes nothing" test "$before" == "$(snapshot)"

"$project/install.sh" > "$root/install.log" 2>&1
state=$home/.local/state/macos9-theme
for f in .local/lib/qt6/plugins/styles/platinumstyle.so .local/lib/qt6/plugins/org.kde.kdecoration3/platinum.so \
    .config/plasma-workspace/env/macos9-theme.sh .local/share/color-schemes/Platinum.colors \
    .local/share/plasma/desktoptheme/platinum/metadata.json .local/share/plasma/plasmoids/platinum.menubarpiece/metadata.json \
    .local/share/plasma/look-and-feel/platinum.desktop/metadata.json; do
    check "installed $f" test -s "$home/$f"
done
check "install records 7 entries" test "$(wc -l < "$state/installed")" -eq 7
check "install alone leaves the config files alone" diff -r "$root/seed" "$config" -x plasma-workspace
check "the login script adds the plugin folder" \
    bash -c "unset QT_PLUGIN_PATH; source '$home/.config/plasma-workspace/env/macos9-theme.sh'; [[ \$QT_PLUGIN_PATH == '$home/.local/lib/qt6/plugins' ]]"
check "the login script doesn't add it twice" \
    bash -c "source '$home/.config/plasma-workspace/env/macos9-theme.sh'; source '$home/.config/plasma-workspace/env/macos9-theme.sh'; [[ \$QT_PLUGIN_PATH == '$home/.local/lib/qt6/plugins' ]]"
# The installed style plugin loads (through dev/styleshot, which prints the
# style it got).
if [[ -x $M9_PROJECT_BUILD/styleshot ]]; then
    check "the installed style plugin loads" bash -c "QT_PLUGIN_PATH='$home/.local/lib/qt6/plugins' QT_STYLE_OVERRIDE=Platinum \
        '$M9_PROJECT_BUILD/styleshot' '$root/styleshot.png' 2> /dev/null | grep -qx 'style platinum'"
else
    echo "skip    the installed style plugin loads (build dev/build/styleshot first: dev/check-style.sh)"
fi

"$project/install.sh" --apply > "$root/apply.log" 2>&1 || true
check "--apply copied the config files" test -f "$state/backup/kdeglobals" -a -f "$state/backup/plasma-org.kde.plasma.desktop-appletsrc"
check "--apply noted the absent ones" grep -qx kdedefaults "$state/backup/ABSENT"
check "--apply switched the global theme" grep -q "LookAndFeelPackage=platinum.desktop" "$config/kdeglobals"
check "--apply wrote kdedefaults" test -f "$config/kdedefaults/kdeglobals"
check "--apply set the widget style" grep -q "widgetStyle=Platinum" "$config/kdedefaults/kdeglobals"
check "--apply set the button order" bash -c "grep -q '^ButtonsOnLeft=X' '$config/kwinrc' && grep -q '^ButtonsOnRight=AI' '$config/kwinrc'"
cp "$state/backup/kwinrc" "$root/first-backup-kwinrc"
"$project/install.sh" --apply > "$root/apply-2.log" 2>&1 || true
check "a second --apply keeps the first copies" cmp -s "$root/first-backup-kwinrc" "$root/seed/kwinrc"

"$project/uninstall.sh" --dry-run > "$root/uninstall-dry.log" 2>&1
check "uninstall --dry-run keeps the record" test -f "$state/installed"

"$project/uninstall.sh" > "$root/uninstall.log" 2>&1
check "uninstall put every config file back" diff -r "$root/seed" "$config"
check "uninstall removed kdedefaults (it wasn't there)" test ! -e "$config/kdedefaults"
check "uninstall removed the plugins" test ! -e "$home/.local/lib/qt6/plugins"
check "uninstall removed the login script" test ! -e "$home/.config/plasma-workspace/env/macos9-theme.sh"
check "uninstall removed the Plasma parts" bash -c "! ls '$home'/.local/share/plasma/*/platinum* > /dev/null 2>&1"
check "uninstall removed the color scheme" test ! -e "$home/.local/share/color-schemes/Platinum.colors"
check "uninstall removed the record" test ! -e "$state"
kept=$(ls -d "$home"/.local/state/macos9-theme-uninstalled-* 2> /dev/null | head -1)
check "uninstall kept the replaced config files" test -n "$kept" -a -f "$kept/kdeglobals"
check "nothing touched a real systemd session" bash -c "! grep -qv 'is-active' '$root/systemctl.log' 2> /dev/null"

if ((failed)); then
    echo "test-install: FAILED (logs in $root)"
    exit 1
fi
echo "test-install: all passed (logs in $root)"
