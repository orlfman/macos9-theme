#!/usr/bin/env python3
"""Live Firefox 160 chrome DOM, CSS, overflow, sidebar, GTK, and theme probe.

Connects to Firefox's built-in Marionette socket inside the isolated nested
KWin Wayland session started by dev/firefox-test.sh, executes chrome-context
inspections and interactions, captures Spectacle screenshots, and writes
structured JSON evidence for dev/firefox-m1/verify.py.

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import os
import pathlib
import socket
import subprocess
import sys
import time
from typing import Any


class Marionette:
    def __init__(self, port: int) -> None:
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=15.0)
        self.sock.settimeout(25.0)
        self.buf = b""
        self.msg_id = 0
        hello = self._recv_packet()
        if hello.get("marionetteProtocol") != 3:
            raise RuntimeError(f"Unexpected Marionette hello: {hello!r}")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def _recv_exact(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("Marionette socket closed unexpectedly")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _recv_packet(self) -> Any:
        while b":" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise EOFError("Marionette socket closed before header")
            self.buf += chunk
        sep = self.buf.index(b":")
        length = int(self.buf[:sep].decode("ascii"))
        self.buf = self.buf[sep + 1 :]
        raw = self._recv_exact(length)
        return json.loads(raw.decode("utf-8"))

    def send(self, command: str, params: dict[str, Any] | None = None) -> Any:
        self.msg_id += 1
        mid = self.msg_id
        payload = json.dumps([0, mid, command, params or {}], separators=(",", ":")).encode("utf-8")
        header = f"{len(payload)}:".encode("ascii")
        self.sock.sendall(header + payload)
        while True:
            pkt = self._recv_packet()
            if isinstance(pkt, list) and len(pkt) == 4 and pkt[0] == 1 and pkt[1] == mid:
                _, _, err, res = pkt
                if err is not None:
                    raise RuntimeError(f"Marionette {command} failed: {err!r}")
                return res

    def exec_chrome(self, script: str, args: list[Any] | None = None, async_mode: bool = False) -> Any:
        cmd = "WebDriver:ExecuteAsyncScript" if async_mode else "WebDriver:ExecuteScript"
        res = self.send(cmd, {"script": script, "args": args or []})
        return res.get("value") if isinstance(res, dict) else res


def shoot(path: pathlib.Path, settle: float = 0.4) -> None:
    time.sleep(settle)
    subprocess.run(["spectacle", "-b", "-n", "-f", "-o", str(path)], check=True)


def main() -> int:
    port = int(os.environ["M9_MARIONETTE_PORT"])
    main_out = pathlib.Path(os.environ["M9_OUT"])
    report_dir = pathlib.Path(os.environ["M9_FF_M1_DIR"])
    shots_dir = main_out.parent

    gtk_html = report_dir / "gtk-test.html"
    gtk_html.write_text(
        """<!doctype html>
<html><head><meta charset="utf-8"><title>Platinum Test Page</title>
<style>
  body { font: 13px sans-serif; margin: 16px; background: #ffffff; color: #000000; }
  .row { margin-bottom: 12px; display: flex; gap: 12px; align-items: center; }
  .scrollbox { width: 220px; height: 90px; overflow-y: scroll; border: 1px solid #888; padding: 6px; }
</style></head>
<body>
  <div class="row">
    <button id="btn">Push Button</button>
    <input id="txt" type="text" value="Selected sample">
    <label><input id="chk" type="checkbox" checked> Check</label>
    <select id="sel"><option>Lavender</option><option>Platinum</option></select>
  </div>
  <div class="scrollbox" id="sc">
    Line 1<br>Line 2<br>Line 3<br>Line 4<br>Line 5<br>Line 6<br>Line 7<br>Line 8<br>Line 9<br>Line 10
  </div>
</body></html>
""",
        encoding="utf-8",
    )

    m = Marionette(port)
    try:
        m.send("WebDriver:NewSession", {"capabilities": {}})
        m.send("Marionette:SetContext", {"value": "chrome"})

        # Wait for delayed startup and seed deterministic offline bookmarks.
        startup = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              if (window.gBrowserInit && !gBrowserInit.delayedStartupFinished) {
                await new Promise(r => {
                  const obs = (subj) => {
                    if (subj === window) {
                      Services.obs.removeObserver(obs, "browser-delayed-startup-finished");
                      r();
                    }
                  };
                  Services.obs.addObserver(obs, "browser-delayed-startup-finished");
                });
              }
              const bm = await PlacesUtils.bookmarks.insert({
                parentGuid: PlacesUtils.bookmarks.toolbarGuid,
                title: "Live Home Page",
                url: "about:blank"
              });
              const bm2 = await PlacesUtils.bookmarks.insert({
                parentGuid: PlacesUtils.bookmarks.toolbarGuid,
                title: "Apple Support",
                url: "about:robots"
              });
              await new Promise(r => setTimeout(r, 250));
              done({
                appVersion: AppConstants.MOZ_APP_VERSION_DISPLAY,
                platform: AppConstants.platform,
                novaEnabled: Services.prefs.getBoolPref("browser.nova.enabled", false),
                sidebarRevamp: Services.prefs.getBoolPref("sidebar.revamp", false),
                verticalTabs: Services.prefs.getBoolPref("sidebar.verticalTabs", false),
                inTitlebar: Services.prefs.getIntPref("browser.tabs.inTitlebar", -1),
                nonNativeTheme: Services.prefs.getBoolPref("widget.non-native-theme.enabled", false),
                gtkOverlayScrollbars: Services.prefs.getBoolPref("widget.gtk.overlay-scrollbars.enabled", true),
                bookmarksSeeded: [bm.guid, bm2.guid],
              });
            })();
            """,
            async_mode=True,
        )

        # 1. Chrome DOM & Shadow DOM inventory.
        dom_inventory = m.exec_chrome(
            """
            const selectors = [
              "#main-window",
              "#navigator-toolbox",
              "#toolbar-menubar",
              "#main-menubar",
              "#TabsToolbar",
              "#TabsToolbar-customization-target",
              "#tabbrowser-tabs",
              ".tabbrowser-tab[selected]",
              "#tabs-newtab-button",
              "#alltabs-button",
              "#nav-bar",
              "#nav-bar-customization-target",
              "#back-button",
              "#forward-button",
              "#stop-reload-button",
              "#reload-button",
              "#stop-button",
              "#home-button",
              "#urlbar-container",
              "#urlbar",
              "#urlbar .urlbar-background",
              "#urlbar .urlbar-input-container",
              "#urlbar-input",
              "#identity-box",
              "#trust-icon-container",
              "#page-action-buttons",
              "#downloads-button",
              "#unified-extensions-button",
              "#PanelUI-button",
              "#PanelUI-menu-button",
              "#nav-bar-overflow-button",
              "#PersonalToolbar",
              "#personal-bookmarks",
              "#PlacesToolbarItems",
              "#PlacesToolbarItems > .bookmark-item",
              "#browser",
              "#sidebar-container",
              "sidebar-main",
              "#vertical-tabs",
              "#sidebar-launcher-splitter",
              "#sidebar-box",
              "#sidebar-header",
              "#sidebar-panel-header",
              "#sidebar-splitter",
              "#tabbrowser-tabbox",
              "#statuspanel",
              "#statuspanel-label",
              "#appMenu-popup",
              "#contentAreaContextMenu",
              "#widget-overflow"
            ];

            function inspectNode(sel) {
              const el = document.querySelector(sel);
              if (!el) return { exists: false };
              const r = el.getBoundingClientRect();
              const cs = getComputedStyle(el);
              let shadow = null;
              if (el.shadowRoot) {
                const parts = Array.from(el.shadowRoot.querySelectorAll("[part]")).map(
                  n => ({ tag: n.tagName.toLowerCase(), part: n.getAttribute("part") })
                );
                const childTags = Array.from(el.shadowRoot.children).map(n => n.tagName.toLowerCase());
                shadow = {
                  mode: el.shadowRoot.mode,
                  childCount: el.shadowRoot.children.length,
                  childTags,
                  parts,
                  adoptedSheetCount: el.shadowRoot.adoptedStyleSheets ? el.shadowRoot.adoptedStyleSheets.length : 0
                };
              }
              return {
                exists: true,
                tag: el.tagName,
                ns: el.namespaceURI,
                id: el.id || null,
                hidden: el.hidden || cs.display === "none" || cs.visibility === "collapse",
                display: cs.display,
                appearance: cs.appearance,
                rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
                shadow
              };
            }

            const out = {};
            for (const s of selectors) out[s] = inspectNode(s);
            const appMenuLazyBeforeInit = !document.getElementById("appMenu-popup");
            if (window.PanelUI && PanelUI.ensureReady) {
              // Instantiate lazy appMenuPopupTemplate synchronously if supported, else record template presence.
              out["#appMenuPopupTemplate"] = inspectNode("#appMenuPopupTemplate");
            }

            const navPlacements = CustomizableUI.getWidgetIdsInArea("nav-bar");
            const homePlacement = CustomizableUI.getPlacementOfWidget("home-button");

            const navButtons = Array.from(document.querySelectorAll("#nav-bar .toolbarbutton-1")).map(b => {
              const txt = b.querySelector(".toolbarbutton-text");
              const icon = b.querySelector(".toolbarbutton-icon");
              return {
                id: b.id,
                cls: b.className,
                labelAttr: b.getAttribute("label"),
                tooltipAttr: b.getAttribute("tooltiptext"),
                ariaLabel: b.getAttribute("aria-label"),
                l10nId: b.getAttribute("data-l10n-id"),
                disabled: b.hasAttribute("disabled"),
                hasTextChild: !!txt,
                textValue: txt ? (txt.value || txt.textContent || "") : null,
                textDisplay: txt ? getComputedStyle(txt).display : null,
                hasIconChild: !!icon
              };
            });

            return {
              rootAttrs: Object.fromEntries(Array.from(document.documentElement.attributes).map(a => [a.name, a.value])),
              windowOuter: { x: window.mozInnerScreenX, y: window.mozInnerScreenY, w: window.innerWidth, h: window.innerHeight, dpr: window.devicePixelRatio },
              nodes: out,
              navPlacements,
              homePlacement,
              navButtons
            };
            """
        )

        # 2. GTK 3 Platinum inheritance (system CSS colors + local page + open menu).
        gtk_inheritance = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            const url = arguments[0];
            (async () => {
              gBrowser.selectedBrowser.fixupAndLoadURIString(url, { triggeringPrincipal: Services.scriptSecurityManager.getSystemPrincipal() });
              await new Promise(r => setTimeout(r, 600));

              const sysColors = [
                "-moz-headerbar", "-moz-headerbartext", "-moz-headerbarinactive", "-moz-headerbarinactivetext",
                "ActiveCaption", "CaptionText", "InactiveCaption", "InactiveCaptionText",
                "Canvas", "CanvasText", "Field", "FieldText", "ButtonFace", "ButtonText",
                "SelectedItem", "SelectedItemText", "ThreeDShadow", "AccentColor"
              ];
              const probe = document.createElement("div");
              document.documentElement.appendChild(probe);
              const resolvedColors = {};
              for (const c of sysColors) {
                probe.style.color = "";
                probe.style.color = c;
                resolvedColors[c] = getComputedStyle(probe).color;
              }
              probe.remove();

              // Check content-document form control appearances via SpecialPowers-free actor / eval in content?
              // In parent process, file:// browser may be remote, so inspect chrome prefs + open File menu popup.
              const fileMenu = document.getElementById("file-menu");
              const filePopup = document.getElementById("menu_FilePopup");
              document.getElementById("toolbar-menubar").removeAttribute("autohide");
              await new Promise(r => setTimeout(r, 150));
              filePopup.openPopup(fileMenu, "after_start", 0, 0, false, false);
              await new Promise(r => setTimeout(r, 250));
              const popupCS = getComputedStyle(filePopup);
              const firstItem = filePopup.querySelector("menuitem:not([hidden])");
              const itemCS = firstItem ? getComputedStyle(firstItem) : null;
              done({
                resolvedColors,
                toolboxBg: getComputedStyle(document.body).backgroundColor,
                navbarBg: getComputedStyle(document.getElementById("nav-bar")).backgroundColor,
                nonNativeThemeEnabled: Services.prefs.getBoolPref("widget.non-native-theme.enabled", true),
                gtkThemeContent: Services.prefs.getBoolPref("widget.content.allow-gtk-dark-theme", false),
                menuPopup: {
                  state: filePopup.state,
                  appearance: popupCS.appearance,
                  mozDefaultAppearance: popupCS.getPropertyValue("-moz-default-appearance"),
                  bg: popupCS.backgroundColor,
                  color: popupCS.color,
                  borderTop: popupCS.borderTopWidth + " " + popupCS.borderTopColor,
                  itemAppearance: itemCS ? itemCS.appearance : null,
                  itemColor: itemCS ? itemCS.color : null
                }
              });
            })();
            """,
            args=[gtk_html.as_uri()],
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-gtk-menu.png", settle=0.2)
        m.exec_chrome(
            """
            document.getElementById("menu_FilePopup").hidePopup();
            document.getElementById("toolbar-menubar").setAttribute("autohide", "true");
            """
        )

        # 3. Revamped sidebar + vertical tabs + legacy sidebar (sidebar.revamp=false) inspection.
        sidebar_revamp_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              await PanelUI.ensureReady();
              const appMenuAfterReady = !!document.getElementById("appMenu-popup");
              Services.prefs.setCharPref("sidebar.visibility", "always-show");
              await SidebarController.show("viewBookmarksSidebar");
              await new Promise(r => setTimeout(r, 400));
              const sm = document.querySelector("sidebar-main");
              const sb = document.getElementById("sidebar-box");
              const sp = document.getElementById("sidebar-panel-header");
              const smRect = sm ? sm.getBoundingClientRect() : null;
              const sbRect = sb ? sb.getBoundingClientRect() : null;
              const shadowParts = sm && sm.shadowRoot
                ? Array.from(sm.shadowRoot.querySelectorAll("[part]")).map(n => ({
                    tag: n.tagName.toLowerCase(),
                    part: n.getAttribute("part")
                  }))
                : [];
              const shadowButtons = sm && sm.shadowRoot
                ? Array.from(sm.shadowRoot.querySelectorAll("moz-button, button")).map(b => ({
                    tag: b.tagName.toLowerCase(),
                    part: b.getAttribute("part"),
                    view: b.getAttribute("view"),
                    hasShadow: !!b.shadowRoot
                  }))
                : [];
              const panelShadow = sp && sp.shadowRoot
                ? { childCount: sp.shadowRoot.children.length, parts: Array.from(sp.shadowRoot.querySelectorAll("[part]")).map(n => n.getAttribute("part")) }
                : null;
              done({
                appMenuAfterReady,
                sidebarMainVisible: sm ? !sm.closest("[hidden]") && smRect.width > 0 : false,
                sidebarMainRect: smRect ? { x: Math.round(smRect.x), y: Math.round(smRect.y), w: Math.round(smRect.width), h: Math.round(smRect.height) } : null,
                sidebarBoxRect: sbRect ? { x: Math.round(sbRect.x), y: Math.round(sbRect.y), w: Math.round(sbRect.width), h: Math.round(sbRect.height) } : null,
                shadowParts,
                shadowButtons,
                panelHeaderShadow: panelShadow
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-sidebar-revamp.png", settle=0.2)

        vertical_tabs_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              SidebarController.hide();
              Services.prefs.setBoolPref("sidebar.verticalTabs", true);
              await new Promise(r => setTimeout(r, 400));
              const tabs = document.getElementById("tabbrowser-tabs");
              const vtBox = document.getElementById("vertical-tabs");
              const r = tabs.getBoundingClientRect();
              done({
                tabsParentId: tabs.parentElement ? tabs.parentElement.id : null,
                tabsOrient: tabs.getAttribute("orient"),
                tabsLightDom: !tabs.getRootNode().host,
                verticalTabsSlottedInSidebarMain: vtBox && vtBox.parentElement ? vtBox.parentElement.tagName.toLowerCase() : null,
                toolboxTabsHiddenAttr: document.getElementById("navigator-toolbox").hasAttribute("tabs-hidden"),
                tabsRect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-vertical-tabs.png", settle=0.2)

        legacy_sidebar_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              Services.prefs.setBoolPref("sidebar.verticalTabs", false);
              SidebarController.hide();
              Services.prefs.setBoolPref("sidebar.revamp", false);
              await new Promise(r => setTimeout(r, 300));
              await SidebarController.show("viewBookmarksSidebar");
              await new Promise(r => setTimeout(r, 350));
              const sm = document.querySelector("sidebar-main");
              const sb = document.getElementById("sidebar-box");
              const sh = document.getElementById("sidebar-header");
              const st = document.getElementById("sidebar-switcher-target");
              const sc = document.getElementById("sidebar-close");
              const innerDoc = document.getElementById("sidebar").contentDocument;
              const sbRect = sb.getBoundingClientRect();
              const shRect = sh.getBoundingClientRect();
              done({
                sidebarMainHidden: !sm || !!sm.closest("[hidden]") || sm.getBoundingClientRect().width === 0,
                sidebarBoxVisible: !sb.hidden && sbRect.width > 0,
                sidebarBoxRect: { x: Math.round(sbRect.x), y: Math.round(sbRect.y), w: Math.round(sbRect.width), h: Math.round(sbRect.height) },
                sidebarHeaderVisible: getComputedStyle(sh).display !== "none" && shRect.height > 0,
                sidebarHeaderLightDom: !sh.shadowRoot && !!st && !!sc,
                innerDocURL: innerDoc ? innerDoc.documentURI : null,
                innerHasSearchAndTree: innerDoc ? (!!innerDoc.getElementById("search-box") && !!innerDoc.getElementById("bookmarks-view")) : false
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-sidebar-legacy-live.png", settle=0.2)
        m.exec_chrome(
            """
            SidebarController.hide();
            Services.prefs.clearUserPref("sidebar.visibility");
            Services.prefs.setBoolPref("sidebar.revamp", true);
            """
        )
        time.sleep(0.3)

        # 4A. Test the clean two-band architecture FIRST on a clean toolbar:
        # #nav-bar reserves padding-bottom: 26px outside Customize Mode and
        # #urlbar-container sits across the full 100% width of Row 2!
        wrap_css = """
        @media (-moz-native-theme) and (prefers-color-scheme: light) and (not (prefers-contrast)) and (not (forced-colors)) {
          :root:not([lwtheme]) {
            #nav-bar {
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
          }
        }
        """

        wrap_wide = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            const css = arguments[0];
            (async () => {
              CustomizableUI.addWidgetToArea("home-button", "nav-bar", 4);
              CustomizableUI.addWidgetToArea("print-button", "nav-bar", 5);
              CustomizableUI.addWidgetToArea("find-button", "nav-bar", 6);

              const sss = Cc["@mozilla.org/content/style-sheet-service;1"].getService(Ci.nsIStyleSheetService);
              const uri = Services.io.newURI("data:text/css;charset=utf-8," + encodeURIComponent(css));
              window._m1WrapURI = uri;
              sss.loadAndRegisterSheet(uri, sss.USER_SHEET);
              window.dispatchEvent(new Event("resize"));
              await new Promise(r => setTimeout(r, 400));

              const backR = document.getElementById("back-button").getBoundingClientRect();
              const homeR = document.getElementById("home-button").getBoundingClientRect();
              const panelR = document.getElementById("PanelUI-button").getBoundingClientRect();
              const urlR = document.getElementById("urlbar-container").getBoundingClientRect();
              const navEl = document.getElementById("nav-bar");
              const navR = navEl.getBoundingClientRect();

              const labels = Array.from(document.querySelectorAll("#nav-bar .toolbarbutton-1")).map(b => {
                const t = b.querySelector(".toolbarbutton-text");
                const tr = t ? t.getBoundingClientRect() : null;
                return {
                  id: b.id,
                  label: b.getAttribute("label"),
                  textRendered: t ? (t.value || t.textContent || "") : "",
                  textRect: tr ? { w: Math.round(tr.width), h: Math.round(tr.height) } : null
                };
              });

              gURLBar.focus();
              const urlFocused = document.activeElement === gURLBar.inputField;
              // Shift+Tab out of #urlbar-input moves focus via <toolbartabstop/> + ToolbarKeyboardNavigator onto a #nav-bar button!
              Services.focus.moveFocus(window, gURLBar.inputField, Services.focus.MOVEFOCUS_BACKWARD, Services.focus.FLAG_BYKEY);
              const activeAfterShiftTab = document.activeElement ? document.activeElement.id : null;
              const toolbarBtnFocused = !!document.activeElement && !!document.activeElement.closest("#nav-bar");

              done({
                navRect: { x: Math.round(navR.x), y: Math.round(navR.y), w: Math.round(navR.width), h: Math.round(navR.height) },
                backRect: { x: Math.round(backR.x), y: Math.round(backR.y), w: Math.round(backR.width), h: Math.round(backR.height) },
                homeRect: { x: Math.round(homeR.x), y: Math.round(homeR.y), w: Math.round(homeR.width), h: Math.round(homeR.height) },
                panelUIRect: { x: Math.round(panelR.x), y: Math.round(panelR.y), w: Math.round(panelR.width), h: Math.round(panelR.height) },
                urlbarContainerRect: { x: Math.round(urlR.x), y: Math.round(urlR.y), w: Math.round(urlR.width), h: Math.round(urlR.height) },
                urlbarFullWidth: Math.abs(Math.round(urlR.width) - Math.round(navR.width)) <= 2,
                urlbarBelowButtons: Math.round(urlR.y) >= Math.round(backR.y + backR.height - 1),
                overflowingWide: navEl.hasAttribute("overflowing"),
                urlFocused,
                toolbarBtnFocused,
                activeAfterShiftTab,
                labels
              });
            })();
            """,
            args=[wrap_css],
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-wrap-wide.png", settle=0.2)

        # Narrow resize test (520px, right at --window-min-width: 500px): verify real OverflowableToolbar overflow!
        wrap_narrow = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              // Add two more standard buttons so 8 buttons (> 450px) exceed a 520px toolbar and trigger real overflow!
              CustomizableUI.addWidgetToArea("save-page-button", "nav-bar", 7);
              CustomizableUI.addWidgetToArea("zoom-controls", "nav-bar", 8);
              window.resizeTo(520, 700);
              await new Promise(r => setTimeout(r, 500));
              const navEl = document.getElementById("nav-bar");
              const urlR = document.getElementById("urlbar-container").getBoundingClientRect();
              const navR = navEl.getBoundingClientRect();
              const defaultListCount = document.getElementById("widget-overflow-default-list")
                ? document.getElementById("widget-overflow-default-list").children.length
                : (document.getElementById("widget-overflow-list") ? document.getElementById("widget-overflow-list").children.length : -1);
              done({
                innerWidth: window.innerWidth,
                navOverflowingAttr: navEl.hasAttribute("overflowing"),
                urlbarFullWidth: Math.abs(Math.round(urlR.width) - Math.round(navR.width)) <= 2,
                urlbarRect: { x: Math.round(urlR.x), y: Math.round(urlR.y), w: Math.round(urlR.width), h: Math.round(urlR.height) },
                overflowCount: defaultListCount
              });
            })();
            """,
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-wrap-narrow.png", settle=0.2)

        # Restore 1120x740 and test Customize Mode enter + exit!
        customize_info = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              window.resizeTo(1120, 740);
              await new Promise(r => setTimeout(r, 350));
              const entered = new Promise(r => window.gNavToolbox.addEventListener("customizationready", r, { once: true }));
              gCustomizeMode.enter();
              await entered;
              await new Promise(r => setTimeout(r, 250));
              const customizingAttr = document.documentElement.hasAttribute("customizing");
              const paletteVisible = !!document.getElementById("customization-palette") &&
                getComputedStyle(document.getElementById("customization-container")).display !== "none";
              const urlPosInCustomize = getComputedStyle(document.getElementById("urlbar-container")).position;
              done({ customizingAttr, paletteVisible, urlPosInCustomize });
            })();
            """,
            async_mode=True,
        )
        shoot(shots_dir / "firefox-m1-customize.png", settle=0.2)

        customize_exit = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              // Remove the 2 extra narrow-only buttons before checking 1120px post-customize state.
              CustomizableUI.removeWidgetFromArea("save-page-button");
              CustomizableUI.removeWidgetFromArea("zoom-controls");
              const exited = new Promise(r => window.gNavToolbox.addEventListener("aftercustomization", r, { once: true }));
              gCustomizeMode.exit();
              await exited;
              await new Promise(r => setTimeout(r, 350));
              const navEl = document.getElementById("nav-bar");
              const urlR = document.getElementById("urlbar-container").getBoundingClientRect();
              const backR = document.getElementById("back-button").getBoundingClientRect();
              done({
                customizingCleared: !document.documentElement.hasAttribute("customizing"),
                stillWrappedAfterExit: Math.round(urlR.y) >= Math.round(backR.y + backR.height - 1),
                overflowingAfterExit: navEl.hasAttribute("overflowing")
              });
            })();
            """,
            async_mode=True,
        )

        # 4B. Also record the naive flex-wrap control (temporarily swapping out _m1WrapURI)
        # to prove why wrapping #urlbar-container inside #nav-bar-customization-target
        # causes false overflow at 1120px and leaves a right-side gap under #PanelUI-button:
        naive_flex_wrap = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const sss = Cc["@mozilla.org/content/style-sheet-service;1"].getService(Ci.nsIStyleSheetService);
              if (window._m1WrapURI && sss.sheetRegistered(window._m1WrapURI, sss.USER_SHEET)) {
                sss.unregisterSheet(window._m1WrapURI, sss.USER_SHEET);
              }
              const css = `
                #nav-bar-customization-target { display: flex !important; flex-wrap: wrap !important; }
                #urlbar-container { flex: 1 0 100% !important; order: 99 !important; }
                #nav-bar .toolbarbutton-1 { flex-direction: column !important; min-width: 52px !important; }
              `;
              const uri = Services.io.newURI("data:text/css;charset=utf-8," + encodeURIComponent(css));
              sss.loadAndRegisterSheet(uri, sss.USER_SHEET);
              window.dispatchEvent(new Event("resize"));
              await new Promise(r => setTimeout(r, 350));
              const navEl = document.getElementById("nav-bar");
              const navR = navEl.getBoundingClientRect();
              const urlR = document.getElementById("urlbar-container").getBoundingClientRect();
              const res = {
                falseOverflowAtWide: navEl.hasAttribute("overflowing"),
                urlbarWidthGapPx: Math.round(navR.width - urlR.width)
              };
              sss.unregisterSheet(uri, sss.USER_SHEET);
              if (window._m1WrapURI) {
                sss.loadAndRegisterSheet(window._m1WrapURI, sss.USER_SHEET);
              }
              await new Promise(r => setTimeout(r, 250));
              done(res);
            })();
            """,
            async_mode=True,
        )

        # 5. Built-in themes + dark mode + high contrast gating matrix.
        theme_matrix = m.exec_chrome(
            """
            const done = arguments[arguments.length - 1];
            (async () => {
              const { AddonManager } = ChromeUtils.importESModule("resource://gre/modules/AddonManager.sys.mjs");
              const themes = [
                "default-theme@mozilla.org",
                "firefox-compact-light@mozilla.org",
                "firefox-compact-dark@mozilla.org",
                "firefox-alpenglow@mozilla.org"
              ];
              const results = [];
              async function snapState(label) {
                await new Promise(r => setTimeout(r, 300));
                const root = document.documentElement;
                const urlC = document.getElementById("urlbar-container");
                const bgImg = getComputedStyle(urlC).backgroundImage;
                results.push({
                  label,
                  lwtheme: root.hasAttribute("lwtheme"),
                  lwthemeImage: root.hasAttribute("lwtheme-image"),
                  mozNativeTheme: window.matchMedia("(-moz-native-theme)").matches,
                  prefersDark: window.matchMedia("(prefers-color-scheme: dark)").matches,
                  prefersContrast: window.matchMedia("(prefers-contrast)").matches,
                  forcedColors: window.matchMedia("(forced-colors)").matches,
                  platinumGateActive: bgImg.includes("rgb(51, 51, 153)")
                });
              }

              for (const id of themes) {
                const addon = await AddonManager.getAddonByID(id);
                if (addon) {
                  await addon.enable();
                  await snapState(id);
                } else {
                  results.push({ label: id, missing: true });
                }
              }

              const defAddon = await AddonManager.getAddonByID("default-theme@mozilla.org");
              await defAddon.enable();
              Services.prefs.setIntPref("ui.systemUsesDarkTheme", 1);
              await snapState("default-theme+systemUsesDarkTheme=1");
              Services.prefs.clearUserPref("ui.systemUsesDarkTheme");
              done(results);
            })();
            """,
            async_mode=True,
        )

        # Toggle GTK HighContrast in the disposable dconf session to verify @media (prefers-contrast) gating!
        subprocess.run(["gsettings", "set", "org.gnome.desktop.a11y.interface", "high-contrast", "true"], check=True)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "HighContrast"], check=True)
        time.sleep(0.5)
        hc_row = m.exec_chrome(
            """
            const root = document.documentElement;
            const urlC = document.getElementById("urlbar-container");
            const bgImg = getComputedStyle(urlC).backgroundImage;
            return {
              label: "default-theme+gtk-high-contrast",
              lwtheme: root.hasAttribute("lwtheme"),
              lwthemeImage: root.hasAttribute("lwtheme-image"),
              mozNativeTheme: window.matchMedia("(-moz-native-theme)").matches,
              prefersDark: window.matchMedia("(prefers-color-scheme: dark)").matches,
              prefersContrast: window.matchMedia("(prefers-contrast)").matches,
              forcedColors: window.matchMedia("(forced-colors)").matches,
              platinumGateActive: bgImg.includes("rgb(51, 51, 153)")
            };
            """
        )
        theme_matrix.append(hc_row)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.a11y.interface", "high-contrast", "false"], check=True)
        subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", "Platinum"], check=True)
        time.sleep(0.5)

        restored_row = m.exec_chrome(
            """
            const root = document.documentElement;
            const urlC = document.getElementById("urlbar-container");
            const bgImg = getComputedStyle(urlC).backgroundImage;
            const res = {
              label: "default-theme-restored",
              lwtheme: root.hasAttribute("lwtheme"),
              lwthemeImage: root.hasAttribute("lwtheme-image"),
              mozNativeTheme: window.matchMedia("(-moz-native-theme)").matches,
              prefersDark: window.matchMedia("(prefers-color-scheme: dark)").matches,
              prefersContrast: window.matchMedia("(prefers-contrast)").matches,
              forcedColors: window.matchMedia("(forced-colors)").matches,
              platinumGateActive: bgImg.includes("rgb(51, 51, 153)")
            };
            const sss = Cc["@mozilla.org/content/style-sheet-service;1"].getService(Ci.nsIStyleSheetService);
            if (window._m1WrapURI && sss.sheetRegistered(window._m1WrapURI, sss.USER_SHEET)) {
              sss.unregisterSheet(window._m1WrapURI, sss.USER_SHEET);
            }
            return res;
            """
        )
        theme_matrix.append(restored_row)

        shoot(main_out, settle=0.2)

        report = {
            "startup": startup,
            "dom_inventory": dom_inventory,
            "gtk_inheritance": gtk_inheritance,
            "sidebar_revamp": sidebar_revamp_info,
            "vertical_tabs": vertical_tabs_info,
            "legacy_sidebar": legacy_sidebar_info,
            "naive_flex_wrap": naive_flex_wrap,
            "wrap_wide": wrap_wide,
            "wrap_narrow": wrap_narrow,
            "customize_enter": customize_info,
            "customize_exit": customize_exit,
            "theme_matrix": theme_matrix,
        }
        (report_dir / "probe-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0
    finally:
        m.close()


if __name__ == "__main__":
    sys.exit(main())
