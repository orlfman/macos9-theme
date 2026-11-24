#!/usr/bin/env python3
"""Interactive Milestone 4 verification probe for firefox/chrome/.

Exercises every Milestone 4 surface in isolated nested KWin Wayland:
  - 1A horizontal Platinum tabs (normal #CCCCCC, active #EEEEEE, pressed #666666/white)
  - 1C live switch to vertical Platinum tabs in left sidebar (sidebar.verticalTabs=true)
  - Busy-tab neutral Platinum Lavender activity indicator (:has(.tabbrowser-tab[selected][busy]))
  - Permanent 16 px IE5 status band (5A) + fullscreen suppression
  - Menubar + Platinum File menu popup (#DDDDDD frame, 0 px radius, #333399 highlight)
  - AppMenu (#appMenu-popup) & Downloads (#downloadsPanel) Platinum panels
  - Square Platinum urlbar results popup (.urlbarView, 0 px radius, #333399 row)
  - Find bar (gFindBar.open()) + Notification bar (appendNotification)
  - Sidebar framing (Bookmarks sidebar)
  - Real inactive window (:-moz-window-inactive via second dialog window!)
  - Private browsing window (OpenBrowserWindow({ private: true }))
  - Popup window without toolbars (window.openDialog / popup)
  - Customize Mode & theme/dark/HighContrast gating

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
    rdir = pathlib.Path(os.environ["M9_M4_DIR"])
    shots = main_out.parent

    m = Marionette(port)
    try:
        m.send("WebDriver:NewSession", {"capabilities": {}})
        m.send("Marionette:SetContext", {"value": "chrome"})

        # Wait for delayed startup & open 2 extra tabs so we have 3 real tabs.
        tabs_1a = m.exec_chrome(
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
              const p2 = gBrowser.addTrustedTab("about:robots");
              const p3 = gBrowser.addTrustedTab("about:support");
              gBrowser.selectedTab = p1;
              await new Promise(r => setTimeout(r, 400));

              const selBg = getComputedStyle(p1.querySelector(".tab-background")).backgroundColor;
              const inactBg = getComputedStyle(p2.querySelector(".tab-background")).backgroundColor;
              InspectorUtils.addPseudoClassLock(p2, ":hover");
              InspectorUtils.addPseudoClassLock(p2, ":active");
              const pressedBg = getComputedStyle(p2.querySelector(".tab-background")).backgroundColor;
              const pressedLabel = getComputedStyle(p2.querySelector(".tab-label")).color;
              InspectorUtils.clearPseudoClassLocks(p2);

              const favR = document.getElementById("PersonalToolbar").getBoundingClientRect();
              const tabsR = document.getElementById("TabsToolbar").getBoundingClientRect();
              const statusAfter = getComputedStyle(document.body, "::after");

              done({
                tabCount: gBrowser.tabs.length,
                tabsBelowFavs: Math.round(tabsR.y) >= Math.round(favR.y + favR.height - 1),
                tabsHeight: Math.round(tabsR.height),
                selBg,
                inactBg,
                pressedBg,
                pressedLabel,
                statusBandDisplay: statusAfter.display,
                statusBandHeight: statusAfter.height
              });
            })();
            """,
            async_mode=True,
        )

        # 1. Busy-tab neutral Platinum Lavender activity indicator (:has(.tabbrowser-tab[selected][busy])).
        activity_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const panelBtn = document.getElementById("PanelUI-button");
              const idleCS = getComputedStyle(panelBtn, "::after");
              const idleBg = idleCS.backgroundColor;
              const idleW = idleCS.width;

              gBrowser.selectedTab.setAttribute("busy", "");
              await new Promise(r => setTimeout(r, 200));
              const busyCS = getComputedStyle(panelBtn, "::after");
              const busyBg = busyCS.backgroundColor;
              const busyImg = busyCS.backgroundImage;
              done({ idleBg, idleW, busyBg, busyImg });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-activity-busy.png", settle=0.2)
        m.exec_chrome('gBrowser.selectedTab.removeAttribute("busy");')

        # 2. Live switch 1A -> 1C (Vertical Platinum tabs in left sidebar) and back!
        tabs_1c = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              Services.prefs.setBoolPref("sidebar.verticalTabs", true);
              await new Promise(r => setTimeout(r, 450));
              const tabs = document.getElementById("tabbrowser-tabs");
              const sc = document.getElementById("sidebar-container");
              const scCS = getComputedStyle(sc);
              const selBg = getComputedStyle(gBrowser.selectedTab.querySelector(".tab-background")).backgroundColor;
              const otherTab = gBrowser.tabs[1];
              const inactBg = getComputedStyle(otherTab.querySelector(".tab-background")).backgroundColor;
              done({
                orient: tabs.getAttribute("orient"),
                tabsHiddenAttr: document.getElementById("navigator-toolbox").hasAttribute("tabs-hidden"),
                sidebarContainerBgImg: scCS.backgroundImage,
                sidebarWidth: Math.round(sc.getBoundingClientRect().width),
                selBg,
                inactBg
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-vertical-1c.png", settle=0.2)
        m.exec_chrome('Services.prefs.setBoolPref("sidebar.verticalTabs", false);')
        time.sleep(0.35)

        # 3. Platinum Menubar + File Menu Popup (measured #DDDDDD frame, 0px radius, #333399 hover).
        menu_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const mb = document.getElementById("toolbar-menubar");
              mb.removeAttribute("autohide");
              const fm = document.getElementById("file-menu");
              const fp = document.getElementById("menu_FilePopup");
              await new Promise(r => setTimeout(r, 150));
              fp.openPopup(fm, "after_start", 0, 0, false, false);
              await new Promise(r => setTimeout(r, 250));
              const item = fp.querySelector("menuitem:not([hidden]):not([disabled])");
              if (item) item.setAttribute("_moz-menuactive", "true");
              await new Promise(r => setTimeout(r, 100));
              const contentPart = fp.shadowRoot ? fp.shadowRoot.querySelector('[part~="content"]') : null;
              const pcs = contentPart ? getComputedStyle(contentPart) : getComputedStyle(fp);
              const ics = item ? getComputedStyle(item) : null;
              done({
                popupState: fp.state,
                panelBg: pcs.backgroundColor,
                panelBorderRadius: pcs.borderTopLeftRadius,
                panelBorderColor: pcs.borderTopColor,
                activeItemBg: ics ? ics.backgroundColor : null,
                activeItemColor: ics ? ics.color : null
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-menu-file.png", settle=0.2)
        m.exec_chrome(
            """
            const fp = document.getElementById("menu_FilePopup");
            const item = fp.querySelector("menuitem[_moz-menuactive]");
            if (item) item.removeAttribute("_moz-menuactive");
            fp.hidePopup();
            document.getElementById("toolbar-menubar").setAttribute("autohide", "true");
            """
        )

        # 4. Platinum AppMenu (#appMenu-popup) panel.
        panel_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              await PanelUI.show();
              await new Promise(r => setTimeout(r, 300));
              const p = document.getElementById("appMenu-popup");
              const contentPart = p.shadowRoot ? p.shadowRoot.querySelector('[part~="content"]') : null;
              const pcs = contentPart ? getComputedStyle(contentPart) : getComputedStyle(p);
              done({
                state: p.state,
                bg: pcs.backgroundColor,
                radius: pcs.borderTopLeftRadius,
                border: pcs.borderTopColor
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-panel-appmenu.png", settle=0.2)
        m.exec_chrome("PanelUI.hide();")

        # 5. Square Platinum URL bar autocomplete popup.
        url_popup_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              gURLBar.focus();
              gURLBar.value = "about";
              gURLBar.startQuery({ searchString: "about" });
              await new Promise(r => setTimeout(r, 400));
              const url = document.getElementById("urlbar");
              const view = url.querySelector(".urlbarView");
              const vcs = getComputedStyle(view);
              const selRow = view.querySelector(".urlbarView-row[selected] > .urlbarView-row-inner");
              const rcs = selRow ? getComputedStyle(selRow) : null;
              done({
                isOpen: url.hasAttribute("open"),
                viewRadius: vcs.borderBottomLeftRadius,
                viewBorder: vcs.borderBottomColor,
                viewBg: vcs.backgroundColor,
                selRowBg: rcs ? rcs.backgroundColor : null,
                selRowColor: rcs ? rcs.color : null
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-urlbar-popup.png", settle=0.2)
        m.exec_chrome("gURLBar.handleRevert(); gURLBar.view.close(); gBrowser.selectedBrowser.focus();")

        # 6. Find Bar + Notification Bar + Legacy Sidebar open together!
        bars_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              await gBrowser.getFindBar();
              gFindBar.open();
              gFindBar._findField.value = "Platinum";
              gFindBar._findField.focus();

              const nb = gBrowser.getNotificationBox();
              nb.appendNotification(
                "m4-test-notif",
                { label: "Platinum notification bar test message.", priority: nb.PRIORITY_INFO_MEDIUM },
                [{ label: "OK", callback: () => {} }]
              );

              Services.prefs.setBoolPref("sidebar.revamp", false);
              await SidebarController.show("viewBookmarksSidebar");
              await new Promise(r => setTimeout(r, 350));

              const fbCS = getComputedStyle(gFindBar);
              const ffCS = getComputedStyle(gFindBar._findField);
              const notifEl = nb.currentNotification;
              const nCS = notifEl ? getComputedStyle(notifEl) : null;
              const sbCS = getComputedStyle(document.getElementById("sidebar-header"));

              done({
                findbarHidden: gFindBar.hidden,
                findbarBg: fbCS.backgroundColor,
                findFieldBg: ffCS.backgroundColor,
                findFieldBorder: ffCS.borderTopColor,
                findFieldRadius: ffCS.borderTopLeftRadius,
                notifVisible: !!notifEl,
                notifBg: nCS ? nCS.backgroundColor : null,
                sidebarHeaderBgImg: sbCS.backgroundImage
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-bars-sidebar.png", settle=0.2)
        m.exec_chrome(
            """
            gFindBar.close();
            const nb = gBrowser.getNotificationBox();
            if (nb.currentNotification) nb.removeNotification(nb.currentNotification, true);
            SidebarController.hide();
            Services.prefs.setBoolPref("sidebar.revamp", true);
            """
        )

        # 7. Real Inactive Window state (:-moz-window-inactive) + Popup Window check!
        # Opening a real popup window deactivates the main browser window in KWin Wayland!
        inactive_and_popup = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              gURLBar.focus();
              const pop = window.openDialog(
                AppConstants.BROWSER_CHROME_URL,
                "_blank",
                "popup=yes,width=480,height=320,left=720,top=360",
                "about:blank"
              );
              await new Promise(r => pop.addEventListener("load", r, { once: true }));
              await new Promise(r => setTimeout(r, 600));
              pop.focus();
              await new Promise(r => setTimeout(r, 300));

              const mainInactive = window.document.documentElement.matches(":-moz-window-inactive");
              const navCS = getComputedStyle(document.getElementById("nav-bar"));
              const urlCCS = getComputedStyle(document.getElementById("urlbar-container"));
              const urlBgCS = getComputedStyle(document.querySelector("#urlbar > .urlbar-background"));
              const homeCS = getComputedStyle(document.getElementById("home-button"));

              const popRoot = pop.document.documentElement;
              const popNavH = Math.round(pop.document.getElementById("nav-bar").getBoundingClientRect().height);
              const popStatusContent = getComputedStyle(pop.document.body, "::after").content;
              window._m4Popup = pop;

              done({
                mainInactive,
                inactiveNavBgImg: navCS.backgroundImage,
                inactiveNavBg: navCS.backgroundColor,
                inactiveUrlCBg: urlCCS.backgroundColor,
                inactiveUrlOutline: urlBgCS.outlineStyle,
                inactiveHomeColor: homeCS.color,
                popupHasAttr: popRoot.hasAttribute("popup-window"),
                popupNavHeight: popNavH,
                popupStatusAfterContent: popStatusContent
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-inactive-and-popup.png", settle=0.2)
        m.exec_chrome(
            """
            if (window._m4Popup && !window._m4Popup.closed) window._m4Popup.close();
            window.focus();
            """
        )
        time.sleep(0.3)

        # 8. Private Browsing Window check!
        private_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const pwin = OpenBrowserWindow({ private: true });
              await new Promise(r => pwin.addEventListener("load", r, { once: true }));
              await new Promise(r => setTimeout(r, 600));
              const pRoot = pwin.document.documentElement;
              const pPrefersDark = pwin.matchMedia("(prefers-color-scheme: dark)").matches;
              const pUrlBg = getComputedStyle(pwin.document.getElementById("urlbar-container")).backgroundImage;
              const pStatusContent = getComputedStyle(pwin.document.body, "::after").content;
              window._m4Priv = pwin;
              done({
                privateAttr: pRoot.getAttribute("privatebrowsingmode"),
                prefersDark: pPrefersDark,
                privateUrlTube: pUrlBg,
                privateStatusContent: pStatusContent
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-private.png", settle=0.2)
        m.exec_chrome(
            """
            if (window._m4Priv && !window._m4Priv.closed) window._m4Priv.close();
            window.focus();
            """
        )
        time.sleep(0.3)

        # 9. Fullscreen check: verify permanent status band disappears cleanly in fullscreen!
        fullscreen_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              window.fullScreen = true;
              await new Promise(r => setTimeout(r, 450));
              const inFs = document.documentElement.hasAttribute("inFullscreen");
              const statusAfterContent = getComputedStyle(document.body, "::after").content;
              window.fullScreen = false;
              await new Promise(r => setTimeout(r, 400));
              const restoredStatus = getComputedStyle(document.body, "::after").display;
              done({ inFs, statusAfterContentInFullscreen: statusAfterContent, restoredStatus });
            })();
            """,
            async_mode=True,
        )

        # 10. Customize Mode check!
        customize_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const entered = new Promise(r => window.gNavToolbox.addEventListener("customizationready", r, { once: true }));
              gCustomizeMode.enter();
              await entered;
              await new Promise(r => setTimeout(r, 250));
              const custBg = getComputedStyle(document.getElementById("customization-container")).backgroundColor;
              const urlPos = getComputedStyle(document.getElementById("urlbar-container")).position;
              const exited = new Promise(r => window.gNavToolbox.addEventListener("aftercustomization", r, { once: true }));
              gCustomizeMode.exit();
              await exited;
              await new Promise(r => setTimeout(r, 250));
              done({ custBg, urlPosInCustomize: urlPos, cleared: !document.documentElement.hasAttribute("customizing") });
            })();
            """,
            async_mode=True,
        )

        # 11. Built-in theme + dark-mode + HighContrast gating still 100% clean across all M4 modules!
        theme_matrix = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const { AddonManager } = ChromeUtils.importESModule("resource://gre/modules/AddonManager.sys.mjs");
              const rows = [];
              async function snap(label) {
                await new Promise(r => setTimeout(r, 250));
                const urlBg = getComputedStyle(document.getElementById("urlbar-container")).backgroundImage;
                const statusD = getComputedStyle(document.body, "::after").display;
                rows.push({
                  label,
                  platinumActive: urlBg.includes("rgb(27, 27, 82)") && statusD === "block"
                });
              }
              for (const id of [
                "default-theme@mozilla.org",
                "firefox-compact-light@mozilla.org",
                "firefox-compact-dark@mozilla.org",
                "firefox-alpenglow@mozilla.org"
              ]) {
                const a = await AddonManager.getAddonByID(id);
                if (a) { await a.enable(); await snap(id); }
              }
              const defA = await AddonManager.getAddonByID("default-theme@mozilla.org");
              await defA.enable();
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
        hc_on = m.exec_chrome(
            'return getComputedStyle(document.getElementById("urlbar-container")).backgroundImage.includes("rgb(27, 27, 82)");'
        )
        theme_matrix.append({"label": "default-theme+high-contrast", "platinumActive": hc_on})
        subprocess.run(["gsettings", "set", "org.gnome.desktop.a11y.interface", "high-contrast", "false"], check=True)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Platinum"], check=True)
        time.sleep(0.45)
        restored_on = m.exec_chrome(
            'return getComputedStyle(document.getElementById("urlbar-container")).backgroundImage.includes("rgb(27, 27, 82)");'
        )
        theme_matrix.append({"label": "default-theme-restored", "platinumActive": restored_on})

        shoot(main_out, settle=0.2)

        report = {
            "tabs_1a": tabs_1a,
            "activity": activity_info,
            "tabs_1c": tabs_1c,
            "menu": menu_info,
            "panel": panel_info,
            "url_popup": url_popup_info,
            "bars": bars_info,
            "inactive_and_popup": inactive_and_popup,
            "private": private_info,
            "fullscreen": fullscreen_info,
            "customize": customize_info,
            "theme_matrix": theme_matrix,
        }
        (rdir / "m4-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0
    finally:
        m.close()


if __name__ == "__main__":
    sys.exit(main())
