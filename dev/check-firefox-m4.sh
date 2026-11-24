#!/bin/bash
# Firefox Milestone 4 full-coverage verification suite.
#
# Exercises the complete firefox/chrome/ stylesheet across 1A + 1C live-
# switchable tabs, 5A permanent status band, neutral busy activity indicator,
# Platinum menus/panels/urlbar popup, find & notification bars, sidebar, real
# inactive window flattening, Private window, popup window, fullscreen,
# Customize Mode, and theme/dark/HighContrast gating.
#
# Never touches ~/.mozilla, ~/.config/mozilla, or the live desktop session.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
mkdir -p "$dev/build" "$dev/shots"

rdir=$(mktemp -d "$dev/build/firefox-m4.XXXXXX")
echo "Firefox Milestone 4 evidence: $rdir"

snap_host() {
    python3 -I - << 'PY'
import json, pathlib
h = pathlib.Path.home()
print(json.dumps({
    "dot_mozilla": (h / ".mozilla").exists(),
    "xdg_mozilla": (h / ".config" / "mozilla").exists(),
}))
PY
}
before_host=$(snap_host)

# Deterministic offline pages for multi-tab cold render
for idx in 1 2 3; do
    case $idx in
        1) title="Mac OS 9 Platinum" ; h1="Platinum Firefox — Milestone 4" ;;
        2) title="Appearance Notes"  ; h1="Platinum Appearance Notes" ;;
        3) title="Favorites Guide"   ; h1="Favorites & Sidebar Guide" ;;
    esac
    cat > "$rdir/page$idx.html" << EOF
<!doctype html>
<html><head><meta charset="utf-8"><title>$title</title>
<style>body{font:13px/1.5 sans-serif;margin:24px;background:#fff;color:#111;}h1{color:#333399;}</style>
</head><body><h1>$h1</h1><p>Offline Milestone 4 verification page with Platinum keyword.</p></body></html>
EOF
done
u1="file://$rdir/page1.html"
u2="file://$rdir/page2.html"
u3="file://$rdir/page3.html"

seed_prof="$rdir/seed-profile"
cat > "$rdir/seed.py" << PY
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path("$dev/firefox-m1")))
from probe import Marionette, shoot

m = Marionette(int(os.environ["M9_MARIONETTE_PORT"]))
try:
    m.send("WebDriver:NewSession", {"capabilities": {}})
    m.send("Marionette:SetContext", {"value": "chrome"})
    m.exec_chrome('''
        const done = arguments[arguments.length - 1];
        (async () => {
          if (window.gBrowserInit && !gBrowserInit.delayedStartupFinished) {
            await new Promise(r => {
              const obs = (s) => { if (s === window) { Services.obs.removeObserver(obs, "browser-delayed-startup-finished"); r(); } };
              Services.obs.addObserver(obs, "browser-delayed-startup-finished");
            });
          }
          for (const [title, url] of [
            ["Live Home Page", "$u1"],
            ["Appearance Notes", "$u2"],
            ["Favorites Guide", "$u3"],
            ["Mozilla Docs", "about:support"]
          ]) {
            await PlacesUtils.bookmarks.insert({ parentGuid: PlacesUtils.bookmarks.toolbarGuid, title, url });
          }
          CustomizableUI.addWidgetToArea("home-button", "nav-bar", 4);
          CustomizableUI.addWidgetToArea("print-button", "nav-bar", 5);
          CustomizableUI.addWidgetToArea("find-button", "nav-bar", 6);
          Services.prefs.savePrefFile(null);
          await new Promise(r => setTimeout(r, 350));
          done(true);
        })();
    ''', async_mode=True)
    shoot(Path(os.environ["M9_OUT"]), settle=0.2)
finally:
    m.close()
PY

echo "--- 1/3 seeding offline profile ---"
M9_FF_PROFILE="$seed_prof" M9_USERCHROME=none \
    M9_MARIONETTE_SCRIPT="python3 -I -W error '$rdir/seed.py'" \
    "$dev/firefox-test.sh" m4-seed "$u1"
rm -rf "$seed_prof/lock" "$seed_prof/.parentlock" "$seed_prof/sessionstore.jsonlz4" "$seed_prof/sessionstore-backups"

echo "--- 2/3 cold normal-launch 3-tab render (1A tabs + 2A address + 4A toolbar + 5A status) ---"
cold_prof="$rdir/prof-cold"
cp -R "$seed_prof" "$cold_prof"
M9_FF_PROFILE="$cold_prof" M9_KEEP_PROFILE=1 M9_USERCHROME="$project/firefox/chrome" \
    M9_NO_CLI_URL=1 M9_WAIT=5 \
    M9_EXTRA_PREFS=$(printf 'user_pref("browser.startup.page", 1);\nuser_pref("browser.startup.homepage", "%s|%s|%s");\nuser_pref("browser.startup.firstrunSkipsHomepage", false);' "$u1" "$u2" "$u3") \
    "$dev/firefox-test.sh" m4-cold-1a

echo "--- 3/3 interactive Milestone 4 full-coverage probe ---"
probe_prof="$rdir/prof-probe"
cp -R "$seed_prof" "$probe_prof"
M9_FF_PROFILE="$probe_prof" M9_KEEP_PROFILE=1 M9_USERCHROME="$project/firefox/chrome" \
    M9_TIMEOUT=180 \
    M9_MARIONETTE_SCRIPT="M9_M4_DIR='$rdir' python3 -I -W error '$dev/firefox-m4/probe.py'" \
    "$dev/firefox-test.sh" m4-probe "$u1"

after_host=$(snap_host)
python3 -I - "$rdir/host-leak.json" "$before_host" "$after_host" << 'PY'
import json, sys
out, b, a = sys.argv[1:]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"before": json.loads(b), "after": json.loads(a)}, fh, indent=2)
PY

python3 -I -W error "$dev/firefox-m4/verify.py" "$rdir" "$dev/shots" | tee "$rdir/verdict.log"
exit "${PIPESTATUS[0]}"
