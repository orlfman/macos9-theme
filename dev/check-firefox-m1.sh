#!/bin/bash
# Firefox Milestone 1 discovery & harness verification suite.
#
# Exercises dev/firefox-test.sh across:
# 1. Cold normal-launch baseline (stock Firefox + Platinum KWin SSD + GTK 3 Platinum)
# 2. Cold normal-launch chrome/userChrome.css marker load
# 3. Negative control: stylesheets pref = false with chrome/userChrome.css present
# 4. Cold normal-launch two-row IE5 toolbar + Lavender address band + button labels
# 5. Cold normal-launch legacy sidebar (sidebar.revamp = false)
# 6. Live Marionette chrome probe (DOM/Shadow-DOM inventory, GTK 3 inheritance,
#    revamped sidebar & vertical tabs, narrow resize overflow, Customize Mode,
#    keyboard focus, and built-in theme / dark-mode / forced-colors gating)
#
# Never touches ~/.mozilla, ~/.config/mozilla, or the live desktop session.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
mkdir -p "$dev/build" "$dev/shots"

rdir=$(mktemp -d "$dev/build/firefox-m1.XXXXXX")
echo "Firefox Milestone 1 evidence: $rdir"

# Record host ~/.mozilla and ~/.config/mozilla existence before any run.
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

# Marker CSS for normal-path userChrome.css proof.
cat > "$rdir/marker.css" << 'EOF'
#PersonalToolbar {
  background-color: #CCCCFF !important;
  background-image: none !important;
  min-height: 24px !important;
}
EOF

# Cold-launch two-row IE5 layout + pinstripe + Lavender address tube probe CSS.
# Uses padding-bottom: 26px on #nav-bar + position: absolute #urlbar-container
# outside Customize Mode so #urlbar-container spans 100% width and never
# triggers false OverflowableToolbar overflow!
cat > "$rdir/wrap-cold.css" << 'EOF'
@media (-moz-native-theme) and (prefers-color-scheme: light) and (not (prefers-contrast)) and (not (forced-colors)) {
  :root:not([lwtheme]) {
    #navigator-toolbox {
      border-bottom: 1px solid #000000 !important;
    }
    #toolbar-menubar { order: 0 !important; }
    #nav-bar {
      order: 1 !important;
      position: relative !important;
      background: repeating-linear-gradient(to bottom, #DEDEDE 0px, #DEDEDE 1px, #CCCCCC 1px, #CCCCCC 2px, #E8E6E8 2px, #E8E6E8 3px) !important;
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 1px solid #ADADAD !important;
    }
    &:not([customizing]) #nav-bar {
      padding-bottom: 26px !important;
    }
    &:not([customizing]) #urlbar-container {
      position: absolute !important;
      inset-inline: 0 !important;
      bottom: 0 !important;
      width: 100% !important;
      max-width: none !important;
      height: 26px !important;
      min-height: 26px !important;
      margin: 0 !important;
      padding: 3px 8px !important;
      box-sizing: border-box !important;
      background: linear-gradient(to bottom, #333399 0px, #333399 4px, #6666CC 4px, #6666CC 9px, #9999FF 9px, #9999FF 15px, #6666CC 15px, #6666CC 20px, #333399 20px, #333399 24px) !important;
      border-top: 1px solid #ADADAD !important;
      border-bottom: 1px solid #000000 !important;
    }
    #nav-bar .toolbarbutton-1 {
      flex-direction: column !important;
      min-width: 52px !important;
      padding: 2px 4px !important;
      align-items: center !important;
    }
    #nav-bar .toolbarbutton-1 > .toolbarbutton-text {
      display: block !important;
      width: auto !important;
      max-width: none !important;
      min-height: 0 !important;
      padding: 1px 2px 0 !important;
      font-size: 10px !important;
      line-height: 11px !important;
      text-align: center !important;
      color: #111111 !important;
      background: transparent !important;
      outline: none !important;
    }
    #PersonalToolbar {
      order: 2 !important;
      min-height: 24px !important;
      background: repeating-linear-gradient(to bottom, #DEDEDE 0px, #DEDEDE 1px, #CCCCCC 1px, #CCCCCC 2px, #E8E6E8 2px, #E8E6E8 3px) !important;
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 1px solid #ADADAD !important;
    }
    #TabsToolbar {
      order: 3 !important;
      background: #DDDDDD !important;
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 1px solid #999999 !important;
    }
  }
}
EOF

echo "--- 1/6 stock baseline ---"
M9_FF_PROFILE="$rdir/prof-stock" M9_USERCHROME=none M9_WAIT=4 \
    "$dev/firefox-test.sh" m1-stock about:blank

echo "--- 2/6 normal-path userChrome.css marker ---"
M9_FF_PROFILE="$rdir/prof-marker" M9_USERCHROME="$rdir/marker.css" M9_WAIT=4 \
    "$dev/firefox-test.sh" m1-marker about:blank

echo "--- 3/6 negative control (stylesheets=false) ---"
M9_FF_PROFILE="$rdir/prof-neg" M9_USERCHROME="$rdir/marker.css" M9_STYLESHEETS_PREF=false M9_WAIT=4 \
    "$dev/firefox-test.sh" m1-neg-pref about:blank

echo "--- 4/6 cold two-row URL bar wrap + pinstripe + Lavender tube ---"
M9_FF_PROFILE="$rdir/prof-wrap" M9_USERCHROME="$rdir/wrap-cold.css" M9_WAIT=4 \
    "$dev/firefox-test.sh" m1-wrap-cold about:blank

echo "--- 5/6 cold legacy sidebar (sidebar.revamp=false) ---"
M9_FF_PROFILE="$rdir/prof-legacy" M9_USERCHROME=none M9_SIDEBAR_REVAMP=false \
    M9_OPEN_SIDEBAR=viewBookmarksSidebar M9_WAIT=4 \
    "$dev/firefox-test.sh" m1-sidebar-legacy about:blank

echo "--- 6/6 live Marionette chrome DOM, GTK, overflow, customize & theme matrix ---"
M9_FF_PROFILE="$rdir/prof-probe" M9_USERCHROME=none \
    M9_MARIONETTE_SCRIPT="M9_FF_M1_DIR='$rdir' python3 -I -W error '$dev/firefox-m1/probe.py'" \
    "$dev/firefox-test.sh" m1-probe-restored about:blank

after_host=$(snap_host)
python3 -I - "$rdir/host-leak-check.json" "$before_host" "$after_host" << 'PY'
import json, sys
out, b, a = sys.argv[1:]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"before": json.loads(b), "after": json.loads(a)}, fh, indent=2)
PY

python3 -I -W error "$dev/firefox-m1/verify.py" "$rdir" "$dev/shots" | tee "$rdir/verdict.log"
exit "${PIPESTATUS[0]}"
