# macos9-theme: plan

## Status

**Bundled global menu plan, 2026-11-26 (Codex GPT-6).** Decision 6 records KDE Global Menu 1.1.3 as the base and File + Go as the fallback. The 20 px nested Wayland panel trial comes first. Source workflow decided by the user the same day: git subtree in `plasma/globalmenu/` (#316). [Bundled global menu plan](#plan-bundled-global-menu)

**Global menu fallback research, 2026-11-26 (Codex GPT-6).** Plasma 6.8.3 has no fallback setting. A replacement applet can show File and Go on the desktop and for apps without menus, then switch to the focused app’s exported menu. The closest existing applet built and passed three focused suites and an offscreen load. The next check is the applet in Platinum’s top panel under nested Wayland. [Research and prototype plan](docs/GLOBAL-MENU-FALLBACK.md)

**#313 fixed and verified, 2026-11-26 (Codex GPT-6, working tree).** The libadwaita verifier samples through the opaque fixture's 8 px gap. The original doubled-line evidence now fails and fresh runs pass 183/183 Broadway and 259/259 nested Plasma. The GTK handoff is desktop review.

**Independent review of #312, 2026-11-26 (Codex GPT-6, working tree).** The zero-margin mutation fails all four new assertions. #313 covers the opaque separator pixel sample ending before the far side of the measured 8 px gap. Libadwaita passed 183/183 Broadway and 259/259 nested Plasma. GTK 4 passed 178/178 Broadway. Live desktop review is pending.

**Control Strip design, 2026-11-26 (Codex GPT-6, working tree).** First test moving the existing Plasma tray from the top bar to a short bottom-left panel beside the dock. A custom tray view would collapse to a grip. A custom Wayland surface is the candidate for dragging the horizontal strip up and down along the left edge. Tray controls and pop-ups on that surface still need a prototype. All five standard theme suites passed. [Design and prototype checks](macos9-applet-bar/CONTROL-STRIP-DESIGN.md)

**Independent review of #311, 2026-11-26 (Codex GPT-6, working tree).** Opaque and transparent toolbars with 4 px and 12 px widget margins draw one separator. The previous 4 px captures fail both margin assertions. #312 tracks the verifier accepting zero-margin evidence from the previous CSS. All five standard suite runs passed. Live desktop review is pending.

**Independent review of #309–310, 2026-11-26 (Antigravity, Gemini 4 Neon, working tree).** Verified #309 for CSS `margin-bottom` and #310 for `#EEEEEE` opacity verification. Recorded #311 (P3): `GtkWidget:margin-bottom` (unaffected by CSS `margin-bottom: 0`) still draws two black separators 4 px apart on opaque and transparent last-child top bars. Broadway suites passed: GTK 4 178/178 (plain and with layer), `check-adw` 168/168, CSS parse 9/9 (0 errors). Wayland/Plasma modes and live desktop review pending.

**Independent review of #307–308, 2026-11-26 (Codex GPT-6, working tree).** The direct opaque toolbar and fixture layout guards pass. Two open findings cover the doubled separator with a bottom margin (#309) and missing opacity verification in the new fixture (#310). All five standard suite runs passed. Desktop visual review is pending.

**Independent review of #305–306, 2026-11-26 (Codex GPT-6, working tree).** Verified the original toolbar cases and the open-search verifier fix. Two follow-ups cover opaque toolbar separators (#307) and the new fixture layout checks (#308). All five standard suite runs passed. Live desktop review is pending.

**Independent review of #302–304, 2026-11-26 (Codex GPT-6, working tree).** #302 and #304 verified. The wrapped-header case in #303 passes. Two open findings cover lost separators on other raised-border top bars (#305) and the search fixture verifier accepting a closed bar as open (#306). All five standard suite runs passed. Desktop visual review is pending.

**Independent review of #300–301, 2026-11-26 (Codex GPT-6, working tree).** Selected-row idle colors and the direct raised-border header pass. Two open findings in AUDIT.md cover named-theme selected links on hover and press (#302) and the doubled edge under wrapped headers (#303). All five standard suite runs passed. Desktop visual review is pending.

**#296–299 fixed and verified, 2026-11-26 (Codex GPT-6, working tree).** Closed the GTK 4 switch sizing and link backdrop gaps, restored libadwaita's solid raised-border separators, and made the verifier require all expected stock and layered fixture logs and PNGs. GTK 4 passed 169/169 Broadway with and without the layer and 244/244 in nested Plasma. Libadwaita passed 101/101 Broadway and 149/149 in nested Plasma. Prior CSS failed the new visual checks, and nine evidence mutations failed verification. Desktop reinstall and visual review are pending.

**#292–295 verified and fixed 2026-11-26 (Antigravity, Gemini 4 Neon, uncommitted).** Fixed all four findings from Claude's GTK 4 / libadwaita audit: Platinum `#CCCCFF`/`#DCDCEF` selections for list/sidebar/grid/flow/textview, `#0000FF` links, and plain-GTK-4 Platinum switches (#292); cleared libadwaita shade variables and raised toolbar drop shadows (#293); removed inherited `--platinum-push-*` custom properties from `button`, cutting 2,700-control `:backdrop` restyle overhead by 62% (`93.29 ms` → `56.30 ms` vs `33.48 ms` stock) (#294); dropped dead `switch:active` rules and documented the `GtkSwitch` gap (#295). Suites pass: CSS parse 9/9 (0 errors), `check-gtk4` Broadway 160/160 (plain and with layer), `check-adw` Broadway 92/92 (new `selections` mode). **Waits on the user:** `./install.sh`, Wayland/plasma rerun if desired, and desktop visual review.

**GTK 4 / libadwaita fixes #292–313 done 2026-11-26 (uncommitted).** Gemini fixed #292–295, Codex #296–299, Claude #300–312; #300–308 and #311 reviewed by Codex, #309–310 by Gemini, #312 verified by Codex and #313 fixed and verified by Codex. GTK 4 178/178 Broadway and 253/253 nested Plasma, libadwaita 183/183 and 259/259. **Waits on the user:** commit, `./install.sh` and a desktop look at plain GTK 4 and libadwaita apps.

**GTK 4 / libadwaita audit 2026-11-26 (Claude Code, `7eb391f`).** The independent review above tracks the remaining GTK findings. Suites passed (GTK 4 Broadway 160/160, `check-adw` Broadway 78/78).

**Platinum classified as a light global theme 2026-11-26.** Plasma reads
the bundled palette and lists Platinum in the light picker. It reports light
to the portal and GTK, and Firefox System follows live palette changes.
The icon default is WhiteSur Lavender Light. The builder produces base and
light, and upgrades retire unselected, unchanged managed dark trees.
The nested appearance test passed 59/59 and icons passed 81/81. All 853
installer checks passed across the full run and corrected fixture replays.
See AUDIT.md #288–290. Desktop reinstall and visual review are pending.

**Small WhiteSur Trash icons restored 2026-11-26.** All three Lavender variants use WhiteSur's empty and full icons at 16, 22 and 24 px. The custom scalable pair supplies the default Platinum dock size. KDE and GTK 3 verified both states in a disposable build, and the icon suite passed 80/80. A desktop reinstall and visual review are pending.

**#284–286 fixed and verified 2026-11-26 (Codex GPT-6, `d37f152`).** Centered captions clear asymmetric boxes, and the decoration suite starts on a clean checkout and observes both capability transitions. Decoration passed 10/10, including both reference crops, and Plasma passed 19/19. In private nested KWin zoom hid and returned with the 5 px gap intact. The plugin and capture tool ran under ASan/UBSan. Live desktop visual review is pending.

**Gemini re-audit, 2026-11-26 (Codex GPT-6, `33e4516`).** #282 verified against two reference crops and through a disable/restore cycle in nested KWin. #283 verified with both default font paths. Findings in `AUDIT.md`: #284 (P2) a compacted asymmetric button layout clips a centered caption, #285 (P3) `check-deco` fails before building on a clean checkout, and #286 (P3) its dynamic restoration assertion passes with the toggle removed. Prepared sandbox suites passed decoration 7/7, Widgets 135/135 plus 12/12, Qt Quick 32/32, tabs 51/51, Trash 11/11, and Plasma 19/19. Desktop visual review is pending.

**#282–283 fixed 2026-11-26 (Antigravity, Gemini 4 Carbon).** Disabled KWin title-bar buttons now collapse their layout slot so pinstripes extend to 5 px before the remaining boxes (`decoration/platinum.cpp`, matching `reference/dialog-get-info.png`; new `dev/check-deco.sh` 7/7, ASan/UBSan clean), and `dev/check-style.sh` pins a ≤ 16 px default font when `FONT` is unset (`check-style` 135/135 + 12/12, `check-quick` 32/32, `check-tabs` 51/51, `check-trash` 11/11). **Waits on the user:** `./install.sh` and desktop visual review.

**Audit of #272–281 fixes, 2026-11-26 (Antigravity, Gemini 4 Neon).** #272–280 verified clean (`FONT="SF Pro Text,10" dev/check-style.sh` 135/135 + 12/12, `check-quick` 32/32, `check-tabs` 51/51, `check-trash` 11/11 + 10 extra URL paths, paint latency 10.0–12.5 µs/call). **2 new open findings (#282 P2, #283 P3):** disabled KWin title-bar buttons leave a 21 px blank gap instead of extending pinstripes to 5 px before the remaining box (`decoration/platinum.cpp` vs `reference/dialog-get-info.png`), and `dev/check-style.sh` fails 129/135 without a ≤ 16 px font pinned. See `AUDIT.md`.

**Qt, KWin and Plasma fixes, 2026-11-26.** Findings #272–281 are fixed and verified in the working tree. Qt Widgets passed 135/135 reference crops and 12/12 state checks. Qt Quick passed 32/32, tabs 51/51, Plasma 19/19 and Trash 11/11. Nested KWin verified that the zoom box disappears and returns with changes to resize capability. All three C++ plugins ran under ASan/UBSan. Evidence is in the newest AUDIT.md entry. **Waits on the user:** desktop visual review.

**Git synchronization, 2026-11-26.** At the user's request, commit `b5facd5` included the GTK fixes #269–271, their regression probes and the audit that reported #272–281.

**#269–271 fixed 2026-11-25 (Antigravity Gemini 4 Neon; committed in the 2026-11-26 synchronization):** GTK 4/libadwaita spinbutton text selection now uses Platinum Lavender `#CCCCFF` (#269), GTK 3 pressed tab close buttons keep flat icon sizing (#270), and GTK 3 header-bar spinbuttons keep both arrow boxes intact (#271). `check-gtk3-headerbar` 19/19, GTK 3 Broadway 47/47, 38/38, 63/63, GTK 4 Broadway 160/160, `check-adw` Broadway 78/78. **Waits on the user:** `./install.sh` and desktop review.

**#268 done 2026-11-25 (uncommitted):** libadwaita window boxes equally inset on both sides (user decision). **Waits on the user:** `./install.sh`.

**#267 done 2026-11-25 (uncommitted):** Platinum spin buttons for GTK 3, GTK 4 and libadwaita (entry field + arrow boxes). All GTK suites and test-install 833/833 pass. **Waits on the user:** `./install.sh` and a look.

**#266 fixed 2026-11-25 (uncommitted):** Kwi's taller tabs now reach the terminal (style `drawTab`). check-tabs 51/51, style 135/135, quick 29/29, plasma 19/19. **Waits on the user:** `./install.sh`, restart Kwi, and a look.

**#265 fixed 2026-11-25 (uncommitted):** GTK 3 tab close buttons no longer make tabs taller (Audacious). GTK 3 suites pass. **Waits on the user:** `./install.sh` and a look.

**#264 fixed and #263 follow-up 2026-11-25 (uncommitted):** GTK 3 tab-row action buttons (Audacious "+") stay above the pane as small bevel buttons; left tab arrow closed. GTK 3 suites pass. **Waits on the user:** `./install.sh` and a look.

**#263 fixed 2026-11-25 (uncommitted):** GTK 3 tab scroll arrows (Audacious) drawn as Platinum scroll arrows. GTK 3 suites pass. **Waits on the user:** `./install.sh` and a look.

**#262 fixed 2026-11-25 (uncommitted):** GTK 3 popover menus (Lutris) drawn as Platinum menus. GTK 3 suites pass. **Waits on the user:** `./install.sh` and a look.

**#261 fixed 2026-11-25 (uncommitted):** GTK 3 header bar stripes only in the gaps between app widgets (Lutris). GTK 3 suites pass (m3b2 64/64 / 63/63). **Waits on the user:** `./install.sh` and a look.

**#260 fixed 2026-11-25 (uncommitted):** libadwaita close boxes now 4 px in (main windows and framed floating dialogs). check-adw 113/113 / 73/73. **Waits on the user:** `./install.sh` and a look.

**#254–259 fixed 2026-11-25 (uncommitted).** Gemini's libadwaita findings (confirmed parts) and the GTK 4 combo box (#259). test-install 833/833, check-gtk4 234/234 / 160/160, check-adw 100/100 / 64/64. **Waits on the user:** `./install.sh` and a look at pavucontrol, zenity and libadwaita header bars; decision on #254's linked-folder half.

**libadwaita Platinum layer ready for live testing, 2026-11-25 (uncommitted).** Colors + shapes for unmodified libadwaita apps (decision 15): `gtk-4.0/libadwaita.css`, imported by one marked line at the top of `~/.config/gtk-4.0/gtk.css` that `install.sh` adds on `--apply` or on a reinstall while Platinum is the global theme, and `uninstall.sh` removes (unless the GTK 4 theme stays installed). Real kded keeps the line first and appends its own import. `test-install` 830/830, `test-install-live` 49/49, `check-adw` plasma 86/86 / broadway 54/54, plain GTK 4 222/222 / 149/149, style 135/135, plasma 19/19, quick 29/29. **Waits on the user:** live testing (plain `./install.sh` reinstall adds the line on the current desktop) and findings. Next: fixes from that, remaining Adw widgets, 150/200 %.

**Firefox 161.0 verified, 2026-11-25 (uncommitted).** No theme changes needed; tested range raised to 160..161 (#253). Selector check 37/37 + 2/2, M1 46/46, M3 36/36, M4 43/43, M5 32/32, M6 85/85. Waits on the user: a quick look in their real Firefox.

GTK uninstall fixes #249–250 passed independent re-audit. Preserving an unset GTK style key and resuming an interrupted config restore remain open (#251–252).

The GTK 3-to-4 installer upgrade and undo passed the handoff audit. Codex's #249–252 fixed 2026-11-25 (uncommitted): undo keeps GTK theme choices made (or keys removed) after `--apply`, also across an interrupted undo, and an exported `GTK_THEME=Platinum` keeps the theme. `test-install` 810/811 + fixed scenario 9/9, `test-install-live` 47/47.

**GTK 4 packaged in main installer (Milestone 6) & #245–248 verified, 2026-11-25 (uncommitted).** `install.sh` packages self-contained `gtk-4.0` alongside `gtk-3.0` (25 targets); `uninstall.sh` restores displaced `gtk-4.0` and keeps both toolkits if `Platinum` is selected in any GTK store. Verified `dev/test-install.sh` **771/771**, `dev/test-install-live.sh` **47/47**, `dev/check-gtk4.sh` **222/222** Wayland / **149/149** Broadway. Ready for commit/push (when requested) and user desktop review.

**Gemini's findings #245–248 fixed 2026-11-25 (uncommitted).** #248 by the user's choice: level fills stop 3 px short. GTK 4 222/222 Wayland, 149/149 Broadway. Re-audit and user review pending.

**Gemini's GTK 4 audit fixed 2026-11-25 (uncommitted):** #240–243 plus #244 (full progress shadow, GTK 3 and 4) verified and fixed; GTK 4 216/216 Wayland, 144/144 Broadway; GTK 3 suites pass. Re-audit and user review pending.

**GTK 4 movable alert, menu buttons and level bars added 2026-11-25 (uncommitted).** Alerts are the Mac OS 9 movable alert with a white body; menu buttons and level bars are Platinum. `dev/check-gtk4.sh` 205/205 Wayland, 133/133 Broadway. The plain GTK 4 port now covers every planned control; user visual review pending, then installer packaging (Milestone 6).

**GTK 3 header bars match GTK 4 and KWin (2026-11-25, uncommitted):** no boxes on inactive bars, and the boxes are no longer blurred. GTK 3 suites pass.

**GTK 4 header bars, tooltips and alerts added 2026-11-25 (uncommitted).** Header-bar apps now get the KWin Platinum frame and title bar drawn client-side, exact against `window-document-active/inactive.png`; Help Balloon tooltips and the plain modal frame on alerts. `dev/check-gtk4.sh`: 201/201 Wayland, 127/127 Broadway. User visual review pending. Next: GtkLevelBar and header-bar menu buttons.

**GTK 4 tabs, scales, progress bars and scrollbars added 2026-11-25 (uncommitted).** `gtk/Platinum/gtk-4.0/tabs-ranges.css` plus guarded GTK 4 slice assets. All GTK 3 Batch 2 reference crops match pixel for pixel on Broadway (Cairo) and nested Wayland (Vulkan); 200% equals the doubled references and 150% has no slice seams. `dev/check-gtk4.sh`: 124/124 Broadway (also under ASan/UBSan), 162/162 Wayland; five injected faults rejected. GTK 4 scrollbars have no arrows (no stepper nodes). User visual review pending. Next: GTK 4 header bars, tooltips and dialogs, then GtkLevelBar.

Kwi bottom tabs rendered at 100%, 150%, and 200%. Qt Widgets label overlap and tab test coverage remain open (#236–237).

**KDE portal file picker fixed 2026-11-24 (#224).** The path, Name and File type fields now use the Platinum Qt Widgets editable combo style. KDE's file widget and the native portal rendered in the sandbox. Qt Widgets 135/135, Qt Quick 29/29, Plasma 19/19, installer/undo 745/745 and nested install 40/40 passed. User visual review is pending.

The Firefox menu now doubles as the selected-tab loading indicator (#223).

Firefox sidebar hover and selection highlights verified in lavender (#222).

Firefox Bookmarks, History, synced tabs, and Passwords sidebar contrast verified on Firefox 160.0.1 (M4 43/43, #221).

Firefox Settings and open address suggestions now use Platinum colors, verified alongside Vapor on Firefox 160.0.1 (#220).

Firefox Customize Sidebar contrast verified with Vapor Firefox and Platinum loaded together (#219).

Firefox Customize Sidebar contrast verified with collapsed vertical tabs and dark sidebar colors on Firefox 160.0.1 (M4 38/38, #218).

Firefox Customize Sidebar contrast and lavender web text selection verified on Firefox 160.0.1 (M4 38/38, #216–217).

GTK 3 packaging audit #213–215 verified coexistence with GTK 4 resources, selected-theme removal and artwork preflight.

The main installer now packages the named GTK 3 theme for per-app or manual selection. Its manifest handles upgrade, removal and restoration. GTK 4 packaging and automatic GTK preference adoption remain planned.

**Firefox is production-ready.** The maintainer approved the Linux Firefox theme on 2026-11-24. Tested on Firefox 160.0.1.

Collapsed vertical tab icons verified in both normal and Private Browsing windows on Firefox 160.0.1 (M4 36/36, #212).

Collapsed Firefox vertical tab alignment verified on Firefox 160.0.1 (M4 35/35, #211). User profile reinstall and visual review are pending.

Firefox content stylesheet and Private Browsing audit #209–210 passed 46/46 discovery, 34/34 chrome and 85/85 install/undo. The current polish awaits live visual review.

**Firefox Private Browsing Platinum support completed 2026-11-24** by Antigravity (Gemini 4 Neon): added `browser.theme.dark-private-windows = false` to `DEFAULT_MANAGED_PREFS` in `firefox/profile_ops.py` (restored on undo) and `dev/firefox-test.sh` so Private Browsing windows follow the active System light/dark scheme and render the full Platinum theme in light mode (keeping Firefox's Private mask icon on the tab strip) while still gating cleanly off in System Dark mode, High Contrast, and explicit themes. Verified `tools/check-firefox-selectors.py` (`35/35` `#id`, `1/1` `::part()`), `dev/check-firefox-m4.sh` (**34/34**, `dev/build/firefox-m4.IBytHU`, visually inspected `dev/shots/firefox-m4-private.png`), and `dev/check-firefox-m6.sh` (**81/81**, `dev/build/firefox-m6.2NybWX`). Waiting on user reinstall (`./install.sh --firefox` with Firefox closed) and live visual check.

**Firefox Lavender scrollbars via `userContent.css` completed 2026-11-24** by Antigravity (Gemini 4 Neon): added `firefox/chrome/platinum/content.css` (`scrollbar-color: #9999FF #CCCCCC;` gated on light normal-contrast mode without `!important`) and `firefox/chrome/userContent.css`, matched browser-chrome scrollbars in `palette.css` / `tabs-sidebar.css`, and wired marker-delimited `chrome/userContent.css` backup/install/upgrade/conflict/crash-safe undo into `firefox/profile_ops.py` (fully backward-compatible with pre-`userContent.css` installs). Verified `tools/check-firefox-selectors.py` (`35/35` `#id`, `1/1` `::part()`), `dev/check-firefox-m3.sh` (**36/36**, `dev/build/firefox-m3.PJK7Dk`), `dev/check-firefox-m4.sh` (**34/34**, `dev/build/firefox-m4.4TwSLt`), `dev/check-firefox-m5.sh` (**32/32**, `dev/build/firefox-m5.WQPaxX`), and `dev/check-firefox-m6.sh` (**81/81**, `dev/build/firefox-m6.vB3b1T`, `1,952` `#9999FF` live scrollbar pixels in `dev/shots/firefox-m6-installed-live.png`). Waiting on user reinstall (`./install.sh --firefox` with Firefox closed) and live visual check.

Firefox polish audit #207–208 verified the Go command, RTL hit target, logo decoding and scrollbar preference restoration. M3/M4/M5/M6 passed 36/34/32/73 checks. The user confirmed live install and undo before these polish changes.

**Firefox live-review polish completed 2026-11-24** by Antigravity (Gemini 4 Neon): per user desktop review of their real Firefox install, added a clickable IE5-style `▸ go` button at the end of the Deep Lavender address band (`firefox/chrome/platinum/top-bands.css`, styling Firefox's real `.urlbar-go-button`), switched the idle activity well in `status-activity.css` to Firefox's own built-in `chrome://branding/content/about-logo.svg` (keeping the animated Platinum Lavender bar while loading), and added classic 16 px full-width square non-overlay scrollbar prefs (`widget.gtk.overlay-scrollbars.enabled=false`, `widget.non-native-theme.scrollbar.style=4`, `scrollbar.size.override=16`, `theme-scrollbar-colors.enabled=true`) to `firefox/profile_ops.py` (restored on undo); kept toolbar left-aligned per IE5; fixed `$rt/doc` FUSE unmount in `dev/firefox-m6/test_suite.py` live teardown trap. Verified `tools/check-firefox-selectors.py` (`35/35` `#id`, `1/1` `::part()`), `dev/check-firefox-m3.sh` (**35/35**, `dev/build/firefox-m3.FtZmBb`), `dev/check-firefox-m4.sh` (**34/34**, `dev/build/firefox-m4.wNy6RK`), `dev/check-firefox-m5.sh` (**32/32**), and `dev/check-firefox-m6.sh` (**72/72**, `dev/build/firefox-m6.mNECuc`).

Firefox lock re-audit #206 passed 72/72 installer checks. A stale loopback link now requires both advisory locks for the duration of the command.

**Firefox installer #205 fixed.** Stale loopback locks with an exited PID allow install and undo after the advisory lock checks. Milestone 6 passed 68/68. A dry run also reached the proposed install steps for the user’s default profile.

The root install and uninstall commands now support Firefox-only mode with `--firefox`. The profile installer suite passed 64/64 in the working tree.

**Second Firefox audit, 2026-11-24.** #198–204 fixed. M1/M3/M4/M5/M6 passed 46/34/34/32/61 checks, respectively. M2 rendered eight mockups and four comparison sheets. User desktop visual review is pending.

**Firefox independent audit, 2026-11-24.** Findings #192–197 fixed in the working tree. All five Firefox suites passed on 160.0.1 (46/46, 34/34, 34/34, 31/31, 54/54). User visual review is pending.

**GTK Milestone 4 menus, dropdowns and lists implemented 2026-11-24.** The named GTK 4 theme and sandbox suite now cover this batch. Wayland passed 109/109 including 53 exact reference crops. Broadway passed 74/74 including 50 exact crops. The Settings demo, active/backdrop row selection, native actions, search, sorting, and 150%/200% outputs passed. The GTK 4 changes are uncommitted. User visual review is pending. Next are notebook tabs, scales, progress bars and scrollbars.

**Firefox Milestone 7 (release check & pre-release audit) completed 2026-11-24** by Antigravity (Gemini 4 Carbon): audited `firefox/` and fixed **#189–191** in the working tree (`bars-states.css` inactive-window focus outline suppression across all controls, `tabs-sidebar.css` / `bars-states.css` explicit `2 px` `#6666CC` `:focus-visible` rings on secondary tab/sidebar/findbar buttons, `profile_ops.py` post-crash `user.js` inner-marker conflict check + empty new `prefs.js` unlinking, and `README.md` / `firefox/README.md` known limitations). Re-ran and passed every Firefox suite end to end (`tools/check-firefox-selectors.py` **35/35 `#id`, 1/1 `::part()`**; `dev/check-firefox-m1.sh` **46/46** `firefox-m1.iJ3Ool`; `dev/check-firefox-m3.sh` **34/34** `firefox-m3.FopVHl`; `dev/check-firefox-m4.sh` **34/34** `firefox-m4.2VHMe7`; `dev/check-firefox-m5.sh` **31/31** `firefox-m5.6HXhws`; `dev/check-firefox-m6.sh` **41/41** `firefox-m6.235YJD`) plus shared project regression suites (`dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**, `dev/test_icons_phase1.py` **80/80**, `dev/test-install.sh` **727/727**), recorded in `AUDIT.md`. Ready for the user's approved live Firefox install (`./firefox/install.sh`) and on-screen review.

**Firefox Milestone 6 (install & byte-for-byte undo) completed 2026-11-24** by Antigravity (Gemini 4 Carbon): added `firefox/install.sh`, `firefox/uninstall.sh`, `firefox/profile_ops.py`, and the throwaway-`HOME` + live nested-Wayland test suite `dev/check-firefox-m6.sh` (`dev/firefox-m6/test_suite.py`), passing **40/40** (`dev/build/firefox-m6.jtZ6no`). Verified XDG (`~/.config/mozilla/firefox/profiles.ini`) and `~/.mozilla/firefox/profiles.ini` discovery with `[Install*]` `Default=` precedence over legacy `[Profile*]` `Default=1`, interactive PTY selection + `--profile`/`--list`/`--dry-run` + non-interactive refusal, untested Firefox major-version warning gate, `lock` dangling-symlink and live `.parentlock` `fcntl` lock refusal + state `flock`, journaled checksummed backup of `chrome/`, `user.js`, and `prefs.js` before any profile change, `@charset`-first / `@import`-before-`@namespace` marker insertion, byte-for-byte + mode restoration of untouched profiles (including displaced pre-existing `chrome/platinum`), preservation of post-install user edits outside markers and new session prefs in `prefs.js`, conflict and symlink refusal without overwriting, reinstall & pref-retiring upgrade, fault-injected mid-install and mid-uninstall crash recovery at all 7 boundaries, two-profile isolation, and live cold launch of Firefox 160.0.1 (`dev/shots/firefox-m6-installed-live.png`) followed by full `prefs.js`/profile undo. Ready for Milestone 7 (release check in `AUDIT.md`, then user's approved install & on-screen review).

**Firefox Milestone 5 (robustness: `omni.ja` selector checker, version gate, 150%/200% scaling & keyboard focus) completed 2026-11-24** by Antigravity (Gemini 4 Neon): added `firefox/version.json`, `tools/check-firefox-selectors.py`, and `dev/check-firefox-m5.sh` + `dev/firefox-m5/{probe.py,verify.py}`, passing **29/29** (`dev/build/firefox-m5.G42eT0`) with full Milestone 3 (**34/34**, `dev/build/firefox-m3.xMDvbW`) and Milestone 4 (**34/34**, `dev/build/firefox-m4.TxG0IM`) regressions passing. The `omni.ja` checker scanned all 1,904 files across both Firefox 160.0.1 `omni.ja` archives, immediately caught and led to fixing a stale `#urlbar-searchmode-switcher` selector (renamed to `.searchmode-switcher` in Firefox 160), verified `35/35` `#id` and `1/1` `::part()` selectors present, and passed all four negative controls (missing `#id`, missing `::part()`, untested major `999.0.1` returning `3`, and `--allow-untested-version` returning `0`). Live nested `2400×1600` virtual KWin tests verified 2 px `#6666CC` keyboard focus rings across `#urlbar`, toolbar buttons (plus Shift+Tab navigation), bookmarks, horizontal `1A` tabs, vertical `1C` tabs, and the Find bar, plus crisp 150% (`dpr=1.5`) and 200% (`dpr=2.0`) rendering with zero clipping, zero overlap, zero false overflow, and intact 16 px permanent status band (`dev/shots/firefox-m5-{keyboard-focus,scale-150,scale-200}.png`). Ready for Milestone 6 (`firefox/install.sh` + `firefox/uninstall.sh`, separate from root `install.sh`, with throwaway-HOME test suite).

**Firefox Milestone 4 (full browser chrome coverage) completed 2026-11-24** by Antigravity (Gemini 4 Neon): added `firefox/chrome/platinum/{tabs-sidebar,status-activity,menus-panels,bars-states}.css` and `dev/check-firefox-m4.sh` + `dev/firefox-m4/{probe.py,verify.py}`, passing **34/34** (`dev/build/firefox-m4.SElfWo`) with Milestone 3 regression **34/34** (`dev/build/firefox-m3.CUcL8R`). Verified live-switchable `1A` horizontal tabs below Favorites (`#CCCCCC`/`#EEEEEE`/`#666666`+white) + `1C` pinstriped vertical sidebar tabs (`sidebar.verticalTabs`), neutral Platinum Lavender orb/barber-pole activity indicator (`:has(.tabbrowser-tab[selected][busy])`, zero Microsoft/Apple logos), permanent 16 px IE5 pinstriped status band (`5A`) with diagonal `#777777`/`#FFFFFF` corner size grip + fullscreen/popup suppression, measured Platinum menubar / `menupopup` / `#appMenu-popup` / `#downloadsPanel` / square `.urlbarView` (`#DDDDDD`, `0 px` radius, `#000000` border, `#333399` Lavender highlight), Platinum Find bar + Notification bar + legacy/revamped sidebar framing, real `:-moz-window-inactive` flattening (clearing focus rings and muting labels to `#777777`), clean delegation of Firefox 160 dark Private windows, compact single-row popup windows, Customize Mode, and System-light-only gating. Ready for Milestone 5 (robustness: `omni.ja` selector checker, version gate, 150%/200% scaling & keyboard focus checks).

**Firefox Milestone 3 (vertical slice: the three top bands) completed 2026-11-24** by Antigravity (Gemini 4 Neon): implemented `firefox/chrome/{userChrome.css,platinum/{platinum.css,palette.css,top-bands.css}}` and `dev/check-firefox-m3.sh` + `dev/firefox-m3/{probe.py,verify.py}`, passing **34/34** (`dev/build/firefox-m3.CUcL8R`). Whole-pixel sampling verified on cold normal-launch `dev/shots/firefox-m3-cold.png`: KWin `#000000` → `#FFFFFF` top highlight → 42 px pinstriped toolbar (`#DEDEDE`/`#CCCCCC`/`#E8E6E8`, 56 px button pitch, `#333399`/`#9999CC` Lavender icons, `#111111`/`#777777` labels, dotted Lavender separator, right-aligned right-side buttons) → 26 px Deep Lavender Tube (`2A`, 26/26 exact discrete rows, crisp white `Address:`, 1 px `#000000` white address field) → 24 px pinstriped Favorites bar. Interactive probe verified Platinum `ToolNormal` hover bevel, `#666666`/white pressed buttons, 2 px `#6666CC` address focus ring (`4,226` px) + `#CCCCFF` selection (`5,563` px), opaque Platinum `#urlbar[open]` autocomplete dropdown with `#333399` highlight, narrow `520 px` real overflow, Customize Mode round-trip, and System-light-only gating across Compact Light, Compact Dark, Alpenglow, System Dark, and GTK HighContrast.

**Firefox Milestone 2 (sandbox visual mockups) completed 2026-11-24** by Antigravity (Gemini 4 Neon): rendered 8 live cold-launch Firefox 160.0.1 mockups + 4 comparison sheets (`dev/render-firefox-m2.sh`, `dev/shots/firefox-m2-*.png`). User reviewed the mockups and locked all four design choices in `docs/FIREFOX-PLAN.md`: **Tabs `1A` + `1C`** (slim Platinum tabs below Favorites bar in horizontal mode, live-switching to vertical Platinum sidebar tabs via Firefox's built-in `sidebar.verticalTabs` toggle), **Address band `2A`** (Deep Lavender Tube with white `Address:` label), **Toolbar `4A`** (42 px icons + text labels), and **Status bar `5A`** (permanent 16 px IE5 pinstriped status band with diagonal size grip).

**Firefox Milestone 1 (sandboxed harness & 160.0.1 chrome discovery) completed 2026-11-24** by Antigravity (Gemini 4 Carbon): added `firefox/README.md`, `dev/firefox-test.sh` (nested `kwin_wayland --virtual` with isolated `HOME`/`XDG_*`/`XDG_RUNTIME_DIR`, Platinum KDecoration, Platinum GTK 3 theme, and throwaway profile), and `dev/check-firefox-m1.sh` + `dev/firefox-m1/{probe.py,verify.py}`, passing **46/46** (`dev/build/firefox-m1.zVJtP1`). Verified cold normal-path `chrome/userChrome.css` loading (`29,506` `#CCCCFF` marker px vs `0` when `stylesheets=false`), exact KWin SSD-to-toolbox join (`#999999` → `#000000` → `#DDDDDD`/`#FFFFFF`), full-width two-row IE5 toolbar + 26 px Lavender address band (`padding-bottom: 26px` + `position: absolute` `#urlbar-container`, avoiding the `104 px` right-side gap and false `OverflowableToolbar` overflow caused by naive `flex-wrap: wrap`), unclipped `.toolbarbutton-text` labels under icons, real narrow-window overflow (`520 px` → `5` items), Customize Mode round-trip, keyboard focus, light-DOM vertical tabs (`#vertical-tabs`) + functional legacy sidebar (`sidebar.revamp=false`), GTK 3 color inheritance vs `non-native-theme` menus/scrollbars, XDG `~/.config/mozilla/firefox/profiles.ini` `[Install*]` precedence, and `@media (-moz-native-theme)` gating (required because Nova Compact Light/Dark omit `[lwtheme]`). Recorded in `docs/FINDINGS.md` and `docs/DEVELOPMENT.md`.

**GTK Milestone 4 initial slice re-audited on 2026-11-24.** The uncommitted working tree fixes #181–188. GTK 4 passed 78/78 Wayland with the default Vulkan renderer and 56/56 Broadway. All 36 reference crops matched on both. Stack switchers and toolbars retain their stock dimensions, disabled labels use Platinum gray, and a mapped window tracks high contrast and restoration. Project regressions passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 80/80 icons, 727/727 install and undo, and 40/40 nested live install. User visual review is pending. The menus and lists follow-up is recorded above. The terminal palette and GTK 3 checkpoint are on `origin/main` in `b34dcb0` and `733afcb`.

Updated 2026-11-23 by Antigravity (Gemini 4 Carbon). **GTK Milestone 3 Batch 2 (#177–180) passed independent cross-verification.** Virtual Wayland (`dev/build/gtk3-m3b2-plasma.EJiAYi`) passed **62/62**, fresh Broadway (`dev/build/gtk3-m3b2-broadway.kDQb5m`) passed **61/61**, ASan/UBSan (`dev/build/m3b2-sanitizers.uwTiMK` + an 80-case progressbar matrix) passed with zero diagnostics, all 6 negative controls rejected injected faults, and all 45 1× reference crops matched pixel for pixel on both backends. GTK Milestone 3 is complete and on `origin/main` in `733afcb`. User visual review and Batch 2 fractional-scale inspection remain pending. `#95` remains open.

Independent review on 2026-11-23 cleared the #142/#143 fixes for commit and plain reinstall on the user's existing Platinum setup (see AUDIT.md). Both nested Plasma suites passed in the user's terminal. The user completed the plain live reinstall without an inline cache override, live `kreadconfig6` returned `WhiteSur-lavender`, and the user visually approved the desktop appearance. The #142/#143 fixes are committed on `main` and the Lavender reinstall checkpoint is complete; #95 remains open.

**WhiteSur Lavender (`#101–143`) complete, live-reinstalled with visual approval, and committed on `main`.**
- Phase 1 (`#101–109`, `#111`), externalized pin (`icons/whitesur-pin.json`),
  read-only update review (`icons/review-whitesur-update.sh`), tracked
  `icons/custom/{all,light}/` override layer (`#119` cross-dir variant
  aliases + GTK3 byte checks), automatic pinned-commit WhiteSur bare cache
  (`icons/fetch-whitesur.sh`, `#116`/`#135` mandatory `flock`, `#121` full
  `git fsck --full`, `#137` early `TMPDIR` validation/trap, `#143` safe
  user-owned symlinked `~/.cache` canonicalization with unsafe/foreign-path
  refusal), `#118` shared Arch-package preflight, `#120`/`#132` recovery-safe
  journaled publish, and `#123`/`#134` archive + linked-worktree protection
  passed **80/80** in `dev/test_icons_phase1.py`.
- Small-overlay architecture remains rejected; full-copy + `icons/custom/`
  retained.
- Phase 2 (`#110`, `#112–115`, `#117–118`, `#122`, `#124–131`, `#133`, `#135`,
  `#136`, `#138`, `#139–142`) uses one durable v3 icon-selection transaction
  (`scripts/icon_prefs.py`) captured under lock before first target/manifest
  mutation (`#139`), refuses install during any unfinished undo via
  `$state/uninstall-in-progress` and transaction phase (`#140`), re-checks the
  active global theme before resuming pending selection (`#141`), deletes KDE
  icon overrides directly without `kwriteconfig6 --delete` / `Theme[$d]` and
  repairs existing installs carrying stale `Theme[$d]` (`#142`), enforces
  `rmdir`-only `manifest_ops.py` removal (`#125`), requires complete outside
  advertised artwork + independent dependencies (`#126`/`#127`), captures and
  restores pre-adoption modes and POSIX ACLs across differing legacy backups
  (`#131`), and preflights plugin build prerequisites (`#136`). Passed
  **702/702** in `dev/test-install.sh` under real `XDG_CONFIG_DIRS` cascade.
- Sandbox suites passed: **135/135** widget (`dev/check-style.sh`), **29/29**
  Qt Quick (`dev/check-quick.sh`), **702/702** install/undo (`dev/test-install.sh`),
  **80/80** icons (`dev/test_icons_phase1.py`).
- User terminal suites passed **19/19** Plasma pixel comparisons with zero differences and **40/40** nested live-install checks.

**Checkpoint 4 passed.** Against `dc8b76f`, 12 C++ findings are fixed in
the working tree (#85–94, #96–97). #95 stays open because the compact slider
thumbs changed pixels at all five fractional scales. #98 is fixed and verified.
The final 200 offscreen images matched across eight scales. All five suites
passed (135/135 widget, 29/29 Quick, 19/19 Plasma, 367/367 install and 37/37
live install). The user ran the three private-D-Bus suites and verified #85
in threaded virtual KWin. See AUDIT.md for costs, coverage and limitations.
Checkpoint patches, images and logs are in `dev/build/audit-baseline/`.

**Checkpoint 5 passed.** #99 and #100 are fixed and verified in the working
tree. The deferred-apply and unchanged-border layout probes passed, as did
QGuiApplication-only PlatinumItem construction under UBSan. All five suites
passed (135/135 widget, 29/29 Quick, 19/19 Plasma, 367/367 install, 37/37
live install), and all 200 images matched across eight scales. Claude's
corrected nested-KWin probe verified title width and right button position
through resize and all maximize/restore transitions (23 paints). The saved
probe now uses the same resize action. #95 remains open.

**Where things stand.** Built and checked headless (sandbox, nested KWin,
throwaway homes). The user has now installed Platinum on their desktop:
- colors, window decoration, application style (C++ QStyle, `style/platinum`),
  Qt Quick Controls style (`style/quick`: menus, menu bar, combo lists,
  tooltips, switches, dialogs, drawers, range sliders), Plasma style, menu
  bar, dock, global theme;
- `install.sh` / `uninstall.sh` (user scope, full undo), including retryable
  Qt Quick cleanup. See AUDIT.md for findings #59–68.

The user reviewed the resized top panel at 32 px and liked the result. Both P3 follow-ups (#69–70) are fixed in the working tree. The Plasma artwork suite passed 19/19 at 100% display scale, including complete comparisons at 32, 34, 38, and 40 px.

The user tested the updated Kwi tab close fix and reported that it worked
well on their desktop (#71–74). The Qt Quick suite passed 29/29.

Lavender Desktop Pattern is the default when applying the Platinum global (user, 2026-11-24; was Pastel Ribbon Landscape)
theme. Installing also adds Pastel Ribbon Landscape, Platinum Waves, Platinum Glass, Platinum Nebula, Finder Waves and Retro Lavender Ripples to Plasma’s picker.
Verified both renders and the upgrade from a single wallpaper.
Findings #75–77 are fixed. Uninstall keeps selected packages, apply
warns if Qt can't open the JPEG XL images, and the live test checks
the rendered default on both screens.

The cursors are part of the theme: Apple Cursor v2.0.1's black set
(GPL-3.0, `cursors/README.md`), shipped as `cursors/macOS-cursors.tar.xz`,
installed as the theme `macOS-cursors` and selected by the global theme
(cursor findings #78–#84 fixed). The login script makes the installed pack
available in Plasma's Cursors picker. Uninstall keeps the pack while it is
selected or restores the previous pack with the same ID.

**Sandbox handoff.** Open Codex on the project folder. Opening on the home
folder previously failed on the `~/.codex` symlink. Keep sandbox network
access off and use the isolated runtime directory with display and session-bus
variables unset. For this audit the user ran the private-D-Bus suites outside
the sandbox. Decoration pixel comparisons used the offscreen software preview.

**Waiting on the user (don't do these without them):**
1. Completed by the user, first real desktop install: `./install.sh`, log out and
   in, `./install.sh --apply`, then a fresh login for Qt Quick controls, with
   the user watching their screens, as required by AGENTS.md.
2. Their on-screen review of everything (#3, the Qt Quick style, waits for
   it).
3. Decisions already made stay: decisions 10-13 below (main screen only, no
   right-to-left, #25 deferred to publication, own Qt Quick
   drawing item).
4. Try the wallpapers on the desktop after updating the install and
   selecting them in the wallpaper settings.
5. Run the updated installer, log out and back in, then check macOS in
   Plasma's Cursors settings.

**Next work after that** (order of work below): #95 remains a visual-fidelity
follow-up. **Remaining theming scope (user, 2026-11-22):** WhiteSur Lavender
icons, GTK 3, GTK 4/libadwaita, an optional IE5-style Firefox theme (decision
14), Plasma Login Manager, Konsole and Kwi colors, splash screen, lock screen,
and the Qt size grip.
Fonts are settled (SF). Publication questions include #25 and the theme name.

**Before finishing any change, run the suites** (expected results are kept
in `docs/AUDIT-REQUEST.md`; today 135/135, 19/19, 833/833, 49/49, 29/29):
`dev/check-style.sh`, `dev/check-plasma.sh`, `dev/test-install.sh`,
`dev/test-install-live.sh`, `dev/check-quick.sh` (DEVELOPMENT.md says what
each covers). Audit rounds: Codex appends to AUDIT.md; verify each finding,
fix it with a test, record it there and in CHANGELOG.md; commit and push
only when the user says so.

### Claims

One row per component. `nobody` = free. See AGENTS.md "Working together".

| Component  | Folder(s)                 | Claimed by | Status      |
|------------|---------------------------|------------|-------------|
| shared     | docs, tools, dev, scripts | nobody | dev/ sandbox + tools/compare.py done (`dev/run.sh` isolates `XDG_CONFIG_DIRS=/etc/xdg`); test-install-live.sh uses real `XDG_CONFIG_DIRS` cascade (#142); docs fixed (AUDIT 24); Finder folder palette recorded in docs/REFERENCE.md (#107); `dev/test_icons_phase1.py` (81/81), `scripts/manifest_ops.py` (#125 `rmdir`-only), `scripts/icon_prefs.py` (v3 durable transaction, #124/#126–131/#133/#139–142), hardened `dev/test-install.sh` (771/771), Milestone 1 GTK discovery harness verified through #162 (32/32 controls), Milestone 2 GTK 3 verification suite (`dev/check-gtk3.sh`, `dev/gtk3-check/`) verified (51/51 Wayland, 47/47 Broadway), Milestone 3 Batch 1 harness (`dev/check-gtk3-m3b1.sh`, `dev/gtk3-m3b1/`) verified (39/39 Wayland, 38/38 Broadway), Milestone 3 Batch 2 harness (`dev/check-gtk3-m3b2.sh`, `dev/gtk3-m3b2/`) verified (62/62 Wayland, 61/61 Broadway), GTK 4 harness (`dev/check-gtk4.sh`, `dev/gtk4-check/`) 222/222 Wayland, 149/149 Broadway (#181–188, #240–248 fixed and verified), and Firefox Milestones 1–7 suites (`dev/firefox-test.sh`, `tools/check-firefox-selectors.py`, `dev/check-firefox-m{1,3,4,5,6}.sh`: 46/46, 36/36, 34/34, 32/32, 81/81; #189–208 fixed and verified); `dev/check-deco.sh` (10/10, #285–286 fixed) and `dev/check-style.sh` default font pin (#283) verified; `dev/check-adw.sh` `selections` mode passed 101/101 Broadway and 149/149 nested Plasma. Mandatory evidence verified (#299) |
| reference  | reference/, docs/REFERENCE.md | nobody | 82 VM captures (incl. `ie5-window-blank.png` backed up in `macos9-theme-reference` `05292a6`); first real Platinum desktop archived at 100%, 150% and 200% in reference/testing/; measurements partial |
| colors     | colors/                   | nobody     | Platinum.colors done and bundled in Global Theme. Palette check guards the two light backgrounds |
| decoration | decoration/               | nobody | plugin works in nested KWin; frame pixel exact; only the three Mac OS 9 boxes are created (AUDIT 20); audit #86, #90, #96 and #99 verified. Disabled title-bar boxes hidden and pinstripes extended to remaining boxes (#281, #282). Centered captions clear asymmetric boxes (#284; `dev/check-deco.sh` 10/10) |
| style      | style/                    | nobody | batches 1-7 + tooltips done (pixel exact); audit fixes #15-#19, #32 (keyboard focus ring, mixed check box, polish symmetry, RTL fallback, 64-bit scroll math, reversed scroll bars); Qt Quick style in style/quick: menus, menu bar, combo list, tooltips, switches (AUDIT 3, check-quick 29/29; installed by install.sh); also dialogs (measured modal frame), drawers, range sliders; combo lists track live model edits (#63); compact tab close indicator and selected state verified in Kwi (#71–74); editable combo styled and verified in KDE file picker (#224); open: size grip; audit #85, #87–89, #91–94, #97 and #100 verified; #95 open; bottom tabs (Konsole, Kwi) drawn as the top tabs upside down, `dev/check-tabs.sh` 51/51 (2026-11-25, Codex #236–237 and Gemini #238–239 fixed; taller Kwi tabs #266). Widget and Quick fixes #272–277 and #279–280 verified |
| plasma     | plasma/, macos9-applet-bar/ | nobody | menu bar, global theme, dock done (headless); selection text contrast fixed (AUDIT 22); main screen only (decision 10); resizable menu bar ends and divider (AUDIT 23), with complete divider dots and pixel comparisons across four panel heights (AUDIT 69–70); #98 table reader verified; Platinum is classified Light and defaults to `WhiteSur-lavender-light` (#288–290); default dock ends with the own `platinum.trash` widget (color empty/full icons sized like the dock apps; 2026-11-24). Reserved-character Trash paths verified (#278). [Control Strip proposal](macos9-applet-bar/CONTROL-STRIP-DESIGN.md) is ready for a tray-move prototype. |
| icons      | icons/                    | nobody | #101–109, #111, #116, #118–121, #123, #132, #134, #135, #137, #143 committed on `main` against pinned `2026-09-10` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`); external pin (`icons/whitesur-pin.json`), tracked custom layer (`icons/custom/{all,light}/` + cross-dir variant aliases), read-only update review (`icons/review-whitesur-update.sh`), mandatory-`flock` full-`fsck` bare-git cache (`icons/fetch-whitesur.sh` with safe user-owned symlinked `~/.cache`), recovery-safe journaled publish, archive + linked-worktree safeguards, and disposable suite (`dev/test_icons_phase1.py`, 80/80); full-copy + custom layer retained; base and light built. Retired dark is supported on upgrade and undo. Custom scalable Trash and upstream small sizes verified |
| cursors    | cursors/                  | nobody | bundled black cursors (`macOS-cursors`) installed and selected by the global theme, verified in nested Plasma; discovery, selection and undo verified (#78–#84). No cursors of our own (decision 8, user). |
| gtk        | gtk/                      | nobody | GTK 3 and GTK 4 install and removal verified (`dev/test-install.sh` 833/833, `dev/test-install-live.sh` 49/49). GTK 4 passes 178/178 Broadway (plain and with layer) and 253/253 nested Plasma. `check-adw` passes 183/183 Broadway and 259/259 nested Plasma. GTK 3 app checks 19/19. #292–299 verified. #300–301 cover the standard cases. Next in GTK is desktop review and automatic GTK selection. libadwaita colors + shapes layer (`gtk-4.0/libadwaita.css`, decision 15) installed with the theme (import line in `~/.config/gtk-4.0/gtk.css`, install/undo tested); user live testing pending. |
| firefox    | firefox/                  | nobody | Production-ready on Linux. Verified on Firefox 161.0 (all suites, #253) and 160.0.1. |
| extras     | extras/, wallpapers/      | nobody | Pastel Ribbon Landscape, Lavender Desktop Pattern (default), Platinum Waves, Platinum Glass, Platinum Nebula, Finder Waves and Retro Lavender Ripples packaged with the global theme (the last five added 2026-11-25, user-supplied). Platinum Lavender terminal palette verified in disposable Kwi and Konsole and included in install and undo (#173–176 fixed). Plasma Login Manager, splash and lock screen remain. |
| packaging  | install.sh, uninstall.sh, packaging/ | nobody | install.sh / uninstall.sh rebuilt after Codex's four audits (#4-#14, #27-#31, #34-#42 fixed); Qt Quick style & pass-through (#59–65); wallpapers (#75–77); bundled cursors (#78–84); WhiteSur Lavender #110, #112–115, #117–118, #122, #124–131, #133, #135–136, #138–143 committed on `main` (`dev/test-install.sh` 702/702 with real `XDG_CONFIG_DIRS` cascade; `dev/test-install-live.sh` 40/40 in user's terminal); live plain reinstall completed and visually approved by user; desktop uninstall untested; terminal palette audit #173–176 fixed, install/undo verified at 727/727; libadwaita import line add/remove (decision 15, `gtk_theme.py adw-import`, 2026-11-25) |

## Goal

Make Plasma 6.8 look as close as possible to Mac OS 9.2.2 with the default
Platinum appearance, measured against the real system. See AGENTS.md
"Fidelity rules" and "Legal rules".

## Decisions

Open decisions need the user. Record the answer here with the date.

1. **Scale.** Both 4K screens run at scale 1, where 1x Mac OS 9 metrics are
   tiny. **Decided 2026-11-20 (user): true 1x at Plasma 100%**: draw every
   metric at its real Mac OS 9 pixel size, pixel exact; "from my testing,
   we can tweak it from there." Facts behind it: a 20 px menu bar is 3.1 mm
   on the 27" (163 ppi) and 3.7 mm on the 32" (138 ppi), against ~6.4 mm on
   a 2001 Mac at ~80 ppi; Plasma 200% would double that and give a
   1920×1080 workspace. So keep metrics in one place (no hard-coded sizes
   scattered around) so a later 2x variant or tweak stays cheap. Other
   options considered: Plasma 200%, a fixed 2x theme at 100%, a build-time
   multiplier.
2. **Application style engine.** Union can't draw scroll bar arrows or two
   bevel layers in Qt Widgets. **Step 3 spike (2026-11-20, see
   docs/FINDINGS.md):** Union gives scroll bar arrows zero size on 6.8.3;
   a C++ QStyle drew the Platinum scroll bar pixel exact in two captured
   cases. **Recommended: a C++ QStyle** (Qt Widgets; Qt Quick / Kirigami
   apps would get it through KDE's qqc2-desktop-style, to verify). Kvantum
   not evaluated (not installed). **Decided 2026-11-20 (user): C++ QStyle.**
3. **Decoration engine.** **Step 3 spike:** Aurorae draws the title as
   elided text over a fixed SVG, so it can't stop pinstripes around the
   title, condense it, or drop it; a C++ QPainter title bar matched the
   captures pixel exact in two window widths (title text excluded).
   **Recommended: C++ KDecoration3**, like windows2000-union. **Decided
   2026-11-20 (user): C++ KDecoration3.**
4. **Name and IDs.** Neutral installable IDs without "Apple"/"Mac OS".
   *Open.*
5. **Fonts.** Charcoal (system) and Geneva (small) can't ship. Find the
   closest freely licensed substitutes, or let the user point at their own
   copies at install time. **Decided 2026-11-22 (user):** keep Apple's San
   Francisco fonts (the user's installed SF Pro Text and SF Mono). They are
   an external dependency and must not be bundled in this repo.
6. **Menu bar.** How close to get: global menu + Apple-menu stand-in
   (launcher) + clock + application switcher on the right. *Details open.*
   Started 2026-11-21 (Claude Code): top panel 20 px, Kicker (cascading
   menu) as the Apple menu stand-in with a neutral icon (no Apple logo),
   the global menu (`appmenu`), a spacer, the system tray (kept: network,
   volume), the clock, and the Window List applet as the Application menu.
   **Global menu, decided 2026-11-26 (user).** Bundle KDE Global Menu 1.1.3
   at `4a24e4dfed7eac640023e1b28d06321f65385e2b` in the theme's default menu
   slot. Show **File** and **Go** on the desktop and when the focused app
   has no usable export. Preserve the focused app's native menu when one
   is available. The user accepted File + Go as close enough to the Mac OS 9
   Finder bar (#314) and wants Platinum's patches kept small enough to pull
   in upstream fixes. Source kept as a git subtree in `plasma/globalmenu/`
   (decided the same day). Name, decided the same day (user): **Platinum
   Global Menu**, plugin ID `platinum.globalmenu` (matching the theme's
   `platinum.*` widget IDs). [Chosen upstream](https://github.com/ChathurangaBW/global-menu-KDE/tree/4a24e4dfed7eac640023e1b28d06321f65385e2b) · [Bundled global menu plan](#plan-bundled-global-menu)
7. **Icons.** **Decided 2026-11-21 (user):** use an existing icon set
   ("what's out there at the moment"); pick after checking licenses
   (NineIcons Redux, Platinum9, Chi-Nata and others). **Updated 2026-11-22
   (user):** use WhiteSur (`vinceliuice/WhiteSur-icon-theme`, GPL-3.0) for
   longevity, coverage and SVG, tracked from upstream with our own patch set
   adding a Lavender variant. Upstream variants are 25 folder SVGs in
   `colors/color-*` plus installer entries. Keep the upstream tree out of
   this repo; store only the patch or generator and its license notes.
8. **Cursors.** **Decided 2026-11-21 (user):** our own, or one of the many
   Mac OS X cursor packs as a temporary stand-in ("not ideal but a temp
   thing ... while focusing more on the meat"). The black variant of
   ful1e5/apple_cursor is the optional external stand-in. **Updated
   2026-11-21 (user):** no cursors of our own; the Apple Cursor pack is the
   cursor set to use ("those mac os icons are the perfect ones"), kept
   bundled in `cursors/` (user, 2026-11-21: "option 1"), installed as
   `macOS-cursors` and selected by the global theme. The ID breaks the
   "no Mac OS in IDs" rule by the user's explicit choice.
9. **Dock.** **Decided 2026-11-21 (user):** window management may stray
   from Mac OS 9: "even though the dock came in OS X, I would like to use
   it in 'os 9.' Bring the dock over, but make it designed around os 9
   look." Design (Claude Code, same day): a bottom panel styled like Mac OS
   9's pop-up window tab (`finder-popup-tab.png`, the OS 9 element that
   already sits on the bottom screen edge), apps as bevel buttons like the
   Launcher control panel (running = raised bevel, active = selected
   bevel, pinned but not running = bare icon).
10. **Screens.** **Decided 2026-11-21 (user):** "Menu bar and dock on
    master monitor": the menu bar and the dock go on the main screen only,
    as on Mac OS 9, and other screens get no panel (AUDIT.md finding 21).
    In Plasma 6 the primary screen is always screen 0, where the layout
    script's new panels go.
11. **Right-to-left layouts.** **Decided 2026-11-21 (user):** not
    supported ("I don't plan on supporting that"). AUDIT.md finding 26 is
    closed. The fallbacks already in the style stay (they keep clicks and
    drawing consistent), but nothing more is done for right-to-left.
12. **Deferred by the user, 2026-11-21:** AUDIT.md finding 25 (measured
    pixel tables and git history) waits until the user is ready to go
    public. On 2026-11-21 the user asked to resume #23 after trying a 38 px top panel.
    **2026-11-26:** the user says `orlfman/macos9-theme` has been public for a
    while (gh confirms PUBLIC); #25 is still open, so its trigger has passed.
13. **Qt Quick drawing.** **Decided 2026-11-21 (user):** our own small C++
    Qt Quick item, public Qt API only, not KDE's private `StyleItem`
    bridge (see "Plan: Qt Quick menus, tooltips and switches").

14. **Firefox.** **Decided 2026-11-22 (user):** add an optional Firefox theme
    styled after Internet Explorer 5 for Mac, with IE's aqua/teal replaced by
    the measured Platinum Lavender colors. The user explicitly approved
    `userChrome.css` as an exception to the officially-supported-hooks rule,
    because an official Firefox theme can't match the layout. Keep it separate
    from the main install path, easy to undo, and free of Microsoft logos or
    artwork. Use a neutral activity icon instead of IE's logo. Tabs need a slim
    Platinum design because IE5 had none. Native reference:
    `reference/ie5-window-blank.png`. The user's screenshot
    `/home/pieman/Pictures/Screenshots/Screenshot_20261122_225730.png` is
    slightly scaled, so use it for layout only. **Clarified 2026-11-23
    (user):** not a 1:1 IE5 clone. IE5 is the layout inspiration for giving
    Firefox a Mac OS 9 look and feel; go as far as `userChrome.css` allows.
    Platinum colors and bevels still come from docs/REFERENCE.md; IE5 pixels
    are not a comparison target, and further IE5 captures are optional.
    Plan: docs/FIREFOX-PLAN.md.
15. **libadwaita.** **Decided 2026-11-25 (user):** Platinum colors and
    shapes for unmodified libadwaita apps, through the one desktop-wide hook
    libadwaita loads: the user stylesheet `~/.config/gtk-4.0/gtk.css`
    imports `gtk-4.0/libadwaita.css` (the plain GTK 4 rules plus
    `adw-colors.css` and `adw-widgets.css`). Light, normal-contrast only.
    Consequence: while the import is there, plain GTK 4 apps also look
    Platinum whatever GTK theme is selected (docs/FINDINGS.md).

## Components

Short list of what each one must match. `docs/REFERENCE.md` holds the
measurements.

- **colors**: Platinum grays, default highlight color, text colors, disabled
  text, window and view backgrounds; scheme groups for Window, View, Button,
  Selection, Tooltip, Header/WM (note: KWin uses `[Colors:Header]` for title
  bars if present).
- **decoration**: active title bar with horizontal pinstripes and centered
  title, inactive title bar flat; close box left; zoom and collapse boxes
  right; window frame and bevels; collapse = shade.
- **style**: push buttons (default button with thick ring), bevel buttons,
  check boxes and radio buttons, pop-up menus, scroll bars (arrows, grip lines
  on the thumb, track), sliders, progress bars (barber pole when
  indeterminate), tabs, list views with header, text fields with inset frame,
  group boxes, menus (incl. highlight), tool tips (help balloons?).
- **plasma**: menu bar panel on top, Apple-menu stand-in, global menu, clock,
  application menu; panel popups; optional Control Strip; desktop with
  volume icons? (scope TBD); task switching.
- **icons**: WhiteSur from upstream plus our Lavender variant patch set
  (decision 7).
- **cursors**: arrow, I-beam, watch (busy), crosshair, hand; redrawn.
- **gtk**: GTK 3 and GTK 4/libadwaita colors and shapes as far as supported.
- **firefox**: optional IE5 Mac-style `userChrome.css` theme in Platinum
  Lavender (decision 14), with its own install and undo.
- **extras**: Konsole and Kwi colors only (user, 2026-11-22), Pastel Ribbon
  Landscape, Lavender Desktop Pattern, Platinum Waves, Platinum Glass,
  Platinum Nebula, Finder Waves and Retro Lavender Ripples wallpapers (user-supplied images),
  Plasma Login Manager (replaces SDDM, user 2026-11-22), splash, lock screen.

## Order of work

0. **Setup** (done 2026-11-19): AGENTS.md, PLAN.md, CHANGELOG.md, AUDIT.md,
   README.md, .gitignore, git repo + private GitHub repo orlfman/macos9-theme.
1. **Reference.** Mac OS 9.2.2 runs in QEMU (user set it up 2026-11-19, see
   AGENTS.md "The reference VM"); `tools/capture.py` takes lossless 1x
   captures (tested 2026-11-20 against a throwaway QEMU). Next: relaunch the
   VM with a QMP socket (done), confirm the Appearance control panel is at
   defaults (done 2026-11-20, see REFERENCE.md), then work through
   `docs/CAPTURES.md` (priority A first) and measure into
   `docs/REFERENCE.md`. A part of the theme starts once its A captures are
   measured. **Capture pass done 2026-11-20** (81 captures, all A and B
   items). REFERENCE.md has first measurements for most widgets; a full
   measuring pass per component (exact sizes, corners, fonts) is still to
   do, ideally right before that component is built.
2. **Sandbox.** Port windows2000-union's `dev/` tooling (sandbox, offscreen
   gallery, nested KWin, screenshot scripts) and add a screenshot comparison
   tool. Settle decision 1 (scale). **Tooling done 2026-11-20** (see
   `docs/DEVELOPMENT.md`); decoration test tools come with the decoration.
3. **Spikes.** Decide the style engine (decision 2) and decoration engine
   (decision 3) by drawing one scroll bar and one title bar each way.
   **Done 2026-11-20** (`spikes/`, docs/FINDINGS.md); both point to C++.
4. **colors** → **decoration** → **style** (the bulk of the look).
5. **plasma**: menu bar layout, Plasma style, look-and-feel package, and the
   [bundled global menu](#plan-bundled-global-menu).
6. **icons**, **cursors**, fonts.
7. **gtk**, **firefox**, **extras**.
8. **packaging**: install/uninstall to user scope with backups; full audit;
   user's on-screen review.

## Plan: Bundled global menu

KDE Global Menu keeps the stock-style `KSvg.FrameSvgItem` delegate, so
Platinum's `widgets/menubaritem` draws the title states. The pinned applet
built against Plasma 6.8.3 and passed three focused test suites and an
offscreen load. The panel trial is the next milestone. Decision 6 makes
the applet part of the default layout and supersedes the initial proposal
to offer it as an optional widget. [Upstream menu delegate](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/qml/MenuDelegate.qml#L45-L68) · [Research and test results](docs/GLOBAL-MENU-FALLBACK.md)

### Source management (#316)

**Decided 2026-11-26 (user): git subtree in `plasma/globalmenu/`.** The
applet's source lives in this public repo. Platinum's patches are ordinary
commits on top of it, `git subtree pull` brings in upstream updates, the
install needs nothing extra downloaded for it, and agents edit it like any
other part of the theme. No private working repo and no patch files.

- Import: `git subtree add --prefix=plasma/globalmenu
  https://github.com/ChathurangaBW/global-menu-KDE
  4a24e4dfed7eac640023e1b28d06321f65385e2b --squash`. The pin is upstream
  `main`, which is the `v1.1.3` tag (`e52d16e`) plus one release-workflow
  commit (`.github/workflows/release.yml` only). `--squash` keeps upstream's
  commits out of this repo's history; the squash commit records the
  upstream commit, which `git subtree pull` uses as the merge base.
- Updates: `git subtree pull --prefix=plasma/globalmenu
  https://github.com/ChathurangaBW/global-menu-KDE <commit> --squash` after
  reviewing upstream's changes, then rerun the applet tests and the theme
  checks. Record the new pin here and in decision 6.
- Our patches: separate commits with a `globalmenu:` subject prefix, never
  mixed into the import or pull commits, so they stay attributable. Each
  file we modify also gets a one-line notice next to its copyright header
  saying the Platinum theme changed it and when (GPL-2.0 section 2a).
  Upstream's
  CI, release and packaging files (`.github/`, `packaging/`, `install.sh`,
  `scripts/`) stay as imported and unused; the theme's `install.sh` builds
  `plasma/globalmenu/` itself.
- `plasma/globalmenu/` belongs to the `plasma` claim.

Record the upstream URL and full commit. Keep the upstream `LICENSE`, copyright and
per-file SPDX notices, including the LGPL importer notices. Publish the
exact corresponding source and build files for any applet binary the
project distributes. The fallback additions are GPL-2.0-or-later. The
component also contains files with their own license terms.
[Upstream license inventory](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/LICENSE)

The two options as Codex laid them out before the decision:

| Workflow | How it would work | Tradeoff |
| --- | --- | --- |
| **Git subtree (chosen)** | Import the pinned source into `plasma/globalmenu/`. Make Platinum edits as separate commits. Pull reviewed upstream updates with `git subtree pull` and rerun the applet and theme checks. | A single public checkout contains the source and patches. The applet adds no network dependency at install time. The theme repo carries the imported sources. |
| **Private working repo and public patches (not chosen)** | Use a standalone private repo such as `orlfman/global-menu-KDE` with a public `upstream` remote. Export ordered patches from the working branch. Put them, the source pin and the license record in the public theme repo. The installer fetches and verifies the exact public revision, then applies the patches in a staging checkout. | The theme checkout carries the patch series. Private development stays in a separate repo. A clean install needs network access to fetch the base, and each update adds a patch export and replay step. |

The subtree is preferable for a bundled dependency because a theme checkout
is sufficient to rebuild the applet against a new Plasma release once the
build dependencies are installed. The private-repo workflow follows the
htop-gpu packaging pattern. GitHub makes forks of public repositories public,
so that workflow calls for a standalone repo with an upstream remote.
[GitHub fork visibility](https://docs.github.com/en/pull-requests/reference/forks)

### Implementation order

1. **Trial the pinned applet in nested Wayland.** Place it in the stock
   menu's slot in the 20 px Platinum bar. Check desktop focus at login,
   a desktop click, Show Desktop, Dolphin, Kate, and a window without an
   export. Include the Claude desktop app if it is available in the trial
   and confirmed to export no menu. Check rapid focus changes, delayed or
   disappearing exports, an open menu during a switch, hover and keyboard
   navigation, and focus on either screen with the panel on the primary.
   Compare the open title with the existing Platinum reference checks.
   [Plasma test harness](docs/DEVELOPMENT.md#the-plasma-style-and-the-menu-bar)
2. **Import the subtree, then patch the applet.** Rename it to the user's
   chosen name: display name **Platinum Global Menu** (`KPlugin.Name` in
   `metadata.json`), plugin ID `platinum.globalmenu` (the
   `plasma_add_applet` target and `KPlugin.Id`), translation domain
   `plasma_applet_platinum.globalmenu`, and matching QML/resource paths,
   so it can coexist on disk with the original package. Keep upstream's
   author entry and add the theme alongside it. Keep one global-menu
   widget active in the panel because both use `org.kde.kappmenuview`.
   Trim the fallback to **File** (New Dolphin Window, New Folder on
   Desktop…) and **Go** (Home, Desktop Folder, Documents, Downloads, Trash).
   Use explicit locations and resolve local folders with the XDG directory
   settings. Reuse upstream's validated folder creation where it fits. Keep
   the upstream task model, D-Bus import, menu source switching and pop-up
   behavior unless testing identifies a Platinum-specific change. Retain
   native menu search for apps that export menus. Keep Platinum's patches
   and updated tests attributable as separate `globalmenu:` commits (see
   Source management).
   [Upstream fallback actions](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/desktopfallback.cpp#L129-L162) · [Upstream source switching](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/appmenumodel.cpp#L386-L454)
3. **Build and discover it user-scope.** Add the applet to the existing
   `install.sh` build and stage it before any panel changes. Check the
   staged `.so` and dependencies. Put it in a dedicated user plugin root,
   for example `~/.local/lib/macos9-theme/global-menu/plasma/applets/platinum.globalmenu.so`,
   using the existing install manifest and Plasma login script to expose
   the root on `QT_PLUGIN_PATH`. At the pinned revision, the `.so` embeds
   its QML and resources, including the applet package entry points. Stage
   translation catalogs as needed. Check actual `plasmashell` discovery and
   loading before enabling the applet. Test a first install with a shell
   that predates the login hook and after a fresh login. The upstream
   installation notes call for logging out and back in even with a system
   install. Passing `QT_PLUGIN_PATH` to `plasma-apply-lookandfeel` alone
   does not update the environment of an already running shell. The
   applet builds with CMake, which the theme doesn't use yet (#318): add
   `cmake`, `extra-cmake-modules`, and checks for `libplasma`,
   `plasma-workspace` (LibTaskManager), `ki18n`, `kwindowsystem` and
   `kconfig` to `preflight_plugin_build` (`install.sh:82–102`) so a
   missing package stops the install before anything changes, and add the
   new packages to the README's "What you need" line.
   [Theme plugin installation](install.sh#L263-L291) · [Upstream applet target](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/CMakeLists.txt#L1-L17) · [Native applet layout](https://github.com/KDE/libplasma/blob/v6.8.3/PlasmaMacros.cmake#L54-L70) · [Upstream first-login note](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/docs/INSTALL.md#L45-L49)
4. **Switch the panel and make the change reversible.** Change
   `plasma/layout.js` and regenerate the look-and-feel copy so new layouts
   choose Platinum's ID once it can load. Use stock as the recovery choice
   when the build or discovery fails. Keep a working installed applet on a
   failed rebuild when it is still compatible. For a customized panel,
   replace the stock widget in place when applying the menu change, with
   the same containment, index and applicable settings. Save enough state
   to undo or retry a partial swap. On uninstall, use the existing complete
   panel restore if it applies. For an in-place migration, restore the
   stock widget in the current managed slot before removing the plugin.
   Respect a later choice to move or remove the menu, and leave other
   applets and their settings alone. Exercise this path without a layout
   reset. [Theme layout source](plasma/layout.js#L35-L43) · [Plasma widget ordering](https://github.com/KDE/plasma-workspace/blob/v6.8.3/shell/scripting/widget.cpp#L90-L144)
5. **Rebuild and verify updates.** Build the applet along with the style
   and decoration on each install or reinstall. Track the Plasma and Qt
   packages the applet builds against because it links to LibPlasma and
   Plasma Workspace's `LibTaskManager`. Test how an incompatible build is
   detected and how an already migrated panel recovers to stock. Hiding a
   stale binary from Qt's search path alone leaves the saved panel pointing
   at that binary's plugin ID. Add a read-only `tools/` check that reports
   new upstream commits relative to the pinned revision. Review updates
   before merging or repinning. QuickBar's reported Plasma 6.8 rebuild
   illustrates the kind of compatibility check needed for a compiled
   menu applet. [Upstream linked libraries](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/CMakeLists.txt#L19-L30) · [QuickBar issue #24](https://github.com/kevinbudz/quickbar/issues/24)
6. **Verify packaging before on-screen review.** Extend
   `dev/test-install.sh` for fresh install, in-place migration, reinstall,
   build or discovery failure, interrupted swap and uninstall. Add nested
   Plasma coverage for first login, stale-binary recovery, alternate themes
   and the focus matrix above. Verify the fitted titles at 100% and at a
   fractional scale, and exercise all File and Go actions in a disposable
   home. Check that a missing CMake package fails the preflight with
   nothing changed (#318), and update the README's "run `./install.sh`
   again after every Plasma update" note to cover the menu as well as the
   decoration. The final check is the user's on-screen review.

## Plan: Qt Quick menus, tooltips and switches (AUDIT.md finding 3)

Asked for by the user 2026-11-21. Revised the same day after Codex's
review (AUDIT.md findings 43-48). **Step 1 (spike) done 2026-11-21**:
results in docs/FINDINGS.md "Qt Quick style spike", code in
`spikes/qtquick/`. It confirmed the approach with these changes: KDE's
parts are hidden (`opacity: 0` through a `Binding`), never replaced, and
our item sits next to them; a hidden `QWidget` tells the items when the
app's style changes; `Menu.delegate` is overridden too; the Kirigami link
is needed. **Built in `style/quick` 2026-11-21 (steps 2-5, 7):** menus,
menu bar, combo box list, tooltips and switches; `dev/check-quick.sh` 12
of 12 (each piece equals its widget counterpart, and after a switch to
Fusion equals KDE's own style). **Then (same day):** step 8 (install.sh
installs it, the login script turns it on as planned), switches checked
(Space, accessible role and state as with KDE's style), and real pop-ups
in the nested KWin (in-window pop-ups, which is what Qt Quick uses by
default, and a menu as its own window: frame, shadow and see-through
corners right). **Step 6 done (same day):** dialogs in the measured plain
modal frame (white body, no dimming), drawers framed like menus on their
open side, the range slider from the QSlider's groove and thumbs; list
rows were already right. Left: step 9 (audit, the user's review).
Open: a menu opened as its own window lands at the window's corner, not
where asked (KDE's style not compared: its menu didn't open in that
test).

**What's wrong.** Qt Quick apps (System Settings pages, Discover, other
Kirigami apps) use KDE's Qt Quick Controls style, `org.kde.desktop`
(qqc2-desktop-style 6.32). It draws buttons, check boxes, radios, sliders,
progress bars, fields, spin boxes, closed combo boxes, tabs, scroll bars
and tool buttons through the QStyle, so those are Platinum already. These
are drawn in its own QML instead (read in
`/usr/lib/qt6/qml/org/kde/desktop/`):
- `Menu`: a `Kirigami.ShadowedRectangle` with rounded corners and a soft
  shadow; `MenuItem`: a highlight `Rectangle` in the focus color at 30%
  opacity; `MenuSeparator`, `MenuBar`, `MenuBarItem` likewise.
- The combo box's pop-up list: `ComboBox.qml` builds its own `Menu` and
  `MenuItem` delegate inside the file, so a `Menu` override alone doesn't
  reach it (finding 47).
- `ToolTip`: a rounded `ShadowedRectangle`.
- `Switch` and `SwitchDelegate`: a Breeze-like sliding switch. Mac OS 9
  had no switches.
- List rows (`ItemDelegate`, `CheckDelegate`, `RadioDelegate`,
  `SwipeDelegate`), `Popup`, `Dialog`, `Drawer`, `RangeSlider`,
  `BusyIndicator`, `PageIndicator`, `RoundButton`.
- Kirigami's own components (cards, inline messages, page headers) are
  drawn by Kirigami, not by any Qt Quick Controls style: only their colors
  follow the theme.
Plasma's own panels and pop-ups use Plasma Components and the Plasma
style, so they're not part of this.

**Approach.** Keep the Platinum QStyle as the one source of the look. Add
a small Qt Quick Controls style of our own that overrides only the
controls above and falls back to KDE's for everything else. The fallback
import is pinned to the version KDE exports, `import org.kde.desktop 1.0`
in our `qmldir`: with `auto` the loader asks for KDE's module at our own
version and the app doesn't open (finding 43).

Drawing: the overrides paint through the QStyle with a small C++ Qt Quick
item of our own (`QQuickPaintedItem` calling the application's QStyle;
public Qt API only). It hands the style what a widget would: menu row
position (first, last, separator), combo pop-up row, checked state, and so
on, through `QStyleOption::styleObject` properties the Platinum style
reads next to the `QMenu`/`QComboBox` pointers it uses today. That keeps
the measured first-row and last-row bevels (REFERENCE.md "Menu
highlight"), which KDE's own bridge can't pass on: it calls `CE_MenuItem`
without a widget (finding 45). The tooltip uses the same item with the
QStyle's tooltip drawing.

**Decided by the user (decision 13): that item.** The other choice was
KDE's private `StyleItem` bridge from `org.kde.qqc2desktopstyle.private` (less
code, but a private module this project would depend on, against the
"only officially supported theming hooks" rule; it can change with any KDE
Frameworks update, and it loses the row context above).

Colors, from the captures (finding 46):
- Menus, menu bar titles and combo pop-up rows: #333399 with white text,
  the measured bevel on first and last rows (`popup-open.png` (700,306),
  `menu-view-checked.png`), as the widget menus already draw it.
- List rows in ordinary views: #CCCCFF with black text, as in the file
  dialog list (`dialog-file-open.png` (780,341)).
- Finder's selected name (an inverted label, not a row) is a Finder
  look, not used here.
- Selection, keyboard focus and hover are kept apart: selection is the
  color above; keyboard focus gets the 1 px #6666CC ring the widget style
  draws (AUDIT.md finding 16); lists get no hover highlight (Mac OS 9
  had none); menu rows highlight under the pointer as menus do.

Switches keep everything that makes them switches (their role and checked
state for screen readers, Space to toggle); only the indicator is drawn
as a Platinum check box.

**When it's on** (finding 44). Two layers:
1. The login script sets `QT_QUICK_CONTROLS_STYLE` and adds our folder to
   `QML_IMPORT_PATH` only when `kdeglobals` `[KDE] widgetStyle` is
   `Platinum` at login, you haven't set the variable yourself, and KDE's
   module is the version our overrides were checked with. After a plain
   install (no switch) nothing changes.
2. Each override only takes effect while the running app's QStyle is
   Platinum (our C++ item reports it and follows style changes; the
   overrides use `Binding { when: ... }`, which puts KDE's own look back
   when it's false). So switching to Breeze in System Settings gives KDE's
   look straight away, in apps already running and in apps the session's
   launcher starts later with the old environment; the variable itself is
   gone from the next login.

Kirigami finds its color and size plugin by the style's name
(`kf6/kirigami/platform/<style>.so`). Codex's probe saw the same grid unit
and text color with and without a link to `org.kde.desktop.so`, but those
two values don't prove which plugin loaded. The spike settles whether the
link is needed. If it ships, install.sh gets a link kind of target (the
record keeps where it points; uninstall removes only that link), with
install tests; today the installer handles only files and folders.

Not chosen: patching or copying `org.kde.desktop` (57 files plus a
compiled plugin; breaks with every KDE Frameworks update), or the Union
style engine (the whole style would have to be redone in its format).

**Steps.**
1. **Spike, sandbox only.** (Done; combo rows and real pop-up windows in
   the nested KWin moved to steps 3 and 7.) A minimal style: `ToolTip` and `Menu`/
   `MenuItem` overrides drawn with our item, `import org.kde.desktop 1.0`.
   Check in `dev/kirigami.qml`, `dev/gallery.qml` and System Settings in
   the nested KWin (`dev/app-test.sh`), and in a Qt Quick app without
   KDE's platform theme (`QGuiApplication` only):
   - the app opens, and each control comes from where it should (ours
     marked; the others KDE's, e.g. a button background that is KDE's
     `KQuickStyleItem`);
   - Kirigami's colors and sizes, and which platform plugin loaded (Qt's
     plugin loader trace), with and without the link;
   - KDE's platform theme leaves an already-set `QT_QUICK_CONTROLS_STYLE`
     alone;
   - a selected first row, a selected last row, a separator and a combo
     pop-up row against the widget renders;
   - the `Binding` fallback: switching the QStyle at run time brings back
     KDE's look.
   Record the results in docs/FINDINGS.md. If the variable route or the
   fallback doesn't hold, stop and bring the options to the user.
2. **Inventory.** Render the galleries and a few System Settings pages,
   list every control from the list above that's visible and wrong, and
   pair each with its Mac OS 9 capture, with separate fixtures for
   ordinary views and for menus.
3. **Menus** (most visible): `Menu`, `MenuItem`, `MenuSeparator`,
   `MenuBar`, `MenuBarItem`, and the combo box's pop-up: our `ComboBox`
   keeps KDE's closed control and replaces only its `popup` and
   `delegate` (finding 47). Compare against the widget menu renders,
   which are already pixel exact.
4. **Tooltips**: the help balloon, as the widget tooltip draws it.
5. **Switches**: Platinum check boxes, switch behavior kept; check Space
   toggling and the accessible checked state.
6. **List rows and pop-ups**: #CCCCFF rows with black text, focus ring
   for keyboard focus; square pop-up, dialog and drawer frames like the
   widget ones.
7. **Checks**: Qt Quick regions in `dev/check-style.sh` rendered with
   `dev/build/quickshot`. A pop-up is a separate window by default and a
   window grab silently leaves it out (finding 48), so region tests set
   `popupType: Popup.Item` and assert the pop-up's own pixels are in the
   image; real pop-up windows are checked in the nested KWin. Sanitizer
   run; app pass with System Settings; activation cases: plain install,
   `--apply`, switching away in a running session, an app launched after
   that, next login.
8. **Packaging**: the style folder, our plugin and (if needed) the
   Kirigami link become install targets (record, checksums, uninstall);
   the login script's conditions as above. Install tests and the live
   test cover it.
9. **Audit and the user's on-screen review.**

**Risks.** The variable reaches every Qt Quick app in the session, KDE or
not (the spike's `QGuiApplication` case). KDE's controls we fall back to
can change with an update (the version guard turns our style off then).
Kirigami's own components keep Kirigami's shapes.

## Open questions

- Include Mac OS 9 sound set equivalents? (Can't ship Apple sounds.)
- Before going public (AUDIT.md finding 25; the user: it waits until
  they're ready to go public): the style's check box and radio sprites and
  button corners (`style/platinum/sprites.h`, `slices.h`) are measured
  pixel by pixel from the captures. They're tiny generic UI shapes, but
  redrawing the check mark and radio dot by hand is the safe choice for a
  public release, and the git history still has the older raw tables.
- Window shade (collapse) vs minimize: settled for Wayland (KWin 6.8 doesn't
  shade Wayland windows, so the collapse box minimizes; docs/FINDINGS.md).
  X11 shading is untested.
