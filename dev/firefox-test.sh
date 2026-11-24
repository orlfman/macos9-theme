#!/bin/bash
# Runs Firefox inside a headless nested KWin (virtual Wayland backend, private
# D-Bus, isolated HOME and XDG folders, Platinum window decoration, Platinum
# GTK 3 theme, and a fresh throwaway Firefox profile) and screenshots the
# virtual screen into dev/shots/firefox-NAME.png.
#
# Never touches ~/.mozilla, ~/.config/mozilla, or the live desktop session.
#
# usage: dev/firefox-test.sh [NAME] [URL]
#   NAME                 output suffix -> dev/shots/firefox-NAME.png (default: test)
#   URL                  initial URL to open (default: about:blank)
#   M9_SIZE              virtual screen WxH (default: 1280x860)
#   M9_FF_WIN_SIZE       Firefox outer window WxH@X,Y (default: 1120x740@60,40)
#   M9_WAIT              seconds before screenshot in standalone mode (default: 5)
#   M9_DECORATION        KDecoration plugin id (default: platinum)
#   M9_GTK_THEME         GTK theme in sandbox (default: Platinum)
#   M9_FF_PROFILE        profile path (default: dev/build/firefox-profile)
#   M9_KEEP_PROFILE      1 = reuse existing M9_FF_PROFILE instead of wiping it
#   M9_USERCHROME        path to a userChrome.css file, a chrome/ folder, or
#                        "none" (default: firefox/chrome if present, else none)
#   M9_STYLESHEETS_PREF  true (default) or false (negative control)
#   M9_INTITLEBAR        0 (default, KWin SSD title bar) or 1 (CSD)
#   M9_SIDEBAR_REVAMP    true (default) or false (legacy sidebar)
#   M9_VERTICAL_TABS     false (default) or true
#   M9_BOOKMARKS_BAR     always (default), newtab, or never
#   M9_OPEN_SIDEBAR      optional sidebar command id in xulstore (e.g. viewBookmarksSidebar)
#   M9_EXTRA_PREFS       optional extra user.js lines
#   M9_MARIONETTE_SCRIPT optional command run once Marionette listens (receives
#                        M9_MARIONETTE_PORT, M9_OUT, M9_SANDBOX_ROOT in env)
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
name=${1:-test}
url=${2:-about:blank}

mkdir -p "$dev/build" "$dev/shots"
out=$dev/shots/firefox-$name.png
log=$dev/shots/firefox-$name.log
rm -f "$out" "$log"

sandbox_root=$(mktemp -d "$dev/build/ff-sandbox-$name.XXXXXX")
runtime_dir=$(mktemp -d)
chmod 700 "$runtime_dir"
cleanup() {
    rm -rf "$runtime_dir" 2>/dev/null || true
    if [[ ${M9_KEEP_SANDBOX:-0} != 1 ]]; then
        rm -rf "$sandbox_root" 2>/dev/null || true
    fi
}
trap cleanup EXIT

s_home=$sandbox_root/home
mkdir -p "$s_home/.config/gtk-3.0" "$s_home/.config/gtk-4.0" \
    "$s_home/.local/share/themes" "$s_home/.cache" "$s_home/.local/state"

# Configure KDE colors, borrowed desktop fonts, and Platinum KWin decoration
# BEFORE switching HOME so nothing reads or writes the real home later.
cp "$project/colors/Platinum.colors" "$s_home/.config/kdeglobals"
globals=$s_home/.config/kdeglobals
for key in font fixed menuFont smallestReadableFont toolBarFont; do
    val=$(kreadconfig6 --file kdeglobals --group General --key "$key" 2>/dev/null || true)
    if [[ -n $val ]]; then
        kwriteconfig6 --file "$globals" --group General --key "$key" "$val"
    fi
done
val=$(kreadconfig6 --file kdeglobals --group WM --key activeFont 2>/dev/null || true)
if [[ -n $val ]]; then
    kwriteconfig6 --file "$globals" --group WM --key activeFont "$val"
fi
kwriteconfig6 --file "$globals" --group KDE --key widgetStyle Platinum

dec=${M9_DECORATION:-platinum}
kwriteconfig6 --file "$s_home/.config/kwinrc" --group org.kde.kdecoration2 --key library "$dec"
kwriteconfig6 --file "$s_home/.config/kwinrc" --group org.kde.kdecoration2 --key theme ""
if [[ $dec == platinum ]]; then
    kwriteconfig6 --file "$s_home/.config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft X
    kwriteconfig6 --file "$s_home/.config/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight AI
fi

gtk_theme=${M9_GTK_THEME:-Platinum}
if [[ -d $project/gtk/Platinum ]]; then
    cp -R "$project/gtk/Platinum" "$s_home/.local/share/themes/Platinum"
fi
cat > "$s_home/.config/gtk-3.0/settings.ini" << EOF
[Settings]
gtk-theme-name=$gtk_theme
gtk-application-prefer-dark-theme=0
EOF
cat > "$s_home/.config/gtk-4.0/settings.ini" << EOF
[Settings]
gtk-theme-name=$gtk_theme
gtk-application-prefer-dark-theme=0
EOF

# Prepare Firefox throwaway profile.
profile=${M9_FF_PROFILE:-$dev/build/firefox-profile}
if [[ ${M9_KEEP_PROFILE:-0} != 1 ]]; then
    rm -rf "$profile"
fi
mkdir -p "$profile"

# Parse window geometry WxH@X,Y
win_spec=${M9_FF_WIN_SIZE:-1120x740@60,40}
win_dim=${win_spec%@*}
win_pos=${win_spec#*@}
win_w=${win_dim%x*}
win_h=${win_dim#*x}
win_x=${win_pos%,*}
win_y=${win_pos#*,}

open_sidebar=${M9_OPEN_SIDEBAR:-}
python3 -I - "$profile/xulstore.json" "$win_w" "$win_h" "$win_x" "$win_y" "$open_sidebar" << 'PY'
import json, sys
path, w, h, x, y, sidebar_cmd = sys.argv[1:]
main_win = {
    "width": str(w),
    "height": str(h),
    "screenX": str(x),
    "screenY": str(y),
    "sizemode": "normal",
}
doc = {"chrome://browser/content/browser.xhtml": {"main-window": main_win}}
if sidebar_cmd:
    doc["chrome://browser/content/browser.xhtml"]["sidebar-box"] = {
        "sidebarcommand": sidebar_cmd,
        "width": "240",
        "checked": "true",
    }
    doc["chrome://browser/content/browser.xhtml"]["sidebar-title"] = {
        "value": "Bookmarks" if "Bookmark" in sidebar_cmd else "History"
    }
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
PY

# Seed deterministic offline bookmarks on the Bookmarks Toolbar so #PersonalToolbar
# renders actual items like IE5's Favorites bar without touching the network.
stylesheets_pref=${M9_STYLESHEETS_PREF:-true}
intitlebar=${M9_INTITLEBAR:-0}
sidebar_revamp=${M9_SIDEBAR_REVAMP:-true}
vertical_tabs=${M9_VERTICAL_TABS:-false}
bookmarks_bar=${M9_BOOKMARKS_BAR:-always}

cat > "$profile/user.js" << EOF
// Sandboxed deterministic Firefox profile for macos9-theme testing.
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", $stylesheets_pref);
user_pref("browser.tabs.inTitlebar", $intitlebar);
user_pref("sidebar.revamp", $sidebar_revamp);
user_pref("sidebar.verticalTabs", $vertical_tabs);
user_pref("browser.toolbars.bookmarks.visibility", "$bookmarks_bar");

// Suppress first-run tabs, welcome modals, default-browser prompts, and telemetry.
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.startup.homepage", "about:blank");
user_pref("browser.startup.page", 0);
user_pref("browser.startup.firstrunSkipsHomepage", true);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("trailhead.firstrun.didSeeAboutWelcome", true);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("app.normandy.enabled", false);
user_pref("app.shield.optoutstudies.enabled", false);
user_pref("browser.discovery.enabled", false);
user_pref("browser.newtabpage.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
user_pref("extensions.getAddons.cache.enabled", false);
user_pref("extensions.Pocket.enabled", false);
user_pref("network.captive-portal-service.enabled", false);
user_pref("network.connectivity-service.enabled", false);
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("browser.safebrowsing.downloads.enabled", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.rights.3.shown", true);
user_pref("browser.messaging-system.whatsNewPanel.enabled", false);
user_pref("browser.UITour.enabled", false);
user_pref("browser.translations.automaticallyPopup", false);
user_pref("ui.prefersReducedMotion", 1);
EOF

if [[ -n ${M9_OPEN_SIDEBAR:-} ]]; then
    cat >> "$profile/user.js" << EOF
user_pref("sidebar.backupState", "{\"command\":\"$M9_OPEN_SIDEBAR\",\"panelOpen\":true}");
EOF
    if [[ $sidebar_revamp == false ]]; then
        cat >> "$profile/user.js" << EOF
user_pref("sidebar.old-sidebar.has-used", true);
EOF
    fi
fi

if [[ -n ${M9_EXTRA_PREFS:-} ]]; then
    printf '%s\n' "$M9_EXTRA_PREFS" >> "$profile/user.js"
fi

# Install optional userChrome.css / chrome directory.
uc_src=${M9_USERCHROME:-}
if [[ -z $uc_src && -d $project/firefox/chrome ]]; then
    uc_src=$project/firefox/chrome
fi
if [[ -n $uc_src && $uc_src != none ]]; then
    mkdir -p "$profile/chrome"
    if [[ -d $uc_src ]]; then
        cp -R "$uc_src"/. "$profile/chrome/"
    elif [[ -f $uc_src ]]; then
        cp "$uc_src" "$profile/chrome/userChrome.css"
    else
        echo "firefox-test.sh: M9_USERCHROME '$uc_src' does not exist" >&2
        exit 2
    fi
fi

# Pick an ephemeral localhost port only when M9_MARIONETTE_SCRIPT is set.
m_port=0
if [[ -n ${M9_MARIONETTE_SCRIPT:-} ]]; then
    m_port=$(python3 -I -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
    cat >> "$profile/user.js" << EOF
user_pref("marionette.port", $m_port);
user_pref("marionette.defaultPrefs.port", $m_port);
EOF
fi

qt_plugins=
for pdir in "$project/style/build/plugins" "$project/decoration/build/plugins"; do
    if [[ -d $pdir ]]; then
        qt_plugins=$pdir${qt_plugins:+:$qt_plugins}
    fi
done

session_sh=$sandbox_root/session.sh
cat > "$session_sh" << 'EOF'
#!/bin/bash
set -euo pipefail

dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM >/dev/null 2>&1 || true
gsettings set org.gnome.desktop.interface gtk-theme "$M9_GTK_THEME" >/dev/null 2>&1 || true
gsettings set org.gnome.desktop.interface color-scheme 'default' >/dev/null 2>&1 || true

ff_args=(--no-remote --profile "$M9_FF_PROFILE" "$M9_URL")
ff_remote_env=()
if [[ -n ${M9_MARIONETTE_SCRIPT:-} ]]; then
    ff_args=(--marionette "${ff_args[@]}")
    ff_remote_env=(MOZ_REMOTE_ALLOW_SYSTEM_ACCESS=1)
fi

env MOZ_ENABLE_WAYLAND=1 MOZ_NO_REMOTE=1 MOZ_CRASHREPORTER_DISABLE=1 "${ff_remote_env[@]}" \
    firefox "${ff_args[@]}" > "$M9_SANDBOX_ROOT/firefox.log" 2>&1 &
ff_pid=$!
trap 'kill "$ff_pid" 2>/dev/null || true' EXIT

if [[ -n ${M9_MARIONETTE_SCRIPT:-} ]]; then
    python3 -I - "$M9_MARIONETTE_PORT" << 'PY'
import socket, sys, time
port = int(sys.argv[1])
deadline = time.monotonic() + 30.0
while time.monotonic() < deadline:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5) as s:
            hdr = s.recv(64)
            if b"marionetteProtocol" in hdr:
                sys.exit(0)
    except OSError:
        time.sleep(0.2)
print(f"Timed out waiting for Marionette on 127.0.0.1:{port}", file=sys.stderr)
sys.exit(1)
PY
    eval "$M9_MARIONETTE_SCRIPT"
else
    sleep "${M9_WAIT:-5}"
    spectacle -b -n -f -o "$M9_OUT"
    sleep 0.4
fi

kill -TERM "$ff_pid" 2>/dev/null || true
wait "$ff_pid" 2>/dev/null || true
echo "done" > "$M9_SANDBOX_ROOT/complete"
EOF
chmod +x "$session_sh"

size=${M9_SIZE:-1280x860}
sock="m9-ff-$$"

rc=0
env -i \
    PATH="/usr/local/bin:/usr/bin:/bin" \
    HOME="$s_home" \
    USER="${USER:-$(id -un)}" \
    LANG=C.UTF-8 \
    XDG_CONFIG_HOME="$s_home/.config" \
    XDG_DATA_HOME="$s_home/.local/share" \
    XDG_CACHE_HOME="$s_home/.cache" \
    XDG_STATE_HOME="$s_home/.local/state" \
    XDG_CONFIG_DIRS="/etc/xdg" \
    XDG_DATA_DIRS="/usr/local/share:/usr/share" \
    XDG_RUNTIME_DIR="$runtime_dir" \
    XDG_CURRENT_DESKTOP=KDE \
    XDG_SESSION_TYPE=wayland \
    KDE_FULL_SESSION=true \
    KDE_SESSION_VERSION=6 \
    QT_QPA_PLATFORM=wayland \
    QT_QPA_PLATFORMTHEME=kde \
    QT_STYLE_OVERRIDE=Platinum \
    QT_FORCE_STDERR_LOGGING=1 \
    QT_PLUGIN_PATH="$qt_plugins" \
    GDK_BACKEND=wayland \
    M9_GTK_THEME="$gtk_theme" \
    M9_FF_PROFILE="$profile" \
    M9_URL="$url" \
    M9_WAIT="${M9_WAIT:-5}" \
    M9_OUT="$out" \
    M9_SANDBOX_ROOT="$sandbox_root" \
    M9_MARIONETTE_PORT="$m_port" \
    M9_MARIONETTE_SCRIPT="${M9_MARIONETTE_SCRIPT:-}" \
    timeout "${M9_TIMEOUT:-120}" dbus-run-session -- \
    kwin_wayland --virtual --width "${size%x*}" --height "${size#*x}" \
    --no-lockscreen --no-global-shortcuts --no-kactivities \
    --socket "$sock" --exit-with-session "$session_sh" \
    > "$log" 2>&1 || rc=$?

if [[ -f $sandbox_root/firefox.log ]]; then
    {
        echo "=== firefox.log ==="
        cat "$sandbox_root/firefox.log"
    } >> "$log"
fi

if [[ $rc -ne 0 || ! -s $sandbox_root/complete || ! -s $out ]]; then
    echo "FAILED  $out (rc=$rc; see $log)" >&2
    tail -n 30 "$log" >&2 || true
    exit 1
fi

echo "ok      $out"
