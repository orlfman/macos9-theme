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


def collapsed_tab_geometry(m: Marionette, *, private: bool = False) -> dict:
    return m.exec_chrome(
        """
        const win = arguments[0] ? window._m4Priv : window;
        const done = arguments[arguments.length - 1];
        (async () => {
          const tabs = win.document.getElementById("tabbrowser-tabs");
          win.SidebarController._state.launcherExpanded = false;
          await new Promise(r => setTimeout(r, 450));
          const center = el => {
            const rect = el.getBoundingClientRect();
            return rect.x + rect.width / 2;
          };
          const rail = win.document.getElementById("vertical-tabs");
          const plus = win.document.querySelector("#tabs-newtab-button .toolbarbutton-icon");
          const frames = Array.from(win.gBrowser.tabs, tab => {
            const frame = tab.querySelector(".tab-background");
            const icon = tab.querySelector(".tab-icon-image");
            return { visible: icon.checkVisibility({visibilityProperty: true, opacityProperty: true}),
                     width: icon.getBoundingClientRect().width,
                     offset: center(icon) - center(frame), plusOffset: center(icon) - center(plus) };
          });
          done({ privateMode: win.document.documentElement.getAttribute("privatebrowsingmode"),
                 vertical: tabs.getAttribute("orient") === "vertical", expanded: tabs.hasAttribute("expanded"),
                 selectedBg: win.getComputedStyle(win.gBrowser.selectedTab.querySelector(".tab-background")).backgroundColor,
                 frames, plusWidth: plus.getBoundingClientRect().width, plusOffset: center(plus) - center(rail) });
        })();
        """,
        [private],
        async_mode=True,
    )


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
              await window.delayedStartupPromise;
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
              const idleImg = idleCS.backgroundImage;
              const idleW = idleCS.width;
              const logo = document.createElementNS("http://www.w3.org/1999/xhtml", "img");
              logo.src = idleImg.slice(5, -2);
              const logoLoaded = await logo.decode().then(() => logo.naturalWidth > 0, () => false);

              gBrowser.selectedTab.setAttribute("busy", "");
              await new Promise(r => setTimeout(r, 200));
              const busyCS = getComputedStyle(panelBtn, "::after");
              const busyBg = busyCS.backgroundColor;
              const busyImg = busyCS.backgroundImage;
              done({ logoLoaded, idleBg, idleImg, idleW, busyBg, busyImg });
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
        tabs_1c["collapsed"] = collapsed_tab_geometry(m)
        shoot(shots / "firefox-m4-vertical-collapsed.png", settle=0.2)
        m.exec_chrome("SidebarController._state.launcherExpanded = true;")
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
              const homeEl = document.getElementById("home-button");
              const bmEl = document.querySelector("#PlacesToolbarItems > .bookmark-item");
              const tabEl = gBrowser.selectedTab;
              InspectorUtils.addPseudoClassLock(homeEl, ":focus-visible");
              if (bmEl) InspectorUtils.addPseudoClassLock(bmEl, ":focus-visible");
              InspectorUtils.addPseudoClassLock(tabEl, ":focus-visible");

              const navCS = getComputedStyle(document.getElementById("nav-bar"));
              const urlCCS = getComputedStyle(document.getElementById("urlbar-container"));
              const urlBgCS = getComputedStyle(document.querySelector("#urlbar > .urlbar-background"));
              const homeCS = getComputedStyle(homeEl);
              const bmCS = bmEl ? getComputedStyle(bmEl) : null;
              const tabBgCS = getComputedStyle(tabEl.querySelector(".tab-background"));

              const popRoot = pop.document.documentElement;
              const popNavH = Math.round(pop.document.getElementById("nav-bar").getBoundingClientRect().height);
              const popStatusContent = getComputedStyle(pop.document.body, "::after").content;
              window._m4Popup = pop;

              const snapshot = {
                mainInactive,
                inactiveNavBgImg: navCS.backgroundImage,
                inactiveNavBg: navCS.backgroundColor,
                inactiveUrlCBg: urlCCS.backgroundColor,
                inactiveUrlOutline: urlBgCS.outlineStyle,
                inactiveHomeOutline: homeCS.outlineStyle,
                inactiveBmOutline: bmCS ? bmCS.outlineStyle : null,
                inactiveTabOutline: tabBgCS.outlineStyle,
                inactiveHomeColor: homeCS.color,
                popupHasAttr: popRoot.hasAttribute("popup-window"),
                popupNavHeight: popNavH,
                popupStatusAfterContent: popStatusContent
              };
              InspectorUtils.clearPseudoClassLocks(homeEl);
              if (bmEl) InspectorUtils.clearPseudoClassLocks(bmEl);
              InspectorUtils.clearPseudoClassLocks(tabEl);

              done(snapshot);
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
        # With browser.theme.dark-private-windows=false, Private windows obey
        # Platinum in System light mode while still respecting System Dark mode!
        private_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const pwin = OpenBrowserWindow({ private: true });
              await new Promise(r => pwin.addEventListener("load", r, { once: true }));
              await new Promise(r => setTimeout(r, 600));
              const pRoot = pwin.document.documentElement;
              const pPrefersLight = pwin.matchMedia("(prefers-color-scheme: light)").matches;
              const pUrlBg = getComputedStyle(pwin.document.getElementById("urlbar-container")).backgroundImage;
              const pStatusDisplay = getComputedStyle(pwin.document.body, "::after").display;
              const pIndBtn = pwin.document.querySelector(".private-browsing-indicator-button");
              const pIndVisible = !!(pIndBtn && pIndBtn.checkVisibility({ opacityProperty: true, visibilityProperty: true })
                                    && pIndBtn.getBoundingClientRect().width >= 16);

              Services.prefs.setIntPref("ui.systemUsesDarkTheme", 1);
              await new Promise(r => setTimeout(r, 250));
              const prefersDark = pwin.matchMedia("(prefers-color-scheme: dark)").matches;
              const pDarkUrlBg = getComputedStyle(pwin.document.getElementById("urlbar-container")).backgroundImage;
              Services.prefs.clearUserPref("ui.systemUsesDarkTheme");
              await new Promise(r => setTimeout(r, 250));

              window._m4Priv = pwin;
              done({
                privateAttr: pRoot.getAttribute("privatebrowsingmode"),
                prefersLight: pPrefersLight,
                privateUrlTube: pUrlBg,
                privateStatusDisplay: pStatusDisplay,
                privateIndicatorVisible: pIndVisible,
                darkModeGatedOff: prefersDark && !pDarkUrlBg.includes("rgb(27, 27, 82)")
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots / "firefox-m4-private.png", settle=0.2)
        m.exec_chrome("""
            Services.prefs.setBoolPref("sidebar.verticalTabs", true);
            window._m4Priv.gBrowser.addTrustedTab("about:robots");
        """)
        private_info["collapsed"] = collapsed_tab_geometry(m, private=True)
        m.exec_chrome('Services.prefs.setBoolPref("sidebar.verticalTabs", false);')
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
