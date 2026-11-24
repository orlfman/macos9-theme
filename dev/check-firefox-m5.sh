#!/bin/bash
# Firefox Milestone 5 robustness verification suite:
#   1. tools/check-firefox-selectors.py against installed omni.ja & version.json
#      + 4 negative controls (missing #id, missing ::part, untested major, allow flag)
#   2. Live nested KWin Wayland (2400x1600 physical output) keyboard focus across
#      all chrome controls + 100%, 150%, and 200% scaling crispness & zero-clipping
#
# Never touches ~/.mozilla, ~/.config/mozilla, or the live desktop session.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
mkdir -p "$dev/build" "$dev/shots"

rdir=$(mktemp -d "$dev/build/firefox-m5.XXXXXX")
echo "Firefox Milestone 5 evidence: $rdir"

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

# Step 1: Run selector checker + negative controls.
echo "--- 1/3 omni.ja selector checker & version gate + negative controls ---"
real_rc=0
python3 -I -W error "$project/tools/check-firefox-selectors.py" || real_rc=$?

# Negative control A: missing #id selector
neg_id_dir="$rdir/neg-id"
mkdir -p "$neg_id_dir"
# A common color literal in omni.ja must not count as a browser element ID.
printf '#ffffff { color: red; }\n' > "$neg_id_dir/bad.css"
neg_missing_id_rc=0
python3 -I -W error "$project/tools/check-firefox-selectors.py" --css-dir "$neg_id_dir" >/dev/null 2>&1 || neg_missing_id_rc=$?

# Negative control B: missing ::part() selector
neg_part_dir="$rdir/neg-part"
mkdir -p "$neg_part_dir"
printf '#nav-bar::part(m9-nonexistent-part) { color: red; }\n' > "$neg_part_dir/bad.css"
neg_missing_part_rc=0
python3 -I -W error "$project/tools/check-firefox-selectors.py" --css-dir "$neg_part_dir" >/dev/null 2>&1 || neg_missing_part_rc=$?

# Negative control C: untested Firefox major version (999.0.1)
cat > "$rdir/fake-app.ini" << 'EOF'
[App]
Name=Firefox
Version=999.0.1
EOF
neg_untested_ver_rc=0
python3 -I -W error "$project/tools/check-firefox-selectors.py" --version-only --application-ini "$rdir/fake-app.ini" >/dev/null 2>&1 || neg_untested_ver_rc=$?

neg_allow_ver_rc=0
python3 -I -W error "$project/tools/check-firefox-selectors.py" --version-only --allow-untested-version --application-ini "$rdir/fake-app.ini" >/dev/null 2>&1 || neg_allow_ver_rc=$?

python3 -I - "$rdir/gates.json" "$real_rc" "$neg_missing_id_rc" "$neg_missing_part_rc" "$neg_untested_ver_rc" "$neg_allow_ver_rc" << 'PY'
import json, sys
out, r, nid, npt, nuv, nav = sys.argv[1:]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({
        "real_rc": int(r),
        "neg_missing_id_rc": int(nid),
        "neg_missing_part_rc": int(npt),
        "neg_untested_ver_rc": int(nuv),
        "neg_allow_ver_rc": int(nav),
    }, fh, indent=2)
PY

# Step 2: Seed deterministic offline profile (bookmarks + IE5 button set)
cat > "$rdir/page.html" << 'EOF'
<!doctype html>
<html><head><meta charset="utf-8"><title>Mac OS 9 Platinum</title>
<style>body{font:13px/1.5 sans-serif;margin:24px;background:#fff;color:#111;}h1{color:#333399;}</style>
</head><body><h1>Milestone 5 — Scaling &amp; Keyboard Focus</h1><p>Offline robustness test page.</p></body></html>
EOF
page_uri="file://$rdir/page.html"

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

echo "--- 2/3 seeding offline profile ---"
M9_FF_PROFILE="$seed_prof" M9_USERCHROME=none \
    M9_MARIONETTE_SCRIPT="python3 -I -W error '$rdir/seed.py'" \
    "$dev/firefox-test.sh" m5-seed "$page_uri"
rm -rf "$seed_prof/lock" "$seed_prof/.parentlock" "$seed_prof/sessionstore.jsonlz4" "$seed_prof/sessionstore-backups"

echo "--- 3/3 keyboard focus everywhere + 150%/200% scaling on 2400x1600 virtual KWin ---"
probe_prof="$rdir/prof-probe"
cp -R "$seed_prof" "$probe_prof"
M9_SIZE="2400x1600" M9_FF_WIN_SIZE="1120x740@40,30" \
    M9_FF_PROFILE="$probe_prof" M9_KEEP_PROFILE=1 M9_USERCHROME="$project/firefox/chrome" \
    M9_TIMEOUT=180 \
    M9_MARIONETTE_SCRIPT="M9_M5_DIR='$rdir' python3 -I -W error '$dev/firefox-m5/probe.py'" \
    "$dev/firefox-test.sh" m5-probe "$page_uri"

after_host=$(snap_host)
python3 -I - "$rdir/host-leak.json" "$before_host" "$after_host" << 'PY'
import json, sys
out, b, a = sys.argv[1:]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"before": json.loads(b), "after": json.loads(a)}, fh, indent=2)
PY

python3 -I -W error "$dev/firefox-m5/verify.py" "$rdir" "$dev/shots" | tee "$rdir/verdict.log"
exit "${PIPESTATUS[0]}"
