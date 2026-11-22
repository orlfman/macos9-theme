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
theme_files_gone() {
    ! ls -d "$home"/.local/lib/macos9-theme "$data"/plasma/*/platinum* "$data/color-schemes/Platinum.colors" \
        "$config/plasma-workspace/env/macos9-theme.sh" > /dev/null 2>&1
}
kept_dir() { ls -d "$home"/.local/state/macos9-theme-uninstalled-* 2> /dev/null | tail -1; }
# The home without what uninstall keeps on purpose (its dated folder).
clean_snapshot() {
    rm -rf "$home"/.local/state/macos9-theme-uninstalled-*
    snapshot
}

# --------------------------------------------------------------------------
fresh "dry runs, install, apply twice, uninstall"
before=$(snapshot)
run dry "$project/install.sh" --dry-run
check "install --dry-run changes nothing" same "$before" "$(snapshot)"
check "install --dry-run says what it would do" grep -q "would copy your config files" "$root/$n-dry.log"
check "  and prints no errors (finding 42)" bash -c "! grep -qiE 'no such file|error' '$root/$n-dry.log'"
run dry-apply "$project/install.sh" --apply --dry-run
check "install --apply --dry-run changes nothing" same "$before" "$(snapshot)"
check "install --apply --dry-run shows the switch" grep -q "would run plasma-apply-lookandfeel" "$root/$n-dry-apply.log"

check "install exits 0" run install "$project/install.sh"
for f in .local/lib/macos9-theme/style/styles/platinumstyle.so .local/lib/macos9-theme/decoration/org.kde.kdecoration3/platinum.so \
    .config/plasma-workspace/env/macos9-theme.sh .local/share/color-schemes/Platinum.colors \
    .local/share/plasma/desktoptheme/platinum/metadata.json .local/share/plasma/plasmoids/platinum.menubarpiece/metadata.json \
    .local/share/plasma/look-and-feel/platinum.desktop/metadata.json; do
    check "installed $f" test -s "$home/$f"
done
check "the record lists the 7 targets" test "$(grep -cE '^(file|dir)	' "$state/installed")" -eq 7
check "install alone leaves the config files alone" same "$seed" "$(config_state)"
check "install already copied the config files (taken: install)" grep -qx install "$state/backup/TAKEN"
plugins=$home/.local/lib/macos9-theme
check "the login script adds both plugin folders" \
    bash -c "unset QT_PLUGIN_PATH; source '$config/plasma-workspace/env/macos9-theme.sh'; [[ \$QT_PLUGIN_PATH == '$plugins/style:$plugins/decoration' ]]"
check "the login script doesn't add them twice" \
    bash -c "QT_PLUGIN_PATH=/x; for i in 1 2; do source '$config/plasma-workspace/env/macos9-theme.sh'; done; [[ \$QT_PLUGIN_PATH == '$plugins/style:$plugins/decoration:/x' ]]"
check "the login script runs in plain sh" sh -c ". '$config/plasma-workspace/env/macos9-theme.sh' && [ -n \"\$QT_PLUGIN_PATH\" ]"
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
check "the record still lists 7 targets, nothing moved aside" \
    bash -c "[[ \$(grep -cE '^(file|dir)	' '$state/installed') -eq 7 ]] && ! grep -q '^displaced' '$state/installed'"

check "--apply exits 0" run apply "$project/install.sh" --apply
check "--apply refreshed the copy (taken: apply)" grep -qx apply "$state/backup/TAKEN"
check "--apply noted the absent ones" grep -qxP 'config\tkdedefaults' "$state/backup/ABSENT"
check "--apply switched the global theme" grep -q "LookAndFeelPackage=platinum.desktop" "$config/kdeglobals"
check "--apply set the widget style" grep -q "widgetStyle=Platinum" "$config/kdedefaults/kdeglobals"
check "--apply set the button order" bash -c "grep -q '^ButtonsOnLeft=X' '$config/kwinrc' && grep -q '^ButtonsOnRight=AI' '$config/kwinrc'"
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
check "uninstall removed the theme's files" theme_files_gone
check "uninstall removed the folders it made" bash -c "[[ ! -e '$home/.local/lib' && ! -e '$config/plasma-workspace' && ! -e '$data/plasma' ]]"
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
check "  and removed everything" bash -c "$(declare -f theme_files_gone no_record_left); home='$home' data='$data' config='$config' state='$state'; theme_files_gone && no_record_left"
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
    bash -c "[[ ! -e '$data/plasma/desktoptheme/platinum/metadata.json' && ! -e '$data/plasma/plasmoids' && ! -e '$home/.local/lib' && \$(ls '$data/plasma/desktoptheme/platinum') == my-variant.svg ]]"
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

fresh "a home with spaces and quotes in its path"
weird="$root/my 'odd' \$home"
rm -rf "$weird"
mkdir -p "$weird"
odd() { env -u XDG_CONFIG_HOME -u XDG_DATA_HOME -u XDG_STATE_HOME -u XDG_CACHE_HOME HOME="$weird" "$@"; }
check "install exits 0" bash -c "$(declare -f odd); weird=\$1; odd '$project/install.sh' > '$root/weird.log' 2>&1" _ "$weird"
check "  the login script adds the odd path" bash -c "unset QT_PLUGIN_PATH; source \"\$1/.config/plasma-workspace/env/macos9-theme.sh\"; [[ \$QT_PLUGIN_PATH == \"\$1/.local/lib/macos9-theme/style:\$1/.local/lib/macos9-theme/decoration\" ]]" _ "$weird"
check "uninstall exits 0" bash -c "$(declare -f odd); weird=\$1; odd '$project/uninstall.sh' > '$root/weird-un.log' 2>&1" _ "$weird"
check "  and removed everything it installed" bash -c "[[ -z \$(find \"\$1\" -path '*/macos9-theme-uninstalled-*' -prune -o -type f -print) ]]" _ "$weird"
rm -rf "$weird"

echo
if ((failed)); then
    echo "test-install: $failed FAILED, $passed passed (logs in $root)"
    exit 1
fi
echo "test-install: all $passed passed (logs in $root)"
