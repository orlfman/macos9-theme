# macos9-theme: plan

## Status

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
  `icons/custom/{all,light,dark}/` override layer (`#119` cross-dir variant
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
in `docs/AUDIT-REQUEST.md`; today 135/135, 19/19, 367/367, 37/37, 29/29):
`dev/check-style.sh`, `dev/check-plasma.sh`, `dev/test-install.sh`,
`dev/test-install-live.sh`, `dev/check-quick.sh` (DEVELOPMENT.md says what
each covers). Audit rounds: Codex appends to AUDIT.md; verify each finding,
fix it with a test, record it there and in CHANGELOG.md; commit and push
only when the user says so.

### Claims

One row per component. `nobody` = free. See AGENTS.md "Working together".

| Component  | Folder(s)                 | Claimed by | Status      |
|------------|---------------------------|------------|-------------|
| shared     | docs, tools, dev, scripts | nobody | dev/ sandbox + tools/compare.py done (`dev/run.sh` isolates `XDG_CONFIG_DIRS=/etc/xdg`); test-install-live.sh uses real `XDG_CONFIG_DIRS` cascade (#142); docs fixed (AUDIT 24); Finder folder palette recorded in docs/REFERENCE.md (#107); `dev/test_icons_phase1.py` (80/80), `scripts/manifest_ops.py` (#125 `rmdir`-only), `scripts/icon_prefs.py` (v3 durable transaction, #124/#126–131/#133/#139–142), hardened `dev/test-install.sh` (727/727), Milestone 1 GTK discovery harness verified through #162 (32/32 controls), Milestone 2 GTK 3 verification suite (`dev/check-gtk3.sh`, `dev/gtk3-check/`) verified (51/51 Wayland, 47/47 Broadway), Milestone 3 Batch 1 harness (`dev/check-gtk3-m3b1.sh`, `dev/gtk3-m3b1/`) verified (39/39 Wayland, 38/38 Broadway), Milestone 3 Batch 2 harness (`dev/check-gtk3-m3b2.sh`, `dev/gtk3-m3b2/`) verified (62/62 Wayland, 61/61 Broadway), GTK 4 harness (`dev/check-gtk4.sh`, `dev/gtk4-check/`) 216/216 Wayland, 144/144 Broadway (#181–188 fixed and verified), and Firefox Milestones 1–7 suites (`dev/firefox-test.sh`, `tools/check-firefox-selectors.py`, `dev/check-firefox-m{1,3,4,5,6}.sh`: 46/46, 36/36, 34/34, 32/32, 81/81; #189–208 fixed and verified) |
| reference  | reference/, docs/REFERENCE.md | nobody | 82 VM captures (incl. `ie5-window-blank.png` backed up in `macos9-theme-reference` `05292a6`); first real Platinum desktop archived at 100%, 150% and 200% in reference/testing/; measurements partial |
| colors     | colors/                   | nobody     | Platinum.colors done (sandbox-checked) |
| decoration | decoration/               | nobody | plugin works in nested KWin; frame pixel exact; only the three Mac OS 9 boxes are created (AUDIT 20); audit #86, #90, #96 and #99 verified |
| style      | style/                    | nobody | batches 1-7 + tooltips done (pixel exact); audit fixes #15-#19, #32 (keyboard focus ring, mixed check box, polish symmetry, RTL fallback, 64-bit scroll math, reversed scroll bars); Qt Quick style in style/quick: menus, menu bar, combo list, tooltips, switches (AUDIT 3, check-quick 29/29; installed by install.sh); also dialogs (measured modal frame), drawers, range sliders; combo lists track live model edits (#63); compact tab close indicator and selected state verified in Kwi (#71–74); editable combo styled and verified in KDE file picker (#224); open: size grip; audit #85, #87–89, #91–94, #97 and #100 verified; #95 open; bottom tabs (Konsole, Kwi) drawn as the top tabs upside down, `dev/check-tabs.sh` 50/50 (2026-11-25, Codex #236–237 and Gemini #238–239 fixed) |
| plasma     | plasma/                   | nobody | menu bar, global theme, dock done (headless); selection text contrast fixed (AUDIT 22); main screen only (decision 10); resizable menu bar ends and divider (AUDIT 23), with complete divider dots and pixel comparisons across four panel heights (AUDIT 69–70); #98 table reader verified; global theme defaults updated to `Theme=WhiteSur-lavender` (#110); default dock ends with the own `platinum.trash` widget (color empty/full icons sized like the dock apps; 2026-11-24) |
| icons      | icons/                    | nobody | #101–109, #111, #116, #118–121, #123, #132, #134, #135, #137, #143 committed on `main` against pinned `2026-09-10` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`); external pin (`icons/whitesur-pin.json`), tracked custom layer (`icons/custom/{all,light,dark}/` + cross-dir variant aliases), read-only update review (`icons/review-whitesur-update.sh`), mandatory-`flock` full-`fsck` bare-git cache (`icons/fetch-whitesur.sh` with safe user-owned symlinked `~/.cache`), recovery-safe journaled publish, archive + linked-worktree safeguards, and disposable suite (`dev/test_icons_phase1.py`, 80/80); full-copy + custom layer retained |
| cursors    | cursors/                  | nobody | bundled black cursors (`macOS-cursors`) installed and selected by the global theme, verified in nested Plasma; discovery, selection and undo verified (#78–#84). No cursors of our own (decision 8, user). |
| gtk        | gtk/                      | nobody | GTK 3 install and removal verified. GTK 3 and the GTK 4 initial slice, menus/lists, tabs/ranges and header bars/tooltips are committed. GTK 3 inactive boxes, GTK 4 movable alert, menu buttons and level bars added locally (uncommitted); 205/205 Wayland, 133/133 Broadway. Next: user review, then GTK 4 packaging (Milestone 6). |
| firefox    | firefox/                  | nobody | Production-ready on Linux. Normal and private collapsed tabs verified on Firefox 160.0.1 (M4 36/36, #211–212). |
| extras     | extras/, wallpapers/      | nobody | Pastel Ribbon Landscape, Lavender Desktop Pattern (default), Platinum Waves, Platinum Glass, Platinum Nebula, Finder Waves and Retro Lavender Ripples packaged with the global theme (the last five added 2026-11-25, user-supplied). Platinum Lavender terminal palette verified in disposable Kwi and Konsole and included in install and undo (#173–176 fixed). Plasma Login Manager, splash and lock screen remain. |
| packaging  | install.sh, uninstall.sh, packaging/ | nobody | install.sh / uninstall.sh rebuilt after Codex's four audits (#4-#14, #27-#31, #34-#42 fixed); Qt Quick style & pass-through (#59–65); wallpapers (#75–77); bundled cursors (#78–84); WhiteSur Lavender #110, #112–115, #117–118, #122, #124–131, #133, #135–136, #138–143 committed on `main` (`dev/test-install.sh` 702/702 with real `XDG_CONFIG_DIRS` cascade; `dev/test-install-live.sh` 40/40 in user's terminal); live plain reinstall completed and visually approved by user; desktop uninstall untested; terminal palette audit #173–176 fixed, install/undo verified at 727/727 |

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
5. **plasma**: menu bar layout, Plasma style, look-and-feel package.
6. **icons**, **cursors**, fonts.
7. **gtk**, **firefox**, **extras**.
8. **packaging**: install/uninstall to user scope with backups; full audit;
   user's on-screen review.

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
