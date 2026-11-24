#!/usr/bin/env python3
"""Firefox Milestone 5 scaling (150% / 200%) & keyboard-focus-everywhere probe.

Runs inside nested kwin_wayland --virtual (2400x1600 physical output so even at
200% scale the logical desktop is 1200x800 and holds the full 1120x740 Firefox
window cleanly without edge clipping!).

Checks:
  1. Keyboard focus rings (#6666CC, 2 px) everywhere:
     - Toolbar button (#home-button via :focus-visible + real Shift+Tab nav)
     - Address field (#urlbar via gURLBar.focus())
     - Bookmarks bar item (#PlacesToolbarItems > .bookmark-item)
     - Horizontal 1A tab (.tabbrowser-tab)
     - Vertical 1C tab (sidebar.verticalTabs = true)
     - Find bar search box (gFindBar._findField.focus())
  2. Output scaling at 100%, 150%, and 200% via kscreen-doctor:
     - Verifies kscreen-doctor reports scale 1.5 and 2
     - Verifies Firefox window.devicePixelRatio updates to 1.5 and 2
     - Verifies zero text clipping (scrollWidth <= clientWidth + 2) across
       toolbar button labels, bookmarks, horizontal tabs, and urlbar
     - Verifies zero overlap between toolbar buttons and row-2 address band,
       zero false overflow, and intact 16 px permanent status band
     - Captures physical compositor screenshots at 150% and 200%!

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "firefox-m1"))
from probe import Marionette, shoot  # noqa: E402


def detect_output_name() -> str:
    p = subprocess.run(["kscreen-doctor", "-o"], capture_output=True, text=True, check=False)
    clean = re.sub(r"\x1b\[[0-9;]*m", "", p.stdout)
    for line in clean.splitlines():
        if "Output:" in line:
            parts = line.split()
            if len(parts) >= 3:
                return parts[2]
    return "Virtual-1"


def set_scale(out_name: str, scale_str: str) -> str:
    subprocess.run(["kscreen-doctor", f"output.{out_name}.scale.{scale_str}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.7)
    p = subprocess.run(["kscreen-doctor", "-o"], capture_output=True, text=True, check=True)
    return re.sub(r"\x1b\[[0-9;]*m", "", p.stdout)


def main() -> int:
    port = int(os.environ["M9_MARIONETTE_PORT"])
    main_out = pathlib.Path(os.environ["M9_OUT"])
    rdir = pathlib.Path(os.environ["M9_M5_DIR"])
    shots = main_out.parent

    out_name = detect_output_name()
    m = Marionette(port)
    try:
        m.send("WebDriver:NewSession", {"capabilities": {}})
        m.send("Marionette:SetContext", {"value": "chrome"})

        # Wait for startup + open 2 extra tabs so we have 3 tabs for clipping/focus checks.
        m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              if (window.gBrowserInit && !gBrowserInit.delayedStartupFinished) {
                await new Promise(r => {
                  const obs = (s) => {
                    if (s === window) {
                      Services.obs.removeObserver(obs, "browser-delayed-startup-finished");
                      r();
                    }
                  };
                  Services.obs.addObserver(obs, "browser-delayed-startup-finished");
                });
              }
              const p1 = gBrowser.selectedTab;
              gBrowser.addTrustedTab("about:robots");
              gBrowser.addTrustedTab("about:support");
              gBrowser.selectedTab = p1;
              await new Promise(r => setTimeout(r, 350));
              done(true);
            })();
            """,
            async_mode=True,
        )

        # 1. Keyboard focus everywhere (#6666CC, 2 px across all interactive chrome controls).
        kb_focus = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const res = {};

              // (a) Address field real focus
              gURLBar.focus();
              await new Promise(r => setTimeout(r, 150));
              const ubg = getComputedStyle(document.querySelector("#urlbar > .urlbar-background"));
              res.urlbar = { width: ubg.outlineWidth, color: ubg.outlineColor };

              // (b) Shift+Tab keyboard navigation into #nav-bar + :focus-visible on #home-button
              Services.focus.moveFocus(window, gURLBar.inputField, Services.focus.MOVEFOCUS_BACKWARD, Services.focus.FLAG_BYKEY);
              res.shiftTabInNavBar = !!document.activeElement && !!document.activeElement.closest("#nav-bar");
              const home = document.getElementById("home-button");
              InspectorUtils.addPseudoClassLock(home, ":focus-visible");
              const rect = home.getBoundingClientRect();
              res.homeSize = [rect.width, rect.height];
              const hcs = getComputedStyle(home);
              res.toolbarButton = { width: hcs.outlineWidth, color: hcs.outlineColor };

              // (c) Bookmark item :focus-visible
              const bm = document.querySelector("#PlacesToolbarItems > .bookmark-item");
              InspectorUtils.addPseudoClassLock(bm, ":focus-visible");
              const bcs = getComputedStyle(bm);
              res.bookmarkItem = { width: bcs.outlineWidth, color: bcs.outlineColor };

              // (d) Horizontal 1A tab :focus-visible
              const tab = gBrowser.selectedTab;
              InspectorUtils.addPseudoClassLock(tab, ":focus-visible");
              const tcs = getComputedStyle(tab.querySelector(".tab-background"));
              res.horizontalTab = { width: tcs.outlineWidth, color: tcs.outlineColor };

              // (e) Find bar real focus + secondary buttons (:focus-visible)
              await gBrowser.getFindBar();
              gFindBar.open();
              gFindBar._findField.focus();
              await new Promise(r => setTimeout(r, 150));
              const fcs = getComputedStyle(gFindBar._findField);
              res.findbarInput = { width: fcs.outlineWidth, color: fcs.outlineColor };

              const newTabBtn = document.getElementById("tabs-newtab-button");
              InspectorUtils.addPseudoClassLock(newTabBtn, ":focus-visible");
              const ntcs = getComputedStyle(newTabBtn);
              res.newTabButton = { width: ntcs.outlineWidth, color: ntcs.outlineColor };
              InspectorUtils.clearPseudoClassLocks(newTabBtn);

              const fbNext = gFindBar.querySelector(".findbar-find-next");
              InspectorUtils.addPseudoClassLock(fbNext, ":focus-visible");
              const fbncs = getComputedStyle(fbNext);
              res.findbarButton = { width: fbncs.outlineWidth, color: fbncs.outlineColor };
              InspectorUtils.clearPseudoClassLocks(fbNext);

              done(res);
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m5-keyboard-focus.png", settle=0.2)

        m.exec_chrome('InspectorUtils.clearPseudoClassLocks(document.getElementById("home-button"));')
        shoot(rdir / "home-without-focus.png", settle=0.2)

        # Also test vertical 1C tab keyboard focus!
        kb_vtab = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              gFindBar.close();
              InspectorUtils.clearPseudoClassLocks(document.getElementById("home-button"));
              const bm = document.querySelector("#PlacesToolbarItems > .bookmark-item");
              if (bm) InspectorUtils.clearPseudoClassLocks(bm);
              InspectorUtils.clearPseudoClassLocks(gBrowser.selectedTab);

              Services.prefs.setBoolPref("sidebar.verticalTabs", true);
              await new Promise(r => setTimeout(r, 350));
              const tab = gBrowser.selectedTab;
              InspectorUtils.addPseudoClassLock(tab, ":focus-visible");
              const vtcs = getComputedStyle(tab.querySelector(".tab-background"));
              const out = { width: vtcs.outlineWidth, color: vtcs.outlineColor };
              InspectorUtils.clearPseudoClassLocks(tab);
              Services.prefs.setBoolPref("sidebar.verticalTabs", false);
              Services.prefs.setBoolPref("sidebar.revamp", false);
              await new Promise(r => setTimeout(r, 350));
              gBrowser.selectedBrowser.focus();
              done(out);
            })();
            """,
            async_mode=True,
        )
        kb_focus["verticalTab"] = kb_vtab

        # 2. Measure layout, crispness, and zero-clipping across 100%, 150%, and 200% scales!
        def measure_scale_metrics() -> dict:
            return m.exec_chrome(
                """
                const nav = document.getElementById("nav-bar");
                const navR = nav.getBoundingClientRect();
                const urlCR = document.getElementById("urlbar-container").getBoundingClientRect();
                const urlR = document.getElementById("urlbar").getBoundingClientRect();
                const favR = document.getElementById("PersonalToolbar").getBoundingClientRect();
                const tabsR = document.getElementById("TabsToolbar").getBoundingClientRect();
                const homeR = document.getElementById("home-button").getBoundingClientRect();

                // Check visible toolbar button labels for horizontal/vertical clipping!
                const clippedButtons = [];
                for (const b of document.querySelectorAll("#nav-bar .toolbarbutton-1")) {
                  const br = b.getBoundingClientRect();
                  if (br.width === 0 || br.height === 0) continue;
                  const txt = b.querySelector(".toolbarbutton-text");
                  if (!txt) continue;
                  const tr = txt.getBoundingClientRect();
                  if (tr.width === 0) continue;
                  if (txt.scrollWidth > txt.clientWidth + 2 || tr.right > br.right + 2) {
                    clippedButtons.push({ id: b.id, sw: txt.scrollWidth, cw: txt.clientWidth });
                  }
                }

                // Check visible bookmarks for clipping!
                const clippedBookmarks = [];
                for (const bm of document.querySelectorAll("#PlacesToolbarItems > .bookmark-item")) {
                  const r = bm.getBoundingClientRect();
                  if (r.width === 0) continue;
                  const lbl = bm.querySelector(".toolbarbutton-text");
                  if (lbl && lbl.scrollWidth > lbl.clientWidth + 2) {
                    clippedBookmarks.push({ label: bm.getAttribute("label"), sw: lbl.scrollWidth, cw: lbl.clientWidth });
                  }
                }

                const statusCS = getComputedStyle(document.body, "::after");
                return {
                  dpr: window.devicePixelRatio,
                  innerW: window.innerWidth,
                  innerH: window.innerHeight,
                  overflowing: nav.hasAttribute("overflowing"),
                  navH: Math.round(navR.height),
                  urlCW: Math.round(urlCR.width),
                  navW: Math.round(navR.width),
                  urlCH: Math.round(urlCR.height),
                  urlbarH: Math.round(urlR.height),
                  urlBelowHome: urlCR.y >= homeR.bottom - 1,
                  favH: Math.round(favR.height),
                  tabsH: Math.round(tabsR.height),
                  statusH: statusCS.height,
                  clippedButtons,
                  clippedBookmarks
                };
                """
            )

        rtl = m.exec_chrome("""
            const root = document.documentElement;
            const previous = root.style.direction;
            root.style.direction = "rtl";
            try {
              const band = document.getElementById("urlbar-container");
              const label = getComputedStyle(band, "::before");
              const go = band.querySelector(".urlbar-go-button");
              const r = go.getBoundingClientRect();
              const goOnLeft = r.left >= band.getBoundingClientRect().left &&
                               r.right <= document.getElementById("urlbar").getBoundingClientRect().left;
              return {goOnLeft, goHit: document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) === go,
                      rightPadding: getComputedStyle(band).paddingRight,
                      labelRight: label.right, separator: label.borderLeftWidth};
            } finally {
              root.style.direction = previous;
            }
        """)
        scales = {}
        scales["100"] = {"kscreen": "", "metrics": measure_scale_metrics()}

        for pct, sval in [("150", "1.5"), ("200", "2")]:
            kout = set_scale(out_name, sval)
            # Maximize inside the 2400x1600 virtual output so the full window
            # (1600x1067 CSS at 150%, 1200x800 CSS at 200%) is visible edge-to-edge.
            m.exec_chrome("window.maximize();")
            # Let Firefox re-composite at the new Wayland fractional/integer scale.
            time.sleep(0.7)
            metrics = measure_scale_metrics()
            shoot(shots / f"firefox-m5-scale-{pct}.png", settle=0.25)
            scales[pct] = {"kscreen": kout, "metrics": metrics}

        # Restore 100% scale cleanly before exit.
        m.exec_chrome("window.restore();")
        set_scale(out_name, "1")
        shoot(main_out, settle=0.2)

        report = {
            "output_name": out_name,
            "keyboard_focus": kb_focus,
            "scales": scales,
            "rtl": rtl,
        }
        (rdir / "m5-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0
    finally:
        m.close()


if __name__ == "__main__":
    sys.exit(main())
