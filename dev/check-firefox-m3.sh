#!/bin/bash
# Firefox Milestone 3 verification suite: tests the real firefox/chrome/
# vertical slice (pinstriped button toolbar + Deep Lavender address band +
# pinstriped Favorites bar) in isolated nested virtual KWin.
#
# Never touches ~/.mozilla, ~/.config/mozilla, or the live desktop session.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
mkdir -p "$dev/build" "$dev/shots"

rdir=$(mktemp -d "$dev/build/firefox-m3.XXXXXX")
echo "Firefox Milestone 3 evidence: $rdir"

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

# Create deterministic offline page
cat > "$rdir/page.html" << 'EOF'
<!doctype html>
<html><head><meta charset="utf-8"><title>Mac OS 9 Platinum</title>
<style>body{font:13px sans-serif;margin:24px;background:#fff;color:#111;}</style>
</head><body><h1>Milestone 3 Vertical Slice</h1><p>Offline verification page.</p></body></html>
EOF
page_uri="file://$rdir/page.html"

# Step 1: Seed one reusable offline profile (bookmarks + IE5 button set)
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
            ["Live Home Page", "$page_uri"],
            ["Appearance Notes", "about:blank"],
            ["Favorites Guide", "about:support"],
            ["Mozilla Docs", "about:robots"]
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
    "$dev/firefox-test.sh" m3-seed "$page_uri"
rm -rf "$seed_prof/lock" "$seed_prof/.parentlock" "$seed_prof/sessionstore.jsonlz4" "$seed_prof/sessionstore-backups"

# Step 2: Cold normal-launch render with the REAL firefox/chrome/ (NO --marionette!)
echo "--- 2/3 cold normal-launch render (firefox/chrome/) ---"
cold_prof="$rdir/prof-cold"
cp -R "$seed_prof" "$cold_prof"
M9_FF_PROFILE="$cold_prof" M9_KEEP_PROFILE=1 M9_USERCHROME="$project/firefox/chrome" M9_WAIT=5 \
    "$dev/firefox-test.sh" m3-cold "$page_uri"

# Step 3: Interactive Marionette state, dropdown, overflow, customize & theme-gate verification
echo "--- 3/3 interactive state & gating probe (firefox/chrome/) ---"
probe_prof="$rdir/prof-probe"
cp -R "$seed_prof" "$probe_prof"
M9_FF_PROFILE="$probe_prof" M9_KEEP_PROFILE=1 M9_USERCHROME="$project/firefox/chrome" \
    M9_MARIONETTE_SCRIPT="M9_M3_DIR='$rdir' python3 -I -W error '$dev/firefox-m3/probe.py'" \
    "$dev/firefox-test.sh" m3-probe "$page_uri"

after_host=$(snap_host)
python3 -I - "$rdir/host-leak.json" "$before_host" "$after_host" << 'PY'
import json, sys
out, b, a = sys.argv[1:]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"before": json.loads(b), "after": json.loads(a)}, fh, indent=2)
PY

python3 -I -W error "$dev/firefox-m3/verify.py" "$rdir" "$dev/shots" | tee "$rdir/verdict.log"
exit "${PIPESTATUS[0]}"
