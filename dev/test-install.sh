#!/bin/bash
# Tests install.sh and uninstall.sh in a throwaway home (dev/build/test-home)
# without touching your real one:
#   - HOME and every XDG folder point into the throwaway home
#   - a private D-Bus session (dbus-run-session) and its own runtime folder,
#     so nothing reaches your Plasma, KWin or systemd user session
#   - a stand-in systemctl on PATH that only logs what it was asked
# Every scenario starts from a fresh home seeded as a Breeze user with a
# panel layout and GTK settings of their own (made-up contents), including
# the cases from AUDIT.md findings 4-14: things already in the way of an
# install target, a linked config folder, a file where install needs a
# folder, an install that fails halfway, a failing theme switch, a switch
# in System Settings instead of --apply, repeats and odd orders; and from
# findings 27-31: a second uninstall after a failed one, Platinum already
# selected, a config folder link pointed elsewhere, files that only look
# like leftovers, another data folder at uninstall time.
# Plasma's shell isn't running here; dev/test-install-live.sh covers that.
#
# usage: test-install.sh        (exit 1 if anything failed)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")

if [[ -z ${M9_TEST_INNER:-} ]]; then
    root=$dev/build/test-home
    rm -rf "$root"
    mkdir -p "$root/home" "$root/runtime" "$root/bin" "$root/prebuilt"
    chmod 700 "$root/runtime"
    cat > "$root/bin/systemctl" << EOF
#!/bin/bash
echo "systemctl \$*" >> "$root/systemctl.log"
exit 3
EOF
    chmod +x "$root/bin/systemctl"
    # Build the plugins once; install.sh copies them (M9_PREBUILT).
    "$project/style/build.sh" "$root/prebuilt/style" > /dev/null
    "$project/decoration/build.sh" "$root/prebuilt/decoration" > /dev/null
    "$project/style/quick/build.sh" "$root/prebuilt/quick" > /dev/null
    exec env -i HOME="$root/home" USER="$USER" PATH="$root/bin:/usr/local/bin:/usr/bin" \
        XDG_CONFIG_HOME="$root/home/.config" XDG_DATA_HOME="$root/home/.local/share" \
        XDG_CACHE_HOME="$root/home/.cache" XDG_STATE_HOME="$root/home/.local/state" \
        XDG_DATA_DIRS=/usr/local/share:/usr/share XDG_CONFIG_DIRS=/etc/xdg \
        XDG_RUNTIME_DIR="$root/runtime" M9_TEST_INNER="$root" M9_PROJECT_BUILD="$dev/build" LANG=C.UTF-8 \
        M9_PREBUILT="$root/prebuilt" M9_USTOPS="${M9_USTOPS:-}" QT_QPA_PLATFORM=offscreen \
        dbus-run-session -- bash "$0"
fi

root=$M9_TEST_INNER
home=$HOME
config=$XDG_CONFIG_HOME
data=$XDG_DATA_HOME
state=$home/.local/state/macos9-theme
failed=0
passed=0
pass() { printf 'ok      %s\n' "$*"; passed=$((passed + 1)); }
fail() { printf 'FAIL    %s\n' "$*"; failed=$((failed + 1)); }
check() { # description command...
    local what=$1
    shift
    if "$@"; then pass "$what"; else fail "$what"; fi
}
# Every file, folder and link in the home with its type, mode, link target
# and checksum (the lock and the logs aside).
snapshot() {
    (cd "$home" && find . -printf '%y %m %p -> %l\n' | sort && find . -type f -print0 | sort -z | xargs -0 -r sha256sum)
}
# The config and GTK files a switch may change, as they were seeded.
config_state() {
    (cd "$home" && find .config .gtkrc-2.0 -path .config/plasma-workspace -prune -o -printf '%y %m %p -> %l\n' | sort &&
        find .config .gtkrc-2.0 -path .config/plasma-workspace -prune -o -type f -print0 | sort -z | xargs -0 -r sha256sum)
}
# Two listings are the same (shows the first differences if not).
same() {
    [[ $1 == "$2" ]] && return 0
    diff <(printf '%s\n' "$1") <(printf '%s\n' "$2") | head -6 | sed 's/^/        /'
    return 1
}
n=0
run() { # name script args... : runs and logs, returns its exit status
    local name=$1
    shift
    n=$((n + 1))
    "$@" > "$root/$n-$name.log" 2>&1
}

# A fresh home: a Breeze user with a panel layout and GTK settings of their
# own.
fresh() { # scenario title
    printf '\n# %s\n' "$1"
    rm -rf "$home"
    mkdir -p "$config/gtk-3.0" "$config/gtk-4.0/assets" "$config/xsettingsd" "$home/.local/state"
    printf '[KDE]\nwidgetStyle=Breeze\nLookAndFeelPackage=org.kde.breeze.desktop\n\n[General]\nColorScheme=BreezeLight\n' > "$config/kdeglobals"
    printf '[org.kde.kdecoration2]\nlibrary=org.kde.breeze\ntheme=Breeze\n' > "$config/kwinrc"
    printf '[Theme]\nname=default\n' > "$config/plasmarc"
    printf '[Containments][1]\nplugin=org.kde.panel\nlocation=4\n# the user'"'"'s own panel\n' > "$config/plasma-org.kde.plasma.desktop-appletsrc"
    printf '[PlasmaViews][Panel 1]\nthickness=44\n' > "$config/plasmashellrc"
    printf '[Settings]\ngtk-theme-name=Breeze\n' > "$config/gtk-3.0/settings.ini"
    printf '/* user css */\n@import url("mine.css");\n' > "$config/gtk-4.0/gtk.css"
    printf 'png' > "$config/gtk-4.0/assets/mine.png"
    printf 'Net/ThemeName "Breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
    printf 'gtk-theme-name="Breeze"\n' > "$home/.gtkrc-2.0"
    # (no kcminputrc, ksplashrc or kdedefaults: they must be absent again
    # after an undo)
    seed=$(config_state)
}

# The changes Plasma's GTK sync makes after a switch (it isn't running here).
fake_gtk_sync() {
    printf '@import "colors.css";\n' > "$config/gtk-4.0/gtk.css"
    printf 'colors' > "$config/gtk-4.0/colors.css"
    printf 'deco' > "$config/gtk-3.0/window_decorations.css"
    printf 'Net/ThemeName "Platinum"\n' > "$config/xsettingsd/xsettingsd.conf"
    printf 'gtk-theme-name="Platinum"\n' > "$home/.gtkrc-2.0"
}

no_record_left() { [[ ! -e $state ]]; }
# The next login: Plasma runs every login script, so the one-shot script
# uninstall.sh leaves runs (it removes the pass-through for the session's
# running apps, finding 49).
next_login() {
    local script
    for script in "$config"/plasma-workspace/env/*.sh; do
        [[ -f $script ]] && sh -c '. "$1"' _ "$script"
    done
    return 0
}
theme_files_gone() {
    next_login
    ! ls -d "$home"/.local/lib/macos9-theme "$data"/plasma/*/platinum* "$data/color-schemes/Platinum.colors" "$data/wallpapers/"platinum-{ribbon,lavender} \
        "$config/plasma-workspace/env/macos9-theme.sh" "$config"/plasma-workspace/env/macos9-theme-cleanup*.sh > /dev/null 2>&1
}
kept_dir() { ls -d "$home"/.local/state/macos9-theme-uninstalled-* 2> /dev/null | tail -1; }
# The home without what uninstall keeps on purpose (its dated folder).
clean_snapshot() {
    next_login
    rm -rf "$home"/.local/state/macos9-theme-uninstalled-*
    snapshot
}

# --------------------------------------------------------------------------
fresh "dry runs, install, apply twice, uninstall"
before=$(snapshot)
run dry "$project/install.sh" --dry-run
check "install --dry-run changes nothing" same "$before" "$(snapshot)"
check "install --dry-run says what it would do" grep -q "would copy your config files" "$root/$n-dry.log"
for id in platinum-ribbon platinum-lavender; do
    check "install --dry-run lists $id" grep -Fq "would install $data/wallpapers/$id/" "$root/$n-dry.log"
done
check "  and prints no errors (finding 42)" bash -c "! grep -qiE 'no such file|error' '$root/$n-dry.log'"
run dry-apply "$project/install.sh" --apply --dry-run
check "install --apply --dry-run changes nothing" same "$before" "$(snapshot)"
check "install --apply --dry-run shows the switch" grep -q "would run plasma-apply-lookandfeel" "$root/$n-dry-apply.log"

check "install exits 0" run install "$project/install.sh"
for f in .local/lib/macos9-theme/style/styles/platinumstyle.so .local/lib/macos9-theme/decoration/org.kde.kdecoration3/platinum.so \
    .config/plasma-workspace/env/macos9-theme.sh .local/share/color-schemes/Platinum.colors \
    .local/share/plasma/desktoptheme/platinum/metadata.json .local/share/plasma/plasmoids/platinum.menubarpiece/metadata.json \
    .local/share/plasma/look-and-feel/platinum.desktop/metadata.json .local/lib/macos9-theme/qml/Platinum/qmldir \
    .local/lib/macos9-theme/qml/Platinum/libplatinumquick.so; do
    check "installed $f" test -s "$home/$f"
done
for id in platinum-ribbon platinum-lavender; do
    check "$id is installed byte for byte" cmp \
        "$project/wallpapers/$id/contents/images/3840x2160.jxl" \
        "$data/wallpapers/$id/contents/images/3840x2160.jxl"
done
check "the record lists the 12 targets" test "$(grep -cE '^(file|dir|link)	' "$state/installed")" -eq 12
check "Kirigami's plugin link for the Qt Quick style points at KDE's" \
    bash -c "[[ \$(readlink '$home/.local/lib/macos9-theme/style/kf6/kirigami/platform/Platinum.so') == */kf6/kirigami/platform/org.kde.desktop.so ]]"
check "install alone leaves the config files alone" same "$seed" "$(config_state)"
check "install already copied the config files (taken: install)" grep -qx install "$state/backup/TAKEN"
plugins=$home/.local/lib/macos9-theme
check "the login script adds both plugin folders" \
    bash -c "unset QT_PLUGIN_PATH; source '$config/plasma-workspace/env/macos9-theme.sh'; [[ \$QT_PLUGIN_PATH == '$plugins/style:$plugins/decoration' ]]"
check "the login script doesn't add them twice" \
    bash -c "QT_PLUGIN_PATH=/x; for i in 1 2; do source '$config/plasma-workspace/env/macos9-theme.sh'; done; [[ \$QT_PLUGIN_PATH == '$plugins/style:$plugins/decoration:/x' ]]"
check "the login script runs in plain sh" sh -c ". '$config/plasma-workspace/env/macos9-theme.sh' && [ -n \"\$QT_PLUGIN_PATH\" ]"
env_script=$config/plasma-workspace/env/macos9-theme.sh
quick_vars() { # runs the login script in sh with the given setup, prints the Qt Quick variables
    env -u QT_QUICK_CONTROLS_STYLE -u QML_IMPORT_PATH "$@" sh -c ". '$env_script'; echo \"style=\${QT_QUICK_CONTROLS_STYLE:-} qml=\${QML_IMPORT_PATH:-}\""
}
check "with Breeze as the widget style, the Qt Quick style stays off" bash -c "[[ \$($(declare -f quick_vars); env_script='$env_script'; quick_vars) == 'style= qml=' ]]"
sed 's|readlink -f \(.[^ ]*libkdecorations3.so[^ ]*\)|readlink -f /nonexistent|' "$config/plasma-workspace/env/macos9-theme.sh" > "$root/env-upgraded.sh"
check "after a KDecoration upgrade it leaves the decoration out" \
    bash -c "unset QT_PLUGIN_PATH; source '$root/env-upgraded.sh'; [[ \$QT_PLUGIN_PATH == '$plugins/style' ]]"
if [[ -x $M9_PROJECT_BUILD/styleshot ]]; then
    check "the installed style plugin loads" bash -c "QT_PLUGIN_PATH='$plugins/style' QT_STYLE_OVERRIDE=Platinum \
        '$M9_PROJECT_BUILD/styleshot' '$root/styleshot.png' 2> /dev/null | grep -qx 'style platinum'"
else
    echo "skip    the installed style plugin loads (build dev/build/styleshot first: dev/check-style.sh)"
fi
check "a second plain install exits 0" run install-2 "$project/install.sh"
check "the record still lists 12 targets, nothing moved aside" \
    bash -c "[[ \$(grep -cE '^(file|dir|link)	' '$state/installed') -eq 12 ]] && ! grep -q '^displaced' '$state/installed'"

check "--apply exits 0" run apply env QT_PLUGIN_PATH="$plugins/style:$plugins/decoration" "$project/install.sh" --apply
check "--apply explains the next login for Qt Quick apps" grep -Fq 'Log out and back in for Qt Quick apps' "$root/$n-apply.log"
check "--apply refreshed the copy (taken: apply)" grep -qx apply "$state/backup/TAKEN"
check "--apply noted the absent ones" grep -qxP 'config\tkdedefaults' "$state/backup/ABSENT"
check "--apply switched the global theme" grep -q "LookAndFeelPackage=platinum.desktop" "$config/kdeglobals"
check "--apply set the widget style" grep -q "widgetStyle=Platinum" "$config/kdedefaults/kdeglobals"
check "--apply set the button order" bash -c "grep -q '^ButtonsOnLeft=X' '$config/kwinrc' && grep -q '^ButtonsOnRight=AI' '$config/kwinrc'"
quick_on="style=Platinum qml=$home/.local/lib/macos9-theme/qml"
check "after --apply the login script turns the Qt Quick style on" \
    bash -c "[[ \$($(declare -f quick_vars); env_script='$env_script'; quick_vars) == '$quick_on' ]]"
check "  once, sourced twice" \
    bash -c "[[ \$(env -u QT_QUICK_CONTROLS_STYLE -u QML_IMPORT_PATH sh -c \". '$env_script'; unset QT_QUICK_CONTROLS_STYLE; . '$env_script'; echo \\\$QML_IMPORT_PATH\") == '$home/.local/lib/macos9-theme/qml' ]]"
check "  but not over a Qt Quick style you chose" \
    bash -c "[[ \$(env QT_QUICK_CONTROLS_STYLE=Fusion sh -c \". '$env_script'; echo \\\$QT_QUICK_CONTROLS_STYLE\") == Fusion ]]"
# (the version the login script expects, changed to one KDE doesn't have)
sed "/kde-qmlmodule.version/s/= '[^']*' \\]/= '0.0.0' ]/" "$env_script" > "$root/env-kde-upgraded.sh"
check "  and not after a KDE Frameworks upgrade (its Qt Quick style changed)" \
    bash -c "grep -q \"= '0.0.0'\" '$root/env-kde-upgraded.sh' && [[ \$(env -u QT_QUICK_CONTROLS_STYLE sh -c \". '$root/env-kde-upgraded.sh'; echo \\\${QT_QUICK_CONTROLS_STYLE:-none}\") == none ]]"
fake_gtk_sync
check "a second --apply exits 0" run apply-2 "$project/install.sh" --apply
check "a plain install after --apply exits 0" run install-3 "$project/install.sh"
check "after all that, the copy still matches the seed" \
    bash -c "diff -r '$state/backup/config/kdeglobals' <(printf '[KDE]\nwidgetStyle=Breeze\nLookAndFeelPackage=org.kde.breeze.desktop\n\n[General]\nColorScheme=BreezeLight\n') > /dev/null &&
        cmp -s '$state/backup/config/gtk-4.0/gtk.css' <(printf '/* user css */\n@import url(\"mine.css\");\n') &&
        grep -qx apply '$state/backup/TAKEN'"

run uninstall-dry "$project/uninstall.sh" --dry-run
check "uninstall --dry-run keeps the record and the copy" test -f "$state/installed" -a -d "$state/backup"
check "uninstall --dry-run shows the restore" grep -q "would put back" "$root/$n-uninstall-dry.log"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "uninstall put every config and GTK file back (incl. absent ones)" same "$seed" "$(config_state)"
check "uninstall left only the pass-through for the session's running apps" \
    bash -c "[[ \$(find '$home/.local/lib' '$config/plasma-workspace' ! -type d | sort | tr '\n' ' ') == '$config/plasma-workspace/env/macos9-theme-cleanup.sh $home/.local/lib/macos9-theme/qml/Platinum/qmldir $home/.local/lib/macos9-theme/style/kf6/kirigami/platform/Platinum.so ' ]]"
next_login
check "uninstall removed the theme's files" theme_files_gone
check "after the next login, the folders it made are gone too" bash -c "[[ ! -e '$home/.local/lib' && ! -e '$config/plasma-workspace' && ! -e '$data/plasma' ]]"
check "uninstall removed the record" no_record_left
kept=$(kept_dir)
check "uninstall kept the replaced files and the copy it put back" \
    test -n "$kept" -a -f "$kept/current/config/kdeglobals" -a -f "$kept/original/config/kdeglobals" -a -f "$kept/current/home/.gtkrc-2.0"
check "a second uninstall exits 0 and does nothing" run uninstall-2 "$project/uninstall.sh"
check "  and leaves no state folder or lock behind" no_record_left
check "nothing touched a real systemd session" bash -c "! grep -qv 'is-active' '$root/systemctl.log' 2> /dev/null"
check "install again after uninstall exits 0" run reinstall "$project/install.sh"
check "and --apply again" run reapply "$project/install.sh" --apply
check "and uninstall again exits 0" run uninstall-3 "$project/uninstall.sh"
check "  and puts the seed back" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "finding 4: things in the way of an install target are kept"
mkdir -p "$data/color-schemes" "$data/plasma/desktoptheme/platinum"
printf 'mine' > "$data/color-schemes/Platinum.colors"
printf 'extra' > "$data/plasma/desktoptheme/platinum/extra.txt"
before=$(snapshot)
check "install exits 0" run install "$project/install.sh"
check "the existing color scheme was moved aside" grep -q "^displaced	$data/color-schemes/Platinum.colors	" "$state/installed"
check "ours is in place" grep -q '^\[General\]' "$data/color-schemes/Platinum.colors"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "uninstall put both earlier ones back, nothing else changed" same "$before" "$(clean_snapshot)"

# --------------------------------------------------------------------------
fresh "finding 6: a linked config entry is refused before any change"
mkdir -p "$root/elsewhere/kdedefaults"
printf '[General]\nColorScheme=MyOriginalScheme\n' > "$root/elsewhere/kdedefaults/kdeglobals"
ln -s "$root/elsewhere/kdedefaults" "$config/kdedefaults"
before=$(snapshot)
check "install refuses (exit 1)" bash -c "! '$project/install.sh' > '$root/link.log' 2>&1"
check "  and says why" grep -q "symbolic link" "$root/link.log"
check "  and changed nothing" same "$before" "$(snapshot)"
check "  the linked folder is untouched" grep -q MyOriginalScheme "$root/elsewhere/kdedefaults/kdeglobals"
rm -rf "$root/elsewhere"

# --------------------------------------------------------------------------
fresh "finding 7: a file where install needs a folder is found first"
mkdir -p "$data"
printf 'not a folder' > "$data/color-schemes"
before=$(snapshot)
check "install refuses (exit 1)" bash -c "! '$project/install.sh' > '$root/parent.log' 2>&1"
check "  and changed nothing" same "$before" "$(snapshot)"

fresh "finding 7: an install that fails halfway can be undone"
mkdir -p "$data/plasma/look-and-feel"
before=$(snapshot)
chmod 555 "$data/plasma/look-and-feel"
check "install fails (exit 1)" bash -c "! '$project/install.sh' > '$root/half.log' 2>&1"
check "  after installing the plugins" test -f "$home/.local/lib/macos9-theme/style/styles/platinumstyle.so"
chmod 755 "$data/plasma/look-and-feel"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and leaves the home as before" same "$before" "$(clean_snapshot)"

fresh "finding 7: an install interrupted at any point can be undone"
before=$(snapshot)
# Stop install.sh after its Nth file operation, for N across the run.
for stop in 1 2 3 5 8 12 16 20 25 30 35 40; do
    M9_STOP_AFTER=$stop bash -c "
        count=0
        mv() { count=\$((count + 1)); command mv \"\$@\"; [[ \$count -lt $stop ]] || kill -INT \$\$; }
        install() { count=\$((count + 1)); command install \"\$@\"; [[ \$count -lt $stop ]] || kill -INT \$\$; }
        export -f mv install 2> /dev/null
        source '$project/install.sh'" > "$root/stop-$stop.log" 2>&1 || true
    "$project/uninstall.sh" > "$root/stop-$stop-uninstall.log" 2>&1 || true
    check "stopped after step $stop, uninstall leaves the home as before" same "$before" "$(clean_snapshot)"
done

# --------------------------------------------------------------------------
fresh "finding 8: switching in System Settings instead of --apply"
check "install exits 0" run install "$project/install.sh"
QT_PLUGIN_PATH=$home/.local/lib/macos9-theme/style plasma-apply-lookandfeel --apply platinum.desktop --resetLayout > "$root/settings-switch.log" 2>&1 || true
check "the switch happened" grep -q "LookAndFeelPackage=platinum.desktop" "$config/kdeglobals"
fake_gtk_sync
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "uninstall put the config back from the install-time copy" same "$seed" "$(config_state)"

fresh "never switched: uninstall leaves later changes alone"
check "install exits 0" run install "$project/install.sh"
printf '[KDE]\nwidgetStyle=Fusion\n' > "$config/kdeglobals"
changed=$(config_state)
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "the user's later change is still there" same "$changed" "$(config_state)"
check "the unused copy is kept" test -f "$(kept_dir)/unused/config/kdeglobals"

# --------------------------------------------------------------------------
fresh "finding 11: a failing theme switch fails the run"
mkdir -p "$root/failbin"
printf '#!/bin/sh\nexit 1\n' > "$root/failbin/plasma-apply-lookandfeel"
chmod +x "$root/failbin/plasma-apply-lookandfeel"
check "install --apply exits 1" bash -c "! PATH='$root/failbin:$PATH' '$project/install.sh' --apply > '$root/fail-apply.log' 2>&1"
check "  without setting the buttons" bash -c "! grep -q ButtonsOnLeft '$config/kwinrc'"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and leaves the config as seeded" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "finding 10: a leftover half-made copy doesn't leak into the next one"
mkdir -p "$state/backup.AAAAAA/config/kdedefaults"
printf 'stale' > "$state/backup.AAAAAA/config/stale"
check "install --apply exits 0" run apply "$project/install.sh" --apply
check "the leftover is gone" test ! -e "$state/backup.AAAAAA"
check "the copy has nothing extra" bash -c "[[ ! -e '$state/backup/config/stale' && ! -e '$state/backup/config/kdedefaults' ]]"
check "a run while another holds the lock is refused" \
    bash -c "exec 9> '$state/lock'; flock 9; ! '$project/install.sh' > '$root/locked.log' 2>&1 && grep -q 'another install.sh' '$root/locked.log'"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and leaves the config as seeded" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "finding 27: running uninstall again never removes what it put back"
mkdir -p "$config/plasma-workspace/env" "$data/color-schemes"
printf 'export MINE=1\n' > "$config/plasma-workspace/env/macos9-theme.sh"
printf 'mine' > "$data/color-schemes/Platinum.colors"
before=$(snapshot)
check "install exits 0" run install "$project/install.sh"
# The user replaces the installed color scheme with a folder of their own.
rm "$data/color-schemes/Platinum.colors"
mkdir "$data/color-schemes/Platinum.colors"
check "uninstall exits 1 (the color scheme's place is taken)" bash -c "! '$project/uninstall.sh' > '$root/27-1.log' 2>&1"
check "  it put the earlier login hook back" grep -qx 'export MINE=1' "$config/plasma-workspace/env/macos9-theme.sh"
check "  the record keeps only what's left (the moved-aside scheme)" \
    bash -c "grep -q '^displaced	$data/color-schemes/Platinum.colors	' '$state/installed' && ! grep -qE '^(file|dir|temp)	' '$state/installed'"
check "  and left the user's folder alone" test -d "$data/color-schemes/Platinum.colors"
check "a second uninstall exits 1 again" bash -c "! '$project/uninstall.sh' > '$root/27-2.log' 2>&1"
check "  and the earlier login hook is still there" grep -qx 'export MINE=1' "$config/plasma-workspace/env/macos9-theme.sh"
rmdir "$data/color-schemes/Platinum.colors"
check "with the way cleared, a third uninstall exits 0" run uninstall-3 "$project/uninstall.sh"
check "  and the home is as before the install" same "$before" "$(clean_snapshot)"

fresh "finding 27: an uninstall stopped at any point is finished by running it again"
mkdir -p "$config/plasma-workspace/env" "$data/color-schemes"
printf 'export MINE=1\n' > "$config/plasma-workspace/env/macos9-theme.sh"
printf 'mine' > "$data/color-schemes/Platinum.colors"
# (the switch writes caches of its own; those aren't compared)
nocache() { clean_snapshot | grep -v '\./\.cache'; }
before=$(nocache)
for stop in ${M9_USTOPS:-1 4 10 20 35 50 65 80 90 96 100 104 108 112 116 119}; do
    "$project/install.sh" --apply > "$root/ustop-$stop-install.log" 2>&1 || true
    fake_gtk_sync
    bash -c "
        count=0
        step() { count=\$((count + 1)); echo \$count > '$root/ustop-$stop.steps'; [[ \$count -lt $stop ]] || kill -INT \$\$; }
        mv() { command mv \"\$@\"; step; }
        rm() { command rm \"\$@\"; step; }
        cp() { command cp \"\$@\"; step; }
        rmdir() { command rmdir \"\$@\"; step; }
        source '$project/uninstall.sh'" > "$root/ustop-$stop.log" 2>&1 || true
    "$project/uninstall.sh" > "$root/ustop-$stop-again.log" 2>&1 || true
    check "stopped after step $stop, a second uninstall leaves the home as before" same "$before" "$(nocache)"
done

# --------------------------------------------------------------------------
fresh "finding 28: Platinum already selected and no copy from before"
printf '[KDE]\nwidgetStyle=Platinum\nLookAndFeelPackage=platinum.desktop\n' > "$config/kdeglobals"
printf '[org.kde.kdecoration2]\nButtonsOnLeft=MS\nButtonsOnRight=HIAX\n' > "$config/kwinrc"
seed=$(config_state)
check "install --apply exits 0" run apply "$project/install.sh" --apply
check "  and warns" grep -q "no copy of your settings from before" "$root/$n-apply.log"
check "  it copied the config first (taken: apply)" grep -qx apply "$state/backup/TAKEN"
check "  --apply set its button order" grep -q '^ButtonsOnRight=AI' "$config/kwinrc"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the user's button order is back" grep -q '^ButtonsOnRight=HIAX' "$config/kwinrc"
check "  every config and GTK file is as before the run" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "finding 29: a config folder link pointed elsewhere since the install"
tree() { (cd "$1" && find . -printf '%y %m %p -> %l\n' | sort && find . -type f -print0 | sort -z | xargs -0 -r sha256sum); }
mv "$config" "$root/profile-a"
ln -s "$root/profile-a" "$config"
a_seed=$(tree "$root/profile-a")
check "install --apply exits 0" run apply "$project/install.sh" --apply
rm -rf "$root/profile-b"
cp -a "$root/profile-a" "$root/profile-b"
ln -sfn "$root/profile-b" "$config"
b_before=$(tree "$root/profile-b")
check "uninstall refuses (exit 1)" bash -c "! '$project/uninstall.sh' > '$root/29.log' 2>&1"
check "  and says why" grep -q "lead somewhere else" "$root/29.log"
check "  the other profile is untouched" same "$b_before" "$(tree "$root/profile-b")"
check "  the record and the copy are kept" test -f "$state/installed" -a -d "$state/backup"
check "install refuses too (exit 1)" bash -c "! '$project/install.sh' > '$root/29-install.log' 2>&1"
check "  and the other profile is still untouched" same "$b_before" "$(tree "$root/profile-b")"
ln -sfn "$root/profile-a" "$config"
check "with the link pointed back, uninstall exits 0" run uninstall "$project/uninstall.sh"
next_login
check "  and the first profile is as seeded" same "$a_seed" "$(tree "$root/profile-a")"
rm -rf "$root/profile-a" "$root/profile-b"

fresh "finding 29: a linked GTK folder pointed elsewhere since the copy"
mv "$config/gtk-4.0" "$root/gtk-a"
ln -s "$root/gtk-a" "$config/gtk-4.0"
a_seed=$(tree "$root/gtk-a")
check "install --apply exits 0" run apply "$project/install.sh" --apply
fake_gtk_sync
rm -rf "$root/gtk-b"
cp -a "$root/gtk-a" "$root/gtk-b"
ln -sfn "$root/gtk-b" "$config/gtk-4.0"
b_before=$(tree "$root/gtk-b")
check "uninstall refuses (exit 1)" bash -c "! '$project/uninstall.sh' > '$root/29-gtk.log' 2>&1"
check "  and says why" grep -q "when your config files were copied" "$root/29-gtk.log"
check "  the other GTK folder is untouched" same "$b_before" "$(tree "$root/gtk-b")"
check "  the copy is kept" test -d "$state/backup"
ln -sfn "$root/gtk-a" "$config/gtk-4.0"
check "with the link pointed back, uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and the first GTK folder is as seeded" same "$a_seed" "$(tree "$root/gtk-a")"
rm -rf "$root/gtk-a" "$root/gtk-b"

# --------------------------------------------------------------------------
fresh "finding 30: files that only look like leftovers are left alone"
mkdir -p "$data/color-schemes" "$data/plasma/look-and-feel/.macos9-theme.XYZ789"
printf 'mine' > "$data/color-schemes/.macos9-theme.abc123"
printf 'mine' > "$data/plasma/look-and-feel/.macos9-theme.XYZ789/file"
before=$(snapshot)
check "install exits 0" run install "$project/install.sh"
check "  they're still there" test -f "$data/color-schemes/.macos9-theme.abc123" -a -f "$data/plasma/look-and-feel/.macos9-theme.XYZ789/file"
check "  no temporary copy is left on the record" bash -c "! grep -q '^temp	' '$state/installed'"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and the home is as before" same "$before" "$(clean_snapshot)"

# --------------------------------------------------------------------------
fresh "finding 31: another data folder at uninstall time is refused"
check "install exits 0" run install "$project/install.sh"
before=$(snapshot)
check "uninstall with another XDG_DATA_HOME refuses (exit 1)" \
    bash -c "! XDG_DATA_HOME='$root/other-data' '$project/uninstall.sh' > '$root/31.log' 2>&1"
check "  and says how to run it" grep -qF "XDG_DATA_HOME=$data" "$root/31.log"
check "  and changed nothing" same "$before" "$(snapshot)"
check "install with another XDG_CONFIG_HOME refuses too" \
    bash -c "! XDG_CONFIG_HOME='$root/other-config' '$project/install.sh' > '$root/31-install.log' 2>&1"
check "with the same folders, uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and removed everything" bash -c "$(declare -f next_login theme_files_gone no_record_left); home='$home' data='$data' config='$config' state='$state'; theme_files_gone && no_record_left"
rm -rf "$root/other-data" "$root/other-config"

# --------------------------------------------------------------------------
fresh "finding 34: a link inside a copied folder is refused before any change"
mkdir -p "$config/kdedefaults" "$root/dotfiles"
printf '[General]\nColorScheme=Custom\n' > "$root/dotfiles/kdeglobals"
ln -s "$root/dotfiles/kdeglobals" "$config/kdedefaults/kdeglobals"
before=$(snapshot)
check "install --apply refuses (exit 1)" bash -c "! '$project/install.sh' --apply > '$root/34.log' 2>&1"
check "  and names the link" grep -qF "$config/kdedefaults/kdeglobals" "$root/34.log"
check "  and changed nothing" same "$before" "$(snapshot)"
check "  the linked dotfile is untouched" grep -qx 'ColorScheme=Custom' "$root/dotfiles/kdeglobals"
rm -rf "$root/dotfiles"

# --------------------------------------------------------------------------
fresh "finding 35: files the user added to or changed in installed things stay"
check "install exits 0" run install "$project/install.sh"
printf 'mine' > "$data/plasma/desktoptheme/platinum/my-variant.svg"
printf '\n' >> "$data/plasma/look-and-feel/platinum.desktop/metadata.json"
edited=$(sha256sum < "$data/plasma/look-and-feel/platinum.desktop/metadata.json")
printf '# my own Platinum\n' > "$data/color-schemes/Platinum.colors"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the added file is still there" grep -qx mine "$data/plasma/desktoptheme/platinum/my-variant.svg"
check "  the changed file is still there, as changed" bash -c "[[ \$(sha256sum < '$data/plasma/look-and-feel/platinum.desktop/metadata.json') == '$edited' ]]"
check "  the replaced color scheme is still the user's" grep -qx '# my own Platinum' "$data/color-schemes/Platinum.colors"
check "  the installed files around them are gone" \
    bash -c "[[ ! -e '$data/plasma/desktoptheme/platinum/metadata.json' && ! -e '$data/plasma/plasmoids' && \$(ls '$data/plasma/desktoptheme/platinum') == my-variant.svg ]]"
check "  and it said what it kept" grep -q "kept" "$root/$n-uninstall.log"
check "  no record left" no_record_left

fresh "finding 35: installing again keeps a changed installed file"
before=$(snapshot)
check "install exits 0" run install "$project/install.sh"
printf '# my own Platinum\n' > "$data/color-schemes/Platinum.colors"
check "a second install exits 0" run install-2 "$project/install.sh"
check "  ours is in place again" grep -q '^\[General\]' "$data/color-schemes/Platinum.colors"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the user's version is back" grep -qx '# my own Platinum' "$data/color-schemes/Platinum.colors"
# (its folders stay with it; without them the rest is as before)
rm -r "$data/color-schemes"
rmdir "$data" "$home/.local/share" 2> /dev/null || true
check "  and the rest is as before" same "$before" "$(clean_snapshot)"

# --------------------------------------------------------------------------
fresh "finding 36: an incomplete or changed copy is refused before any change"
check "install --apply exits 0" run apply "$project/install.sh" --apply
fake_gtk_sync
mv "$state/backup/config/kwinrc" "$root/kwinrc.saved"
before=$(snapshot)
check "uninstall with a file missing from the copy refuses (exit 1)" bash -c "! '$project/uninstall.sh' > '$root/36-1.log' 2>&1"
check "  and names it" grep -q "kwinrc" "$root/36-1.log"
check "  and changed nothing" same "$before" "$(snapshot)"
printf 'changed' > "$state/backup/config/kwinrc"
before=$(snapshot)
check "uninstall with a changed file in the copy refuses (exit 1)" bash -c "! '$project/uninstall.sh' > '$root/36-2.log' 2>&1"
check "  and changed nothing" same "$before" "$(snapshot)"
mv -f "$root/kwinrc.saved" "$state/backup/config/kwinrc"
cp "$state/backup/SUMS" "$root/SUMS.saved"
grep -v 'config/kwinrc$' "$root/SUMS.saved" > "$state/backup/SUMS"
before=$(snapshot)
check "uninstall with a cut-short checksum list refuses (exit 1)" bash -c "! '$project/uninstall.sh' > '$root/36-3.log' 2>&1"
check "  and names the unlisted file" grep -q "kwinrc isn't on the checksum list" "$root/36-3.log"
check "  and changed nothing" same "$before" "$(snapshot)"
cp "$root/SUMS.saved" "$state/backup/SUMS"
check "with the copy whole again, uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and puts the seed back" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "finding 37: a dry run tells what the real uninstall does"
mkdir -p "$data/color-schemes"
printf 'mine' > "$data/color-schemes/Platinum.colors"
check "install exits 0" run install "$project/install.sh"
run uninstall-dry "$project/uninstall.sh" --dry-run || true
check "  the dry run says it would put the earlier one back" grep -q "would put back the earlier $data/color-schemes/Platinum.colors" "$root/$n-uninstall-dry.log"
check "  and warns about nothing" bash -c "! grep -q warning '$root/$n-uninstall-dry.log'"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and put it back" grep -qx mine "$data/color-schemes/Platinum.colors"

# --------------------------------------------------------------------------
fresh "finding 38: a shell that couldn't be started again is started by the next run"
mkdir -p "$root/sdbin"
rm -f "$root/sd.log" "$root/sd.active" "$root/sd.fail"
cat > "$root/sdbin/systemctl" << EOF
#!/bin/bash
# A user systemd with a plasmashell service; starts fail while sd.fail exists.
echo "systemctl \$*" >> '$root/sd.log'
case "\$*" in
    *is-active*) [[ -f '$root/sd.active' ]] ;;
    *stop*) rm -f '$root/sd.active' ;;
    *start*) [[ ! -f '$root/sd.fail' ]] && touch '$root/sd.active' ;;
    *) exit 1 ;;
esac
EOF
chmod +x "$root/sdbin/systemctl"
check "install --apply exits 0" run apply "$project/install.sh" --apply
touch "$root/sd.active" "$root/sd.fail"
check "uninstall exits 1 (the shell won't start)" bash -c "! PATH='$root/sdbin:$PATH' '$project/uninstall.sh' > '$root/38-1.log' 2>&1"
check "  and says so" grep -q "couldn't start Plasma's shell" "$root/38-1.log"
check "  the config was put back" same "$seed" "$(config_state)"
rm -f "$root/sd.fail"
: > "$root/sd.log"
check "uninstall again exits 0" bash -c "PATH='$root/sdbin:$PATH' '$project/uninstall.sh' > '$root/38-2.log' 2>&1"
check "  and started the shell" bash -c "grep -q 'start plasma-plasmashell' '$root/sd.log' && test -f '$root/sd.active'"
check "  no record left" no_record_left

# --------------------------------------------------------------------------
fresh "finding 39: two earlier versions of the same file are both kept"
mkdir -p "$data/color-schemes"
printf 'first\n' > "$data/color-schemes/Platinum.colors"
check "install exits 0" run install "$project/install.sh"
printf 'second\n' > "$data/color-schemes/Platinum.colors"
check "a second install exits 0" run install-2 "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the one from before the install is back in place" grep -qx first "$data/color-schemes/Platinum.colors"
check "  the later one is kept in the dated folder" \
    bash -c "grep -rlx second '$(dirname "$state")'/macos9-theme-uninstalled-*/ 2> /dev/null | grep -q Platinum.colors"
check "  and uninstall says where" grep -q "later version" "$root/$n-uninstall.log"

# --------------------------------------------------------------------------
fresh "finding 40: a file missing inside a copied folder is found"
mkdir -p "$config/kdedefaults"
printf 'x=1\n' > "$config/kdedefaults/custom-settings"
check "install --apply exits 0" run apply "$project/install.sh" --apply
rm "$state/backup/config/kdedefaults/custom-settings"
before=$(snapshot)
check "uninstall refuses (exit 1)" bash -c "! '$project/uninstall.sh' > '$root/40.log' 2>&1"
check "  and names the missing file" grep -q "kdedefaults/custom-settings is missing" "$root/40.log"
check "  and changed nothing" same "$before" "$(snapshot)"
mv "$state/backup" "$root/backup-moved-away"
check "with the copy moved away (as the message says), uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and removed the theme" theme_files_gone
rm -rf "$root/backup-moved-away"

# --------------------------------------------------------------------------
fresh "finding 41: an empty folder the user added to an installed one stays"
check "install exits 0" run install "$project/install.sh"
mkdir "$data/plasma/desktoptheme/platinum/user-templates"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the folder is still there" test -d "$data/plasma/desktoptheme/platinum/user-templates"
rm -rf "$data"
check "install again exits 0" run install-2 "$project/install.sh"
mkdir "$data/plasma/desktoptheme/platinum/user-templates"
check "a reinstall exits 0" run install-3 "$project/install.sh"
check "  it moved the changed folder aside" grep -q "^displaced	$data/plasma/desktoptheme/platinum	" "$state/installed"
check "uninstall exits 0" run uninstall-2 "$project/uninstall.sh"
check "  the folder is back" test -d "$data/plasma/desktoptheme/platinum/user-templates"

# --------------------------------------------------------------------------
fresh "Kirigami's plugin link: what's there before is kept, a changed link stays"
link=$home/.local/lib/macos9-theme/style/kf6/kirigami/platform/Platinum.so
mkdir -p "$(dirname "$link")"
ln -s /nonexistent/mine.so "$link"
before=$(snapshot)
check "install exits 0" run install "$project/install.sh"
check "  the earlier link was moved aside" grep -q "^displaced	$link	" "$state/installed"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the earlier link is back, nothing else changed" same "$before" "$(clean_snapshot)"
rm -f "$link"
rm -rf "$home/.local/lib"
check "install again exits 0" run install-2 "$project/install.sh"
ln -sfn /nonexistent/other.so "$link"
check "uninstall exits 0" run uninstall-2 "$project/uninstall.sh"
check "  a link pointed elsewhere since is left alone" bash -c "[[ \$(readlink '$link') == /nonexistent/other.so ]]"
check "  and uninstall says so" grep -q "points somewhere else now" "$root/$n-uninstall-2.log"

# --------------------------------------------------------------------------
fresh "finding 50: a profile where none of the copied files existed"
rm -rf "$config" "$home/.gtkrc-2.0"
mkdir -p "$config"
check "install --apply exits 0" run apply "$project/install.sh" --apply
check "  the copy lists no files (all absent)" bash -c "[[ ! -s '$state/backup/SUMS' ]] && [[ -z \$(find '$state/backup/config' '$state/backup/home' -type f 2> /dev/null) ]]"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and removed what the switch wrote" bash -c "[[ ! -e '$config/kdeglobals' && ! -e '$config/kwinrc' && ! -e '$config/kdedefaults' ]]"

# --------------------------------------------------------------------------
fresh "finding 49: apps started from the old session still start after uninstall"
check "install --apply exits 0" run apply "$project/install.sh" --apply
# The session's environment, as the login script made it.
session_env=$(env -u QT_QUICK_CONTROLS_STYLE -u QML_IMPORT_PATH sh -c ". '$config/plasma-workspace/env/macos9-theme.sh'; echo \"QT_QUICK_CONTROLS_STYLE=\$QT_QUICK_CONTROLS_STYLE QML_IMPORT_PATH=\$QML_IMPORT_PATH QT_PLUGIN_PATH=\$QT_PLUGIN_PATH\"")
check "  the session names the Platinum Qt Quick style" bash -c "[[ '$session_env' == QT_QUICK_CONTROLS_STYLE=Platinum* ]]"
cat > "$root/probe.qml" << 'QML'
import QtQuick
import QtQuick.Controls as QQC2
QQC2.ApplicationWindow { width: 100; height: 60; visible: false; QQC2.Button { text: "x" } }
QML
probe() { # prints the Qt Quick style a new app gets with the session's environment, or "failed"
    env $session_env QT_FORCE_STDERR_LOGGING=1 DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent timeout 20 "$M9_PROJECT_BUILD/quickshot" "$root/probe.qml" "$root/probe.png" > "$root/probe.log" 2>&1 || { echo failed; return; }
    sed -n 's/^QtQuick style: "\(.*\)"$/\1/p' "$root/probe.log"
}
if [[ -x $M9_PROJECT_BUILD/quickshot ]]; then
    check "  an app started from it gets Platinum" bash -c "[[ \$($(declare -f probe); session_env='$session_env' root='$root' M9_PROJECT_BUILD='$M9_PROJECT_BUILD'; probe) == Platinum ]]"
fi
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and says what it left for the session" grep -q "Left a pass-through" "$root/$n-uninstall.log"
if [[ -x $M9_PROJECT_BUILD/quickshot ]]; then
    check "  an app started from the old session's environment still starts" \
        bash -c "[[ \$($(declare -f probe); session_env='$session_env' root='$root' M9_PROJECT_BUILD='$M9_PROJECT_BUILD'; probe) != failed ]]"
fi
check "install again before logging out exits 0" run install-2 "$project/install.sh"
check "  it took the pass-through's place (nothing moved aside)" bash -c "! grep -q '^displaced' '$state/installed' && [[ ! -e '$config/plasma-workspace/env/macos9-theme-cleanup.sh' ]]"
run uninstall-dry "$project/uninstall.sh" --dry-run || true
check "  a dry run says it would leave the pass-through (finding 58)" grep -q "would leave a pass-through" "$root/$n-uninstall-dry.log"
check "uninstall exits 0" run uninstall-2 "$project/uninstall.sh"
next_login
check "after the next login, nothing of the theme is left" bash -c "[[ ! -e '$home/.local/lib' && ! -e '$config/plasma-workspace' ]]"
check "  and the config is as seeded" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "finding 54: a login script of the user's at the pass-through script's name stays"
mkdir -p "$config/plasma-workspace/env"
printf '# mine\nexport MINE=1\n' > "$config/plasma-workspace/env/macos9-theme-cleanup.sh"
check "install exits 0" run install "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the user's script is untouched" grep -qx 'export MINE=1' "$config/plasma-workspace/env/macos9-theme-cleanup.sh"
check "  the pass-through's script took another name" test -f "$config/plasma-workspace/env/macos9-theme-cleanup-2.sh"
next_login
check "  after the next login the user's script is still there" grep -qx 'export MINE=1' "$config/plasma-workspace/env/macos9-theme-cleanup.sh"
check "  and the pass-through is gone" bash -c "[[ ! -e '$home/.local/lib' && ! -e '$config/plasma-workspace/env/macos9-theme-cleanup-2.sh' ]]"

# --------------------------------------------------------------------------
fresh "finding 55: a Kirigami link of the user's survives the next login"
link=$home/.local/lib/macos9-theme/style/kf6/kirigami/platform/Platinum.so
mkdir -p "$(dirname "$link")"
ln -s "$(readlink "$(ls -d /usr/lib/qt6/plugins/kf6/kirigami/platform/org.kde.desktop.so)" 2> /dev/null || echo /usr/lib/qt6/plugins/kf6/kirigami/platform/org.kde.desktop.so)" "$link"
target=$(readlink "$link")
check "install exits 0" run install "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the user's link is back" bash -c "[[ \$(readlink '$link') == '$target' ]]"
next_login
check "  and still there after the next login" bash -c "[[ \$(readlink '$link') == '$target' ]]"

# --------------------------------------------------------------------------
fresh "finding 56: something of the user's at the Qt Quick module's place stays as it was"
module=$home/.local/lib/macos9-theme/qml/Platinum
mkdir -p "$(dirname "$module")"
printf 'mine' > "$module"
check "install exits 0" run install "$project/install.sh"
check "uninstall exits 0 (a file there)" run uninstall "$project/uninstall.sh"
check "  it explains when Qt Quick apps may need a new login" grep -Fq 'may need you to log out' "$root/$n-uninstall.log"
check "  the user's file is back, nothing added" bash -c "[[ -f '$module' && \$(cat '$module') == mine ]]"
check "  a second uninstall exits 0 too" run uninstall-2 "$project/uninstall.sh"
rm -f "$module"
mkdir -p "$module"
printf 'mine' > "$module/notes.txt"
check "install exits 0" run install-2 "$project/install.sh"
check "uninstall exits 0 (a folder there)" run uninstall-3 "$project/uninstall.sh"
check "  the user's folder is back with nothing added" bash -c "[[ \$(ls -A '$module') == notes.txt ]]"
next_login
check "  and still so after the next login" bash -c "[[ \$(ls -A '$module') == notes.txt ]]"

# The installed folder was moved away before uninstall. The dry run must
# still reserve its place for the original folder when it simulates restore.
check "install the theme again" run install-again "$project/install.sh"
mv "$module" "$root/moved-quick-module"
check "uninstall dry run exits 0" run preview "$project/uninstall.sh" --dry-run
if grep -q 'would leave a pass-through' "$root/$n-preview.log"; then
    fail "the preview reserves the vacant path for the original folder"
else
    pass "the preview reserves the vacant path for the original folder"
fi
check "uninstall exits 0" run restore "$project/uninstall.sh"
check "  the original folder occupies the path" grep -Fxq mine "$module/notes.txt"

# --------------------------------------------------------------------------
fresh "finding 57: a backslash in a copied file's name"
mkdir -p "$config/gtk-3.0/assets"
printf 'svg' > "$config/gtk-3.0/assets/custom\\blue.svg"
seed=$(config_state)
check "install --apply exits 0" run apply "$project/install.sh" --apply
check "  the checksum list escapes its name" grep -q '^\\' "$state/backup/SUMS"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and puts the seed back" same "$seed" "$(config_state)"

# --------------------------------------------------------------------------
fresh "a reinstall preserves personal copies of the one-shot login script"
check "install exits 0" run install "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
hook=$config/plasma-workspace/env/macos9-theme-cleanup.sh
cp "$hook" "${hook%.sh}-saved.sh"
cp "$hook" "${hook%.sh}-2.sh"
check "reinstall exits 0" run reinstall "$project/install.sh"
check "  both personal copies survive under their own names" \
    cmp "${hook%.sh}-saved.sh" "${hook%.sh}-2.sh"
check "  the original cleanup hook was retired" test ! -e "$hook"

fresh "a login preserves edits and replacements in the temporary Qt Quick module"
check "install exits 0" run install "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
module=$home/.local/lib/macos9-theme/qml/Platinum
printf '# my extra settings\n' >> "$module/qmldir"
next_login
check "  the edited qmldir survives the next login" grep -Fxq '# my extra settings' "$module/qmldir"
check "install over the edited file exits 0" run reinstall "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  and restores my edited qmldir" grep -Fxq '# my extra settings' "$module/qmldir"

fresh "a personal edit to the generated login hook survives login and reinstall"
check "install exits 0" run install "$project/install.sh"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
hook=$config/plasma-workspace/env/macos9-theme-cleanup.sh
printf '# local note\n' >> "$hook"
cp "$hook" "$root/edited-hook"
next_login
check "  login preserves the edited hook" cmp "$root/edited-hook" "$hook"
check "reinstall exits 0" run reinstall "$project/install.sh"
check "  reinstall preserves the edited hook" cmp "$root/edited-hook" "$hook"

# Interrupt each of the last two publications, then rerun the real uninstaller.
for operation in ln mv; do
    fresh "uninstall can retry a failed $operation while leaving the temporary Qt Quick module"
    check "install exits 0" run install "$project/install.sh"
    module=$home/.local/lib/macos9-theme/qml/Platinum
    target=$module
    [[ $operation != ln ]] || target=$home/.local/lib/macos9-theme/style/kf6/kirigami/platform/Platinum.so
    bin=$root/fail-publish-$operation
    mkdir -p "$bin"
    cat > "$bin/$operation" <<'STUB'
#!/bin/bash
[[ ${!#} != "$M9_TEST_TARGET" ]] || exit 1
exec "/usr/bin/${0##*/}" "$@"
STUB
    chmod +x "$bin/$operation"
    if run interrupted env PATH="$bin:$PATH" M9_TEST_TARGET="$target" "$project/uninstall.sh"; then
        fail "uninstall reports the failed publication"
    else
        pass "uninstall reports the failed publication"
    fi
    check "  no partial module is visible" test ! -e "$module"
    check "retry exits 0" run retry "$project/uninstall.sh"
    check "  the session's module is complete" grep -Fxq 'import org.kde.desktop 1.0' "$module/qmldir"
    next_login
    check "  login removes the temporary library folders" test ! -e "$home/.local/lib"
    check "  login removes the temporary login folder" test ! -e "$config/plasma-workspace"
done

fresh "a backup filename ending in a line break restores byte for byte"
mkdir -p "$config/gtk-3.0/assets"
asset=$config/gtk-3.0/assets/$'blue\n'
printf 'original' > "$asset"
check "install --apply exits 0" run apply "$project/install.sh" --apply
printf 'changed' > "$asset"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the original file and name are restored" grep -Fxq original "$asset"

fresh "a home with spaces and quotes in its path"
weird="$root/my 'odd' \$home"
rm -rf "$weird"
mkdir -p "$weird"
odd() { env -u XDG_CONFIG_HOME -u XDG_DATA_HOME -u XDG_STATE_HOME -u XDG_CACHE_HOME HOME="$weird" "$@"; }
check "install exits 0" bash -c "$(declare -f odd); weird=\$1; odd '$project/install.sh' > '$root/weird.log' 2>&1" _ "$weird"
check "  the login script adds the odd path" bash -c "unset QT_PLUGIN_PATH; source \"\$1/.config/plasma-workspace/env/macos9-theme.sh\"; [[ \$QT_PLUGIN_PATH == \"\$1/.local/lib/macos9-theme/style:\$1/.local/lib/macos9-theme/decoration\" ]]" _ "$weird"
check "uninstall exits 0" bash -c "$(declare -f odd); weird=\$1; odd '$project/uninstall.sh' > '$root/weird-un.log' 2>&1" _ "$weird"
check "  and removed everything it installed (after the next login)" bash -c "[[ -f \"\$1/.config/plasma-workspace/env/macos9-theme-cleanup.sh\" ]] && sh -c '. \"\$1\"' _ \"\$1/.config/plasma-workspace/env/macos9-theme-cleanup.sh\" &&
    [[ -z \$(find \"\$1\" -path '*/macos9-theme-uninstalled-*' -prune -o -type f -print) ]]" _ "$weird"
rm -rf "$weird"

fresh "wallpaper selected in a saved Plasma config (finding 75)"
check "picker-only install exits 0" run install "$project/install.sh"
cat >> "$config/plasma-org.kde.plasma.desktop-appletsrc" << EOF
[Containments][9]
wallpaperplugin=org.kde.image
[Containments][9][Wallpaper][org.kde.image][General]
Image=file://$data/wallpapers/platinum%2Dlavender/contents/images/3840x2160.jxl
EOF
before=$(config_state)
if run undo "$project/uninstall.sh"; then
    fail "uninstall defers the selected wallpaper"
else
    check "uninstall defers the selected wallpaper" grep -q 'is still selected in Plasma' "$root/$n-undo.log"
fi
check "the selected package stays in place" test -s "$data/wallpapers/platinum-lavender/contents/images/3840x2160.jxl"
check "the unselected package is removed" test ! -e "$data/wallpapers/platinum-ribbon"
check "the saved desktop config stays byte for byte" same "$before" "$(config_state)"
sed -i 's/wallpaperplugin=org.kde.image/wallpaperplugin=org.kde.color/' "$config/plasma-org.kde.plasma.desktop-appletsrc"
check "uninstall finishes after changing the wallpaper plugin" run retry "$project/uninstall.sh"
check "neither wallpaper package remains" theme_files_gone

fresh "Qt without a JPEG XL decoder (finding 76)"
mkdir -p "$root/no-jxl/bin" "$root/no-jxl/plugins"
cat > "$root/no-jxl/bin/g++" << 'SH'
#!/bin/bash
set -euo pipefail
/usr/bin/g++ "$@"
while (($# > 1)); do
    if [[ $1 == -o && $2 == */check-wallpaper ]]; then
        printf '[Paths]\nPlugins=%s\n' "$M9_TEST_INNER/no-jxl/plugins" > "${2%/*}/qt.conf"
        break
    fi
    shift
done
SH
chmod +x "$root/no-jxl/bin/g++"
check "theme apply still exits 0" run apply env -u QT_PLUGIN_PATH PATH="$root/no-jxl/bin:$PATH" "$project/install.sh" --apply
check "apply warns about the missing JPEG XL decoder before switching" awk '
    /Qt can.t read the JPEG XL wallpapers/ { warning = NR }
    /Switched to the Platinum global theme/ { switched = NR }
    END { exit !(warning && warning < switched) }
' "$root/$n-apply.log"
check "uninstall exits 0" run undo "$project/uninstall.sh"

fresh "the cursors: installed with the theme, selected by the switch, removed again"
cursors=$data/icons/macOS-cursors
check "install exits 0" run install "$project/install.sh"
check "  the cursor theme is installed" test -f "$cursors/index.theme"
check "  its pointer is a whole cursor file" bash -c "source <(sed -n '/^xcursor_ok() {/,/^}/p' '$project/scripts/common.sh'); xcursor_ok '$cursors/cursors/left_ptr'"
check "  its links are kept as links" bash -c "[[ \$(find '$cursors' -type l | wc -l) -gt 100 && -L '$cursors/cursors/x-cursor' ]]"
check "--apply exits 0" run apply "$project/install.sh" --apply
check "  the global theme selects macOS-cursors" grep -qx 'cursorTheme=macOS-cursors' "$config/kdedefaults/kcminputrc"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the cursor theme is gone" test ! -e "$cursors"
check "  and the config is as seeded" same "$seed" "$(config_state)"

echo
if ((failed)); then
    echo "test-install: $failed FAILED, $passed passed (logs in $root)"
    exit 1
fi
echo "test-install: all $passed passed (logs in $root)"
