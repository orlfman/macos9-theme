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
umask 022
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
    # Build the C++ plugins and one real-size WhiteSur Lavender trio once, plus
    # a tiny 3-theme fixture (for fast general scenarios) and a local bare git
    # remote (for offline/auto-fetch tests with zero real network access).
    "$project/style/build.sh" "$root/prebuilt/style" > /dev/null
    "$project/decoration/build.sh" "$root/prebuilt/decoration" > /dev/null
    "$project/style/quick/build.sh" "$root/prebuilt/quick" > /dev/null
    upstream_src="${M9_WHITESUR_UPSTREAM:-$(dirname "$project")/WhiteSur-icon-theme}"
    mkdir -p "$root/prebuilt-real/icons" "$root/prebuilt/icons"
    "$project/icons/build-whitesur-lavender.sh" "$upstream_src" "$root/prebuilt-real/icons" > /dev/null
    rm -f "$root/prebuilt-real/icons"/WhiteSur-lavender{,-light,-dark}/.macos9-whitesur-lavender-build
    cp -R "$root/prebuilt/style" "$root/prebuilt/decoration" "$root/prebuilt/quick" "$root/prebuilt-real/"
    # Build tiny valid 3-theme icon fixture mirroring WhiteSur Lavender's symlink structure (~18 entries).
    python3 -I - "$root/prebuilt-real/icons" "$root/prebuilt/icons" << 'PYEND'
import shutil, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
for tid in ("WhiteSur-lavender", "WhiteSur-lavender-light", "WhiteSur-lavender-dark"):
    (dst / tid).mkdir(parents=True, exist_ok=True)
    for meta in ("index.theme", "COPYING", "AUTHORS", "LAVENDER-NOTICE.txt"):
        shutil.copy2(src / tid / meta, dst / tid / meta)
base = dst / "WhiteSur-lavender"
(base / "places/scalable").mkdir(parents=True)
(base / "status/32").mkdir(parents=True)
shutil.copy2(src / "WhiteSur-lavender/places/scalable/folder.svg", base / "places/scalable/folder.svg")
shutil.copy2(src / "WhiteSur-lavender/status/32/start-here.svg", base / "status/32/start-here.svg")
(base / "places@2x").symlink_to("places")
light = dst / "WhiteSur-lavender-light"
(light / "status/32").mkdir(parents=True)
shutil.copy2(src / "WhiteSur-lavender-light/status/32/start-here.svg", light / "status/32/start-here.svg")
(light / "places").symlink_to("../WhiteSur-lavender/places")
dark = dst / "WhiteSur-lavender-dark"
(dark / "places/scalable").mkdir(parents=True)
(dark / "status").mkdir(parents=True)
shutil.copy2(src / "WhiteSur-lavender-dark/places/scalable/folder.svg", dark / "places/scalable/folder.svg")
(dark / "status/32").symlink_to("../../WhiteSur-lavender/status/32")
PYEND
    # Local bare remote for automatic-fetch tests (zero network access).
    git clone --bare --quiet "$upstream_src" "$root/local-remote.git"
    git -C "$root/local-remote.git" config uploadpack.allowAnySHA1InWant true
    exec env -i HOME="$root/home" USER="$USER" PATH="$root/bin:/usr/local/bin:/usr/bin" \
        XDG_CONFIG_HOME="$root/home/.config" XDG_DATA_HOME="$root/home/.local/share" \
        XDG_CACHE_HOME="$root/home/.cache" XDG_STATE_HOME="$root/home/.local/state" \
        XDG_DATA_DIRS=/usr/local/share:/usr/share XDG_CONFIG_DIRS="$root/home/.config/kdedefaults:/etc/xdg" \
        XDG_RUNTIME_DIR="$root/runtime" M9_TEST_INNER="$root" M9_PROJECT_BUILD="$dev/build" LANG=C.UTF-8 \
        M9_PREBUILT="$root/prebuilt" M9_PREBUILT_REAL="$root/prebuilt-real" \
        M9_TEST_REMOTE="file://$root/local-remote.git" M9_USTOPS="${M9_USTOPS:-}" QT_QPA_PLATFORM=offscreen \
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
    # kded rewrites these files but keeps the widget-theme name (docs/FINDINGS.md).
    printf 'Net/ThemeName "Breeze"\nNet/CursorBlink 1\n' > "$config/xsettingsd/xsettingsd.conf"
    printf 'gtk-theme-name="Breeze"\ngtk-cursor-blink=1\n' > "$home/.gtkrc-2.0"
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
icons_absent() {
    local d=${1:-$data} id
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        [[ ! -e $d/icons/$id && ! -L $d/icons/$id ]] || return 1
    done
    return 0
}
theme_files_gone() {
    next_login
    local p
    shopt -s nullglob
    for p in "$home/.local/lib/macos9-theme" "$data"/plasma/*/platinum* "$data/color-schemes/Platinum.colors" "$data/konsole/PlatinumLavender.colorscheme" \
        "$data/wallpapers/platinum-ribbon" "$data/wallpapers/platinum-lavender" "$data/wallpapers/platinum-waves" "$data/wallpapers/platinum-glass" "$data/wallpapers/platinum-nebula" "$data/wallpapers/platinum-finder-waves" "$data/wallpapers/platinum-ripples" \
        "$data/icons/WhiteSur-lavender" "$data/icons/WhiteSur-lavender-light" "$data/icons/WhiteSur-lavender-dark" \
        "$config/plasma-workspace/env/macos9-theme.sh" "$config"/plasma-workspace/env/macos9-theme-cleanup*.sh; do
        if [[ -e $p || -L $p ]]; then
            shopt -u nullglob
            return 1
        fi
    done
    shopt -u nullglob
    return 0
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
terminal_palette=$data/konsole/PlatinumLavender.colorscheme
printf '[Appearance]\nColorScheme=konsole:Vapor.colorscheme\n' > "$config/kwiterminalrc"
seed=$(config_state)
before=$(snapshot)
run dry "$project/install.sh" --dry-run
check "install --dry-run changes nothing" same "$before" "$(snapshot)"
check "install --dry-run says what it would do" grep -q "would copy your config files" "$root/$n-dry.log"
for id in platinum-ribbon platinum-lavender platinum-waves platinum-glass platinum-nebula platinum-finder-waves platinum-ripples; do
    check "install --dry-run lists $id" grep -Fq "would install $data/wallpapers/$id/" "$root/$n-dry.log"
done
check "install --dry-run lists the terminal palette" grep -Fq "would install $terminal_palette" "$root/$n-dry.log"
check "  and prints no errors (finding 42)" bash -c "! grep -qiE 'no such file|error' '$root/$n-dry.log'"
run dry-apply "$project/install.sh" --apply --dry-run
check "install --apply --dry-run changes nothing" same "$before" "$(snapshot)"
check "install --apply --dry-run shows the switch" grep -q "would run plasma-apply-lookandfeel" "$root/$n-dry-apply.log"

check "install exits 0" run install "$project/install.sh"
for f in .local/lib/macos9-theme/style/styles/platinumstyle.so .local/lib/macos9-theme/decoration/org.kde.kdecoration3/platinum.so \
    .local/share/themes/Platinum/{index.theme,gtk-3.0/palette.css,gtk-3.0/gtk.css,gtk-4.0/palette.css,gtk-4.0/gtk.css} \
    .config/plasma-workspace/env/macos9-theme.sh .local/share/color-schemes/Platinum.colors \
    .local/share/plasma/desktoptheme/platinum/metadata.json .local/share/plasma/plasmoids/platinum.menubarpiece/metadata.json .local/share/plasma/plasmoids/platinum.trash/metadata.json \
    .local/share/plasma/plasmoids/platinum.trash/contents/ui/main.qml \
    .local/share/plasma/look-and-feel/platinum.desktop/metadata.json .local/lib/macos9-theme/qml/Platinum/qmldir \
    .local/lib/macos9-theme/qml/Platinum/libplatinumquick.so; do
    check "installed $f" test -s "$home/$f"
done
for id in platinum-ribbon platinum-lavender platinum-waves platinum-glass platinum-nebula platinum-finder-waves platinum-ripples; do
    check "$id is installed byte for byte" cmp \
        "$project/wallpapers/$id/contents/images/3840x2160.jxl" \
        "$data/wallpapers/$id/contents/images/3840x2160.jxl"
done
check "all GTK 3 artwork is installed" diff -qr "$project/gtk/Platinum/gtk-3.0/assets" "$data/themes/Platinum/gtk-3.0/assets"
check "all GTK 4 artwork is installed" diff -qr --exclude=gtk3 "$project/gtk/Platinum/gtk-4.0/assets" "$data/themes/Platinum/gtk-4.0/assets"
# GTK 4 carries its own copy of the GTK 3 artwork and palette it uses.
check "the installed GTK 4 theme stands alone" python3 -I -c '
import re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
for css in root.glob("*.css"):
    for url in re.findall(r"url\(\"([^\"]+)\"\)", css.read_text()):
        if url.startswith("resource://"):
            continue
        path = (root / url).resolve()
        assert path.is_relative_to(root) and path.is_file() and path.stat().st_size, url
' "$data/themes/Platinum/gtk-4.0"
check "the Kwi and Konsole palette is installed byte for byte" cmp \
    "$project/extras/terminal/PlatinumLavender.colorscheme" "$terminal_palette"
check "the record lists the 25 targets" test "$(grep -cE '^(file|dir|link)	' "$state/installed")" -eq 25
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
check "the record still lists 25 targets, nothing moved aside" \
    bash -c "[[ \$(grep -cE '^(file|dir|link)	' '$state/installed') -eq 25 ]] && ! grep -q '^displaced' '$state/installed'"

check "--apply exits 0" run apply env QT_PLUGIN_PATH="$plugins/style:$plugins/decoration" "$project/install.sh" --apply
check "--apply explains the next login for Qt Quick apps" grep -Fq 'Log out and back in for Qt Quick apps' "$root/$n-apply.log"
check "--apply refreshed the copy (taken: apply)" grep -qx apply "$state/backup/TAKEN"
check "--apply noted the absent ones" grep -qxP 'config\tkdedefaults' "$state/backup/ABSENT"
check "--apply preserves the chosen Kwi color scheme" grep -qx 'ColorScheme=konsole:Vapor.colorscheme' "$config/kwiterminalrc"
check "--apply switched the global theme" grep -q "LookAndFeelPackage=platinum.desktop" "$config/kdeglobals"
check "--apply set the widget style" grep -q "widgetStyle=Platinum" "$config/kdedefaults/kdeglobals"
check "--apply set the button order" bash -c "grep -q '^ButtonsOnLeft=X' '$config/kwinrc' && grep -q '^ButtonsOnRight=AI' '$config/kwinrc'"
cp "$config/gtk-4.0/gtk.css" "$root/adw-after-apply.css" # evidence
adw_mark='/* macos9-theme: Platinum for libadwaita apps (install.sh adds this, uninstall.sh removes it) */'
adw_line="@import url(\"file://$data/themes/Platinum/gtk-4.0/libadwaita.css\");"
check "--apply puts the libadwaita import first in gtk-4.0/gtk.css (decision 15)" \
    bash -c "[[ \$(head -2 '$config/gtk-4.0/gtk.css') == \"\$(printf '%s\n%s' '$adw_mark' '$adw_line')\" ]]"
check "  and keeps the user's own rules" grep -Fqx '@import url("mine.css");' "$config/gtk-4.0/gtk.css"
check "  and the imported layer is installed" test -s "$data/themes/Platinum/gtk-4.0/libadwaita.css"
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
check "  which puts the import back after the GTK sync rewrote the file, once" test "$(grep -cF "$adw_mark" "$config/gtk-4.0/gtk.css")" -eq 1
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
check "  which takes the libadwaita import out" bash -c "! grep -qF 'macos9-theme: Platinum for libadwaita' '$config/gtk-4.0/gtk.css'"
check "uninstall left only the pass-through for the session's running apps" \
    bash -c "[[ \$(find '$home/.local/lib' '$config/plasma-workspace' ! -type d | sort | tr '\n' ' ') == '$config/plasma-workspace/env/macos9-theme-cleanup.sh $home/.local/lib/macos9-theme/qml/Platinum/qmldir $home/.local/lib/macos9-theme/style/kf6/kirigami/platform/Platinum.so ' ]]"
next_login
check "uninstall removed the theme's files" theme_files_gone
check "uninstall removed the GTK theme and its empty parent" test ! -e "$data/themes"
check "uninstall removed the empty terminal palette directory" test ! -e "$data/konsole"
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
mkdir -p "$data/color-schemes" "$data/plasma/desktoptheme/platinum" "$data/konsole"
printf 'mine' > "$data/color-schemes/Platinum.colors"
printf '[General]\nDescription=My Platinum Lavender\n' > "$terminal_palette"
mkdir -p "$data/themes/Platinum"
printf 'original theme' > "$data/themes/Platinum/original"
printf 'extra' > "$data/plasma/desktoptheme/platinum/extra.txt"
before=$(snapshot)
check "install exits 0" run install "$project/install.sh"
check "the existing terminal palette was moved aside" grep -Fq $'displaced\t'"$terminal_palette"$'\t' "$state/installed"
check "the existing color scheme was moved aside" grep -q "^displaced	$data/color-schemes/Platinum.colors	" "$state/installed"
check "ours is in place" grep -q '^\[General\]' "$data/color-schemes/Platinum.colors"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "uninstall put the earlier files back, nothing else changed" same "$before" "$(clean_snapshot)"

# --------------------------------------------------------------------------
fresh "GTK selection and another theme's resources under the same name"
gtk_theme=$data/themes/Platinum
mkdir -p "$gtk_theme/gtk-4.0"
printf 'existing GTK 4 rules' > "$gtk_theme/gtk-4.0/gtk.css"
printf 'existing shared colors' > "$gtk_theme/palette.css"
printf 'existing metadata' > "$gtk_theme/index.theme"
check "install GTK 3 and GTK 4 over another theme's GTK 4 folder" run gtk-install "$project/install.sh"
check "reinstall GTK 3 and GTK 4" run gtk-update "$project/install.sh"
check "installed GTK 3 palette matches the source" cmp "$project/gtk/Platinum/palette.css" "$gtk_theme/gtk-3.0/palette.css"
check "installed GTK 4 palette matches the source" cmp "$project/gtk/Platinum/palette.css" "$gtk_theme/gtk-4.0/palette.css"
check "the other GTK 4 folder is set aside while installed" grep -q 'Platinum GTK 4 theme' "$gtk_theme/gtk-4.0/gtk.css"
check "existing palette still available" grep -qx 'existing shared colors' "$gtk_theme/palette.css"
check "existing metadata still available" grep -qx 'existing metadata' "$gtk_theme/index.theme"
printf '[Settings]\ngtk-theme-name=Platinum\n' > "$config/gtk-3.0/settings.ini"
check "preview selected GTK theme removal" run gtk-preview "$project/uninstall.sh" --dry-run
check "preview explains selected GTK theme" grep -Fq 'Keeping the Platinum GTK theme' "$root/$n-gtk-preview.log"
check "uninstall defers removal while GTK selects Platinum" bash -c '! "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/gtk-selected.log"
check "selected GTK 3 artwork stays installed" test -s "$gtk_theme/gtk-3.0/gtk.css"
# The other theme's GTK 4 folder is restored at once: the name stays usable.
check "the other theme's GTK 4 folder is back" grep -qx 'existing GTK 4 rules' "$gtk_theme/gtk-4.0/gtk.css"
printf '[Settings]\ngtk-theme-name=Adwaita\n' > "$config/gtk-3.0/settings.ini"
check "retry removes GTK 3" run gtk-retry "$project/uninstall.sh"
check "GTK 3 is gone" test ! -e "$gtk_theme/gtk-3.0"
check "the other theme's GTK 4 folder stays" grep -qx 'existing GTK 4 rules' "$gtk_theme/gtk-4.0/gtk.css"

fresh "a GTK 4 selection keeps both toolkits"
gtk_theme=$data/themes/Platinum
check "install GTK 3 and GTK 4" run gtk4-install "$project/install.sh"
printf '[Settings]\ngtk-theme-name=Platinum\n' > "$config/gtk-4.0/settings.ini"
check "uninstall defers removal while GTK 4 selects Platinum" bash -c '! "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/gtk4-selected.log"
check "  and says so" grep -Fq 'Keeping the Platinum GTK theme' "$root/gtk4-selected.log"
check "  GTK 3 stays installed" test -s "$gtk_theme/gtk-3.0/gtk.css"
check "  GTK 4 stays installed" grep -q 'Platinum GTK 4 theme' "$gtk_theme/gtk-4.0/gtk.css"
check "  and still stands alone" test -s "$gtk_theme/gtk-4.0/assets/gtk3/push-disabled.png"
rm "$config/gtk-4.0/settings.ini"
check "retry removes both" run gtk4-retry "$project/uninstall.sh"
check "the GTK theme is gone" test ! -e "$gtk_theme"

fresh "libadwaita import (decision 15)"
check "plain install while another theme is active" run adw-install "$project/install.sh"
check "  adds no libadwaita import" bash -c "! grep -qF 'macos9-theme: Platinum for libadwaita' '$config/gtk-4.0/gtk.css'"
sed -i 's/^LookAndFeelPackage=.*/LookAndFeelPackage=platinum.desktop/' "$config/kdeglobals"
check "plain reinstall while Platinum is active (switched in System Settings)" run adw-reinstall "$project/install.sh"
check "  adds the import" grep -qF 'macos9-theme: Platinum for libadwaita' "$config/gtk-4.0/gtk.css"
check "  and says so" grep -Fq 'libadwaita apps use Platinum' "$root/$n-adw-reinstall.log"
check "  without asking for --apply again" bash -c 'grep -Fq "Platinum is already your global theme" "$1" && ! grep -Fq "then run install.sh --apply" "$1"' _ "$root/$n-adw-reinstall.log"
check "a third reinstall leaves gtk.css alone" bash -c 'a=$(sha256sum < "$1"); "$2" > "$3" 2>&1 && [[ $a == $(sha256sum < "$1") ]] && ! grep -q "libadwaita apps use" "$3"' \
    _ "$config/gtk-4.0/gtk.css" "$project/install.sh" "$root/adw-reinstall-2.log"
check "uninstall exits 0" run adw-undo "$project/uninstall.sh"
check "  the import is gone" bash -c "! grep -qF 'macos9-theme: Platinum for libadwaita' '$config/gtk-4.0/gtk.css'"
check "  the user's rules are still there" grep -Fqx '@import url("mine.css");' "$config/gtk-4.0/gtk.css"

fresh "libadwaita import never writes through a linked gtk.css"
mv "$config/gtk-4.0/gtk.css" "$home/linked-gtk.css"
ln -s "$home/linked-gtk.css" "$config/gtk-4.0/gtk.css"
linked_before=$(sha256sum < "$home/linked-gtk.css")
check "install --apply refuses the linked config file" bash -c '! "$1" --apply > "$2" 2>&1 && grep -Fq "is a symbolic link" "$2"' \
    _ "$project/install.sh" "$root/adw-link-apply.log"
check "  the linked file is unchanged" test "$linked_before" == "$(sha256sum < "$home/linked-gtk.css")"
check "uninstall exits 0" run adw-link-undo "$project/uninstall.sh"
check "  the linked file is still unchanged" test "$linked_before" == "$(sha256sum < "$home/linked-gtk.css")"

fresh "libadwaita import helper edge cases (#254, #255, #258)"
adw_dir=$root/adw-helper
mkdir -p "$adw_dir"
printf 'victim\n' > "$adw_dir/victim.txt"
printf '/* u */\n' > "$adw_dir/gtk.css"
chmod 600 "$adw_dir/gtk.css"
ln -s "$adw_dir/victim.txt" "$adw_dir/.gtk.css.macos9-theme.tmp"
check "a planted temp-file link isn't written through (#254)" bash -c '
    out=$(python3 -I "$1" adw-import add "$2/gtk.css" /t/gtk-4.0/libadwaita.css) && [[ $out == added ]] &&
    [[ $(cat "$2/victim.txt") == victim && ! -L $2/gtk.css && $(stat -c %a "$2/gtk.css") == 600 ]]' _ "$project/scripts/gtk_theme.py" "$adw_dir"
check "a non-ASCII path is UTF-8 percent-encoded (#255)" bash -c '
    printf "" > "$2/u.css" && python3 -I "$1" adw-import add "$2/u.css" "/home/my—theme b/gtk-4.0/libadwaita.css" > /dev/null &&
    grep -Fq "file:///home/my%E2%80%94theme%20b/gtk-4.0/libadwaita.css" "$2/u.css"' _ "$project/scripts/gtk_theme.py" "$adw_dir"
check "removing our lines from a file that held nothing else removes the file (#258)" bash -c '
    [[ $(python3 -I "$1" adw-import remove "$2/u.css") == removed && ! -e $2/u.css ]]' _ "$project/scripts/gtk_theme.py" "$adw_dir"

fresh "#249: a GTK theme chosen after the switch survives undo"
check "install --apply" run gtk249-apply "$project/install.sh" --apply
fake_gtk_sync
printf '[Settings]\ngtk-theme-name=Adwaita\n' > "$config/gtk-3.0/settings.ini"
check "uninstall exits 0" run gtk249-undo "$project/uninstall.sh"
check "  the later GTK 3 choice is kept" grep -qx 'gtk-theme-name=Adwaita' "$config/gtk-3.0/settings.ini"
check "  the GTK 2 and XSettings files are put back" bash -c 'grep -qx "gtk-theme-name=\"Breeze\"" "$1/.gtkrc-2.0" && grep -qx "Net/ThemeName \"Breeze\"" "$2/xsettingsd/xsettingsd.conf" && ! grep -q Blink "$1/.gtkrc-2.0"' _ "$home" "$config"
check "  and the rest of the config is put back" same "$(printf '[KDE]\nwidgetStyle=Breeze\nLookAndFeelPackage=org.kde.breeze.desktop\n\n[General]\nColorScheme=BreezeLight\n')" "$(cat "$config/kdeglobals")"
check "  the GTK theme is removed" test ! -e "$data/themes/Platinum"

fresh "#249: Platinum chosen for GTK 4 after the switch is kept with the theme"
check "install --apply" run gtk249p-apply "$project/install.sh" --apply
fake_gtk_sync
printf '[Settings]\ngtk-theme-name=Platinum\n' > "$config/gtk-4.0/settings.ini"
check "preview exits 0" run gtk249p-preview "$project/uninstall.sh" --dry-run
check "  says it keeps the later choice" grep -Fq 'would keep your later GTK theme choice "Platinum" in gtk-4.0/settings.ini' "$root/$n-gtk249p-preview.log"
check "  and the theme" grep -Fq 'Keeping the Platinum GTK theme' "$root/$n-gtk249p-preview.log"
check "uninstall defers the GTK theme" bash -c '! "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/gtk249p-undo.log"
check "  the later choice is still there" grep -qx 'gtk-theme-name=Platinum' "$config/gtk-4.0/settings.ini"
check "  GTK 3 and GTK 4 stay installed" bash -c 'test -s "$1/gtk-3.0/gtk.css" && grep -q "Platinum GTK 4 theme" "$1/gtk-4.0/gtk.css"' _ "$data/themes/Platinum"
check "  the rest of the config is put back" grep -qx 'gtk-theme-name=Breeze' "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-theme-name=Adwaita\n' > "$config/gtk-4.0/settings.ini"
check "retry removes the theme" run gtk249p-retry "$project/uninstall.sh"
check "  and keeps the new choice" grep -qx 'gtk-theme-name=Adwaita' "$config/gtk-4.0/settings.ini"
check "  the GTK theme is gone" test ! -e "$data/themes/Platinum"

fresh "#251: a GTK theme key removed after the switch stays removed"
printf '[Settings]\ngtk-theme-name=Platinum\n' > "$config/gtk-4.0/settings.ini"
check "install --apply" run gtk251-apply "$project/install.sh" --apply
fake_gtk_sync
printf '[Settings]\n' > "$config/gtk-4.0/settings.ini"
check "preview says the key stays removed" bash -c '"$1" --dry-run > "$2" 2>&1; grep -Fq "keep the GTK theme setting you removed from gtk-4.0/settings.ini removed" "$2"' _ "$project/uninstall.sh" "$root/gtk251-preview.log"
check "uninstall exits 0" run gtk251-undo "$project/uninstall.sh"
check "  the key is still gone" bash -c '! grep -q gtk-theme-name "$1"' _ "$config/gtk-4.0/settings.ini"
check "  the GTK theme is removed" test ! -e "$data/themes/Platinum"

fresh "#251: the GTK sync filling in a missing key is not a choice"
check "install --apply" run gtk251s-apply "$project/install.sh" --apply
fake_gtk_sync
# (like kded: the name the other files already hold, in a file that wasn't there)
printf '[Settings]\ngtk-theme-name=Breeze\n' > "$config/gtk-4.0/settings.ini"
check "uninstall exits 0" run gtk251s-undo "$project/uninstall.sh"
check "  every config and GTK file is put back" same "$seed" "$(config_state)"

fresh "#252: an undo stopped before the GTK choice is written back keeps it"
check "install --apply" run gtk252-apply "$project/install.sh" --apply
fake_gtk_sync
printf '[Settings]\ngtk-theme-name=Platinum\n' > "$config/gtk-4.0/settings.ini"
bash -c "
    python3() { if [[ \${3:-} == carry ]]; then kill -INT \$\$; exit 130; fi; command python3 \"\$@\"; }
    source '$project/uninstall.sh'" > "$root/gtk252-stopped.log" 2>&1 || true
check "the stopped undo had put the config back" grep -qx 'LookAndFeelPackage=org.kde.breeze.desktop' "$config/kdeglobals"
check "  and saved the choice" grep -q 'Platinum' "$state/gtk-later-choices"
check "running it again keeps the theme" bash -c '! "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/gtk252-again.log"
check "  with the later choice" grep -qx 'gtk-theme-name=Platinum' "$config/gtk-4.0/settings.ini"
check "  and both toolkits" bash -c 'test -s "$1/gtk-3.0/gtk.css" && grep -q "Platinum GTK 4 theme" "$1/gtk-4.0/gtk.css"' _ "$data/themes/Platinum"
check "  the saved list is gone once used" test ! -e "$state/gtk-later-choices"
rm "$config/gtk-4.0/settings.ini"
check "retry after switching away removes the theme" run gtk252-retry "$project/uninstall.sh"
check "  the GTK theme is gone" test ! -e "$data/themes/Platinum"

fresh "#250: an exported GTK_THEME keeps the theme"
check "install" run gtk250-install "$project/install.sh"
check "uninstall with GTK_THEME=Platinum:dark defers" bash -c '! env GTK_THEME=Platinum:dark "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/gtk250-undo.log"
check "  and names the variable" grep -Fq 'GTK_THEME=Platinum:dark' "$root/gtk250-undo.log"
check "  GTK 3 and GTK 4 stay installed" bash -c 'test -s "$1/gtk-3.0/gtk.css" && test -s "$1/gtk-4.0/gtk.css"' _ "$data/themes/Platinum"
check "another theme in GTK_THEME does not" run gtk250-other env GTK_THEME=Adwaita "$project/uninstall.sh"
check "  the GTK theme is gone" test ! -e "$data/themes/Platinum"

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
printf '[General]\nDescription=My edited terminal palette\n' > "$terminal_palette"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the added file is still there" grep -qx mine "$data/plasma/desktoptheme/platinum/my-variant.svg"
check "  the changed file is still there, as changed" bash -c "[[ \$(sha256sum < '$data/plasma/look-and-feel/platinum.desktop/metadata.json') == '$edited' ]]"
check "  the edited terminal palette is still the user's" grep -qx 'Description=My edited terminal palette' "$terminal_palette"
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
check "with the copy moved away, uninstall stops with the active cursors and icons kept" bash -c '! "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/40-without-backup.log"
check "  it removed the other theme files" bash -c '
    next_login() { for s in "$1"/plasma-workspace/env/*.sh; do [ -f "$s" ] && sh -c ". \"\$1\"" _ "$s"; done; }
    next_login "$2"
    shopt -s nullglob
    for p in "$3/.local/lib/macos9-theme" "$4"/plasma/*/platinum* "$4/color-schemes/Platinum.colors" \
        "$4/wallpapers/platinum-ribbon" "$4/wallpapers/platinum-lavender" "$4/wallpapers/platinum-waves" "$4/wallpapers/platinum-glass" "$4/wallpapers/platinum-nebula" "$4/wallpapers/platinum-finder-waves" "$4/wallpapers/platinum-ripples" \
        "$4/icons/WhiteSur-lavender-light" "$4/icons/WhiteSur-lavender-dark" \
        "$2/plasma-workspace/env/macos9-theme.sh" "$2"/plasma-workspace/env/macos9-theme-cleanup*.sh; do
        [[ ! -e $p && ! -L $p ]] || exit 1
    done
' _ "$config" "$config" "$home" "$data"
check "  the active cursors remain" test -f "$data/icons/macOS-cursors/cursors/left_ptr"
check "  the active WhiteSur-lavender icon theme remains" test -f "$data/icons/WhiteSur-lavender/index.theme"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme Breeze
kwriteconfig6 --file kdeglobals --group Icons --key Theme breeze
check "  retry after changing the cursor and icons exits 0" run retry "$project/uninstall.sh"
check "  it removes the cursor package" test ! -e "$data/icons/macOS-cursors"
check "  it removes WhiteSur-lavender" test ! -e "$data/icons/WhiteSur-lavender"
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
check "  its links are kept as links" bash -c "[[ \$(find '$cursors' -type l | wc -l) -gt 100 && -L '$cursors/cursors/x-cursor' ]]"
check "  Plasma lists the black theme after login" env -u XCURSOR_PATH sh -c '
    . "$1"
    plasma-apply-cursortheme --list-themes | grep -E "[[]macOS-cursors[]]$"
' _ "$config/plasma-workspace/env/macos9-theme.sh"
check "  the login script preserves a custom cursor path without duplicates" sh -c '
    XCURSOR_PATH=/custom/cursors:/usr/share/icons
    . "$1"
    . "$1"
    [ "$XCURSOR_PATH" = "$2/icons:/custom/cursors:/usr/share/icons" ]
' _ "$config/plasma-workspace/env/macos9-theme.sh" "$data"
check "--apply exits 0" run apply "$project/install.sh" --apply
check "  the global theme selects macOS-cursors" grep -qx 'cursorTheme=macOS-cursors' "$config/kdedefaults/kcminputrc"
check "uninstall dry run exits 0" run preview "$project/uninstall.sh" --dry-run
check "  the preview removes the cursor pack after restoring the settings" grep -Fq "would remove $cursors" "$root/$n-preview.log"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the cursor theme is gone" test ! -e "$cursors"
check "  and the config is as seeded" same "$seed" "$(config_state)"

fresh "a standalone cursor selection survives uninstall"
check "install exits 0" run install "$project/install.sh"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme macOS-cursors
before=$(snapshot)
check "uninstall dry run exits 0" run preview "$project/uninstall.sh" --dry-run
check "  the preview says the cursors are selected" grep -Fq 'macOS-cursors is still selected' "$root/$n-preview.log"
check "  the preview changes nothing" same "$before" "$(snapshot)"
check "uninstall reports the selected pack still needs removal" bash -c '! "$1" > "$2" 2>&1' _ "$project/uninstall.sh" "$root/cursor-selected.log"
check "  the installed pointer and its aliases remain" test -e "$cursors/cursors/x-cursor"
check "  the separate cursor preference remains" grep -qx 'cursorTheme=macOS-cursors' "$config/kcminputrc"
check "  the other parts of Platinum were removed" test ! -d "$data/plasma/look-and-feel/platinum.desktop"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme Breeze
check "uninstall retry exits 0 after changing cursors" run retry "$project/uninstall.sh"
check "  the cursor theme is now gone" test ! -e "$cursors"
check "  the changed cursor preference remains" grep -qx 'cursorTheme=Breeze' "$config/kcminputrc"

fresh "a previously installed cursor pack with the same ID is restored"
mkdir -p "$data/icons"
tar -xJf "$project/cursors/macOS-cursors.tar.xz" -C "$data/icons" macOS-cursors
printf '\n# an earlier installation\n' >> "$cursors/index.theme"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme macOS-cursors
check "install exits 0" run install "$project/install.sh"
check "  the bundled pack was installed" bash -c '! grep -Fq "an earlier installation" "$1"' _ "$cursors/index.theme"
check "uninstall exits 0" run undo "$project/uninstall.sh"
check "  the earlier pack is restored" grep -Fq 'an earlier installation' "$cursors/index.theme"
check "  the earlier pack is still selected" grep -qx 'cursorTheme=macOS-cursors' "$config/kcminputrc"

fresh "an edited symbolic link in the cursor pack belongs to the user"
check "install exits 0" run install "$project/install.sh"
alias_file=$cursors/cursors/x-cursor
ln -sfn -- "$(readlink -- "$alias_file")"$'\n' "$alias_file"
check "uninstall exits 0" run uninstall "$project/uninstall.sh"
check "  the edited link stays, including the line break" bash -c '
    target=$(readlink -n -- "$1" && printf .) &&
    [[ $target == *$'"'"'\n'"'"'. ]]
' _ "$alias_file"
check "  the unchanged pointer is gone" test ! -e "$cursors/cursors/left_ptr"

fresh "a corrupt cursor archive is rejected before any writes"
fixture=$root/bad-cursor-project
mkdir -p "$fixture/cursors"
cp "$project/install.sh" "$fixture/install.sh"
for component in scripts wallpapers colors plasma; do
    ln -s "$project/$component" "$fixture/$component"
done
printf 'bad archive\n' > "$fixture/cursors/macOS-cursors.tar.xz"
before=$(snapshot)
for mode in --dry-run --apply; do
    check "install $mode rejects the bad archive" bash -c '! "$1" "$2" > "$3" 2>&1' _ "$fixture/install.sh" "$mode" "$root/bad-cursor.log"
    check "  the reason is the cursor archive" grep -Fq 'the bundled cursor archive is missing or has changed' "$root/bad-cursor.log"
    check "  the home is unchanged" same "$before" "$(snapshot)"
done

# --------------------------------------------------------------------------
# #110: WhiteSur Lavender icons install, apply, adoption, update, and undo
# --------------------------------------------------------------------------
eff_icon() {
    XDG_CONFIG_HOME="$config" XDG_CONFIG_DIRS="$config/kdedefaults:/etc/xdg" \
        kreadconfig6 --file kdeglobals --group Icons --key Theme
}

fresh "#110 fresh install, apply, relative symlinks, and clean undo"
before=$(snapshot)
run dry-icons "$project/install.sh" --dry-run
check "install --dry-run lists all three WhiteSur Lavender themes" bash -c '
    grep -Fq "would install $1/icons/WhiteSur-lavender/" "$2" &&
    grep -Fq "would install $1/icons/WhiteSur-lavender-light/" "$2" &&
    grep -Fq "would install $1/icons/WhiteSur-lavender-dark/" "$2"
' _ "$data" "$root/$n-dry-icons.log"
check "install --dry-run changes nothing" same "$before" "$(snapshot)"
check "plain install exits 0" run install "$project/install.sh"
check "  all three icon themes are installed without builder ownership stamps" bash -c '
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        test -f "$1/icons/$id/index.theme" && test ! -e "$1/icons/$id/.macos9-whitesur-lavender-build" || exit 1
    done
' _ "$data"
check "  relative symlinks in -light and -dark are preserved as links" bash -c '
    [[ $(readlink "$1/icons/WhiteSur-lavender-light/places") == "../WhiteSur-lavender/places" ]] &&
    [[ $(readlink "$1/icons/WhiteSur-lavender-dark/status/32") == "../../WhiteSur-lavender/status/32" ]]
' _ "$data"
check "  plain install records absences in icon-adoption" python3 -I - "$state/icon-adoption" << 'PYEND'
import json, sys
d = json.loads(open(sys.argv[1]).read())
assert d["version"] == 3 and d["backup_predated"] is False and d["phase"] == "skipped"
for tid in ("WhiteSur-lavender", "WhiteSur-lavender-light", "WhiteSur-lavender-dark"):
    assert d["preexisting"][tid] == "absent", d
PYEND
check "  plain install leaves icon selection untouched" bash -c '[[ -z $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) ]]' _ "$config"
check "--apply exits 0" run apply "$project/install.sh" --apply
check "  global theme selects WhiteSur-lavender" bash -c '[[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]]' _ "$config"
check "  other global theme defaults stay unchanged" bash -c '
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group KDE --key widgetStyle) == Platinum ]] &&
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group General --key ColorScheme) == Platinum ]] &&
    [[ $(kreadconfig6 --file "$1/kdedefaults/kcminputrc" --group Mouse --key cursorTheme) == macOS-cursors ]]
' _ "$config"
check "uninstall --dry-run plans removal of all three icon themes" bash -c '
    "$1/uninstall.sh" --dry-run > "$2" 2>&1 &&
    grep -Fq "would remove $3/icons/WhiteSur-lavender" "$2" &&
    grep -Fq "would remove $3/icons/WhiteSur-lavender-light" "$2" &&
    grep -Fq "would remove $3/icons/WhiteSur-lavender-dark" "$2"
' _ "$project" "$root/110-fresh-dry.log" "$data"
check "uninstall exits 0" run undo "$project/uninstall.sh"
check "  all three icon themes are gone" icons_absent "$data"
check "  inherited icon setting and full config are back byte for byte" same "$seed" "$(config_state)"
check "  no state record left" no_record_left

fresh "#110 adopt manual Lavender with pre-existing Platinum backup (old WhiteSur + Papirus-Dark gone)"
# 1. Seed a legacy pre-Platinum config that referenced old deleted WhiteSur icons and GTK Papirus-Dark.
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$config/xsettingsd/xsettingsd.conf"
check "pre-existing Platinum apply exits 0" run pre-apply "$project/install.sh" --apply
# Simulate the older pre-icon Platinum install: remove icon tracking/dirs from state & disk
# so $state/backup has TAKEN=apply (with legacy Theme=WhiteSur + GTK Papirus-Dark) predating manual Lavender!
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    rm -rf "$data/icons/$icon_id"
done
python3 -I - "$state/installed" "$data/icons/WhiteSur-lavender" << 'PYEND'
import sys
from pathlib import Path
p = Path(sys.argv[1])
pref = sys.argv[2]
lines = [ln for ln in p.read_text().splitlines() if pref not in ln]
p.write_text("\n".join(lines) + "\n")
PYEND
rm -f "$state/icon-adoption"
# 2. User manually copied unstamped WhiteSur-lavender trio (byte-identical to build on -light/-dark,
#    plus a distinct marker on base to verify restoration; also verify identical bytes get captured!)
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT/icons/$icon_id" "$data/icons/$icon_id"
    rm -f "$data/icons/$icon_id/.macos9-whitesur-lavender-build"
done
printf '# manual lavender base\n' >> "$data/icons/WhiteSur-lavender/index.theme"
# Select manual WhiteSur-lavender explicitly in kdeglobals and GTK (old Platinum kdedefaults had WhiteSur; old WhiteSur folders do not exist!)
kwriteconfig6 --file "$config/kdedefaults/kdeglobals" --group Icons --key Theme WhiteSur
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="WhiteSur-lavender"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "WhiteSur-lavender"\n' > "$config/xsettingsd/xsettingsd.conf"
backup_sums_before=$(cd "$state/backup" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
check "updated install.sh (plain update) adopts manual trio" run adopt "$project/install.sh"
backup_sums_after=$(cd "$state/backup" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
check "  pre-existing Platinum backup is preserved byte for byte" same "$backup_sums_before" "$backup_sums_after"
check "  icon-adoption recorded backup_predated=true and manual KDE+GTK selection" python3 -I - "$state/icon-adoption" << 'PYEND'
import json, sys
d = json.loads(open(sys.argv[1]).read())
assert d["version"] == 3 and d["backup_predated"] is True
cap = d["captured"]
assert cap["kde"]["effective_source"] == "kdeglobals" and cap["kde"]["effective_theme"] == "WhiteSur-lavender"
assert cap["gtk"]["gtk3"]["value"] == "WhiteSur-lavender" and cap["gtk"]["gtk4"]["value"] == "WhiteSur-lavender"
assert cap["gtk"]["gtk2"]["value"] == "WhiteSur-lavender" and cap["gtk"]["xsettingsd"]["value"] == "WhiteSur-lavender"
for tid in ("WhiteSur-lavender", "WhiteSur-lavender-light", "WhiteSur-lavender-dark"):
    assert d["preexisting"][tid] == "manual", d
PYEND
check "  all three manual copies were displaced (including byte-identical -light and -dark)" bash -c '
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        grep -q "^displaced	$1/icons/$id	" "$2/installed" || exit 1
    done
' _ "$data" "$state"
check "  managed WhiteSur-lavender replaced the manual copy in place" bash -c '! grep -Fq "# manual lavender base" "$1/icons/WhiteSur-lavender/index.theme"' _ "$data"
check "  plain update preserved WhiteSur-lavender selection" bash -c '[[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]]' _ "$config"
# Repeated plain update + local edit + another update must preserve original manual copies!
check "repeated plain update exits 0" run update-2 "$project/install.sh"
printf 'my-later-edit\n' > "$data/icons/WhiteSur-lavender/local-edit.txt"
check "update after local edit exits 0" run update-3 "$project/install.sh"
check "uninstall --dry-run plans restoring manual selection and copies" bash -c '
    "$1/uninstall.sh" --dry-run > "$2" 2>&1 &&
    grep -Fq "would restore explicit KDE icon theme (WhiteSur-lavender)" "$2" &&
    grep -Fq "would restore gtk3 icon theme (WhiteSur-lavender)" "$2" &&
    grep -Fq "would put back the earlier $3/icons/WhiteSur-lavender" "$2" &&
    ! grep -Fq "is still selected" "$2"
' _ "$project" "$root/110-adopt-dry.log" "$data"
check "uninstall exits 0 without assuming old WhiteSur exists" run undo "$project/uninstall.sh"
check "  original manual WhiteSur-lavender base is restored" grep -Fq "# manual lavender base" "$data/icons/WhiteSur-lavender/index.theme"
check "  manual -light and -dark are restored with working relative symlinks" bash -c '
    [[ $(readlink "$1/icons/WhiteSur-lavender-light/places") == "../WhiteSur-lavender/places" ]] &&
    test -f "$1/icons/WhiteSur-lavender-light/places/scalable/folder.svg" &&
    [[ $(readlink "$1/icons/WhiteSur-lavender-dark/status/32") == "../../WhiteSur-lavender/status/32" ]] &&
    test -f "$1/icons/WhiteSur-lavender-dark/status/32/start-here.svg"
' _ "$data"
check "  WhiteSur-lavender icon selection is restored in kdeglobals and GTK (not Papirus-Dark)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"WhiteSur-lavender\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"WhiteSur-lavender\"" "$1/xsettingsd/xsettingsd.conf"
' _ "$config" "$home"
check "  later local-edit copy was preserved in later-versions" bash -c 'grep -rlx my-later-edit "$1"/macos9-theme-uninstalled-*/later-versions 2> /dev/null | grep -q local-edit.txt' _ "$home/.local/state"
check "  no state record left" no_record_left
check "repeated uninstall exits 0 and leaves restored manual copies untouched" bash -c '
    "$1/uninstall.sh" > "$2" 2>&1 &&
    grep -Fq "# manual lavender base" "$3/icons/WhiteSur-lavender/index.theme" &&
    [[ $(kreadconfig6 --file "$4/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$project" "$root/110-repeat-undo.log" "$data" "$config"

# Independent selection of all three variants + base dependency retention
for variant in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    fresh "#110 independent selection of $variant retains required copy until unselected"
    check "install exits 0" run install "$project/install.sh"
    kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme "$variant"
    before=$(snapshot)
    check "uninstall --dry-run warns about $variant and changes nothing" bash -c '
        "$1/uninstall.sh" --dry-run > "$2" 2>&1 &&
        grep -Fq "$3 is still selected" "$2"
    ' _ "$project" "$root/110-sel-$variant-dry.log" "$variant"
    check "  dry run left home unchanged" same "$before" "$(snapshot)"
    if run undo "$project/uninstall.sh"; then
        fail "uninstall defers $variant while selected"
    else
        pass "uninstall defers $variant while selected"
    fi
    check "  $variant remains usable" test -f "$data/icons/$variant/index.theme"
    check "  base WhiteSur-lavender remains usable" test -f "$data/icons/WhiteSur-lavender/places/scalable/folder.svg"
    if [[ $variant == WhiteSur-lavender-light ]]; then
        check "  unselected -dark was removed" test ! -e "$data/icons/WhiteSur-lavender-dark"
    elif [[ $variant == WhiteSur-lavender-dark ]]; then
        check "  unselected -light was removed" test ! -e "$data/icons/WhiteSur-lavender-light"
    else
        check "  unselected -light and -dark were removed" bash -c 'test ! -e "$1/icons/WhiteSur-lavender-light" && test ! -e "$1/icons/WhiteSur-lavender-dark"' _ "$data"
    fi
    kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
    check "  retry after switching to breeze exits 0" run retry "$project/uninstall.sh"
    check "  all three icon dirs are now gone" icons_absent "$data"
    check "  no state record left" no_record_left
done

fresh "#110 local edits inside managed icon theme survive uninstall (unselected and selected)"
check "install exits 0" run install "$project/install.sh"
printf 'user-custom-file\n' > "$data/icons/WhiteSur-lavender/custom.txt"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender-light
if run undo-sel "$project/uninstall.sh"; then
    fail "uninstall keeps selected -light and edited base together"
else
    pass "uninstall keeps selected -light and edited base together"
fi
check "  base folder and its installed icons stay intact while -light is selected" test -f "$data/icons/WhiteSur-lavender/places/scalable/folder.svg"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
check "retry after switching away exits 0" run undo-retry "$project/uninstall.sh"
check "  user custom file in WhiteSur-lavender is preserved" grep -Fxq user-custom-file "$data/icons/WhiteSur-lavender/custom.txt"
check "  unchanged installed icons around it were removed" test ! -e "$data/icons/WhiteSur-lavender/places/scalable/folder.svg"
check "  unmodified -light and -dark were removed" bash -c 'test ! -e "$1/icons/WhiteSur-lavender-light" && test ! -e "$1/icons/WhiteSur-lavender-dark"' _ "$data"

fresh "#110 interrupted update during icon placement recovers cleanly on retry"
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT/icons/$icon_id" "$data/icons/$icon_id"
    rm -f "$data/icons/$icon_id/.macos9-whitesur-lavender-build"
done
printf '# manual-before-interrupt\n' >> "$data/icons/WhiteSur-lavender/index.theme"
fail_bin=$root/fail-icon-mv
mkdir -p "$fail_bin"
cat > "$fail_bin/mv" << 'STUB'
#!/bin/bash
if [[ ${!#} == "$M9_FAIL_ICON_TARGET" ]]; then
    exit 1
fi
exec /usr/bin/mv "$@"
STUB
chmod +x "$fail_bin/mv"
if run interrupted env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender-light" "$project/install.sh"; then
    fail "interrupted install reports failure"
else
    pass "interrupted install reports failure"
fi
check "retry install exits 0" run retry-install "$project/install.sh"
check "  all three icon themes are installed cleanly" bash -c '
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        test -f "$1/icons/$id/index.theme" || exit 1
    done
' _ "$data"
check "  no leftover temp directories in icons/" bash -c '! ls -d "$1/icons"/.macos9-theme.* > /dev/null 2>&1' _ "$data"
check "uninstall after recovered install exits 0" run undo "$project/uninstall.sh"
check "  original manual WhiteSur-lavender base survived the interruption and was restored" grep -Fq "# manual-before-interrupt" "$data/icons/WhiteSur-lavender/index.theme"

fresh "#110 unpinned upstream repo is rejected before any writes (without M9_PREBUILT)"
bad_up=$root/bad-whitesur-up
rm -rf "$bad_up"
mkdir -p "$bad_up"
before=$(snapshot)
for mode in --dry-run ""; do
    if env -u M9_PREBUILT M9_WHITESUR_UPSTREAM="$bad_up" "$project/install.sh" ${mode:+"$mode"} > "$root/110-bad-up.log" 2>&1; then
        fail "install ${mode:-real} rejects bad upstream"
    else
        pass "install ${mode:-real} rejects bad upstream"
    fi
    check "  home unchanged after bad upstream (${mode:-real})" same "$before" "$(snapshot)"
done

# --------------------------------------------------------------------------
# Real-size 44,619-entry WhiteSur Lavender round-trip, custom layer, and
# automatic fetch/cache tests (local file:// remote, zero real network)
# --------------------------------------------------------------------------
fresh "#110 real-size 44,619-entry install, apply, adoption, custom layer, and undo"
# 1. Real-size fresh install + --apply + undo (M9_PREBUILT_REAL)
check "real-size install exits 0" run real-install env M9_PREBUILT="$M9_PREBUILT_REAL" "$project/install.sh"
check "  real-size WhiteSur-lavender installed (>20k files/links)" bash -c '[[ $(find "$1/icons/WhiteSur-lavender" -mindepth 1 | wc -l) -gt 20000 ]]' _ "$data"
check "real-size --apply exits 0" run real-apply env M9_PREBUILT="$M9_PREBUILT_REAL" "$project/install.sh" --apply
check "  real-size --apply selected WhiteSur-lavender" bash -c '[[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]]' _ "$config"
check "real-size uninstall exits 0" run real-undo "$project/uninstall.sh"
check "  all three real-size icon dirs removed" icons_absent "$data"
check "  real-size config restored byte for byte" same "$seed" "$(config_state)"
check "  no state record left" no_record_left

# 2. Automatic fetch/cache + custom icon layer (no M9_PREBUILT/icons; local file:// remote only!)
fresh "#110 automatic WhiteSur fetch/cache, offline/corrupt/wrong-commit handling, and custom layer"
# Build a prebuilt dir containing ONLY the C++ plugins (no icons/) so install.sh uses real fetch+build!
no_icon_prebuilt=$root/prebuilt-cpp-only
rm -rf "$no_icon_prebuilt"
mkdir -p "$no_icon_prebuilt"
cp -R "$M9_PREBUILT/style" "$M9_PREBUILT/decoration" "$M9_PREBUILT/quick" "$no_icon_prebuilt/"

custom_test_dir=$root/test-custom-icons
rm -rf "$custom_test_dir"
mkdir -p "$custom_test_dir/all/apps/scalable" "$custom_test_dir/light/places/scalable" "$custom_test_dir/dark/apps/scalable"
printf '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#123456"/></svg>\n' > "$custom_test_dir/all/apps/scalable/m9-custom-app.svg"
ln -s m9-custom-app.svg "$custom_test_dir/all/apps/scalable/m9-custom-alias.svg"
printf '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#abcdef"/></svg>\n' > "$custom_test_dir/light/places/scalable/folder.svg"
printf '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="20" fill="#222222"/></svg>\n' > "$custom_test_dir/dark/apps/scalable/firefox.svg"

cache_repo=$XDG_CACHE_HOME/macos9-theme/WhiteSur-icon-theme
before=$(snapshot)
check "install --dry-run does not download or create cache dir" bash -c '
    M9_PREBUILT="$1" M9_WHITESUR_REMOTE="$2" M9_ICON_CUSTOM_DIR="$3" "$4/install.sh" --dry-run > "$5" 2>&1 &&
    grep -Fq "would fetch pinned WhiteSur commit" "$5" &&
    test ! -e "$6"
' _ "$no_icon_prebuilt" "$M9_TEST_REMOTE" "$custom_test_dir" "$project" "$root/110-fetch-dry.log" "$XDG_CACHE_HOME/macos9-theme"
check "  home completely unchanged after --dry-run" same "$before" "$(snapshot)"

# Offline miss when cache does not exist yet
if env M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="file:///nonexistent-offline-repo" "$project/install.sh" > "$root/110-offline-miss.log" 2>&1; then
    fail "offline install fails when cache is missing"
else
    pass "offline install fails when cache is missing"
fi
check "  offline miss prints clear error" grep -qi "offline\|unreachable\|could not fetch" "$root/110-offline-miss.log"
check "  offline miss leaves entire home unchanged" same "$before" "$(snapshot)"

# #118: Missing icon-builder tool fails preflight BEFORE lock, fetch, or writes and names Arch package
masked_bin=$root/masked-xmllint
rm -rf "$masked_bin"
mkdir -p "$masked_bin"
for t in bash sh env awk sed grep find sort xargs cat head tail tr cut mkdir rmdir rm mv cp ln chmod touch mktemp realpath dirname basename readlink tar sha256sum g++ pkg-config install ldd python3 git kreadconfig6 kwriteconfig6 rsvg-convert gtk-update-icon-cache flock dbus-send; do
    tpath=$(command -v "$t" 2> /dev/null || true)
    [[ -n $tpath ]] && ln -sf "$tpath" "$masked_bin/$t"
done
if env PATH="$masked_bin" M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="$M9_TEST_REMOTE" "$project/install.sh" > "$root/118-preflight.log" 2>&1; then
    fail "#118 preflight rejects missing xmllint"
else
    pass "#118 preflight rejects missing xmllint"
fi
check "  #118 error names missing xmllint and Arch package libxml2" bash -c '
    grep -Fq "xmllint" "$1" && grep -Fq "libxml2" "$1"
' _ "$root/118-preflight.log"
check "  #118 failed preflight left entire home unchanged (no lock, no cache)" same "$before" "$(snapshot)"

# #116: Unrelated sibling dir .WhiteSur-fetch.mydata must survive real fetch untouched!
mkdir -p "$XDG_CACHE_HOME/macos9-theme/.WhiteSur-fetch.mydata"
printf 'keep-my-data\n' > "$XDG_CACHE_HOME/macos9-theme/.WhiteSur-fetch.mydata/note.txt"
check "real install auto-fetches pinned commit from local remote and applies custom layer" \
    run real-fetch-install env M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="$M9_TEST_REMOTE" M9_ICON_CUSTOM_DIR="$custom_test_dir" "$project/install.sh"
check "  cache populated and unrelated .WhiteSur-fetch.mydata preserved (#116)" bash -c '
    test -d "$1" && grep -Fxq "keep-my-data" "$2/.WhiteSur-fetch.mydata/note.txt"
' _ "$cache_repo" "$XDG_CACHE_HOME/macos9-theme"
check "  custom brand-new icon, alias, and light/dark overrides installed cleanly" bash -c '
    grep -Fq "#123456" "$1/icons/WhiteSur-lavender/apps/scalable/m9-custom-app.svg" &&
    [[ $(readlink "$1/icons/WhiteSur-lavender/apps/scalable/m9-custom-alias.svg") == "m9-custom-app.svg" ]] &&
    grep -Fq "#abcdef" "$1/icons/WhiteSur-lavender-light/places/scalable/folder.svg" &&
    grep -Fq "#b5b4f9" "$1/icons/WhiteSur-lavender/places/scalable/folder.svg" &&
    grep -Fq "#222222" "$1/icons/WhiteSur-lavender-dark/apps/scalable/firefox.svg"
' _ "$data"

# Offline reuse of populated cache succeeds with unreachable remote URL!
check "offline update reuses populated cache without network" \
    run real-offline-hit env M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="file:///nonexistent-offline-repo" M9_ICON_CUSTOM_DIR="$custom_test_dir" "$project/install.sh"

# Corrupt cache rejected with clear error and installed theme left untouched!
mv "$cache_repo" "$root/cache-repo.saved"
mkdir -p "$cache_repo"
printf 'not a git repo\n' > "$cache_repo/corrupt"
if env M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="$M9_TEST_REMOTE" "$project/install.sh" > "$root/110-corrupt-cache.log" 2>&1; then
    fail "corrupt cache is rejected"
else
    pass "corrupt cache is rejected"
fi
check "  corrupt cache error is clear and installed icons untouched" bash -c '
    grep -qi "corrupt" "$1" && grep -Fq "#123456" "$2/icons/WhiteSur-lavender/apps/scalable/m9-custom-app.svg"
' _ "$root/110-corrupt-cache.log" "$data"

# Cache at wrong commit rejected with clear error and installed theme left untouched!
rm -rf "$cache_repo"
git clone --quiet "$root/local-remote.git" "$cache_repo"
git -C "$cache_repo" -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -q -m "wrong commit"
if env M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="$M9_TEST_REMOTE" "$project/install.sh" > "$root/110-wrong-cache.log" 2>&1; then
    fail "wrong-commit cache is rejected"
else
    pass "wrong-commit cache is rejected"
fi
check "  wrong-commit cache error is clear and installed icons untouched" bash -c '
    grep -Fq "expected reviewed pin" "$1" && grep -Fq "#123456" "$2/icons/WhiteSur-lavender/apps/scalable/m9-custom-app.svg"
' _ "$root/110-wrong-cache.log" "$data"
rm -rf "$cache_repo"
mv "$root/cache-repo.saved" "$cache_repo"

check "uninstall after real-size custom install exits 0" run real-custom-undo "$project/uninstall.sh"
check "  all three real-size icon dirs removed" icons_absent "$data"

# --------------------------------------------------------------------------
# #112, #113, #114, #115, #117, #122 + active-Platinum auto-select tests
# --------------------------------------------------------------------------

# Export real HEAD 8b5c251 into $root/head-project to test genuine format-4
# full-size upgrades in BOTH legacy backup states (TAKEN=apply and TAKEN=install+picker).
head_project=$root/head-project
rm -rf "$head_project"
mkdir -p "$head_project"
git -C "$project" archive 8b5c251 | tar -x -C "$head_project"

fresh "#113/#117/#122 real-size upgrade from genuine HEAD 8b5c251 (TAKEN=apply, manual Lavender, old WhiteSur + Papirus-Dark)"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$config/xsettingsd/xsettingsd.conf"
check "HEAD 8b5c251 install --apply exits 0" run head-apply env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh" --apply
check "  HEAD backup has TAKEN=apply" grep -qx apply "$state/backup/TAKEN"
# User manually installed unstamped full-size Lavender trio and selected it in KDE & GTK.
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT_REAL/icons/$icon_id" "$data/icons/$icon_id"
done
printf '# real-head-apply-manual\n' >> "$data/icons/WhiteSur-lavender/index.theme"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="WhiteSur-lavender"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "WhiteSur-lavender"\n' > "$config/xsettingsd/xsettingsd.conf"
backup_sums_before=$(cd "$state/backup" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
check "working-tree full-size upgrade exits 0" run wt-upgrade env M9_PREBUILT="$M9_PREBUILT_REAL" "$project/install.sh"
backup_sums_after=$(cd "$state/backup" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
check "  HEAD backup untouched byte for byte" same "$backup_sums_before" "$backup_sums_after"
check "  all three real-size manual copies were displaced" bash -c '
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        grep -q "^displaced	$1/icons/$id	" "$2/installed" || exit 1
    done
' _ "$data" "$state"
check "uninstall after HEAD TAKEN=apply upgrade exits 0" run wt-undo "$project/uninstall.sh"
check "  original real-size manual Lavender base restored" grep -Fq "# real-head-apply-manual" "$data/icons/WhiteSur-lavender/index.theme"
check "  real-size -light/-dark restored with working relative symlinks" bash -c '
    [[ $(readlink "$1/icons/WhiteSur-lavender-light/places") == "../WhiteSur-lavender/places" ]] &&
    test -f "$1/icons/WhiteSur-lavender-light/places/scalable/folder.svg" &&
    [[ $(readlink "$1/icons/WhiteSur-lavender-dark/status/32") == "../../WhiteSur-lavender/status/32" ]] &&
    test -f "$1/icons/WhiteSur-lavender-dark/status/32/start-here.svg"
' _ "$data"
check "  KDE and GTK restored to WhiteSur-lavender (not missing WhiteSur or Papirus-Dark)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"WhiteSur-lavender\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"WhiteSur-lavender\"" "$1/xsettingsd/xsettingsd.conf"
' _ "$config" "$home"
check "  no state record left" no_record_left

fresh "#113/#117/#122 real-size upgrade from genuine HEAD 8b5c251 (TAKEN=install + picker activation, inherited KDE Lavender)"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
check "HEAD 8b5c251 plain install exits 0" run head-plain env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh"
check "  HEAD backup has TAKEN=install" grep -qx install "$state/backup/TAKEN"
# Simulate System Settings picker activating Platinum + inherited kdedefaults WhiteSur-lavender + manual full-size copies.
kwriteconfig6 --file "$config/kdeglobals" --group KDE --key LookAndFeelPackage platinum.desktop
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme --delete
mkdir -p "$config/kdedefaults"
kwriteconfig6 --file "$config/kdedefaults/kdeglobals" --group Icons --key Theme WhiteSur-lavender
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-4.0/settings.ini"
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT_REAL/icons/$icon_id" "$data/icons/$icon_id"
done
printf '# real-head-picker-manual\n' >> "$data/icons/WhiteSur-lavender/index.theme"
check "working-tree full-size upgrade promotes backup and sets backup_predated=true" run wt-picker-upgrade env M9_PREBUILT="$M9_PREBUILT_REAL" "$project/install.sh"
check "  backup/TAKEN promoted to apply" grep -qx apply "$state/backup/TAKEN"
check "  icon-adoption recorded backup_predated=true and inherited kdedefaults source" python3 -I - "$state/icon-adoption" << 'PYEND'
import json, sys
d = json.loads(open(sys.argv[1]).read())
assert d["version"] == 3 and d["backup_predated"] is True
assert d["captured"]["kde"]["effective_source"] == "kdedefaults"
assert d["captured"]["kde"]["effective_theme"] == "WhiteSur-lavender"
assert d["captured"]["kde"]["kdeglobals"]["present"] is False
PYEND
check "uninstall after HEAD TAKEN=install+picker upgrade exits 0" run wt-picker-undo "$project/uninstall.sh"
check "  original real-size manual Lavender base restored" grep -Fq "# real-head-picker-manual" "$data/icons/WhiteSur-lavender/index.theme"
check "  inherited KDE WhiteSur-lavender preserved in kdedefaults without explicit override or Theme[\$d] (#117, #142)" bash -c '
    ! grep -Eq "^Theme([[:space:]]*=|\[\$)" "$1/kdeglobals" &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$config"
check "  GTK restored to WhiteSur-lavender (not Papirus-Dark)" bash -c '
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini"
' _ "$config"
check "  no state record left" no_record_left

fresh "#112 displacement failure on BOTH sides of the first rename (and abrupt pre-rename orphan record)"
# Side 1a: mv fails BEFORE the displacement rename of WhiteSur-lavender
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT/icons/$icon_id" "$data/icons/$icon_id"
done
printf '# manual-side1a\n' >> "$data/icons/WhiteSur-lavender/index.theme"
fail_disp_bin=$root/fail-disp-mv
mkdir -p "$fail_disp_bin"
cat > "$fail_disp_bin/mv" << 'STUB'
#!/bin/bash
if [[ $1 == "$M9_FAIL_DISP_SRC" && $2 == */displaced/* ]]; then
    exit 1
fi
exec /usr/bin/mv "$@"
STUB
chmod +x "$fail_disp_bin/mv"
if run disp-fail-before env PATH="$fail_disp_bin:$PATH" M9_FAIL_DISP_SRC="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "displacement mv failure reports error"
else
    pass "displacement mv failure reports error"
fi
check "  manual copy untouched in place after pre-rename mv failure" grep -Fq "# manual-side1a" "$data/icons/WhiteSur-lavender/index.theme"
check "  failed displaced record was rolled back from manifest" bash -c '! grep -q "^displaced	$1/icons/WhiteSur-lavender	" "$2/installed"' _ "$data" "$state"
check "  retry install exits 0" run disp-retry1 "$project/install.sh"
check "  uninstall restores original manual copy cleanly (not demoted to later-versions)" run disp-undo1 "$project/uninstall.sh"
check "  manual-side1a is back in place" grep -Fq "# manual-side1a" "$data/icons/WhiteSur-lavender/index.theme"
check "  no state record left" no_record_left

# Side 1b: simulated abrupt SIGKILL between manifest_add displaced and mv "$path" "$saved"
fresh "#112 abrupt pre-rename orphan displaced record recovered on retry + undo"
mkdir -p "$data/icons" "$state/displaced/orph01"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT/icons/$icon_id" "$data/icons/$icon_id"
done
printf '# manual-side1b\n' >> "$data/icons/WhiteSur-lavender/index.theme"
real_base=$(realpath -m -- "$data/icons")/WhiteSur-lavender
printf 'macos9-theme-record\t4\nhome\t%s\ndata\t%s\nconfig\t%s\ndisplaced\t%s/icons/WhiteSur-lavender\t%s/displaced/orph01/WhiteSur-lavender\t%s\n' \
    "$home" "$data" "$config" "$data" "$state" "$real_base" > "$state/installed"
check "install after abrupt pre-rename orphan record exits 0" run disp-retry1b "$project/install.sh"
check "  orphan empty holder cleaned and real displacement recorded" bash -c 'test ! -e "$1/displaced/orph01" && [[ $(grep -c "^displaced	$2/icons/WhiteSur-lavender	" "$1/installed") -eq 1 ]]' _ "$state" "$data"
check "uninstall restores original manual-side1b copy (not demoted to later-versions)" run disp-undo1b "$project/uninstall.sh"
check "  manual-side1b is back in place" grep -Fq "# manual-side1b" "$data/icons/WhiteSur-lavender/index.theme"
check "  no state record left" no_record_left

# Side 2: failure AFTER the first displacement rename (displace_foreign succeeded, place_dir mv failed)
fresh "#112 failure AFTER first displacement rename recovers on both direct undo and retry+undo"
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT/icons/$icon_id" "$data/icons/$icon_id"
done
printf '# manual-side2\n' >> "$data/icons/WhiteSur-lavender/index.theme"
if run disp-fail-after env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "post-displacement place_dir failure reports error"
else
    pass "post-displacement place_dir failure reports error"
fi
check "  direct uninstall restores manual-side2 back into icons/" run disp-direct-undo "$project/uninstall.sh"
check "  manual-side2 restored by direct uninstall" grep -Fq "# manual-side2" "$data/icons/WhiteSur-lavender/index.theme"
check "  no state record left" no_record_left
# Same failure again, then retry install -> undo
if run disp-fail-after2 env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "second post-displacement failure reports error"
else
    pass "second post-displacement failure reports error"
fi
check "  retry install after post-displacement failure exits 0" run disp-retry2 "$project/install.sh"
check "  uninstall after retry restores manual-side2" run disp-undo2 "$project/uninstall.sh"
check "  manual-side2 back in place after retry+undo" grep -Fq "# manual-side2" "$data/icons/WhiteSur-lavender/index.theme"
check "  no state record left" no_record_left

fresh "#114 interrupted undo at exact backup -> keep/original boundary keeps icon-adoption intact"
kwriteconfig6 --file "$config/kdeglobals" --group KDE --key LookAndFeelPackage platinum.desktop
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
# Predating backup with legacy WhiteSur + Papirus-Dark
mkdir -p "$state/backup/config/gtk-3.0" "$state/backup/config/gtk-4.0"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=WhiteSur\n' > "$state/backup/config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-4.0/settings.ini"
printf 'apply\n' > "$state/backup/TAKEN"
printf 'config\t%s\nhome\t%s\n' "$config" "$home" > "$state/backup/ROOTS"
: > "$state/backup/ABSENT"
for f in kdeglobals gtk-3.0/settings.ini gtk-4.0/settings.ini; do
    printf 'config\t%s\t%s\n' "$f" "$config/$f"
done > "$state/backup/ENTRIES"
(cd "$state/backup" && find config -type f -print0 | sort -z | xargs -0 sha256sum) > "$state/backup/SUMS"
check "plain install on active Platinum exits 0" run install-114 "$project/install.sh"
fail_bak_mv=$root/fail-bak-mv
mkdir -p "$fail_bak_mv"
cat > "$fail_bak_mv/mv" << 'STUB'
#!/bin/bash
if [[ $1 == -T && $2 == */macos9-theme/backup && $3 == */original ]]; then
    exit 1
fi
exec /usr/bin/mv "$@"
STUB
chmod +x "$fail_bak_mv/mv"
if run undo-114-fail env PATH="$fail_bak_mv:$PATH" "$project/uninstall.sh"; then
    fail "interrupted undo at backup rename exits non-zero"
else
    pass "interrupted undo at backup rename exits non-zero"
fi
check "  backup and icon-adoption BOTH remain in state after failed backup rename" bash -c 'test -d "$1/backup" && test -f "$1/icon-adoption"' _ "$state"
check "retry uninstall after backup-rename interruption exits 0" run undo-114-retry "$project/uninstall.sh"
check "  pre-adoption breeze restored in KDE and GTK (not WhiteSur or Papirus-Dark)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini"
' _ "$config"
check "  all three icon dirs removed" icons_absent "$data"
check "  no state record left" no_record_left

fresh "#115 ~/.icons symlink to managed WhiteSur-lavender is rejected as an outside copy"
check "install exits 0" run install-115 "$project/install.sh"
mkdir -p "$home/.icons"
ln -s "$data/icons/WhiteSur-lavender" "$home/.icons/WhiteSur-lavender"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender
if run undo-115-base "$project/uninstall.sh"; then
    fail "uninstall keeps managed base when ~/.icons/WhiteSur-lavender points to it"
else
    pass "uninstall keeps managed base when ~/.icons/WhiteSur-lavender points to it"
fi
check "  managed base dir survived (not deleted through ~/.icons symlink)" test -f "$data/icons/WhiteSur-lavender/index.theme"
# Also test a variant in ~/.icons whose places symlink resolves into managed base!
rm -f "$home/.icons/WhiteSur-lavender"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
check "  clean up after base test" run undo-115-clean1 "$project/uninstall.sh"
check "  reinstall for variant places symlink test" run install-115b "$project/install.sh"
ln -s "$data/icons/WhiteSur-lavender" "$home/.icons/WhiteSur-lavender"
mkdir -p "$home/.icons/WhiteSur-lavender-light"
cp "$data/icons/WhiteSur-lavender-light/index.theme" "$home/.icons/WhiteSur-lavender-light/index.theme"
ln -s ../WhiteSur-lavender/places "$home/.icons/WhiteSur-lavender-light/places"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender-light
if run undo-115-light "$project/uninstall.sh"; then
    fail "uninstall keeps managed -light and base when ~/.icons/-light/places resolves into managed base"
else
    pass "uninstall keeps managed -light and base when ~/.icons/-light/places resolves into managed base"
fi
check "  managed base and -light both kept intact" bash -c 'test -f "$1/icons/WhiteSur-lavender/index.theme" && test -f "$1/icons/WhiteSur-lavender-light/index.theme"' _ "$data"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
check "  retry after switching to breeze exits 0" run undo-115-done "$project/uninstall.sh"
check "  all three managed icon dirs removed" icons_absent "$data"
check "  no state record left" no_record_left

fresh "#117 inherited KDE key + unset GTK key + missing-theme fallback safety"
mkdir -p "$config/kdedefaults"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n' > "$config/kdeglobals"
printf '[Icons]\nTheme=breeze\n' > "$config/kdedefaults/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\n' > "$config/gtk-3.0/settings.ini"
rm -f "$config/gtk-4.0/settings.ini" "$home/.gtkrc-2.0" "$config/xsettingsd/xsettingsd.conf"
# Predating backup has explicit WhiteSur in kdeglobals AND stale Papirus-Dark in GTK 3/4/2/xsettingsd
mkdir -p "$state/backup/config/gtk-3.0" "$state/backup/config/gtk-4.0" "$state/backup/config/xsettingsd" "$state/backup/home"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=WhiteSur\n' > "$state/backup/config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$state/backup/home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$state/backup/config/xsettingsd/xsettingsd.conf"
printf 'apply\n' > "$state/backup/TAKEN"
printf 'config\t%s\nhome\t%s\n' "$config" "$home" > "$state/backup/ROOTS"
printf 'config\tkdedefaults\n' > "$state/backup/ABSENT"
{
    for f in kdeglobals kdedefaults gtk-3.0/settings.ini gtk-4.0/settings.ini xsettingsd/xsettingsd.conf; do
        printf 'config\t%s\t%s\n' "$f" "$config/$f"
    done
    printf 'home\t.gtkrc-2.0\t%s/.gtkrc-2.0\n' "$home"
} > "$state/backup/ENTRIES"
(cd "$state/backup" && find config home -type f -print0 | sort -z | xargs -0 sha256sum) > "$state/backup/SUMS"
check "plain install on active Platinum (inherited breeze, unset GTK) exits 0" run install-117 "$project/install.sh"
check "  plain install selected WhiteSur-lavender in KDE and GTK" bash -c '
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini"
' _ "$config"
check "uninstall restores inherited KDE breeze and clears stale GTK Papirus-Dark" run undo-117 "$project/uninstall.sh"
check "  kdeglobals has NO explicit Theme key; kdedefaults has inherited breeze" bash -c '
    ! grep -q "^Theme=" "$1/kdeglobals" &&
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == breeze ]]
' _ "$config"
check "  stale Papirus-Dark cleared from GTK 3, GTK 4, GTK 2, and xsettingsd" bash -c '
    ! grep -q "gtk-icon-theme-name" "$1/gtk-3.0/settings.ini" &&
    test ! -e "$1/gtk-4.0/settings.ini" &&
    test ! -e "$2/.gtkrc-2.0" &&
    test ! -e "$1/xsettingsd/xsettingsd.conf"
' _ "$config" "$home"
check "  all three icon dirs removed" icons_absent "$data"
check "  no state record left" no_record_left

fresh "#117 missing pre-adoption icon theme falls back safely (never selects a missing theme)"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=MissingTheme999\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=MissingTheme999\n' > "$config/gtk-3.0/settings.ini"
mkdir -p "$state/backup/config/gtk-3.0"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=WhiteSur\n' > "$state/backup/config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-3.0/settings.ini"
printf 'apply\n' > "$state/backup/TAKEN"
printf 'config\t%s\nhome\t%s\n' "$config" "$home" > "$state/backup/ROOTS"
: > "$state/backup/ABSENT"
printf 'config\tkdeglobals\t%s/kdeglobals\nconfig\tgtk-3.0/settings.ini\t%s/gtk-3.0/settings.ini\n' "$config" "$config" > "$state/backup/ENTRIES"
(cd "$state/backup" && find config -type f -print0 | sort -z | xargs -0 sha256sum) > "$state/backup/SUMS"
check "plain install exits 0" run install-missing-fb "$project/install.sh"
check "uninstall exits 0 and falls back away from missing theme" run undo-missing-fb "$project/uninstall.sh"
check "  neither KDE nor GTK selects MissingTheme999, WhiteSur, or Papirus-Dark" bash -c '
    kde_eff=$(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme)
    [[ $kde_eff == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini"
' _ "$config"
check "  all three icon dirs removed" icons_absent "$data"

fresh "active-Platinum plain-install auto-select: one-time only, other settings untouched, clean undo (with & without prior backup)"
# Case A: Platinum active + predating backup + live explicit breeze + custom panels/cursors/kwinrc
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Mouse]\ncursorTheme=Breeze_Custom\n' > "$config/kcminputrc"
printf '[org.kde.kdecoration2]\nButtonsOnLeft=X\nButtonsOnRight=AI\n' > "$config/kwinrc"
printf 'panel=my-live-panel\nwallpaper=my-live-wall\n' > "$config/plasma-org.kde.plasma.desktop-appletsrc"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="breeze"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
mkdir -p "$state/backup/config/gtk-3.0" "$state/backup/config/gtk-4.0" "$state/backup/config/xsettingsd" "$state/backup/home"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=WhiteSur\n' > "$state/backup/config/kdeglobals"
printf '[Mouse]\ncursorTheme=Breeze_Orig\n' > "$state/backup/config/kcminputrc"
printf '[org.kde.kdecoration2]\nButtonsOnLeft=M\nButtonsOnRight=IAX\n' > "$state/backup/config/kwinrc"
printf 'panel=orig-panel\n' > "$state/backup/config/plasma-org.kde.plasma.desktop-appletsrc"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$state/backup/config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$state/backup/home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$state/backup/config/xsettingsd/xsettingsd.conf"
printf 'apply\n' > "$state/backup/TAKEN"
printf 'config\t%s\nhome\t%s\n' "$config" "$home" > "$state/backup/ROOTS"
: > "$state/backup/ABSENT"
{
    for f in kdeglobals kcminputrc kwinrc plasma-org.kde.plasma.desktop-appletsrc gtk-3.0/settings.ini gtk-4.0/settings.ini xsettingsd/xsettingsd.conf; do
        printf 'config\t%s\t%s\n' "$f" "$config/$f"
    done
    printf 'home\t.gtkrc-2.0\t%s/.gtkrc-2.0\n' "$home"
} > "$state/backup/ENTRIES"
(cd "$state/backup" && find config home -type f -print0 | sort -z | xargs -0 sha256sum) > "$state/backup/SUMS"
before=$(snapshot)
check "plain install --dry-run plans active-Platinum auto-select and changes nothing" bash -c '
    "$1/install.sh" --dry-run > "$2" 2>&1 &&
    grep -Fq "would select WhiteSur-lavender icons for KDE and GTK" "$2"
' _ "$project" "$root/auto-sel-dry.log"
check "  home unchanged after --dry-run" same "$before" "$(snapshot)"
check "plain install on active Platinum exits 0" run auto-sel-1 "$project/install.sh"
check "  selected WhiteSur-lavender in KDE and GTK without touching panels, wallpaper, cursors, or kwinrc" bash -c '
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    ! grep -q "^Theme=" "$1/kdeglobals" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"WhiteSur-lavender\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"WhiteSur-lavender\"" "$1/xsettingsd/xsettingsd.conf" &&
    grep -qx "cursorTheme=Breeze_Custom" "$1/kcminputrc" &&
    grep -qx "ButtonsOnLeft=X" "$1/kwinrc" &&
    grep -qx "panel=my-live-panel" "$1/plasma-org.kde.plasma.desktop-appletsrc" &&
    grep -qx "wallpaper=my-live-wall" "$1/plasma-org.kde.plasma.desktop-appletsrc"
' _ "$config" "$home"
# User switches icons to breeze later -> subsequent plain update MUST keep user choice!
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
sed -i 's/WhiteSur-lavender/breeze/' "$config/gtk-3.0/settings.ini" "$config/gtk-4.0/settings.ini" "$home/.gtkrc-2.0" "$config/xsettingsd/xsettingsd.conf"
check "second plain update exits 0 and keeps user chosen breeze" run auto-sel-2 "$project/install.sh"
check "  user breeze choice preserved across plain update" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini"
' _ "$config"
check "uninstall restores explicit breeze in KDE & GTK and removes trio" run auto-sel-undo "$project/uninstall.sh"
check "  explicit breeze restored in KDE & GTK (not Papirus-Dark or WhiteSur)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"breeze\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"breeze\"" "$1/xsettingsd/xsettingsd.conf" &&
    grep -qx "panel=orig-panel" "$1/plasma-org.kde.plasma.desktop-appletsrc"
' _ "$config" "$home"
check "  all three icon dirs removed" icons_absent "$data"
check "  no state record left" no_record_left

# Case B: Active Platinum with NO prior backup (backup_predated=0) -> backup taken BEFORE auto-select!
fresh "active-Platinum plain-install auto-select without prior backup restores pre-switch breeze byte-for-byte"
mkdir -p "$config/kdedefaults"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n' > "$config/kdeglobals"
printf '[Icons]\nTheme=breeze\n' > "$config/kdedefaults/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
seed_b=$(config_state)
check "plain install on active Platinum without prior backup exits 0" run auto-nobak "$project/install.sh"
check "  selected WhiteSur-lavender in KDE and GTK" bash -c '
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini"
' _ "$config"
check "uninstall restores exact pre-install breeze state byte for byte" run auto-nobak-undo "$project/uninstall.sh"
check "  config and GTK files back byte for byte" same "$seed_b" "$(config_state)"
check "  all three icon dirs removed" icons_absent "$data"
check "  no state record left" no_record_left

# Case C: Non-Platinum desktop -> plain install must NOT change KDE or GTK icon selection!
fresh "non-Platinum desktop plain install never changes KDE or GTK icon selection"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
seed_c=$(config_state)
check "plain install on Breeze desktop exits 0" run nonplat-plain "$project/install.sh"
check "  KDE and GTK icon selection completely untouched" same "$seed_c" "$(config_state)"
check "uninstall exits 0" run nonplat-undo "$project/uninstall.sh"
check "  all three icon dirs removed" icons_absent "$data"
check "  no state record left" no_record_left

# --------------------------------------------------------------------------
# #124–#131, #133, #135, #136, #138 regression suite
# --------------------------------------------------------------------------

fresh "#124 interrupted undo on HEAD TAKEN=install+picker backup resumes restore and never exposes WhiteSur/Papirus-Dark"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$config/xsettingsd/xsettingsd.conf"
check "HEAD plain install creates TAKEN=install backup" run head-124 env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh"
check "  HEAD backup has TAKEN=install" grep -qx install "$state/backup/TAKEN"
# Activate Platinum via picker and select breeze across KDE + GTK (no WhiteSur dirs).
kwriteconfig6 --file "$config/kdeglobals" --group KDE --key LookAndFeelPackage platinum.desktop
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="breeze"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
# Fail upgrade on first icon placement (so backup/TAKEN stays "install"!).
if run upg-124-fail env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "upgrade fails on first icon placement"
else
    pass "upgrade fails on first icon placement"
fi
check "  backup/TAKEN is still install" grep -qx install "$state/backup/TAKEN"
# Stop undo right AFTER kdeglobals is put back (before backup retires!).
fail_124_mv=$root/fail-124-mv
mkdir -p "$fail_124_mv"
cat > "$fail_124_mv/mv" << 'STUB'
#!/bin/bash
if [[ $1 == -T && $3 == */gtk-3.0/settings.ini ]]; then
    exit 1
fi
exec /usr/bin/mv "$@"
STUB
chmod +x "$fail_124_mv/mv"
if run undo-124-mid env PATH="$fail_124_mv:$PATH" "$project/uninstall.sh"; then
    fail "interrupted undo mid-restore exits non-zero"
else
    pass "interrupted undo mid-restore exits non-zero"
fi
# Even mid-interruption, staged merge ensured kdeglobals already has breeze (NEVER WhiteSur)!
check "  mid-interruption kdeglobals already has breeze (never missing WhiteSur)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group KDE --key LookAndFeelPackage) == org.kde.breeze.desktop ]]
' _ "$config"
check "  persisted restore_decision=restore_backup in icon-adoption" bash -c '
    [[ $(python3 -I "$1/scripts/icon_prefs.py" read-restore-decision "$2/icon-adoption") == restore_backup ]]
' _ "$project" "$state"
check "retry uninstall resumes restore despite TAKEN=install and Breeze LookAndFeelPackage" run undo-124-retry "$project/uninstall.sh"
check "  KDE and all 4 GTK files restored to breeze (never WhiteSur or Papirus-Dark)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"breeze\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"breeze\"" "$1/xsettingsd/xsettingsd.conf"
' _ "$config" "$home"
check "  all three icon dirs absent and no state left" bash -c '
    for id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
        [[ ! -e "$1/icons/$id" && ! -L "$1/icons/$id" ]] || exit 1
    done
    [[ ! -e "$2" ]]
' _ "$data" "$state"

fresh "#125 concurrent personal file saved during clean-dir removal is preserved (rmdir only, never rmtree)"
check "real-size install exits 0" run inst-125 env M9_PREBUILT="$M9_PREBUILT_REAL" "$project/install.sh"
# Spawn a watcher that creates personal-note as soon as index.theme disappears during undo!
(
    for _ in $(seq 1 400); do
        if [[ ! -e "$data/icons/WhiteSur-lavender/index.theme" && -d "$data/icons/WhiteSur-lavender" ]]; then
            printf 'keep-this-concurrent-note\n' > "$data/icons/WhiteSur-lavender/personal-note" 2>/dev/null || true
            break
        fi
        sleep 0.01
    done
) &
watcher_pid=$!
check "real-size uninstall exits 0 while concurrent file is saved" run undo-125 "$project/uninstall.sh"
wait "$watcher_pid" || true
check "  concurrently saved personal-note survived clean-dir removal (#125)" grep -Fxq "keep-this-concurrent-note" "$data/icons/WhiteSur-lavender/personal-note"
check "  uninstall reported keeping personal-note" grep -Fq "personal-note" "$root/$n-undo-125.log"
check "  unchanged variants -light and -dark were removed" bash -c 'test ! -e "$1/icons/WhiteSur-lavender-light" && test ! -e "$1/icons/WhiteSur-lavender-dark"' _ "$data"

fresh "#126 undo refuses to delete a theme still selected by GTK (even when KDE selects breeze)"
check "plain install on Breeze desktop exits 0" run inst-126 "$project/install.sh"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=WhiteSur-lavender-dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=WhiteSur-lavender-dark\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="WhiteSur-lavender-dark"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "WhiteSur-lavender-dark"\n' > "$config/xsettingsd/xsettingsd.conf"
if run undo-126 "$project/uninstall.sh"; then
    fail "uninstall keeps -dark and base while selected in GTK"
else
    pass "uninstall keeps -dark and base while selected in GTK"
fi
check "  warning names GTK selection" grep -q "WhiteSur-lavender-dark is still selected in GTK" "$root/$n-undo-126.log"
check "  managed -dark and base WhiteSur-lavender remain usable; unselected -light removed" bash -c '
    test -f "$1/icons/WhiteSur-lavender-dark/index.theme" &&
    test -f "$1/icons/WhiteSur-lavender/places/scalable/folder.svg" &&
    test ! -e "$1/icons/WhiteSur-lavender-light"
' _ "$data"
sed -i 's/WhiteSur-lavender-dark/breeze/g' "$config/gtk-3.0/settings.ini" "$config/gtk-4.0/settings.ini" "$home/.gtkrc-2.0" "$config/xsettingsd/xsettingsd.conf"
check "  retry after switching GTK away exits 0" run undo-126-retry "$project/uninstall.sh"
check "  all three icon dirs removed" icons_absent "$data"

fresh "#127 outside copy in ~/.icons with only apps/ linked to managed base is rejected as independent"
check "install exits 0" run inst-127 "$project/install.sh"
mkdir -p "$home/.icons/WhiteSur-lavender/places/scalable" "$home/.icons/WhiteSur-lavender/status/32"
printf '[Icon Theme]\nName=WhiteSur-lavender\nInherits=hicolor,breeze\nDirectories=places/scalable,status/32,apps/scalable\n' > "$home/.icons/WhiteSur-lavender/index.theme"
cp "$data/icons/WhiteSur-lavender/places/scalable/folder.svg" "$home/.icons/WhiteSur-lavender/places/scalable/folder.svg"
cp "$data/icons/WhiteSur-lavender/status/32/start-here.svg" "$home/.icons/WhiteSur-lavender/status/32/start-here.svg"
mkdir -p "$data/icons/WhiteSur-lavender/apps/scalable"
printf '<svg/>\n' > "$data/icons/WhiteSur-lavender/apps/scalable/firefox.svg"
ln -s "$data/icons/WhiteSur-lavender/apps" "$home/.icons/WhiteSur-lavender/apps"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender
if run undo-127 "$project/uninstall.sh"; then
    fail "uninstall rejects partially shared outside copy (apps/ symlink)"
else
    pass "uninstall rejects partially shared outside copy (apps/ symlink)"
fi
check "  managed base stayed intact so ~/.icons/WhiteSur-lavender/apps/scalable/firefox.svg still resolves" test -f "$home/.icons/WhiteSur-lavender/apps/scalable/firefox.svg"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
check "  retry after switching to breeze exits 0" run undo-127-done "$project/uninstall.sh"

fresh "#128 retry finishes unfinished first selection (both failed placement and read-only GTK 4 dir)"
# Case A: fail during first base placement after capture -> plain retry MUST complete selection!
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
if run inst-128a-fail env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "first install fails on base placement"
else
    pass "first install fails on base placement"
fi
check "  transaction stays in phase=captured" python3 -I -c 'import json, sys; assert json.load(open(sys.argv[1]))["phase"] == "captured"' "$state/icon-adoption"
check "plain retry completes placement AND selects WhiteSur-lavender everywhere" run inst-128a-retry "$project/install.sh"
check "  KDE and GTK 3/4 now select WhiteSur-lavender and phase=selected" bash -c '
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    ! grep -q "^Theme=" "$1/kdeglobals" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini" &&
    python3 -I -c "import json, sys; assert json.load(open(sys.argv[1]))[\"phase\"] == \"selected\"" "$2/icon-adoption"
' _ "$config" "$state"
check "  undo restores breeze cleanly" run undo-128a "$project/uninstall.sh"

# Case B: read-only gtk-4.0 dir stops mid-selection -> fixing perms and retrying finishes GTK 4/2/xsettingsd!
fresh "#128b read-only gtk-4.0 dir mid-selection resumes cleanly on retry and preserves later choices after completion"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="breeze"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
chmod 500 "$config/gtk-4.0"
if run inst-128b-fail "$project/install.sh"; then
    fail "install fails when gtk-4.0 dir is read-only"
else
    pass "install fails when gtk-4.0 dir is read-only"
fi
chmod 700 "$config/gtk-4.0"
check "  transaction stays in phase=selecting after partial failure" python3 -I -c 'import json, sys; assert json.load(open(sys.argv[1]))["phase"] == "selecting"' "$state/icon-adoption"
check "retry after fixing gtk-4.0 permissions exits 0" run inst-128b-retry "$project/install.sh"
check "  KDE and ALL 4 GTK files now select WhiteSur-lavender and phase=selected" bash -c '
    [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"WhiteSur-lavender\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"WhiteSur-lavender\"" "$1/xsettingsd/xsettingsd.conf" &&
    python3 -I -c "import json, sys; assert json.load(open(sys.argv[1]))[\"phase\"] == \"selected\"" "$3/icon-adoption"
' _ "$config" "$home" "$state"
check "  undo restores breeze cleanly" run undo-128b "$project/uninstall.sh"

fresh "#129 explicit KDE breeze does not leave stale inherited Adwaita from older backup underneath"
for kd_mode in same_breeze absent_kd; do
    rm -rf "$state" "$config/kdedefaults"
    mkdir -p "$state/backup/config/kdedefaults" "$config/kdedefaults"
    printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
    if [[ $kd_mode == same_breeze ]]; then
        printf '[Icons]\nTheme=breeze\n' > "$config/kdedefaults/kdeglobals"
    fi
    # Older predating backup has inherited Adwaita in kdedefaults/kdeglobals!
    printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n' > "$state/backup/config/kdeglobals"
    printf '[Icons]\nTheme=Adwaita\n' > "$state/backup/config/kdedefaults/kdeglobals"
    printf 'apply\n' > "$state/backup/TAKEN"
    printf 'config\t%s\nhome\t%s\n' "$config" "$home" > "$state/backup/ROOTS"
    : > "$state/backup/ABSENT"
    printf 'config\tkdeglobals\t%s/kdeglobals\nconfig\tkdedefaults\t%s/kdedefaults\n' "$config" "$config" > "$state/backup/ENTRIES"
    (cd "$state/backup" && find config -type f -print0 | sort -z | xargs -0 sha256sum) > "$state/backup/SUMS"
    check "install ($kd_mode) exits 0" run "inst-129-$kd_mode" "$project/install.sh"
    check "undo ($kd_mode) exits 0" run "undo-129-$kd_mode" "$project/uninstall.sh"
    if [[ $kd_mode == same_breeze ]]; then
        check "  ($kd_mode) explicit kdeglobals=breeze AND inherited kdedefaults=breeze (not Adwaita)" bash -c '
            [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
            [[ $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme) == breeze ]]
        ' _ "$config"
    else
        check "  ($kd_mode) explicit kdeglobals=breeze AND kdedefaults has NO stale Adwaita" bash -c '
            [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
            [[ -z $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme 2>/dev/null || true) ]]
        ' _ "$config"
    fi
done

fresh "#130 direct undo after post-displacement base failure restores manual trio AND preserves Lavender selection"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
check "HEAD apply creates predating backup" run head-130 env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh" --apply
mkdir -p "$data/icons"
for icon_id in WhiteSur-lavender WhiteSur-lavender-light WhiteSur-lavender-dark; do
    cp -RP "$M9_PREBUILT/icons/$icon_id" "$data/icons/$icon_id"
done
printf '# manual-130-marker\n' >> "$data/icons/WhiteSur-lavender/index.theme"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-4.0/settings.ini"
if run upg-130-fail env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "post-displacement base placement fails"
else
    pass "post-displacement base placement fails"
fi
check "  base target is currently empty while displaced original exists" test ! -e "$data/icons/WhiteSur-lavender"
check "direct uninstall exits 0" run undo-130 "$project/uninstall.sh"
check "  manual trio restored AND KDE + GTK selection stays WhiteSur-lavender (#130)" bash -c '
    grep -Fq "# manual-130-marker" "$1/icons/WhiteSur-lavender/index.theme" &&
    [[ $(kreadconfig6 --file "$2/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]] &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$2/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=WhiteSur-lavender" "$2/gtk-4.0/settings.ini"
' _ "$data" "$config"

fresh "#131 private 0600 permissions preserved across install, update, and undo"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="breeze"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
chmod 600 "$config/kdeglobals" "$config/gtk-3.0/settings.ini" "$config/gtk-4.0/settings.ini" "$home/.gtkrc-2.0" "$config/xsettingsd/xsettingsd.conf"
check "plain install on active Platinum exits 0" run inst-131 "$project/install.sh"
check "  all 0600 files stayed 0600 after plain auto-select (#131)" bash -c '
    for f in "$1/kdeglobals" "$1/gtk-3.0/settings.ini" "$1/gtk-4.0/settings.ini" "$2/.gtkrc-2.0" "$1/xsettingsd/xsettingsd.conf"; do
        [[ $(stat -c "%a" "$f") == 600 ]] || { echo "mode of $f is $(stat -c %a "$f")"; exit 1; }
    done
' _ "$config" "$home"
check "uninstall exits 0" run undo-131 "$project/uninstall.sh"
check "  all 0600 files stayed 0600 after undo (#131)" bash -c '
    for f in "$1/kdeglobals" "$1/gtk-3.0/settings.ini" "$1/gtk-4.0/settings.ini" "$2/.gtkrc-2.0" "$1/xsettingsd/xsettingsd.conf"; do
        [[ $(stat -c "%a" "$f") == 600 ]] || { echo "mode of $f is $(stat -c %a "$f")"; exit 1; }
    done
' _ "$config" "$home"

fresh "#133 uninstall --dry-run succeeds when backup had ABSENT kdeglobals"
rm -f "$config/kdeglobals"
check "HEAD plain install records kdeglobals in ABSENT" run head-133 env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh"
check "  backup/ABSENT lists config/kdeglobals" grep -qxF $'config\tkdeglobals' "$state/backup/ABSENT"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
check "upgrade exits 0" run upg-133 "$project/install.sh"
before_133=$(snapshot)
check "uninstall --dry-run exits 0 with absent backup kdeglobals (#133)" run dry-133 "$project/uninstall.sh" --dry-run
check "  --dry-run changed nothing" same "$before_133" "$(snapshot)"
check "real uninstall exits 0" run undo-133 "$project/uninstall.sh"

fresh "#135 missing flock is refused before creating state or cache entries"
noflock_bin=$root/masked-flock
rm -rf "$noflock_bin"
mkdir -p "$noflock_bin"
for t in bash sh env awk sed grep find sort xargs cat head tail tr cut mkdir rmdir rm mv cp ln chmod touch mktemp realpath dirname basename readlink tar sha256sum g++ pkg-config install ldd python3 git kreadconfig6 kwriteconfig6 xmllint rsvg-convert gtk-update-icon-cache dbus-send; do
    tpath=$(command -v "$t" 2> /dev/null || true)
    [[ -n $tpath ]] && ln -sf "$tpath" "$noflock_bin/$t"
done
before_135=$(snapshot)
if env PATH="$noflock_bin" M9_PREBUILT="$M9_PREBUILT" "$project/install.sh" > "$root/135-install.log" 2>&1; then
    fail "#135 install refuses when flock is missing"
else
    pass "#135 install refuses when flock is missing"
fi
check "  #135 install error names flock and util-linux and left home unchanged" bash -c '
    grep -Fq "flock" "$1" && grep -Fq "util-linux" "$1"
' _ "$root/135-install.log"
check "  #135 home completely unchanged" same "$before_135" "$(snapshot)"

fresh "#136 missing plugin build prerequisites (pkg-config Qt6/KF6) fail preflight before fetching or locking"
empty_pc=$root/empty-pkgconfig
mkdir -p "$empty_pc"
before_136=$(snapshot)
if env -u M9_PREBUILT PKG_CONFIG_LIBDIR="$empty_pc" PKG_CONFIG_PATH="" M9_WHITESUR_REMOTE="$M9_TEST_REMOTE" "$project/install.sh" > "$root/136-preflight.log" 2>&1; then
    fail "#136 preflight rejects missing Qt6/KF6 pkg-config modules"
else
    pass "#136 preflight rejects missing Qt6/KF6 pkg-config modules"
fi
check "  #136 error names qt6-base, qt6-declarative, and kcoreaddons" bash -c '
    grep -Fq "qt6-base" "$1" && grep -Fq "qt6-declarative" "$1" && grep -Fq "kcoreaddons" "$1"
' _ "$root/136-preflight.log"
check "  #136 failed preflight created no lock and no cache" same "$before_136" "$(snapshot)"

fresh "#138 install.sh --help documents active-Platinum one-time plain-install icon switch"
check "install.sh --help mentions active Platinum plain-install WhiteSur-lavender switch" bash -c '
    out=$("$1/install.sh" --help) &&
    grep -Fq "Platinum" <<< "$out" &&
    grep -Fq "WhiteSur-lavender" <<< "$out"
' _ "$project"

# --------------------------------------------------------------------------
# #139, #140, #141, #127 (incomplete outside copy), #131 (0644 backup / 0600 live)
# --------------------------------------------------------------------------

fresh "#139 capture precedes first change to installed targets or manifest; failed first target still undoes cleanly"
mkdir -p "$config/kdedefaults"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n' > "$config/kdeglobals"
printf '[Icons]\nTheme=Adwaita\n' > "$config/kdedefaults/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$config/xsettingsd/xsettingsd.conf"
check "HEAD plain install creates committed TAKEN=install backup" run head-139 env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh"
# Picker activates Platinum + explicit KDE breeze (no inherited key) + GTK breeze
rm -rf "$config/kdedefaults"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="breeze"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
# Case A: fail capture itself (make $state read-only after lock exists) -> ZERO targets or manifest changed!
lnf_before=$(sha256sum "$data/plasma/look-and-feel/platinum.desktop/contents/defaults" | awk '{print $1}')
man_before=$(sha256sum "$state/installed" | awk '{print $1}')
touch "$state/lock"
chmod 500 "$state"
if run cap-139-fail "$project/install.sh"; then
    fail "#139 failed capture exits non-zero"
else
    pass "#139 failed capture exits non-zero"
fi
chmod 700 "$state"
check "  #139 failed capture left look-and-feel and manifest untouched" bash -c '
    [[ $(sha256sum "$1" | awk "{print \$1}") == "$2" ]] &&
    [[ $(sha256sum "$3" | awk "{print \$1}") == "$4" ]] &&
    test ! -e "$5/icon-adoption"
' _ "$data/plasma/look-and-feel/platinum.desktop/contents/defaults" "$lnf_before" "$state/installed" "$man_before" "$state"
# Case B: fail on the VERY FIRST target placement (platinumstyle.so) -> capture already succeeded before it!
if run first-target-139-fail env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$home/.local/lib/macos9-theme/style/styles/platinumstyle.so" "$project/install.sh"; then
    fail "#139 first-target placement failure exits non-zero"
else
    pass "#139 first-target placement failure exits non-zero"
fi
check "  #139 icon-adoption was durably captured BEFORE first target placement" test -f "$state/icon-adoption"
check "  #139 direct undo restores KDE breeze (no stale Adwaita) and GTK breeze (no Papirus-Dark)" run undo-139 "$project/uninstall.sh"
check "  #139 post-undo KDE and GTK match pre-adoption breeze exactly" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    [[ -z $(kreadconfig6 --file "$1/kdedefaults/kdeglobals" --group Icons --key Theme 2>/dev/null || true) ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"breeze\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"breeze\"" "$1/xsettingsd/xsettingsd.conf"
' _ "$config" "$home"
check "  #139 no state record left" no_record_left

fresh "#140 install refuses unfinished undo across all 3 boundaries (mid-restore, phase=restored, post-archive manifest)"
# Boundary 1: kill undo after merged GTK 3 published (phase=restoring)
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "install on active Platinum exits 0" run inst-140a "$project/install.sh"
fail_140_gtk4=$root/fail-140-gtk4
mkdir -p "$fail_140_gtk4"
cat > "$fail_140_gtk4/mv" << 'STUB'
#!/bin/bash
if [[ $1 == -T && $3 == */gtk-4.0/settings.ini ]]; then
    exit 1
fi
exec /usr/bin/mv "$@"
STUB
chmod +x "$fail_140_gtk4/mv"
if run undo-140a-mid env PATH="$fail_140_gtk4:$PATH" "$project/uninstall.sh"; then
    fail "#140 boundary 1 undo stops mid-restore"
else
    pass "#140 boundary 1 undo stops mid-restore"
fi
before_140a=$(snapshot)
if run inst-140a-refused "$project/install.sh"; then
    fail "#140 install refuses during phase=restoring"
else
    pass "#140 install refuses during phase=restoring"
fi
check "  #140 boundary 1 refused install changed nothing" same "$before_140a" "$(snapshot)"
check "  #140 boundary 1 resuming uninstall finishes cleanly" run undo-140a-finish "$project/uninstall.sh"
check "  #140 boundary 1 no state left" no_record_left

# Boundary 2: kill undo after phase=restored saved, BEFORE icon-adoption archived
fresh "#140b install refuses after phase=restored saved before archive, and fresh install carries no stale decision"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "install exits 0" run inst-140b "$project/install.sh"
fail_140_arch=$root/fail-140-arch
mkdir -p "$fail_140_arch"
cat > "$fail_140_arch/mv" << 'STUB'
#!/bin/bash
if [[ $1 == -T && $2 == */icon-adoption && $3 == */icon-adoption ]]; then
    exit 1
fi
exec /usr/bin/mv "$@"
STUB
chmod +x "$fail_140_arch/mv"
if run undo-140b-stop env PATH="$fail_140_arch:$PATH" "$project/uninstall.sh"; then
    fail "#140 boundary 2 undo stops after phase=restored before archive"
else
    pass "#140 boundary 2 undo stops after phase=restored before archive"
fi
if run inst-140b-refused "$project/install.sh"; then
    fail "#140 install refuses when phase=restored and uninstall unfinished"
else
    pass "#140 install refuses when phase=restored and uninstall unfinished"
fi
check "  #140 boundary 2 resuming uninstall finishes cleanly" run undo-140b-finish "$project/uninstall.sh"
check "  #140 boundary 2 no state left" no_record_left

# Boundary 3: kill undo immediately AFTER backup + icon-adoption archived, while old manifest & packages remain!
fresh "#140c install refuses after icon-adoption archived while manifest remains; after uninstall finishes, fresh install works"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "install exits 0" run inst-140c "$project/install.sh"
fail_140_rm=$root/fail-140-rm
mkdir -p "$fail_140_rm"
cat > "$fail_140_rm/rm" <<'STUB'
#!/usr/bin/env bash
for arg in "$@"; do
    if [[ $arg == *Platinum.colors ]]; then
        exit 1
    fi
done
exec /usr/bin/rm "$@"
STUB
chmod +x "$fail_140_rm/rm"
if run undo-140c-stop env PATH="$fail_140_rm:$PATH" "$project/uninstall.sh"; then
    fail "#140 boundary 3 undo stops in section 2 after journal archival"
else
    pass "#140 boundary 3 undo stops in section 2 after journal archival"
fi
check "  #140 boundary 3 backup and icon-adoption are archived while manifest and uninstall-in-progress remain" bash -c '
    test ! -e "$1/backup" &&
    test ! -e "$1/icon-adoption" &&
    test -f "$1/installed" &&
    test -f "$1/uninstall-in-progress"
' _ "$state"
if run inst-140c-refused "$project/install.sh"; then
    fail "#140 install refuses when uninstall-in-progress remains after journal archival"
else
    pass "#140 install refuses when uninstall-in-progress remains after journal archival"
fi
check "  #140 boundary 3 resuming uninstall retires manifest and marker" run undo-140c-finish "$project/uninstall.sh"
check "  #140 boundary 3 no state left" no_record_left
# Now a brand-new install on active Platinum captures fresh preferences and selects WhiteSur-lavender cleanly!
kwriteconfig6 --file "$config/kdeglobals" --group KDE --key LookAndFeelPackage platinum.desktop
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
check "  #140 boundary 3 fresh install after completed undo succeeds and selects WhiteSur-lavender" run inst-140c-fresh "$project/install.sh"
check "  #140 boundary 3 fresh install has new restore_decision=none and WhiteSur-lavender selected" bash -c '
    [[ $(python3 -I "$1/scripts/icon_prefs.py" read-restore-decision "$2/icon-adoption") == none ]] &&
    [[ $(kreadconfig6 --file "$3/kdedefaults/kdeglobals" --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$project" "$state" "$config"
check "  #140 boundary 3 undo exits 0" run undo-140c-done "$project/uninstall.sh"

fresh "#141 pending selection (captured AND selecting) cancels cleanly if user switched away from Platinum"
# Case A: killed after phase=captured -> user switches global theme to Breeze + breeze icons -> retry keeps Breeze!
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
if run inst-141a-fail env PATH="$fail_bin:$PATH" M9_FAIL_ICON_TARGET="$data/icons/WhiteSur-lavender" "$project/install.sh"; then
    fail "#141a install stops while phase=captured"
else
    pass "#141a install stops while phase=captured"
fi
kwriteconfig6 --file "$config/kdeglobals" --group KDE --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
check "#141a retry after switching away from Platinum exits 0" run inst-141a-retry "$project/install.sh"
check "  #141a global theme stays Breeze, icons stay breeze (NOT WhiteSur-lavender), and phase=skipped" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group KDE --key LookAndFeelPackage) == org.kde.breeze.desktop ]] &&
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini" &&
    python3 -I -c "import json, sys; assert json.load(open(sys.argv[1]))[\"phase\"] == \"skipped\"" "$2/icon-adoption"
' _ "$config" "$state"
check "  #141a undo exits 0" run undo-141a "$project/uninstall.sh"

# Case B: killed during phase=selecting (KDE + GTK 3 switched to Lavender, GTK 4 failed read-only) ->
# user switches global theme to Breeze and sets KDE to Adwaita (leaving GTK 3 at partial Lavender) ->
# retry keeps user's Adwaita in KDE, rolls back partial GTK 3 Lavender to breeze, and sets phase=skipped!
fresh "#141b partial selecting phase reconciles transaction-owned writes and preserves later user choice on Breeze"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
chmod 500 "$config/gtk-4.0"
if run inst-141b-fail "$project/install.sh"; then
    fail "#141b install stops during phase=selecting"
else
    pass "#141b install stops during phase=selecting"
fi
chmod 700 "$config/gtk-4.0"
kwriteconfig6 --file "$config/kdeglobals" --group KDE --key LookAndFeelPackage org.kde.breeze.desktop
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme Adwaita
check "#141b retry after switching to Breeze + Adwaita exits 0" run inst-141b-retry "$project/install.sh"
check "  #141b KDE keeps user Adwaita, partial GTK 3 rolled back to breeze, GTK 4 stays breeze, phase=skipped" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group KDE --key LookAndFeelPackage) == org.kde.breeze.desktop ]] &&
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == Adwaita ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini" &&
    python3 -I -c "import json, sys; assert json.load(open(sys.argv[1]))[\"phase\"] == \"skipped\"" "$2/icon-adoption"
' _ "$config" "$state"
check "  #141b undo exits 0" run undo-141b "$project/uninstall.sh"

fresh "#127 incomplete outside copy (index.theme only, zero advertised artwork dirs) cannot authorize deleting managed trio"
check "real-size install exits 0" run inst-127b env M9_PREBUILT="$M9_PREBUILT_REAL" "$project/install.sh"
mkdir -p "$home/.icons/WhiteSur-lavender"
cp "$data/icons/WhiteSur-lavender/index.theme" "$home/.icons/WhiteSur-lavender/index.theme"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme WhiteSur-lavender
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=WhiteSur-lavender\n' > "$config/gtk-3.0/settings.ini"
if run undo-127b "$project/uninstall.sh"; then
    fail "#127 incomplete outside copy (index.theme only) is rejected"
else
    pass "#127 incomplete outside copy (index.theme only) is rejected"
fi
check "  #127 managed base and its real Lavender folder.svg stayed intact" test -f "$data/icons/WhiteSur-lavender/places/scalable/folder.svg"
kwriteconfig6 --file "$config/kdeglobals" --group Icons --key Theme breeze
sed -i 's/WhiteSur-lavender/breeze/g' "$config/gtk-3.0/settings.ini"
check "  #127 retry after switching away exits 0" run undo-127b-done "$project/uninstall.sh"
check "  #127 all three managed icon dirs removed" icons_absent "$data"

fresh "#131 legacy 0644 backup does not widen pre-adoption 0600 permissions on undo (even when backed-up key already matches)"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=WhiteSur\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="Papirus-Dark"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "Papirus-Dark"\n' > "$config/xsettingsd/xsettingsd.conf"
chmod 644 "$config/kdeglobals" "$config/gtk-3.0/settings.ini" "$config/gtk-4.0/settings.ini" "$home/.gtkrc-2.0" "$config/xsettingsd/xsettingsd.conf"
has_acl=0
if command -v setfacl >/dev/null && setfacl -m u:0:r-- "$config/gtk-4.0/settings.ini" 2>/dev/null; then
    has_acl=1
fi
check "HEAD install --apply creates 0644 legacy backup" run head-131b env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh" --apply
check "  legacy backup gtk-3.0 is 0644 and gtk-4.0 is group/world readable" bash -c '
    [[ $(stat -c "%a" "$1/backup/config/gtk-3.0/settings.ini") == 644 ]] &&
    [[ $(stat -c "%a" "$1/backup/config/gtk-4.0/settings.ini") == 644 ]]
' _ "$state"
# Before adopting, user has breeze across KDE & GTK and hardened all 5 files to 0600
# (clearing any legacy ACL on gtk-4.0 and adding a custom pre-adoption ACL on xsettingsd.conf).
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
printf 'gtk-icon-theme-name="breeze"\n' > "$home/.gtkrc-2.0"
printf 'Net/IconThemeName "breeze"\n' > "$config/xsettingsd/xsettingsd.conf"
if ((has_acl)); then
    setfacl -b "$config/gtk-4.0/settings.ini" "$config/xsettingsd/xsettingsd.conf"
fi
chmod 600 "$config/kdeglobals" "$config/gtk-3.0/settings.ini" "$config/gtk-4.0/settings.ini" "$home/.gtkrc-2.0" "$config/xsettingsd/xsettingsd.conf"
if ((has_acl)); then
    setfacl -m u:0:r-- "$config/xsettingsd/xsettingsd.conf"
fi
check "plain upgrade exits 0" run upg-131b "$project/install.sh"
check "  pre-adoption 0600 modes and ACL stayed intact after upgrade" bash -c '
    for f in "$1/kdeglobals" "$1/gtk-3.0/settings.ini" "$1/gtk-4.0/settings.ini" "$2/.gtkrc-2.0"; do
        [[ $(stat -c "%a" "$f") == 600 ]] || { echo "upgrade mode of $f is $(stat -c %a "$f")"; exit 1; }
    done
    if [[ $3 == 1 ]]; then
        getfacl -p "$1/xsettingsd/xsettingsd.conf" | grep -qx "user:root:r--" || exit 1
        ! getfacl -p "$1/gtk-4.0/settings.ini" | grep -q "^user:root:"
    else
        [[ $(stat -c "%a" "$1/xsettingsd/xsettingsd.conf") == 600 ]]
    fi
' _ "$config" "$home" "$has_acl"
check "plain update exits 0" run upd-131b "$project/install.sh"
check "uninstall exits 0" run undo-131b "$project/uninstall.sh"
check "  all 5 files restored to breeze AND kept pre-adoption 0600 + ACL despite 0644 legacy backup (#131)" bash -c '
    [[ $(kreadconfig6 --file "$1/kdeglobals" --group Icons --key Theme) == breeze ]] &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-3.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=breeze" "$1/gtk-4.0/settings.ini" &&
    grep -qx "gtk-icon-theme-name=\"breeze\"" "$2/.gtkrc-2.0" &&
    grep -qx "Net/IconThemeName \"breeze\"" "$1/xsettingsd/xsettingsd.conf" &&
    for f in "$1/kdeglobals" "$1/gtk-3.0/settings.ini" "$1/gtk-4.0/settings.ini" "$2/.gtkrc-2.0"; do
        [[ $(stat -c "%a" "$f") == 600 ]] || { echo "undo mode of $f is $(stat -c %a "$f")"; exit 1; }
    done
    if [[ $3 == 1 ]]; then
        getfacl -p "$1/xsettingsd/xsettingsd.conf" | grep -qx "user:root:r--" || { echo "missing ACL on xsettingsd.conf"; exit 1; }
        ! getfacl -p "$1/gtk-4.0/settings.ini" | grep -q "^user:root:" || { echo "stale legacy ACL on gtk-4.0"; exit 1; }
    else
        [[ $(stat -c "%a" "$1/xsettingsd/xsettingsd.conf") == 600 ]]
    fi
' _ "$config" "$home" "$has_acl"
check "  repeated uninstall exits 0 and keeps 0600 + ACL" run undo-131b-2 "$project/uninstall.sh"
check "  all 5 files still 0600 + ACL after repeated uninstall" bash -c '
    for f in "$1/kdeglobals" "$1/gtk-3.0/settings.ini" "$1/gtk-4.0/settings.ini" "$2/.gtkrc-2.0"; do
        [[ $(stat -c "%a" "$f") == 600 ]] || exit 1
    done
    if [[ $3 == 1 ]]; then
        getfacl -p "$1/xsettingsd/xsettingsd.conf" | grep -qx "user:root:r--" || exit 1
        ! getfacl -p "$1/gtk-4.0/settings.ini" | grep -q "^user:root:"
    else
        [[ $(stat -c "%a" "$1/xsettingsd/xsettingsd.conf") == 600 ]]
    fi
' _ "$config" "$home" "$has_acl"

fresh "#142a selecting inherited KDE icon theme under real XDG_CONFIG_DIRS leaves no Theme[\$d] marker"
mkdir -p "$config/kdedefaults"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\nForceFontDPI=96\n' > "$config/kdeglobals"
printf '[Icons]\nTheme=breeze\n' > "$config/kdedefaults/kdeglobals"
chmod 600 "$config/kdeglobals" "$config/kdedefaults/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "#142a plain install exits 0 under real XDG_CONFIG_DIRS cascade" run inst-142a "$project/install.sh"
check "  #142a kdeglobals has no Theme[\$d] marker, keeps ForceFontDPI=96 and mode 0600, and real cascade reads WhiteSur-lavender" bash -c '
    ! grep -Eq "^Theme([[:space:]]*=|\[\$)" "$1/kdeglobals" &&
    grep -qx "ForceFontDPI=96" "$1/kdeglobals" &&
    [[ $(stat -c "%a" "$1/kdeglobals") == 600 ]] &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$config"
check "  #142a undo restores breeze cleanly under real XDG_CONFIG_DIRS cascade" run undo-142a "$project/uninstall.sh"
check "  #142a real cascade reads breeze after undo and no Theme[\$d]" bash -c '
    ! grep -q "Theme\[\$d\]" "$1/kdeglobals" &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == breeze ]]
' _ "$config"

fresh "#142b restoring an inherited pre-adoption KDE icon theme over a legacy explicit backup leaves no Theme[\$d] marker"
printf '[KDE]\nLookAndFeelPackage=org.kde.breeze.desktop\n[Icons]\nTheme=WhiteSur\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=Papirus-Dark\n' > "$config/gtk-4.0/settings.ini"
check "HEAD install --apply creates legacy explicit-Theme backup" run head-142b env M9_PREBUILT="$no_icon_prebuilt" "$head_project/install.sh" --apply
# Before upgrading, user has Platinum active with INHERITED breeze (no Theme= in kdeglobals, Theme=breeze in kdedefaults).
mkdir -p "$config/kdedefaults"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n' > "$config/kdeglobals"
printf '[Icons]\nTheme=breeze\n' > "$config/kdedefaults/kdeglobals"
chmod 600 "$config/kdeglobals" "$config/kdedefaults/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "#142b plain upgrade exits 0" run upg-142b "$project/install.sh"
check "  #142b real cascade reads WhiteSur-lavender with no Theme[\$d]" bash -c '
    ! grep -Eq "^Theme([[:space:]]*=|\[\$)" "$1/kdeglobals" &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$config"
check "#142b uninstall exits 0" run undo-142b "$project/uninstall.sh"
check "  #142b restored inherited breeze has NO Theme[\$d] marker and real cascade reads breeze" bash -c '
    ! grep -Eq "^Theme([[:space:]]*=|\[\$)" "$1/kdeglobals" &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == breeze ]] &&
    [[ $(stat -c "%a" "$1/kdeglobals") == 600 ]]
' _ "$config"

fresh "#142c existing install with stale Theme[\$d] marker is repaired by plain update, --apply, and direct undo"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\nForceFontDPI=96\n' > "$config/kdeglobals"
chmod 600 "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "#142c initial install exits 0 (phase=selected)" run inst-142c "$project/install.sh"
# Inject the exact stale Theme[$d] marker left by older kwriteconfig6 --delete on live install.
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n\n[Icons]\nForceFontDPI=96\nTheme[$d]\n' > "$config/kdeglobals"
chmod 600 "$config/kdeglobals"
check "  #142c before repair, real XDG_CONFIG_DIRS cascade is hidden (empty)" bash -c '
    [[ -z $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) ]]
' _ "$config"
before_142c=$(snapshot)
check "  #142c --dry-run plans removing stale Theme[\$d] without changing home" bash -c '
    "$1/install.sh" --dry-run > "$2" 2>&1 &&
    grep -Fq "Theme[\$d]" "$2"
' _ "$project" "$root/dry-142c.log"
check "  #142c --dry-run changed nothing" same "$before_142c" "$(snapshot)"
check "#142c plain update repairs stale Theme[\$d] marker" run upd-142c "$project/install.sh"
check "  #142c after plain update, real cascade reads WhiteSur-lavender, ForceFontDPI=96 and mode 0600 preserved" bash -c '
    ! grep -q "Theme\[\$d\]" "$1/kdeglobals" &&
    grep -qx "ForceFontDPI=96" "$1/kdeglobals" &&
    [[ $(stat -c "%a" "$1/kdeglobals") == 600 ]] &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$config"
# Also verify install.sh --apply heals a stale Theme[$d] marker.
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n\n[Icons]\nForceFontDPI=96\nTheme[$d]\n' > "$config/kdeglobals"
chmod 600 "$config/kdeglobals"
check "#142c --apply also heals stale Theme[\$d] marker" run app-142c "$project/install.sh" --apply
check "  #142c after --apply, real cascade reads WhiteSur-lavender with no Theme[\$d]" bash -c '
    ! grep -q "Theme\[\$d\]" "$1/kdeglobals" &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$config"
# Also verify direct uninstall from stale Theme[$d] state restores breeze cleanly.
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n\n[Icons]\nForceFontDPI=96\nTheme[$d]\n' > "$config/kdeglobals"
chmod 600 "$config/kdeglobals"
check "#142c direct uninstall from stale Theme[\$d] exits 0" run undo-142c "$project/uninstall.sh"
check "  #142c after direct undo, real cascade reads breeze with no Theme[\$d]" bash -c '
    ! grep -q "Theme\[\$d\]" "$1/kdeglobals" &&
    [[ $(XDG_CONFIG_HOME="$1" XDG_CONFIG_DIRS="$1/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == breeze ]]
' _ "$config"

fresh "#143 normal user-owned symlinked ~/.cache works end-to-end; unsafe/foreign ~/.cache symlink refused"
storage_143=$root/storage-143/local/cache
rm -rf "$root/storage-143"
mkdir -p "$storage_143"
chmod 700 "$storage_143"
rm -rf "$home/.cache"
ln -s "$storage_143" "$home/.cache"
printf '[KDE]\nLookAndFeelPackage=platinum.desktop\n[Icons]\nTheme=breeze\n' > "$config/kdeglobals"
printf '[Settings]\ngtk-theme-name=Breeze\ngtk-icon-theme-name=breeze\n' > "$config/gtk-3.0/settings.ini"
printf '[Settings]\ngtk-icon-theme-name=breeze\n' > "$config/gtk-4.0/settings.ini"
check "#143 real-source install with XDG_CACHE_HOME unset and symlinked ~/.cache exits 0" run inst-143 env -u XDG_CACHE_HOME M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="$M9_TEST_REMOTE" "$project/install.sh"
check "  #143 cache populated inside symlink target and WhiteSur-lavender installed + selected" bash -c '
    test -d "$1/macos9-theme/WhiteSur-icon-theme/objects" &&
    test -f "$2/icons/WhiteSur-lavender/places/scalable/folder.svg" &&
    [[ $(XDG_CONFIG_HOME="$3" XDG_CONFIG_DIRS="$3/kdedefaults:/etc/xdg" kreadconfig6 --file kdeglobals --group Icons --key Theme) == WhiteSur-lavender ]]
' _ "$storage_143" "$data" "$config"
check "  #143 offline update reuses cache through symlinked ~/.cache" run upd-143 env -u XDG_CACHE_HOME M9_PREBUILT="$no_icon_prebuilt" M9_WHITESUR_REMOTE="file:///nonexistent-offline" "$project/install.sh"
check "  #143 undo exits 0 and restores breeze" run undo-143 "$project/uninstall.sh"
check "  #143 unsafe world-writable ~/.cache symlink refused without changing home" bash -c '
    ww="$1/ww-cache-143"
    rm -rf "$ww"
    mkdir -p "$ww"
    chmod 777 "$ww"
    rm -f "$2/.cache"
    ln -s "$ww" "$2/.cache"
    ! env -u XDG_CACHE_HOME M9_PREBUILT="$3" M9_WHITESUR_REMOTE="$4" "$5/install.sh" > "$1/err-143-ww.log" 2>&1 &&
    grep -Fq "world-writable" "$1/err-143-ww.log"
' _ "$root" "$home" "$no_icon_prebuilt" "$M9_TEST_REMOTE" "$project"
check "  #143 foreign-owned (/etc) ~/.cache symlink refused" bash -c '
    rm -f "$2/.cache"
    ln -s /etc "$2/.cache"
    ! env -u XDG_CACHE_HOME M9_PREBUILT="$3" M9_WHITESUR_REMOTE="$4" "$5/install.sh" > "$1/err-143-etc.log" 2>&1
' _ "$root" "$home" "$no_icon_prebuilt" "$M9_TEST_REMOTE" "$project"

fresh "terminal palette upgrade and selected profiles"
palette_source=$project/extras/terminal/PlatinumLavender.colorscheme
legacy=$root/pre-terminal-project
mkdir -p "$legacy/scripts"
for name in install.sh scripts/common.sh; do
    git -C "$project" show "f1d6045:$name" > "$legacy/$name"
done
for name in scripts/icon_prefs.py scripts/manifest_ops.py colors cursors icons plasma wallpapers; do
    ln -sfn "$project/$name" "$legacy/$name"
done
check "pre-palette install exits 0" run pre-palette bash "$legacy/install.sh"
check "pre-palette install has 15 recorded targets" test "$(grep -cE '^(file|dir|link)' "$state/installed")" -eq 15
check "upgrade installs the terminal palette" run palette-upgrade "$project/install.sh"
check "upgraded palette matches its source" cmp "$palette_source" "$terminal_palette"
mkdir -p "$data/konsole"
printf '[Appearance]\nColorScheme=konsole:PlatinumLavender.colorscheme\n' > "$config/kwiterminalrc"
printf '[Appearance]\nColorScheme=PlatinumLavender\n' > "$data/konsole/Personal.profile"
before=$(snapshot)
check "dry run warns about Kwi" run terminal-dry "$project/uninstall.sh" --dry-run
check "dry run names Kwi's selected scheme" grep -Fq 'still selected in Kwi' "$root/$n-terminal-dry.log"
check "terminal dry run changes nothing" same "$before" "$(snapshot)"
check "uninstall waits while Kwi selects the palette" bash -c '! "$1"' _ "$project/uninstall.sh"
check "selected terminal palette is kept" cmp "$palette_source" "$terminal_palette"
check "Kwi's selection persists" grep -qx 'ColorScheme=konsole:PlatinumLavender.colorscheme' "$config/kwiterminalrc"
kwriteconfig6 --file "$config/kwiterminalrc" --group Appearance --key ColorScheme system
check "retry waits while Konsole selects the palette" bash -c '! "$1"' _ "$project/uninstall.sh"
check "Konsole profile's selection persists" grep -qx 'ColorScheme=PlatinumLavender' "$data/konsole/Personal.profile"
kwriteconfig6 --file "$data/konsole/Personal.profile" --group Appearance --key ColorScheme Breeze
check "retry removes the unselected palette" run terminal-retry "$project/uninstall.sh"
check "unselected palette is gone" test ! -e "$terminal_palette"
check "Konsole profile is preserved" grep -qx 'ColorScheme=Breeze' "$data/konsole/Personal.profile"
check "terminal retry removes the install record" no_record_left

fresh "terminal palette selection with a restorable original"
mkdir -p "$data/konsole"
cp "$palette_source" "$terminal_palette"
printf '\n# pre-existing copy\n' >> "$terminal_palette"
original_palette=$(sha256sum "$terminal_palette")
printf '[Appearance]\nColorScheme=konsole:PlatinumLavender.colorscheme\n' > "$config/kwiterminalrc"
check "install displaces the previous terminal palette" run terminal-install "$project/install.sh"
check "uninstall restores a selected compatible original" run terminal-restore "$project/uninstall.sh"
check "original palette restored byte for byte" same "$original_palette" "$(sha256sum "$terminal_palette")"


echo
if ((failed)); then
    echo "test-install: $failed FAILED, $passed passed (logs in $root)"
    exit 1
fi
echo "test-install: all $passed passed (logs in $root)"
