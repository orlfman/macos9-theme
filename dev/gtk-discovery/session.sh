#!/bin/bash
# Invoked exclusively by dev/gtk-discovery.sh inside its disposable HOME,
# XDG directories, and private D-Bus session.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
umask 022

mode=$1
cd "$ROOT"

# --- 0. Verify isolation BEFORE writing any settings ------------------------
{
    [[ $HOME == "$ROOT/home" ]] || { echo "ISOLATION=FAIL reason=HOME"; exit 1; }
    [[ $XDG_CONFIG_HOME == "$HOME/.config" ]] || { echo "ISOLATION=FAIL reason=XDG_CONFIG_HOME"; exit 1; }
    [[ $XDG_DATA_HOME == "$HOME/.local/share" ]] || { echo "ISOLATION=FAIL reason=XDG_DATA_HOME"; exit 1; }
    [[ $XDG_CACHE_HOME == "$HOME/.cache" ]] || { echo "ISOLATION=FAIL reason=XDG_CACHE_HOME"; exit 1; }
    [[ $XDG_STATE_HOME == "$HOME/.local/state" ]] || { echo "ISOLATION=FAIL reason=XDG_STATE_HOME"; exit 1; }
    [[ $XDG_CONFIG_DIRS == "$XDG_CONFIG_HOME/kdedefaults:/etc/xdg" ]] || { echo "ISOLATION=FAIL reason=XDG_CONFIG_DIRS"; exit 1; }
    [[ $XDG_DATA_DIRS == "/usr/local/share:/usr/share" ]] || { echo "ISOLATION=FAIL reason=XDG_DATA_DIRS"; exit 1; }
    [[ -d $XDG_RUNTIME_DIR && $XDG_RUNTIME_DIR == "$RUNTIME" ]] || { echo "ISOLATION=FAIL reason=XDG_RUNTIME_DIR"; exit 1; }
    [[ -n ${DBUS_SESSION_BUS_ADDRESS:-} ]] || { echo "ISOLATION=FAIL reason=DBUS"; exit 1; }
    [[ ! -e $XDG_CONFIG_HOME/dconf/user ]] || { echo "ISOLATION=FAIL reason=preexisting-dconf"; exit 1; }

    gsettings set org.gnome.desktop.interface gtk-theme DiscoveryDconf
    got=$(gsettings get org.gnome.desktop.interface gtk-theme)
    [[ $got == "'DiscoveryDconf'" ]] || { echo "ISOLATION=FAIL reason=dconf-readback($got)"; exit 1; }
    [[ -s $XDG_CONFIG_HOME/dconf/user ]] || { echo "ISOLATION=FAIL reason=dconf-file-missing"; exit 1; }
    gsettings reset org.gnome.desktop.interface gtk-theme
    got_reset=$(gsettings get org.gnome.desktop.interface gtk-theme)
    echo "ISOLATION=PASS dconf_file=$XDG_CONFIG_HOME/dconf/user reset_value=$got_reset"
} > isolation.log

# --- 1. Create distinct named themes and layer stylesheets ------------------
make_theme() { # name probe_hex ind_hex
    local name=$1 phex=$2 ihex=$3 ver dir
    for ver in 3 4; do
        dir="$XDG_DATA_HOME/themes/$name/gtk-$ver.0"
        mkdir -p "$dir"
        cat > "$dir/gtk.css" << EOF
#probe { color: $phex; }
#ind-theme { color: $ihex; }
EOF
    done
}

make_theme DiscoveryIni           "#112233" "#11aa33"
make_theme DiscoveryGSettings     "#223344" "#22bb44"
make_theme DiscoveryGSettingsLive "#334455" "#33cc55"
make_theme DiscoveryXSettings     "#445566" "#44dd66"
make_theme DiscoveryKde           "#123456" "#1188ee"

cat > app.css << 'EOF'
#probe { color: #654321; }
#ind-app { color: #ee8811; }
EOF

cat > user.css << 'EOF'
#probe { color: #abcdef; }
#ind-user { color: #cc11aa; }
EOF

mkdir -p "$XDG_CONFIG_HOME/gtk-3.0" "$XDG_CONFIG_HOME/gtk-4.0"

cleanup_pids=()
cleanup() {
    local p
    for p in "${cleanup_pids[@]:-}"; do
        kill "$p" 2>/dev/null || true
    done
    kill $(jobs -pr) 2>/dev/null || true
}
trap cleanup EXIT

if [[ $mode == broadway ]]; then
    export GDK_BACKEND=broadway
    export GSK_RENDERER=cairo
    export QT_QPA_PLATFORM=offscreen
    broadwayd -u "$XDG_RUNTIME_DIR/http3" :3 > broadway3.log 2>&1 &
    cleanup_pids+=($!)
    gtk4-broadwayd -u "$XDG_RUNTIME_DIR/http4" :4 > broadway4.log 2>&1 &
    cleanup_pids+=($!)
    sleep 0.5
else
    export GDK_BACKEND=wayland
    export GSK_RENDERER=cairo
    export QT_QPA_PLATFORM=wayland
    dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM
fi

clear_gtk_state() {
    rm -f "$XDG_CONFIG_HOME/gtk-3.0/settings.ini" \
          "$XDG_CONFIG_HOME/gtk-4.0/settings.ini" \
          "$XDG_CONFIG_HOME/gtk-3.0/gtk.css" \
          "$XDG_CONFIG_HOME/gtk-4.0/gtk.css" \
          "$XDG_CONFIG_HOME/gtk-3.0/colors.css" \
          "$XDG_CONFIG_HOME/gtk-4.0/colors.css" \
          "$XDG_CONFIG_HOME/xsettingsd/xsettingsd.conf" \
          "$HOME/.gtkrc-2.0"
    unset PROBE_APP_CSS || true
    gsettings reset org.gnome.desktop.interface gtk-theme
    gsettings reset org.gnome.desktop.interface color-scheme
    gsettings reset org.gnome.desktop.a11y.interface high-contrast
}

run_trial() { # trial_name
    local trial=$1 stack
    for stack in gtk3 gtk4 adw; do
        if [[ $mode == broadway ]]; then
            if [[ $stack == gtk3 ]]; then
                export BROADWAY_DISPLAY=:3
            else
                export BROADWAY_DISPLAY=:4
            fi
        fi
        printf 'trial=%s ' "$trial" >> results.log
        "./$stack" "$trial-$stack.png" >> results.log
    done
}

snapshot_kde_files() { # out_file
    local out=$1 f
    {
        echo "=== LOOK AND FEEL ==="
        echo "kdedefaults_package=$(cat "$XDG_CONFIG_HOME/kdedefaults/package" 2>/dev/null || echo ABSENT)"
        echo "kreadconfig_lnf=$(kreadconfig6 --group KDE --key LookAndFeelPackage 2>/dev/null || echo ABSENT)"
        echo "=== PATHS AND SYMLINKS ==="
        for f in "$XDG_CONFIG_HOME/gtk-3.0" "$XDG_CONFIG_HOME/gtk-4.0" \
                 "$XDG_CONFIG_HOME/xsettingsd" "$HOME/.gtkrc-2.0" \
                 "$XDG_CONFIG_HOME/kdeglobals" "$XDG_CONFIG_HOME/kdedefaults"; do
            if [[ -e $f || -L $f ]]; then
                find "$f" -maxdepth 3 -printf '%y %m %p -> %l\n' 2>/dev/null | sort
            fi
        done
        echo "=== GSETTINGS ==="
        echo "gtk-theme=$(gsettings get org.gnome.desktop.interface gtk-theme 2>&1)"
        echo "color-scheme=$(gsettings get org.gnome.desktop.interface color-scheme 2>&1)"
        echo "accent-color=$(gsettings get org.gnome.desktop.interface accent-color 2>&1 || true)"
        echo "high-contrast=$(gsettings get org.gnome.desktop.a11y.interface high-contrast 2>&1)"
        echo "=== FILE CONTENTS ==="
        for f in "$XDG_CONFIG_HOME/gtk-3.0/settings.ini" \
                 "$XDG_CONFIG_HOME/gtk-3.0/gtk.css" \
                 "$XDG_CONFIG_HOME/gtk-3.0/colors.css" \
                 "$XDG_CONFIG_HOME/gtk-4.0/settings.ini" \
                 "$XDG_CONFIG_HOME/gtk-4.0/gtk.css" \
                 "$XDG_CONFIG_HOME/gtk-4.0/colors.css" \
                 "$XDG_CONFIG_HOME/xsettingsd/xsettingsd.conf" \
                 "$HOME/.gtkrc-2.0"; do
            if [[ -L $f ]]; then
                echo "--- $f (SYMLINK -> $(readlink -f "$f" 2>&1)) ---"
            elif [[ -f $f ]]; then
                echo "--- $f ($(stat -c '%a %sB' "$f")) ---"
                if [[ $f == */colors.css ]]; then
                    echo "lines=$(wc -l < "$f")"
                    head -10 "$f"
                else
                    cat "$f"
                    echo ""
                fi
            else
                echo "--- $f (ABSENT) ---"
            fi
        done
    } > "$out"
}

wait_for_platinum_colors() {
    local i
    for i in $(seq 1 25); do
        if grep -q '@define-color borders_breeze #b1b1b1;' "$XDG_CONFIG_HOME/gtk-3.0/colors.css" 2>/dev/null \
           && grep -q '@define-color borders_breeze #b1b1b1;' "$XDG_CONFIG_HOME/gtk-4.0/colors.css" 2>/dev/null; then
            sleep 0.3
            return 0
        fi
        sleep 0.15
    done
    return 0
}

# --- 2. Standalone per-store and per-layer trials ---------------------------
: > results.log
clear_gtk_state
run_trial stock

# Store A: settings.ini alone
clear_gtk_state
for ver in 3 4; do
    printf '[Settings]\ngtk-theme-name=DiscoveryIni\n' > "$XDG_CONFIG_HOME/gtk-$ver.0/settings.ini"
done
run_trial theme-ini

# Store B: GSettings alone (different theme name)
clear_gtk_state
gsettings set org.gnome.desktop.interface gtk-theme DiscoveryGSettings
run_trial theme-gsettings

# Store C: XSettings file alone (X11-only; confirms non-X11 backends ignore it)
clear_gtk_state
mkdir -p "$XDG_CONFIG_HOME/xsettingsd"
printf 'Net/ThemeName "DiscoveryXSettings"\n' > "$XDG_CONFIG_HOME/xsettingsd/xsettingsd.conf"
run_trial theme-xsettings

# Layer B: diagnostic application CSS provider alone
clear_gtk_state
export PROBE_APP_CSS="$ROOT/app.css"
run_trial app-only
unset PROBE_APP_CSS

# Layer C: disposable user gtk.css alone
clear_gtk_state
cp user.css "$XDG_CONFIG_HOME/gtk-3.0/gtk.css"
cp user.css "$XDG_CONFIG_HOME/gtk-4.0/gtk.css"
run_trial user-only

# Conflict 1: named theme vs diagnostic app CSS (separate indicators retained).
# Set both settings.ini (Broadway) and GSettings (Wayland) so the named theme
# loads on whichever display backend is active.
clear_gtk_state
for ver in 3 4; do
    printf '[Settings]\ngtk-theme-name=DiscoveryIni\n' > "$XDG_CONFIG_HOME/gtk-$ver.0/settings.ini"
done
gsettings set org.gnome.desktop.interface gtk-theme DiscoveryIni
export PROBE_APP_CSS="$ROOT/app.css"
run_trial conflict-theme-app
unset PROBE_APP_CSS

# Conflict 2: named theme vs diagnostic app CSS vs user gtk.css
clear_gtk_state
for ver in 3 4; do
    printf '[Settings]\ngtk-theme-name=DiscoveryIni\n' > "$XDG_CONFIG_HOME/gtk-$ver.0/settings.ini"
    cp user.css "$XDG_CONFIG_HOME/gtk-$ver.0/gtk.css"
done
gsettings set org.gnome.desktop.interface gtk-theme DiscoveryIni
export PROBE_APP_CSS="$ROOT/app.css"
run_trial conflict-all
unset PROBE_APP_CSS

# --- 3. KDE kded6 selection, global-theme reapply, and file inspection ------
clear_gtk_state
kded6 > kded.log 2>&1 &
kded_pid=$!
cleanup_pids+=($kded_pid)
kded_ready=0
for _ in $(seq 1 50); do
    if dbus-send --session --print-reply --dest=org.kde.kded6 /kded org.kde.kded6.loadedModules 2>/dev/null | grep -q '"gtkconfig"'; then
        kded_ready=1
        break
    fi
    sleep 0.15
done
echo "KDED_GTKCONFIG_LOADED=$kded_ready" > kded-status.log
sleep 0.8
snapshot_kde_files kde-files-before.log

# Select temporary named theme through KDE's GtkConfig
setgtk_rc=0
dbus-send --session --print-reply --dest=org.kde.GtkConfig /GtkConfig \
    org.kde.GtkConfig.setGtkTheme string:DiscoveryKde > setgtktheme.log 2>&1 || setgtk_rc=$?
echo "SETGTKTHEME_RC=$setgtk_rc" >> setgtktheme.log
sleep 1.0
snapshot_kde_files kde-files-selected.log
run_trial kde-selected

# Reapply Platinum global theme (colors + look-and-feel) with kded6 running.
# No synthetic KGlobalSettings signal: observe what plasma-apply-lookandfeel does on its own.
mkdir -p "$XDG_DATA_HOME/plasma/look-and-feel" "$XDG_DATA_HOME/color-schemes"
cp -R "$PROJECT/plasma/look-and-feel/platinum.desktop" "$XDG_DATA_HOME/plasma/look-and-feel/"
cp "$PROJECT/colors/Platinum.colors" "$XDG_DATA_HOME/color-schemes/"
lnf_rc=0
plasma-apply-lookandfeel -a platinum.desktop > lnf-apply.log 2>&1 || lnf_rc=$?
echo "LNF_APPLY_RC=$lnf_rc" >> lnf-apply.log
wait_for_platinum_colors
snapshot_kde_files kde-files-reapplied.log
run_trial kde-reapplied

# Also observe what happens if user gtk-4.0/gtk.css pre-existed before reapply
printf '/* user-owned gtk4 css */\n#ind-user { color: #aa4499; }\n#ind-app { color: @error_color_breeze; }\n' > "$XDG_CONFIG_HOME/gtk-4.0/gtk.css"
lnf2_rc=0
plasma-apply-lookandfeel -a platinum.desktop > lnf-reapply2.log 2>&1 || lnf2_rc=$?
echo "LNF_REAPPLY2_RC=$lnf2_rc" >> lnf-reapply2.log
wait_for_platinum_colors
sleep 0.8
snapshot_kde_files kde-files-reapplied-with-user-gtk4.log
run_trial kde-reapplied-user
# Restore KDE-only gtk-4.0/gtk.css before watcher / app trials
printf "@import 'colors.css';\n" > "$XDG_CONFIG_HOME/gtk-4.0/gtk.css"

# --- 4. Live preference changes on already-running apps + Portal checks -----
start_watchers() { # prefix
    local prefix=$1 stack
    watcher_pids=()
    for stack in gtk3 gtk4 adw; do
        rm -f "$ROOT/$prefix-$stack.ready"
        if [[ $mode == broadway ]]; then
            if [[ $stack == gtk3 ]]; then
                BROADWAY_DISPLAY=:3 "./$stack" --watch "$ROOT/$prefix-$stack.ready" "$ROOT/$prefix-$stack.log" "$ROOT/$prefix-final-$stack.png" &
            else
                BROADWAY_DISPLAY=:4 "./$stack" --watch "$ROOT/$prefix-$stack.ready" "$ROOT/$prefix-$stack.log" "$ROOT/$prefix-final-$stack.png" &
            fi
        else
            "./$stack" --watch "$ROOT/$prefix-$stack.ready" "$ROOT/$prefix-$stack.log" "$ROOT/$prefix-final-$stack.png" &
        fi
        watcher_pids+=($!)
        cleanup_pids+=($!)
    done
    for stack in gtk3 gtk4 adw; do
        for _ in $(seq 1 40); do
            [[ -f "$ROOT/$prefix-$stack.ready" ]] && break
            sleep 0.15
        done
    done
}

poll_watchers() {
    local p
    for p in "${watcher_pids[@]}"; do
        kill -USR1 "$p" 2>/dev/null || true
    done
    sleep 0.35
}

stop_watchers() {
    local p
    for p in "${watcher_pids[@]}"; do
        kill -TERM "$p" 2>/dev/null || true
    done
    for p in "${watcher_pids[@]}"; do
        wait "$p" 2>/dev/null || true
    done
}

if [[ $mode == broadway ]]; then
    {
        echo "PORTAL_MODE=BLOCKED_SANDBOX"
        echo "REASON=broadway mode has no Wayland compositor; run dev/gtk-discovery.sh plasma in a desktop terminal for virtual KWin + KDE/GTK Settings portal checks"
    } > portal.log

    # Test live GSettings changes reaching already-running Broadway fixtures
    initial_cs=$(gsettings get org.gnome.desktop.interface color-scheme)
    start_watchers watch-broadway
    {
        echo "=== STEP 1: GSettings gtk-theme=DiscoveryGSettingsLive ==="
        rc=0; gsettings set org.gnome.desktop.interface gtk-theme DiscoveryGSettingsLive || rc=$?
        echo "STEP1_RC=$rc"
        echo "gsettings_gtk_theme=$(gsettings get org.gnome.desktop.interface gtk-theme)"
        sleep 0.7
        poll_watchers

        echo "=== STEP 2: GSettings color-scheme=prefer-dark ==="
        rc=0; gsettings set org.gnome.desktop.interface color-scheme prefer-dark || rc=$?
        echo "STEP2_RC=$rc"
        echo "gsettings_color_scheme=$(gsettings get org.gnome.desktop.interface color-scheme)"
        sleep 0.7
        poll_watchers

        echo "=== STEP 3: GSettings high-contrast=true ==="
        rc=0; gsettings set org.gnome.desktop.a11y.interface high-contrast true || rc=$?
        echo "STEP3_RC=$rc"
        echo "gsettings_high_contrast=$(gsettings get org.gnome.desktop.a11y.interface high-contrast)"
        sleep 0.7
        poll_watchers

        echo "=== STEP 4: Return GSettings to baseline ==="
        rc=0
        gsettings set org.gnome.desktop.interface gtk-theme DiscoveryKde || rc=$?
        gsettings set org.gnome.desktop.interface color-scheme "$initial_cs" || rc=$?
        gsettings reset org.gnome.desktop.a11y.interface high-contrast || rc=$?
        echo "STEP4_RC=$rc"
        echo "gsettings_gtk_theme=$(gsettings get org.gnome.desktop.interface gtk-theme)"
        echo "gsettings_color_scheme=$(gsettings get org.gnome.desktop.interface color-scheme)"
        echo "gsettings_high_contrast=$(gsettings get org.gnome.desktop.a11y.interface high-contrast)"
        sleep 0.7
        poll_watchers
    } > broadway-trace.log
    stop_watchers
else
    # Verify BOTH KDE and GTK portal backends + frontend Settings API
    {
        echo "=== BACKEND CHECKS ==="
        for backend in kde gtk; do
            dest="org.freedesktop.impl.portal.desktop.$backend"
            echo "--- backend=$backend ---"
            if busctl --user call "$dest" /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings ReadAll as 0 > "portal-backend-$backend.out" 2>&1; then
                echo "BACKEND_${backend}_READALL=OK"
                head -30 "portal-backend-$backend.out"
            else
                echo "BACKEND_${backend}_READALL=FAIL"
                cat "portal-backend-$backend.out"
            fi
            owner=$(dbus-send --session --print-reply --dest=org.freedesktop.DBus / org.freedesktop.DBus.NameHasOwner "string:$dest" 2>&1 | grep -oE 'boolean (true|false)' || echo "unknown")
            echo "BACKEND_${backend}_OWNER=$owner"
        done
        echo "=== FRONTEND CHECK ==="
        if busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings ReadAll as 3 org.freedesktop.appearance org.gnome.desktop.interface org.gnome.desktop.a11y.interface > portal-frontend.out 2>&1; then
            echo "FRONTEND_READALL=OK"
            cat portal-frontend.out
        else
            echo "FRONTEND_READALL=FAIL"
            cat portal-frontend.out
        fi
    } > portal.log

    # Live preference propagation on already-running Wayland fixtures
    start_watchers watch-plasma
    {
        echo "=== STEP 0: Initial Platinum baseline ==="
        echo "kde_backend_cs=$(busctl --user call org.freedesktop.impl.portal.desktop.kde /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
        echo "frontend_cs=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
        echo "kde_backend_accent=$(busctl --user call org.freedesktop.impl.portal.desktop.kde /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
        echo "frontend_accent=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
        echo "gtk_backend_contrast=$(busctl --user call org.freedesktop.impl.portal.desktop.gtk /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        echo "frontend_contrast=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        echo "gsettings_gtk_theme=$(gsettings get org.gnome.desktop.interface gtk-theme 2>&1 || true)"

        echo "=== STEP 1: KDE BreezeDark color-scheme ==="
        rc=0; plasma-apply-colorscheme BreezeDark 2>&1 || rc=$?
        echo "STEP1_APPLY_RC=$rc"
        sleep 1.2
        echo "kde_backend_cs=$(busctl --user call org.freedesktop.impl.portal.desktop.kde /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
        echo "frontend_cs=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
        echo "kde_backend_accent=$(busctl --user call org.freedesktop.impl.portal.desktop.kde /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
        echo "frontend_accent=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
        poll_watchers

        echo "=== STEP 2: Platinum light color-scheme + accent ==="
        rc=0; plasma-apply-colorscheme Platinum 2>&1 || rc=$?
        echo "STEP2_APPLY_RC=$rc"
        sleep 1.2
        echo "kde_backend_cs=$(busctl --user call org.freedesktop.impl.portal.desktop.kde /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
        echo "frontend_cs=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
        echo "kde_backend_accent=$(busctl --user call org.freedesktop.impl.portal.desktop.kde /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
        echo "frontend_accent=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
        poll_watchers

        echo "=== STEP 3: High contrast ON (GTK portal backend) ==="
        rc=0; gsettings set org.gnome.desktop.a11y.interface high-contrast true 2>&1 || rc=$?
        echo "STEP3_RC=$rc"
        sleep 1.0
        echo "gtk_backend_contrast=$(busctl --user call org.freedesktop.impl.portal.desktop.gtk /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        echo "frontend_contrast=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        poll_watchers

        echo "=== STEP 4: High contrast OFF ==="
        rc=0; gsettings set org.gnome.desktop.a11y.interface high-contrast false 2>&1 || rc=$?
        echo "STEP4_RC=$rc"
        sleep 1.0
        echo "gtk_backend_contrast=$(busctl --user call org.freedesktop.impl.portal.desktop.gtk /org/freedesktop/portal/desktop org.freedesktop.impl.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        echo "frontend_contrast=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        poll_watchers

        echo "=== STEP 5: Live KDE setGtkTheme(DiscoveryGSettingsLive) ==="
        rc=0
        dbus-send --session --print-reply --dest=org.kde.GtkConfig /GtkConfig \
            org.kde.GtkConfig.setGtkTheme string:DiscoveryGSettingsLive >/dev/null 2>&1 || rc=$?
        echo "STEP5_RC=$rc"
        sleep 1.0
        echo "gsettings_gtk_theme=$(gsettings get org.gnome.desktop.interface gtk-theme 2>&1 || true)"
        poll_watchers

        echo "=== STEP 6: Return KDE setGtkTheme(DiscoveryKde) ==="
        rc=0
        dbus-send --session --print-reply --dest=org.kde.GtkConfig /GtkConfig \
            org.kde.GtkConfig.setGtkTheme string:DiscoveryKde >/dev/null 2>&1 || rc=$?
        echo "STEP6_RC=$rc"
        sleep 1.0
        echo "gsettings_gtk_theme=$(gsettings get org.gnome.desktop.interface gtk-theme 2>&1 || true)"
        poll_watchers
    } > portal-trace.log
    stop_watchers

    # Real-world application compatibility check: FFmpeg Converter GTK
    # Runs after Step 6 restored Platinum light + high-contrast=false + DiscoveryKde.
    if [[ -x /usr/bin/ffmpeg-converter-gtk ]]; then
        {
            echo "ACTIVE_GTK_THEME=$(gsettings get org.gnome.desktop.interface gtk-theme 2>&1 || true)"
            echo "ACTIVE_COLOR_SCHEME=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>&1 || true)"
            echo "ACTIVE_ACCENT=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance accent-color 2>&1 || true)"
            echo "ACTIVE_CONTRAST=$(busctl --user call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss org.freedesktop.appearance contrast 2>&1 || true)"
        } > ffmpeg.log
        /usr/bin/ffmpeg-converter-gtk >> ffmpeg.log 2>&1 &
        ff_pid=$!
        echo "FFMPEG_PID=$ff_pid" >> ffmpeg.log

        # Wait up to 6s for com.github.pieman.FFmpegConverterGTK to appear on D-Bus
        dbus_owner_pid=""
        for _ in $(seq 1 30); do
            out=$(busctl --user call org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus GetConnectionUnixProcessID s com.github.pieman.FFmpegConverterGTK 2>/dev/null || true)
            if [[ $out =~ ^u[[:space:]]+([0-9]+)$ ]]; then
                dbus_owner_pid=${BASH_REMATCH[1]}
                break
            fi
            sleep 0.2
        done
        echo "DBUS_OWNER_PID=${dbus_owner_pid:-NONE}" >> ffmpeg.log
        sleep 1.5

        if kill -0 "$ff_pid" 2>/dev/null; then
            # Query KWin's live window list via KWin Scripting so the capture is tied
            # to the mapped FFmpeg Converter GTK window (AUDIT.md #155).
            cat > "$ROOT/dump-windows.js" << 'JSEOF'
function reportActiveWindow() {
    var w = workspace.activeWindow;
    if (!w) return;
    var g = w.frameGeometry || {x: w.x, y: w.y, width: w.width, height: w.height};
    console.warn(
        "KWIN_WINDOW_INFO"
        + " pid=" + w.pid
        + " active=1"
        + " class=" + w.resourceClass
        + " desktop=" + w.desktopFileName
        + " x=" + Math.round(g.x)
        + " y=" + Math.round(g.y)
        + " w=" + Math.round(g.width)
        + " h=" + Math.round(g.height)
        + " uuid=" + w.internalId
        + " caption=" + JSON.stringify(w.caption)
    );
}
console.warn("KWIN_PROBE_READY");
workspace.windowActivated.connect(reportActiveWindow);
reportActiveWindow();
JSEOF
            {
                echo "=== KWIN WINDOW LIST ==="
                load_out=$(busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting loadScript ss "$ROOT/dump-windows.js" "macos9-gtk-discovery-dump" 2>&1 || true)
                echo "LOAD_SCRIPT=$load_out"
                if [[ $load_out =~ ^i[[:space:]]+([0-9]+)$ ]]; then
                    sid=${BASH_REMATCH[1]}
                    busctl --user call org.kde.KWin "/Scripting/Script${sid}" org.kde.kwin.Script run 2>&1 || true
                    for _ in {1..30}; do
                        grep -q "KWIN_WINDOW_INFO.*pid=${ff_pid} " "$ROOT/session.log" && break
                        sleep 0.1
                    done
                    busctl --user call org.kde.KWin /Scripting org.kde.kwin.Scripting unloadScript s "macos9-gtk-discovery-dump" 2>&1 || true
                fi
                grep -E 'KWIN_PROBE_READY|KWIN_WINDOW_INFO' "$ROOT/session.log" || true
                ff_uuid=$(grep "KWIN_WINDOW_INFO.*pid=${ff_pid} " "$ROOT/session.log" | sed -n 's/.*uuid=\([^ ]*\).*/\1/p' | tail -1 || true)
                echo "=== KWIN GETWINDOWINFO ==="
                if [[ -n $ff_uuid ]]; then
                    echo "FFMPEG_UUID=$ff_uuid"
                    busctl --user call org.kde.KWin /KWin org.kde.KWin getWindowInfo s "$ff_uuid" 2>&1 || true
                else
                    echo "FFMPEG_UUID=NONE"
                fi
            } > ffmpeg-window.log

            active_ok=0
            if timeout 15 spectacle -b -n -a -o "$ROOT/ffmpeg-active.png" >> ffmpeg.log 2>&1 && [[ -s "$ROOT/ffmpeg-active.png" ]]; then
                active_ok=1
            fi
            echo "FFMPEG_ACTIVE_CAPTURE=$active_ok" >> ffmpeg.log

            if timeout 15 spectacle -b -n -f -o "$ROOT/ffmpeg-plasma.png" >> ffmpeg.log 2>&1 && [[ -s "$ROOT/ffmpeg-plasma.png" ]]; then
                echo "FFMPEG_STATUS=PASS" >> ffmpeg.log
            else
                echo "FFMPEG_STATUS=FAIL reason=spectacle-failed" >> ffmpeg.log
            fi
            kill -TERM "$ff_pid" 2>/dev/null || true
            wait "$ff_pid" 2>/dev/null || true
        else
            echo "FFMPEG_STATUS=FAIL reason=exited-early" >> ffmpeg.log
        fi
    else
        echo "FFMPEG_STATUS=BLOCKED reason=not-installed" > ffmpeg.log
    fi
fi

echo "finished" > complete
