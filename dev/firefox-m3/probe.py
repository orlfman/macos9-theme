#!/usr/bin/env python3
"""Interactive Milestone 3 state & robustness probe for firefox/chrome/.

Runs inside nested virtual KWin via dev/firefox-test.sh with the real
firefox/chrome/ stylesheet loaded through the normal profile path, inspecting:
  - 56 px button pitch & geometry of all 3 top bands
  - Button hover (:hover lock) and pressed (:hover + :active lock) renders
  - Address field focused (#6666CC 2 px ring) + selected text (#CCCCFF) render
  - Address bar live query / open autocomplete dropdown (.urlbarView visible)
  - Narrow-window real OverflowableToolbar overflow (520 px)
  - Customize Mode enter & exit round-trip
  - Built-in theme / dark-mode / GTK HighContrast gating (deactivates cleanly)

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "firefox-m1"))
from probe import Marionette, shoot  # noqa: E402


def main() -> int:
    port = int(os.environ["M9_MARIONETTE_PORT"])
    main_out = pathlib.Path(os.environ["M9_OUT"])
    rdir = pathlib.Path(os.environ["M9_M3_DIR"])
    shots = main_out.parent

    m = Marionette(port)
    try:
        m.send("WebDriver:NewSession", {"capabilities": {}})
        m.send("Marionette:SetContext", {"value": "chrome"})

        # Wait for delayed startup & measure geometry of the 3 top bands.
        geom = m.exec_chrome(
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
              await new Promise(r => setTimeout(r, 300));

              const nav = document.getElementById("nav-bar");
              const navR = nav.getBoundingClientRect();
              const urlC = document.getElementById("urlbar-container");
              const urlCR = urlC.getBoundingClientRect();
              const urlEl = document.getElementById("urlbar");
              const urlR = urlEl.getBoundingClientRect();
              const fav = document.getElementById("PersonalToolbar");
              const favR = fav.getBoundingClientRect();
              const home = document.getElementById("home-button");
              const homeR = home.getBoundingClientRect();
              const back = document.getElementById("back-button");
              const backR = back.getBoundingClientRect();
              const backCS = getComputedStyle(back);
              const homeCS = getComputedStyle(home);
              const goBtn = urlEl.querySelector(".urlbar-go-button");
              const goR = goBtn ? goBtn.getBoundingClientRect() : null;
              const goCS = goBtn ? getComputedStyle(goBtn) : null;

              done({
                navRect: { x: Math.round(navR.x), y: Math.round(navR.y), w: Math.round(navR.width), h: Math.round(navR.height) },
                urlContainerRect: { x: Math.round(urlCR.x), y: Math.round(urlCR.y), w: Math.round(urlCR.width), h: Math.round(urlCR.height) },
                urlbarRect: { x: Math.round(urlR.x), y: Math.round(urlR.y), w: Math.round(urlR.width), h: Math.round(urlR.height) },
                goButton: goR ? { hit: document.elementFromPoint(goR.x + goR.width / 2, goR.y + goR.height / 2) === goBtn, display: goCS.display, x: Math.round(goR.x), y: Math.round(goR.y), w: Math.round(goR.width), h: Math.round(goR.height) } : null,
                favRect: { x: Math.round(favR.x), y: Math.round(favR.y), w: Math.round(favR.width), h: Math.round(favR.height) },
                homeRect: { x: Math.round(homeR.x), y: Math.round(homeR.y), w: Math.round(homeR.width), h: Math.round(homeR.height) },
                backRect: { x: Math.round(backR.x), y: Math.round(backR.y), w: Math.round(backR.width), h: Math.round(backR.height) },
                backDisabled: back.hasAttribute("disabled"),
                backColor: backCS.color,
                backFill: backCS.fill,
                homeColor: homeCS.color,
                homeFill: homeCS.fill,
                overflowingWide: nav.hasAttribute("overflowing")
              });
            })();
            """,
            async_mode=True,
        )

        # 1. Hover state on #home-button & first bookmark via InspectorUtils pseudo-class lock.
        hover_info = m.exec_chrome(
            """
            const home = document.getElementById("home-button");
            const bm = document.querySelector("#PlacesToolbarItems > .bookmark-item");
            InspectorUtils.addPseudoClassLock(home, ":hover");
            if (bm) InspectorUtils.addPseudoClassLock(bm, ":hover");
            const hcs = getComputedStyle(home);
            const bcs = bm ? getComputedStyle(bm) : null;
            return {
              homeHoverBg: hcs.backgroundColor,
              homeHoverBorderTop: hcs.borderTopColor,
              homeHoverBorderBottom: hcs.borderBottomColor,
              bmHoverBg: bcs ? bcs.backgroundColor : null
            };
            """
        )
        shoot(shots / "firefox-m3-btn-hover.png", settle=0.25)

        # 2. Pressed state on #home-button & first bookmark (:hover + :active lock).
        pressed_info = m.exec_chrome(
            """
            const home = document.getElementById("home-button");
            const bm = document.querySelector("#PlacesToolbarItems > .bookmark-item");
            InspectorUtils.addPseudoClassLock(home, ":active");
            if (bm) InspectorUtils.addPseudoClassLock(bm, ":active");
            const hcs = getComputedStyle(home);
            const bcs = bm ? getComputedStyle(bm) : null;
            return {
              homePressedBg: hcs.backgroundColor,
              homePressedColor: hcs.color,
              bmPressedBg: bcs ? bcs.backgroundColor : null,
              bmPressedColor: bcs ? bcs.color : null
            };
            """
        )
        shoot(shots / "firefox-m3-btn-pressed.png", settle=0.25)

        # Clear button locks before testing URL bar focus & selection.
        m.exec_chrome(
            """
            const home = document.getElementById("home-button");
            const bm = document.querySelector("#PlacesToolbarItems > .bookmark-item");
            InspectorUtils.clearPseudoClassLocks(home);
            if (bm) InspectorUtils.clearPseudoClassLocks(bm);
            """
        )

        # 3. URL bar focused (2 px #6666CC focus ring) + selected text (#CCCCFF).
        url_focus_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              gURLBar.focus();
              gURLBar.select();
              await new Promise(r => setTimeout(r, 250));
              const url = document.getElementById("urlbar");
              const bg = url.querySelector(".urlbar-background");
              const cs = getComputedStyle(bg);
              const selCS = getComputedStyle(gURLBar.inputField, "::selection");
              done({
                hasFocusedAttr: url.hasAttribute("focused"),
                bgOutlineWidth: cs.outlineWidth,
                bgOutlineColor: cs.outlineColor,
                bgBorderColor: cs.borderTopColor,
                selectionBg: selCS.backgroundColor,
                selectionStart: gURLBar.inputField.selectionStart,
                selectionEnd: gURLBar.inputField.selectionEnd
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m3-urlbar-focused.png", settle=0.25)

        # 4. URL bar live autocomplete dropdown ([open="true"] / [breakout-extend="true"]).
        url_open_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              gURLBar.value = "about";
              gURLBar.startQuery({ searchString: "about" });
              await new Promise(r => setTimeout(r, 450));
              const url = document.getElementById("urlbar");
              const view = url.querySelector(".urlbarView");
              const vr = view ? view.getBoundingClientRect() : null;
              const ur = url.getBoundingClientRect();
              const go = url.querySelector(".urlbar-go-button");
              const rect = go.getBoundingClientRect();
              done({
                goHit: document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2) === go,
                isOpen: url.hasAttribute("open"),
                breakoutExtend: url.getAttribute("breakout-extend"),
                urlbarRect: { x: Math.round(ur.x), y: Math.round(ur.y), w: Math.round(ur.width), h: Math.round(ur.height) },
                viewRect: vr ? { x: Math.round(vr.x), y: Math.round(vr.y), w: Math.round(vr.width), h: Math.round(vr.height) } : null
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m3-urlbar-open.png", settle=0.25)

        m.exec_chrome(
            """
            gURLBar.handleRevert();
            gURLBar.view.close();
            gBrowser.selectedBrowser.focus();
            """
        )

        # Submit an offline address with a pointer click on the actual Go control.
        goal = m.exec_chrome('return gBrowser.currentURI.spec.split("#")[0] + "#go-check";')
        m.exec_chrome("""
            gURLBar.focus();
            gURLBar.value = arguments[0];
            gURLBar.inputField.dispatchEvent(new window.Event("input", { bubbles: true }));
        """, [goal])
        time.sleep(0.3)
        x, y = m.exec_chrome("""
            const r = document.querySelector("#urlbar .urlbar-go-button").getBoundingClientRect();
            return [Math.floor(r.x + r.width / 2), Math.floor(r.y + r.height / 2)];
        """)
        m.send("WebDriver:PerformActions", {"actions": [{
            "type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
            "actions": [{"type": "pointerMove", "x": x, "y": y},
                        {"type": "pointerDown", "button": 0}, {"type": "pointerUp", "button": 0}],
        }]})
        for _ in range(30):
            if m.exec_chrome("return gBrowser.currentURI.spec;") == goal:
                break
            time.sleep(0.1)
        go_navigated = m.exec_chrome("return gBrowser.currentURI.spec;") == goal

        # 5. Narrow-window real overflow + Customize Mode round-trip.
        narrow_and_customize = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              CustomizableUI.addWidgetToArea("save-page-button", "nav-bar", 7);
              CustomizableUI.addWidgetToArea("zoom-controls", "nav-bar", 8);
              window.resizeTo(520, 700);
              await new Promise(r => setTimeout(r, 450));
              const nav = document.getElementById("nav-bar");
              const narrowOverflow = nav.hasAttribute("overflowing");
              const narrowUrlW = Math.round(document.getElementById("urlbar-container").getBoundingClientRect().width);

              CustomizableUI.removeWidgetFromArea("save-page-button");
              CustomizableUI.removeWidgetFromArea("zoom-controls");
              window.resizeTo(1120, 740);
              await new Promise(r => setTimeout(r, 350));

              const entered = new Promise(r => window.gNavToolbox.addEventListener("customizationready", r, { once: true }));
              gCustomizeMode.enter();
              await entered;
              await new Promise(r => setTimeout(r, 250));
              const urlPosInCust = getComputedStyle(document.getElementById("urlbar-container")).position;

              const exited = new Promise(r => window.gNavToolbox.addEventListener("aftercustomization", r, { once: true }));
              gCustomizeMode.exit();
              await exited;
              await new Promise(r => setTimeout(r, 300));
              const urlPosAfterCust = getComputedStyle(document.getElementById("urlbar-container")).position;
              const overflowAfterCust = nav.hasAttribute("overflowing");

              done({
                narrowOverflow,
                narrowUrlW,
                urlPosInCust,
                urlPosAfterCust,
                overflowAfterCust
              });
            })();
            """,
            async_mode=True,
        )

        # 6. Theme / dark-mode / HighContrast gating matrix on the REAL firefox/chrome/ stylesheet.
        theme_matrix = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const { AddonManager } = ChromeUtils.importESModule("resource://gre/modules/AddonManager.sys.mjs");
              const ids = [
                "default-theme@mozilla.org",
                "firefox-compact-light@mozilla.org",
                "firefox-compact-dark@mozilla.org",
                "firefox-alpenglow@mozilla.org"
              ];
              const rows = [];
              async function snap(label) {
                await new Promise(r => setTimeout(r, 280));
                const urlC = document.getElementById("urlbar-container");
                const bg = getComputedStyle(urlC).backgroundImage;
                rows.push({
                  label,
                  platinumActive: bg.includes("rgb(27, 27, 82)")
                });
              }
              for (const id of ids) {
                const addon = await AddonManager.getAddonByID(id);
                if (addon) {
                  await addon.enable();
                  await snap(id);
                }
              }
              const defAddon = await AddonManager.getAddonByID("default-theme@mozilla.org");
              await defAddon.enable();
              Services.prefs.setIntPref("ui.systemUsesDarkTheme", 1);
              await snap("default-theme+dark");
              Services.prefs.clearUserPref("ui.systemUsesDarkTheme");
              done(rows);
            })();
            """,
            async_mode=True,
        )

        subprocess.run(["gsettings", "set", "org.gnome.desktop.a11y.interface", "high-contrast", "true"], check=True)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "HighContrast"], check=True)
        time.sleep(0.45)
        hc_active = m.exec_chrome(
            """
            return getComputedStyle(document.getElementById("urlbar-container")).backgroundImage.includes("rgb(27, 27, 82)");
            """
        )
        theme_matrix.append({"label": "default-theme+high-contrast", "platinumActive": hc_active})
        subprocess.run(["gsettings", "set", "org.gnome.desktop.a11y.interface", "high-contrast", "false"], check=True)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Platinum"], check=True)
        time.sleep(0.45)
        restored_active = m.exec_chrome(
            """
            return getComputedStyle(document.getElementById("urlbar-container")).backgroundImage.includes("rgb(27, 27, 82)");
            """
        )
        theme_matrix.append({"label": "default-theme-restored", "platinumActive": restored_active})

        shoot(main_out, settle=0.2)

        report = {
            "geom": geom,
            "hover": hover_info,
            "pressed": pressed_info,
            "url_focus": url_focus_info,
            "go_navigated": go_navigated,
            "url_open": url_open_info,
            "narrow_and_customize": narrow_and_customize,
            "theme_matrix": theme_matrix,
        }
        (rdir / "m3-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0
    finally:
        m.close()


if __name__ == "__main__":
    sys.exit(main())
