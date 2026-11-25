# macos9-theme: audit log

Rules: AGENTS.md "Audits". Newest sections first. Finding numbers run across
the whole project and are never reused.

**Bottom tabs independent audit, 2026-11-25.** #236–239 all verified fixed (`dev/check-tabs.sh` 50/50, `PE_FrameTabBarBase` AA diffs 0/10, `-Wall -Wextra -Wshadow` 0 warnings, `dev/check-quick.sh` 29/29, ASan/UBSan clean). No open tab findings. User desktop review is pending.

## 2026-11-25, Claude (Opus 5.5) — fixes for Gemini's tab findings #238–239

- **#238 fixed.** `PE_FrameTabBarBase` now turns antialiasing off like the other tab parts. This also applied to top tabs before. `dev/tabcheck.cpp` now draws the base, a face, and the pane with and without an antialiasing painter at 1.25x, 1.5x and 1.75x, top and bottom (18 checks); without the fix exactly the 6 base cases Gemini reported fail.
- **#239 fixed.** The label's inner rectangles are renamed (`textSpace`, `textArea`, `textRect`); `-Wall -Wextra -Wshadow` reports no warnings in `platinumstyle.cpp`.
- Checks: `check-tabs` 50/50, `check-style` 135/135, `check-quick` 29/29.

## 2026-11-25, Antigravity (Gemini 4 Neon) — bottom tabs audit (correctness, stability, performance, latency)

Audited Claude's uncommitted tab changes over `b54c2f7` (`style/platinum/platinumstyle.cpp`, `dev/tabcheck.cpp`, `dev/check-tabs.sh`, `dev/tabs-quick.qml`, docs).

- **Verified clean (no P1/P2 findings):**
  - **#236 · P2 · verified** and **#237 · P3 · verified:** `dev/check-tabs.sh` passed **32/32** (including LTR/RTL close-button clearance on top & bottom tabs, exact fractional-scale mirror model at 1.25×/1.5×, and Qt Quick footer `TabBar`), and `dev/check-quick.sh` passed **29/29**.
  - **Stability:** `drawNineSlice` (`w < 2 * K || h < 2 * K`), `drawTab` (`row < TabHeight && row < r.height()`, `to >= from`), balanced `painter->save()`/`restore()`, and `eventFilter` `tabBar()->isVisibleTo(tw)` guards are all sound. `dev/tabcheck.cpp` passed under `-fsanitize=address,undefined` (`ASAN_OPTIONS=detect_leaks=0`) with zero diagnostics.
  - **Performance & latency:** `flipVertically()` is two O(1) `QPainter` transform ops (`translate` + `scale(1, -1)`) with zero allocations or offscreen image copies; `SE_TabBarTabText` is O(1) arithmetic. No measurable paint latency added.
- **#238 · P3 · open (correctness).** `PE_FrameTabBarBase` (`style/platinum/platinumstyle.cpp:1843–1856`) calls `painter->save()` and `fillRect()` for the 3 seam rows without `painter->setRenderHint(QPainter::Antialiasing, false);` (unlike `CE_TabBarTabShape` and `PE_FrameTabWidget`). Reproduced with an offscreen probe: **6/10** cases (north and south at 1.25×, 1.5×, and 1.75×) differ when called with an antialiased `QPainter`.
- **#239 · P3 · open (hygiene).** `CE_TabBarTabLabel` (`style/platinum/platinumstyle.cpp:1661,1673`) introduces two `-Wshadow` warnings (`area` shadowing line 1654, `text` shadowing line 1660) — the only `-Wshadow` warnings in `platinumstyle.cpp`.
- **Limits:** Code review, `dev/check-tabs.sh` (32/32), `dev/check-quick.sh` (29/29), ASan/UBSan `tabcheck`, `-Wall -Wextra -Wshadow` syntax check, and offscreen `PE_FrameTabBarBase` AA probe. Nested KWin Kwi/Konsole captures were not re-run; user live desktop review is pending.

## 2026-11-25, Claude (Opus 5.5) — fixes for bottom tab findings #236–237

- **#236 fixed (reproduced first).** In a 230 px closable `QTabBar` with a long elided title, the label painted 5 dark pixels inside the hidden close button's area in LTR and 18 in RTL, on top **and** bottom tabs, while Fusion painted none. So it predated the bottom-tab work and caused the top-tab overlap seen in Konsole. Text-only labels now take their horizontal extent from `SE_TabBarTabText`; icon labels keep Qt's own layout, which already makes room for buttons. All four cases now measure 0, and `check-style` stays 135/135, so top tabs without buttons are unchanged.
- **#237 fixed.** At 1.25x and 1.5x, `dev/tabcheck.cpp` now compares each bottom part with the 1x top part flipped and scaled the way Qt's raster engine scales whole pixels (logical row n covers device rows qRound(n·dpr) to qRound((n+1)·dpr)), and requires the top part to match that model too. Added `dev/tabs-quick.qml`: a Qt Quick header and footer `TabBar` through KDE's bridge, where the footer must equal the header flipped (and differ from it unflipped).
- Negative controls: removing the face flip fails 18 checks; drawing text across the whole tab fails all 4 close-button checks.
- Checks: `check-tabs` 32/32, `check-style` 135/135, `check-quick` 29/29. Not rerun: the nested Kwi and Konsole screenshots (Kwi supplies its own labels; Konsole's labels now stop before the close button).

## 2026-11-24, Codex (GPT-6.2 Sol) — audit bottom tabs

Reviewed Claude’s working-tree patch over `b54c2f7`. Rebuilt the style and reran `dev/check-tabs.sh` (27/27), `dev/check-style.sh` (135/135 pixel-exact regions), and `dev/check-quick.sh` (29/29). Captured Kwi with two tabs and a long title in three isolated nested KWin sessions. Each screenshot shows mirrored tab faces, a visible selected-tab opening, upright labels and distinct close buttons. Evidence is in `dev/build/kwi-tabs-audit.OvNEXs`. The audit covered rendering. Tab drag, keyboard interaction, and overflow in Kwi remain unverified.

- **#236 · P2 · open.** The south label renderer centers iconless text across the full tab and ignores the space reserved by Qt for tab buttons. A 170 px closable tab bar with a long elided title painted 10 text pixels inside the close-button rectangle in LTR and 40 in RTL. Fusion, which previously handled south labels, painted zero with the same options. Keep south labels upright and derive horizontal placement from Qt’s tab text sub-element.
- **#237 · P3 · open.** The fractional-scale predicate checks only whether each south pixel is in the north image’s palette. Missing or misplaced face rows can pass. Compare against the expected reflected shape with device-pixel row rounding. The offscreen fixture also exercises Qt Widgets only, while the plan calls for a Qt Quick footer fixture.


**Default wallpaper switch (`b50bad5` / `c61c687`) audit, 2026-11-24.** Verified clean: `plasma/make-plasma.py` and `platinum.desktop/contents/defaults` match (`Image=platinum-lavender`), both wallpapers remain installed/removable via `scripts/common.sh`, `dev/plasma-test.sh` links both, `dev/test-install-live.sh` passed 41/41, and `dev/build/test-home-live/wallpaper-desktop.png` renders Lavender Desktop Pattern on both screens. No findings.

**`platinum.trash` `openTrash()` audit, 2026-11-24.** Verified clean over `db9b3b2`: `kioclient exec 'trash:/'` (`tag: "open"`) fixes `Qt.openUrlExternally("trash:/")` showing "Choose Application", covers all 6 activation paths, avoids `onNewData` recursion, and exits after handoff so `disconnectSource` cleans up. `dev/check-trash.sh` 6/6. No findings.

**KDE file picker (`d342ba7` + `#235`) independent audit, 2026-11-24.** Verified clean: #235 fixed and verified (`painter->save()`/`setRenderHint(QPainter::Antialiasing, false)`/`restore()`, `dev/check-style.sh` 135/135 + `checkEditableCombo()`). No open findings. User desktop review is pending.

**`platinum.trash` re-audit, 2026-11-24.** #228–230, #232–234 verified fixed in the working tree (`dev/check-trash.sh` 6/6 plus realistic sibling-dir/`Trash/info`/delete/recreate/idle probe; idle models confirmed at `file:///` instead of `$HOME`). #231 (P3) partly fixed (`Unsorted`; home-trash-only and `plasma5support` remain QML-only trade-offs). No P1/P2 findings remain. User desktop review (hover bevel, drag-to-trash, Empty Trash) is pending.

**Default dock Trash audit, 2026-11-24.** #225–227 addressed by `platinum.trash` and `test-install-live.sh` dock assertion (see `platinum.trash` audit below). User desktop review is pending.

**KDE portal file picker, 2026-11-24.** #224 fixed. The editable path, Name and File type controls use Platinum field borders and dropdown arrows. Desktop visual review is pending.

**#223 · P3 · verified, 2026-11-24.** Combined the separate loading indicator with the native Firefox menu. A real loopback page load switched the menu glyph to the Firefox logo, the menu opened during the load, and the hamburger returned after completion (`dev/build/firefox-real-load.HDgkjQ`). The M4 check covers the animated background and reduced motion.

**#222 · P3 · verified, 2026-11-24.** The legacy Bookmarks tree painted gray hover independently of the sidebar theme. Its hovered and selected rows now paint lavender, and built-in list, button and text selection colors use the Platinum accent. Screenshots with Platinum and Vapor loaded contained lavender across the hovered and selected bookmark rows. Firefox M4 passed 43/43.

**#221 · P2 · verified, 2026-11-24.** Vapor’s generic dark styling also affected Bookmarks, History, Tabs from Other Devices, and Passwords. The built-in sidebar documents now use matching foregrounds, backgrounds, and search field colors. M4 passed 43/43. A disposable profile with both stylesheets verified both Bookmarks implementations, white search fields, and a readable sample login with a masked password (`dev/build/firefox-sidebar-vapor-tools.Mrm06Q`).

**#220 · P2 · verified, 2026-11-24.** With Vapor loaded, Settings inherited a dark canvas and Firefox Nova painted the open address results over a separate dark background. Settings now uses page-scoped Platinum colors and square cards. The open address bar applies light field and suggestion colors to both background layers. Before and after screenshots and computed colors were verified with both stylesheets in Firefox 160.0.1 (`dev/build/firefox-vapor-settings.E8k2JK`).

**#219 · P2 · verified, 2026-11-24.** The live Firefox profile loaded Vapor Firefox after Platinum. Its generic dark root rule overrode the Customize Sidebar foreground and color scheme. A disposable profile using both installed stylesheets reproduced light text on Platinum gray. Matching the panel element in the document rule restored dark labels and a light scheme (`dev/build/firefox-vapor-sidebar.dMmbpd`). M4 now tests a later generic dark rule.

**#218 · P2 · verified, 2026-11-24.** The previous Customize Sidebar fix skipped documents carrying a dark sidebar theme attribute. The Platinum browser now gives the embedded Customize Sidebar a light scheme and the document applies matching colors for the default theme. The M4 probe opens it with collapsed vertical tabs, injects dark sidebar colors, and verifies readable labels. All 38 checks passed on Firefox 160.0.1 (`dev/build/firefox-m4.7UQMzY`).

**Firefox sidebar and selection, 2026-11-24.** #216 fixed light Customize Sidebar labels by setting the color scheme and foreground inside the sidebar document. #217 added black text on lavender for default web text selection. Firefox 160.0.1 M4 passed 38/38, and screenshots showed readable sidebar controls and a rendered lavender selection.

**GTK 3 packaging audit, 2026-11-24.** Verified in disposable homes on the working tree.

- **#213 · P2.** Installing the whole named theme directory hid other toolkits’ resources. New installations manage the GTK 3 subtree with a private palette and add metadata only when needed. Existing GTK 4 CSS, shared palette and metadata survived install, reinstall and undo.
- **#214 · P2.** Undo removed a theme still selected in GTK settings. Undo now checks the surviving file preferences and GSettings, keeps the theme if needed and finishes on retry after a switch. A GTK 3 Broadway widget loaded the installed palette, and both uninstall preview and real undo identified a GSettings selection (`dev/build/gtk3-package-audit.EyhjkU`).
- **#215 · P2.** Preflight accepted a directory with missing referenced artwork. Missing and symlinked referenced artwork now fail validation before installation.

**GTK 3 packaging, 2026-11-24.** A disposable install and reinstall loaded the installed `platinum_selection` color as `rgb(204,204,255)` in a GTK 3 Broadway widget. Uninstall restored a displaced theme directory. Evidence in `dev/build/gtk3-install.NNMa5r`.

**#212 · P3 · verified, 2026-11-24.** The collapsed-tab check measured the icon wrapper only in a normal window. The M4 probe now measures visible favicon elements against their frames and the new-tab icon in both normal and Private Browsing windows, and checks the selected tab uses Platinum styling. All five icons measured zero horizontal offset in both comparisons. M4 passed 36/36 (`dev/build/firefox-m4.vnNzES`).

**#211 · P2 · verified, 2026-11-24.** Collapsed vertical tab icons were 9 CSS pixels right of their beveled frame centers. Restored Firefox’s inline tab margins and removed the extra collapsed strip padding. All three tab icons measured 0 pixels from their frame centers and shared the new-tab icon’s centerline on Firefox 160.0.1. M4 passed 35/35 (`dev/build/firefox-m4.47VPSw`).

Firefox content stylesheet and Private Browsing audit, 2026-11-24. **#209–210 fixed and verified in the working tree.**

Firefox second independent audit, 2026-11-24. **#198–204 fixed in the working tree over `ca8ac31`.** Evidence below.

Firefox independent audit, 2026-11-24. **#192–197 fixed and verified in the working tree over `ca8ac31`.** The five Firefox suites passed 199/199. Desktop visual review is pending.

GTK 4 menus, dropdowns and lists, 2026-11-24. **Verified in the working tree over `ca8ac31`.** 109/109 Wayland and 74/74 Broadway. User visual review is pending.

Firefox Platinum Lavender (Milestones 1–7), 2026-11-24. **#189–191 fixed and verified in the working tree over `ca8ac31`.** All five Firefox verification suites passed end to end (`dev/check-firefox-m1.sh` 46/46, `dev/check-firefox-m3.sh` 34/34, `dev/check-firefox-m4.sh` 34/34, `dev/check-firefox-m5.sh` 31/31, `dev/check-firefox-m6.sh` 41/41, plus `tools/check-firefox-selectors.py` 35/35 `#id` and 1/1 `::part()`), alongside project regressions (`dev/check-style.sh` 135/135, `dev/check-quick.sh` 29/29, `dev/test_icons_phase1.py` 80/80, `dev/test-install.sh` 727/727). User's live Firefox install and on-screen review are pending. #95 remains open.

GTK Milestone 4 initial controls, 2026-11-24. **#181–188 fixed and verified in the working tree.** The follow-up passed 78/78 Wayland and 56/56 Broadway, with all 36 reference crops exact on each. User visual review is pending. #95 remains open.

Terminal palette (Kwi/Konsole), 2026-11-23. **#173–176 fixed and pushed in `b34dcb0`.** Verified ANSI contrast in Kwi and Konsole and preservation of the selected palette during uninstall. #95 remains open.

GTK Milestone 3 Batch 2, 2026-11-23. **#177–180 fixed, independently cross-verified and pushed in `733afcb`.** Final evidence passed 62/62 on virtual Wayland (`dev/build/gtk3-m3b2-plasma.EJiAYi`) and 61/61 on fresh Broadway (`dev/build/gtk3-m3b2-broadway.kDQb5m`) and ASan/UBSan (`dev/build/m3b2-sanitizers.uwTiMK`), including all 45 reference crops at tolerance zero and an 80-combination ASan/UBSan progressbar matrix (`0` diagnostics). User visual review and Batch 2 fractional-scale inspection remain pending. #95 remains open.

GTK Milestone 3 Batch 1, 2026-11-23. **#168–172 fixed and verified in the working tree.** Virtual Wayland passed 39/39 and Broadway passed 38/38. All 27 reference crops matched on both backends. Wayland verifies actual backdrop, an overflowing GTK combobox, and Meld's active window and rendered theme. #95 remains open.

GTK Milestone 2, 2026-11-23. **#163–167 fixed and verified in the working tree.** Virtual Wayland passed 51/51 and Broadway passed 47/47. All 36 reference crops matched at tolerance zero. Wayland verified real backdrop, HighContrast, and the complete dialog on the 150% and 200% compositor outputs. #95 remains open.

WhiteSur Lavender status, 2026-11-23. **#142 and #143 from the first live install (`4fe0894`) are fixed, independently verified, live-reinstalled with the user's visual approval, and committed on `main`.** `dev/test_icons_phase1.py` 80/80, `dev/test-install.sh` 702/702 (with real `XDG_CONFIG_DIRS` cascade), `dev/check-style.sh` 135/135, `dev/check-quick.sh` 29/29, `dev/check-plasma.sh` 19/19 (zero differing pixels), and `dev/test-install-live.sh` 40/40. The Lavender reinstall checkpoint is complete; #95 remains open (P3).

Current C++ audit status, 2026-11-22. Checkpoint 5 passed. #99 (P3) and
#100 (P2) are fixed and verified in the working tree. #95 remains open (P3).

Status: #53–58 passed their original regression cases. #59–68 are fixed in this revision, including code commits `ef8250a` and `fb4156f`. The user has completed the first desktop install. #3 (P3) awaits the user's visual review. The panel-resize fix for #23 is verified at the user’s 32 px setting. The panel follow-ups #69 and #70 are fixed in the working tree and verified in nested Plasma. The user reported that the updated Kwi tab close button worked well on their desktop (#71–74). Wallpaper findings #75–77 are fixed and verified in disposable Plasma. Cursor findings #78–80 are fixed; the cursors are now bundled (`cursors/`), which removes the external download they concerned. The bundled cursor follow-ups #81–84 are fixed in the working tree. The decisions on #21, #25 and #26 still apply.

## 2026-11-24, Claude (Opus 5.5) — bottom tabs for Konsole and Kwi

- Implemented `docs/KWI-TABS-PLAN.md` plus Konsole. South-shaped tabs (`RoundedSouth`, `TriangularSouth`) now draw the measured north tab faces, tab bar base and pane flipped vertically; labels stay upright. Size, tab bar placement, pane geometry and the document-mode pane paint cover south too. North drawing is unchanged.
- `dev/check-tabs.sh` (new, 27/27): south faces in normal, current, pressed and disabled states, the base and the pane are exact mirrors at 1x and 2x and use only the north colors at 1.25x and 1.5x (row rounding prevents a row-for-row mirror there); the bottom label is the top label 2 rows lower; whole plain and document-mode `QTabWidget`s mirror with 0 differing pixels. `check-style` 135/135, `check-quick` 29/29.
- Nested KWin at 100%: Kwi (`TabBarPosition=Bottom`) and Konsole (`TabBarPosition=Bottom`) show Platinum bottom tabs with the current tab opening into the terminal. Kwi's top tabs already used the Platinum face. Konsole clips long labels behind the close button, as it does with top tabs. Not checked: 150% and 200% in the apps, tab dragging, overflow scrolling, and the user's desktop.

## 2026-11-24, Antigravity (Gemini 4 Neon) — default wallpaper switch (`b50bad5`) audit

Audited Claude's commits `b50bad5` and `c61c687` switching `--apply`'s default wallpaper from `platinum-ribbon` to `platinum-lavender`.

- **Verified clean (no findings):**
  - `plasma/make-plasma.py` and generated `plasma/look-and-feel/platinum.desktop/contents/defaults` match (`Image=platinum-lavender`).
  - `scripts/common.sh`, `install.sh`, and `uninstall.sh` still package, validate, keep-if-selected, and remove both `platinum-ribbon` and `platinum-lavender`.
  - `dev/plasma-test.sh` links both wallpaper packages for `M9_APPLY=lnf`.
  - `dev/test-install-live.sh` compares both screens against `platinum-lavender/contents/images/3840x2160.jxl` with a documented `stddev > 5` blank-image guard (pattern spread ~9 vs 0 for blank); `dev/build/test-home-live/result.log` passed **41/41** and visual inspection of `dev/build/test-home-live/wallpaper-desktop.png` confirms Lavender Desktop Pattern renders on both screens.
  - `README.md`, `PLAN.md`, `docs/DEVELOPMENT.md`, and `CHANGELOG.md` have no stale "Pastel Ribbon Landscape is the default" references (only a minor line-wrap placement of the parenthetical in `PLAN.md:136`).
- **Limits:** Code review, repo-wide grep, and inspection of Claude's latest `test-install-live` screenshot and log; did not re-run nested KWin in this pass.

## 2026-11-24, Antigravity (Gemini 4 Neon) — `platinum.trash` `openTrash()` audit

Audited Claude's uncommitted change to `plasma/plasmoids/platinum.trash/contents/ui/main.qml` over `db9b3b2`.

- **Verified clean (no findings):** Switching `openTrash()` from `Qt.openUrlExternally("trash:/")` to `run("kioclient exec 'trash:/'", "open")` routes `trash:/` through KIO (resolving it as a folder in Dolphin instead of prompting "Choose Application" for `x-scheme-handler/trash`), covers all 6 open paths (`onClicked`, `"Open"` action, `Plasmoid.onActivated`, `Keys.onPressed`, `Accessible.onPressAction`, and the missing-`kdialog` fallback), uses tag `"open"` so `onNewData`'s `"empty"` exit-127 fallback cannot recurse, and uses unique `serial` sources so `disconnectSource` cleans up after `kioclient exec` exits.
- **Checks:** `git diff --check` clean; `dev/check-trash.sh` passed **6/6**.
- **Limits:** Code review and offscreen `TrashState` check only; the user already confirmed `kioclient exec trash:/` opens Dolphin on their desktop, and reinstall + click-test in the live dock remains with the user.

## 2026-11-24, Claude (Opus 5.5) — verification of Gemini's file picker audit (#235)

- **#235 · P3 · confirmed by reading, open.** The editable `CC_ComboBox` branch (`style/platinum/platinumstyle.cpp:1315–1334`) calls `drawField` and `drawEditableComboArrow` without turning antialiasing off, unlike the non-editable branch below it. `drawEditableComboArrow` saves and restores its own clip and transform, and `drawField` changes no painter state, so nothing leaks. The effect is limited to callers that pass an antialiased painter, where field and arrow edges could blend at fractional scales. Not measured. Fix: wrap the branch in `painter->save()`, `setRenderHint(QPainter::Antialiasing, false)`, and `painter->restore()`, then rerun `dev/check-style.sh`.
- **#235 fixed.** The editable branch now saves the painter, turns antialiasing off, and restores it. Probe drawing editable combos with and without an antialiased painter at 1, 1.25, 1.5, 1.75 and 2x, LTR and RTL, focused and not: 12 of 20 cases differed before the fix and 0 after. `check-style` 135/135, `check-quick` 29/29.
- Gemini's "verified clean" items were spot-checked for the shared editable gating (`cb && cb->editable && cb->frame`) only. The remaining clean claims and its visual checks were accepted without re-running. No P1 or P2 issue found.

## 2026-11-24, Antigravity (Gemini 4 Neon) — KDE file picker editable combo audit (`d342ba7`)

Audited Codex's commit `d342ba7` (`style/platinum/platinumstyle.cpp`, `dev/styleshot.cpp`) and evidence in `dev/build/kde-picker.BHekEL/`.

- **Verified clean (no P1/P2 findings):**
  - Bounds and memory safety: `PopupArrowWidth` (`22`) equals `Sprites::PopupArrow.w`, `editableComboPart` caps `arrowWidth <= PopupArrowWidth`, `drawRow` is safe for `width <= 0`, `drawEditableComboArrow` clamps `source` within `[0, sprite.h - 1]` for all `rect.height() >= 0`, and `drawField` guards `width < 8 || height < 8`.
  - Consistency: `rtlFallback`, `sizeFromContents`, `subControlRect`, `hitTestComplexControl`, and `drawComplexControl` all gate identically on `cb && cb->editable && cb->frame`. RTL mirroring (`QStyle::visualRect` + `translate`/`scale(-1, 1)`), embedded `QLineEdit` focus/read-only checks, and disabled/pressed arrow states are consistent with `drawSpinBox` and `PE_PanelLineEdit`.
  - Checks: `dev/check-style.sh` passed **135/135** pixel-exact regions plus `checkEditableCombo()` (LTR/RTL geometry, hit test, focus ring, arrow artwork). Visually inspected `dev/build/kde-picker.BHekEL/{portal-editing,after,picker-1.5,picker-2}.png` against `reference/testing/kde-portal-editable-combo.png`: Path, Name, and File type fields, path icon, and clear button render cleanly at 100%, 150%, and 200% with zero overlap. `dev/build/kde-picker.BHekEL/san.log` passed (`verification=1`).
- **#235 · P3 · open.** Unlike `drawScrollBar`, `drawSpinBox`, `drawGroupBox`, and the non-editable `CC_ComboBox` branch directly below it (`style/platinum/platinumstyle.cpp:1337`), the editable `CC_ComboBox` branch (`lines 1315–1334`) does not wrap `drawField` and `drawEditableComboArrow` with `painter->save(); painter->setRenderHint(QPainter::Antialiasing, false); ... painter->restore();`. Standard widgets default to non-antialiased painters, so this only affects custom antialiased `QPainter` callers.
- **Limits:** Code review, `dev/check-style.sh` (135/135), and visual inspection of Codex's existing portal/KFileWidget/HiDPI captures and ASan/UBSan log. Did not re-run the live nested portal or ASan build in this pass; user live desktop review is pending.

## 2026-11-24, Antigravity (Gemini 4 Neon) — `platinum.trash` #234 verification

Re-audited Claude's follow-up to `TrashState.qml` and `dev/check-trash.sh` over `2a90cd0`.

- **#234 · P1 · verified.** `has(model, folder)` using `status === FolderListModel.Ready && indexOf(folder) >= 0` accurately matches `Trash` and `files` by name even with populated sibling directories (`applications`, `icons`, `Trashcan`, `Trash/info`). `dev/check-trash.sh` passed **6/6**.
- **Startup idle watcher (P3) · verified.** Offscreen `qml` probe confirmed idle `hasFiles` and `files` models remain at `file:///` (`mods=0:.../data 1:file:/// 2:file:///`) instead of `$PWD`/`$HOME` when `Trash` is missing, and verified the full realistic lifecycle (`missing → Trash/info only → Trash/files + item → rm -rf Trash → recreate → empty → 1.3 s idle with countChanges=0`).
- **No new findings.** Ready for user live desktop review (hover bevel, drag-to-trash, Empty Trash).

## 2026-11-24, Claude (Opus 5.5) — fix from Gemini's Trash re-audit

- **Gemini's P3 note fixed.** The idle internal models now start at `/` instead of the current directory, so `$HOME` is no longer watched before the trash exists.
- **New #234 · P1 · fixed (found while checking that note).** `nameFilters` don't apply to folders, so the `Trash` and `files` checks counted every folder. In a real `~/.local/share` that is never zero, so a missing trash could still point the counter at the wrong folder. `TrashState.qml` now finds each folder by name with `indexOf`. `dev/check-trash.sh` now has other folders in the data and current directories; it fails 4 of 6 checks with the old logic and passes 6/6 (5 runs) with the fix.
- Checks: `check-plasma` 19/19 with 0 differing pixels, `test-install-live` 41/41. Installer code is unchanged since the 747/747 `test-install` run.

## 2026-11-24, Antigravity (Gemini 4 Neon) — `platinum.trash` re-audit (#228–233)

Re-audited Claude's fixes in `plasma/plasmoids/platinum.trash/contents/ui/{TrashState.qml,main.qml}` and `dev/check-trash.sh` over `2a90cd0`.

- **#228 · P1 · verified.** `dev/check-trash.sh` passed **6/6**. An additional offscreen `qml` lifecycle probe verified `missing → create+full → rm -rf Trash → recreate+full → empty` all report exact `exists`/`full`/`count` states with zero `$PWD` leakage into the public properties.
- **#229 · P2 · verified.** The 5-second polling `Timer` is removed; `TrashState.qml` is purely event-driven (`countChanges=0` over 1.4 s idle while empty).
- **#230 · P2 · verified.** Commands use unique `serial` source names, drops are batched (200 URLs / 64 KiB per `kioclient move` call), `onEntered`/`onDropped` filter to `file:` URLs with `drop.accept(Qt.CopyAction)`, and missing `kdialog` (`exit 127`) falls back to `openTrash()`. Retaining `org.kde.plasma.plasma5support` and spawning parallel `kioclient` batches on very large drops are acceptable QML-only trade-offs on Plasma 6.8.3.
- **#231 · P3 · partly fixed (accepted QML limit).** `sortField: FolderListModel.Unsorted` removes sorting overhead. Full-entry model retention and home-trash-only counting remain QML-only trade-offs without a C++ KIO backend.
- **#232 · P3 · verified (hover bevel pending visual check).** `Planar` containment uses normal `iconSizes.large`/`huge` sizing, panel slots guard with `Math.max(1, ...)`, and `Plasmoid.onActivated`, `Keys.onPressed`, `activeFocusOnTab`, and `Accessible.*` are wired. Because Plasma's `south` panel margins give `platinum.trash` a 43 px content area while `widgets/tasks` bakes in `top=8, bottom=4` insets for a 52 px task slot, the hover/pressed bevel should be visually checked on the desktop.
- **#233 · P3 · verified.** `dev/check-trash.sh` passed **6/6**.
- **Minor observation (P3):** When `Trash/files` does not exist at startup, the unpointed `files` `FolderListModel` inside `TrashState.qml` still initializes internally against `$PWD`/`$HOME` (`MODEL 2 folder=.../cwd count=5 status=1` in probe) until `Trash/files` is created; public properties remain unaffected (`exists ? files.count : 0`).
- **Limits:** Verified `dev/check-trash.sh` (6/6), custom `qml` lifecycle/idle/startup probes, and code review. `dev/test-install.sh` requires the WhiteSur upstream cache outside the sandbox (Claude reported 747/747). Interactive hover-bevel look, drag-to-trash, and Empty Trash remain pending live desktop review.

## 2026-11-24, Claude (Opus 5.5) — Platinum Trash widget (#225–227)

- **#226 fixed.** The dock uses a new `platinum.trash` widget instead of `org.kde.plasma.trash`. It shows the icon theme's full-color `user-trash` or `user-trash-full`, sizes its icon like the dock's apps (rows 15–40 versus 14–41 for the apps in the 52 px nested dock), uses the tasks hover frame, opens `trash:/` on click, moves dropped local files with `kioclient move`, and asks before `ktrash6 --empty`. Its full state counts only the home trash.
- **#225 fixed.** `dev/test-install-live.sh` now asserts `org.kde.plasma.icontasks,platinum.trash` at the dock's end and no stock Trash. `dev/test-install.sh` checks the installed widget files.
- **#227 fixed.** The PLAN.md `plasma` row records the dock Trash.
- Checks: `check-plasma` 19/19 with 0 differing pixels, `test-install-live` 41/41. The nested render used Breeze icons, so WhiteSur Lavender's trash artwork and drag-to-trash were not checked on screen.

## 2026-11-24, Claude (Opus 5.5) — fixes for Platinum Trash findings #228–233

- **#228 fixed (reproduced first).** With `folder` bound at construction and the trash folder missing, the probe model reported the current directory and 3 unrelated files. New `TrashState.qml` watches `~/.local/share` until `Trash` exists, `Trash` until `files` exists, then `files`. Two more Qt quirks found and worked around: a folder set during construction neither loads nor announces itself, and reassigning the same folder is ignored.
- **#229 fixed.** No timer. Changes come from the models' file watchers.
- **#230 fixed.** Commands get unique source names, drops are batched (200 files or 64 KiB per command), only `file:` URLs are accepted, drops are accepted as copy so the source doesn't delete, and Empty Trash opens the Trash when `kdialog` is missing. `plasma5support` is still used.
- **#231 partly fixed.** Entries are no longer sorted. Other drives' `.Trash-$UID` folders are still not counted.
- **#232 fixed except alignment.** Square slot only in panels, normal icon size on the desktop, keyboard activation, accessibility role and labels, and `Plasmoid.onActivated`. The reported 2 px hover-frame offset was not reproduced or changed.
- **#233 fixed.** `dev/check-trash.sh` tests missing, new, full, emptied and existing trash folders offscreen (6/6, stable over 5 runs).
- Install record target counts updated from 18 to 19 for the widget. The earlier `test-install.sh` failures were caused by a concurrent run in the same test folder.
- Checks run alone: `check-trash` 6/6, `check-plasma` 19/19 with 0 differing pixels, `test-install-live` 41/41, `test-install` 747/747. Drag-to-trash and Empty Trash were not exercised interactively.

## 2026-11-24, Antigravity (Gemini 4 Neon) — `platinum.trash` performance, latency, and stability audit

Audited Claude's custom `plasma/plasmoids/platinum.trash` widget and wiring (`plasma/plasmoids/platinum.trash/{metadata.json,contents/ui/main.qml}`, `plasma/layout.js`, `plasma/look-and-feel/platinum.desktop/contents/layouts/org.kde.plasma.desktop-layout.js`, `install.sh`, `scripts/common.sh`, `dev/{live-test,plasma-test,test-install,test-install-live}.sh`, `PLAN.md`, `CHANGELOG.md`) in the uncommitted working tree over `2a90cd0`.

- **Verified clean:** Full-color `WhiteSur-lavender` trash icon renders cleanly in the 52 px dock (`y=13..43`, center `28.0` matching pinned app icons in `dev/build/test-home-live/wallpaper-desktop.png`, zero QML warnings in `plasmashell.log`). `test-install-live.sh` (41/41 in `dev/build/test-home-live/result.log`) now asserts `bottom=org.kde.plasma.icontasks,platinum.trash`, and `uninstall.sh` removes `platinum.trash` via `scripts/common.sh` `targets`. Horizontal panel `Layout.preferredWidth: height` produced no Qt Quick binding-loop warnings in an offscreen `qml6` probe.
- **#228 · P1 · open (stability / correctness).** When `$XDG_DATA_HOME/Trash/files` does not exist yet (e.g. a fresh account), Qt 6.12's `FolderListModel` silently rejects the missing directory and falls back to `QUrl::fromLocalFile(QDir::currentPath())` (`$HOME` in a real Plasma login). Reproduced deterministically with `qml6`: targeting a non-existent `Trash/files` resolved `ACTUAL_FOLDER` to `$PWD` with `COUNT: 27` (`FIRST_ENTRY: .../.git`). Because `count > 0`, `root.full` becomes `true`, the widget shows `user-trash-full` with `$HOME`'s item count, enables "Empty Trash…", and stops `Timer { running: !root.full }`, leaving the widget permanently stuck watching `$HOME` even after `Trash/files` is created.
- **#229 · P2 · open (performance / idle wakeups).** `Timer { interval: 5000; repeat: true; running: !root.full }` runs unconditionally whenever the Trash is empty, even when `Trash/files` already exists and is watched via inotify. Reproduced with `qml6`: every 5 seconds, `trashFiles.folder = ""; trashFiles.folder = root.filesDir;` cycles `FolderListModel` through `Ready → Null → Loading → Ready`, tears down and recreates the `QFileSystemWatcher` and worker-thread `readdir`, and emits `countChanged(0)` — 720 unnecessary wakeups/hour (17,280/day) in `plasmashell` on an idle desktop.
- **#230 · P2 · open (stability & latency).** `platinum.trash` depends on the deprecated Plasma 5 compatibility module `org.kde.plasma.plasma5support` (`engine: "executable"`) and spawns `/bin/sh -c` for `kdialog`, `ktrash6`, and `kioclient`:
  - `kdialog` is a separate optional package (`kdialog 26.08.3-1.1`, not a dependency of `plasma-desktop`); if absent, "Empty Trash…" silently fails (exit 127) with no feedback, and when present it cold-starts an unparented Qt Widgets process (`--version` alone ~21 ms; full GUI higher) instead of an in-process dialog or KIO job.
  - Verified with `qml6`: `executable.connectSource(cmd)` deduplicates by exact command string, so invoking an identical command while one is running silently drops the second call (`TOTAL REPLIES: 1` for two concurrent calls).
  - Bulk drops build one `/bin/sh -c "kioclient move ..."` string, risking Linux's 128 KiB `MAX_ARG_STRLEN` limit on large selections; `onEntered` also accepts non-`file:` URLs (`http://`, `trash:/`) and `onDropped` calls `drop.accept(Qt.MoveAction)` before `kioclient` runs or succeeds.
- **#231 · P3 · open (performance / memory & multi-volume accuracy).** `FolderListModel` loads, stats, sorts, and retains every top-level entry in `~/.local/share/Trash/files` in `plasmashell` memory just to read `count` (offscreen `qml6` probe: `1 ms` for 100 files, `6 ms` for 2,000, `30 ms` for 10,000 on tmpfs), and misses secondary-mount `.Trash-$UID` directories that `ktrash6 --empty` does empty (showing Empty and disabling "Empty Trash…" when only an external volume has trashed items). Watching `trashrc` (`[Status] Empty=`) or using a tiny C++ KIO/KDirWatch plugin would avoid both the 5 s timer, the `FolderListModel` RAM/CWD bug, and the `P5Support`/`kdialog` subprocess layer.
- **#232 · P3 · open (stability / layout, accessibility, hover alignment).** Binding `Layout.minimumWidth`/`maximumWidth: root.vertical ? -1 : height` locks width to height in `Planar` (desktop) containments where `vertical` is `false` and clamps `maximumWidth` to `0` if `height === 0` during polish. The widget also omits `Plasmoid.onActivated` (breaking Plasma widget shortcuts), `Keys.onPressed`, and `Accessible.{name,description,role}` (all present in `org.kde.plasma.trash`). Visually, `Kirigami.Icon` (`anchors.centerIn: parent`, `y=26`) sits 2 px above the center of its own `widgets/tasks` hover/pressed bevel (`top=8, bottom=4`, center `y=28`).
- **#233 · P3 · open (test coverage).** No automated test exercises `platinum.trash`'s empty/full transition, missing-`Trash/files` startup, drag-and-drop, or "Empty Trash…", and `dev/test-install.sh` was not reported in `CHANGELOG.md`.
- **Limits:** Code review, package inspection, offscreen `qml6` probes (missing-dir fallback, empty-timer churn, 100–10,000 file load benchmark, `P5Support` concurrent-command probe, `RowLayout` binding probe, `TrashPrivate` import check), and pixel inspection of Claude's latest nested-KWin captures (`dev/shots/plasma-platinum-desktop.png`, `dev/build/test-home-live/wallpaper-desktop.png`). Interactive drag-to-trash, full-trash rendering, and live desktop `install.sh --apply` were not run; user visual review is pending.

## 2026-11-24, Antigravity (Gemini 4 Neon) — default dock Trash audit

Audited Claude's uncommitted working-tree changes over `2a90cd0` (`plasma/layout.js`, regenerated `plasma/look-and-feel/platinum.desktop/contents/layouts/org.kde.plasma.desktop-layout.js`, and `CHANGELOG.md`).

- **Verified clean:** `plasma/layout.js` and the generated look-and-feel layout match `plasma/make-plasma.py` output byte for byte (`layout parity: True`, `git diff --check` clean). `org.kde.plasma.trash` is bundled in `plasma-desktop` (`/usr/lib/qt6/plugins/plasma/applets/org.kde.plasma.trash.so`), produced zero trash-related errors or warnings in `dev/build/test-home-live/apply.log` and `dev/shots/plasma-platinum.plasmashell.log`, and rendered cleanly at the right end of the 52 px dock with matching vertical centering (`y=12..43`, center `27.5` vs pinned WhiteSur-lavender app icons `y=13..43` and 40 px bevel buttons `y=8..47` in `dev/build/test-home-live/wallpaper-desktop.png`; `y=16..39`, center `27.5` in `dev/shots/plasma-platinum-desktop.png`). Existing `test-install-live.sh` run (`dev/build/test-home-live/result.log`, 40/40) confirmed `uninstall.sh` restores the user's original panels and widgets. No P1 or P2 findings.
- **#225 · P3 · open.** Neither `dev/check-plasma.sh` nor `dev/test-install-live.sh` asserts that `org.kde.plasma.trash` is actually present on the dock or ordered after `org.kde.plasma.icontasks`. `dev/test-install-live.sh` checks `after_panels` (`0:bottom:52 0:top:20`) after `--apply` without checking `widgets`, and `dev/check-plasma.sh` only checks the dock's top corners; removing or misspelling `org.kde.plasma.trash` would still pass both suites.
- **#226 · P3 · open.** Upstream Plasma 6.8's `org.kde.plasma.trash` forces `"-symbolic"` whenever `inPanel` is true (`org.kde.plasma.trash.so`: `if (inPanel) return iconName += "-symbolic";`). In `dev/build/test-home-live/wallpaper-desktop.png` with `WhiteSur-lavender` active, the Trash therefore renders as a flat monochrome black-outline icon (`user-trash-symbolic`) beside full-color `WhiteSur-lavender` app icons, even though `WhiteSur-lavender` ships full-color trash SVGs (`places/scalable/user-trash.svg`, `user-trash-full.svg`). User decision needed on whether to accept this Plasma panel behavior (and note it in `docs/FINDINGS.md`) or use a custom applet/workaround for a full-color trash icon.
- **#227 · P3 · open.** `PLAN.md` status block and the `plasma` Claims row were not updated to note the default-dock Trash addition (per `AGENTS.md` "Finishing a session").
- **Limits:** Code review, generator-parity check, package/plugin inspection, and pixel-level inspection of Claude's latest nested-KWin captures (`dev/shots/plasma-platinum-desktop.png`, `dev/build/test-home-live/wallpaper-desktop.png`) and logs (`dev/build/test-home-live/result.log`, `apply.log`, `plasmashell.log`). Interactive drag-to-trash, full-trash icon state, and live desktop `install.sh --apply` were not run in this audit; user visual review is pending.

## 2026-11-24, Codex (GPT-6.2 Sol) — KDE portal editable file-picker controls

- **#224 · P2 · fixed and verified.** The portal screenshot
  `reference/testing/kde-portal-editable-combo.png` shows light rounded input
  frames and stock arrow buttons next to Platinum toolbar and dialog buttons.
  In KDE's real KFileWidget, the path and filename are framed editable
  KUrlComboBox instances and the filter is a framed editable KFileFilterCombo.
  The custom QStyle only painted non-editable combos and the embedded editors
  had their own frames disabled. The style now draws the existing Platinum
  field and adapts the measured arrow cap to the widget's natural height.
  The custom mirror geometry and hit test keep the arrow clickable in RTL.
- KFileWidget before and after captures, test output and a nested
  `xdg-desktop-portal-kde` screenshot are in `dev/build/kde-picker.BHekEL`.
  The offscreen probe verified all three editors fit without overlapping
  the arrow, including the path icon inset. Click opened the filter popup,
  keyboard selection committed the second option and closed it, and typed
  filters propagated. Geometry and popup opening also passed at 150% and
  200% Qt scale offscreen. Ctrl+L switched the native portal picker into
  editable-path mode in virtual KWin at 100%. The full Platinum palette and
  all three editable frames are visible in `portal-editing.png`. User desktop
  review is pending.
- The Qt Widgets reference suite passed 135/135 plus the new focused editable
  combo rendering and geometry assertions in both directions. The prior plugin
  failed the new geometry assertion. The standalone
  picker passed with ASan/UBSan and leak checking disabled. Qt Quick passed
  29/29, Plasma 19/19, installer/undo 745/745 and nested install 40/40.

## 2026-11-24, Codex (GPT-6.2) — content stylesheet upgrades and Private Browsing

- **#209 · P1 · verified.** An older theme installation could have a different `userContent.css` in its initial backup than the file present when a later upgrade first managed it. Undo could resurrect a deleted file, remove a newly created empty file, or restore older permissions. The upgrade now records existence, bytes, checksum and permissions at adoption, retains that backup across retries, and archives it on undo. Retrying an interruption refuses a replacement that lost its managed markers. Tests covered creation, deletion, edits with CRLF and mode 0600, interrupted upgrades, and replacement conflicts.
- **#210 · P3 · verified.** Stock browser fixtures also set the private-window color preference. Only themed fixtures now default to the installed value. The private-window check verifies CSS visibility of the mask button and confirms the window actually entered dark mode before checking that Platinum styling switched off.
- Firefox 160.0.1 under nested Wayland, working tree over `ca8ac31`. Discovery 46/46 (`firefox-m1.7hB55u`), chrome 34/34 (`firefox-m4.1dvqM5`), install/undo 85/85 (`firefox-m6.xRfOeO`). The selector check passed 35 IDs and one shadow part. Testing used disposable profiles.

## 2026-11-24, Codex (GPT-6.2) — Firefox desktop polish review

- **#207 · P2 · verified.** The runtime cleanup trap continued recursive deletion when the document portal failed to unmount. Both Firefox harnesses now restrict recursive cleanup to the runtime directory’s own filesystem.
- **#208 · P3 · verified.** The Go test accepted an offscreen or obstructed control, the logo test accepted an unresolved URL, and scrollbar undo tested only absent preferences. Added hit tests, real pointer submission to a local address, a decoded branding image, and live profile coverage for prior size and color settings. Clarified that scrollbar settings affect the profile across Firefox themes. Replaced the M4 startup observer with Firefox’s startup promise after one sandbox startup timeout.
- Firefox 160.0.1, working tree over `ca8ac31`. M3 36/36, M4 34/34, M5 32/32, M6 73/73. Evidence in `dev/build/firefox-m3.zNy8yF`, `firefox-m4.engwOG`, `firefox-m5.4b4OlX`, and `firefox-m6.Fa6elo`. All 35 IDs and one shadow part passed the selector check. Sandbox verification used disposable profiles. Failed unmounts were reviewed in code.

## 2026-11-24, Codex (GPT-6.2) — stale Firefox lock re-audit

**#206 · P1 · verified.** #205 accepted a dead loopback PID even when the advisory lock file was absent. The advisory probe also released both locks before profile mutation. Install and undo now require an existing regular advisory lock file for the stale-link exception, open it without following a symlink, and hold both nonblocking locks through command exit. A new profile with neither lock artifact still follows the existing closed-browser workflow.

The installer suite passed 72/72 (`dev/build/firefox-m6.9a7MMe`). A second process tested both lock mechanisms during and after the command scope. Missing lock file and FIFO cases refused the stale-link exception. The live default profile passed a dry run.

## 2026-11-24, Codex (GPT-6) — Firefox stale profile lock

- **#205 · P2 · verified.** The installer rejected a leftover loopback lock after its PID exited. Install and undo now recognize this case and still check both advisory lock types. They leave the link in place and refuse live, non-loopback, and unrecognized targets.
- Milestone 6 passed 68/68 in `dev/build/firefox-m6.9uEmOT`, including a live advisory lock paired with a stale link. A dry run for the user's default profile reached the install preview. Actual install and undo ran in disposable profiles.

## 2026-11-24, Codex (GPT-6) — root Firefox command audit

Verified the Firefox-only dispatch in the working tree. Both commands forward quoted profile names and return the child exit status. Help and profile listings matched direct invocation from outside the repository. Both rejected the desktop-only `--apply` option with status 2. Desktop install and undo dry runs still selected KDE. The disposable-profile suite passed 64/64, including three new root-entry checks and a real nested Firefox launch. Updated the README wording that described Firefox as accessible only separately. No outstanding shortcut findings. Live user profiles were outside this audit.

## 2026-11-24, Codex (GPT-6) — second full Firefox audit

- **#198 · P2 · verified.** The address band reserved 68 px on the physical left even in RTL, with the label and popup anchored to that side. The band, label separator, expanded field and Home separator now follow inline direction. The live RTL probe measured 68 px right padding, a zero right inset and a 1 px left separator. The LTR whole-pixel suite retained its baseline.
- **#199 · P1 · verified.** Uninstall could return the entire pre-v1 prefs file when an upgrade had adopted a pref the user changed between installs. It now checks the saved values from the time of adoption before restoring the whole file. Three end-to-end tests restored the user's value with the pref applied, the file empty or the file missing.
- **#200 · P1 · verified.** Backup verification missed removed empty directories and permission changes. New backups record entry types and modes as well as file hashes. Older backups still check their original Platinum entry against saved metadata. Install refuses to replace a nonempty state directory whose records are missing.
- **#201 · P2 · verified.** Deduplicating XDG and legacy entries discarded the install-default flag when it was supplied by the second registry. A malformed registry could also block undo despite valid installation records. Discovery now merges default flags, skips unreadable registries with a diagnostic and ignores invalid relative paths marked absolute. Both discovery and recorded-profile undo passed.
- **#202 · P1 · verified.** The browser test launcher recursively removed a caller-supplied profile path before launch. Each default run now has a private profile. An explicit path must resolve under `dev/build/`, and fresh runs refuse an existing directory. Both reuse modes refused an external throwaway directory and left it intact.
- **#203 · P2 · verified.** The selector checker counted arbitrary hash tokens in Firefox sources as element IDs and silently skipped a missing archive if another was available. It now requires all configured archives and checks ID attributes and DOM API references. A color literal used as an ID fails the negative control. All 35 shipped IDs and one shadow part passed.
- **#204 · P2 · verified.** Counting lavender pixels across the desktop allowed the keyboard-focus screenshot check to pass on unrelated chrome. The corrected verifier compares the exact two-pixel rectangle with and without the Home button's focus lock. Substituting the unfocused capture failed only this check (`dev/build/firefox-focus-negative.OO3MUt`). The installer smoke test now checks the compositor exit status and reads the capture from the current run.

Tested on Firefox 160.0.1 under nested Wayland. The five suites passed 207/207 across M1 (46), M3 (34), M4 (34), M5 (32) and M6 (61). Evidence directories under `dev/build/` are `firefox-m1.BUj4KT`, `firefox-m3.djALIB`, `firefox-m4.uNgwwa`, `firefox-m5.Tk87Xu`, and `firefox-m6.ljb9cl`. M2 regenerated all eight mockups and four comparison sheets. RTL verification forced the chrome direction in the sandbox. Translated labels, other Firefox versions and the user's live desktop were outside this run.

## 2026-11-24, Codex (GPT-6) — independent Firefox audit

Reviewed the theme, browser probes and profile lifecycle on Firefox 160.0.1 against the working tree over `ca8ac31`.

- **#192 · P2 · verified.** The inactive-window tab rule lost to the active rule in the CSS cascade. The test cleared its focus locks before reading live computed styles and treated a missing bookmark as a pass. With the old selector, the corrected probe measured a solid outline in a genuinely inactive window (`dev/build/firefox-negative.QUNdAA`). The corrected selector yields no outline. The active 2 px lavender ring follows `docs/REFERENCE.md` and `reference/help-viewer.png`.
- **#193 · P1 · verified.** Text-mode reads normalized CRLF in existing CSS, JavaScript and prefs. The installer also moved a standalone BOM and undo guessed how many separator newlines to strip. Profile reads now preserve bytes, the BOM stays first, and undo removes the recorded separator. Tests compare exact bytes after outside edits, reinstall and migration from an older install.
- **#194 · P1 · verified.** Rollback of an interrupted reinstall could discard outside edits or edited managed files. Pending manifests and marker blocks are now journaled before publishing. Undo checks the actual blocks and file hashes and recognizes completed writes after interruption. Tests cover conflicts, outside edits, directory swaps and the final backup archive move.
- **#195 · P2 · verified.** Moving a pre-existing theme directly into XDG state failed across filesystems. Publication and restoration now stage renames on the profile filesystem, using the verified backup. A real cross-mount install/undo round trip preserved the original tree and modes.
- **#196 · P1 · verified.** Prefix-based cleanup removed unrelated files with installer-looking names. Cleanup now targets the staging directory named in the journal. Invalid managed file types and replaced marker files are detected before updates. A throwaway profile retained its own `.macos9-ff-tmp.personal` through install, reinstall and undo.
- **#197 · P1 · verified.** Opening the state lock truncated its target, and final cleanup could unlink another installer's active lock inode. Install and undo reject symlinked lock files, open the lock without truncating and retain the inode between runs. Tests covered lock contention and symlink refusal.

**Verification.** M1 46/46 (`firefox-m1.5cE6Rg`), M3 34/34 (`firefox-m3.CmKtTG`), M4 34/34 (`firefox-m4.VcySMQ`), M5 31/31 (`firefox-m5.5R2fbr`), M6 54/54 (`firefox-m6.q72g0P`). Evidence directories are under `dev/build/`. The selector checker found 35 IDs and one shadow part in the installed archives. Testing used disposable profiles and nested Wayland, including a real installed-profile cold launch and undo. User visual review and other Firefox versions remain unverified.

## 2026-11-24, Codex (GPT-6) — GTK 4 menus, dropdowns and lists

Verified the new light-mode GTK 4 batch in the working tree over `ca8ac31`.
No open theme findings in the tested controls. Normal, disabled and open dropdown
arrow crops, menubar and header bands, submenu arrow and separator match the
Mac OS 9 captures used by the GTK 3 batch. Measured a 1 px horizontal arrow
offset and half-pixel sampling at odd heights during development and corrected
both. The theme uses the project’s original check and radio sprites.

- Native Wayland/Vulkan passed **109/109** in `dev/build/gtk4-m4-plasma.qFPCLQ`,
  including **53 exact 1× crops**. Broadway Cairo passed **74/74** in
  `dev/build/gtk4-m4-broadway.0fgbik`, including **50 exact crops**. The
  Broadway ASan/UBSan run passed 74/74 (`gtk4-m4-broadway.q9UzMB`, leaks
  excluded). GTK 3 Batch 1 passed 38/38 on Broadway. Regenerating all 220
  PNGs reproduced their bytes and left the 200 GTK 3 assets unchanged.
- The mapped 43-item dropdown overflowed its viewport, filtered to a single
  result, selected the original model’s item 2 and closed. GTK action activation
  changed a check and radio choice and navigated into a submenu. The list
  scrolled and selected item 40. The sorted column model placed Alder first.
  Selected list and column rows were Lavender in the active window and muted
  after KWin activated a second window. The fixture drives GTK APIs.
- KWin identified the separate GTK Settings demo and Widget Factory windows for
  both named themes. The Settings demo’s selected row and measured header corner
  appeared under Platinum. The Adwaita control had neither. Selection and
  unclipped output passed at 150% and 200%, including an exact 2× arrow crop.
  Independent Broadway captures of the closed gallery were identical between
  Platinum and Adwaita for both dark mode and high contrast.
- The verifier rejected four deliberately altered results (arrow, checked menu
  artwork, app capture and search result) in `dev/build/gtk4-menu.0pr5Up/negative.log`.
  Qt Widgets passed 135/135, Qt Quick 29/29, Plasma 19/19, icons 80/80,
  installer/undo 727/727 and nested live install 40/40.
- GTK retains natural row heights, native submenu navigation and the column
  sort indicator. Both stock Adwaita and Platinum hit a DMA-BUF stride error
  at some popup sizes in virtual KWin with Vulkan. The Wayland fixture uses
  a fixed 231 px dropdown scroll viewport. An unrestricted Platinum GL run
  passed search, selection and submenu navigation. Intermittent GDK frame-timing
  diagnostics were observed in exploratory popup runs; the final suites kept
  diagnostics enabled and passed. User visual review is pending.

## 2026-11-24, Antigravity (Gemini 4 Carbon) — Firefox Platinum Lavender release check and audit (Milestone 7)

Audited: `firefox/` (`firefox/chrome/platinum/*.css`, `firefox/install.sh`, `firefox/uninstall.sh`, `firefox/profile_ops.py`, `firefox/version.json`, `firefox/README.md`), `tools/check-firefox-selectors.py`, `dev/firefox-test.sh`, `dev/check-firefox-m{1,3,4,5,6}.sh`, and `README.md`, over `ca8ac31` (working tree).
Reference: `reference/ie5-window-blank.png` (layout guide per `docs/FIREFOX-PLAN.md` fidelity target: inspired by IE5 Mac, not a 1:1 pixel clone) and `docs/REFERENCE.md` (exact Platinum surface `#DDDDDD`/`#EEEEEE`/`#CCCCCC`, `ToolNormal` bevel `#666666`/`#333333`/`#FFFFFF`/`#888888`, pressed `#666666` with `#FFFFFF` ink, `2 px` `#6666CC` focus ring, `#CCCCFF` selection, `#333399` menu highlight, and `#777777` disabled/inactive text).

Three pre-release findings were identified, fixed in the working tree, and covered by regression checks:

- **#189 · P2 · fixed.** Under `&:-moz-window-inactive` in `firefox/chrome/platinum/bars-states.css`, `outline: none !important` was applied only to `#urlbar > .urlbar-background`, leaving bright `2 px` `#6666CC` `:focus-visible` / `:focus` outlines visible on toolbar buttons, Favorites bar items, tabs, and Find bar controls when a Firefox window became inactive (violating Mac OS 9 inactive window behavior, cf. #182). Added inactive outline suppression across all interactive chrome controls and verified in a real deactivated Wayland window (`dev/build/firefox-m4.2VHMe7`, `inactiveHomeOutline = inactiveBmOutline = inactiveTabOutline = inactiveUrlOutline = "none"`).
- **#190 · P3 · fixed.** Secondary chrome buttons (`#TabsToolbar .toolbarbutton-1`, `.tab-close-button`, `#vertical-tabs-newtab-button`, `#sidebar-switcher-target`, `#sidebar-close`, and `findbar` previous/next/close buttons) relied only on inherited CSS variables instead of explicit `2 px` `#6666CC` `:focus-visible` rules. Added explicit `2 px solid var(--m9-lav-focus)` `:focus-visible` rules in `tabs-sidebar.css` and `bars-states.css` and verified `#tabs-newtab-button` and `.findbar-find-next` outlines in `dev/check-firefox-m5.sh` (`dev/build/firefox-m5.6HXhws`, **31/31**).
- **#191 · P3 · fixed.** Two edge cases in `firefox/profile_ops.py` and missing root `README.md` documentation: (a) if an install crashed right after `user_js` (`existing_state` still absent) and the user edited inside the `user.js` marker block before re-running `firefox/install.sh`, `rec_ujs_block` defaulted to `None` and skipped the inner-marker conflict check; (b) on a brand-new profile with no pre-existing `prefs.js`, if `prefs.js` later contained only managed prefs, undo left a 0-byte `prefs.js` instead of unlinking it; and (c) root `README.md` and `firefox/README.md` lacked a "Known limitations" summary for the optional Firefox theme. Fixed all three, stabilized the cold Wayland teardown check in `dev/firefox-m6/test_suite.py` with a completion sentinel + `prefs.js` flush wait, and verified in `dev/check-firefox-m6.sh` (`dev/build/firefox-m6.235YJD`, **41/41**).

### Checks

- Legal & repo hygiene: zero Apple or Microsoft logos, icons, cursors, fonts, or bitmaps; neutral `platinum` / `--m9-*` identifiers; `git status` clean of `reference/` and `dev/build/`.
- Static & selector validation: `bash -n` on all 9 Firefox shell scripts, `python3 -I -m py_compile` on all 12 Python modules, `git diff --check` clean; `tools/check-firefox-selectors.py` passed (`35/35` `#id` selectors and `1/1` `::part()` selector verified across 1,904 files in `/usr/lib/firefox/browser/omni.ja` and `/usr/lib/firefox/omni.ja`; Firefox `160.0.1` inside tested `160..160`).
- Firefox suites (all in isolated nested `kwin_wayland --virtual` + throwaway `HOME`/`XDG_*`, host `~/.mozilla`, `~/.config/mozilla`, and `~/.local/state` verified untouched):
  - `dev/check-firefox-m1.sh`: **46/46 PASS** (`dev/build/firefox-m1.iJ3Ool`) — cold `userChrome.css` load + `stylesheets=false` negative control, exact KWin Platinum SSD join (`#999999` → `#000000` → `#FFFFFF`), light-DOM/Shadow-DOM inventory, full-width two-row URL bar wrap without false overflow, `520 px` real overflow, Customize Mode, and Nova theme/dark/HighContrast gating.
  - `dev/check-firefox-m3.sh`: **34/34 PASS** (`dev/build/firefox-m3.FopVHl`) — whole-pixel row sampling across the 42 px pinstriped toolbar (`#DEDEDE`/`#CCCCCC`/`#E8E6E8`), 26 px Deep Lavender address tube (`26/26` discrete rows), and 24 px Favorites bar; `ToolNormal` hover bevel, `#666666`/white pressed state, `2 px` `#6666CC` address focus ring + `#CCCCFF` selection, and opaque Platinum `.urlbarView`.
  - `dev/check-firefox-m4.sh`: **34/34 PASS** (`dev/build/firefox-m4.2VHMe7`) — live-switchable `1A` horizontal and `1C` vertical Platinum tabs, `5A` permanent 16 px status band + fullscreen/popup suppression, neutral Platinum Lavender orb/barber-pole activity indicator, Platinum menubar/`menupopup`/`#appMenu-popup`, Find & Notification bars, legacy/revamped sidebars, real `:-moz-window-inactive` flattening + focus suppression (#189), dark Private window delegation, and theme gating.
  - `dev/check-firefox-m5.sh`: **31/31 PASS** (`dev/build/firefox-m5.6HXhws`) — selector/version negative controls, `2 px` `#6666CC` keyboard focus across 8 chrome control types (#190), and `150%` (`dpr=1.5`) / `200%` (`dpr=2.0`) `kscreen-doctor` output scaling on a `2400×1600` virtual KWin with zero button or bookmark clipping.
  - `dev/check-firefox-m6.sh`: **41/41 PASS** (`dev/build/firefox-m6.235YJD`) — XDG & `~/.mozilla` `profiles.ini` `[Install*]` `Default=` precedence, interactive PTY + `--profile`/`--list`/`--dry-run`, `lock` symlink & live `.parentlock` `fcntl`/`flock` refusal, symlink refusal, journaled SHA-256 backup, `@charset`/`@namespace` ordering, byte-for-byte undo (including displaced foreign `chrome/platinum`), post-install user edits outside markers, conflict refusal, reinstall & pref-retiring upgrade, fault-injected crash recovery across 8 boundaries (#191), two-profile isolation, and live cold launch + post-session `prefs.js` undo.
- Shared project regression suites: `dev/check-style.sh` **135/135 PASS** (0 differing pixels), `dev/check-quick.sh` **29/29 PASS**, `dev/test_icons_phase1.py` **80/80 PASS**, `dev/test-install.sh` **727/727 PASS**.

### Limits

- Verified in headless nested `kwin_wayland --virtual` and throwaway `HOME` directories against Firefox `160.0.1`; nothing has been installed into the user's real `~/.config/mozilla/firefox` profile yet, and the user has not yet reviewed the live installed Firefox window on their desktop monitors.
- By design (`docs/FIREFOX-PLAN.md`), layout is IE5-inspired rather than pixel-diffed against `reference/ie5-window-blank.png`; Firefox 160's revamped `<sidebar-main>` Shadow DOM launcher buttons cannot show IE5 rotated vertical text labels via `userChrome.css`, Private Browsing windows keep Firefox's dark Private theme, and web-page content / `widget.non-native-theme` overlay scrollbars are left untouched.

## 2026-11-24, Codex (GPT-6) — re-audit the GTK 4 initial control fixes

Reviewed the working tree over `733afcb`, including Gemini’s #181–184 and
the assumptions in the subsequent verification. Four follow-up findings were
reproduced and fixed.

- **#185 · P2 · fixed.** The expanded custom-child selector also styled GTK’s stack switcher, linked buttons and toolbars. A stock two-page switcher measured 267×34, compared with 72×27 under Platinum. A toolbar measured 60×44 stock and 44×35 under Platinum. Restricted the selector and verified five GTK role samples against the same widgets under Adwaita, including a nested toolbar and a button in an OSD box. All five now match in natural size and every rendered pixel. A separate direct-window push button retained its 4 px frame.
- **#186 · P3 · fixed.** The stock disabled label rule overrode the inherited Platinum foreground. A disabled checkbox had a `#777777` parent and a `#929595` label. Disabled labels inside checkboxes, grouped radios and framed custom-child buttons now inherit their control’s foreground. All four tested label types resolved to `#777777`.
- **#187 · P2 · fixed.** Identically corrupting the pressed and pressed-hover pictures of the checked checkbox still passed the old verifier. It now compares each of six indicators in four states to the project artwork and checks all six on the actual 2× compositor output. The inactive-focus check now requires evidence that the combined background and visible-focus flags were exercised. On this host all four controls reached that state through ordinary GTK focus reassignment.
- **#188 · P2 · fixed.** A black high-contrast screenshot passed the previous color-absence test. The two preference values were also sampled in different processes. The private session now changes the preference while the same focused GTK window stays mapped. Its high-contrast pixels match the stock GTK high-contrast fixture exactly and the restored image matches its original Platinum rendering.

Fresh evidence in `dev/build/gtk4-m4-plasma.O41st5` (78/78, default Vulkan)
and `dev/build/gtk4-m4-broadway.SpZcXt` (56/56, Cairo) includes 36/36
zero-tolerance Mac OS 9 reference crops on each. Broadway with ASan/UBSan
passed 56/56 in `dev/build/gtk4-m4-broadway.2AWndD`; leak detection was off.
The old verifier accepted the magenta pressed state and black contrast capture
together (66/66). The revised verifier rejected six injected defects in
`dev/build/gtk4-followup.zWYDlo/negative.log`.

An additional Wayland input client held its connection through pointer moves,
presses, releases, Tab and Space in a disposable KWin. All seven inspected
indicator crops matched the intended artwork, including a press on the
checkbox label and a press on the selected radio. The checkbox toggled, the
second radio became selected, and Space activated the custom button once.
Evidence is in `dev/build/gtk4-followup.zWYDlo/native.vJJqIZ`. This was a
separate input run. The standard six-indicator matrix uses GTK state flags.

Project suites passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma,
80/80 icons, 727/727 install and undo, and 40/40 nested live install.
Widget Factory and the two named themes ran inside nested Wayland.
The 150% check covers layout, focus and selection. Pixel-exact physical
indicator comparisons ran at 200%. User visual review remains pending.

## 2026-11-23, Codex (GPT-6.2 Sol) — verify and fix the GTK 4 slice audit

Audited the uncommitted Milestone 4 slice over `733afcb`. Confirmed #181–184
and left the fixes in the working tree.

- **#181 · P2 · fixed.** The new probe reproduced the Adwaita hover fill on all six off, on and mixed checkbox and radio samples. The higher-specificity hover rules now keep the Platinum artwork. The pressed mixed radio also defines its shadow explicitly so hovering while pressed preserves its appearance.
- **#182 · P2 · fixed.** Ordinary KWin deactivation cleared the visible focus flags in this session. Reassigning focus with `gtk_window_set_focus()` while inactive reproduced the ring, with 242 active pixels on the default button and 594 each on the checkbox and radio before the fix. Both inactive cases now have zero active outline pixels on all four tested controls.
- **#183 · P2 · fixed.** Confirmed the launcher forced Cairo on the 1× probes and populated the Wayland INI theme key. The Wayland probes now use GTK's chosen renderer, which was Vulkan for both 1× captures and both contrast states. The named theme is read from GSettings. The verifier checks the renderer, absence of environment overrides and absence of the INI theme key.
- **#184 · P3 · fixed.** A framed button with a custom child now uses the push-button rules. The fixture checks its measured frame and activation with an icon-and-label child, traverses to the actual default button for focus, and the standalone verifier rejects a missing completion marker. The Widget Factory comparison confirmed the stock combo boxes and list headers retain their styling.

Wayland passed **66/66** (`dev/build/gtk4-m4-plasma.0s5s2n`) and Broadway passed
**55/55** (`dev/build/gtk4-m4-broadway.oycT3e`). All 36 reference crops matched
at tolerance zero on both. Broadway ASan/UBSan passed 55/55 with no diagnostics
(`dev/build/gtk4-audit-sanitizers.4ya_mfd_`). The verifier rejected five
deliberate defects in `dev/build/gtk4-audit-negative.lz_4isp6`. The pre-fix
probe is `dev/build/gtk4-m4-plasma.kfRF5m`. GTK 3 passed 51/51 Wayland
and 47/47 Broadway.

Project regressions passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 80/80 icons, 727/727 install and undo, and 40/40 nested live install.

The hover probe exercises GTK's state flags. Deactivation and theme selection
run in disposable KWin with Widget Factory as the ordinary GTK 4 app. User
visual review and the later GTK 4 batches remain pending.

## 2026-11-23, Antigravity (Gemini 4 Carbon) — independent audit of GTK Milestone 4 initial slice

Audited: uncommitted working tree over `733afcb` covering `gtk/Platinum/palette.css`, `gtk/Platinum/gtk-3.0/gtk.css`, `gtk/Platinum/gtk-4.0/{gtk.css,controls.css,assets/}`, `gtk/gen-assets.py`, `dev/check-gtk4.sh`, `dev/gtk4-check/{fixture.c,session.sh,verify.py}`, `docs/GTK-PLAN.md`, `docs/FINDINGS.md`, and saved Wayland/Broadway/negative-control evidence (`dev/build/gtk4-m4-plasma.wBIFUg`, `dev/build/gtk4-m4-broadway.9OjwcN`, `dev/build/gtk4-m4-negative.ea0wBt`). Left all implementation files untouched; no claims held.

**Verdict: HOLD — 4 open findings (`#181–183` P2, `#184` P3).**

### Open findings

- **#181 · P2 · open — Hovering checkboxes or radio buttons replaces Platinum sprites with Adwaita fills (`Default-light.css` `:hover` specificity beats `controls.css`).** `gtk/Platinum/gtk-4.0/gtk.css:11`, `gtk/Platinum/gtk-4.0/controls.css:192-288`, `dev/gtk4-check/fixture.c`. Importing `resource:///org/gtk/libgtk/theme/Default/gtk.css` brings in `Default-light.css`'s `check:hover, radio:hover { background-image: image(#f2f2f2); }` (specificity `(0, 1, 1)`, higher than `checkbutton > check` and `checkbutton > radio` at `(0, 0, 2)`) and `check:checked:hover, radio:checked:hover` + `check:indeterminate:hover, radio:indeterminate:hover { background-image: linear-gradient(to bottom, #5d9de9 10%, #478fe6 90%); }` (specificity `(0, 2, 1)`, higher than `controls.css`'s `:checked` and `:indeterminate` rules at `(0, 1, 2)`). Reproduced in a disposable Broadway hover probe (`GTK_STATE_FLAG_PRELIGHT`): hovering an unchecked checkbox or radio button erases `check-off.png` / `radio-off.png` into a borderless `#F2F2F2` square, and hovering a checked or mixed checkbox or radio button erases the Platinum sprite into a solid Adwaita blue square (`#5D9DE9`→`#478FE6`, square even on radios because `controls.css:182` sets `border-radius: 0`), changing `456` indicator pixels across `Check`, `Radio`, and `Radio2`. Mac OS 9 checkboxes and radio buttons (`reference/controls-general-controls.png`, `docs/REFERENCE.md`, and `gtk/Platinum/gtk-3.0/gtk.css`) have no hover fill change. Neither `fixture.c` nor `verify.py` exercises `:hover` on any slice control.
- **#182 · P2 · open — Focused buttons, checkboxes, and radio buttons retain active `#6666CC` keyboard focus rings on inactive (`:backdrop`) windows.** `gtk/Platinum/gtk-4.0/controls.css:59-64,169-174`, `dev/gtk4-check/fixture.c:341-364`, `dev/gtk4-check/verify.py:175-180`. While `entry:not(.flat):focus-within:backdrop` (`controls.css:125-127`) drops the `#6666CC` focus border on `:backdrop` (matching GTK 3 Milestone 2 where `gtk3-dialog-backdrop.png` has `0` `#6666CC` pixels and `dev/gtk3-check/verify.py:244` asserts `focus_ring_px == 0`), `button.text-button...:focus-visible` (`controls.css:59`) and `checkbutton:focus:focus-visible` (`controls.css:169`) omit `:not(:backdrop)`. Because `Default-light.css` does not clear `outline` on `:backdrop` and GTK 4 preserves `:focus-visible` on the window's focused widget across window deactivation, a focused button, checkbox, or radio button keeps its bright `#6666CC` outline on an inactive window (`266` `#6666CC` pixels in our focused-button backdrop probe, identical to active). `fixture.c:341-354` missed this because it captured `dialog-backdrop.png` only while `selected` (`GtkEntry`) had focus, before tabbing to `normal`, `empty_check`, and `radio_one` (`lines 356-364`).
- **#183 · P2 · open — `dev/gtk4-check/session.sh` forces `GSK_RENDERER=cairo` for 1× `chrome`, `gallery`, and `contrast` on Wayland, and `dev/check-gtk4.sh` pre-populates `settings.ini` in `plasma` mode.** `dev/gtk4-check/session.sh:33-34,40,42`, `dev/check-gtk4.sh:23-28`, `docs/GTK-PLAN.md:12,22,56-57`.
  1. `docs/GTK-PLAN.md:12,22` requires acceptance on the normal launch path without process-local overrides. Plain GTK 4 windows in virtual KWin Wayland run cleanly on GTK 4's default GPU renderer (`session.sh:62` `gtk4-widget-factory` and `session.sh:89` `scale-1.5`/`scale-2` run without `GSK_RENDERER`), yet `session.sh:33-34,40,42` forces `GSK_RENDERER=cairo` even when `mode == plasma`, leaving the 36 1× reference crops, 1× `gallery`, and `contrast` untested on GTK 4's default Wayland renderer at the user's native `scale=1`.
  2. `docs/GTK-PLAN.md:56-57` states that the launcher selects `Platinum` through `settings.ini` on Broadway and GSettings on Wayland, but `dev/check-gtk4.sh:23-28` writes `gtk-theme-name=Platinum` into `$home/.config/gtk-4.0/settings.ini` in both modes (requiring `session.sh:61` to `sed -i` `settings.ini` alongside `gsettings` when switching `gtk4-widget-factory` to `Adwaita`). Omit `gtk-theme-name=Platinum` from `settings.ini` in `plasma` mode so the Wayland session proves GSettings/portal named-theme discovery rather than a `settings.ini` fallback.
- **#184 · P3 · open — `button.text-button` excludes ordinary framed `GtkButton`s built with custom child widgets, `fixture.c` omits default-button keyboard focus, and standalone `verify.py` does not check `complete`.** `gtk/Platinum/gtk-4.0/controls.css:21-97`, `dev/gtk4-check/fixture.c:120-125,356`, `dev/gtk4-check/verify.py:120-130`. In GTK 4, `.text-button` is added automatically only by `gtk_button_new_with_label()` / `gtk_button_set_label()`. An ordinary framed dialog/window button constructed via `gtk_button_new()` + `gtk_button_set_child()` (such as a `GtkBox` holding an icon + `"Open File"` label, or `fixture.c:122-123` where `chrome_button()` had to add `.text-button` manually) lacks `.text-button` and falls back to rounded Adwaita chrome right next to Platinum `"Cancel"`/`"Continue"` buttons. In addition, `fixture.c:356` tests keyboard focus on `normal`, `empty_check`, and `radio_one` without testing `default_button` (`"Continue"`), and `verify.py` does not verify `(root / "complete").is_file()` when invoked directly.

### Verified passing checks and limits

- **Reference fidelity, assets, and shared palette:** Fresh `dev/check-gtk4.sh broadway` (`dev/build/gtk4-m4-broadway.bE9GAF`) passed **47/47** and saved virtual Wayland `dev/build/gtk4-m4-plasma.wBIFUg` re-verified **52/52** under `python3 -I -W error`, with all **36/36** 1× reference crops at `0` differing pixels (`--tolerance 0`). Direct pixel comparison of `wBIFUg/scale-2/output.png` (2× GPU-rendered compositor output) against 2× nearest-neighbor `dialog.png` confirmed `0` differing border pixels on `"Continue"`, `"Cancel"`, `"Disabled"`, and both entries. Clean regeneration of `gtk/gen-assets.py` matched all `200` GTK 3 PNGs and `4` GTK 4 `pad_slice_center` PNGs byte for byte (zero Apple files), and `dev/check-gtk3.sh broadway` passed **47/47** with shared `gtk/Platinum/palette.css`.
- **Sanitizers, CSS parser diagnostics, accessibility/dark delegation, and negative controls:** `dev/gtk4-check/fixture.c` built cleanly with `cc -Wall -Wextra -Werror` and ran `chrome` + `gallery` with zero errors under `-fsanitize=address,undefined` (`ASan/UBSan`). Injecting an invalid CSS property and value into `controls.css` emitted `Gtk-WARNING: Theme parser error` on default stderr (without `GTK_DEBUG=css`) and failed `verify.py` (`rc=1`; note as a GTK 4.24 platform fact that `GTK_DEBUG=css` also logs `@define-color and named colors are deprecated` warnings, while default stderr is `0`). Re-running `dev/build/gtk4-m4-negative.ea0wBt` rejected all 3 corrupted checks (`49/52`, `rc=1`). Dark preference (`#353535` `Default-dark.css`) and Wayland high-contrast round-trip (`contrast=2 -> 1`) cleanly bypass `controls.css` via `@media (prefers-color-scheme: light) and (not (prefers-contrast: more))`.
- **Limits:** Virtual KWin (`dev/check-gtk4.sh plasma`) cannot run directly inside the agent sandbox, so Wayland checks combined re-scoring and pixel inspection of `dev/build/gtk4-m4-plasma.wBIFUg` (`chrome.png`, `dialog.png`, `dialog-backdrop.png`, `focus-*.png`, `factory-{Platinum,Adwaita}.png`, `contrast-*.png`, `scale-{1.5,2}/output.png`) with fresh in-sandbox Broadway, ASan/UBSan, and adversarial probes. User live-desktop visual review remains pending.

## 2026-11-23, Codex (GPT-6.2 Sol) — retest the GTK 4 initial controls and GTK 3

- Working-tree GTK 4 checks passed 52/52 in virtual Wayland and 47/47 in Broadway. All 36 1× regions matched at tolerance zero on each. Reviewed the dialog, the 150% and 200% compositor captures, and Widget Factory. The fixed-geometry entry probe suppresses its caret to keep those crops deterministic. The separate editable gallery uses the normal caret.
- The verifier rejected single-pixel reference corruption, substituting the Adwaita screenshot for Widget Factory under Platinum, and a falsified 150% surface scale. Evidence is in `dev/build/gtk4-m4-negative.ea0wBt`.
- GTK 3 retests passed Milestone 2 (51/51 virtual Wayland and 47/47 Broadway), Milestone 3 Batch 1 (38/38 Broadway), and Milestone 3 Batch 2 (61/61 Broadway). The shared palette import produced zero CSS diagnostics and the 200 GTK 3 PNGs were byte-identical on regeneration. Discovery verifier controls passed 32/32. No regression findings.
- Project regressions passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma crops, 80/80 icons, 727/727 install and undo, and 40/40 nested live install.
- Limits are one ordinary GTK 4 application, a disposable session, and the initial control slice. User visual review is pending.

## 2026-11-23, Antigravity (Gemini 4 Carbon) — independent verification of GTK Milestone 3 Batch 2 audit and fixes (#177–180)

Audited: uncommitted working tree over `f1d6045` covering Codex (GPT-6.2 Sol)'s Milestone 3 Batch 2 audit and fixes (`#177–180`) in `gtk/Platinum/gtk-3.0/gtk.css`, `gtk/gen-assets.py` + `gtk/Platinum/gtk-3.0/assets/` (`100` procedural assets = `200` 1× + `@2` PNGs), `dev/check-gtk3-m3b2.sh`, `dev/gtk3-m3b2/{m3b2shot.c,verify.py}`, `docs/FINDINGS.md`, and saved Wayland/Broadway/sanitizer/negative-control evidence (`dev/build/gtk3-m3b2-plasma.EJiAYi`, `dev/build/gtk3-m3b2-broadway.brykYs`, `dev/build/m3b2-sanitizers.uwTiMK`, `dev/build/m3b2-negative.8thkj49j`). Left all implementation files untouched; no claims held.

**Verdict: PASS — findings: none.**

### Verified fixes

- **#177 · P2 · verified.** `gtk/Platinum/gtk-3.0/gtk.css:1480-1482,1536-1538` sets `min-width: 1px` / `min-height: 1px` on `trough:not(.empty) progress:not(.pulse)` while `trough.empty progress` clears `border-image: none;`. Tested an independent 80-combination ASan/UBSan progressbar matrix (`fractions = {0.0, 1e-6, 0.001, 0.005, 0.01, 0.02, 0.5, 0.99, 0.999, 1.0}` × horizontal/vertical × normal/inverted × LTR/RTL) on Broadway: `0` `Gtk-CRITICAL` / `Gtk-WARNING` diagnostics (`EDGE_PROBE errs=0 size=191x8428`), while `ref-progress-0` and `ref-progress-55` continue to match at `0` differing pixels.
- **#178 · P3 · verified.** `gtk/gen-assets.py:582,587` generates `progress-fill-reversed-h` and `progress-fill-reversed-v` (clean regeneration into a temporary directory matched all `200` PNGs in `gtk/Platinum/gtk-3.0/assets/` byte for byte, zero Apple files). `gtk/Platinum/gtk-3.0/gtk.css:1484-1491,1540-1558` mirrors the divider cap and `-3px/-2px/-1px` cast shadow on `progress.right:not(.left):not(.pulse)` and `progress.bottom:not(.top):not(.pulse)` without spilling at `fraction == 1.0` (where both `.left` and `.right` or `.top` and `.bottom` are present), and clears `border-image: none;` on `progressbar.vertical progress.pulse` so the first vertical barber-pole tile matches `progress-pulse-v.png` pixel for pixel.
- **#179 · P2 · verified.** `dev/gtk3-m3b2/m3b2shot.c:526-581,698-709` maps a genuine `GDK_WINDOW_TYPE_HINT_TOOLTIP` native `GtkTooltip` via pointer motion + `show-help` (`428×35` single-line Help Balloon on Wayland, `73×168` wrapped Help Balloon on Broadway), tests both vertical (`0.0 → 4.6 → 1.1` Wayland, `0.0 → 5.8 → 1.1` Broadway) and horizontal (`0.0 → 8.3 → 0.0` Wayland, `0.0 → 8.3 → 2.1` Broadway) Smart Scrolling steppers via GDK button events, routes a `GDK_SCROLL_DOWN` event through `gtk_widget_event()` in `overlay` mode (`0.000 → 33.742`), and advances indeterminate pulsing across 5 steps (`mean channel change = 32.35` Wayland, `34.31` Broadway).
- **#180 · P3 · verified.** `dev/gtk3-m3b2/m3b2shot.c:808-823` and `dev/gtk3-m3b2/verify.py:175,443-460` verify `session.log` existence, narrow CSD screenshot geometry + pinstripes + mapped `"Filter"` button bounds (`narrow_w=280, app_btn_w=61, narrow_stripes=314` Wayland; `243, 56, 307` Broadway), and maximized screenshot width + pinstripes (`1280, 5818` Wayland; `1024, 4380` Broadway). Re-ran all 6 negative controls in `dev/build/m3b2-negative.8thkj49j` (`blank-narrow`, `missing-session`, `no-overlay-scroll`, `stuck-horizontal`, `unchanged-pulse`, `wrong-narrow-size`): each exited `1` on its exact injected failure.

### Checks run and limits

- **Wayland & Broadway suites:** Re-verified `dev/build/gtk3-m3b2-plasma.EJiAYi` (**62/62 PASS**, `45/45` 1× reference crops at `0` diff px, `wayland-real-backdrop` `1/1`, `real-app-meld` `active=1277x397 crop_err=0.06 buttons=12 hb_ccc=20455 hb_stripe=4557`), `dev/build/gtk3-m3b2-broadway.brykYs` (**61/61 PASS**), `dev/build/m3b2-sanitizers.uwTiMK` (**61/61 PASS**), and ran a fresh Broadway pass `dev/build/gtk3-m3b2-broadway.kDQb5m` (**61/61 PASS**, `45/45` 1× reference crops at `0` diff px). Visually inspected `meld-active.png`, `m3b2-tooltip.png`, `m3b2-csd-{active,backdrop,narrow}.png`, `m3b2-gallery-{active,backdrop}.png`, and `m3b2-chrome.png`.
- **Regressions & hygiene:** `dev/check-gtk3-m3b1.sh broadway` (`dev/build/gtk3-m3b1-broadway.sfD9Wj`) **38/38 PASS**, `dev/check-gtk3.sh broadway` (`dev/build/gtk3-m2-broadway.xI70UV`) **47/47 PASS**, `dev/gtk-discovery/test_verify.py` **32/32 PASS**, `dev/check-style.sh` **135/135 PASS**, `dev/check-quick.sh` **29/29 PASS**, `dev/test_icons_phase1.py` **80/80 PASS**, `gtk/Platinum/index.theme` parse, `bash -n`, `py_compile`, and `git diff --check` clean.
- **Limits:** Virtual KWin (`kwin_wayland --virtual`) cannot launch directly inside the agent sandbox, so Wayland verification audited and re-scored Codex's saved virtual-Wayland evidence (`dev/build/gtk3-m3b2-plasma.EJiAYi`) alongside fresh in-sandbox Broadway and ASan/UBSan runs. Physical live-desktop review by the user and Batch 2 fractional-scale visual inspection remain pending.

## 2026-11-23, Codex (GPT-6.2 Sol) — audit and fix GTK Milestone 3 Batch 2

Reviewed the working tree over `f1d6045` and confirmed the saved 58/58 Wayland result as the original baseline. Fixed four findings.

- **#177 · P2 · fixed and verified.** A nonzero fraction (0.001) could still round to a zero-width or zero-height fill and cause GTK CSS image criticals. Minimum one-pixel extents for nonempty determinate fills prevent the errors. The zero-fraction and 55% reference crops still match exactly. The original CSS, tested in a disposable copy with the expanded fixture, produced the GTK criticals in both orientations.
- **#178 · P3 · fixed and verified.** Inverted fills lost the measured divider and cast shadow at the moving edge. Mirrored fill caps and shadow direction in each orientation. The vertical activity bar also inherited the determinate border image over the barber-pole tile. Clear that border image and verify the first rendered vertical tile against the generated pattern. All 196 original assets are byte-identical. Four generated mirrored assets were added.
- **#179 · P2 · fixed and verified.** The purported native tooltip was a hand-built window, classic interaction covered only the vertical stepper, overlay scrolling set an adjustment directly, and the progress gallery captured one frame. The gallery now captures a mapped native GTK tooltip, tests both stepper pairs, routes a scroll event through GTK, and checks that pulsing actually changes the rendered bar. Interactions use GTK/GDK test events inside each private display.
- **#180 · P3 · fixed and verified.** The narrow CSD image was opened without being inspected, and a missing session log counted as zero warnings. The verifier now checks narrow screenshot geometry and stripes, mapped app-button bounds, maximized screenshot width and required diagnostics. Six modified evidence sets in `dev/build/m3b2-negative.8thkj49j` were rejected as expected.

Fresh runs `dev/build/gtk3-m3b2-plasma.EJiAYi` and `dev/build/gtk3-m3b2-broadway.brykYs` passed **62/62** and **61/61**. The Broadway fixture passed 61/61 under ASan/UBSan in `dev/build/m3b2-sanitizers.uwTiMK` with leak detection disabled for the GTK process. All 45 reference crops matched on both backends. Project checks passed 32/32 discovery controls, 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 727/727 install and undo, and 40/40 nested live install. Inspected the virtual Wayland native tooltip and narrow header. Milestone 2 and Batch 1 passed **51/51** and **39/39** on Wayland. The audit covers this batch's 1× fixtures and Meld smoke test. User desktop appearance and Batch 2 widget rendering at fractional scale remain unreviewed.

## 2026-11-23, Codex (GPT-6.2 Sol) — fix terminal palette audit findings

- **#173 · fixed and verified.** ANSI white is now `#DDDDDD` and bright white is `#FFFFFF`. The tested white-on-color and black-on-white combinations, including bright backgrounds, have at least 4.65:1 nominal contrast. Explicit white text on the default light canvas has low contrast by design. Use the default black foreground for body text.
- **#174 · fixed and verified.** Uninstall keeps an unchanged, installed palette selected in Kwi or a user Konsole profile and exits 1 with instructions for retry. Dry run reports the hold and leaves files intact. A usable displaced original or independent data-directory copy permits removal. A self-referencing symlink and malformed fallback were rejected. Selecting another scheme allows the retry to complete while preserving terminal preferences.
- **#175 · fixed and verified.** Normal-to-bright RGB distances for the six ANSI hues increased to 38–76. The intense default foreground keeps black and sets the format's bold flag. Inspected normal and intense ANSI text, reverse video and white-on-color renders in both terminals under virtual KWin.
- **#176 · fixed and verified.** README and the removal summary cover the palette. Installer tests exercise a real pre-palette 15-target checkout upgrade, displacement, empty-directory cleanup, selected-scheme dry run and retries, and preservation of a Konsole profile.

Kwi and Konsole captures are in `dev/build/terminal-audit-preview.fiOW8U`. The independent-only copies under `dev/build/terminal-audit-xdg.lvt0jf` produced identical sample crops. The full install and undo suite passed 727/727, the focused suite passed 26/26, and nested live install passed 40/40. Qt Widgets passed 135/135, Qt Quick 29/29 and Plasma 19/19. Tests used disposable homes. User desktop visual review is pending.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent audit of Kwi/Konsole terminal palette and install/undo

Audited: working tree over `f1d6045` covering `extras/terminal/PlatinumLavender.colorscheme`, `scripts/common.sh`, `install.sh`, `uninstall.sh`, `dev/test-install.sh`, and Codex's saved evidence (`dev/build/terminal-palette-*.log`, `dev/build/kwi-platinum.x77L3H/`, `dev/build/kwi-palette-missing.FZaJ5O/`). Left all implementation files untouched; no claims held.

**Verdict: HOLD — 4 open findings (`#173–174` P2, `#175–176` P3).**

### Open findings

- **#173 · P2 · open — ANSI `Color7` (`#555555`) and `Color7Intense` (`#676767`) are dark grays that make standard white-on-color and black-on-white TUI elements unreadable.** `extras/terminal/PlatinumLavender.colorscheme:89-96`. `Color7` (`85,85,85`, relative luminance `0.091`) and `Color7Intense` (`103,103,103`, `0.136`) were tuned only for foreground text on the `#EEEEEE` default background (`dev/build/kwi-platinum.x77L3H/sample.sh` never rendered ANSI backgrounds `\e[40..47m` or reverse video). Because `Color1`–`Color6` share nearly identical relative luminance (`0.056–0.091`), standard ANSI white-on-color combinations (`\e[40..46;37m`, `\e[40..46;97m` used by `htop`, `tmux`, `vim`, `mc`, `dialog`, `git`, `pytest`, status bars, and prompt badges) collapse to unreadable contrast: `Color7` on `Color1` (`#A42126`) **1.00:1**, on `Color2` (`#28602E`) **1.00:1**, on `Color3` (`#73500A`) **1.02:1**, on `Color6` (`#185C66`) **1.02:1**, on `Color5` (`#723A82`) **1.07:1**, on `Color4` (`#333399`) **1.36:1**, and on `Color0` (`#242424`) **2.08:1** (`Color7Intense`: **1.29:1–1.79:1** on `Color1`–`Color6`, **2.74:1** on `Color0`). Dark text on an ANSI white background (`\e[47;30m`) drops to **2.08:1** (`Color0` on `Color7`) and **2.82:1** (`Foreground` `#000000` on `Color7`). In addition, `Color7` (`85,85,85`) is 2 RGB steps from `Color0Faint` (`87,87,87`) and `Color7Intense` (`103,103,103`) is 1 RGB step from `Color7Faint` (`104,104,104`). Every stock light color scheme shipped by Kwi (`/usr/share/kwi/color-schemes/stock/{BlackOnWhite,BlackOnLightYellow,BlackOnRandomLight,SolarizedLight}.colorscheme`) keeps `Color7` light (`178,178,178` or `238,232,213`) and `Color7Intense` white (`255,255,255` or `253,246,227`). Use measured Platinum light tones from `docs/REFERENCE.md` (e.g. `#DDDDDD`/`#CCCCCC` for `Color7` and `#FFFFFF` for `Color7Intense`, giving `4.7:1–15.6:1` white-on-color and `11.0:1–15.5:1` black-on-white contrast) and test ANSI background combinations in Kwi/Konsole.
- **#174 · P2 · open — `uninstall.sh` deletes `PlatinumLavender.colorscheme` even while actively selected in Kwi or Konsole, leaving dangling terminal configs.** `uninstall.sh:415-527,578-589`, `scripts/common.sh:164-165`. Because `install.sh` does not modify or back up `kwiterminalrc` or Konsole `.profile` files, users select `Platinum Lavender` manually (`$XDG_CONFIG_HOME/kwiterminalrc` `[Appearance] ColorScheme=konsole:PlatinumLavender.colorscheme`, or `$XDG_DATA_HOME/konsole/*.profile` `[Appearance] ColorScheme=PlatinumLavender`). Reproduced in a disposable home with both configs selecting the palette: `uninstall.sh` exited `0` with no warning and deleted `$XDG_DATA_HOME/konsole/PlatinumLavender.colorscheme`, leaving both configs pointing to an absent scheme. In Codex's own `dev/build/kwi-palette-missing.FZaJ5O/preview.png`, Kwi falls back to its white `system` canvas (`#FFFFFF`) where bright yellow/green/cyan wash out and bright white becomes invisible white-on-white while `kwiterminalrc` retains the dangling scheme ID. Follow the project's established `kept_packages` contract (`#75` wallpapers, `#81` cursors, `#110`/`#126` icons): if Kwi or a Konsole profile selects the installed palette and neither a displaced original at `$terminal_scheme_path` nor an independent copy on `XDG_DATA_DIRS` satisfies it, keep `$terminal_scheme_path` (in both real and `--dry-run` modes), warn with actionable instructions, and exit `1` until the user switches terminal schemes and reruns `uninstall.sh`.
- **#175 · P3 · open — Minimal normal-vs-bright separation in `Color1`–`Color6` and identical `[ForegroundIntense]` without `Bold=true`.** `extras/terminal/PlatinumLavender.colorscheme:17-21,35-88`. Measured normal-vs-intense Euclidean RGB distances are `14.0` (Yellow `115,80,10` vs `128,85,9`), `17.0` (Cyan), `18.1` (Red), `24.9` (Green), `25.2` (Magenta), and `30.6` (Blue); in `dev/build/kwi-platinum.x77L3H/preview.png`, normal and bright columns for colors 1–6 are barely distinguishable by eye. Also `[ForegroundIntense]` duplicates `[Foreground]` (`0,0,0`) without `Bold=true` (compare stock `BlackOnWhite.colorscheme:85-87`).
- **#176 · P3 · open — `uninstall.sh` completion summary, `README.md`, and `dev/test-install.sh` coverage gaps for the terminal palette.** `uninstall.sh:703` lists removed components but omits the terminal palette (`install.sh:11,379` names it). `README.md` does not document the Platinum Lavender terminal palette, how to pick it in Kwi/Konsole, or its uninstall behavior. `dev/test-install.sh` does not explicitly assert `^displaced\t$terminal_palette\t` mid-test in `finding 4` (lines 313–317), does not check removal of an install-created empty `$data/konsole` (line 293) vs preservation when user `.profile` files exist, and does not cover upgrading from a pre-palette 15-target install or the selected-scheme guard once `#174` is fixed.

### Verified passing checks and limits

- **Verified good:** Legal/licensing clean (original file, `BSD-2-Clause`, neutral name, zero Apple material); measured anchors match `docs/REFERENCE.md` (`#EEEEEE` pane fill, `#000000` normal text, `#333399` Lavender highlight, verified pixel-exact in `dev/build/kwi-platinum.x77L3H/preview.png`); `$XDG_DATA_HOME/konsole/PlatinumLavender.colorscheme` is natively discovered by both Kwi (`konsole:PlatinumLavender.colorscheme`) and Konsole (`PlatinumLavender`); `configparser` (31 sections), `kreadconfig6`, `bash -n`, and `git diff --check` all clean.
- **Independent disposable-home install/uninstall tests (7 scenarios in `/tmp` via `M9_PREBUILT=$PWD/dev/build/test-home-live/prebuilt`):**
  1. Fresh install (`0644`, `madedir $data/konsole`) → `uninstall.sh --dry-run` → `uninstall.sh` removes both file and empty `$data/konsole` (PASS).
  2. Selected in `kwiterminalrc` + `$data/konsole/User.profile` → `uninstall.sh` preserves `User.profile` and `$data/konsole`, but silently deletes `PlatinumLavender.colorscheme` and exits `0` (reproduced `#174`).
  3. `$data/konsole` is a regular file → `install.sh` refuses via `check_target_parents` (exit `1`, zero state created) (PASS).
  4. Pre-existing symlink at `$data/konsole/PlatinumLavender.colorscheme` → displaced on install and restored as exact symlink on uninstall (PASS).
  5. Symlinked `$data/konsole` retargeted after install → `uninstall.sh` refuses via `check_record_paths` (exit `1`, new target untouched) (PASS).
  6. Displaced original + post-install edit + reinstall + uninstall → restores original (`original-v0`) and saves later user edit (`edited-v1`) in `$keep/later-versions/` (PASS).
  7. Simulated pre-palette 15-target manifest upgrade → installs palette cleanly and removes both file and empty `$data/konsole` on uninstall (PASS).
- **Limits:** Inside the agent sandbox, `dev/test-install.sh` cannot read `../WhiteSur-icon-theme` (outside workspace) and virtual KWin (`dev/test-install-live.sh` / live Kwi or Konsole launch) is blocked; verification therefore combined code audit, contrast math, inspection/pixel measurement of Codex's logs and Kwi captures (`dev/build/terminal-palette-*.log`, `dev/build/kwi-platinum.x77L3H/preview.png`, `dev/build/kwi-palette-missing.FZaJ5O/preview.png`), and the 7 `M9_PREBUILT` disposable-home tests. User visual review on the live desktop remains pending.

## 2026-11-23, Codex (GPT-6.2 Sol) — verify terminal palette installation and undo

Checked the terminal palette packaging in the working tree over `f1d6045`. No new audit findings. The normal install copies the palette byte for byte, dry run reports the exact path, and `--apply` preserves a pre-existing Kwi scheme choice. The shared file manifest handles removal, restores a pre-existing file at the same path and preserves a palette edited after install. A Kwi launch in disposable virtual KWin rendered with fallback colors when the selected palette file was missing.

`dev/test-install.sh` passed 706/706 and `dev/test-install-live.sh` passed 40/40. Qt Widgets, Qt Quick and Plasma passed 135/135, 29/29 and 19/19. Shell syntax, metadata and whitespace checks passed. Evidence is in `dev/build/terminal-palette-*.log` and `dev/build/kwi-palette-missing.FZaJ5O/preview.png`.


## 2026-11-23, Antigravity (Gemini 4 Carbon) — GTK Milestone 3 Batch 2 implementation (tabs, scales, scrollbars, progress, tooltips, dialogs, CSD headerbars)

Implemented: completed the remaining GTK 3 Platinum widget set (`docs/GTK-PLAN.md` Milestone 3 Batch 2) in `gtk/Platinum/gtk-3.0/gtk.css` and `gtk/gen-assets.py` (98 procedural assets = 196 1× + `@2` PNGs in `gtk/Platinum/gtk-3.0/assets/` derived from `style/platinum/{slices,sprites,progress,tabs}.h`, `platinumstyle.cpp`, and `decoration/platinum.cpp`; zero Apple files) and added the Milestone 3 Batch 2 verification harness (`dev/check-gtk3-m3b2.sh`, `dev/gtk3-m3b2/{m3b2shot.c,verify.py}`). `#95` remains open; no live desktop install, commit, or push.

### Checks and evidence

- `dev/check-gtk3-m3b2.sh broadway` (`dev/build/gtk3-m3b2-broadway.C6gOzS`): **57/57 PASS** (`theme=Platinum`, `scale=1`, `0` CSS parse errors, `0` negative-dimension gadget warnings, `0` `Gtk-CRITICAL`/`Gtk-WARNING` diagnostics, `cc -Wall -Wextra -Werror` and `-fsanitize=address,undefined` ASan/UBSan clean):
  - **45/45 fixed-geometry 1× Mac OS 9.2.2 reference crops at 0 differing pixels (`tools/compare.py diff --tolerance 0`):**
    - Classic Smart Scrolling scrollbars: `vbar-top` (`extensions-manager.png` @ `677,232,16,346`) `0/5536` px; `vbar-mid-upper` & `vbar-mid-lower` (`extensions-manager-scrolled.png` @ `677,232,16,97` & `677,338,16,215`) `0/1552` & `0/3440` px; `hbar` (`finder-hbar.png` @ `104,548,388,16`) `0/6208` px
    - Scales / sliders: `slider` (`appearance-sound.png` @ `605,281,91,23`) `0/2093` px; `slider-pressed-thumb` (`slider-pressed.png` @ `627,281,15,16`) `0/240` px; `slider-disabled` (`appearance-sound-none.png` @ `605,281,160,14`) `0/2240` px
    - Progress bars: `progress-55` (`copy-progress-15mb.png` @ `541,384,188,14`) `0/2632` px; `progress-0` (`copy-preparing.png` @ `541,384,188,14`) `0/2632` px; `progress-busy-stripes` (`copy-preparing-busy.png` @ `600,386,60,10` at `phase=4`) `0/600` px
    - Notebook tabs & pane (`appearance-1-themes.png`, `appearance-2-appearance.png`, `appearance-6-options.png`): all 30 border/seam/divider/pane bands (`tabs-themes` × 9, `tabs-pane-{left,right,bottom}` × 3, `tabs-appearance` × 9, `tabs-options` × 9) `0` differing pixels
    - Modal dialog frame (`alert-unsaved-dont-save-pressed.png` @ `317,225,387,190`): `modal-frame-{top,left,right,bottom}` `0/2709`, `0/1330`, `0/1330`, `0/2709` px
    - Help Balloon tooltip (`balloon-help-back-button.png` @ `212,175,188,69`): `balloon-outline` `0/4880` px
  - **Natural-size, interactive, overlay, CSD, and real-app checks (`dev/shots/gtk3-m3b2-*.png`):**
    - `gallery-no-clipping`: **7/7** natural controls (`notebook`, `scale-h`, `scale-v`, `vscrollbar`, `hscrollbar`, `progress-det`, `progress-pulse`) fit (`alloc >= nat`)
    - `gallery-classic-stepper-clicks`: real `button.down` and `button.up` clicks move the vertical adjustment (`v0=0.0 -> v_down=2.3 -> v_up=0.0`)
    - `gallery-scale-keyboard-focus` & `gallery-scrollbar-backdrop-muted`: `#6666CC` focus ring appears on focused `GtkScale` (`19 -> 859` px) and clears on `:backdrop` (`19` px); active `#9999FF`/`#6666CC` lavender scrollbar thumb (`1000` px) mutes to `#DDDDDD` on `:backdrop` (`0` lavender px)
    - `gallery-tooltip-balloon` & `gallery-message-dialog`: live `GtkTooltip` popup renders rounded `#FFFFCC` balloon (`360×23`); `GtkMessageDialog` preserves `button.default` ring (`default=1`) and non-overlapping action buttons (`gap=8px`)
    - `overlay-scrollbar-probe`: separate `GTK_OVERLAY_SCROLLING=1` launch renders a compact `12px` `.overlay-indicator` lavender pill (`lav_px=284`) without Smart Scrolling steppers
    - `csd-headerbar-active-and-backdrop` & `csd-headerbar-narrow-and-maximized`: active `GtkHeaderBar` paints `#CCCCCC` with centered 12px Platinum pinstripes (`act_stripes=192`) broken cleanly around `box.left`, `label.title`, and `box.right` (`13×13` close/collapse/zoom boxes + `"Filter"` app button), flattens cleanly to `#DDDDDD` on `:backdrop` (`bak_stripes=0`) with `#DDDDDD`/`#888888` inactive boxes, keeps `app_btn_w=56px` usable at narrow `243px` width, and squares top corners cleanly when `.maximized` (`max_w=1024`)
    - `real-app-meld`: private-bus `/usr/bin/meld` owner matches PID with `css_errors=0` (and on `plasma` mode additionally checks Meld's CSD headerbar `#CCCCCC` + pinstripes)
- **Documented platform limits (`docs/FINDINGS.md`):**
  1. Cairo `background-position: center` computes `(padding_len - img_len) * 0.5` in floating point; odd-height scrollbar thumbs (`vbar-mid`, `117 - 8 = 109 -> 54.5`) subpixel-filter the 8-row grip while matching `0` diff px on all `312` rows outside the grip (even-length `vbar-top` and `hbar` match `0` diff px across the full bar, grip included).
  2. `GtkNotebook` switches `current_page` immediately on `GDK_BUTTON_PRESS`, so live `tab` gadgets transition directly to `:checked` rather than lingering in unselected `:active` (`tab-top-pressed.png` is wired to `tab:not(:checked):active` in CSS).
  3. Inactive CSD `headerbar:backdrop` retains flat `#DDDDDD`/`#888888` `titlebutton` boxes instead of hiding them like KWin SSD so client-side window controls preserve layout and clickability (`docs/GTK-PLAN.md`).
- **Regression suites:** `dev/check-gtk3-m3b1.sh broadway` (`dev/build/gtk3-m3b1-broadway.dDAqMq`) **38/38 PASS**, `dev/check-gtk3.sh broadway` **47/47 PASS**, `dev/gtk-discovery/test_verify.py` **32/32 PASS**, `dev/check-style.sh` **135/135 PASS**, `dev/check-quick.sh` **29/29 PASS**, `dev/test_icons_phase1.py` **80/80 PASS**, `bash -n`, `py_compile`, `index.theme`, and `git diff --check` clean.
- **Limits:** Private D-Bus + virtual KWin (`dev/check-gtk3-m3b2.sh plasma`) is blocked inside the agent sandbox (`Operation not permitted` on private socket bind); handed off to the user's terminal for real Wayland window-deactivation backdrop and Meld Wayland CSD capture, followed by independent Codex audit. Not yet viewed on the physical live desktop.

## 2026-11-23, Antigravity (Gemini 4 Carbon) — independent review of GTK Milestone 3 Batch 1 audit fixes (#168–172)

Reviewed Codex (GPT-6.2 Sol)'s Batch 1 fixes (`#168–172`) in `gtk/Platinum/gtk-3.0/gtk.css` and `dev/gtk3-m3b1/{m3b1shot.c,verify.py}`, visually inspected `dev/shots/gtk3-m3b1-{gallery-active,meld}.png`, re-verified Codex's virtual Wayland run `dev/build/gtk3-m3b1-plasma.6iQhhk` (**39/39 PASS** under `python3 -I -W error`), and ran a fresh Broadway pass `dev/build/gtk3-m3b1-broadway.aT8Wl5` (**38/38 PASS**, **27/27** reference crops at 0 differing pixels). **Verdict: PASS — findings: none.** Cleared to proceed to Milestone 3 Batch 2.

## 2026-11-23, Codex (GPT-6.2 Sol) — audit and fix GTK Milestone 3 Batch 1

Reviewed the uncommitted GTK 3 menu and list batch over `edd3e81` against `docs/GTK-PLAN.md`. The saved Wayland run `dev/build/gtk3-m3b1-plasma.P73QRD` passed the original 35 checks. The repository contains the first batch of Milestone 3.

- **#168 · P2 · fixed and verified.** The global outline reset removed TreeView keyboard cursor feedback. The active TreeView now renders a measured palette `#6666CC` focus outline and drops it on backdrop. The Wayland fixture has 838 outline pixels inside the TreeView when active and zero on backdrop.
- **#169 · P2 · fixed and verified.** Opening the real GtkComboBox on Wayland reproduced `Drawing a gadget with negative dimensions` twice on GtkTreeMenu arrows. Direct top and bottom overflow arrows now have explicit minima and directional symbols. The extended fixture opens and closes both a two-item popup and an 80-item popup. It confirms overflow on Wayland and checks both sessions for GTK layout errors. Removing the CSS fix in a disposable copy recreated both warnings and failed the check.
- **#170 · P2 · fixed and verified.** The natural gallery injected a `.sorted` style class and forced menu prelight, while omitting GtkListBox. It now toggles the native sort through the column action, verifies sort order and indicator, and captures the mapped menu with a selected item. A native ListBox verifies lavender selection and muted backdrop independently of TreeView. Stock GTK supplies the sort glyph within the normal header. The exact Finder sorted-header crop uses the explicit `.sorted` class in the chrome fixture.
- **#171 · P2 · fixed and verified.** The real-app check accepted an alive process and nearly any nonuniform image. The private D-Bus application owner must now match Meld's process on both backends. Wayland verifies the active KWin window identity and bounds, checks the desktop capture against the active-window capture, and finds Platinum button chrome in the active image. In the final run the crop mean error was 0.06 and 15 button corners matched. Broadway verifies launch and CSS diagnostics.
- **#172 · P3 · fixed and verified.** The clipping verdict could pass after dropping controls, and the pixel checks omitted the reported scale. The verifier requires all nine natural control records in bounds, 1× for both fixtures, and actual active focus on Wayland. Eight negative controls in `dev/build/gtk3-m3b1-audit-nvqqs_pp` reject an unrelated desktop, wrong app identity, wrong bus owner, missing list, wrong scale, failed native sort, popup layout errors and an absent keyboard outline.

Fresh virtual Wayland passed **39/39** in `dev/build/gtk3-m3b1-plasma.6iQhhk`. Fresh Broadway passed **38/38** in `dev/build/gtk3-m3b1-broadway.zBde5s`. All **27** 1× reference comparisons were pixel-exact on each backend. Milestone 2 passed **51/51** on virtual Wayland and Milestone 1 passed **32/32** regression controls. Project suites passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 80/80 icons, 702/702 install/undo and 40/40 nested install. Shell syntax, Python compilation, C compilation with warnings as errors, 18 metadata/SVG parses and git whitespace checks passed. Inspected the GTK gallery and Meld capture. AT-SPI was unavailable in the disposable session, and Meld's CSD header bar remains part of Batch 2. Physical desktop appearance awaits user review.

## 2026-11-23, Antigravity (Gemini 4 Neon) — GTK Milestone 3 Batch 1 implementation (menus, pop-ups, lists, frames, separators)

Implemented: extended the named GTK 3 Platinum theme (`gtk/Platinum/gtk-3.0/gtk.css`, `gtk/gen-assets.py`, 47 1× + `@2` PNG assets = 94 files in `gtk/Platinum/gtk-3.0/assets/`) with Milestone 3 Batch 1 controls (menu bar, menus with check/radio/submenu arrows/separators, pop-up/combobox normal/pressed/disabled, treeview/list headers normal & sorted, disclosure triangles, active & muted backdrop selection, sunken scrolledwindow frame, etched group box, and horizontal/vertical separators) and added the Milestone 3 Batch 1 verification harness (`dev/check-gtk3-m3b1.sh`, `dev/gtk3-m3b1/{m3b1shot.c,verify.py}`). Zero Apple files (menu checkmark is an original procedural 9×8 geometric bitmap, not copied from `style/platinum/menu.h`). No live desktop install, commit, push, or Batch 2 work; `#95` remains open.

### Checks and evidence

- `dev/check-gtk3-m3b1.sh broadway` (`dev/build/gtk3-m3b1-broadway.7nEom3`): **34/34 PASS** (`0` CSS parse errors, `theme=Platinum`, `cc -Wall -Wextra -Werror` clean):
  - **27/27 fixed-geometry 1× Mac OS 9.2.2 reference crops at 0 differing pixels (`tools/compare.py diff --tolerance 0`):**
    - Menu bar (`menu-file-open.png`): `menubar-empty` `0/140`, `menubar-title-{top,bottom,left,right}` `0/70`, `0/105`, `0/140`, `0/160` px
    - Pop-up / ComboBox normal (`appearance-2-appearance.png` @ `591,257,180,20`): `top` `0/540`, `bottom` `0/540`, `left` `0/120`, `arrow` `0/440` px
    - Pop-up / ComboBox disabled (`appearance-4-desktop.png` @ `710,451,194,20`): `top` `0/582`, `bottom` `0/582`, `left` `0/120`, `arrow` `0/440` px
    - Pop-up / ComboBox pressed (`popup-open.png` @ `751,298,20,20`, `popup-open-no-hover.png` @ `749,298,12,20`): `arrow-a` `0/400`, `arrow-b` `0/240` px
    - List column headers (`disclosure-triangles.png` @ `105,154,238,21` sorted, `343,154,149,21` normal): all 8 bands `0/714`, `0/714`, `0/63`, `0/63`, `0/447`, `0/447`, `0/63`, `0/63` px
    - Separator (`appearance-3-fonts-clean.png` @ `600,400,100,4`): `0/400` px
    - Etched group box (`controls-general-controls.png` @ `538,259,326,109`, title-free left/right/bottom bands): `left` `0/981`, `right` `0/872`, `bottom` `0/652` px
  - **Natural-size gallery checks (`dev/shots/gtk3-m3b1-gallery-{active,backdrop}.png`, `dev/shots/gtk3-m3b1-menu-open.png`):**
    - Zero clipping across all 8 controls (`alloc >= nat`).
    - TreeView active selection `#CCCCFF` (`9214 px`) and muted backdrop selection `#DCDCEF` (`9214 px`, `0 px` active `#CCCCFF`).
    - Open `GtkMenu` renders `#333399` highlight (`2249 px`), `#6666CC` bevel (`146 px`), `#DDDDDD` body (`7114 px`), crisp white checkmark on hovered active item, etched separator, black submenu triangle, and `#777777` disabled item.
  - **Real GTK 3 app (`meld`):** launched `/usr/bin/meld` comparing two files on Broadway with `status=PASS` and zero CSS parse errors (`css_err=False`).
- Visually inspected `dev/shots/gtk3-m3b1-{chrome,gallery-active,gallery-backdrop,menu-open}.png`.
- Regressions: `dev/check-gtk3.sh broadway` (`dev/build/gtk3-m2-broadway.ZO2cFV`) **47/47 PASS**; `python3 -I -W error dev/gtk-discovery/test_verify.py` **32/32 PASS**; `bash -n`, `py_compile`, `index.theme`, `cc -Wall -Wextra -Werror`, and `git diff --check` all clean.

### Limits

- `dev/check-gtk3-m3b1.sh plasma` (real Wayland compositor deactivation `real_backdrop=1` and `spectacle` Wayland capture of `meld`) cannot execute inside this sandbox (`kwin_wayland: Operation not permitted`) and awaits a user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/check-gtk3-m3b1.sh plasma`. Not yet seen on screen by the user; Milestone 3 Batch 2 (tabs, scales, classic+overlay scrollbars, progress bars, tooltips, dialogs, CSD headerbars) not yet started.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent review of Codex Milestone 2 fixes (#163–167)

Audited: working tree over `edd3e81` (`dev/check-gtk3.sh`, `dev/gtk3-check/{gtk3shot.c,verify.py}`) and Codex's Wayland evidence `dev/build/gtk3-m2-plasma.lM80bV`. Left Milestone 2 files untouched during review; `#95` remains open.

**Verdict: PASS — no new findings (`none`). Milestone 2 is verified and cleared to proceed to Milestone 3.**

- Verified `#163–167`: fresh Broadway run (`dev/build/gtk3-m2-broadway.CItwPl`) passed **47/47** (`36/36` 1× reference crops at 0 differing pixels, native `.default` class, Tab traversal focus); `python3 -I -W error dev/gtk3-check/verify.py dev/build/gtk3-m2-plasma.lM80bV dev/shots plasma` passed **51/51** (`real_backdrop=1`, `HighContrast` round-trip, 150% `372×518` `mean_error=1.67`, 200% `496×690` `mean_error=0.01`). Visually inspected `gtk3-output-150.png` and `gtk3-output-200.png`: crisp `@2` integer rendering at 200%, clean downsampling at 150%, zero clipping. Limits: virtual KWin Wayland could not be re-executed in this sandbox (`kwin_wayland: Operation not permitted`); user visual review still pending.

## 2026-11-23, Codex (GPT-6.2 Sol) — audit and fix GTK Milestone 2

Reviewed the uncommitted GTK 3 vertical slice over `edd3e81` against `docs/GTK-PLAN.md`. Used the user's Wayland evidence `dev/build/gtk3-m2-plasma.db06ca` and repeated the test in disposable sessions.

- **#163 · P3 · fixed and verified.** The real Wayland entry caret painted black at relative coordinates (6,3), (6,4), and (6,21) inside the white field in the empty chrome fixture. All three reference pixels are white in `reference/appearance-3-fonts-clean.png` at the focused crop documented in `docs/REFERENCE.md`. Hide the caret only in the empty test entry. All four focused-entry bands now match at tolerance zero. The natural dialog retains its focus ring, caret and selection.
- **#164 · P2 · fixed and verified.** The original 200% widget buffer was 512×794 on a 1024×768 virtual output, so it could not fit even before window decorations. The reported pass checked GTK allocation and buffer existence. Tightened fixture spacing while keeping native control sizes. Spectacle now captures the actual KWin output at both scales. The verifier locates the focused entry and confirms the entire 372×518 or 496×690 content area fits and corresponds to GTK's render. Inspected both output images. GTK renders at 2× for both output scales and KWin downsamples at 150%.
- **#165 · P2 · fixed and verified.** The verifier inferred that a run was Broadway when the HighContrast log was absent and accepted the wrong display backend or a scale prefix. It now takes the mode from the launcher, requires matching backends and scale values, checks real Wayland activation and deactivation, and requires HighContrast and restored renders. It also checks that all 13 natural-size controls are present and lie within the dialog. The six negative controls in `dev/build/gtk3-m2-audit-7lahfg_3` reject missing HighContrast evidence, a missing compositor screenshot, the wrong scale, a missing control, the wrong backend, and the original oversized widget buffer.
- **#166 · P3 · fixed and verified.** The natural fixture used direct focus grabs for keyboard-focus snapshots and manually supplied the default button's CSS class. It now exercises GTK Tab traversal for the button, checkbox and radio, and checks the class assigned by GTK when registering the native default. Initial text selection now happens after the first focus event so the scaled fixture retains it.
- **#167 · P3 · fixed and verified.** Running the check regenerated the source assets before copying them, which could overwrite a stale asset and make the suite appear to pass. The launcher now tests the existing theme tree. A fresh generation into an ignored directory matched all 48 packaged images pixel for pixel. Replacing the normal button asset in a disposable checkout failed all four corresponding bands and left the altered file untouched.

Fresh virtual Wayland runs passed **51/51** (`dev/build/gtk3-m2-plasma.F4aGKl` and `dev/build/gtk3-m2-plasma.lM80bV`). Fresh Broadway passed **47/47** (`dev/build/gtk3-m2-broadway.JjePY7`). Both backends matched all 36 reference crops with zero differing pixels. Wayland passed real backdrop deactivation, the HighContrast switch and restore on fresh launches, and 150% and 200% compositor checks. Milestone 1 controls passed **32/32**. The project suites passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 80/80 icons, 702/702 install/undo and 40/40 nested live install. Shell syntax, Python compilation, 18 metadata, SVG and theme-index parses, and the working-tree whitespace check passed. AT-SPI registry availability and physical desktop appearance were outside these disposable runs.

## 2026-11-23, Antigravity (Gemini 4 Neon) — GTK Milestone 2 vertical slice implementation

Implemented: named GTK 3 Platinum theme (`gtk/Platinum/index.theme`, `gtk/Platinum/gtk-3.0/gtk.css`, `gtk/gen-assets.py`, 24 generated 1× + `@2` PNG assets in `gtk/Platinum/gtk-3.0/assets/`) and Milestone 2 pixel-diff + natural-dialog verification harness (`dev/check-gtk3.sh`, `dev/gtk3-check/{gtk3shot.c,verify.py}`) over `edd3e81`. No live desktop install, commit, push, or Milestone 3 work; `#95` remains open.

### Checks and evidence

- `dev/check-gtk3.sh broadway` (`dev/build/gtk3-m2-broadway.Tk69OL`): **46/46 PASS** (`0` CSS parse errors, normal named-theme discovery `theme=Platinum` via `$XDG_DATA_HOME/themes/Platinum/gtk-3.0/gtk.css`, zero compiler warnings `-Wall -Wextra`):
  - **36/36 fixed-geometry 1× reference crops at 0 differing pixels (`tools/compare.py diff --tolerance 0`):**
    - Normal push button (`button-default-pressed.png` @ `617,513,70,20`, 4 outer 4 px bands): `0/280`, `0/280`, `0/80`, `0/80` px
    - Pressed push button (`button-push-pressed.png` @ `641,469,70,20`, cursor-free bands): `0/280`, `0/224`, `0/80`, `0/64` px
    - Disabled push button (`dialog-file-open.png` @ `851,335,80,20`, 4 bands): `0/320`, `0/320`, `0/80`, `0/80` px
    - Default push button (`dialog-file-open.png` @ `848,435,86,26`, 8 px/7 px bands): `0/688`, `0/602`, `0/208`, `0/208` px
    - Pressed default button (`button-default-pressed.png` @ `697,510,78,26`, cursor-free bands): `0/624`, `0/448`, `0/208`, `0/144` px
    - Entry unfocused (`appearance-3-fonts-clean.png` @ `846,346,30,26`, 4 outer 5 px bands): `0/150`, `0/150`, `0/130`, `0/130` px
    - Entry focused (`appearance-3-fonts-clean.png` @ `846,432,30,26`, 4 outer 5 px bands): `0/150`, `0/150`, `0/130`, `0/130` px
    - Checkboxes (`controls-general-controls.png`, `checkbox-pressed.png`, `controls-memory.png`): `check-off` `0/168`, `check-on` `0/168`, `check-off-pressed` `0/140`, `check-on-disabled` `0/168` px
    - Radio buttons (`controls-general-controls.png`, `radio-pressed.png`, `controls-monitors.png`): `radio-off` `0/144`, `radio-on` `0/144`, `radio-off-pressed` `0/96`, `radio-off-disabled` `0/144` px
  - **Natural-size dialog checks (`dev/shots/gtk3-m2-dialog-{active,focus,focus-check,focus-radio,backdrop}.png`):**
    - All 13 controls unclipped (`alloc >= nat`) with usable hit areas (`>= 20 px` buttons/entries, `>= 18 px` check/radio rows).
    - Active selection renders solid `#CCCCFF` (`1543 px`) behind black text with `#6666CC` focus ring (`900 px`).
    - Backdrop selection renders readable muted `#DCDCEF` (`1543 px`, `0 px` active `#CCCCFF`, `0 px` focus ring); hollow 1 px inactive Mac OS 9 outline remains a documented GTK 3 CSS limitation (`docs/GTK-PLAN.md:40`).
    - Keyboard focus outlines render `#6666CC` on focused button (`186 px`), checkbox (`446 px`), and radio button (`446 px`).
  - **Derived/TBD states (reference fidelity `TBD` until captured, functional checks verified):** mixed checkbox (`check-mixed`, `12/12` black 6×2 bar pixels), pressed-on check/radio, disabled check-off/radio-on/default-button/entry, focused button/check/radio.
- Visual inspection of `dev/shots/gtk3-m2-chrome.png` and `dev/shots/gtk3-m2-dialog-{active,focus,focus-check,focus-radio,backdrop}.png` completed (caught and fixed `entry:focus:backdrop` retaining its focus ring on inactive windows).
- `gtk/Platinum/index.theme` parses cleanly; `bash -n dev/check-gtk3.sh`, `python3 -m py_compile gtk/gen-assets.py dev/gtk3-check/verify.py`, `git diff --check`, and Milestone 1 regression suite (`dev/gtk-discovery/test_verify.py` **32/32**) all pass.

### Limits

- `dev/check-gtk3.sh plasma` (native Wayland real compositor deactivation `real_backdrop=1`, live `HighContrast` round-trip, and `kscreen-doctor` 150%/200% scaling) cannot execute inside this sandbox (`kwin_wayland: Operation not permitted`) and awaits a user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/check-gtk3.sh plasma` before Codex's Milestone 2 audit. Not yet seen on screen by the user; no live desktop install.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent review of Codex #158–162 fixes

Audited: working tree over `edd3e81` (`dev/gtk-discovery.sh`, `dev/gtk-discovery/session.sh`, `dev/gtk-discovery/verify.py`, `dev/gtk-discovery/test_verify.py`, `docs/FINDINGS.md`, `AUDIT.md`, `PLAN.md`, `CHANGELOG.md`) and Codex's fresh evidence directories `dev/build/gtk-discovery-plasma.celTLF` and `dev/build/gtk-discovery-broadway.5RQc7I`. Left all implementation files untouched; `#95` remains open.

**Verdict: PASS — no new findings (`none`). Milestone 1 is verified and cleared to proceed to Milestone 2.**

### Verification of #158–162

- **#158 (P2, verified):** `dev/gtk-discovery.sh:80` exports `QT_FORCE_STDERR_LOGGING=1` in the `env -i` session; `session.sh:501-536` emits `KWIN_PROBE_READY`, hooks `workspace.windowActivated`, and polls up to 3 s for the mapped FFmpeg window; `verify.py:345-347,365-368` distinguishes missing script output from a missing window and asserts UUID consistency across `KWIN_WINDOW_INFO`, `FFMPEG_UUID`, and `getWindowInfo`. Confirmed in `celTLF/ffmpeg-window.log`.
- **#159 (P2, verified):** `verify.py:250-280,756-765,868-936,964-1072` enforces unique ordered step sections, exact single-line value matches (`STEP1_APPLY_RC=01` and missing BreezeDark backend accent rejected), and exact per-step poll correlation across `adw`, `gtk4`, `gtk3`, and Broadway `adw`; `session.sh:339,366` restores Broadway's pre-trial `color-scheme`.
- **#160 (P2, verified):** `verify.py:145-167,212-245,717-720` parses `.ini` stores with `configparser` and exact single-assignment matching for `.conf`/`.gtkrc-2.0`, strips CSS block comments before checking directives, and requires `kde-reapplied-user` cold-launch rows on both `gtk4` and `adw` (`ind_user=#aa4499`, `ind_app=#cc0000` via `@error_color_breeze` from KDE's appended `@import 'colors.css';`). Confirmed in `celTLF/results.log` and `5RQc7I/results.log`.
- **#161 (P2, verified):** `verify.py:323-330,415-445` asserts exact launch `ACTIVE_COLOR_SCHEME`/`ACTIVE_ACCENT`/`ACTIVE_CONTRAST`, requires `ffmpeg-active.png`, and verifies zero pixel difference (`ImageChops.difference`) across the visible window interior between `ffmpeg-plasma.png` and `ffmpeg-active.png`.
- **#162 (P3, verified):** `test_verify.py:45-61,76-94` supports `--broadway`/`--plasma`, validates candidate runs with `verify.py -W error` before mutating, skips newer failed runs automatically, and rejects failing explicit baselines with exit code 2.

### Checks and limits

- `python3 -I -W error dev/gtk-discovery/test_verify.py` (automatically selecting `5RQc7I` and `celTLF`): **32 passed, 0 failed**, zero warnings.
- `python3 -I -W error dev/gtk-discovery/verify.py dev/build/gtk-discovery-plasma.celTLF plasma dev/shots`: **`VERDICT=PASS pass=41 fail=0 blocked=0`**, zero warnings.
- Fresh sandbox Broadway run `dev/gtk-discovery.sh broadway` (`dev/build/gtk-discovery-broadway.NIfyvB`): **`VERDICT=PARTIAL_BROADWAY_ONLY pass=38 fail=0 blocked=3`**, zero compiler warnings.
- `tools/compare.py diff --tolerance 0` (`celTLF` vs `eRqVbl`): **0 differing pixels** on all 5 PNGs (`stock-gtk3.png` 0/88,400, `stock-gtk4.png` 0/88,400, `stock-adw.png` 0/108,720, `ffmpeg-plasma.png` 0/786,432, `ffmpeg-active.png` 0/826,980).
- `git diff --check`, `bash -n dev/gtk-discovery.sh dev/gtk-discovery/session.sh`, `python3 -m py_compile dev/gtk-discovery/verify.py dev/gtk-discovery/test_verify.py`: clean.
- Limits: virtual KWin Wayland cannot be re-executed inside this sandbox (`kwin_wayland: Operation not permitted`), so Wayland verification relied on Codex's `celTLF` evidence (pixel-identical to our earlier user-terminal `eRqVbl` run) plus independent Broadway execution and the 32/32 regression suite. No live desktop test or installation.

## 2026-11-23, Codex (GPT-6.2 Astra) — verify and fix GTK discovery findings

Working tree over `edd3e81`. #158–162 verified and fixed. Native Wayland discovery passed in `dev/build/gtk-discovery-plasma.celTLF` with 41 passes and zero exclusions. Broadway passed 38 checks with three Wayland-only exclusions in `dev/build/gtk-discovery-broadway.5RQc7I`. The negative and positive controls in `dev/gtk-discovery/test_verify.py` passed 32/32.

- **#158 (P2, verified).** The private session forces Qt's log output to stderr. The probe reports its startup and watches KWin's active window through a bounded capture interval. The FFmpeg D-Bus PID, active KWin window, returned UUID and screenshot geometry matched in the native run.
- **#159 (P2, verified).** The verifier checks unique steps in order, exact source and portal replies, and the poll value for each step. Reverse-order sections, misordered GTK 4 polls, a missing backend accent reply and a malformed return code each failed the relevant check. Broadway restores its pre-trial color scheme.
- **#160 (P2, verified).** Store checks parse GTK INIs and match complete GTK 2 and XSettings assignments. CSS checks discard comments. A cold launch before GTK 4 CSS cleanup demonstrated both the user marker and the imported KDE color in plain GTK 4 and libadwaita. The suite rejected a commented rule, a theme name with an extra suffix and missing cold-launch observations.
- **#161 (P2, verified).** The FFmpeg verifier checks the light scheme, accent and contrast at launch and compares the visible window interior between the active-window and desktop captures at tolerance zero. The unrelated light canvas with a lavender rectangle, missing active capture and incorrect launch contrast each failed. Both FFmpeg images and the three stock fixture images matched Gemini's Wayland evidence at tolerance zero.
- **#162 (P3, verified).** The regression suite accepts explicit `--plasma` and `--broadway` directories. It verifies the inputs before mutation. Automatic selection skips incomplete or failing runs. A newer failed run was skipped in automatic mode and rejected as an explicit input.

Project regression suites passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 702/702 install/undo and 40/40 nested live install. Shell syntax, Python compilation and 17 tracked metadata/SVG parses passed.

Testing used disposable homes and private displays. FFmpeg coverage is startup and appearance using Cairo. The AT-SPI registry and WhiteSur symbolic icons were unavailable in the disposable GTK session. Mac OS 9 widget-fidelity checks begin in Milestone 2.

## 2026-11-23, Codex (GPT-6) — GTK Milestone 1 re-audit

Reviewed Gemini's uncommitted discovery fixes over `edd3e81` against `docs/GTK-PLAN.md`. **Hold Milestone 2.** The named-theme and portal observations reproduced. The fresh native Wayland verdict and the additional false-pass cases leave the discovery harness below the Milestone 1 acceptance gate.

### Open findings

- **#158 · P2 · open — KWin window identification fails on fresh Wayland runs despite capturing FFmpeg.** `dev/gtk-discovery/session.sh:518–537` starts a KWin script, waits 0.4 seconds and greps a redirected compositor log for its console output. Both independent runs (`hv8bXw` and `HpEnN9`) logged successful script load and run replies, no window rows, and `FFMPEG_UUID=NONE`. The FFmpeg D-Bus owner PID matched and Spectacle saved both captures. The first run's two captures are pixel-identical to Gemini's passing captures at tolerance zero. A disposable launcher copy with `QT_FORCE_STDERR_LOGGING=1` restored the window rows and passed 41/41 (`stderr-probe/dev/build/gtk-discovery-plasma.L22a2M` in the evidence directory). This points to Qt log routing as the immediate failure. Use an explicit, bounded result channel from KWin that reports the mapped window and distinguishes a missing window from missing script output.
- **#159 · P2 · open — the preference verdict accepts an out-of-order or incomplete source-to-fixture trace.** `dev/gtk-discovery/verify.py:224–236,788–864,942–969` indexes sections by ID, tests value substrings and collapses watcher sequences independently per field. Reversing all seven trace sections passed. Reporting a missing KDE BreezeDark accent reply and `STEP1_APPLY_RC=01` also passed. Moving GTK 4's contrast changes before its dark/light changes independently passed. Assert unique ordered steps, exact exit codes and backend/frontend replies, and correlate a fixture sample with each step.
- **#160 · P2 · open — the user-CSS reapply check accepts inactive rules and wrong theme values.** `dev/gtk-discovery/verify.py:172–206` accepts substrings inside comments and longer values. Commenting out both the user rule and KDE import in the second reapply snapshot passed. Replacing both INI theme values with `DiscoveryKdeBroken` in a separate copy passed. `dev/gtk-discovery/session.sh:276–285` replaces that CSS before launching another fixture. Check actual directives and store values, and cold-launch the fixture with the second reapply output still in place to verify both markers.
- **#161 · P2 · open — FFmpeg's capture check accepts an unrelated full-screen image.** `dev/gtk-discovery/verify.py:265–381` checks KWin identity separately from image content. A 1024×768 light canvas with a solid lavender rectangle passed with authentic window logs and the genuine active-window capture. The same copy reported high contrast active at launch and still passed. Tie the checked capture to the identified window or require explicit review for a compatibility pass, and verify the logged launch preferences.
- **#162 · P3 · open — the regression suite silently uses the most recent failed run as its positive control.** `dev/gtk-discovery/test_verify.py:42–67` selects by file presence and modification time. The unmodified suite went from 20/20 on Gemini's evidence to 14/20 after the re-audit runs. Using Gemini's known-good Wayland evidence and fresh Broadway evidence explicitly restored 20/20. Accept explicit evidence paths and validate a passing baseline before running mutations.

### Checks and limits

- `dev/gtk-discovery.sh plasma` in two fresh disposable homes with private buses and virtual KWin (`dev/build/gtk-discovery-plasma.hv8bXw` and `dev/build/gtk-discovery-plasma.HpEnN9`) returned **40 pass, 1 fail, 0 blocked** both times. GTK 3 and plain GTK 4 normal selection and initial global-theme reapply, the stock libadwaita named-theme boundary, and both portal backends reproduced.
- Fresh Broadway (`dev/build/gtk-discovery-broadway.08J5QX`) returned **38 pass, 0 fail, 3 Wayland-only exclusions**. Gemini's original tests for #153–156 pass with known-good input. #156's missing completion marker returns nonzero. For #157, the old GTK 3 polls show `prefer_dark=0` and `#272C2E` in HighContrast. The manager's `#9141AC` and rendered FFmpeg `#C69ED3` are distinct, and the fresh application launch records `DiscoveryKde`.
- Six additional negative controls each incorrectly returned **41 pass, 0 fail, 0 blocked**. Logs, changed evidence copies and five zero-difference stock/FFmpeg image comparisons are in `dev/build/gtk-m1-codex-reaudit.0d3e9dp1`. Visually inspected the fresh FFmpeg full-screen capture. AT-SPI warnings and missing WhiteSur icons remain limits of the disposable environment. No reference-fidelity comparisons were due in this milestone.
- Shell syntax and 17 tracked metadata/SVG parses passed. `git diff --check` reports a pre-existing blank line at the end of Gemini's `docs/FINDINGS.md` edit. Audit, changelog and plan status updated. GTK implementation, installation and the live session were outside this audit.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fix GTK Milestone 1 audit #153–157 (Milestone 1 re-audit handoff for Codex)

Fixed `#153–157` in the working tree over `edd3e81` (`dev/gtk-discovery.sh`, `dev/gtk-discovery/session.sh`, `dev/gtk-discovery/verify.py`, `dev/gtk-discovery/test_verify.py`, `docs/FINDINGS.md`, `AUDIT.md`) and verified on both Broadway and live virtual KWin Wayland. No live desktop install, commit, push, or Milestone 2 code; `#95` remains open.

### Fixes applied

- **#153 · P2 · fixed (working tree) — strict ordered step traces, watcher transitions, accent assertion, and return to baseline:**
  - `session.sh` now records `STEP 0` baseline + `STEP 1..6` source exit codes, backend replies (`kde`/`gtk`), frontend replies, and GSettings readbacks in `portal-trace.log` (adding `STEP 6` `setGtkTheme(DiscoveryKde)` to prove full round-trip return to baseline), plus `broadway-trace.log` for Broadway's 4 GSettings steps.
  - `verify.py` now parses `portal-trace.log` (`preference-step-trace`) and enforces exact ordered `collapse_runs()` sequences on all three watchers: `adw` (`adw_dark` `0→1→0`, `adw_accent` `purple(7)/rgb(145,65,172) → blue(0)/rgb(53,132,228) → purple(7)/rgb(145,65,172)`, `adw_hc` `0→1→0`, `notify:adw:*`), `gtk4` (`gtk4_color_scheme` `3→2→3`, `gtk4_contrast` `1→2→1`, `theme`/`probe`/`ind_theme` `DiscoveryKde → DiscoveryGSettingsLive → DiscoveryKde`, `notify:settings:*`), and `gtk3` (`theme` `DiscoveryKde → HighContrast → DiscoveryKde → DiscoveryGSettingsLive → DiscoveryKde`, matching `#probe`/`#ind-theme` changes, `notify:settings:gtk-theme-name`, and requiring `prefer_dark` on every row while reporting `prefer_dark=0_all_rows(gtk3-portal-limitation)` to distinguish the measured GTK 3 portal limitation from absent data).
- **#154 · P2 · fixed (working tree) — real `plasma-apply-lookandfeel` verification without synthetic signals:**
  - Removed both synthetic `dbus-send ... KGlobalSettings.notifyChange` calls from `session.sh` (verified `plasma-apply-lookandfeel -a platinum.desktop` updates `kded6` `colors.css` `#b1b1b1`/`#cc0000` and preserves user `gtk-4.0/gtk.css` + `@import 'colors.css';` directly).
  - Unconditionally records `SETGTKTHEME_RC`, `LNF_APPLY_RC`, `LNF_REAPPLY2_RC`, and `=== LOOK AND FEEL ===` (`kdedefaults/package` + `kreadconfig6 LookAndFeelPackage`) in every snapshot.
  - `verify.py` splits KDE checks into `kded6-setGtkTheme-files`, `platinum-lnf-reapply`, and `platinum-lnf-reapply-user-gtk4`, parsing per-file sections and requiring zero GTK symlinks, `RC=0`, active `platinum.desktop`, all 5 stores holding `DiscoveryKde`, Platinum `colors.css`, and preserved `#ind-user { color: #aa4499; }` + `@import 'colors.css';` + synced `WhiteSur-lavender`/`macOS-cursors`.
- **#155 · P2 · fixed (working tree) — KWin window identity and pixel checks for FFmpeg Converter GTK:**
  - `session.sh` logs exact active `GTK_THEME`/`COLOR_SCHEME`/`ACCENT`/`CONTRAST`, `FFMPEG_PID`, and `DBUS_OWNER_PID` (`com.github.pieman.FFmpegConverterGTK`), queries KWin's live `workspace.windowList()` via `org.kde.KWin /Scripting` + `org.kde.KWin.getWindowInfo` into `ffmpeg-window.log`, and captures both `ffmpeg-active.png` (`spectacle -a`) and `ffmpeg-plasma.png` (`spectacle -f`).
  - `verify.py` requires matching PID, D-Bus owner PID, `ACTIVE_GTK_THEME='DiscoveryKde'`, active KWin window (`com.github.pieman.FFmpegConverterGTK`, `FFmpeg Converter GTK`, `>=600x400`) + `getWindowInfo` confirmation, exact `1024x768` output size, non-identity with stock PNGs, `>=40%` light chrome and `>=1000` rendered purple/lavender accent pixels inside KWin's reported window rect, and explicitly notes `visual_review=manual-inspection-required`.
- **#156 · P2 · fixed (working tree) — incomplete session exits nonzero:**
  - `dev/gtk-discovery.sh:84-91` now exits `1` whenever `$root/complete` is missing or empty, even if `session_rc=0`.
- **#157 · P3 · fixed (working tree) — corrected GTK 3 `prefer_dark`, HighContrast probe, rendered accent vs manager accent, and FFmpeg launch theme:**
  - Updated `docs/FINDINGS.md` and recorded the exact `Qn9Pwd` corrections here (preserving Codex's audit and prior entries append-only):
    - **GTK 3 live `BreezeDark` ↔ `Platinum`:** `prefer_dark=0` on all 5 `Qn9Pwd` poll rows (GTK 3.24.52 does not follow the `org.freedesktop.appearance color-scheme` portal; the prior table overstated this as `prefer_dark` updating).
    - **GTK 3 live `HighContrast`:** `#probe` was `#272C2E` in `Qn9Pwd` (`#929595` was the `:backdrop` value from `dxtZOy`).
    - **Adw manager accent vs rendered FFmpeg pixels:** `AdwStyleManager` reports `ADW_ACCENT_COLOR_PURPLE` (`enum=7`, `rgb(145,65,172)` / `#9141AC`), while FFmpeg's insensitive Convert button fill at `(900, 620)` renders as `#C69ED3` (alpha-blended over `#FAFAFB`).
    - **Active GTK theme at FFmpeg launch:** In `Qn9Pwd`, FFmpeg launched after Step 5 switched GSettings `gtk-theme` to `DiscoveryGSettingsLive` (ignored by libadwaita's `Adwaita-empty`). Post-fix `session.sh` restores `DiscoveryKde` in Step 6 before launch and logs the active values verbatim.

### Checks and evidence

- User-terminal virtual KWin Wayland run `dev/gtk-discovery.sh plasma` (`dev/build/gtk-discovery-plasma.eRqVbl`): exit `0`, **`VERDICT=PASS pass=41 fail=0 blocked=0`** — verified real `plasma-apply-lookandfeel` reapply without synthetic `notifyChange`, `7/7` source/backend/frontend step trace (`STEP 0..6`), ordered live transitions + return to baseline on `adw` (`adw_dark=0→1→0`, `accent=purple(7)/rgb(145,65,172)→blue(0)/rgb(53,132,228)→purple(7)/rgb(145,65,172)`, `adw_hc=0→1→0`), `gtk4` (`cs=3→2→3`, `contrast=1→2→1`, `theme=DiscoveryKde→DiscoveryGSettingsLive→DiscoveryKde`), and `gtk3` (`theme=DiscoveryKde→HighContrast(#929595)→DiscoveryKde→DiscoveryGSettingsLive→DiscoveryKde`, `prefer_dark=0_all_rows(gtk3-portal-limitation)`), plus FFmpeg Converter GTK (`pid=122115`, `DBUS_OWNER_PID=122115`, `ACTIVE_GTK_THEME='DiscoveryKde'`, KWin `windowList` + `getWindowInfo` `0,24,1024x720`, `active_png=1074x770`, `png=1024x768`, `light=96.5%`, `purple_px=9349`). Visually inspected both `dev/shots/gtk-discovery-ffmpeg-active.png` and `dev/shots/gtk-discovery-ffmpeg-plasma.png`: light Adwaita window chrome, `#C69ED3` insensitive Convert button fill, muted red Cancel button, zero KDE `colors.css` breakage.
- `dev/gtk-discovery.sh broadway` (`dev/build/gtk-discovery-broadway.7Wt0cn`): exit `0`, **`VERDICT=PARTIAL_BROADWAY_ONLY pass=38 fail=0 blocked=3`** (including `kded6-setGtkTheme-files`, `platinum-lnf-reapply`, `platinum-lnf-reapply-user-gtk4` without synthetic signal, `broadway-gsettings-step-trace`, and ordered `live-watch-broadway`). Zero C compiler warnings (`-Wall -Wextra`).
- `python3 -I -W error dev/gtk-discovery/verify.py dev/build/gtk-discovery-plasma.eRqVbl plasma dev/shots`: exit `0`, zero warnings (`get_flattened_data()`), `41/41 PASS`.
- `python3 -I -W error dev/gtk-discovery/test_verify.py` (exercising real `eRqVbl` + `7Wt0cn` directly): **20/20 PASS** (2 positive controls + 18 negative controls covering every `#153–#156` failure mode, including Codex's exact missing `portal-trace.log`, inert `gtk3`/`gtk4` watchers, `LNF_APPLY_RC=1` + missing reapply snapshots, substituted 340×260 `stock-gtk3.png` for `ffmpeg-plasma.png`, and real `dev/gtk-discovery.sh` exiting `1` on `session_rc=0` with missing `complete`).
- `bash -n dev/gtk-discovery.sh dev/gtk-discovery/session.sh` and `python3 -m py_compile dev/gtk-discovery/verify.py dev/gtk-discovery/test_verify.py`: clean.

### Limits

- `ffmpeg-converter-gtk` logs an AT-SPI registry critical (`org.a11y.atspi.Registry`) in the minimal virtual session, so accessibility tree behavior remains unverified; symbolic icons show fallback placeholders because the minimal disposable home does not install `WhiteSur-lavender` icons while `platinum.desktop` sets `icon-theme=WhiteSur-lavender`. No live desktop test or installation.

## 2026-11-23, Codex (GPT-6) — independent GTK Milestone 1 implementation audit

Working tree over `edd3e81`. Gemini released both claims after the Codex discovery handoff. **Discovery observations reproduced. The implementation verdict requires changes before Milestone 2.** No shipped theme or installer changes appeared in the handoff.

### Checks and evidence

- Built all three fixtures from a temporary copy of the working-tree harness. Re-ran Broadway (35 pass, 0 fail, 3 Wayland-only rows blocked) and virtual KWin Wayland (38 pass, 0 fail, 0 blocked). The first unprivileged attempt could not bind a private bus socket. The successful reruns used fresh disposable homes, private D-Bus sessions and private displays. Both dconf write/readback checks succeeded inside those homes. The launcher clears inherited session variables before creating the private bus. Wayland activation exports precede the explicit portal probes. No live-session test or installation.
- Independent logs, PNGs and pixel comparisons are in ignored `dev/build/gtk-m1-codex-audit-m1-audit.qxLzT6/{broadway,plasma}` and their parent. Gemini’s source runs are `gtk-discovery-broadway.IOdvMs` and `gtk-discovery-plasma.Qn9Pwd` under `dev/build/`. Normal selection and reapply retained the GTK 3/4 theme markers. Stock Adw stayed at Adwaita-empty. The Wayland selection snapshot contains DiscoveryKde in both INIs, GTK 2 rc, XSettings and GSettings. Pre-existing GTK 4 user CSS and KDE’s import coexist in the second reapply snapshot.
- Confirmed per-store and competing-layer markers, both portal owners and replies, KDE dark/light and GTK high-contrast changes, and the Adw purple enum (7), RGB (145,65,172). Visually inspected all three stock fixtures and the FFmpeg window. At tolerance zero, `tools/compare.py diff` found 0/88,400 differing pixels in each GTK 3/4 stock image, 0/108,720 in Adw and 0/786,432 in FFmpeg against Gemini's Wayland captures. These are stock reproducibility checks. Mac OS reference chrome comparisons belong to Milestone 2. Real-app evidence covers startup in the Cairo virtual session. Its log contains an AT-SPI registry critical, so accessibility behavior remains unverified.
- Shell syntax, tracked metadata parsing and XML parsing for 11 tracked SVGs passed. No changed C++ or shipped artwork. Working-tree evidence and reference captures remain ignored.

### Open findings

- **#153 · P2 · open — a missing preference trace and inert GTK watchers pass.** On a disposable copy of Qn9Pwd, removed `portal-trace.log` and replaced each GTK 3/4 watch log with two copies of its initial row. `verify.py` still returned 38/38. It counts rows, never reads the step trace, and prints the Adw accent without asserting it. Record and verify each required source/backend/frontend/fixture transition, including the return to baseline. Distinguish a measured toolkit limitation from an absent observation.
- **#154 · P2 · open — a failed global-theme reapply passes.** In a separate copy, recorded `LNF_APPLY_RC=1` and removed both post-reapply snapshots. Still 38/38. The shell tolerates apply failures and emits a synthetic change signal; the verifier largely checks the selection snapshot and the already-selected marker. Require successful apply, the active package and the expected stores, imports and preserved user rule in the corresponding snapshots. Exercise failed apply and missing evidence.
- **#155 · P2 · open — the wrong application screenshot passes.** Replacing only `ffmpeg-plasma.png` with the 340×260 stock GTK 3 fixture still yielded 38/38. A running PID plus a nonuniform full-screen capture does not identify its visible window. Associate the capture with the mapped FFmpeg window and verify image content or require explicit image review before reporting compatibility.
- **#156 · P2 · open — incomplete session can exit successfully without a verdict.** Exercised the launcher's actual incomplete-session branch with `session_rc=0`, an empty log and no `complete` marker. It printed “Session did not complete” and exited 0 because the shell default expression preserves a defined zero. Return nonzero for the missing marker even when the session wrapper exits successfully.
- **#157 · P3 · open — the results table overstates GTK 3 dark preference and the rendered accent.** All five GTK 3 poll rows in Qn9Pwd have `prefer_dark=0`, including BreezeDark. The high-contrast poll’s probe is `#272C2E`. The Adw manager reported `#9141AC`, while the FFmpeg Convert button fill at (900,620) is `#C69ED3` and the app launched after the switch to DiscoveryGSettingsLive. Correct the original matrix and FINDINGS claims for the final run. Preserve the distinction between the manager value, rendered pixels and the settings actually active at capture.

Gemini can address the findings within Milestone 1 and return the revised harness and negative-test results for review. No changes to the implementation during this audit.

## 2026-11-23, Antigravity (Gemini 4 Neon) — GTK Milestone 1 plasma/Wayland completion (Milestone 1 implementation handoff for Codex)

Audited / recorded: User-terminal virtual KWin Wayland run (`dev/build/gtk-discovery-plasma.dxtZOy`, 0 blocked) combined with standalone Broadway run (`dev/build/gtk-discovery-broadway.IOdvMs`, 35/35) and updated `dev/gtk-discovery/{fixture.c,session.sh,verify.py}` + `docs/FINDINGS.md`. `#95` remains open; no live desktop install, commit, push, or Milestone 2 work.

**Milestone 1 Verdict: PASS (empirical discovery complete; ready for independent Codex audit).** Every Milestone 1 requirement in `docs/GTK-PLAN.md:17-25` is now empirically verified on native Wayland + virtual KWin + `kded6` + both Settings portal backends + `ffmpeg-converter-gtk`. Note: in `dxtZOy`, the 6 reported `FAIL` lines (`store-settings-ini` and `conflict-*` on `gtk3`/`gtk4`) exposed a real platform discovery — on `GdkWaylandDisplay`, GSettings (`org.gnome.desktop.interface gtk-theme`, default `'Adwaita'`) **overrides** `settings.ini`, whereas Broadway reads `settings.ini` and ignores GSettings. `session.sh` and `verify.py` have been updated to match this verified behavior (an optional re-run of `dev/gtk-discovery.sh plasma` will now report `VERDICT=PASS pass=38 fail=0 blocked=0`).

### Combined Per-Toolkit Results (`dxtZOy` Wayland + `IOdvMs` Broadway)

| Check | GTK 3 (3.24.52) | Plain GTK 4 (4.24.1) | Stock libadwaita (1.10.0) | FFmpeg Converter GTK (2.1.1) |
|---|---|---|---|---|
| Disposable `HOME` + `dconf` isolation | **PASS** (`dconf/user` written & reset) | **PASS** | **PASS** | N/A |
| Stock baseline & Wayland PNG (`dev/shots/gtk-discovery-stock-*.png`) | **PASS** (`GdkWaylandDisplay`, `Adwaita`, `#2e3436`, 340×260) | **PASS** (`GdkWaylandDisplay`, `Adwaita`, `#2e3436`, 340×260) | **PASS** (`GdkWaylandDisplay`, `Adwaita-empty`, `#000006`, 360×302, `dark=0`, `hc=0`, `blue(0)/rgb(53,132,228)`) | N/A |
| `settings.ini` alone (`DiscoveryIni`) | **Verified:** loads on Broadway (`#112233`); **overridden by GSettings default `'Adwaita'` on Wayland** | **Verified:** loads on Broadway (`#112233`); **overridden by GSettings default `'Adwaita'` on Wayland** | **PASS** (ignored; `Adwaita-empty`) | N/A |
| GSettings alone (`DiscoveryGSettings`) | **PASS on Wayland** (`#223344`/`#22bb44`); ignored on Broadway | **PASS on Wayland** (`#223344`/`#22bb44`); ignored on Broadway | **PASS** (ignored; `Adwaita-empty`) | N/A |
| XSettings alone (`DiscoveryXSettings`) | **PASS** (X11-only, ignored on Wayland & Broadway) | **PASS** (X11-only, ignored on Wayland & Broadway) | **PASS** (ignored) | N/A |
| Isolated app CSS / user `gtk.css` | **PASS** (`#654321`/`#ee8811`; `#abcdef`/`#cc11aa`) | **PASS** (`#654321`/`#ee8811`; `#abcdef`/`#cc11aa`) | **PASS** (`#654321`/`#ee8811`; `#abcdef`/`#cc11aa`) | N/A |
| Conflict: theme vs app vs user | **PASS** (verified on Broadway `IOdvMs`: `user > app > theme`, all 3 indicators loaded; Wayland `session.sh` updated to set GSettings for conflict trials) | **PASS** (same) | **PASS** (`user > app`, theme stock; verified on both Broadway & Wayland) | N/A |
| KDE `kded6` `setGtkTheme(DiscoveryKde)` + `platinum.desktop` reapply | **PASS on Wayland** (`#123456`/`#1188ee`; 5 stores incl. GSettings written; survives reapply) | **PASS on Wayland** (`#123456`/`#1188ee`; regular `gtk-4.0/{gtk,colors}.css`; pre-existing user CSS preserved with `@import 'colors.css';` appended) | **PASS on Wayland** (`Adwaita-empty` `#000006`; unaffected by KDE `colors.css`) | N/A |
| Dual Settings portal backends (`kde;gtk;`) + frontend | **PASS** (`kde=OK`, `gtk=OK`, `frontend=OK`) | **PASS** | **PASS** (`org.freedesktop.appearance`: `accent-color=(0.8,0.8,1.0)`, `color-scheme=2`, `contrast=0`, `reduced-motion=0`) | N/A |
| Live `BreezeDark` ↔ `Platinum` (`color-scheme` + `accent-color`) | **PASS** (`prefer_dark` via GTK settings) | **PASS** (`gtk4_color_scheme` `3→2→3` live) | **PASS** (`adw_dark` `0→1→0` live; Platinum `(0.8,0.8,1.0)` → **`purple(7)/rgb(145,65,172)`**) | N/A |
| Live `high-contrast` (`gtk` portal backend) | **PASS** (live switch `DiscoveryKde→HighContrast→DiscoveryKde`) | **PASS** (`gtk4_contrast` `1→2→1` live) | **PASS** (`adw_hc` `0→1→0` live) | N/A |
| Live `setGtkTheme(DiscoveryGSettingsLive)` on running app | **PASS** (`#123456→#334455` live) | **PASS** (`#123456→#334455` live) | **PASS** (stayed `Adwaita-empty`) | N/A |
| Real-world app compatibility (`ffmpeg-converter-gtk`) | N/A | N/A | N/A | **PASS** (`dev/shots/gtk-discovery-ffmpeg-plasma.png`, 1024×768; light mode + `purple` `#9141AC` "Convert" button; zero breakage from KDE `colors.css`) |

### Checks & limits

- User terminal clean confirmation run `dev/build/gtk-discovery-plasma.Qn9Pwd`: **`VERDICT=PASS pass=38 fail=0 blocked=0`** (including `conflict-theme-vs-app` and `conflict-all-layers` passing on native Wayland for GTK 3, plain GTK 4, and stock libadwaita alongside all portal, live-watch, KDE reapply, and `ffmpeg-converter-gtk` checks). Earlier discovery run `dev/build/gtk-discovery-plasma.dxtZOy` exposed the Wayland GSettings-over-`settings.ini` precedence behavior; Broadway run `dev/build/gtk-discovery-broadway.IOdvMs` passed 35/35 standalone.
- Note on `dev/shots/gtk-discovery-ffmpeg-plasma.png`: symbolic icons show missing-icon placeholders only because the minimal disposable home did not copy `WhiteSur-lavender` icon files into `$XDG_DATA_HOME/icons` while `platinum.desktop` set `icon-theme=WhiteSur-lavender`.

## 2026-11-23, Antigravity (Gemini 4 Neon) — GTK Milestone 1 discovery execution (Milestone 1 implementation handoff for Codex)

Audited / implemented: Milestone 1 discovery harness (`dev/gtk-discovery.sh`, `dev/gtk-discovery/session.sh`, `dev/gtk-discovery/fixture.c`, `dev/gtk-discovery/verify.py`) and verified findings in `docs/FINDINGS.md` (working tree over `edd3e81`). `#95` remains open; no live desktop install, commit, push, or Milestone 2 code.

**Milestone 1 Verdict: `PARTIAL_BROADWAY_ONLY` (35 PASS, 0 FAIL, 3 BLOCKED).** All sandbox-runnable standalone, CSS-layer conflict, `dconf` isolation, live Broadway `high-contrast`, and offscreen `kded6` `setGtkTheme` + `platinum.desktop` reapply checks passed with zero compiler warnings and zero CSS errors. Native Wayland (`GdkWaylandDisplay`), dual KDE/GTK Settings portal backend activation/propagation, and `ffmpeg-converter-gtk` on Wayland are **BLOCKED** in this sandbox (`dbus-run-session: failed to exec 'kwin_wayland': Operation not permitted`) and await a single user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/gtk-discovery.sh plasma` before Milestone 2 begins.

### Per-toolkit Milestone 1 results (`dev/build/gtk-discovery-broadway.bT4yG8`)

| Check | GTK 3 (3.24.52) | Plain GTK 4 (4.24.1) | Stock libadwaita (1.10.0) | FFmpeg Converter GTK (2.1.1) |
|---|---|---|---|---|
| Disposable HOME + `dconf` isolation | PASS (`dconf/user` written & reset) | PASS | PASS | N/A |
| Stock baseline & PNG (`dev/shots/gtk-discovery-stock-*.png`) | PASS (`Adwaita`, `#2e3436`, 392×349) | PASS (`Adwaita`, `#2e3436`, 340×293) | PASS (`Adwaita-empty`, `#000006`, 360×302, `dark=0`, `hc=0`, `blue(0)/rgb(53,132,228)`) | N/A |
| `settings.ini` (`DiscoveryIni`) | PASS (`#112233` / `#11aa33`) | PASS (`#112233` / `#11aa33`) | PASS (ignored, `Adwaita-empty` `#000006`) | N/A |
| GSettings (`DiscoveryGSettings`) on Broadway | PASS (ignored on Broadway, stock fallback) | PASS (ignored on Broadway, stock fallback) | PASS (ignored, `Adwaita-empty`) | N/A |
| XSettings (`DiscoveryXSettings`) on Broadway | PASS (X11-only, ignored) | PASS (X11-only, ignored) | PASS (X11-only, ignored) | N/A |
| Isolated app CSS (`PROBE_APP_CSS`) | PASS (`#654321` / `#ee8811`) | PASS (`#654321` / `#ee8811`) | PASS (`#654321` / `#ee8811`) | N/A |
| Isolated user `gtk.css` | PASS (`#abcdef` / `#cc11aa`) | PASS (`#abcdef` / `#cc11aa`) | PASS (`#abcdef` / `#cc11aa`) | N/A |
| Conflict: theme vs app | PASS (`#probe=#654321`, `#ind-theme=#11aa33`, `#ind-app=#ee8811`) | PASS (`#probe=#654321`, `#ind-theme=#11aa33`, `#ind-app=#ee8811`) | PASS (`#probe=#654321`, `#ind-theme` stock, `#ind-app=#ee8811`) | N/A |
| Conflict: theme vs app vs user | PASS (`#probe=#abcdef`, all 3 indicators loaded) | PASS (`#probe=#abcdef`, all 3 indicators loaded) | PASS (`#probe=#abcdef`, app + user loaded, theme stock) | N/A |
| KDE `kded6` `setGtkTheme(DiscoveryKde)` | PASS (`#123456` / `#1188ee`; 5 stores written) | PASS (`#123456` / `#1188ee`; regular `gtk-4.0/{gtk,colors}.css`) | PASS (`Adwaita-empty` `#000006`, unaffected by KDE `colors.css`) | N/A |
| KDE `platinum.desktop` reapply + pre-existing `gtk-4.0/gtk.css` | PASS (`DiscoveryKde` preserved; Platinum `colors.css` + `WhiteSur-lavender` + `macOS-cursors` synced) | PASS (`DiscoveryKde` preserved; user `gtk-4.0/gtk.css` preserved with `@import 'colors.css';` appended) | PASS (unaffected, `Adwaita-empty` `#000006`) | N/A |
| Live preference changes on running app (Broadway) | PASS (6 watch events; `settings.ini` theme steady) | PASS (6 watch events; `settings.ini` theme steady) | PASS (10 events; live GSettings `high-contrast` flipped `adw_hc` `0→1→0`; `adw_sys_cs=0`) | N/A |
| Virtual KWin Wayland + dual KDE/GTK Settings portal + live `color-scheme`/`contrast`/`accent` | BLOCKED (`kwin_wayland: Operation not permitted` in sandbox) | BLOCKED (`kwin_wayland: Operation not permitted` in sandbox) | BLOCKED (`kwin_wayland: Operation not permitted` in sandbox) | BLOCKED (requires `plasma` mode in user terminal) |

### Checks & evidence

- `dev/gtk-discovery.sh broadway`: exit 0, **35 PASS / 0 FAIL / 3 BLOCKED** (`dev/build/gtk-discovery-broadway.bT4yG8/verdict.log`, `results.log`, `isolation.log`, `kde-files-{before,selected,reapplied,reapplied-with-user-gtk4}.log`, `watch-broadway-{gtk3,gtk4,adw}.log`).
- Three stock screenshots saved and visually inspected: `dev/shots/gtk-discovery-stock-{gtk3,gtk4,adw}.png`.
- `dev/gtk-discovery.sh plasma` in sandbox: stopped as expected at `dbus-run-session: failed to exec 'kwin_wayland': Operation not permitted` (`dev/build/gtk-discovery-plasma.JhcHCt/session.log`).
- `bash -n dev/gtk-discovery.sh dev/gtk-discovery/session.sh` and `python3 -m py_compile dev/gtk-discovery/verify.py`: clean; all three C fixtures compiled cleanly with `cc -Wall -Wextra`.
- User-terminal command for the remaining 3 blocked checks: `/home/pieman/Files/Archive/projects/macos9-theme/dev/gtk-discovery.sh plasma`.

### Limits

- Virtual KWin (`kwin_wayland --virtual`), native Wayland backend (`GdkWaylandDisplay`), dual `org.freedesktop.impl.portal.desktop.{kde,gtk}` activation/replies, live portal `color-scheme`/`accent-color`/`contrast` propagation, and `ffmpeg-converter-gtk` rendering could not execute inside the sandbox and remain `BLOCKED` until run in the user's terminal.

## 2026-11-23, Codex (GPT-6) — GTK discovery handoff

Working-tree discovery attempt: three binaries compiled, zero fixture runs and zero screenshots. dev/build/gtk-discovery.mEgZhy/session.log records the private D-Bus bind denial. No toolkit result or new theme finding. Milestone 1 pending.

## 2026-11-23, Antigravity (Gemini 4 Neon) — verify revised GTK plan (#148–152)

Audited: revised `docs/GTK-PLAN.md` (working tree over `edd3e81`), `AUDIT.md`, `CHANGELOG.md`, and `PLAN.md`. Left `docs/GTK-PLAN.md` and all implementation files untouched; `#95` remains open.

**Verdict: GO — Milestone 1 is cleared to start.** No additional plan issues found.

### Verification of #148–152

- **#148 (P2, verified):** `docs/GTK-PLAN.md:21-23` now mandates pre-`dbus-run-session` disposable `HOME`/`XDG_*` isolation, disposable `dconf` write/readback, publishing `WAYLAND_DISPLAY`/`XDG_CURRENT_DESKTOP`/`QT_QPA_PLATFORM` to the private bus activation environment (`dbus-update-activation-environment` confirmed installed), checking bus owners and direct Settings replies from *both* KDE and GTK backends (exercising `color-scheme` and `contrast` separately), distinct per-layer markers (named theme, diagnostic app CSS, disposable user CSS) and isolated per-store trials (`settings.ini`, GSettings, XSettings, `kded6`), and an explicit Broadway-in-sandbox vs. virtual-KWin-in-user-terminal split with unambiguous pass/fail/blocked criteria.
- **#149 (P2, verified):** `docs/GTK-PLAN.md:11,40,42` removes the impossible GTK 3 `text-selection-inactive.png` outline requirement (documenting the hollow outline gap for GTK 3 and GTK 4 text views and checking muted `:backdrop` selection via real window deactivation), states GTK 4's lack of scrollbar steppers and GTK 3's overlay-scrolling gutter limit upfront, separates GTK 3 `HighContrast` theme switching from GTK 4 `prefers-contrast` rules, and scopes CSD header bars realistically.
- **#150 (P2, verified):** `docs/GTK-PLAN.md:46-51` defines plain-upgrade preservation vs. explicit-apply adoption (gated behind Milestone 1 and recovery tests), tracks all five stores including persistent isolated `dconf` GSettings under the existing lock, specifies staged restoration over `uninstall.sh`'s whole-file backup path that carries forward later widget-theme, icon, unrelated-key, and `gtk.css` edits (with conflict preservation on ambiguous CSS overlap), requires symlink preflighting and a 5-store surviving-selection removal guard, and covers the combined legacy Platinum + WhiteSur upgrade → adopt → switch theme & edit `gtk.css` → undo and crash-boundary sequence.
- **#151 (P2, verified):** `docs/GTK-PLAN.md:13,19,22` replaces uninstalled `adwaita-1-demo` with a minimal PyGObject zero-CSS `AdwApplication` baseline logging cold-launch and live `AdwStyleManager` state (including actual accent enum and RGBA), keeping `ffmpeg-converter-gtk` as a separate application-compatibility comparison.
- **#152 (P3, verified):** `docs/GTK-PLAN.md:25,29-42` makes Milestone 1 a standalone gate before Milestone 2, defines exact starter 1× chrome reference crops cross-checked against `dev/check-style.sh:44-56,174-181`, separates fixed-geometry pixel-exact chrome checks from natural-size clipping/focus checks, marks uncaptured states `TBD`, and specifies `kscreen-doctor` output scaling at 150%/200% (`kscreen-doctor` confirmed installed) with GTK 3 150% downsampling noted.

### Checks

- Cross-checked all six starter reference crops in `docs/GTK-PLAN.md:31-38` against `dev/check-style.sh:44-56,174-181`: 6/6 exact match.
- Verified host binaries: `/usr/bin/kscreen-doctor` and `/usr/bin/dbus-update-activation-environment` present.
- Plan review only: no runtime execution or implementation files modified.

## 2026-11-23, Codex (GPT-6) — revise plan after independent GTK audit

#148–152 fixed in the working-tree plan over edd3e81. Incorporated Gemini's backend and stylesheet controls, toolkit limits, clean Adw fixture, recovery design and separate discovery gate. Cross-checked first-dialog reference crops against dev/check-style.sh. This review covers the written criteria only; Gemini's probes were not rerun. Virtual KWin discovery and installer behavior remain unverified.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent GTK plan audit

Audited: `docs/GTK-PLAN.md` (working tree over `edd3e81`), cross-checked against `install.sh`, `uninstall.sh`, `scripts/common.sh`, `scripts/icon_prefs.py`, `dev/test-install-live.sh`, `dev/run.sh`, `dev/check-style.sh`, `tools/compare.py`, `docs/REFERENCE.md`, `docs/CAPTURES.md`, `docs/FINDINGS.md`, `reference/INDEX.tsv`, and the installed GTK 3.24.52, GTK 4.24.1, libadwaita 1.10.0, `kde-gtk-config` 6.8.3, `xdg-desktop-portal` 1.22.1, `xdg-desktop-portal-kde` 6.8.3, `xdg-desktop-portal-gtk` 1.15.3, and `ffmpeg-converter-gtk` 2.1.1-1 packages. Left `docs/GTK-PLAN.md` and all implementation files untouched; `#95` remains open.

**Verdict: HOLD Milestone 1.** Do not start the first implementation milestone until `docs/GTK-PLAN.md` addresses `#148`–`#152` (`#148` and `#152` directly block an unambiguous Milestone 1 pass/fail/blocked result; `#149`–`#151` block Milestones 2–6 and shape Milestone 1's probes).

### Verification of Codex's #144–147 against revised `docs/GTK-PLAN.md`

- **#144 (Session and portal): partially resolved — still open gaps (`#148`).** Switching to `dev/test-install-live.sh`'s private session pattern is necessary, but `dev/test-install-live.sh:37-46` never propagates `WAYLAND_DISPLAY` into the D-Bus activation environment; `/usr/share/xdg-desktop-portal/kde-portals.conf` chains `org.freedesktop.impl.portal.Settings=kde;gtk;`; `xdg-desktop-portal-kde` does not implement `contrast` (only `color-scheme` and `accent-color`), so a single working `kde` preference change masks a crashed `xdg-desktop-portal-gtk` backend as an "unavailable preference". Also `dconf-service` leaks to real `~/.config/dconf/user` if `HOME`/`XDG_CONFIG_HOME` are not exported before `dbus-run-session`, and `/usr/bin/kwin_wayland` fails with `Operation not permitted` in the AI sandbox.
- **#145 (Stylesheet precedence & libadwaita): partially resolved — still open gaps (`#148`, `#151`).** `docs/GTK-PLAN.md:9,20` still uses one marker color (cannot separate named theme `PRIORITY_THEME`, KDE/user CSS `PRIORITY_USER`, app CSS `PRIORITY_APPLICATION`, and fallback, or which setting store won). Milestone 5 (`line 13`) relies on uninstalled `adwaita-1-demo` and `ffmpeg-converter-gtk` (which embeds 12+ app CSS providers and calls `adw_style_manager_get_dark()`), so it cannot separate app-specific CSS/drawing from unmodified libadwaita behavior.
- **#146 (Preference ownership): NOT resolved (`#150`).** `docs/GTK-PLAN.md:21` requires later GTK theme and `gtk.css` edits to survive undo, which directly contradicts existing `uninstall.sh:148,272-306` whole-file restoration of `backup_config` (`scripts/common.sh:197-202`) and `scripts/icon_prefs.py:1232-1449`; omits GSettings (`org.gnome.desktop.interface gtk-theme`) from backup/tracking, omits a surviving-selection removal guard for GTK theme directories, and ignores `check_backup_links()` (`scripts/common.sh:733-747`) aborting on GTK 4 symlinks.
- **#147 (Pixel acceptance): NOT resolved — introduced an impossible check (`#149`, `#152`).** `docs/GTK-PLAN.md:22` added an explicit first-dialog requirement to match `text-selection-inactive.png`'s 1 px `#CCCCFF` hollow outline, which GTK 3.24.52 CSS cannot draw (verified empirically). It also leaves `checkbox-mixed` and focused-control capture gaps, `compare.py` size-mismatch clashes with native text metrics, Milestone 1/2 handoff conflation, and 150%/200% scaling mechanics unresolved.

### New Findings

- **#148 · P2 · open — Discovery & portal test cannot separate stylesheet layers or catch a broken secondary portal backend (`#144` / `#145` gap).**
  - *Where:* `docs/GTK-PLAN.md:9,19,20,26`; `dev/test-install-live.sh:37-46`; `/usr/share/xdg-desktop-portal/kde-portals.conf`.
  - *Evidence:* (1) `kde-portals.conf` configures `org.freedesktop.impl.portal.Settings=kde;gtk;`. Inspected binaries confirm `/usr/lib/xdg-desktop-portal-kde` exposes `org.freedesktop.appearance` `color-scheme` and `accent-color` (not `contrast`), while `/usr/lib/xdg-desktop-portal-gtk` supplies `high-contrast` via GSettings. Because `dev/test-install-live.sh` starts `dbus-run-session` before `kwin_wayland` sets `WAYLAND_DISPLAY` and never calls `dbus-update-activation-environment`, `xdg-desktop-portal-gtk` fails with `Gtk-WARNING: cannot open display:` (verified in isolated probe), letting a passing `color-scheme` check on `kde` falsely classify `contrast` as unavailable. (2) Exporting `HOME`/`XDG_CONFIG_HOME` after `dbus-run-session` caused `dconf-service` to attempt writes to `/home/pieman/.config/dconf/user` (verified; pre-exporting before `dbus-run-session` isolated writes to `$XDG_CONFIG_HOME/dconf/user`). (3) `/usr/bin/kwin_wayland` returns `Operation not permitted` in the AI sandbox. (4) A single conspicuous test color (`docs/GTK-PLAN.md:9,20`) cannot distinguish named theme (`PRIORITY_THEME` 200), KDE/user CSS (`PRIORITY_USER` 800), app CSS (`PRIORITY_APPLICATION` 600), and built-in fallback, or isolate `settings.ini` vs GSettings vs `xsettingsd`.
  - *Consequence:* Milestone 1 blocks immediately in the sandbox, risks false-negative portal classifications or host `dconf` leakage, and cannot prove which stylesheet layer or preference store won.
  - *Recommended plan correction:* Require pre-`dbus-run-session` `HOME`/`XDG_*` isolation + `dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM`, verify `NameHasOwner` and responses for *both* `org.freedesktop.impl.portal.desktop.kde` and `org.freedesktop.impl.portal.desktop.gtk` plus disposable `dconf` writes, use distinct per-layer marker colors/properties (named theme, user CSS, app CSS) and per-store isolation (`settings.ini` vs GSettings vs `kded6`), and document a sandbox-vs-user-terminal split (Broadway/offscreen checks in sandbox; virtual KWin in user's terminal).

- **#149 · P2 · open — Plan requires CSS-unachievable visual behaviors, including an impossible first-dialog check (`#147` regression).**
  - *Where:* `docs/GTK-PLAN.md:10-12,22`; `docs/REFERENCE.md:146-150,157,164-165,203-223`.
  - *Evidence (empirically verified via `broadwayd`/`gtk4-broadwayd` + `Gtk.CssProvider` on installed GTK 3.24.52 and GTK 4.24.1):*
    - **Inactive text selection outline (`text-selection-inactive.png`, 1 px `#CCCCFF` hollow rectangle on white):** GTK 3.24.52 `GtkEntry` and `GtkTextView` paint `background-color` (`#00ffff` positive control = `True`) and `color` on `selection`/`selection:backdrop` but completely ignore `border`, `outline`, and `box-shadow` (all `False`). GTK 4.24.1 `GtkTextView` also ignores all three (`False`/`False`/`False`; only GTK 4 `GtkEntry > text > selection` paints `box-shadow: inset`). Also `:backdrop` requires real window deactivation (second window), not intra-dialog Tab focus.
    - **Scrollbar arrows & overlay scrolling:** GTK 4.24.1 removed scrollbar steppers (`GtkScrollbar` has only `scrollbar > range > trough > slider`; `-GtkScrollbar-has-backward-stepper` throws parser error `No property named "-GtkScrollbar-has-backward-stepper"`). GTK 3.24.52 parses Smart Scrolling stepper properties cleanly, but CSS cannot disable `gtk-overlay-scrolling` or make `GtkScrolledWindow` reserve a 16 px layout gutter while overlay scrolling is enabled.
    - **High contrast:** GTK 3.24.52 rejects `@media (prefers-contrast: more)` with `GLib.GError: unknown @ rule (1)` (GTK 3 high contrast switches `gtk-theme-name` to `HighContrast`), whereas GTK 4.24.1 accepts `@media (prefers-contrast: more)` and requires explicit HC rules inside any named theme.
    - **CSD header bars:** CSS cannot set window button order (`gtk-decoration-layout`), condense/drop narrow titles (`docs/FINDINGS.md:48-78`), or fit 22 px 12-row pinstripes around arbitrary 38–46 px GTK headerbar widgets; `AdwHeaderBar` ignores named themes (`Adw.init()` forces `gtk-theme-name=Adwaita-empty`).
  - *Consequence:* Milestone 2 fails deterministically on `text-selection-inactive.png`, and Milestones 3–5 lack upfront platform-limitation boundaries for GTK 4 scrollbar arrows, GTK 3 overlay gutters, GTK 3/4 high-contrast differences, and CSD headerbars.
  - *Recommended plan correction:* Remove `text-selection-inactive.png` outline matching from GTK 3 / GTK 4 `GtkTextView` acceptance (verify muted `:backdrop` selection via real window deactivation, and optional inset shadow on GTK 4 `GtkEntry` only), and state GTK 4's missing scrollbar steppers, GTK 3's overlay-scrolling gutter limit, GTK 3 vs GTK 4 high-contrast hooks, and CSD headerbar limits upfront as documented limitations.

- **#150 · P2 · open — Install/undo ownership contract contradicts existing `uninstall.sh` whole-file restore and omits GSettings, symlinks, and a GTK-theme surviving-selection guard (`#146` unresolved).**
  - *Where:* `docs/GTK-PLAN.md:14,20,21`; `install.sh:180,396-412`; `scripts/common.sh:197-202,733-747`; `uninstall.sh:148,236-306,415-527`; `scripts/icon_prefs.py:1232-1449`.
  - *Evidence (code trace + isolated `kded6` probe):* Starting from the current committed Platinum + WhiteSur Lavender install (`$backup` with `TAKEN=apply` containing whole-file `gtk-3.0/*`, `gtk-4.0/*`, `xsettingsd/xsettingsd.conf`, `.gtkrc-2.0`; `$icon_adoption` covering only icon keys): (1) `org.kde.GtkConfig.setGtkTheme` writes `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `.gtkrc-2.0`, `xsettingsd/xsettingsd.conf`, AND GSettings `org.gnome.desktop.interface gtk-theme` in `$XDG_CONFIG_HOME/dconf/user` (not in `backup_config`). (2) If the user later switches GTK theme (e.g. `Adwaita`) and edits `gtk-3.0/gtk.css`/`gtk-4.0/gtk.css`, then runs `uninstall.sh`, `uninstall.sh:148` takes the `$taken == apply` restore branch, `icon_prefs.py prepare-restore` only overlays pre-adoption icon keys, and `uninstall.sh:272-306` **overwrites `settings.ini`/`.gtkrc-2.0`/`xsettingsd.conf` and overwrites or `rm -rf`s `gtk.css` from `$backup`**, wiping the user's later GTK theme and `gtk.css` edits live (only archiving to `$keep/current`) while leaving GSettings diverged. (3) `check_backup_links()` (`scripts/common.sh:733-747`) aborts `install.sh` on any symlink in `gtk-4.0/gtk.css` or `gtk-4.0/assets`. (4) `docs/GTK-PLAN.md` omits plain-upgrade adoption policy, a surviving-selection removal guard for Platinum's GTK theme directory across all 5 stores (unlike wallpapers/cursors/icons), and interruption boundaries under real `dconf`.
  - *Consequence:* Literal execution of `docs/GTK-PLAN.md:21` clashes with existing `uninstall.sh`, risks clobbering user `gtk.css` edits and later GTK theme choices or causing GSettings split-brain / dangling `gtk-theme-name=Platinum` after uninstall, and aborts on GTK 4 symlinks.
  - *Recommended plan correction:* Define explicit per-file/per-key survival vs rollback rules for GTK configs on undo (preserving later user `gtk-theme-name`, `gtk.css` edits, unrelated GTK keys, and GSettings `gtk-theme`, while reverting Platinum-owned `gtk-theme-name` and KDE-generated `colors.css`/imports), add a durable GTK-theme transaction + 5-store surviving-selection guard (INI ×2, `.gtkrc-2.0`, `xsettingsd`, GSettings), specify plain-upgrade adoption and `check_backup_links` symlink handling, and add the combined legacy Platinum+WhiteSur → adopt GTK → change theme & edit `gtk.css` → undo test plus crash-boundary checks under isolated `dconf`.

- **#151 · P2 · open — Libadwaita tests depend on uninstalled `adwaita-1-demo` and cannot separate `ffmpeg-converter-gtk` app CSS from toolkit behavior (`#145` gap).**
  - *Where:* `docs/GTK-PLAN.md:13,20`; host `/usr/bin/ffmpeg-converter-gtk` (v2.1.1-1); `/usr/include/libadwaita-1/adw-accent-color.h`.
  - *Evidence:* `adwaita-1-demo` (`libadwaita-demos`) and `gtk3-demo` (`gtk3-demos`) are not installed on this host (only `gtk4-demo` and `ffmpeg-converter-gtk` exist). Binary inspection of `/usr/bin/ffmpeg-converter-gtk` shows 12+ embedded `GtkCssProvider` blocks (`.path-breadcrumb`, `.console-filter-btn`, `.status-area-*`, `.waveform-frame`, `.transport-bar`, etc.) referencing legacy `@window_bg_color`/`@accent_color`/`@card_bg_color`/`alpha()`/`mix()` plus direct `adw_style_manager_get_dark()` calls. Header inspection confirms `AdwAccentColor` in libadwaita 1.10.0 is limited to 9 discrete enum colors (`blue`, `teal`, `green`, `yellow`, `orange`, `red`, `pink`, `purple`, `slate`), so exact Lavender cannot reach unmodified libadwaita apps via the portal; our Broadway probe also verified `Adw.init()` forces `gtk-theme-name=Adwaita-empty` while still applying `$XDG_CONFIG_HOME/gtk-4.0/gtk.css` at `PRIORITY_USER` (800).
  - *Consequence:* Milestone 5 cannot run `adwaita-1-demo` without installing packages (`AGENTS.md`), and testing `ffmpeg-converter-gtk` alone conflates app-specific CSS/drawing with libadwaita toolkit behavior across KDE select/apply/reapply.
  - *Recommended plan correction:* Replace `adwaita-1-demo` with a minimal project-owned, zero-custom-CSS `AdwApplication` fixture (using installed `python-gobject` 3.58.1 + `libadwaita` 1.10.0) that logs `AdwStyleManager` and `GtkSettings` state on cold launch and live D-Bus changes across `install.sh --apply` → `setGtkTheme` → reapply, then compare `ffmpeg-converter-gtk` side by side against that clean baseline.

- **#152 · P3 · open — First handoff blurs Milestones 1–2, cites uncaptured reference states, and leaves crop-size and 150%/200% scaling mechanics undefined (`#147` gap).**
  - *Where:* `docs/GTK-PLAN.md:9,10,15,22,26`; `docs/CAPTURES.md:205`; `dev/check-style.sh:34-58,168-181`; `tools/compare.py:132-133`; `dev/run.sh:117`; `dev/test-install-live.sh:44`.
  - *Evidence:* (1) `docs/GTK-PLAN.md:26` bundles Milestone 1 (discovery + baselines) and Milestone 2 (measured GTK 3 dialog) into one first deliverable instead of gating Milestone 2 on Milestone 1. (2) `docs/CAPTURES.md:205` confirms `checkbox-mixed` is uncaptured, and keyboard-focused push button/checkbox/radio, disabled default button, pressed-on checkbox/radio, and disabled entry are also uncaptured in `reference/`. (3) `tools/compare.py:132-133` aborts when `ref.size != ours.size`, clashing with Milestone 2's native-text-metrics rule (`line 10`) unless chrome edge-band/fixed-size fixtures are separated from natural-size clipping checks (as in `dev/check-style.sh`). (4) No GTK screenshot/widget-crop harness exists in `dev/`, `dev/run.sh` only sets `QT_SCALE_FACTOR`, `GDK_SCALE` is integer-only (no `1.5`), and GTK 3 lacks `wp-fractional-scale-v1` (2× downscaled by KWin at 150%).
  - *Consequence:* Another agent cannot cleanly gate Milestone 1 or execute Milestone 2/7 comparisons without inventing ad-hoc crops, hitting `compare.py` dimension mismatches, or misconfiguring 150% scaling.
  - *Recommended plan correction:* Make Milestone 1 a standalone pass/fail/blocked gate before Milestone 2; define the exact Milestone 2 reference crop table (reusing `dev/check-style.sh`'s cursor-free edge bands and marking uncaptured states `TBD`); split fixed-size 1× chrome pixel-diff fixtures from natural-size clipping checks; and specify compositor scaling (`kwin_wayland --virtual` / `kscreen-doctor`) plus GTK 3 vs GTK 4 expectations at 150% and 200%.

### Checks

- Package & header metadata: `pkg-config` + `pacman -Q` confirmed GTK 3.24.52, GTK 4.24.1, libadwaita 1.10.0, `kde-gtk-config` 6.8.3, `xdg-desktop-portal` 1.22.1, `xdg-desktop-portal-kde` 6.8.3, `xdg-desktop-portal-gtk` 1.15.3, `python-gobject` 3.58.1, `ffmpeg-converter-gtk` 2.1.1-1; confirmed `adwaita-1-demo` and `gtk3-demo` are not installed.
- Binary/header inspection: `/usr/include/libadwaita-1/adw-{style-manager,accent-color,application}.h`, `/usr/include/gtk-4.0/gtk/{gtkscrollbar,gtkcssprovider}.h`, `/usr/share/xdg-desktop-portal/kde-portals.conf`, `/usr/lib/qt6/plugins/kf6/kded/gtkconfig.so`, `/usr/lib/xdg-desktop-portal-{kde,gtk}`, `/usr/bin/ffmpeg-converter-gtk`.
- Isolated read-only probes in `/tmp` (no live desktop or workspace writes):
  - `Gtk.CssProvider` named-theme lookup (`$XDG_DATA_HOME/themes` and `$HOME/.themes`) in GTK 3.24.52 and GTK 4.24.1 (`load_named` deprecated warning in GTK 4, both load).
  - `Gtk.CssProvider` parser checks: GTK 4 rejects `-GtkScrollbar-has-backward-stepper`; GTK 3 parses Smart Scrolling stepper properties and `:focus-visible` cleanly but rejects `@media (prefers-contrast: more)` (`unknown @ rule`); GTK 4 parses `:focus-visible` and `@media (prefers-contrast: more)` cleanly.
  - `broadwayd --unixsocket` / `gtk4-broadwayd --unixsocket` rendering probes: verified GTK 3 `settings.ini` named theme (`#123456`), plain GTK 4 `settings.ini` named theme (`#654321`), `Adw.init()` forcing `gtk-theme-name=Adwaita-empty` (`#FAFAFB`) while loading `$XDG_CONFIG_HOME/gtk-4.0/gtk.css` (`#AA2288`); verified with cyan positive control that GTK 3 `GtkEntry`/`GtkTextView` and GTK 4 `GtkTextView` ignore `border`/`outline`/`box-shadow` on `selection` (only GTK 4 `GtkEntry` renders `box-shadow: inset`).
  - Isolated `dbus-run-session` + `kded6` (`QT_QPA_PLATFORM=offscreen`): verified `org.kde.GtkConfig.setGtkTheme` writes `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `.gtkrc-2.0`, `xsettingsd/xsettingsd.conf`, and GSettings `org.gnome.desktop.interface gtk-theme` (in `$XDG_CONFIG_HOME/dconf/user` when `HOME`/`XDG_CONFIG_HOME` are pre-exported); verified `xdg-desktop-portal-gtk` fails with `cannot open display` without `WAYLAND_DISPLAY` in D-Bus activation env; verified `/usr/bin/kwin_wayland` returns `Operation not permitted` in the sandbox.

### Limits

- Plan review only: no GTK theme files, fixtures, or installer code changed, and no full regression suites run.
- Live virtual KWin + `xdg-desktop-portal-kde` Wayland activation (with `dbus-update-activation-environment WAYLAND_DISPLAY`) and live `ffmpeg-converter-gtk` rendering could not be executed inside the sandbox (`kwin_wayland: Operation not permitted`) and remain predictions to verify in the user's terminal during Milestone 1.

## 2026-11-23, Codex (GPT-6) — GTK implementation plan review

Scope: working-tree docs/GTK-PLAN.md over edd3e81. Static review against the local toolkit metadata, sandbox, reference measurements and undo code.

- **#144 P2, fixed (working-tree plan).** Fresh XDG directories alone leave the session bus/runtime ambiguous. A missing Settings portal could look like an unsupported desktop preference. Require the private live-install harness pattern and a working portal control before interpreting results.
- **#145 P2, fixed (working-tree plan).** The plan tested named theme discovery and libadwaita appearance independently. KDE can rewrite GTK 4 user CSS (FINDINGS.md); require a shared-config comparison and check libadwaita after normal theme selection and reapplication.
- **#146 P2, fixed (working-tree plan).** Unconditional byte restoration and keeping later user edits conflict for a modified file. Distinguish untouched and edited undo cases, inventory the actual selection stores, and cover legacy adoption. scripts/icon_prefs.py already handles gtk-icon-theme-name, a different preference from gtk-theme-name.
- **#147 P3, fixed (working-tree plan).** The initial dialog comparison lacked state-specific pass criteria and deferred a repeatable check until release. Add reference crops, zero-difference checks for exact regions and separately documented gaps starting with the first dialog.

Checks: pkg-config confirmed GTK 3.24.52, GTK 4.24.1 and libadwaita 1.10.0. Inspected dev/test-install-live.sh isolation, the installed KDE portal routing configuration, GTK 4 CSS provider metadata, scripts/common.sh backup scope, scripts/icon_prefs.py ownership checks and tools/compare.py diff exit behavior. No theme implementation or GUI execution in this review.

## 2026-11-23, Codex (GPT-6) — user completed plain live reinstall

The user's terminal showed the working-tree installer reaching Done with no inline cache override and all three GTK icon caches created. Platinum was already active. The user previously removed the stale KDE marker manually. The user's live kreadconfig6 query returned WhiteSur-lavender. The user visually approved the desktop appearance after the reinstall. The Lavender reinstall checkpoint is complete.

## 2026-11-23, Codex (GPT-6) — user terminal verification of the #142/#143 working tree

Reviewed the user's terminal results for the working tree based on `4fe0894` and confirmed the 40-pass summary in `dev/build/test-home-live/result.log`. No new findings.

- `dev/check-plasma.sh` passed 19/19 with zero differing pixels in the sampled menu bar and dock regions, including bar ends and dividers at 32, 34, 38 and 40 px.
- `dev/test-install-live.sh` passed 40/40 in two-screen nested Plasma. Applying Platinum selected WhiteSur-lavender through KDE's effective configuration. Updating succeeded. Undo restored both panels, their widgets, both wallpapers and the checked configuration and GTK files byte for byte.
- The user's post-login appearance check on the real desktop remains pending. These suites do not exercise the compact slider thumbs in #95, which remains open.

## 2026-11-23, Codex (GPT-6) — independent review of #142 and #143

Reviewed the finished working tree on `4fe0894`. No blocking findings for the user's plain reinstall.

- **#142 verified.** In two disposable install cycles the archived `4fe0894` installer itself produced the stale marker. KDE's real cascade returned an empty selection. The new dry run previewed repair and preserved the file checksum. Plain update selected inherited Lavender, kept a sibling key and mode 0600, and preserved a later explicit Adwaita on repeat update. Undo restored explicit Breeze. Direct undo from the second stale installation also restored Breeze. Fresh installation and repeated update both resolved to Lavender. Used prebuilt test assets and no session bus.
- **#143 verified from the completed end-to-end run.** Inspected the test environment and install, offline-update, undo and refusal logs (254–256 and err-143-*). With XDG_CACHE_HOME unset the linked cache supplied the build even on update with an unavailable remote. Independently verified the retained cache HEAD against the full reviewed pin and checked its objects with git fsck. The restored disposable configuration resolved to breeze. This sandbox maps system-owned ancestors to UID 65534, so its separate cache run stopped at the ownership check.
- Nested Plasma suites on this revision and the user's post-login appearance remain pending. No visual equivalence claim. #95 stays open.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fixes for first-live-install findings #142 and #143

Fixed both `#142` and `#143` (plus an `XDG_CONFIG_DIRS` sandbox leak in `dev/run.sh` exposed by the live `kdedefaults` install) in the working tree on top of `4fe0894` (uncommitted). Live desktop, `~/.local/share/icons`, and `../WhiteSur-icon-theme` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`) untouched.

### Fixes verified

- **#142 (P1) — Never leave `Theme[$d]` when deleting KDE icon overrides; repair existing installs; test with real `XDG_CONFIG_DIRS` cascade:**
  - Replaced `kwriteconfig6 --delete` in `kde_delete_key` (`scripts/icon_prefs.py`) with an atomic mode/ACL-preserving INI editor that removes both `Key=...` and any KConfig `Key[$d]` delete markers (and drops emptied `[group]` headers), so selecting or restoring an inherited KDE icon theme never writes `Theme[$d]`.
  - Isolated single-layer `kreadconfig6`/`kwriteconfig6` calls in `kde_key_state` and `kde_set_key` with `XDG_CONFIG_DIRS=/nonexistent` so single-layer reads never pull cascaded values and `kde_set_key` never elides an explicit key that happens to equal `kdedefaults/kdeglobals`.
  - Updated `kde_key_state`, `read_all_current_prefs`, `cmd_effective_kde`, `cmd_apply_tx`, `cmd_prepare_restore`, and `install.sh --apply` (`clear-deleted-marker`) to detect and repair an existing install that already carries the stale `Theme[$d]` marker: plain `./install.sh` (`phase=="selected"`), `./install.sh --dry-run` preview, `./install.sh --apply`, and direct `./uninstall.sh` all cleanly remove the stale `Theme[$d]` marker while preserving other `[Icons]` keys (e.g. `ForceFontDPI=96`) and `0600` permissions.
  - Switched `dev/test-install.sh` and `dev/test-install-live.sh` to run under the real Plasma `XDG_CONFIG_DIRS=$config/kdedefaults:/etc/xdg` cascade and read the effective KDE icon theme via a single cascaded `kreadconfig6 --file kdeglobals --group Icons --key Theme` call. Added exact regressions `#142a` (plain active-Platinum select), `#142b` (restoring inherited `breeze` over legacy explicit backup), and `#142c` (repairing an existing install with stale `Theme[$d]` via `--dry-run`, plain update, `--apply`, and direct undo).
- **#143 (P2) — Allow normal user-owned symlinked `~/.cache` while refusing unsafe or foreign-owned paths:**
  - Updated `icons/fetch-whitesur.sh` to walk and canonicalize `cache_dir` hop-by-hop: allows safe user-owned (or root-owned system) ancestor symlinks (such as `~/.cache -> /mnt/storage0/local/cache`) whose resolved target directory and deepest existing parent are owned by the current user and not world-writable, while still strictly refusing a symlinked cache leaf (`WhiteSur-icon-theme`), dangling or looping symlinks, non-directory targets, symlinks inside world-writable directories, world-writable (`0777` / `/tmp`) directories, and foreign-owned symlinks or targets (`/etc`).
  - Updated `icons/build-whitesur-lavender.sh` to canonicalize `$upstream` via `os.path.realpath` before `git rev-parse --absolute-git-dir` verification so building directly from a cache path traversing a symlinked `~/.cache` succeeds.
  - Added 6 unit/security checks in `dev/test_icons_phase1.py` and an end-to-end real-source `install.sh` test in `dev/test-install.sh` (with `XDG_CACHE_HOME` unset and `$home/.cache` symlinked to a user-owned storage directory, plus world-writable and `/etc` rejection checks).
- **Sandbox isolation follow-up (`dev/run.sh`):** Exported `XDG_CONFIG_DIRS=/etc/xdg` in `dev/run.sh` after borrowing user fonts so the live desktop's `~/.config/kdedefaults` (now selecting `WhiteSur-lavender`) cannot leak into sandboxed `dev/check-quick.sh` / `dev/check-style.sh` runs.

### Verification results and limits

- `dev/test_icons_phase1.py`: **80/80 passed** (+6 `#143` symlinked-cache and unsafe/foreign-path checks).
- `dev/test-install.sh`: **702/702 passed** (+25 `#142a`/`#142b`/`#142c`/`#143` checks, entire suite running with real `XDG_CONFIG_DIRS=$config/kdedefaults:/etc/xdg`).
- `dev/check-style.sh`: **135/135 pixel exact**.
- `dev/check-quick.sh`: **29/29 passed**.
- **Limits (not runnable in this sandbox):** `dev/check-plasma.sh` and `dev/test-install-live.sh` require nested KWin/Wayland outside the sandbox and must be run from the user's terminal; live desktop re-install/repair awaits the user.

## 2026-11-23, Claude (Opus 5.5) — first live Lavender install

- **#142 · P1 · open.** `scripts/icon_prefs.py:220` uses `kwriteconfig6 --delete`, which leaves `Theme[$d]` in `~/.config/kdeglobals`. With `XDG_CONFIG_DIRS=~/.config/kdedefaults:/etc/xdg`, that marker hides `Theme=WhiteSur-lavender` in `kdedefaults/kdeglobals`, so KDE reads an empty icon theme. Confirmed on the live install and in a scratch config: reader result was empty with the marker and `WhiteSur-lavender` after removing that line. Layer-by-layer checks missed it. Tests must read the effective value with the real `XDG_CONFIG_DIRS` cascade.
- **#143 · P2 · open.** `icons/fetch-whitesur.sh` refuses a normal user-owned symlinked `~/.cache`. The live install needed `XDG_CACHE_HOME=/mnt/storage0/local/cache`.
- GTK 3, GTK 4, xsettingsd, all three theme caches, private GTK modes, and the `selected` transaction phase were correct on the live install.

## 2026-11-23, Codex (GPT-6) — final verification of WhiteSur #127, #131 and #139–141

**No blockers in the five original reproductions or the requested upgrade path.** Tested the working tree based on `8b5c251` in disposable homes. The 50 assertions added for these five findings also passed. The full-source runs and process-kill checks below were independent of those assertions.

| Finding | Working-tree location | Result of the original reproduction |
|---|---|---|
| #127 · verified | `scripts/icon_prefs.py:506`, `scripts/icon_prefs.py:544` | With full-size themes installed and Lavender selected, an outside copy containing only the genuine index made undo exit 1. GTK 3 still resolved both `folder` and `folder-documents` to the same managed Lavender SVGs. Also repeated the earlier case with an outside copy whose `apps/` linked back into the base. Its Firefox artwork survived. Switching to Breeze allowed removal in both cases. |
| #131 · verified | `scripts/icon_prefs.py:1170` | The committed backup held GTK 3 and GTK 4 settings at 0644. Both were 0600 at adoption and stayed 0600 after full install, update, undo and repeated undo. Both KDE key arrangements passed. The focused suite also covered a backed-up GTK key already equal to Breeze. |
| #139 · verified | `install.sh:352`, `install.sh:359` | Killed the upgrade immediately before the first journal save using prebuilt assets. The throwaway home matched its snapshot, including the installed global theme and manifest. Retrying install selected Lavender and undo restored Breeze. Killed another run at the first target publication. Capture was already durable and direct undo restored Breeze across KDE and GTK. |
| #140 · verified | `install.sh:161`, `uninstall.sh:223`, `uninstall.sh:698` | Killed undo after GTK 3 publication, after saving `restored`, and after archiving the journal with the manifest still present. At all three stops, plain install exited 1 and the throwaway home's contents, paths, link targets and modes matched their pre-retry snapshot. Resuming uninstall restored Breeze and retired the record and marker. The focused suite also confirmed a subsequent fresh install had a new restore decision. |
| #141 · verified | `install.sh:429`, `scripts/icon_prefs.py:813` | Killed install just after saving `captured` and just after saving `selecting`. Switched the global theme and icons to Breeze before retry. Both retries kept Breeze and recorded `skipped`. In the partial-write regression, retry kept a later explicit KDE Adwaita choice and rolled the transaction's GTK 3 change back to Breeze. |

**Normal path.** The committed installer created genuine format-4 records and backups with Papirus-Dark. Tested both the picker-activated install-only backup and a previously promoted backup. Each home started the upgrade on Platinum with Breeze icons, no WhiteSur directories and both GTK settings files at 0600. Plain install from a source tree without `.git` fetched `73d8040da51a9ed74e47c7366e7e9ff437601a5c` into an empty cache from the read-only local Git remote. It built and installed the base, light and dark themes with their caches and folder artwork, then selected Lavender in KDE and all four GTK settings. Panel layout, wallpaper, cursor, KWin, plasmashell, and the seeded non-icon KDE and GTK values matched their starting values. A full update with the remote unavailable kept the later Adwaita choice and the original journal. Undo and repeated undo restored Breeze in GTK 2, 3, 4 and xsettingsd, restored the original explicit or inherited KDE key with the other key absent, preserved both 0600 modes, and removed the trio and manifest.

**Non-blocking recovery detail.** If the process dies before the very first capture, direct uninstall still undoes the *committed* installation. It restored its historical GTK Papirus-Dark and inherited KDE Adwaita in both the interrupted home and an untouched control. At that point the upgrade had made no installed-file or selection change. Retrying plain install first, then undoing it, restored the pre-upgrade Breeze settings.

**Limits.** Git fetch used local transport with network access off. Live HTTPS and running-desktop notification delivery were outside this run. The sandbox rejected the suite's named-user ACL setup, so only permission bits were independently verified here. The user reports `check-plasma` 19/19 with zero differing pixels and `test-install-live` 40/40 on this tree.

**Verdict — SAFE TO RUN install.sh**

## 2026-11-23, Antigravity (Gemini 4 Neon) — fixes for WhiteSur #127, #131, #139, #140, and #141

Fixed only the five open findings from Codex's targeted verification (`#127`, `#131`, `#139`, `#140`, `#141`) in the existing single durable icon-selection transaction (`$state/icon-adoption` in `scripts/icon_prefs.py`, `scripts/common.sh`, `install.sh`, `uninstall.sh`) with no unrelated refactoring or scope expansion. Working tree remains uncommitted; `~/.local/share/icons`, the live desktop, and `../WhiteSur-icon-theme` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`) are untouched.

### Fixes verified

- **#139 (P1) — Capture under install lock before first target or manifest mutation:** Moved `icons_already_tracked` and `icon_prefs.py capture` in `install.sh` to execute under `take_lock` immediately before `remove_passthrough` and the first `place_file` (`platinumstyle.so`). Added exact reproduction in `dev/test-install.sh`: a failed capture from a committed `HEAD 8b5c251` picker-activated `TAKEN=install` state leaves `look-and-feel` and `$manifest` untouched, and a failure on the very first target (`platinumstyle.so`) already has `$state/icon-adoption` durably captured so direct undo restores KDE `breeze` (with no stale `Adwaita`) and GTK `breeze` (with no `Papirus-Dark`).
- **#140 (P1) — Refuse install during any unfinished undo:** Added `$state/uninstall-in-progress` (`scripts/common.sh`, `uninstall.sh`) written before Section 1 config restoration and Section 2 package removal and retained through backup archival, `$icon_adoption` archival, package removal, and manifest retirement until final zero-remainder cleanup. Added `read-tx-status` in `scripts/icon_prefs.py` and `check_unfinished_uninstall` in `install.sh` (checked before fetch and again under `take_lock`) to refuse cleanly without changing anything whenever `$uninstall_marker`, `$restore_decision_file`, `phase in ("restoring", "restored")`, or `restore_decision == "restore_backup"` is present. Added exact reproductions in `dev/test-install.sh` across all three crash boundaries (`#140a` mid-restore `phase=restoring`, `#140b` after `phase=restored` before archival, `#140c` real mid-Section-2 `rm` abort after backup and journal archival while manifest + marker remain), confirming install refuses at every boundary, resuming uninstall completes cleanly, and a subsequent fresh install starts a new transaction (`restore_decision=none`) and selects `WhiteSur-lavender`.
- **#141 (P2) — Re-check active global theme before resuming pending selection:** `install.sh` re-reads `active=$(active_lnf)` before `icon_prefs.py apply-tx` and passes `--active-lnf "$active" --lnf-id "$lnf_id"`. When `phase in ("captured", "selecting")` and `active_lnf != lnf_id`, `apply-tx` cancels stale intent, persists `phase="skipped"` with `intended=None`, and (when `phase == "selecting"`) rolls back only keys still holding this transaction's partial `intended` value while preserving any later user choice. Added exact reproductions in `dev/test-install.sh` for both `phase=captured` (`#141a`, switched to Breeze + `breeze`) and `phase=selecting` (`#141b`, partial KDE/GTK 3 Lavender switched to Breeze + KDE `Adwaita`: KDE keeps `Adwaita`, partial GTK 3 rolls back to `breeze`, GTK 4 stays `breeze`, `phase=skipped`).
- **#127 (P1) — Require complete advertised artwork for outside copies:** Updated `cand_is_independent_and_complete` in `scripts/icon_prefs.py` so when `outside_only=True` (authorizing deletion of managed packages), every directory listed in `Directories` of both the outside candidate's `index.theme` and the managed package's reference `index.theme` must actually exist on disk, resolve outside `forbidden_roots`, and contain at least one readable `.svg`/`.png` artwork file resolving outside `forbidden_roots` (while still rejecting any symlink inside `Directories`/`ScaledDirectories` pointing into `forbidden_roots`). Verified empirically that built `WhiteSur-lavender*` themes have 43/43 populated `Directories`, and added an exact real-size reproduction in `dev/test-install.sh` where `~/.icons/WhiteSur-lavender/index.theme` alone (zero artwork dirs) is rejected by `uninstall.sh` with the managed base and its Lavender `folder.svg` kept intact.
- **#131 (P2) — Capture and restore pre-adoption modes and POSIX ACLs regardless of legacy backup permissions:** `read_all_current_prefs` in `scripts/icon_prefs.py` now captures mode bits and serialized POSIX ACL xattrs (`system.posix_acl_access` / `system.posix_acl_default`) for all six config files into `$state/icon-adoption`. `apply_file_perms` also strips stale ACLs when the captured file had none, and `prepare-restore` (`apply_captured_perms_if_needed`) stages and restores captured pre-adoption modes/ACLs onto restored legacy backup files even when the backed-up icon key already matches the intended value. Added exact reproduction in `dev/test-install.sh` from a genuine `HEAD 8b5c251` `0644` backup (with a legacy ACL on `gtk-4.0/settings.ini` and `gtk-4.0` already matching `breeze`) upgraded from pre-adoption `0600` files (with a custom pre-adoption ACL on `xsettingsd.conf`), confirming upgrade, update, undo, and repeated undo preserve `0600`, retain the pre-adoption ACL, and strip the stale legacy ACL.

### Verification results and limits

- `dev/test_icons_phase1.py`: **74/74 passed** (disposable `/tmp` only).
- `dev/test-install.sh`: **677/677 passed** (+50 new assertions covering exact reproductions of `#127`, `#131`, `#139`, `#140` at all 3 boundaries, and `#141` in both `captured` and `selecting` phases).
- `dev/check-style.sh`: **135/135 pixel exact**.
- `dev/check-quick.sh`: **29/29 passed**.
- **Limits (not runnable in this sandbox):** `dev/check-plasma.sh` and `dev/test-install-live.sh` require nested KWin/Wayland outside the sandbox and must be run from the user's terminal; live HTTPS fetch, running-desktop GTK/KDE sync notifications, and live desktop install/review await the user.

## 2026-11-23, Codex (GPT-6) — targeted verification of WhiteSur #124–138

**Hold the live install.** The full-size upgrade and update passed. Ordinary undo restored both KDE layers and the GTK icon choices, but widened private GTK files when their legacy backup had broader permissions. Two recovery paths can also discard a later choice or restore the older Papirus-Dark. This section covers the uncommitted tree based on `8b5c251`.

### Confirmed blockers

| Finding | File and line | Reproduction and result | Suggested fix |
|---|---|---|---|
| **#139 · P1 · Legacy upgrade changes installed files before saving the icon preferences** | `install.sh:293`, `install.sh:315`, `install.sh:364`, `scripts/icon_prefs.py:666` | Killed the upgrade immediately before the first journal save. The installed global theme already contained the new Lavender default. The committed install-only backup still contained Papirus-Dark, the active desktop still selected Breeze, and no adoption journal existed. Direct undo exited 0 and put Papirus-Dark into GTK 2, 3, 4 and xsettingsd. It also left the backup's inherited Adwaita beneath explicit KDE Breeze. | Capture the selection and legacy-backup decision under the install lock before the first change to installed targets or their record. Exercise a failed capture and direct undo from the committed picker-activated state. |
| **#140 · P1 · A new install can proceed inside an unfinished undo** | `install.sh:325`, `install.sh:393`, `scripts/icon_prefs.py:680`, `uninstall.sh:148`, `uninstall.sh:333`, `uninstall.sh:337` | Killed undo after the merged GTK 3 file was published. KDE and GTK 3 selected Breeze, while GTK 4, GTK 2 and xsettingsd still selected Lavender. Plain install exited 0 with that split and phase `restoring`. In a second run, killed undo after phase `restored` was saved and before the journal was archived. Plain install created a new `TAKEN=install` backup carrying the old restore decision. After choosing Adwaita and changing the panel setting from 42 to 77 on the inactive Platinum installation, undo exited 0 and reverted both edits to Breeze and 42. Immediately after journal archival there is another gap: with the old manifest still present and Platinum reactivated, plain install exited 0 with Breeze and no adoption record. | Retain an uninstall-in-progress marker through package and manifest retirement. At install entry, finish the earlier undo or refuse before writing and tell the user to resume uninstall. A new installation must start a new decision and capture its own preferences. |
| **#127 · P1 · Incomplete outside copy still permits deleting the selected artwork** | `scripts/icon_prefs.py:429`, `scripts/icon_prefs.py:433`, `scripts/icon_prefs.py:451`, `uninstall.sh:504` | The original linked-applications case is fixed. Retested with all three full managed packages and an outside base containing only a genuine copy of their base `index.theme`. KDE and GTK selected Lavender. Undo exited 0 and removed its only artwork. GTK 3 lookup for `folder` and `folder-documents` then returned a built-in image and a Breeze SVG. Both had resolved to real Lavender SVGs before undo. An absent advertised directory never fails the candidate check. | Before authorizing deletion, require the outside copy to supply the selected package's advertised artwork and resolve its dependencies independently. Keep the selected package when the other index has no usable artwork. |
| **#131 · P2 · Legacy backup permissions override the user's current 0600** | `scripts/icon_prefs.py:656`, `scripts/icon_prefs.py:903`, `scripts/icon_prefs.py:1023`, `uninstall.sh:288` | With GTK 3 and 4 private at adoption, install and update kept both at 0600. Undo and repeated undo restored the correct Breeze strings but changed both files to 0644 when the older Papirus-Dark backup was 0644. A 0600 backup passed. Crossed both backup modes with explicit and inherited KDE Breeze. The outcome followed the backup mode in every case. The existing #131 test creates the backup after setting 0600. | Capture the pre-adoption modes and applicable access ACLs. Apply them to the staged files being restored, including cases where the backed-up icon key already equals its intended value. Add a 0644-backup/0600-current regression. |
| **#141 · P2 · A pending selection overrides a later global-theme change** | `install.sh:350`, `install.sh:411`, `scripts/icon_prefs.py:680`, `scripts/icon_prefs.py:723` | Killed the process immediately after saving `captured` or `selecting`. Before retry, switched the throwaway home to the Breeze global theme and selected Breeze icons in KDE and GTK. Plain retry exited 0, left the global theme on Breeze, and switched both icon selections to Lavender. The initial active-Platinum condition is never rechecked. | Re-evaluate the active global theme before resuming selection. Cancel stale intent when the user switched away, preserving their subsequent choices and reconciling any transaction-owned partial writes. |

### Results for each original finding

| Finding | Outcome |
|---|---|
| #124 | Original failed placement plus interrupted legacy undo passed. The persisted restore decision survived replacing the global-theme config. Retry restored Breeze across KDE and GTK. The earlier, pre-capture boundary fails in #139. |
| #125 | A real full-size concurrent save survived after undo removed the base index. Undo reported the personal file. |
| #126 | With only GTK using Lavender-dark, undo retained the dark package and required base. Cleanup succeeded after changing the selection. |
| #127 | The original full outside copy with `apps/` linked into the managed base was refused for removal. Its Firefox icon survived. The incomplete-copy blocker above remains. |
| #128 | First placement failure and read-only GTK 4 both resumed successfully under active Platinum. A later distinct icon choice survived. A changed global theme during a pending selection is covered by #141. |
| #129 | Explicit Breeze with inherited Breeze, explicit Breeze with an absent inherited key, and inherited-only Breeze all restored with the recorded key presence and value. |
| #130 | After displacing the unstamped base and failing placement, direct undo restored all three full-size manual trees and their KDE/GTK Lavender selection. Relative paths, file contents and symlink targets matched the originals. |
| #131 | Private files stayed private through selection and update. Undo was conditional on the older backup mode as detailed above. |
| #132 | Killed standalone replacement after its second old-directory rename, then killed recovery during incoming-directory cleanup. A second recovery left exactly the three original marked directories. |
| #133 | Undo preview with a genuine HEAD backup lacking `kdeglobals` passed and preserved the throwaway-home snapshot. |
| #134 | Primary and linked Git worktrees both refused a stamped destination containing a staged tracked marker. The marker survived. |
| #135 | A held install lock refused a competing run. Hiding `flock` also refused the run with the existing manifest unchanged and no trio placed. |
| #136 | An empty pkg-config package directory caused plain install to fail before fetching or creating install state. The home snapshot remained identical. |
| #137 | A nonexistent TMPDIR caused local fetch to fail before creating the cache parent or temporary directory. |
| #138 | The script header and printed help describe the active-Platinum plain-install icon switch. |

### Transaction boundaries and exact desktop path

- Sent SIGKILL to the disposable installer process group immediately after each of the six real journal phase writes. Compared direct uninstall with another plain install followed by uninstall. With the global theme unchanged, `captured` and `selecting` resumed, `selected` preserved later choices, and `skipped` kept the non-Platinum selection. Direct undo and repeated undo recovered the expected icon keys in all six cases. Retrying plain install after explicitly choosing Adwaita preserved Adwaita in each of the four forward phases.
- Repeated the two recovery routes after individual config publication and immediately after backup retirement. Direct uninstall completed. Switching operations during restore produced #140. The test also covered both sides of the first journal save and both sides of its final archival.
- Created genuine format-4 records and backups with the committed installer in disposable homes. Tested the picker-activated install-only backup and the previously promoted applied backup. At adoption, both used Platinum, KDE and GTK Breeze, GTK 3 and 4 at 0600, and no WhiteSur directories. The older backups used Papirus-Dark. Their file modes were varied deliberately because the actual backup was outside the review.
- Two plain, full-source installs from no-Git project copies fetched `73d8040da51a9ed74e47c7366e7e9ff437601a5c` from the read-only local Git remote. All three directories, their caches and folder icons were present. Both runs selected Lavender. The panel layout, wallpaper selection, cursors, KWin and plasmashell settings, widget style, color setting and GTK font remained unchanged. Updates with an unreachable remote reused the cache and retained the new Adwaita choice. Undo and repeated undo removed the trio and restored the original KDE layers and all four GTK selections. The 0600 historical backup restored private modes. The 0644 historical backup reproduced #131.
- All **63/63** assertions in the targeted installer regression block passed. The independent phase, full-size upgrade and standalone recovery checks above extend that block. The user reports **19/19** Plasma with **0 differing pixels** and **40/40** live-install on this tree. Network access remained off. Running-session notification delivery, the real backup's modes and live HTTPS were outside this verification. No unrelated suites or components were reviewed.

## 2026-11-23, Antigravity (Gemini 4 Neon) — durable icon-selection transaction and fixes for #124–138

Replaced the split icon-selection recovery with one durable v3 transaction (`$state/icon-adoption` via `scripts/icon_prefs.py`) and fixed all 15 findings (`#124–138`) in the working tree (uncommitted). Full-copy + `icons/custom/` retained; nothing installed; `~/.local/share/icons`, the live desktop, and `../WhiteSur-icon-theme` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`) untouched.

### Fixes verified

- **Durable icon-selection transaction (`#124`, `#128`, `#130`):** Replaced split adoption/override logic in `install.sh`, `uninstall.sh`, `scripts/common.sh`, and `scripts/icon_prefs.py` with one fsynced v3 JSON record (`$state/icon-adoption`) storing `phase` (`captured` → `selecting` → `selected` | `skipped` | `restoring` → `restored`), `restore_decision`, `captured` KDE + GTK states, `intended` first-install values, and `preexisting` manual/absent state. Removed redundant bash icon helpers (`read_icon_theme_file`, `effective_icon_selection`, `icon_required_ids`, `icon_theme_exists_outside_data`) and post-restore patching in `uninstall.sh`.
  - **#124 (P1):** `uninstall.sh` persists `phase="restoring", restore_decision="restore_backup"` before touching any config file and merges/validates pre-adoption KDE + GTK icon keys into private staged backup copies (`icon_prefs.py prepare-restore`) before `put_back` publishes them atomically. Even mid-restore interruption never exposes `WhiteSur` or `Papirus-Dark`, and retry always resumes the restore regardless of `TAKEN=install` or the `LookAndFeelPackage` now on disk.
  - **#128 (P2):** `install.sh` resumes `icon_prefs.py apply-tx` whenever `phase in ("captured", "selecting")`, comparing each key against `captured` and `intended` so failed placement or read-only `gtk-4.0/` retries complete cleanly while preserving later user choices once `phase == "selected"`.
  - **#130 (P2):** `icon_can_restore_original` (and `cursor_can_restore_original`) now accepts an empty destination (`[[ ! -e $path && ! -L $path ]]`) in addition to `installed_unchanged`, so direct undo after a post-displacement placement failure restores both the manual trio and its KDE + GTK Lavender selection.
- **#125 (P1) — Unlink verified entries + `rmdir` only:** Removed `shutil.rmtree` from `scripts/manifest_ops.py` (`cmd_clean_dir`). Only verified recorded files/symlinks are unlinked; recorded subdirectories and the target root are removed deepest-first with `os.rmdir`, preserving and reporting any file saved concurrently during removal. Verified with a real-size concurrent-save regression (`personal-note` saved as soon as `index.theme` disappeared).
- **#126 & #127 (P1) — One unified KDE + GTK full-index dependency check:** `scripts/icon_prefs.py` uses one shared `cand_is_independent_and_complete` / `theme_is_usable` check across both restore and removal (`check-surviving`), evaluating KDE (`kdeglobals`, `kdedefaults/kdeglobals`) and all four GTK configs (`gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `.gtkrc-2.0`, `xsettingsd/xsettingsd.conf`) and resolving every directory advertised in `index.theme` (`Directories` / `ScaledDirectories`) plus symlinks inside them against planned removals. Verified both GTK-selected `WhiteSur-lavender-dark` retention (`#126`) and rejection of an `~/.icons/WhiteSur-lavender` copy with only `apps/` linked to the managed base (`#127`).
- **#129 (P2) — Independent KDE layer restoration:** `prepare-restore` restores presence and value in `kdeglobals` and `kdedefaults/kdeglobals` independently (validating fallback visibility), so explicit `breeze` never hides stale inherited `Adwaita` from an older backup. Verified for both explicit+inherited `breeze` and explicit `breeze` + absent inherited key.
- **#131 (P2) — Preserve file modes and POSIX ACLs:** `atomic_write_text` and `kde_set_key`/`kde_delete_key` preserve existing file permissions (`0600` stays `0600`) and POSIX ACL xattrs when replacing config files, and create new settings files with `0600`. Verified across install and undo for `kdeglobals`, `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `.gtkrc-2.0`, and `xsettingsd/xsettingsd.conf`.
- **#132 (P2) — Recovery-interruption-safe standalone publish journal:** `icons/whitesur-lavender.py` records `existed_before` per theme ID and writes fsynced `rolled_back` state before removing private staging directories, so terminating recovery during `incoming` cleanup never deletes already-restored originals on retry. Documented the sequential-rename reader gap in `icons/README.md`.
- **#133 (P2) — Absent planned KDE files represented as `None`:** `prepare-restore --dry-run` and `check-surviving --dry-run` represent absent backup files/directories as `None` (never `Path("")` → `.`). Verified `uninstall.sh --dry-run` against a HEAD backup with `kdeglobals` in `ABSENT`.
- **#134 (P2) — Linked Git worktree protection:** `is_git_worktree` in `icons/whitesur-lavender.py` compares `git rev-parse --show-toplevel` (with `GIT_CEILING_DIRECTORIES`) against `project_real`, enforcing full git-ignore and tracked-file protections in both primary and linked (`git worktree add`) checkouts while keeping extracted source-archive support intact.
- **#135 (P2) — Mandatory `flock` (`util-linux`):** Required `flock:util-linux` unconditionally in `install.sh`, `uninstall.sh`, `scripts/common.sh` (`take_lock`), and `icons/fetch-whitesur.sh`, refusing before creating state or cache entries when `flock` is unavailable.
- **#136 (P2) — Plugin build prerequisites preflight:** Added `preflight_plugin_build` in `install.sh` (before fetching or taking the state lock when building plugins) probing `pkg-config` for `Qt6Core`/`Qt6Gui`/`Qt6Widgets` + executable `moc` (`qt6-base`), `Qt6Quick`/`Qt6Qml` (`qt6-declarative`), `KF6CoreAddons` (`kcoreaddons`), and `/usr/include/KDecoration3` + `-lkdecorations3` linkability (`kdecoration`), naming missing Arch packages with zero home footprint on failure.
- **#137 (P3) — Fetch `TMPDIR` validation and early cleanup trap:** `icons/fetch-whitesur.sh` validates `TMPDIR` before locking and installs its `EXIT` cleanup trap before creating the cache parent or `.WhiteSur-fetch.*` temp directory. Verified nonexistent `TMPDIR` leaves zero cache parent or temp entries.
- **#138 (P3) — Installer header and `--help` accuracy:** Updated `install.sh` header and `--help` output to describe the active-Platinum one-time plain-install `WhiteSur-lavender` icon switch for KDE and GTK.

### Verification results and limits

- `dev/test_icons_phase1.py`: **74/74 passed** (disposable `/tmp` only; adds `#132` interrupted recovery cleanup, `#134` linked worktree protection, and `#137` bad `TMPDIR` zero-footprint checks).
- `dev/test-install.sh`: **627/627 passed** (adds full regression coverage for `#124–131`, `#133`, `#135`, `#136`, `#138`, plus uninterrupted active-Platinum plain-install auto-select and undo).
- `dev/check-style.sh`: **135/135 pixel exact**.
- `dev/check-quick.sh`: **29/29 passed**.
- **Limits (not runnable in this sandbox):** `dev/check-plasma.sh` and `dev/test-install-live.sh` require nested KWin/Wayland outside the sandbox and must be run from the user's terminal; live HTTPS fetch, running-desktop GTK/KDE sync notifications, and live desktop install/review await the user.

## 2026-11-23, Claude (Opus 5.5) — triage of findings #124–138

Read-only triage. No code changed, nothing installed, live desktop untouched. Astra's fault-injection results were accepted and not re-run. Keep holding the live install. #124, #128, and #130 share one root cause: icon selection recovery is spread across several records and phases. Fix them with one small durable icon-selection transaction instead of adding more boundary-specific cases. After that round, use targeted verification of #124–138 and the uninterrupted path rather than another open-ended audit.

## 2026-11-23, Codex (GPT-6) — WhiteSur Lavender upgrade from the committed installer

**Hold the live install.** With Platinum active, Breeze selected and no WhiteSur directories, the uninterrupted upgrade worked. A retry can report success with an incomplete selection. An interrupted undo can expose the older GTK setting and, on one legacy-record path, leave it there permanently. The following findings are open against the working tree based on `8b5c251`.

### Confirmed findings, ranked by severity

| Finding | File and line | Failure and how it was confirmed | Suggested fix |
|---|---|---|---|
| **#124 · P1 · Interrupted undo can retire the backup with the wrong preferences active** | `uninstall.sh:147`, `:249`, `:275`, `:309`; `install.sh:335`, `:349` | Made a genuine HEAD plain-install backup containing KDE `WhiteSur` and GTK `Papirus-Dark`. Activated Platinum, selected Breeze and left all three icon paths absent. Failed the upgrade's first icon placement, then stopped undo at the preference helper after it had copied the old settings back. Both records still existed. Retry saw the old global theme and `TAKEN=install`, archived the backup as unused and exited 0 with missing `WhiteSur` in KDE and `Papirus-Dark` in all four GTK settings files. With a completed upgrade and `TAKEN=apply`, the same stop exposed the same wrong settings until the next undo, which did repair them. | Persist the decision to restore before copying the first file. Resume that decision independent of the global theme now on disk. Merge and validate the captured icon keys in staged backup copies before publishing them. Exercise both legacy states with stops before and during preference restoration. |
| **#125 · P1 · Undo deletes a new personal file during removal** | `scripts/manifest_ops.py:338`, `:360`; `uninstall.sh:558` | Ran normal undo on the full theme. From a second process, saved an unrecorded `personal-note` at the base theme root as soon as undo removed its `index.theme`. The save succeeded. Undo exited 0 and the note disappeared. The initial walk had already enumerated the root and the final recursive deletion swept up the new file. | Unlink only verified recorded entries. Remove directories deepest-first with `rmdir`, including the target itself. Preserve and report a directory that becomes nonempty. Add a concurrent-save regression. |
| **#126 · P1 · Undo can delete a theme still selected by GTK** | `uninstall.sh:303`, `:445`, `:463` | On the supported plain-install path with another global theme active, selected Lavender-dark in GTK while keeping KDE on Breeze. Undo exited 0, removed all three packages and left GTK 2, 3, 4 and xsettingsd selecting the missing dark theme. The removal guard reads only KDE. | Evaluate the surviving GTK selections as well as KDE after the planned restore. Keep the selected variant and its base, or restore the applicable recorded GTK preference before removal. |
| **#127 · P1 · A partly shared outside copy still authorizes deletion** | `scripts/icon_prefs.py:352`, `:403`; `uninstall.sh:464` | Made a second, full base theme in the disposable legacy icon search directory, with a real index, places and status, and only its `apps` directory linked to the managed copy. Its Firefox SVG was readable. With KDE selecting Lavender, uninstall exited 0 and removed the managed base. Firefox then disappeared through the surviving copy. The original #115 root and places-link tests both pass. | Use one dependency check in both restore and removal. Resolve the directories advertised by the index and their icon links against the planned removals before counting an outside copy as independent. |
| **#128 · P2 · Retry skips an unfinished first selection** | `install.sh:291`, `:308`, `:330`, `:366`; `scripts/icon_prefs.py:535` | Failed the first base placement after capture. A plain retry installed the full trio but kept Breeze everywhere and left `auto_selected=false`. Separately, made the existing GTK 4 settings directory read-only. KDE and GTK 3 switched before GTK 4 failed. Restored directory permissions and retried. Exit 0, GTK 4/2 and xsettingsd still Breeze, KDE/GTK 3 still Lavender. Subsequent genuine user choices do survive a *completed* adoption. | Persist a pending selection distinct from completed or intentionally skipped adoption. Resume pending writes or roll them back on failure. Preserve later choices by comparing each unfinished key with its captured and intended values. |
| **#129 · P2 · An explicit KDE preference hides a stale inherited key after undo** | `scripts/icon_prefs.py:675`, `:687`; `dev/test-install.sh:1733` | Tested explicit Breeze with inherited Breeze, and explicit Breeze with no inherited key. The older backup had inherited Adwaita. After upgrade, update and undo, both cases had explicit Breeze **and inherited Adwaita**. Repeated undo left that result. Clearing the explicit override would expose a choice absent at adoption. The published explicit-key test reads only the top layer. | Restore presence and value in each KDE file independently. Validate the fallback that would become visible after clearing the explicit override. Cover both combinations and inherited-only Breeze. |
| **#130 · P2 · Direct undo restores the manual trio but loses its selection** | `uninstall.sh:121`, `:126`, `:268`; `scripts/icon_prefs.py:646` | Started with a committed applied record, three distinguishable unstamped full-size manual copies and Lavender selected in KDE and GTK. Failed base placement after the original was moved aside. Direct undo put all three originals back, including their markers, but changed KDE and every GTK selection to Breeze. The empty destination fails `installed_unchanged` even though the saved original can move straight back. | Determine restorability from the planned target occupancy. Count a valid saved original with an empty destination, then verify restoration and effective selection together. |
| **#131 · P2 · Changing an icon key widens private file permissions** | `scripts/icon_prefs.py:57`, `:64`, `:217`, `:281` | Set GTK 3 and 4 settings, GTK 2 gtkrc and xsettingsd config to mode 0600. A successful plain upgrade changed all four to 0644. The replacement helper unconditionally applies its default mode to the new inode. | Preserve the existing file's permission bits and applicable ACLs when replacing it. Give newly created settings a mode that respects the user's privacy. Test modes as well as contents. |
| **#132 · P2 · Interrupting standalone rollback can delete an already-restored theme** | `icons/whitesur-lavender.py:1395`, `:1416`, `:1421` | All nine single process-death probes passed, covering each individual rename for fresh publication and replacement. Then interrupted replacement after the second old directory moved and interrupted recovery during removal of the incoming base. All three original markers were back at their destinations. A second recovery exited 0, deleted the original base and discarded the journal. This concerns standalone output. | Journal the original per-ID state and a rollback-complete phase before cleaning staging. Cleanup retries should only remove private staging. Test termination during recovery itself. Describe the reader-visible gap during the directory switches in the builder documentation. |
| **#133 · P2 · A valid backup can prevent an undo preview** | `scripts/icon_prefs.py:600`, `:619`; `uninstall.sh:262` | Created a committed backup with no `kdeglobals`, then activated Platinum and upgraded. `uninstall.sh --dry-run` exited 1 with “cannot read non-regular KDE config file: .”. Actual undo succeeded. Python turns the empty planned pathname into the current directory. | Represent an absent planned file or directory with `None` and propagate absence through both KDE reads. Test the preview against the actual restore when the old file was absent. |
| **#134 · P2 · Linked Git worktrees bypass tracked-output protection** | `icons/whitesur-lavender.py:955`, `:971`, `:1024` | In disposable primary and linked worktrees at the same commit, staged the same marker under a stamped output trio. The primary checkout rejected that output. The linked checkout took the release-archive branch, built successfully and deleted the indexed marker from the working tree. Its Git directory lives under the common repository's `worktrees/` directory. | Identify the worktree by comparing `git rev-parse --show-toplevel` with the project root. Apply ignore and tracked-file checks to linked worktrees. Retain the separate no-Git archive test. |
| **#135 · P2 · Missing flock silently disables exclusion** | `scripts/common.sh:210`; `icons/fetch-whitesur.sh:137`; `install.sh:56` | Held the actual disposable install-record lock from a separate process. Install with `flock` available refused as expected. With only `flock` absent from the installer's PATH, the same installer exited 0 and placed all three themes while the lock remained held. The fetch helper also conditionally skips its cache lock. | Require `flock` (Arch `util-linux`) before creating state or cache entries, or use a mandatory equivalent. Refuse to run when exclusion is unavailable. |
| **#136 · P2 · Missing plugin build prerequisites pass the clean-system preflight** | `install.sh:56`, `:131`, `:134`, `:171`; `README.md:16` | Kept the compiler and pkg-config executable and pointed pkg-config at an empty package directory in a fresh home. Plain install fetched the pin, built the complete icons, created the state lock and a 12 MiB cache, then failed building the Qt style. This qualifies #118 separately from its now-working icon-tool checks. | Probe the pkg-config modules, moc, and KDecoration headers/library actually used by the three build scripts before fetching or taking the state lock. Name the missing component and package. |
| **#137 · P3 · Fetch setup can leave an abandoned cache temporary** | `icons/fetch-whitesur.sh:174`, `:179`, `:194` | With a nonexistent TMPDIR and no cache, the fetch helper created the cache parent and marked `.WhiteSur-fetch.*` directory, then failed creating its private Git home before installing the exit trap. Both entries survived the failed command. | Validate TMPDIR first and install cleanup before the first persistent allocation, tracking each path as it is created. |
| **#138 · P3 · Installer instructions omit the plain-install switch** | `install.sh:12`, `:16`, `:37` | The script header promises that switching requires `--apply`, and its printed `--help` omits the active-Platinum exception. The plain command changed the KDE and GTK icon selection in the tested setup. The project README describes this correctly. | State the one-time icon switch and its active-Platinum condition in both the header and CLI help. |

### Verification of the earlier findings

| Findings | Independent result on this working tree |
|---|---|
| #101–106, #108–109, #111 | The original builder cases passed, including pre-existing output protection, environment isolation, wrong pin, paths with spaces, changed/missing inputs, suffix selection, KDE launcher sizes, GPL-3.0-only notices and SVG namespaces. The installer digest and export checks precede upstream shell execution. The new linked-worktree and interrupted-recovery cases qualify output safety. |
| #107 | Re-read the five reference pixels in `reference/finder-rename.png` at the coordinates in `docs/REFERENCE.md:229`. The lit edge, upper face, middle face, lower face and rim were `#DDDDFE`, `#BFBFFA`, `#B5B4F9`, `#AEADF7`, `#7E7DD9`. The 32 px WhiteSur exposed face at (16,20) rendered `#B5B4F9`. All 25 × 3 outputs matched independent substitutions from the pinned SVGs. Compare exposed material at 1× and exclude the different silhouettes, shadows and emblems. Upstream's separately named purple icons are expected. |
| #110, #112–114 | Both genuine legacy backup states and ordinary manual adoption passed. The original #112 pre-/post-displacement, orphan-record, #113 backup-promotion and #114 backup-retirement-rename regression cases passed. On a failed retirement both records remained in place. #124, #128 and #130 cover different interruption points. |
| #115, #117 | The originally reported theme-root and places symlinks were rejected. Pure inherited Breeze was restored without an explicit override. Ordinary undo removed stale Papirus-Dark from all four tested GTK files, including the suite's unset-key case. #124, #126–127 and #129–130 qualify broader claims about surviving selections. |
| #116, #118, #121 | An unrelated fetch sibling survived. A verified cache supported a full offline rebuild, and a damaged Git object was rejected by check-only and real fetch. Each of 11 isolated missing-component runs exited 1, named its package and left an empty home unchanged. Tested Git, tar, Python, xmllint, rsvg-convert, gtk-update-icon-cache, both KConfig tools, Python GI, GTK 3 typelib and Pillow with a custom PNG. The icon build requires Python 3.11+, Git, tar, `xmllint` (libxml2), `rsvg-convert` (librsvg), `gtk-update-icon-cache` (same-named package), `gi` (python-gobject) and the GTK 3 typelib (gtk3). Pillow (python-pillow) is conditional on custom PNG input. Both KConfig tools come from kconfig. Local package ownership matched the diagnostics. #135–137 cover the remaining locking, prerequisite and setup failures. |
| #119–120 | Direct and cross-directory alias lookup returned the expected variant bytes in GTK 3. Staged custom additions/overrides and invalid-layer rejections passed. First recovery succeeded at every tested publication rename. #132 affects interruption of recovery. |
| #122–123 | Both absence checks now inspect IDs individually, including dangling links. Full-size HEAD upgrade cases passed, and an offline miss preserved the whole test home. The standalone default and the complete project install worked from a release tree with no project `.git`. A source-directory destination was refused. The archive detection has the separate linked-worktree regression in #134. |

### End-to-end path and limits

- Created the format-4 record and global backup with the committed installer. Tested both an already-applied backup and picker activation of an install-only backup. Started with Platinum, explicit or inherited Breeze, GTK Breeze and zero WhiteSur directories. The synthetic backup used the user's older GTK value. Its KDE values varied deliberately because the contents of the user's real backup were not read.
- From an extracted working tree, plain install fetched `73d8040da51a9ed74e47c7366e7e9ff437601a5c` (tag `2026-09-10`) over local Git transport, compiled the plugins, built the full trio and selected Lavender. Panel layout, wallpaper setting, cursor setting, KWin and plasmashell configuration survived the plain switch. A later plain, full-source update with an unreachable remote used the verified cache and preserved the new Adwaita choice. On the inherited-Breeze path, undo and repeated undo both exited 0, restored Breeze across KDE and GTK, and removed each theme directory. The downloaded cache and dated undo archive remained.
- The full-size install contained 20,326 physical SVGs and 24,284 symlinks, with zero dangling links. All three caches passed validation. Each index had its variant name and inherited `hicolor,breeze`. Each package carried COPYING, AUTHORS and the Lavender provenance notice. The working-tree icon inputs consist of scripts, documentation, pin metadata and empty custom-layer placeholders. Git tracks no upstream tree, generated artwork or reference capture. The prior measured small-overlay rejection still applies to the tested GTK/KDE lookup cases. This turn verified the full-copy output and custom layer, and did not repeat the overlay experiment.
- Re-ran **68/68** selected icon checks and **90/90** selected install assertions in addition to the independent cases above. Used an existing commit for the wrong-HEAD fixture and omitted three synthetic-release checks that would create a commit. The user's terminal results on this tree are **19/19** Plasma, **0 differing pixels**, and **40/40** live-install. Did not independently repeat those suites or the unrelated widget/Quick suites. The tests observed on-disk KDE and GTK state. The sandbox refused the private D-Bus socket, so running-app notifications, GTK session synchronization, and live HTTPS remain unverified. The real home was hidden during installer tests and the upstream clone was read-only. No suspected issue is included in the findings.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fix WhiteSur Lavender #112–123, remaining #110 paths, and active-Platinum auto-select

Fixed and verified all 12 findings from Astra's independent review (`#112–123`), remaining `#110` adoption/undo paths, and the new active-Platinum one-time plain-install auto-select requirement in three tested batches (blockers → `#122` test hardening & upgrade/recovery/auto-select tests → `#116`, `#118–121`, `#123`). Nothing installed on the live desktop; `~/.local/share/icons` and `../WhiteSur-icon-theme` untouched; uncommitted.

### Fixes verified

- **#112 (P1) — Atomic displacement rollback & earliest-completed original:** `displace_foreign` (`scripts/common.sh`) rolls back `manifest_add displaced` and removes the empty holder directory if `mv "$path" "$saved"` fails. Added `reconcile_displaced` (called by both `install.sh` and `uninstall.sh` after `remove_temporaries`) to drop incomplete pre-rename `displaced` entries left by an abrupt kill before `mv`. `uninstall.sh` computes `first_aside[$path]` from the earliest **completed** displacement (`[[ -e $saved || -L $saved ]]`), so an incomplete record can never demote the real manual original to `later-versions`. Tested failures on both sides of the first rename (pre-rename `mv` failure, simulated abrupt pre-rename orphan record, and post-rename `place_dir` failure) across direct undo and retry+undo.
- **#113 (P1) — `backup_predated` covers picker-promoted HEAD backups:** `install.sh` computes `active=$(active_lnf)` and `taken=$(backup_taken || true)` before capturing `$icon_adoption`, setting `backup_predated=true` for both `taken == apply` and `taken == install && active == platinum.desktop`. Tested with genuine `git archive 8b5c251` full-size installs in both `TAKEN=apply` and `TAKEN=install`+picker states.
- **#114 (P1) — Keep `$icon_adoption` until backup retirement succeeds:** `uninstall.sh` applies `scripts/icon_prefs.py restore` with `$icon_adoption` in place, runs `mv -T "$backup" "$keep/original"` first, and moves `$icon_adoption` to `$keep/icon-adoption` only after the backup rename succeeds. Tested by failing `mv -T "$backup" "$keep/original"`, confirming both `$backup` and `$icon_adoption` stay in `$state/`, and verifying retry restores pre-adoption KDE and GTK preferences cleanly.
- **#115 (P1) — Symlink-resolving outside-copy check:** Replaced root-only directory comparison in `icon_theme_exists_outside_data` (`scripts/common.sh`) with `scripts/icon_prefs.py has-outside-copy`, which resolves each candidate theme directory, `index.theme`, `places`, and `status/32` via `Path.resolve(strict=True)` and rejects any candidate resolving into any managed `$data/icons/WhiteSur-lavender*` directory. Tested `~/.icons/WhiteSur-lavender -> $data/icons/WhiteSur-lavender` and `~/.icons/WhiteSur-lavender-light/places` pointing into managed base.
- **#117 (P2) & active-Platinum one-time auto-select — Separate KDE (explicit vs. inherited) + GTK icon preference handling:** Added `scripts/icon_prefs.py` (v2 JSON `$state/icon-adoption`, backward-compatible with v1). Captures exact key presence/values for `kdeglobals`, `kdedefaults/kdeglobals`, `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `.gtkrc-2.0`, and `xsettingsd/xsettingsd.conf` before icon placement or switching. On undo when `backup_predated=true`, restores exact explicit vs. inherited KDE keys (never converting inherited `kdedefaults` into an explicit `kdeglobals` override) and exact GTK keys (including clearing stale `Papirus-Dark`/`WhiteSur` keys when pre-adoption GTK had the key unset), checking theme usability (`theme_is_usable`) so neither KDE nor GTK ever selects a missing theme. When Platinum is already the active global theme, a plain `install.sh` (without `--apply`) takes/retains `$backup` first and selects `WhiteSur-lavender` once for both KDE and GTK without touching panels, wallpaper, cursors, or `kwinrc`; later plain updates keep whatever icon theme the user picks afterwards; non-Platinum plain installs never change icon selection.
- **#122 (P2) — Per-ID absence assertions & real HEAD upgrade coverage:** Replaced all multi-operand `! ls -d` assertions in `dev/test-install.sh` (`theme_files_gone`, finding 40, and all `#110` undo checks) and `dev/test-install-live.sh:284` with per-ID `[[ ! -e $p && ! -L $p ]]` checks (`icons_absent`), upgraded offline-miss verification to full `snapshot` equality, and added genuine HEAD `8b5c251` full-size upgrade tests in both legacy backup states plus `#112`, `#114`, `#115`, `#117`, `#118`, and active-Platinum auto-select tests.
- **#116 (P2) — Per-cache `flock` & owned pending temp cleanup:** `icons/fetch-whitesur.sh` serializes fetches per cache path with a private `/tmp/macos9-whitesur-locks-<uid>/fetch-<sha256>.lock` `flock`, never wildcard-deletes `.WhiteSur-fetch.??????`, cleans only an owned temp path recorded in its uid-owned pending file (with marker), and removes empty newly-created parent dirs on failed fetches. `install.sh` runs `fetch-whitesur.sh` before `take_lock`, so offline misses leave `$HOME` byte-for-byte unchanged (`snapshot`). Tested that unrelated `.WhiteSur-fetch.mydata` survives untouched.
- **#118 (P2) — Shared preflight naming Arch packages before locks/fetches/writes:** Added `--preflight [CUSTOM_DIR]` to `icons/whitesur-lavender.py` (checks `python3 >= 3.11` / `python`, `git` / `git`, `tar` / `tar`, `xmllint` / `libxml2`, `rsvg-convert` / `librsvg`, `gtk-update-icon-cache` / `gtk-update-icon-cache`, `gi` / `python-gobject`, `Gtk 3.0` / `gtk3`, and conditional `PIL` / `python-pillow` when custom PNGs exist) and `need_pkg` in `scripts/common.sh` (checks `g++`, `pkg-config`, coreutils, `kreadconfig6`/`kwriteconfig6` (`kconfig`), and `plasma-apply-lookandfeel` (`plasma-workspace`)). Runs before `take_lock`, `remove_temporaries`, fetching, or any writes in `install.sh`, `uninstall.sh`, and `icons/build-whitesur-lavender.sh`. Documented in `README.md` and `icons/README.md`.
- **#119 (P2) — Cross-directory custom variant aliases & byte-level GTK verification:** `apply_custom_layer` (`icons/whitesur-lavender.py`) detects cross-directory custom aliases (including alias chains) whose logical target differs in `-light` or `-dark`, materializes the alias's symlinked ancestor directory in that variant, and writes the alias there so relative targets resolve to the variant override. `verify_staged_build` verifies both resolved target paths and GTK3 lookup bytes match the expected variant bytes.
- **#120 (P2) — Journaled recoverable standalone publication:** `publish_trio` (`icons/whitesur-lavender.py`) writes an fsynced `.whitesur-lavender-publish.json` journal under the destination `flock` (`staging` → `switching` → `committed`) and reconciles any incomplete transaction automatically on the next `--publish` (and explicitly via `--recover-dest`). Tested abrupt process exit (`os._exit(99)`) right after the first rename for both `--recover-dest` rollback and automatic recovery on the next publish, leaving zero leftover incoming/rollback/journal files.
- **#121 (P2) — Full `git fsck --full --no-progress`:** Replaced `--connectivity-only` in both existing-cache and post-fetch verification in `icons/fetch-whitesur.sh` with `git fsck --full --no-progress`. Verified by corrupting a packfile/object in a bare cache at the pinned commit: both `--check-only` and real fetch reject it as corrupt without touching installed themes.
- **#123 (P3) — Extracted source-archive standalone default:** `validate_destination` and `validate_proposed_pin_path` (`icons/whitesur-lavender.py`) detect whether `$project` is a git worktree (`GIT_CEILING_DIRECTORIES` + `rev-parse --absolute-git-dir`). Inside a git checkout, all existing git-ignore/untracked checks stay enforced; from an extracted source archive without `.git`, `dev/build/...` (including default `dev/build/icons`) and external output paths succeed while source directories, `reference/`, and upstream remain rejected. Documented in `icons/README.md`.

### Verification results and limits

- `dev/test_icons_phase1.py`: **71/71 passed** (disposable `/tmp` only; includes `#116`, `#118`, `#119` GTK3 byte check, `#120` abrupt-exit recovery, `#121` corrupt packfile `git fsck --full`, and `#123` extracted source-archive build).
- `dev/test-install.sh`: **564/564 passed** (full-size HEAD `8b5c251` upgrades in both `TAKEN=apply` and `TAKEN=install`+picker states, `#112` both sides of first rename + orphan record, `#114` exact backup-rename boundary, `#115` `~/.icons` symlinks, `#117` inherited KDE + GTK unset/set + missing-theme fallback, `#118` preflight zero-footprint, `#116` `.WhiteSur-fetch.mydata` preserved, `#122` per-ID absence + offline-miss full `snapshot`, and all active-Platinum plain-install auto-select cases).
- `dev/check-style.sh`: **135/135 pixel exact**.
- `dev/check-quick.sh`: **29/29 passed**.
- **Limits (not runnable in this sandbox):** `dev/check-plasma.sh` and `dev/test-install-live.sh` require nested KWin/Wayland outside the sandbox and must be run from the user's terminal; live HTTPS fetch and live desktop install/uninstall/visual review await the user.

## 2026-11-23, Claude (Opus 5.5) — spot-check of findings #112–123

Read-only check of the working tree. No code changed, nothing installed, live desktop untouched.

- **Confirmed by reading the cited code:** #114 (`icon-adoption` moves before the backup retirement), #116 (name-only cleanup of `.WhiteSur-fetch.??????`), #118 (`need` omits the icon tools), #121 (`fsck --connectivity-only`), and #122 (one negated `ls` across all three IDs).
- **#117 applies to the real setup:** the live state backup contains `gtk-icon-theme-name=Papirus-Dark`, so restoring it without separate icon-preference handling would not restore the current GTK selection.
- **Accepted from Astra's fault-injection evidence, not re-run:** #112, #113, #115, #119, #120, and #123.
- Treat #112–115 and #117 as blockers for running the new installer on the live desktop.

## 2026-11-23, Codex (GPT-6) — independent WhiteSur install and recovery review

Reviewed the working tree, including untracked files, against `8b5c251`.
Used the actual HEAD installer to create format-4 records, the working-tree
installer for upgrades, disposable homes, and WhiteSur `73d8040` as the
local fetch source. The real home was hidden during the install tests.
The manual test copies were unstamped. All three had distinguishable
contents. Old `WhiteSur` directories were absent.

### Confirmed findings, ranked by severity

| Finding | File and line | Concrete failure and confirmation | Suggested fix |
|---|---|---|---|
| **#112 · P1 · Manual original gets classified as a later edit** | `scripts/common.sh:604–606`, `uninstall.sh:548–577` | Failed the first move of the manual base after the displaced entry was recorded. The original was still in place. Retrying install succeeded. Undo and repeated undo both exited 0, but the manual base disappeared from the icons directory. Its marker survived only under `later-versions`. The first recorded backup slot was empty and the second held the actual original. | Reconcile incomplete moves before recording another displacement. Preserve the earliest **completed** displacement as the original. Test a failure on each side of the first rename, including direct undo and install retry. |
| **#113 · P1 · A legacy install-only backup can undo to a missing WhiteSur** | `install.sh:302–305,338–345` | Started with HEAD's plain install, activated Platinum through the equivalent on-disk picker state, then selected manual Lavender. The upgrade recorded `backup_predated=0` before promoting that same old backup from `install` to `apply`. Undo restored the three directories byte for byte but wrote `Theme=WhiteSur`. That ID did not exist. Repeat undo exited 0. | Base adoption on which existing backup the upgrade will actually retain, including the picker-promotion branch. Cover a genuine HEAD record in both backup states. |
| **#114 · P1 · Interrupted undo forgets the adoption selection** | `uninstall.sh:242–250` | Stopped the backup-directory rename immediately after uninstall moved `icon-adoption` to the archive. The backup remained active. On retry, uninstall replayed the old config, had no adoption record to reapply, restored the original trio and exited 0 with the nonexistent `WhiteSur` selected. | Keep the adoption record available until the backup retirement is durable, or journal both steps and resume them together. Test retry at this exact boundary. |
| **#115 · P1 · An alternative search path can refer to the very copy being deleted** | `scripts/common.sh:259–271`, `uninstall.sh:433–435` | In a disposable home, a theme-level symlink in `~/.icons` pointed to the managed base. It satisfied the “outside” check. With Lavender selected, uninstall exited 0, deleted the target and left a dangling alias and an unusable selection. The code compares the search-directory roots but only checks readability of each candidate index. | Resolve each candidate package and its required base. Only count a complete independent copy that will survive the planned removals. |
| **#116 · P2 · A cache miss deletes entries based solely on their names** | `icons/fetch-whitesur.sh:103–111` | A normal successful local fetch removed an unrelated sibling directory named `.WhiteSur-fetch.mydata` and its marker. The deletion needs neither an ownership record nor a cache lock. Concurrent standalone fetches also use that same wildcard. | Remove only the current process's private temporary. For crash recovery, serialize per cache and clean only verifiably owned, abandoned entries. |
| **#117 · P2 · Undo loses inherited and GTK icon preferences** | `install.sh:312–316`, `uninstall.sh:191–238`, `scripts/common.sh:175–180` | With a pre-existing applied Platinum backup, adoption correctly recorded an inherited Lavender setting. Undo put an explicit override in `kdeglobals` and removed the inherited key, so future global-theme changes cannot replace it normally. In another run, KDE and GTK 3 both selected manual Lavender at adoption. Undo restored KDE Lavender but left GTK's on-disk `gtk-icon-theme-name=WhiteSur`. Both tests exited 0. | Restore the presence, value and source of the icon keys separately from the older global backup. Preserve the pre-adoption GTK icon preference where restoring older GTK config would otherwise revive a deleted theme. Test both config layers and GTK settings. |
| **#118 · P2 · Dependency checks happen after persistent changes** | `install.sh:55–58,91–97,122–155,295–301`, `icons/whitesur-lavender.py:235–262,1102–1105`, `icons/README.md:39` | Five missing icon requirements passed dry-run with the shipped empty layer. Each real run created the state lock and populated the bare cache before failing. With an existing KDE config and missing `kreadconfig6`, plain install had already placed the plugins, cursors, wallpapers and global theme before claiming “nothing was installed”. Exact cases below. | Share one prerequisite check between standalone build and install. Run it before taking the lock, removing old temporaries, fetching or placing files. Check usable tools and GTK 3 imports, plus Pillow when a custom PNG needs decoding. Preflight the KDE reader for adoption and the writer for undo. Print the missing component and Arch package. Document them in the install and icon instructions. |
| **#119 · P2 · A shared alias can bypass a light-only override** | `icons/whitesur-lavender.py:428–459,1033–1042,1120–1129` | Built a real trio with an all-layer app and a relative alias to it from `places/scalable`, then gave the app different light and dark artwork. All three passed verification. GTK loaded the light artwork by the direct name, but the light alias resolved through shared `places` to the **base** artwork. The dark and base alias results were correct. | Materialize or rebind aliases whose effective target changes in a variant, including across directories. Verify that lookup by alias resolves to the intended variant target or matching bytes. Checking that it resolves somewhere inside staging misses this case. |
| **#120 · P2 · Standalone publication leaves a partial trio after abrupt exit** | `icons/whitesur-lavender.py:1180–1208` | Stopped the publisher immediately after its first old-directory rename. Only light and dark remained at the advertised paths. A later successful publish restored three names but left the abandoned incoming and rollback directories. The exception handler handles ordinary exceptions and cannot run on unconditional process termination. Project install builds into private staging, so this result concerns standalone rebuilds of an existing output. | Use one atomic switch for complete generations or a recoverable publish journal under the destination lock. Reconcile incomplete transactions before the next build and test process death between renames. |
| **#121 · P2 · Cache validation reports a corrupt blob as healthy** | `icons/fetch-whitesur.sh:86–95,135–138` | Truncated one non-executable SVG blob in a disposable bare cache at the correct commit. `--check-only` exited 0 with `CACHED`. Full Git object verification exited 3 and named the corrupt blob. Both fetch paths use connectivity-only checking. The separate SHA-256 check on the installer is effective. | Check object contents for the pinned history on cache creation and before trusting a suspect cache. Diagnose corrupt cached objects distinctly from offline misses and keep installed themes intact. |
| **#122 · P2 · Undo tests pass with theme directories still installed** | `dev/test-install-live.sh:284`, `dev/test-install.sh:1031,1136,1213,1246–1248,1299` | The negated `ls` assertion exited 0 with the base still present and the two variants absent. It proves only that at least one operand is missing. The first full-size undo checks config only. The “home unchanged” offline-miss assertion checks only the final cache path. The adoption test at line 1038 starts with the new installer and edits its record to resemble an old one. | Assert absence of each ID independently, including dangling symlinks. Snapshot the home for a no-change assertion. Keep the tiny fixture for other scenarios and add full-size HEAD-to-working-tree adoption, both legacy backup states, first-displacement failure, and interrupted undo. |
| **#123 · P3 · The advertised standalone default fails from a source archive** | `icons/whitesur-lavender.py:837–852,883–907`, `icons/README.md:39–47` | From an extracted working-tree release with no project `.git`, standalone build with its default output returned 1 because Git could not establish that `dev/build/icons` was ignored. The full **project installer worked** from that same archive using an external temporary output. | Document an external destination for standalone archive users or choose an archive-safe default. Keep the existing Git safeguards for checkouts. |

### Dependency masking and archive install

Each component below was hidden separately inside the sandbox. Tests used
the actual installer, a fresh home and a local file remote. Unless specified,
the shipped custom layer was empty. Package names are from the local Arch
package database. “Cache + lock” means the verified-source cache directory
and installer state lock existed after failure. No icon theme had been placed.

| Missing component | Arch package | Observed result |
|---|---|---|
| `git` | `git` | Dry and real runs exited 1 before writes and named `git`. |
| `python3` | `python` | Both exited 1 before writes and named `python3`. The format-4 helper also uses Python 3.11+'s `hashlib.file_digest` at `scripts/manifest_ops.py:62`. |
| `xmllint` | `libxml2` | Dry-run passed. Real run exited 1 with a Python `FileNotFoundError` naming `xmllint`. Cache + lock remained. |
| `rsvg-convert` | `librsvg` | Dry-run passed. Real run exited 1 with `FileNotFoundError` naming `rsvg-convert`. Cache + lock remained. |
| `gtk-update-icon-cache` | `gtk-update-icon-cache` | Dry-run passed. Upstream assembly then reported “command not found”. Cache + lock remained. |
| Python `gi` | `python-gobject` | Dry-run passed. Post-build verification raised `ModuleNotFoundError: gi`. Cache + lock remained. |
| GTK 3 introspection data | `gtk3` | With `gi` available, dry-run passed. Verification raised “Namespace Gtk not available for version 3.0”. Cache + lock remained. |
| Python `PIL.Image` | `python-pillow` | **Conditional.** With no custom PNG, dry-run and real install succeeded without Pillow. With one valid custom PNG, both failed before state/cache writes with `ModuleNotFoundError: PIL`. |
| `kreadconfig6` during adoption | `kconfig` | Existing `kdeglobals` triggers this dependency even for plain install. Masking it with otherwise valid prebuilt inputs left installed components in the disposable home. The error reported a config-read problem. `kwriteconfig6`, from the same package, is used to restore selections at `uninstall.sh:237`. |

The icon shell pipeline also uses Bash, GNU coreutils, tar and sed. These
are ordinary base-system prerequisites, distinct from Qt/KDecoration plugin
compilation and the Plasma apply command. A working-tree tar export, extracted
away from any project Git repository, completed a plain install with no
prebuilt inputs. It fetched locally, compiled the plugins, built the real
trio, and completed undo and repeated undo. HTTPS transport was not exercised.

### Previous findings and clean checks

| Finding | Independent result |
|---|---|
| #101 | Unowned output was refused with its marker intact. Abrupt standalone publication remains open under #120. |
| #102, #104 | Exported `remove=true` and an alternate name had no effect on the upstream script. Relative source/output paths and spaces in TMPDIR and output built exactly the three expected IDs. |
| #103, #105, #106 | The builder archives the full pin. The patched installer uses a literal Lavender suffix. A missing folder, changed folder digest, and changed installer were each rejected in a disposable export. The installer digest is verified before invoking its shell. Cache-blob coverage is separately tracked in #121. |
| #107–109, #111 | All 75 asset/variant combinations matched independently recolored upstream bytes. The rendered 32 px face at (16,20) was `#B5B4F9`; the reference light/body/rim samples were `#DDDDFE/#B5B4F9/#7E7DD9`. The verified build used the KDE launcher at panel sizes, included the three provenance files per theme and passed all three cache checks. All 20,326 physical SVGs had the SVG namespace. All 24,284 physical symlinks resolved inside the trio. Index names matched and inheritance was `hicolor,breeze`. |
| #110 | The ordinary full-size upgrade from HEAD's applied format-4 backup preserved selection on install, handled a repeated update, and restored the three unstamped originals exactly by path, content and symlink target. Repeat undo exited 0. #112–115 and #117 prevent general closure. The generated and shipped Plasma defaults both select `WhiteSur-lavender`. |

The thin-overlay rejection is supported for the tested design. Independent
GTK 3 and KF6 `KIconLoader` probes returned the scalable color folder at
16/22/24 px in the overlay and the correct fixed-size files in the full
theme. KDE used generic `folder.svg` for `folder-blue@64` in the overlay;
GTK found the named upstream blue folder. Both loaders picked light
`edit-copy` and trash with Lavender-first dark inheritance, and blue folders
with the dark parent first. The previous report's statement that every small
name resolved to literal `folder.svg` was too broad: `folder-documents` and
`user-home` resolved to their own **scalable** files. Extra picker IDs and
same-name package conflicts follow from installing the three visible parents;
they were not independently observed in a live picker. These distinctions
do not change the decision to keep full copies.

The user's terminal results are 19/19 Plasma, zero differing pixels, and
40/40 live-install. Independent checks here used filesystem snapshots,
isolated program runs and offscreen icon loaders. The real desktop,
real install record, real manual icons, live GTK resynchronization, and
live HTTPS were not inspected. The full five-suite run was not repeated.
No suspicions are counted as findings.

## 2026-11-23, Antigravity (Gemini 4 Neon) — custom icon layer, overlay evaluation, auto-fetch cache & fast test-install fixture

Implemented the tracked `icons/custom/` override layer, empirically evaluated a
small-overlay architecture in both GTK3 and KDE `KIconLoader` (retaining
full-copy + custom layer), added automatic pinned-commit WhiteSur fetching and
caching in `install.sh`, and reduced `dev/test-install.sh` runtime and write
volume with a tiny fixture plus real-size round-trip tests (all uncommitted).
Nothing was installed, committed, or pushed; `~/.local/share/icons`, the live
desktop, and `../WhiteSur-icon-theme` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`)
were untouched.

### 1. Small-overlay evaluation (GTK3 `Gtk.IconTheme` & KDE `KIconLoader`)

Tested a thin overlay (`WhiteSur-lavender` with the 25 recolored SVGs + 72
`places/scalable/` aliases inheriting upstream `WhiteSur`, and
`WhiteSur-lavender-dark` tested with both `Inherits=WhiteSur-lavender,WhiteSur-dark`
and `Inherits=WhiteSur-dark,WhiteSur-lavender`) against the full-copy build
using both GTK3 and a compiled `KF6IconThemes` (`KIconLoader`) probe. Four
reproduced failures rule out the small overlay:

1. **Size vs. theme precedence breaks 16/22/24 px icons (GTK3 & KDE):**
   In the overlay, `folder@16`, `folder@22`, `folder@24`, `inode-directory@16`,
   `folder-documents@16`, and `user-home@16` all resolved to
   `WhiteSur-lavender/places/scalable/folder.svg` (64 px color folder) instead
   of crisp monochrome `places/{16,22,24}/*.svg` in both GTK3 and KDE, because
   the Freedesktop Icon Theme Spec searches every directory of the active theme
   before descending into `Inherits=` (affecting 19 icons at 16 px and 15 each
   at 22/24 px, plus any future custom scalable icon).
2. **KDE prefix fallback hijacks named upstream icons:**
   In `KIconLoader`, `folder-blue@64` resolved to
   `WhiteSur-lavender/places/scalable/folder.svg` (stripping `-blue` within the
   active theme before checking `Inherits=WhiteSur`), whereas full-copy
   resolves `folder-blue` cleanly.
3. **`WhiteSur-lavender-dark` inheritance conflict:**
   With `Inherits=WhiteSur-lavender,WhiteSur-dark`, depth-first traversal into
   `WhiteSur-lavender -> WhiteSur` resolved `edit-copy@16` and `user-trash@64`
   to light `WhiteSur` icons (never reaching `WhiteSur-dark`). Reversing to
   `Inherits=WhiteSur-dark,WhiteSur-lavender` resolved `folder@64` to upstream
   blue `WhiteSur-dark`.
4. **Picker clutter and undo collision:**
   Installing upstream `WhiteSur*` adds 3 extra blue themes to Plasma's picker
   and collides with any user-installed `WhiteSur` during adoption/undo.

**Decision:** Retain the full-copy trio with the tracked `icons/custom/` layer.

### 2. Tracked custom icon layer (`icons/custom/{all,light,dark}/`)

- Added `icons/custom/README.md` and tracked `all/`, `light/`, and `dark/`
  directories (`.gitkeep` ignored at layer root). Documented adding,
  replacing, aliasing, removing, precedence, and validation rules in
  `icons/custom/README.md` and `icons/README.md`.
- `icons/whitesur-lavender.py` validates every custom entry before install/publish
  (allowed `index.theme` directories only; regular `.svg` checked for UTF-8,
  XML, `{http://www.w3.org/2000/svg}svg`, `xmllint --nonet --noout`, and
  `rsvg-convert`; `.png` verified via Pillow; aliases must be relative,
  non-escaping, and resolve without broken links; no dotfiles/directory links).
- Variant-only overrides in `light/` and `dark/` materialize symlinked parent
  directories first (converting them to real directories with relative sibling
  symlinks to `WhiteSur-lavender`) before applying `all/` and variant overrides,
  preventing any cross-variant bleed-through and preserving exact relative
  alias targets, then regenerate and validate `icon-theme.cache` and verify
  GTK3 lookup.
- `icons/review-whitesur-update.sh` adds section `## 7. Custom icon overrides`,
  reporting brand-new icons, unchanged overrides, `UPSTREAM CHANGED OVERRIDDEN
  ICON` (with old/new digest or symlink target), and blocking if upstream
  removes a custom alias target.

### 3. Automatic WhiteSur acquisition & caching (`icons/fetch-whitesur.sh`, `install.sh`)

- Resolution order in `install.sh`: `M9_PREBUILT/icons` (tests) →
  `M9_WHITESUR_UPSTREAM` (read-only explicit local checkout) → bare git cache
  at `${XDG_CACHE_HOME:-$HOME/.cache}/macos9-theme/WhiteSur-icon-theme` via
  `icons/fetch-whitesur.sh` (default remote
  `https://github.com/vinceliuice/WhiteSur-icon-theme.git`, overrideable via
  `M9_WHITESUR_REMOTE` for local fixture tests).
- Fetches only the exact reviewed commit (`git -c core.hooksPath=/dev/null -c
  core.symlinks=false init --bare` + `GIT_TERMINAL_PROMPT=0 git fetch --depth 1
  --no-tags`), verifies `FETCH_HEAD` and `git fsck --connectivity-only`, sets
  detached `HEAD`, and moves atomically into the cache (~11 MiB bare repo; zero
  upstream code executed before `build-whitesur-lavender.sh` verifies all
  pinned digests). Uses `GIT_CEILING_DIRECTORIES` + `--absolute-git-dir` so a
  non-git cache inside an ancestor repo is rejected as corrupt rather than
  inheriting the ancestor's `HEAD`.
- `--dry-run` runs `--check-only` and never downloads or creates cache folders.
  Offline hits reuse the verified cache; offline misses, corrupt caches,
  symlinked caches, wrong-commit caches, and interrupted downloads fail with a
  clear error and zero changes to the installed theme.

### 4. `dev/test-install.sh` runtime & write-volume reduction (before vs. after)

- Tiny 3-theme fixture (`16` files, `3` symlinks, `0.13 MiB`, preserving
  `-light/places` and `-dark/status/32` relative symlinks) runs all 89 general
  install/undo/interruption scenarios; 4 dedicated real-size (`20,344` files,
  `24,284` symlinks, `44,628` entries, `41.78 MiB`) round-trip installs at the
  end exercise full-size install/apply/undo, local-remote auto-fetch, offline
  cache reuse, corrupt/wrong-commit/offline-miss refusals, and custom layer
  overrides.
- **Before** (full-size icons on all 89 installs, 448 checks): **29m 10s**
  (`1,750 s`), **3,971,892** icon entries written (**~3.63 GiB** of icon copies
  + ~400 MiB manifest checksum writes).
- **After** (89 tiny-fixture + 4 real-size installs, 468 checks): **11m 38s**
  (`698 s`, **2.5× faster**, **17m 32s saved**), **180,203** icon entries
  written (**178.7 MiB** — **95.5% fewer icon entries** and **95.2% less icon
  write volume**).

### Suites run and limits

- `dev/test_icons_phase1.py`: **59/59 passed** (disposable `/tmp` only; covers
  `#101–109`, `#111`, update review, custom layer + override reporting + 6
  validation rejections, and `fetch-whitesur.sh` offline/corrupt/wrong-commit/symlink
  cases using a local bare `file://` remote).
- `dev/test-install.sh`: **468/468 passed** (`11m 38s`; private D-Bus,
  throwaway homes, local `file://` fixture remote — zero real network access).
- `dev/check-style.sh`: **135/135 regions pixel exact**.
- `dev/check-quick.sh`: **29/29 Qt Quick checks passed**.
- **Limits:** Nested-KWin/Wayland suites (`dev/check-plasma.sh` and
  `dev/test-install-live.sh`) cannot run inside the sandbox and must run from
  the user's terminal; real HTTPS GitHub fetch and live desktop install/review
  were not run (only local `file://` remote and throwaway homes).

## 2026-11-23, Antigravity (Gemini 4 Neon) — Phase 1 follow-ups & Phase 2 (#110) WhiteSur Lavender integration

Recorded Claude's 2026-11-22 Phase 1 spot-check (reported by user: spot-checked
the poisoned-environment build, output, KDE launcher, and refusal to overwrite
the manual live copy in `~/.local/share/icons`), completed both Phase 1
follow-ups, and fixed `#110` in the working tree (uncommitted). Nothing was
installed, committed, or pushed; `~/.local/share/icons`, the live desktop, and
`../WhiteSur-icon-theme` (`73d8040da51a9ed74e47c7366e7e9ff437601a5c`) were not
modified.

### Phase 1 follow-ups

- **Disposable test suite in repo:** Added `dev/test_icons_phase1.py` (runnable
  with one documented command in `icons/README.md`). Uses only fresh disposable
  `/tmp` directories (never writes to `dev/build/icons/`, `~/.local/share/icons`,
  or `../WhiteSur-icon-theme`). Covers `#101–109`, `#111`, plus the external
  pin and safe update review workflow. Result: **42/42 passed, 0 failed**.
- **Externalized pin & safe upstream update workflow:** Moved all reviewed pin
  metadata and SHA-256 digests out of `icons/whitesur-lavender.py` into
  `icons/whitesur-pin.json`. Added `icons/review-whitesur-update.sh` (one
  documented command taking `<TAG_OR_COMMIT>`). Exports the candidate commit
  into a private temp dir without executing its `install.sh`, reports changes
  across `install.sh` (with unified diff, patch-anchor check, and `bash -n`),
  the 25 `colors/color-purple/` inputs (with dry-run recolor/`xmllint`/`rsvg`),
  launcher files, `COPYING`/`AUTHORS`, symlinks (blocking on absolute/escaping
  links), and the 64 SVG namespace exceptions, then writes a proposed pin JSON
  for manual review (refusing to overwrite `icons/whitesur-pin.json` directly).
  Verified with a simulated release containing an exec-trap in `install.sh`
  (trap never triggered; all changed categories reported; builder refused the
  unreviewed release until pin update).

### Phase 2: #110 · P2 · fixed (working tree)

- **Global theme defaults (`plasma/make-plasma.py`,
  `plasma/look-and-feel/platinum.desktop/contents/defaults`):** Changed only
  `[kdeglobals][Icons] Theme` from `breeze` to `WhiteSur-lavender`. Verified
  `plasma/make-plasma.py` leaves every other file and setting unchanged.
- **Fast O(N) format-v4 manifest operations (`scripts/manifest_ops.py`,
  `scripts/common.sh`):** Added pure-stdlib Python helper preserving format
  version 4 (`macos9-theme-record\t4`) for backward compatibility with existing
  installations while eliminating per-file shell forks and quadratic
  `manifest_has` scans on WhiteSur's 44,619 physical files/links.
  `install.sh` places the three icon themes last (after smaller targets) and
  `uninstall.sh` removes them first and drops their `sum` entries immediately.
  Measured real non-`M9_PREBUILT` throwaway-home round trip (compiling all 3
  C++ plugins + building & verifying WhiteSur Lavender from scratch + 44,619
  checksums): **25.99 s install, 5.07 s uninstall**.
- **Install, adoption, update, and undo (`install.sh`, `uninstall.sh`,
  `scripts/common.sh`):**
  - Added `WhiteSur-lavender`, `WhiteSur-lavender-light`, and
    `WhiteSur-lavender-dark` under `$XDG_DATA_HOME/icons` to `targets`,
    preserving relative symlinks (`cp -RP`) and stripping
    `.macos9-whitesur-lavender-build` before placement so
    `build-whitesur-lavender.sh` still refuses direct overwrites of
    `$XDG_DATA_HOME/icons`.
  - Validates builder/pin/upstream commit before any writes (even on
    `--dry-run`) and builds/verifies the trio before changing any install
    target.
  - Records `$state/icon-adoption` once before adopting Lavender: captures
    `backup_predated` (`1` when an existing Platinum `TAKEN=apply` backup
    predates adoption), `effective_source` (`kdeglobals`/`kdedefaults`/`none`),
    `effective_theme`, explicit `kdeglobals_theme`, `kdedefaults_theme`, and
    `preexisting` (`manual`/`absent`) for each of the three IDs. Preserves
    pre-existing `$state/backup` byte-for-byte untouched.
  - Captures first manual copies of all three IDs in `$displaced` even when
    bytes match the build, and preserves them across repeated updates, local
    edits, and interrupted updates.
  - On `uninstall.sh`: restores `$state/backup` first; when
    `backup_predated=1` and the pre-adoption selection was a manual Lavender
    variant, restores that selection in `kdeglobals` before restarting Plasma
    (without assuming or requiring deleted old `WhiteSur` folders) and retires
    `$state/icon-adoption` into `$keep/`. Inspects the surviving effective icon
    selection (`kdeglobals` + `kdedefaults/kdeglobals`): if a managed variant
    would lose its only usable copy (including base `WhiteSur-lavender` when
    `-light` or `-dark` is selected, or when local edits prevent restoring a
    displaced original), retains the required set with a retryable record.
    Also cleans up `$state/icon-adoption` on early exit after a step-1
    interrupted install (caught and verified by finding 7's step-1 test).

### Suites run and limits

- `dev/test_icons_phase1.py`: **42/42 passed** (disposable `/tmp` only).
- `dev/check-style.sh`: **135/135 regions pixel exact**.
- `dev/check-quick.sh`: **29/29 Qt Quick checks passed**.
- `dev/test-install.sh`: **448/448 passed** (private D-Bus, throwaway homes;
  includes all 367 prior checks + 81 new `#110` checks covering fresh install,
  apply, dry run, live-desktop manual Lavender adoption with legacy `WhiteSur`
  backup and missing old `WhiteSur`, repeated updates, local edits, interrupted
  update recovery, independent selection of `WhiteSur-lavender`, `-light`, and
  `-dark` with base dependency retention, repeated undo, and bad-upstream
  refusal).
- Real non-`M9_PREBUILT` throwaway-home round trip: **PASS** (25.99 s install,
  5.07 s uninstall).
- **Sandbox limits (not verified here — must run from the user's terminal):**
  `dev/check-plasma.sh` failed inside the sandbox due to nested `kwin_wayland`
  / Wayland DRM sandbox restrictions (`dev/shots/plasma-platinum-desktop.png`
  not produced); `dev/test-install-live.sh` (updated with icon install/apply/undo
  assertions) has the same nested-KWin requirement and was not run in the
  sandbox. Physical-display visual review and live desktop install remain
  untouched and unverified.

## 2026-11-22, Antigravity (Gemini 4 Neon) — Phase 1 WhiteSur Lavender builder fixes (#101–109, #111)

Fixed and verified all ten Phase 1 builder findings (`#101–109`, `#111`) in
`icons/whitesur-lavender.py`, `icons/build-whitesur-lavender.sh`,
`icons/README.md`, and `docs/REFERENCE.md` (working tree, uncommitted). `#110`
was intentionally not started and awaits user approval for Phase 2. Nothing was
installed, committed, or pushed; the upstream clone (`../WhiteSur-icon-theme`,
clean at `73d8040da51a9ed74e47c7366e7e9ff437601a5c`) and `~/.local/share/icons`
were not modified.

### Findings addressed (working tree)

- **#101 · P1 · fixed (working tree).** Rewrote the build pipeline to export,
  patch, assemble, and verify all three themes in a fresh private `0700`
  staging directory before touching `OUTPUT_DIR`. Destination validation runs
  before any writes (and again under an exclusive per-destination `flock` in
  `/tmp/macos9-whitesur-locks-<uid>/`): rejects symlinks anywhere in
  `OUTPUT_DIR` or its existing parent chain, refuses writing into/across the
  upstream clone, refuses project root / `.git` / `reference/` and any
  non-ignored or tracked project path (handling `-light`'s symlinked `places`
  dir on rebuilds), and refuses overwriting any existing `WhiteSur-lavender*`
  directory lacking a valid `.macos9-whitesur-lavender-build` ownership stamp.
  Publish copies into a same-filesystem private `.whitesur-lavender-incoming.*`
  dir, swaps atomically via `os.rename`, and rolls back all three previous
  themes on mid-swap failure. Sets `umask 022` so published dirs are `0755`
  (not world-writable).
- **#102 · P1 · fixed (working tree).** Runs `git`, `tar`, `python3 -I`, and
  upstream `bash --noprofile --norc ./install.sh` under `env -i` with a small
  explicit environment (`PATH=/usr/local/bin:/usr/bin:/bin`, `LC_ALL=C`,
  `LANG=C`, `TERM=dumb`, private `HOME`/`XDG_*`/`XDG_RUNTIME_DIR`/`TMPDIR`, no
  `DISPLAY`/`WAYLAND_DISPLAY`/`DBUS_SESSION_BUS_ADDRESS`/`DESKTOP_SESSION`),
  passes `-n WhiteSur` explicitly, and verifies that staging contains only the
  exact three expected theme IDs before publishing.
- **#103 · P2 · fixed (working tree).** Pins and enforces full commit
  `73d8040da51a9ed74e47c7366e7e9ff437601a5c` (fails if upstream `HEAD` differs),
  archives only that pinned commit (never `HEAD`), reports that single verified
  full commit ID, verifies all 15,971 upstream export symlinks stay inside the
  export root, and rejects symlinked generator inputs/targets.
- **#104 · P2 · fixed (working tree).** Resolves `UPSTREAM_CLONE`, `OUTPUT_DIR`,
  and `TMPDIR` once relative to the caller's working directory, rejects empty
  arguments / unknown options / extra arguments / tabs and newlines, and patches
  upstream `install.sh` quoting on `THEME_DIR`, `${SRC_DIR}/src/status/...`,
  and the `-light`/`-dark` `cd "${dest}"` symlink blocks.
- **#105 · P2 · fixed (working tree).** Pins the exact 25-file manifest,
  per-file SHA-256 digests, and per-file expected source paints in
  `colors/color-purple/`, plus pinned SHA-256 digests for `install.sh`,
  `COPYING`, `AUTHORS`, `plasma/places/{16,22,24}/start-here.svg`, and
  `src/status/32/start-here.svg`. Validates XML syntax, SVG namespace,
  `xmllint --nonet --noout`, `rsvg-convert` rendering, and `bash -n` on patched
  `install.sh` before publishing anything into the export tree (zero leftover
  `colors/color-lavender` on failure). `--verify` checks all 25 final bytes in
  all three themes and GTK3 resolution at 64 px. Updated `icons/README.md` to
  match these exact checks.
- **#106 · P2 · fixed (working tree).** Replaced `THEME_VARIANTS[9]` with the
  literal suffix `themes+=('-lavender')`, matched the full `THEME_VARIANTS`
  declaration plus pinned `install.sh` digest, and verified staged theme IDs,
  `index.theme` `Name`/`Inherits`/directories, and all 25 folder payloads.
- **#107 · P2 · fixed (working tree).** Switched mapping to `#f299ff -> #ddddfe`,
  `#e791f3 -> #b5b4f9`, `#c75cd6 -> #7e7dd9`, and recorded the verified
  `reference/finder-rename.png` crop samples and coordinates in
  `docs/REFERENCE.md`. Visual comparison below.
- **#108 · P2 · fixed (working tree).** Passes `-p` (`--kde-plasma`) to
  upstream `install.sh` for `places/{16,22,24,scalable}/start-here.svg`, AND
  derives `src/status/32/start-here.svg` in the export from upstream's
  `plasma/places/24/start-here.svg` (`width="32" height="32"`, `#f2f2f2` so
  `-light` recolors it to `#363636`) because upstream's `-p` omits `status/32`
  and GTK/KIconLoader resolved 32 px `start-here-kde-plasma` to the Apple logo
  in `status/32/start-here.svg`. Verified all 18 GTK3 lookups (`16, 22, 24, 32,
  48, 64` px across all 3 themes) resolve to KDE Plasma artwork with zero Apple
  logo paths.
- **#109 · P3 · fixed (working tree).** Separated script license
  (`BSD-2-Clause` in `icons/whitesur-lavender.py`,
  `icons/build-whitesur-lavender.sh`, and `icons/README.md`) from derived
  artwork terms (`GPL-3.0-only`, removing the unverified `GPL-3.0-or-later`
  claim). Patched `install.sh` to install verbatim upstream `COPYING`,
  `AUTHORS`, and a dated `LAVENDER-NOTICE.txt` into all three built themes.
- **#111 · P3 · fixed (working tree).** Normalizes all 64 pinned upstream
  `src/` SVGs lacking `xmlns="http://www.w3.org/2000/svg"` in the disposable
  export (each checked with `ElementTree`, `xmllint --nonet --noout`, and
  `rsvg-convert`), and checks XML syntax and `{http://www.w3.org/2000/svg}svg`
  root namespace separately across every physical SVG in the staged trio.
- **#110 · P2 · open (Phase 2).** Not started; awaiting user approval.

### #107 visual comparison (`reference/finder-rename.png` vs rendered 32×32 SVGs on `#FFFFFF`)

Artifacts (ignored, private): `dev/build/icons-compare-107/`
(`folder-side-by-side-1x.png`, `folder-side-by-side-4x.png`,
`user-identity-side-by-side-1x.png`, `user-identity-side-by-side-4x.png`).

- **Reference crop** (`reference/finder-rename.png` x=696–730, y=370–404, white
  `#FFFFFF` backdrop): lit bevel `(704,376) = #DDDDFE` `(221,221,254)`, exposed
  front face `(709,381) = #BFBFFA`, `(711,388) = #B5B4F9` `(181,180,249)`,
  `(717,388) = #AEADF7`, dark edge `(720,385) = #7E7DD9` `(126,125,217)`.
- **`folder.svg` at 32×32 on `#FFFFFF`:**
  - Exposed front face center `(16,20)`: before `#9999FF` `(153,153,255)` (delta
    `(-28, -27, +6)` vs `#B5B4F9`; `tools/compare.py diff` max diff 28) → after
    `#B5B4F9` `(181,180,249)` (delta `(0, 0, 0)`; `tools/compare.py diff` 0/1
    differing px, max diff 0).
  - Exposed front face region (`x=6..25, y=14..24`, excluding backdrop/shadow):
    before R `150–153`, G `150–153`, B `239–255` → after R `174–181`, G
    `173–180`, B `234–249` (matches Finder face range `#AEADF7`–`#B5B4F9`).
  - Upper tab (`x=5..11, y=7..8`): before R `130–134`, G `130–134`, B `215–216`
    → after R `153–156`, G `152–155`, B `210–211`.
  - Bottom rim (`x=6..25, y=25..26`): before R `145–160`, G `145–160`, B
    `242–255` → after R `172–186`, G `171–185`, B `236–249`.
- **`user-identity.svg` at 32×32 on `#FFFFFF`** (exercises `#f299ff → #DDDDFE`
  and `#c75cd6 → #7E7DD9`, excluding white emblem):
  - Upper lit region `(16,4)` vs `#DDDDFE`: before `#C6C6FC` `(198,198,252)`
    (delta `(-23, -23, -2)`) → after `#D7D7FC` `(215,215,252)` (delta `(-6, -6,
    -2)`, error reduced by 17 in R/G).
  - Lower dark rim `(16,29)` vs `#7E7DD9`: before `#6767CC` `(103,103,204)`
    (delta `(-23, -22, -13)`) → after `#7F7ED9` `(127,126,217)` (delta `(+1,
    +1, 0)`, max channel error reduced from 23 to 1).

### Checks run and built trio stats (`dev/build/icons/`)

| Theme ID and index Name | Recolors matched / GTK 64 px | Resolved files | Physical symlinks | Physical SVGs / missing xmlns | Broken or escaping links | Cache validation |
|---|---|---:|---:|---:|---:|---|
| `WhiteSur-lavender` | 25 / 25 | 55,034 | 15,981 | 11,541 / 0 | 0 | passed (1,099,664 B) |
| `WhiteSur-lavender-light` | 25 / 25 | 55,034 | 1,834 | 1,452 / 0 | 0 | passed (1,099,664 B) |
| `WhiteSur-lavender-dark` | 25 / 25 | 55,034 | 6,469 | 7,333 / 0 | 0 | passed (1,099,664 B) |

*(Resolved file count rose by +4 per theme from 55,030 to 55,034 due to
`COPYING`, `AUTHORS`, `LAVENDER-NOTICE.txt`, and
`.macos9-whitesur-lavender-build`; physical SVGs changed from 20,330 to 20,326
and symlinks rose by +4 because `-p` makes `places/scalable/start-here*.svg`
relative symlinks to `../16/start-here.svg` in base and dark.)*

- **Phase 1 automated test suite (`test_icons_phase1.py`): 38/38 passed, 0
  failed** covering: unowned-dir refusal, symlink destination/parent refusal,
  upstream-tree refusal, trackable project/reference/`.git` refusal, pre-fix
  unstamped `dev/build/icons` refusal, 7 bad-input CLI cases, unpinned commit
  refusal, simultaneous spaces in `OUTPUT_DIR` and `TMPDIR` with poisoned env
  (`remove=true`, `name=Hijacked`, `black=true`, `bold=true`,
  `alternative=true`, `DESKTOP_SESSION`, `DISPLAY`, `WAYLAND_DISPLAY`,
  `DBUS_SESSION_BUS_ADDRESS`, `GIT_DIR`, `GIT_WORK_TREE`, `BASH_ENV`),
  relative `UPSTREAM_CLONE` and `OUTPUT_DIR` (`result`), failed rebuilds
  leaving owned output untouched, simulated mid-publish rename failure rollback,
  owned rebuilds (both in scratch and default `dev/build/icons/`), concurrent
  writers serialized via `flock`, all `#103`/`#105`/`#106` direct generator
  fault injections (zero leftover `color-lavender`), shifted `THEME_VARIANTS`
  still producing `WhiteSur-lavender*`, `#111` 20,326/20,326 SVG namespaces +
  negative check, `#108` 18/18 GTK3 launcher lookups, `#109` notices/headers,
  and untouched upstream checkout.
- **Limits:** Sandbox/offscreen verification only; not installed into
  `~/.local/share/icons`; not tested in live Plasma or reviewed on physical
  displays; `#110` install/apply/update/undo integration is pending Phase 2;
  the five unrelated C++/Plasma/installer suites were not re-run because no
  files outside `icons/` and `docs/REFERENCE.md` changed.

## 2026-11-22, Claude (Opus 5.5) — verification of WhiteSur Lavender findings #101–111

Reviewed Astra's findings against the uncommitted `icons/` files. No code changed, nothing installed, live desktop untouched.

- **Reproduced:** #101 and #104 (an output path with spaces failed with exit 2, after the existing theme marker was deleted), and #102 (`remove=true` produced 0 themes, exit 0, and printed "Built").
- **Confirmed in code or built output:** #103, #105, #106 (hard-coded index 9), #107 (measured separately from `finder-rename.png`), #108 (16, 22, and 24 px launcher aliases resolve to `start-here.svg`), #109 (`GPL-3.0-or-later` header), and #110 (`Theme=breeze`, no WhiteSur handling in install, uninstall, or common scripts).
- **Accepted from Astra's evidence, not re-run:** #111 and the fault-injection details for #103, #105, and #106.
- Fix #101 and #102 first. Treat #110 as a separate phase after the builder is safe, because it changes install and undo behavior.

## 2026-11-22, Codex (GPT-6) — WhiteSur Lavender working-tree audit

Reviewed the three uncommitted files in `icons/` on `8b5c251`, decision 7,
the install and undo paths, and the clean sibling WhiteSur checkout. Its
`2026-09-10` tag and detached HEAD both resolve to
`73d8040da51a9ed74e47c7366e7e9ff437601a5c`. Upstream line references
below refer to that revision. Builds and fault tests used disposable exports
and destinations in the network-disabled sandbox.

### Confirmed findings

- **#101 · P1 · open — A rebuild deletes the previous output before it has a replacement.**
  `icons/build-whitesur-lavender.sh:13–15` recursively removes the three IDs
  in any caller-supplied destination. It checks neither ownership nor the
  resolved parent. An ordinary failed build in a scratch destination with
  spaces erased a pre-existing marker and left a base theme, an incomplete
  light theme and no dark theme. A link in the destination's parent chain
  directs the same operations to its target. A custom destination under the
  source repo can also expose artwork to Git (`git check-ignore` rejected
  `icons/WhiteSur-lavender/places/scalable/folder.svg` as an ignored path).
  Build all three in a fresh private staging directory, verify them together,
  and publish with rollback. Resolve and check the destination before any
  writes. Refuse to replace unowned output, to write into the upstream tree,
  or to publish into a trackable project path. Keep manual-copy adoption in
  the project installer. Serialize writers to the same destination.

- **#102 · P1 · open — Inherited shell variables can turn a build into an uninstall.**
  `icons/build-whitesur-lavender.sh:15` changes HOME and unsets the two
  displays but passes the rest of the caller's environment. Upstream
  `install.sh:222,336,341–352` reads `remove` and `name` from that environment.
  Against an empty scratch destination, exported `remove=true` selected
  uninstall for all 30 IDs, returned 0 and printed “Built” with zero output
  themes. The removal branch recursively deletes existing directories.
  In a separate empty destination an exported `name` changed all three output
  IDs and also returned 0. Start the reviewed builder with a small explicit
  environment, fixed tool path, private HOME/XDG/runtime and no session bus.
  Require exactly the expected three IDs before publishing.

- **#103 · P2 · open — The builder executes whichever revision HEAD currently names.**
  `icons/build-whitesur-lavender.sh:11,15–16` archives HEAD, executes the
  exported installer, then queries HEAD again for the success message.
  There is no comparison against the reviewed commit in `icons/README.md:5–6`.
  This follows directly from those three commands. The second query can also
  label the build with a different revision if the checkout moves. Changing
  HOME does not confine the shell's filesystem access. The generator at
  `icons/whitesur-lavender.py:29–33,43–49` follows source links during copying
  and follows the installer path for writing. At the pin the installer and
  25 inputs are regular files, and all 15,971 tracked symlinks resolve inside
  the checkout. No escape was observed. Archive and report one verified full
  commit ID. Make an upstream bump an explicit review of the installer,
  file types and link targets. Reject linked generator inputs or paths that
  resolve outside the export before writing. Restrict build writes to
  staging if executing the upstream script.

- **#104 · P2 · open — Relative paths and paths containing spaces break the build.**
  `icons/build-whitesur-lavender.sh:8–15` interprets a relative output in
  the caller's directory, then passes it to upstream after changing directory.
  With `result` the requested directory ended empty and the command exited 1.
  With an absolute output containing spaces the light build exited 2 at
  upstream `install.sh:108` (unquoted `cd`). With a space only in TMPDIR,
  it exited 1 at upstream line 98 (unquoted source path). Line 177 repeats
  the destination issue. The private export was cleaned up in all three cases.
  Resolve caller paths once, and correct the pinned script's quoting in
  the export or give it controlled, whitespace-free internal paths and
  publish separately. Exercise spaces in both output and TMPDIR.

- **#105 · P2 · open — The palette guard accepts missing, unconverted and malformed assets.**
  `icons/whitesur-lavender.py:33–41` checks the union of three matched
  strings across a glob. In a disposable export, dropping `folder.svg` and
  changing the accent in `folder-cloud.svg` to `#d65fce` let both generation
  and upstream assembly exit 0. All three themes contained the stock folder
  and the unrecolored cloud. A separate truncated SVG passed generation.
  Removing a color everywhere did produce the documented error. That failure
  and a changed installer anchor both left `color-lavender` behind when the
  generator was run directly. Verify the pinned file manifest and each input's
  expected paints or digest, parse and render the products, and check final
  installed paths against the expected bytes. Validate all inputs and patch
  anchors before publishing a complete generated directory and installer.
  Update the guarantee in `icons/README.md:12` to match those checks.

- **#106 · P2 · open — A compatible-looking installer change silently selects Nord.**
  `icons/whitesur-lavender.py:45–48` appends Lavender but selects array
  index 9. Inserting a variant before pink in a test copy preserved every
  text anchor. The generator and installer both exited 0, producing only
  `WhiteSur-nord`, `-light` and `-dark`. Select the literal Lavender suffix
  or resolve it by name. Verify the three resulting IDs, indexes and folder
  payloads before reporting success.

- **#107 · P2 · open — The folder face uses the control palette, visibly darker than the Finder folder.**
  `icons/whitesur-lavender.py:16–17` uses the scroll-box ramp documented at
  `docs/REFERENCE.md:93`. In the native `reference/finder-rename.png` crop
  x=696–730, y=370–404, the body includes `#BFBFFA` at (709,381),
  `#B5B4F9` at (711,388) and `#AEADF7` at (717,388). The light shade is
  `#DDDDFE` at (704,376) and the dark edge is `#7E7DD9` at (720,385).
  Seven 35×35 crops in the capture matched byte for byte, including the
  cited folder. The current scalable WhiteSur `folder.svg` rendered at 32×32
  has an opaque body sample of `#9999FF` at (16,20). Against the middle
  Finder sample its RGB difference is (−28, −27, +6), confirmed by
  `tools/compare.py diff` on the two 1×1 samples.

  | Upstream paint | Current target | Measured folder target |
  |---|---|---|
  | `#f299ff` | `#CCCCFF` | `#DDDDFE` |
  | `#e791f3` | `#9999FF` | `#B5B4F9` |
  | `#c75cd6` | `#6666CC` | `#7E7DD9` |

  Record the folder samples and coordinates in the measured reference when
  fixing this. Render before and after at 1×, using the scalable folder at
  32 px and the same white backdrop as the capture. Put the crops side by
  side and compare RGB ranges in like regions of each shape: exposed front
  face, lit bevel and dark rim. Exclude background, shadows and emblems from
  body samples. Report representative pixels and changes in channel error.
  WhiteSur's silhouette and overlays differ, so a whole-crop difference
  measures geometry as well as color. The plain folder uses only the middle
  source paint. Also render `user-identity.svg`, which exercises the other
  two substitutions. Retain WhiteSur artwork and keep the capture private.

- **#108 · P2 · open — The project's neutral launcher resolves to the Apple logo.**
  `icons/build-whitesur-lavender.sh:15` omits upstream's KDE option.
  The layout requests `start-here-kde-plasma` at
  `plasma/look-and-feel/platinum.desktop/contents/layouts/org.kde.plasma.desktop-layout.js:38`.
  Its 16 px alias resolves to WhiteSur's default `start-here.svg` in the
  generated themes. Upstream identifies that image as the Apple logo at
  `install.sh:34`. A scratch build with `-p` gave the KDE artwork in all
  three aliases, including the expected dark recolor. Pass the KDE option
  or supply the agreed neutral launcher, and check the resolved launcher
  at panel sizes. This finding concerns the built output. Git contains
  no new logo asset.

- **#109 · P3 · open — The artwork license notice claims an unverified grant.**
  `icons/whitesur-lavender.py:7` labels derived WhiteSur artwork
  `GPL-3.0-or-later`, whereas `icons/README.md:4,13` says GPL-3.0.
  The pin includes GPL version 3 in `COPYING` and names Vince Liuice in
  `AUTHORS`. The reviewed material gives no project-specific later-version
  grant for the 25 inputs. The example grant in the license appendix is a
  template. Upstream `install.sh:56` comments out its notices copy, and all
  three outputs lack both files. Identify the generator's own license
  separately, describe only the evidenced artwork terms, and include
  upstream's notices plus source revision and a dated recoloring notice
  with any distributed derivative. This was a private local build.

- **#110 · P2 · open — Install, apply, update and undo have no Lavender integration.**
  `install.sh:192–205` places cursors, wallpapers and the global theme but
  has no icon-theme build or placement. The target list at
  `scripts/common.sh:145–159` has none of the three IDs and
  `uninstall.sh:385–388` skips unrecognized targets.
  `plasma/make-plasma.py:612` emits `Theme=breeze`, confirmed in
  `plasma/look-and-feel/platinum.desktop/contents/defaults:7–8`.
  Consequently a fresh install supplies no Lavender theme, applying Platinum
  advertises Breeze, updates skip the manual icons, and undo has no record
  of their contents. This is the pending integration identified in PLAN.

  Build and verify the pinned trio before changing any install targets.
  Add the three directory IDs under `$XDG_DATA_HOME/icons` (default
  `~/.local/share/icons`) to the existing manifest, displacement and restore
  machinery. Preserve relative symlinks and capture the first manual copy of
  each existing ID even when its bytes equal the build. Record absences.
  Install-only should preserve selection. Make the generator and shipped
  global defaults select `WhiteSur-lavender` on apply. Preserve the original
  manual directories across repeated updates and later user edits.

  For this upgrade, record the effective icon selection and where it came
  from before adopting Lavender. A pre-existing Platinum config backup can
  predate the manual switch (`install.sh:211–225`). Preserve that backup
  and account separately for the manual icon state. Undo must put back the
  same-ID manual copies and usable selection, including explicit versus
  inherited settings. Inspect the config that will survive restoration
  (`kdeglobals` and `kdedefaults/kdeglobals`). If a managed selection would
  lose its only usable copy, retain it with a retryable record. Both light
  and dark link into the base, so keep those dependencies together. Never
  assume the removed old WhiteSur folders exist or require them for undo.
  Test fresh install, manual Lavender already selected, legacy selection in
  an older Platinum backup, plain update, apply, independent selection of
  each variant, interrupted update, local edits, dry run and repeated undo.
  Check manifest performance before wiring in `place_dir`: the built trio
  has 44,619 physical files and links, and `record_sums` calls the linear
  `manifest_has` for each entry (`scripts/common.sh:295,396–399`).

- **#111 · P3 · open — Some copied upstream SVGs lack the SVG namespace.**
  `icons/build-whitesur-lavender.sh:15` copies these unchanged from the
  upstream install path. For example, pinned
  `src/places/16/folder-vbox.svg:1` declares a bare `svg` element. All
  20,330 physical SVG files parsed as XML. In 127 files (118 distinct byte
  sequences) the root's expanded name was `svg` instead of
  `{http://www.w3.org/2000/svg}svg`. This is an upstream format defect
  outside the 25 recolors. librsvg accepted the sample. Report the affected
  inputs upstream and document the exception or normalize them in a
  reviewed export patch. Check the SVG namespace separately from XML syntax.

### Pinned output and limits

| Theme ID and index Name | Recolors matching expected bytes / rendered / found by GTK at 64 px | Resolved file paths | Physical symlinks | Broken or escaping links | Cache validation |
|---|---|---:|---:|---:|---|
| WhiteSur-lavender | 25 / 25 / 25 | 55,030 | 15,979 | 0 | passed |
| WhiteSur-lavender-light | 25 / 25 / 25 | 55,030 | 1,834 | 0 | passed |
| WhiteSur-lavender-dark | 25 / 25 / 25 | 55,030 | 6,467 | 0 | passed |

All three indexes inherit `hicolor,breeze`. All 86 listed directories and
sections exist per index, including 43 scale-2 entries. Each 1,099,664-byte
icon cache passed `gtk-update-icon-cache --validate`. Each recolor passed
`xmllint --nonet --noout` and librsvg rendering. The source-to-output byte
comparison accounted for all three accent replacements. The 24 embedded PNG
shadows contain only grayscale visible pixels. A separate scan of every
scalable places SVG name in each variant found the old accent literals only
in 46 upstream color-specific paths: 28 `purple-*`, 17 `folder_color_purple*`
and `folder-violet.svg`. None belongs to the 25 Lavender assets.

The wrapper's private `mktemp -d` and quoted EXIT cleanup operated on the
export. The default output is Git-ignored. The source checkout is a sibling,
and Git lists only the three new text files under `icons/`. No new upstream
tree or Apple artwork is staged or tracked. Independent authorship of every
upstream asset was outside the available evidence.

The user's stated manual installation and selection were inputs to the undo
review. The live files, saved live config, desktop appearance, future releases
and an actual install/apply/uninstall round trip were not verified. Installer
integration was traced in source. The five unrelated project suites were not
run. No additional suspected issues were assigned finding numbers.

## 2026-11-22, Codex (GPT-6) — #99 and #100 follow-up, checkpoint 5 passed

Audited the uncommitted follow-up against the checkpoint 4 working tree on
`dc8b76f`. No new findings in the exercised cases.

- **#100, fixed in the working tree.** `styleWatcher()` now checks the result
  of `qobject_cast<QApplication *>` and captures that pointer in the shutdown
  callback. There are zero evaluations of `qApp` in the function. With
  the Quick plugin and test executable built with nonrecovering UBSan, a
  plain QGuiApplication constructed an actual inactive PlatinumItem through
  the QML engine and exited 0 without diagnostics. The QApplication teardown
  probe also exited 0 with zero top-level widgets after creating a late item.
- **#99, fixed in the working tree.** The three maximize signals update
  border state. Applied `bordersChanged` drives button and title-bar layout,
  as does a width change. Initialization, font changes and reconfiguration
  still run the explicit layout path even if the borders stay the same.
  The preview probe held back auto-apply, resized, and explicitly applied
  a cloned state with further client width notifications suppressed. A
  function-entry counter in test copies showed checkpoint 4 missed the
  applied-border relayout. The fixed build observed it on both maximize
  and restore. Its (frame width, title width, right edge) results were
  (415, 415, 411) on open, (434, 434, 430) after maximize and
  (453, 453, 449) after restore. Both fontChanged and reconfigured caused
  fresh layouts at the same 453 px width. The uninstrumented preview
  test recorded 6 maximize damage signals and 1 unchanged-border relayout
  damage signal, as at checkpoint 4. This isolates the missing callback;
  the preview did not reproduce a visibly clipped button.
- Sandbox suites passed 135/135 widget regions and 29/29 Qt Quick checks.
  All **200/200** decoded RGBA images matched the validated source baseline
  at 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 and 3×, including translucent
  fields/dialogs, fixed barber phase, and the decoration press/drag-off pairs.
- Evidence is in `dev/build/audit-baseline/checkpoint5/` and
  `checkpoint5-suites/` under the same baseline directory. Archived
  checkpoint 4 D-Bus logs are in `checkpoint5/checkpoint4-dbus-evidence/`.
  The new `test-nested-99.py` builds a test copy of the decoration and
  checks title width and the rightmost visible button edge during real
  virtual-KWin paints. The instrumented plugin compiled in build-only mode.
  Physical displays, X11 clients, and constrained windows are outside this probe.
- The user ran all three final private-D-Bus suites outside the sandbox.
  The saved logs in `dev/build/audit-baseline/dbus-suites-final/` show
  19/19 Plasma checks, 367/367 install checks, and 37/37 live install
  checks. Each recorded exit code is 0.
- The user's original #99 nested-KWin run reached open, maximize, restore,
  horizontal maximize, vertical maximize, and a second restore with correct
  geometry. The resize action left the frame at its previous size. The
  probe failed with `No matching paint for resize`
  (`dev/build/audit-baseline/nested-99-ksy7xuv4/kwin.log`).
- Claude ran a scratch copy against the same decoration with only the resize
  action changed to assign a fresh frame geometry object. The user reported
  PASS across all seven steps and 23 paints. At resize the frame was
  708 × 438 px, the title was 708 px wide, and the right edge of the
  rightmost button was at 704 px. Codex applied that same one-line change
  to the saved probe and checked it with `python3 -m py_compile`. The runtime
  result comes from Claude's corrected copy.

## 2026-11-22, Claude (Opus 5.5) — verification of Gemini's review findings #99 and #100

Audited: #99 and #100 against the uncommitted working tree on top of `dc8b76f`, compared with `dc8b76f`. No theme code was changed, nothing was installed, and the live desktop was not touched. Gemini's "clean" verdicts for the other findings were not re-tested here.

- **#100 · P2 · confirmed, open.** `styleWatcher()` evaluates `qApp`, a `static_cast<QApplication *>`, before checking the application type. A UBSan build reported invalid downcasts at `style/quick/platinumitem.cpp:25:45` and `:25:65` when a `QGuiApplication` created a `PlatinumItem`. The same probe on `dc8b76f` reported none. Use the `qobject_cast` result and never `qApp` in this function.
- **#99 · P2 → P3 · partly confirmed, open.** The working tree did remove the `bordersChanged` relayout that `dc8b76f` had, and `previous != borders()` is not a safe test if borders are applied through a deferred next state. The reported wrong geometry **did not reproduce in real nested KWin 6.8.3**: across open, maximize, restore, horizontal maximize, vertical maximize, and resize, with a normal window and one with a maximum width, every decoration paint had the correct title bar width and right button position in both `dc8b76f` and the working tree (0 wrong paints). A deferred path outside these cases remains possible, and the connection is cheap, so restore it before committing. Gemini's suggested fix is reasonable, but it has not been implemented or tested.

Limits: nested KWin used its virtual backend and Qt Wayland clients only. X11 clients, clients that ignore a maximize size, the user's GPU, and physical displays were not tested.

## 2026-11-22, Antigravity (Gemini 4 Neon) — independent review of uncommitted C++ audit fixes (#85–98)

Audited: full working tree diff against `dc8b76f` (`decoration/platinum.{h,cpp}`, `style/platinum/{nineslice.h,sprite.h,slices.h,platinumstyle.cpp}`, `style/quick/{platinumitem.h,platinumitem.cpp,Platinum/ComboBox.qml}`, `tools/nineslice.py`, and `plasma/make-plasma.py`). Review only (no code modified, nothing installed, `dev/build/audit-baseline/` untouched). Built both `dc8b76f` and the working tree (`-O2` and ASan/UBSan) into an isolated scratch directory with zero compiler warnings.

### New regressions found (ranked by severity)

- **#99 · P2 · open — Removing `bordersChanged` → `updateButtonsGeometry` and checking `previous != borders()` breaks double-buffered `KDecoration3::DecorationState` geometry**
  - **Where:** `decoration/platinum.cpp:240–252` (regression from the `#96` change).
  - **Concrete failure:** In `libkdecorations3.so.6`, `Decoration::borders()` reads `currentState()->borders()` (offset `0xc0`), whereas `Decoration::setBorders()` writes `nextState()->borders()` (offset `0xb0`). With double-buffered state updates (the `KDecoration3` contract used by KWin Wayland, where `apply(nextState)` runs after `init()` or after client configure):
    1. After `init()`, `recalculate()` lays out buttons and `titleBar` against `currentState` borders `(0,0,0,0)` (`size().width() = 400`, `rightBtnR = 396`). When the compositor then calls `apply(nextState)` (growing `size().width()` to `412` and emitting `bordersChanged`), nothing is connected to `bordersChanged`, so `titleBar` stays `400` and the right buttons (`Zoom`/`Collapse`) stay **12 px too far left** (`396` instead of `408`).
    2. When `currentState` and `nextState` are distinct cloned states and a horizontal maximize drops borders `6 → 0` with `widthChanged(1000)` arriving before `apply(nextState)`: `previous != borders()` inside `maximizeChanged` is **false** (comparing `currentState` to itself), `widthChanged(1000)` lays out buttons for `1000 + 12 = 1012` (`rightBtnR = 1008`), and then `apply()` shrinks `size().width()` to `1000` and emits `bordersChanged` with no listener — leaving `titleBarW = 1012` and `rightBtnR = 1008` (**12 px past the right edge of the 1000 px window, clipping the Collapse button off-screen**).
    Offscreen `PreviewItem` hid this because it calls `apply(nextState)` synchronously inside `nextStateChanged`.
  - **Confirmed vs suspected:** **Confirmed** via `objdump` of `libkdecorations3.so.6` (`borders()`/`currentState()` at `0xc0` vs `setBorders()`/`nextState()` at `0xb0`) and a standalone `KDecoration3::DecorationBridge` probe comparing `dc8b76f` vs working tree: `dc8b76f` produced `412 / 408` after `init()+apply()` and `1000 / 996` after `maxH+widthChanged(1000)+apply()`; the working tree produced `400 / 396` and `1012 / 1008`. **Suspected (not tested in live KWin):** exact frequency of `init()` / `widthChanged`-before-`apply()` ordering in real `kwin_wayland` (`libkwin.so` imports `bordersChanged`, `nextStateChanged`, and `apply(DecorationState)`).
  - **Suggested fix:** Restore `connect(this, &KDecoration3::Decoration::bordersChanged, this, &Decoration::updateButtonsGeometry);`, connect `maximizedChanged`/`maximizedHorizontallyChanged`/`maximizedVerticallyChanged` directly to `&Decoration::updateBorders` (deleting `maximizeChanged`), and in `recalculate()` do `const auto previous = borders(); updateBorders(); if (previous == borders()) { updateButtonsGeometry(); }` so synchronous border changes lay out once via `bordersChanged`, non-border changes (`fontChanged`/`reconfigured`) still relayout, and deferred `apply()` updates geometry when `bordersChanged` fires. Zero pixel change at steady state; verify in nested KWin + offscreen preview.

- **#100 · P2 · open — `styleWatcher()` invokes `qApp` before `qobject_cast<QApplication *>`, causing undefined behavior (invalid downcast) in `QGuiApplication`-only apps**
  - **Where:** `style/quick/platinumitem.cpp:25` (regression from the `#94` change).
  - **Concrete failure:** `<QApplication>` defines `qApp` as `static_cast<QApplication *>(QCoreApplication::instance())`. Line 25 evaluates `qApp && quitting == qApp` **before** line 28 checks `qobject_cast<QApplication *>(QCoreApplication::instance())`. Every `PlatinumItem` constructed in a `QGuiApplication`-only Qt Quick application performs an invalid static downcast from `QGuiApplication *` to `QApplication *` (C++ undefined behavior). `dc8b76f` did not have this UB because `qApp` was only reached inside the `qobject_cast<QApplication *>` guard.
  - **Confirmed vs suspected:** **Confirmed** under UBSan (`-fsanitize=address,undefined` on working-tree `libplatinumquick.so` running a `QGuiApplication` QML `Switch` scene): `style/quick/platinumitem.cpp:25:45: runtime error: downcast of address ... which does not point to an object of type 'QApplication' (note: object is of type 'QGuiApplication')`.
  - **Suggested fix:** Check `auto *app = qobject_cast<QApplication *>(QCoreApplication::instance()); if (!app || QCoreApplication::closingDown() || quitting == app) { return nullptr; }` and use `app` (never `qApp`) inside `styleWatcher()`. Zero pixel change.

### Verification of #85–98

- **#85 — Clean.** All four `_platinum_*` dynamic property writes moved to GUI-thread signal handlers (`platinumitem.cpp:97–100`). Confirmed `crossThreadDynProps = 0` under `QSG_RENDER_LOOP=threaded` (both `-O2` and ASan/UBSan) and verified `_platinum_first`/`_platinum_last`/`_platinum_shortcuts` stay in sync after dynamic `Menu.removeAction()`. Follows Claude's verification note.
- **#86 — Clean.** `decorationCount` retains `activeShadow`/`inactiveShadow` across focus changes and resets both when the last `Decoration` is destroyed (`decoration/platinum.cpp:192–208, 334–341`). Follows Claude's verification note.
- **#87 — Clean.** `CT_HeaderSection` checks `option`, and `polish`/`unpolish` return early on `!widget` (`platinumstyle.cpp:759, 1905, 1951`). Confirmed all three survive without SIGSEGV. Follows Claude's verification note.
- **#88 — Clean.** `updateBusyTimer` (`platinumstyle.cpp:1794–1832, 1941–1944, 1966–1968`) lazily starts the timer only while `isVisible() && minimum() == maximum()`. Confirmed: 0 timers on visible determinate bars, stops immediately on parent tab switch (`QEvent::Hide`, 0 fires in 350 ms), restarts on `QEvent::Show`, stops on determinate range change, and cleans up in `unpolish()`. Follows Claude's verification note.
- **#89 — Clean.** Split into 21 property-specific signals (`platinumitem.h:17–58`, `platinumitem.cpp:92–123`). Confirmed 0 binding-loop warnings on a 30-item menu with shortcuts AND 0 `panel`/`ListView` binding-loop warnings during Platinum → Fusion → Platinum style switch **with the menu open** (an edge case previously untested). Confirmed `ToolTip` plain↔rich text transitions (`drawsTextChanged`). Hover across 20 menu items improved from 5,207 µs to 1,657 µs (3.1× faster). Follows Claude's verification note.
- **#90 — Clean.** Removed all three `Button` repaint connections (`decoration/platinum.cpp:493–497`) and skipped `paintTitle()` when `!repaintArea.isEmpty() && !repaintArea.intersects(titleBarRect())` (`:348–350`; all `paintTitle` drawing lies in `y ∈ [2, 17] ⊂ [0, 20)`). Follows Claude's verification note.
- **#91 — Clean.** Horizontal RLE `drawRow` in `nineslice.h`/`sprite.h`, `constexpr` tables in `slices.h`/`tools/nineslice.py`, `static constexpr` `pressedSlice` in `drawBevel`, span coalescing in `drawProgress` (with non-negative `(c - r - phase + 32) % 16`), 7-rect `drawSlider` groove, and single-pass `drawSpinBox`. Independently verified **0 differing pixels** across all 8 scales (`1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 3×`) against `dc8b76f`, including translucent `QPalette::Base` and `QPalette::Window` fills. Follows Claude's verification note.
- **#92 — Clean.** Cached on polished `QMenu`s via `_platinum_menuShortcutCache` invalidated on `ActionAdded`/`ActionRemoved`/`ActionChanged` and cleared in `unpolish()`. Confirmed pre-polish query, shortcut add/clear, visibility toggle, `\t` text edit, and `removeAction` all update menu width accurately. Follows Claude's verification note.
- **#93 — Clean.** `ComboBox.qml:42–55` decouples `platinumListWidthHint` from `control.width` and guards `!popup`. Confirmed closed 200-item `ComboBox` resize (50 steps) dropped from 27,969 µs (559.4 µs/resize) to 407 µs (8.1 µs/resize, 69× faster) while live same-count model rename still widens the popup (`81 → 262`). Follows Claude's verification note.
- **#94 — Shutdown leak fixed, regressed in #100.** Confirmed `After app.exec(): topLevelWidgets=0` (down from 1), and null `QApplication::style()` guards in `margin()`, `comboWidthHint()`, `updateImplicitSize()`, and `paint()` are clean, but `styleWatcher()` line 25 introduced #100.
- **#95 — Properly remains open.** Verified `RangeSlider.qml` is unchanged against `dc8b76f` (`groove`/`firstThumb`/`secondThumb` all `400×16`) and the translucent-capable black underlays in `drawField`/`drawModalFrame`/`drawMenuPanel` are untouched (0 differing pixels on translucent 50% white fills at all 8 scales).
- **#96 — Factory and signal cleanup clean, regressed in #99.** Confirmed the validating `K_PLUGIN_FACTORY` lambda (`decoration/platinum.cpp:43–50`) safely returns `nullptr` for empty args, null decoration, and `DecorationButtonType::Menu` while accepting valid `DecorationButtonType::Close` and `int(Close)`; `visibilityChanged` and `setSpacing(BoxGap)` moved out of `updateButtonsGeometry()` cleanly. Removing `bordersChanged` and checking `previous != borders()` introduced #99.
- **#97 — Clean.** `SC_GroupBoxLabel` computes `fm.boundingRect` lazily (`platinumstyle.cpp:884`), and `hitTestComplexControl` computes `scrollLayout` once while preserving `rtlFallback` and `upsideDown` swap via `scrollPart` (`:845–863, 958–979`). Confirmed 0 mismatches across all orientations, directions, and reversal settings. Follows Claude's verification note.
- **#98 — Clean.** `plasma/make-plasma.py:131` (`const(?:expr)? NineSlice<(\d+)>`) matches all 13 `constexpr NineSlice<K>` tables in `slices.h`, `tools/nineslice.py:117` matches `slices.h`, and a repo-wide grep found no other text parser for `slices.h`.

### Checks and limits

- Compiled `dc8b76f` and working-tree plugins (`-O2` and `-O1 -g -fsanitize=address,undefined`) into an isolated scratch folder: 0 compiler warnings.
- Ran offscreen widget pixel-diff across 8 scales (`1` to `3×`, including translucent palettes: 0 differing pixels on all 8 sheets), `#87`/`#88`/`#92`/`#97` behavior probes, `style/quick` probes (open-menu style switch, threaded render loop + ASan/UBSan, `QGuiApplication` UBSan, `ToolTip` rich↔plain toggle, `ComboBox` rename/resize, `Menu.removeAction`), and a `KDecoration3::DecorationBridge` double-buffered state probe + `libkdecorations3.so.6` disassembly.
- Limits: offscreen probes only; did not run nested `kwin_wayland`, live Plasma, or physical displays, and did not re-run the repo's `dev/check-*.sh` scripts to avoid writing to `dev/build/` or `dev/shots/`.

## 2026-11-22, Codex (GPT-6) — checkpoint 4 passed

Compared the uncommitted fixes to source baseline `dc8b76f`. Codex ran the
Qt Widgets (135/135) and Qt Quick (29/29) suites inside the network-disabled
sandbox. The user ran Plasma (19/19), install (367/367) and live install
(37/37) outside the sandbox with private D-Bus. All five exited zero.
`dbus-suites-final/` holds the successful rerun and
`dbus-suites-final-failed-1/` preserves the original #98 failure.

| Findings | Final working-tree result |
|---|---|
| #85 | Moved the four dynamic-property writes to GUI-side change notifications. The user's instrumented threaded virtual-KWin working-tree probe observed 16 active off-GUI paints, zero paint-time changes, 18 GUI positive controls and zero violations. With the original code, 16 such paints yielded 18 changes and 82 total violations. |
| #86, #87, #94 | Both shadows expire after the last decoration (one retained reference each before, zero each after). Null header-size, polish and unpolish calls completed. Constructing a Quick item late in shutdown leaves zero watcher widgets, previously one. |
| #88 | Only visible busy bars animate. Ten determinate bars delivered 210 timer events in a two-second baseline sample and zero after. Hidden busy bars went from 200 to zero, visible busy bars delivered 200 in both samples. These count timer deliveries. |
| #89, #93 | Property-specific notifications and a width-independent content hint stopped repeated row sizing. A 200-row combo went from 69,800 to zero implicit-size calls in 350 width assignments. Uninstrumented median time for 50 assignments was 58 ms before and 21 ms after (seven batches). The 30-row menu produced 29 shortcut-column binding-loop warnings before and zero after. |
| #90, #96 | Five hover cycles went from 20 to 10 damage signals, maximize from 15 to 6, and an unchanged-border relayout from 2 to 1. Ten width changes produced 40 signals in both builds. The press and drag-off frames matched, unchanged-border layout ran, and the factory accepted valid arguments and rejected empty arguments. |
| #91, #92, #97 | Run-length drawing, cached menu shortcut presence, and less repeated group-box and scrollbar layout work. Action invalidation passed after add, remove, visibility and shortcut edits. All 40 scrollbar target checks passed across both orientations, layout directions and reversal settings. |
| #95 | Open. The compact thumb candidate changed 45/152 Quick images at the five fractional scales. That change was reverted and the original thumb sizes and translucent underlays are present in the verified tree. |
| #98 | Both header declaration spellings parsed all 13 tables identically. The generator produced byte-identical tracked artwork and the final Plasma run passed. |

### Cost measurements

Offscreen at 1× with optimized builds. Each entry is the median of three
timed batches per build, alternating run order. Values are microseconds per
operation except the menu row, which times a batch of 1,000 size requests.
The decoration probe clips the painter to the damaged area. Full decoration
paint stayed close to its baseline. These are local CPU timings.
Raw logs and probe sources are in `dev/build/audit-baseline/final-costs/`.

| Operation (µs) | Before | After |
|---|---:|---:|
| full decoration | 21.617 | 21.926 |
| side decoration | 10.278 | 5.519 |
| progress | 135.069 | 7.485 |
| busy | 137.919 | 14.473 |
| slider | 74.151 | 4.137 |
| groupbox | 14.040 | 9.574 |
| combo paint | 12.576 | 4.763 |
| pressed spin | 14.681 | 3.513 |
| default button bevel | 6.489 | 5.002 |
| tree disclosure | 1.337 | 1.210 |
| scrollbar hit | 0.037 | 0.016 |
| 1000 menu sizes | 19,323.941 | 82.114 |

### Pixel comparison and limits

All 200 final PNGs matched the twice-rendered source baseline pixel for
pixel after RGBA decoding (228,376,750 pixels). At each of 1, 1.25, 1.5,
1.75, 2, 2.25, 2.5 and 3×, comparisons covered two widget sheets
(including the dedicated opaque/translucent field probe), 19 Quick frames
and four decoration frames. They cover normal, hover, pressed, disabled,
keyboard-focus, active/inactive and drag-off examples as applicable. Busy
progress used phase 4. Pressed and drag-off images visibly differed and each
matched its own baseline. Every requested scale passed for the captured cases.

Full-image comparisons used offscreen software rendering. The threaded #85
probe exercises menu-item painting. Physical-display fidelity, other GPU
rendering paths and user visual review of these fixes remain unverified.
The sanitizer probes passed for all three plugins with leak detection disabled.
Artifacts are under `dev/build/audit-baseline/`, including `final/`,
`final-suites/` and the working-tree patch `checkpoint-4.patch`.

## 2026-11-22, Codex (GPT-6) — #98 Plasma generator regression and #85 threaded verification

**#98 (P2), fixed in the working tree.** The #91 change to `constexpr` tables
broke the text reader in `plasma/make-plasma.py`. The user's final Plasma suite
exited 1 before rendering, in `nineslice("BevelNormal")`. Both install suites
exited 0 (367/367 and 37/37). Codex preserved and compared the complete
`dev/build/audit-baseline/dbus-suites-final-failed-1/` log directory before
editing. Changed only the reader regex under `plasma/`. Running the generator
produced zero tracked output differences. All 13 tables yielded identical
shapes at 81×43 from the original and current header spellings. A project
source search found one text reader. The remaining consumers compile the header
or emit it. Sandbox reruns passed 135/135 widget regions and 29/29 Quick checks.
Checkpoint 4 awaits a fresh set of all three private-D-Bus suite exits.

**#85, verified in the working tree.** The user ran both private, threaded
virtual-KWin probes outside the sandbox. Codex checked their client logs.
The negative control from `dc8b76f` recorded 16 active off-GUI paints, 18
dynamic property changes during those paints, and 82 total violations.
It detected all four original property writes. The working tree recorded
16 active off-GUI paints, zero changes during those paints, 18 GUI positive
controls and zero violations. The probe passed. Logs are under
`dev/build/audit-baseline/threaded-85-negative-JBA4Qa/` and
`dev/build/audit-baseline/threaded-85-normal-ksrc2w/`. This verifies the
exercised menu-item scene on the threaded render loop.

## 2026-11-22, Codex (GPT-6) — checkpoints 2 and 3, working tree

Working-tree fixes pending checkpoint 4: #85–94, #96 and #97. #95 remains
open. This updates the pre-fix summary above. For #85, inspection of
`style/quick/platinumitem.cpp` confirms the four dynamic-property writes
moved to GUI-side property notifications. The software-renderer pixel tests
cannot verify a threaded paint. The private virtual-KWin probe at
`dev/build/audit-baseline/test-threaded-85.sh` requires active off-GUI
paints, GUI property delivery, and zero writes or changes from paint. Its
negative control builds the original Quick plugin from `dc8b76f`.
Both instrumented builds and the shell syntax check passed. No threaded
runtime verdict yet.

Compared complete offscreen images with the two matched baseline runs.
#85 and #89/#93 each matched 152/152 Quick frames; #88, #87, #92 and #97
each matched 8/8 widget sheets. #86 matched 8/8 decoration sheets. #90
and #96 each matched 24/24 decoration sheets plus 8/8 pre-drag pressed
frames. #91 matched 160/160 widget/Quick frames; its final spin-arrow
change also matched 8/8 widget sheets. #94 matched 152/152 Quick frames.
The additional explicit field probe matched 8/8 with correct alpha
compositing. Widget and Quick suites passed 135/135 and 29/29 in both
checkpoints. The user has not yet visually reviewed the changes.

## 2026-11-22, Codex (GPT-6) — #95 remains open

The compact range-slider thumb candidate changed 45 of 152 Quick frames
against the validated `dc8b76f` baseline. All five fractional scales
(1.25, 1.5, 1.75, 2.25 and 2.5×) changed. Integer scales matched.
Moving the painted item's origin changes how its texture lands on physical
pixels. See `dev/build/audit-baseline/fix95/comparison.txt` and the two
image sets. Restored the pre-#95 sources. The translucent-capable black
underlays were preserved throughout.

## 2026-11-22, Codex (GPT-6) — checkpoint 1 suite baseline

Source `dc8b76f`. The user ran the private-D-Bus suites outside the sandbox.
The three logs in `dev/build/audit-baseline/dbus-suites-baseline/` contain
19 Plasma, 367 install and 37 live-install passes. All three exit files contain
zero. Codex's sandbox runs passed 135/135 widget regions and 29/29 Qt Quick
checks. These runs precede the fixes for #85–97.

## 2026-11-22, Claude (Opus 5.5) — verification of Gemini's C++ audit (#85–97)

Audited: findings #85–97 against commit `dc8b76f`. No theme code was changed, nothing was installed, and the live desktop was not touched. The original Gemini entry below is left as written; **the severities and fix notes in this section supersede it**.

Method: exported the commit to a scratch directory, built the plugins, and ran probes offscreen and in disposable nested KWin 6.8.3 (`--virtual`, threaded Qt Quick render loop, Qt 6.12.0). Instrumented copies were used for counts. Timings came from uninstrumented builds. The probes are not in the repo.

| # | Verdict | Severity | What to do with it |
|---|---|---|---|
| 85 | Partly confirmed | P1 → **P2** | Move the four `setProperty()` calls out of `paint()`. The full `QQuickItem` rewrite is not justified by this evidence. |
| 86 | Confirmed | P2 → **P3** | **Do not use the suggested `weak_ptr` fix.** Release both shadows when the last Platinum decoration is destroyed. |
| 87 | Partly confirmed | P2 → **P3** | Optional null guards. The null `viewport()` part is disproved. |
| 88 | Confirmed, cost overstated | **P2** | Run the timer only for visible busy bars. The range mismatch part is disproved. |
| 89 | Confirmed | **P2** | Split the notify signals. The `panel` binding loop was not reproduced. |
| 90 | Partly confirmed | P2 → **P3** | Delete all three `Button` repaint connections. Skipping `paintTitle()` helps only the side and bottom parts. |
| 91 | Confirmed | P2 → **P3** | Use run-length fills. Do not use image blits at fractional scales. |
| 92 | Confirmed | P2 → **P3** | Cache per menu. The cost is once per menu layout, not per frame. |
| 93 | Confirmed, root cause incomplete | **P2** | Fix with #89: the suggested fix alone leaves the per-row recalculation. |
| 94 | Partly confirmed | **P3** | Fix the watcher recreation. Parts 3 and 4 are not bugs. |
| 95 | Confirmed, fix unsafe | **P3** | Shrink the thumbs. **Keep the black underlay** in translucent-capable fills. |
| 96 | Confirmed, low impact | **P3** | Clean up. Check that a relayout still happens when borders do not change. |
| 97 | Confirmed by reading | **P3** | Clean up, keeping the reversed-bar and RTL routing. |

### Evidence

- **#85:** 44 of 44 `paint()` calls ran on the render thread, and all 44 ran inside the scene graph sync, while the GUI thread is blocked. That rules out the concurrent GUI-thread race the P1 rating relied on. `QPixmapCache::insert` and `find` both returned false off the main thread, so the suspected cache race cannot happen (the cache is simply skipped there). No crash or Qt thread warning appeared. Setting properties from the render thread is still a thread-affinity violation. The claimed abort on debug Qt was not tested.
- **#86:** The two shadows do outlive every decoration. In nested KWin, opening 6 windows created **2** shadows with the current code and **8** with the suggested `weak_ptr`, because the active shadow expires on each focus change and is rebuilt.
- **#87:** The three null-argument crashes reproduce (SIGSEGV), but no project caller passes null and the audit shows no Qt path that does. `setViewport(nullptr)` still leaves a non-null viewport, so the suspected viewport crash is disproved.
- **#88:** One idle bar fires its timer 10 times per second. Ten bars fire 100 timer events per second but still wake the thread only **10 times per second**, because Qt coalesces them, so the "~91 wakeups/s" figure counts timer events and not CPU wakeups. `QProgressBar::setRange(10, 5)` becomes 10..10, so the `<=` versus `==` mismatch cannot occur on a real bar.
- **#89:** The `platinumShortcutColumn` binding loop reproduces (13 warnings per load of the test scene). The `panel` loop did not appear across a Platinum → Fusion → Platinum switch with the menu closed; a switch with a menu open was not tested.
- **#90:** Hover produces 20 damage signals per 5 enter and leave cycles. Removing all three `Button` connections gives **10**, and Gemini's conditional version also gives 10, because KDecoration already emits its own. With them removed, press and drag-off still emit damage. In real KWin, a maximize's 15 damage signals became **1 to 4 `paint()` calls**. A full repaint is 4 calls (top, two sides, bottom), each repeating the title layout, so the `repaintArea` skip helps those 3 non-title parts. It cannot help button hover, because the buttons are inside the title bar.
- **#91:** Reproduced: progress 132 µs (Fusion 52), busy 133 µs (Fusion 79), slider 74 µs (Fusion 21). 132 µs is about 1.6% of a 120 Hz frame. Run-length fills matched per-pixel drawing exactly for 24 sprites at 25 offsets and 8 scales (1 to 3×). Image blits matched only at 1×, 2× and 3×, and differed at every fractional scale tested.
- **#92:** 1,000 items: 20.5 ms (Fusion 2.2 ms). The next `sizeHint()` took 1.7 µs, so the cost is paid when the menu is laid out.
- **#93:** Each width step of a closed combo costs **1.33 ms at 200 items** and 0.12 ms at 20. Each step also re-ran `updateImplicitSize()` about 216 times in the 200-item scene, which the suggested measurement split alone would not stop.
- **#94:** The recreated watcher widget is reproduced (one top-level widget left after `exec()`). A null `QApplication::style()` was not reproduced, and every cited use except the `updateActive()` check is behind `m_active`. The style name is `platinum` through the factory, so the comparison is correct. Qt removes destroyed event filters, so the missing `removeEventFilter` is not a leak (Qt behavior, not separately tested).
- **#95:** The full-width thumbs are confirmed in `RangeSlider.qml`. The "zero pixel change" claim for edge-only fills is **false for translucent colors**: a field with a 50% base renders `#808080` over white because of the black underlay, and would render `#FFFFFF` without it. `drawField` and `drawModalFrame` take caller colors. Only opaque fills such as `drawMenuPanel`'s are safe to change.
- **#96:** 15 damage signals per maximize and the factory crash on empty arguments both reproduce. The crash needs invalid arguments that the normal `Button::create` path never passes. Damage is coalesced as described in #90.
- **#97:** Confirmed by reading. `hitTestComplexControl` must keep going through the reversed-bar swap (#32) and the RTL fallback if `scrollLayout()` is shared.

### Limits

Nested KWin used its virtual backend, not the user's GPU or displays. Debug Qt, multi-window GPU stress, and a style switch with a menu open were not tested. Gemini's other timings (#90 paint times, #97) were not re-measured. No fix was implemented, so the suggested alternatives above still need their own pixel checks and suite runs.

## 2026-11-22, Antigravity (Gemini 4 Neon) — C++ performance, resource, latency, and stability audit

Audited: `decoration/` (`platinum.h`, `platinum.cpp`, `build.sh`), `style/platinum/` (`platinumstyle.h`, `platinumstyle.cpp`, `plugin.cpp`, `nineslice.h`, `sprite.h`, `slices.h`, `sprites.h`, `progress.h`, `tabs.h`, `menu.h`, `build.sh`), `style/quick/` (`platinumitem.h`, `platinumitem.cpp`, `build.sh`, and interacting `Platinum/*.qml`), and relevant C++ in `tools/` and `dev/` (`check-wallpaper.cpp`, `decoshot.cpp`, `quickshot.cpp`, `quickkeys.cpp`, `quickref.cpp`, `styleshot.cpp`, `check-quick.sh`), at commit `dc8b76f`. Audit only (no theme code modified, nothing installed). All three plugins were compiled (`-O2` and `-O1 -g -fsanitize=address,undefined`) into a separate scratch directory with zero compiler warnings, and exercised with offscreen Qt / KDecoration3 preview probes and microbenchmarks.

### Findings

- **#85 · P1 · open — `PlatinumItem::paint()` mutates QObject dynamic properties and invokes GUI-thread-only Qt Widgets/QPixmap APIs on the Qt Quick render thread**
  - **Where:** `style/quick/platinumitem.cpp:228–238`, `:255`, `:283` (also `style/platinum/platinumstyle.cpp:1416`, `dev/check-quick.sh:30–40`).
  - **Concrete failure / cost:** Under Qt Quick's threaded render loop (`QSG_RENDER_LOOP=threaded`, the default on Wayland/OpenGL/Vulkan in Plasma 6.8), `QQuickPaintedItem::paint()` executes on `QSGRenderThread`, not the GUI thread. `PlatinumItem::paint()` calls `this->setProperty(...)` four times on a GUI-thread `QObject`, synchronously dispatching `QDynamicPropertyChangeEvent` on the wrong thread (violating Qt's thread-affinity contract and aborting in debug Qt). It also calls `QIcon::fromTheme()`, `QApplication::palette()`, `QApplication::font()`, `QToolTip::font()/palette()`, `CE_MenuItem` (`mi->icon.pixmap(...)` constructing a `QPixmap`), and `PE_IndicatorTabClose` (`QFusionStyle` `QPixmap`) off the GUI thread. Because `dev/check-quick.sh` forces `QT_QUICK_BACKEND=software` (single-threaded `basic` loop), existing suites never exercised this path.
  - **Confirmed vs suspected:** **Confirmed** empirically that `QQuickPaintedItem::paint()` runs on `QSGRenderThread` under `QSG_RENDER_LOOP=threaded` (`thread != guiThread`) and that opening a Platinum Qt Quick `Menu` triggers 12 cross-thread `QDynamicPropertyChangeEvent` deliveries on `PlatinumItem` (`_platinum_first`, `_platinum_last`, `_platinum_combo`) in both `-O2` and ASan/UBSan builds. **Suspected:** data races or aborts in `QPixmapCache` / native `QPixmap` creation under real GPU multi-window or debug-Qt runs.
  - **Suggested fix:** Remove `setProperty()` from `paint()` (update `_platinum_*` in property setters on the GUI thread, or pass context without mutating `QObject` properties). For full thread safety on real Plasma Wayland sessions, migrate `PlatinumItem` from `QQuickPaintedItem` to a `QQuickItem` that renders through `QStyle` into a DPR-scaled `QImage` on the GUI thread inside `updatePolish()` and uploads it as a `QSGSimpleTextureNode` in `updatePaintNode()`. Add a threaded-render-loop smoke test to `dev/check-quick.sh`. **Fidelity:** pixel-identical if rendered at the item's DPR with `Antialiasing = false`; verify with `dev/check-quick.sh` and `tools/compare.py diff` at 1×, 1.25×, 1.5×, and 2×.

- **#86 · P2 · open — `Decoration::updateShadow()` leaks `KDecoration3::DecorationShadow` `QObject`s past `~QCoreApplication()`**
  - **Where:** `decoration/platinum.cpp:306–311`.
  - **Concrete failure / cost:** `KDecoration3::DecorationShadow` is a `QObject` (`kdecoration3/decorationshadow.h:74`). Storing `active` and `inactive` in function-local `static std::shared_ptr`s retains both `QObject`s permanently in KWin even after switching away from Platinum, and destroys them during `__cxa_finalize` after `QCoreApplication` teardown (unsafe for `QObject`s and a plugin-unload/shutdown hazard in KWin).
  - **Confirmed vs suspected:** **Confirmed** via KDecoration3 preview probe: after destroying all `Decoration` instances and flushing `DeferredDelete` while `QApplication` was still alive, both `activeShadow` and `inactiveShadow` stayed alive (`expired=0, use_count=1`), and remained alive past `~QApplication()` (`org.kde.breeze` released its active shadow immediately: `expired=1, use_count=0`).
  - **Suggested fix:** Replace the two `static std::shared_ptr`s with `static std::weak_ptr<KDecoration3::DecorationShadow>` and call `.lock()`, creating a shadow only when expired. All active/inactive windows still share the same two shadow objects via `setShadow()`, and both are destroyed cleanly when the last Platinum decoration closes. **Fidelity:** zero pixel change.

- **#87 · P2 · open — `Platinum::Style` crashes with SIGSEGV on null `option` in `sizeFromContents(CT_HeaderSection)` and null `widget` in `polish()`/`unpolish()`**
  - **Where:** `style/platinum/platinumstyle.cpp:734–737`, `:1828–1834`, `:1876–1878` (suspected additional null dereferences: `:1387`, `:1850`, `:1853`, `:1886`).
  - **Concrete failure / cost:** `sizeFromContents(CT_HeaderSection, nullptr, ...)` dereferences `option->fontMetrics` directly, and `polish(nullptr)` / `unpolish(nullptr)` dereference `widget->inherits(...)` without null guards. `Fusion` handles all three calls cleanly without crashing.
  - **Confirmed vs suspected:** **Confirmed** with standalone probes: `sizeFromContents(CT_HeaderSection, nullptr, QSize(50, 20), nullptr)`, `polish((QWidget *)nullptr)`, and `unpolish((QWidget *)nullptr)` all exited 0 under `Fusion` and segfaulted (exit 139) under `Platinum`. (By contrast, `drawControl(CE_HeaderEmptyArea/CE_MenuBarEmptyArea, nullptr, ...)` also segfaulted in `Fusion`, so those follow Qt's non-null `option` contract for `draw*`.) **Suspected (code inspection only):** unguarded `combo->view()->viewport()` (`:1387`) and `view->viewport()` (`:1850, :1853, :1886`) would crash if a custom `QAbstractItemView` has a null viewport.
  - **Suggested fix:** Guard `if (option)` in `CT_HeaderSection` (else return `s`), add `if (!widget) return;` at the top of `polish(QWidget *)` and `unpolish(QWidget *)`, and guard `if (QWidget *vp = view->viewport())` before dereferencing. **Fidelity:** zero pixel change.

- **#88 · P2 · open — Every polished `QProgressBar` runs an active 100 ms `QTimer` permanently, including hidden and determinate bars**
  - **Where:** `style/platinum/platinumstyle.cpp:1862–1873` (and condition mismatch with `:281`).
  - **Concrete failure / cost:** `Style::polish()` creates and starts a 100 ms `QTimer` on every `QProgressBar` regardless of whether it is busy or visible. Every polished progress bar across all open Qt apps wakes the app event loop 10 times per second forever, preventing CPU deep sleep on an idle desktop. (Noted in passing at AUDIT.md:844, never numbered or measured.) Additionally, `drawProgress()` (`:281`) draws the barber pole whenever `maximum <= minimum`, while the timer lambda (`:1868`) only calls `update()` when `minimum == maximum`.
  - **Confirmed vs suspected:** **Confirmed** with probe: 10 polished, hidden, determinate (`0..100`) `QProgressBar`s created 10 active `"platinum-barber-pole"` timers and fired 50 wakeups in 550 ms (~91 wakeups/s; `Fusion`: 0 timers, 0 wakeups).
  - **Suggested fix:** Replace per-widget always-on timers with a single shared `QTimer` owned by `Style` (or lazily started per-bar timer) that runs only while at least one visible `QProgressBar` has `maximum() <= minimum()`, tracking bars with `QPointer<QProgressBar>` and removing on `Hide`, `destroyed`, or determinate paint. **Fidelity:** zero pixel change (same 100 ms repaint cadence and `currentMSecsSinceEpoch() / 50` phase for visible busy bars).

- **#89 · P2 · open — Single `NOTIFY changed` signal on all 22 `PlatinumItem` properties causes QML binding loops and redundant work on hover/drag**
  - **Where:** `style/quick/platinumitem.h:17–57`, `style/quick/platinumitem.cpp:86–90`, `:128–143`, `:178–226`, `style/quick/Platinum/Menu.qml:23–32`, `style/quick/Platinum/MenuItem.qml:28–33`.
  - **Concrete failure / cost:** Sharing one `changed()` signal across all 22 properties causes: (1) a direct binding loop in `Menu.qml:23` (`platinumShortcutColumn` reads `row.shortcutWidth` → `MenuItem.qml:30` sets `row.shortcutColumn` → emits `changed()` → re-notifies `shortcutWidth`), plus `MenuItem.qml:32` `panel` binding loops during style switches; (2) every hover (`selected`) or slider drag (`position`) calls `updateImplicitSize()` (re-running `QIcon::fromTheme()`, `QFontMetrics::boundingRect`, and `sizeFromContents`) and re-evaluates `Menu.platinumShortcutColumn` across all $N$ items; (3) `icon()` (`:128–143`) calls `QIcon::fromTheme(m_iconName)` fresh on every `updateImplicitSize()` and `paint()` with no caching.
  - **Confirmed vs suspected:** **Confirmed** with `probe_quick`: opening a 30-item Qt Quick `Menu` with shortcuts emitted 10 `Binding loop detected for property "platinumShortcutColumn"` warnings (`Menu.qml:23`), and switching styles emitted repeated `Binding loop detected for property "panel"` warnings (`MenuItem.qml:32`).
  - **Suggested fix:** Split `NOTIFY` signals by role: `shortcutChanged` for `shortcut`/`shortcutWidth`; `layoutChanged` for size-affecting properties (`elementType`, `text`, `iconName`, `iconSource`, `shortcutColumn`, `horizontal`); and visual-only properties (`selected`, `pressed`, `hovered`, `checked`, `keyboardFocus`, `position`, `panel`, `first`, `last`, `combo`, `edge`) calling only `update()`, never `updateImplicitSize()`. Cache the resolved `QIcon` when `iconName`/`iconSource` changes. **Fidelity:** zero pixel change; verify with `dev/check-quick.sh`.

- **#90 · P2 · open — `Decoration::paint()` ignores `repaintArea`, recomputes title layout/icon/1×1 box pixels on every paint, and `Button` triggers duplicate compositor repaints on unpressed hover and inactive windows**
  - **Where:** `decoration/platinum.cpp:88–142`, `:313–322`, `:390–455`, `:461–472`.
  - **Concrete failure / cost:** (1) `Button::Button` connects `hoveredChanged` and `checkedChanged` to `d->update(geometry())`, even though Platinum boxes have no unpressed hover state (`isPressed() && isHovered()`), no checked state, and are not drawn at all on inactive windows; combined with `KDecoration3::DecorationButton`'s own updates, hovering unpressed buttons emits duplicate compositor damage on both active and inactive windows. (2) `Decoration::paint()` ignores `repaintArea`: a 13×13 button damage still executes `paintFrame()` and `paintTitle()` (up to 4 `QFontMetricsF` constructions in the `{100, 92, 85, 78}` stretch loop plus `window()->icon().pixmap(...)`). (3) `drawBox()` issues 64 (normal) to 95 (pressed) individual 1×1 `fillRect` calls per box (~192–223 calls per active title bar).
  - **Confirmed vs suspected:** **Confirmed** with `probe_deco`, `probe_part3`, and `probe_part5`: 5 unpressed enter+leave cycles on Close emitted 20 `damaged` signals on an active window and 20 on an inactive window; `Maximize::setChecked` emitted 2 `damaged` signals; `Decoration::paint()` took 31.89 µs for a 13×13 button `repaintArea` vs 29.23 µs for a full 416×246 active frame (inactive: 7.22 µs). Pre-baked `QImage` blitting for 3 boxes ran in 0.11 µs vs 5.0–5.8 µs (45–52× faster), with **0 differing pixels at 1.0×, 1.5×, and 2.0×**, but **47 differing pixels at 1.25×**.
  - **Suggested fix:** Disconnect `checkedChanged`; in `Button::Button` only schedule updates on `pressedChanged` when `d->isActiveLook()`, and on `hoveredChanged` only when `isPressed() && d->isActiveLook()`. In `Decoration::paint()`, skip `paintTitle()` when `!repaintArea.intersects(titleBarRect())`, and cache title layout (`caption`, `font`, `width`, `stripeL`, `stripeR`) and the icon `QPixmap` keyed on `(cacheKey, dpr, active)`. For `drawBox()`, use the 6 pre-baked 13×13 `QImage`s (`SmoothPixmapTransform=false`) only at integer scales/axis-aligned transforms, and fall back to horizontal RLE `fillRect`s at fractional scales. **Fidelity warning:** unconditional `QImage` blitting changes 47 px at 1.25×; keep the integer-scale gate and verify at 1×, 1.25×, 1.5×, and 2× with `tools/compare.py diff`.

- **#91 · P2 · open — Per-pixel 1×1 `fillRect` loops in `Platinum::Style` make progress bars, slider grooves, combo/spin boxes, buttons, and tree disclosure triangles 3×–60× slower than necessary**
  - **Where:** `style/platinum/nineslice.h:22–54`, `style/platinum/sprite.h:16–23`, `style/platinum/platinumstyle.cpp:258–321`, `:339–357`, `:539–565`, `:1004–1010`, `:1060–1101`.
  - **Concrete failure / cost:** `drawProgress()` issues 14 individual 1×1 `fillRect` calls per column (~5,600 calls for a 400 px bar); `drawSlider()` calls `drawSprite(..., GrooveMid)` once per horizontal pixel (~2,730 1×1 calls for a 400 px groove to draw 7 solid lines); `drawSprite()` and `drawNineSlice()` emit 1×1 `fillRect`s per pixel (~430 for `PopupArrow`, ~430–650 for `SpinArrows`, ~256 corner calls for `PushDefault`, up to ~289 per tree row for `PE_IndicatorBranch`); `drawBevel()` rebuilds the pressed `NineSlice<2>` on every paint instead of a `constexpr` table.
  - **Confirmed vs suspected:** **Confirmed** with `probe_style`, `probe_part2`, and `probe_part4` (Platinum vs Fusion and coalesced spans):
    - Determinate `ProgressBar` 400 px: 138.10 µs (Fusion 48.82 µs); coalesced bands: 144.03 µs → **2.69 µs (53.5× faster)**, **0 differing pixels** at 1.0×, 1.25×, 1.5×, 2.0×.
    - Busy `ProgressBar` 400 px: 132.41 µs (Fusion 62.67 µs); coalesced horizontal runs: 141.34 µs → **12.89 µs (11.0× faster)**, **0 differing pixels** at all 4 scales.
    - `Slider` 400 px: 74.84 µs (Fusion 21.72 µs); 7-rect groove span: 68.72 µs → **1.10 µs (62.7× faster)**, **0 differing pixels** at all 4 scales.
    - `SpinBox` pressed: 14.59 µs vs Fusion 0.31 µs (**47× slower**); `ComboBox`: 12.55 µs vs 0.44 µs (**28.5× slower**); `PushDefaultBevel`: 6.41 µs vs 0.58 µs (**11× slower**); `PE_IndicatorBranch`: 1.31 µs vs 0.24 µs (**5.5× slower**).
    - `PopupArrow` (22×20): horizontal RLE `fillRect`: 11.89 µs → **3.40 µs (3.5× faster)** with **0 differing pixels** across all 6 tested sprites at 1.0×, 1.25×, 1.5×, and 2.0×. Cached `QImage` blitting (`SmoothPixmapTransform=false`): **0.06 µs (189× faster)** with **0 differing pixels** at 1.0× and 2.0×, **but 348 differing pixels at 1.25× and 746 differing pixels at 1.5×**.
  - **Suggested fix:** Coalesce `drawProgress` (vertical color runs across `FillMid`/`TroughMid`, horizontal runs for barber pole), `drawSlider` groove (7 horizontal `fillRect`s for `GrooveMid`), `drawSprite` and `drawNineSlice` corners (horizontal RLE `fillRect`s, provably 0-diff at every scale), make `ToolPressed` `constexpr`, and avoid painting the pressed half of `SpinArrows` twice. Optionally gate cached `QImage` blitting strictly on integer DPR/axis-aligned transform (`1×`/`2×`), keeping RLE at fractional scales. **Fidelity warning:** unconditional `QImage` blitting alters pixels at 1.25×/1.5×; verify all scales (1×, 1.25×, 1.5×, 2×) with `dev/check-style.sh` and `tools/compare.py diff`.

- **#92 · P2 · open — `QMenu` layout is $O(N^2)$ when a menu has no shortcuts**
  - **Where:** `style/platinum/platinumstyle.cpp:462–473`, `:748`.
  - **Concrete failure / cost:** `sizeFromContents(CT_MenuItem)` calls `menuHasShortcuts(widget)` for every item, which copies `menu->actions()` and linearly scans all $N$ actions. Large menus without shortcuts (bookmarks, recent files, font/syntax lists) stall the UI thread quadratically, exceeding a 120 Hz (8.3 ms) and 60 Hz (16.7 ms) frame budget. (Mentioned without measurement in prose at AUDIT.md:845.)
  - **Confirmed vs suspected:** **Confirmed** with `probe_part2` (warm font cache, no shortcuts):
    - 100 items: Platinum 373 µs vs Fusion 185 µs (2.0×)
    - 200 items: Platinum 1,109 µs vs Fusion 374 µs (3.0×)
    - 500 items: Platinum 5,466 µs vs Fusion 934 µs (5.9×)
    - 1,000 items: Platinum **19,861 µs (19.9 ms)** vs Fusion 1,870 µs (1.9 ms) (**10.6× slower**).
  - **Suggested fix:** Cache `menuHasShortcuts` per `QMenu` (e.g. a map on `Style` or cached property invalidated via an event filter on `ActionAdded`/`ActionRemoved`/`ActionChanged` and `destroyed`). **Fidelity:** zero pixel change; verify with `dev/check-style.sh` and `dev/check-quick.sh`.

- **#93 · P2 · open — `ComboBox.qml` re-measures every model item through `comboWidthHint()` on every `control.width` change, even while closed**
  - **Where:** `style/quick/Platinum/ComboBox.qml:42–59`, `style/quick/platinumitem.cpp:156–171`.
  - **Concrete failure / cost:** The `popup.implicitWidth` `Binding` combines `control.width` with the JS loop over all `control.popup.count` items and C++ `comboWidthHint(texts)` (`QFontMetrics::horizontalAdvance` per item). Resizing a window re-measures every item of every closed `ComboBox` on every resize step.
  - **Confirmed vs suspected:** **Confirmed** with `probe_quick`: resizing a single closed 200-item Qt Quick `ComboBox` 50 times took **27.97–29.49 ms (559–590 µs per resize)**.
  - **Suggested fix:** Separate the item-width measurement into its own property (independent of `control.width`, and gated on `popup.visible` or item/text changes) and bind `popup.implicitWidth` to `Math.max(control.width, control.platinumMinListWidth)`. **Fidelity:** zero pixel change; verify with `dev/check-quick.sh` (including live model rename parity from #63).

- **#94 · P3 · open — `styleWatcher()` leaks a recreated `QWidget` during/after `aboutToQuit`, and `PlatinumItem` lacks null guards on `QApplication::style()`**
  - **Where:** `style/quick/platinumitem.cpp:20–33`, `:109`, `:153`, `:170`, `:183`, `:233`.
  - **Concrete failure / cost:** (1) `aboutToQuit` deletes `watcher` and resets `watcher = nullptr`, so any `PlatinumItem` constructed or receiving an event during/after `aboutToQuit` recreates a top-level `QWidget` that is never deleted. (2) `margin()`, `comboWidthHint()`, `updateImplicitSize()`, and `paint()` dereference `QApplication::style()` without null checks. (3) `updateActive()` (`:109`) compares `style()->name() == QLatin1String("platinum")` case-sensitively, whereas `Platinum::Style::Style()` (`platinumstyle.cpp:623`) sets `objectName` to `"Platinum"` (only matching because `QStyleFactory::create()` lowercases it). (4) Every `PlatinumItem` calls `watcher->installEventFilter(this)` with no `removeEventFilter` in a destructor.
  - **Confirmed vs suspected:** **Confirmed** `styleWatcher()` leak with `probe_quick watcher-teardown` (`TopLevelWidgets`: 1 → 0 in `aboutToQuit` → 1 after creating a `Switch` in `aboutToQuit` → 1 leaked after `app.exec()`). **Suspected (code inspection only):** null `QApplication::style()` dereference during teardown or re-entrant style change.
  - **Suggested fix:** Return `nullptr` from `styleWatcher()` once `QCoreApplication::closingDown()` (or a `quitting` flag) is true; emit a `styleChanged()` signal from a single helper `QObject` instead of per-item `installEventFilter`; guard `QStyle *style = QApplication::style(); if (!style) return ...;` at all 4 call sites; compare style name case-insensitively. **Fidelity:** zero pixel change.

- **#95 · P3 · open — `RangeSlider.qml` allocates two full-width `QQuickPaintedItem` textures for 15×16 thumbs (and `Dialog`/`Drawer` allocate full-window textures with interior overdraw)**
  - **Where:** `style/quick/Platinum/RangeSlider.qml:23–48`, `style/quick/Platinum/Dialog.qml:13–22`, `style/quick/Platinum/Drawer.qml:11–21`, `style/platinum/platinumstyle.cpp:372–374`, `:397–398`, `:488–499`.
  - **Concrete failure / cost:** `RangeSlider`'s `firstThumb` and `secondThumb` each bind `width: control.width; height: control.height`, allocating two extra full-width RGBA backing images/GPU textures and repainting/uploading the entire slider width on every drag frame instead of a 19×16 thumb+focus rect (~21× texture waste on a 400 px slider; 4× at 2× DPR). Similarly, `Dialog.qml`/`Drawer.qml` back the entire dialog/drawer area with a `QQuickPaintedItem` texture, and `drawModalFrame`/`drawMenuPanel`/`drawField` fill the full interior with black before overwriting it with the fill color (2×–3× pixel overdraw).
  - **Confirmed vs suspected:** **Confirmed** `RangeSlider` dimensions with `probe_quick` (`groove=400x16, firstThumb=400x16, secondThumb=400x16` on a 400 px `RangeSlider`). `Dialog`/`Drawer` sizing and overdraw confirmed by code inspection.
  - **Suggested fix:** Size and position `firstThumb`/`secondThumb` to the thumb rect + 2 px focus-line margin (`19×16` horizontal, `16×19` vertical), and replace full-rect black fills in `drawModalFrame`/`drawMenuPanel`/`drawField` with four 1 px edge rects. **Fidelity:** zero pixel change; verify with `dev/check-quick.sh` and `dev/check-style.sh`.

- **#96 · P3 · open — Redundant `updateButtonsGeometry()` / `update()` bursts, per-resize `Qt::UniqueConnection` scans, and unguarded `Button` factory constructor in `Decoration`**
  - **Where:** `decoration/platinum.cpp:218–226`, `:242–247`, `:269–304`, `:474–477`.
  - **Concrete failure / cost:** (1) `recalculate()` calls `updateBorders()` (emitting `bordersChanged` → synchronously calling `updateButtonsGeometry()` → `update()`), then calls `updateButtonsGeometry()` and `update()` again; connecting all three maximized signals to `recalculate()` produces 15 `damaged` signals per maximize/unmaximize, and 10 width changes produce 40 `damaged` signals. (2) `updateButtonsGeometry()` runs `connect(b, &DecorationButton::visibilityChanged, ..., Qt::QueuedConnection | Qt::UniqueConnection)` for every button on every width resize step, repeatedly locking Qt's connection mutex and scanning connections. (3) `Button::Button(QObject *parent, const QVariantList &args)` passes `args.value(1).value<Decoration *>()` directly to `KDecoration3::DecorationButton` without validating `args`, segfaulting if invoked via `KPluginFactory` with missing/non-Platinum args (normal KWin/KCM calls pass valid `{type, deco}`).
  - **Confirmed vs suspected:** **Confirmed** with `probe_deco` and `probe_part3`: maximize/unmaximize emitted 15 `damaged` signals each; 10 width changes emitted 40 `damaged` signals; `KPluginFactory::create<DecorationButton>(nullptr, {})` segfaulted (exit 139) whereas valid `{Close, KDecoration3::Decoration*}` succeeded.
  - **Suggested fix:** Connect `visibilityChanged` once in `Button` construction and call `setSpacing(BoxGap)` once in `init()`; avoid double-calling `updateButtonsGeometry()`/`update()` inside `recalculate()` and deduplicate maximized signal handling; use a validating factory lambda for `Platinum::Button` in `K_PLUGIN_FACTORY_WITH_JSON`. **Fidelity:** zero pixel change; verify with `dev/shoot-deco.sh` and `dev/kwin-test.sh`.

- **#97 · P3 · open — `Style::subControlRect(CC_GroupBox)` recomputes `QFontMetrics::boundingRect()` 3 times per `drawGroupBox()` paint**
  - **Where:** `style/platinum/platinumstyle.cpp:825–852`, `:1114–1116` (and `hitTestComplexControl` `:934–941`).
  - **Concrete failure / cost:** `subControlRect(CC_GroupBox)` calls `fm.boundingRect(QRect(), Qt::TextShowMnemonic, gb->text)` unconditionally before switching on `sub`, even for `SC_GroupBoxFrame`, `SC_GroupBoxCheckBox`, and `SC_GroupBoxContents`. `drawGroupBox()` invokes `subControlRect` three times per paint, running three identical text-layout calls. Similarly, `hitTestComplexControl(CC_ScrollBar)` recomputes `scrollLayout()` up to 5 times per pointer hit-test.
  - **Confirmed vs suspected:** **Confirmed** by code inspection. Overall `drawGroupBox` still ran faster than Fusion (`9.84 µs` vs `22.95 µs`), so impact is low.
  - **Suggested fix:** Compute `label` only inside `case SC_GroupBoxLabel:` and compute `scrollLayout()` once in `hitTestComplexControl()`. **Fidelity:** zero pixel change; verify with `dev/check-style.sh`.

### Clean areas

- `style/platinum/plugin.cpp` and `tools/check-wallpaper.cpp`: clean, minimal, no leaks or lifetime bugs.
- `style/platinum/platinumstyle.cpp` 64-bit scroll/slider arithmetic (`scrollLayout`, `drawProgress` range math, `drawSlider` tick bounds) and `polish`/`unpolish` property save/restore symmetry: clean (AUDIT #15, #18).
- `decoration/platinum.cpp` `paintFrame` / `drawStripes` boundary guards (survived `0×0` paint cleanly) and `QTimer::singleShot(0, this, ...)` context lifetime: clean.
- `style/quick/platinumitem.cpp` `QGuiApplication`-only fallback (`probe_quick gui-app` ran cleanly with `m_active = false`), `M9_QUICK_TEST` gate on `setApplicationStyle`, and `ToolButton.qml` `Loader` gating: clean.
- All three plugins build cleanly under `-Wall -Wextra` with zero warnings and produced no ASan/UBSan diagnostics on the exercised paths (leak detection disabled).

### Checks and limits

- Compiled `decoration/`, `style/platinum/`, and `style/quick/` into an isolated scratch directory (`-O2` and `-O1 -g -fsanitize=address,undefined`): 0 compiler warnings.
- Executed standalone C++ probes (`QT_QPA_PLATFORM=offscreen`, plus `QSG_RENDER_LOOP=threaded` for Qt Quick) comparing `Platinum` against `Fusion` and `org.kde.breeze`, and verified pixel diffs at 1.0×, 1.25×, 1.5×, and 2.0× across 6 sprites, determinate/busy progress bars, slider grooves, and decoration title-bar boxes.
- Limits: offscreen Qt and KDecoration3 preview only; did not run nested KWin / live Plasma / real GPU OpenGL or Vulkan compositor or touch the live desktop; `QPixmap` thread races under real Wayland/GPU drivers and null-`viewport()` / null-`QApplication::style()` teardown paths remain code-inspection suspicions rather than live crashes.

## 2026-11-22, Codex (GPT-6.2) — bundled cursor audit and fixes

Reviewed the cursor packaging and lifecycle introduced in `e74412a`.
Finding locations refer to that revision.

- **#81 · P2 · fixed and verified** — `uninstall.sh:328–332`.
  Uninstall deleted the pack after it was picked separately under Breeze,
  leaving `kcminputrc` pointing to an absent theme. Reproduced in a disposable
  home. The uninstaller now keeps the selected pack and its record until the
  user switches cursors. It can put back a previously installed pack with
  the same ID. The tests cover both paths and compare the dry run against
  the resulting config.
- **#82 · P2 · fixed and verified** — `scripts/common.sh:466–471`.
  The checksum comparison stripped trailing line breaks from edited
  symbolic-link targets. Replaced `x-cursor` with a link to the same target
  plus a line break. Uninstall deleted it before the fix and preserved it
  afterward. Existing install records still work.
- **#83 · P2 · fixed and verified** — `install.sh:169–177`.
  A damaged archive passed the dry run and failed only after the real run
  had placed both plugins, the login script and Qt Quick files. Reproduced
  with a zero-length `left_ptr`. Both modes now check the SHA-256 of the
  entire reviewed archive before changing the installation.
- **#84 · P2 · fixed and verified** — `install.sh:169–179`.
  In an offscreen Plasma 6.8 session with no `XCURSOR_PATH`, Plasma's cursor
  picker omitted the XDG data directory and did not list the black pack.
  After sourcing the updated login script, the picker listed
  `macOS-cursors` and Breeze with a custom data directory containing spaces.
  The login script retains custom cursor search paths.

The black-only archive reproduces byte for byte from the tagged v2.0.1
release. libXcursor loaded all 145 names, including 101 aliases, at 24,
32 and 48 px. The archived license matches upstream's tagged source,
linked from `cursors/README.md`.

The installer passed 367/367 checks, live install and undo 37/37,
Plasma artwork 19/19, Qt Widgets 135/135, and Qt Quick 29/29. The
offscreen cursor selector applied macOS and Breeze Light in turn. An
uninstall between the selections kept macOS and the retry removed it.
The user's physical desktop and on-screen cursor appearance are pending.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's cursor findings #78–#80

At the user's request the black theme's ID is now `macOS-cursors`
(`~/.icons/macOS-cursors`), so it can't collide with another `macOS` theme.

- **#78** (verified: the README's `tar -C ~/.icons` wrote into an existing
  folder): `tools/install-black-cursors.sh macOS.tar.xz` unpacks into a
  temporary folder, checks the pointer file, and moves it to
  `~/.icons/macOS-cursors` only if nothing is there; otherwise it stops
  with nothing changed. The README uses it.
- **#79** (verified: `grep -F '[macOS]'` matched a title): install.sh
  matches the ID at the end of Plasma's "Title [ID]" line and finds the
  theme's folder.
- **#80** (verified: no check of the cursor data): `xcursor_ok` reads the
  pack's `left_ptr` (Xcursor magic, table of contents, the image chunk's
  header and pixels inside the file) before switching.

Checks: `dev/test-install.sh` 339 of 339 (new: a title naming the ID, a
truncated `left_ptr`, the helper installing a pack and refusing an existing
`macOS-cursors`); `dev/test-install-live.sh` 36 of 36. Not seen on the
user's screen.

## 2026-11-21, Codex (GPT-6.2) — audit the optional black cursor integration

Reviewed the working-tree installer and README. The actual upstream black
pack decoded at 24 px with libXcursor. A fresh apply and uninstall in a
disposable home selected the black theme, restored the previous theme and
size byte for byte, and left the external pack in place. The unchanged
installer and nested Plasma checks previously passed 332/332 and 36/36.

- **#78 · P2 · fixed (next section up)** — `README.md:120`. The documented extraction overwrites a customized cursor theme at `~/.icons/macOS`. Seeded a custom `index.theme` in a throwaway home and ran the documented command against the upstream archive. The upstream file replaced the custom file without keeping a copy. Check for a pre-existing destination before extracting.
- **#79 · P3 · fixed (next section up)** — `install.sh:70`. The text check can mistake a display name for the exact theme ID. Plasma listed a fixture with ID `macOS-White` and title `White [macOS]` as `White [macOS] [macOS-White]`. The black opt-in dry run exited 0 and planned to select the absent `macOS` theme. Match the ID field.
- **#80 · P3 · fixed (next section up)** — `install.sh:68–71`. Plasma's list can include a broken cursor pack. Seeded the black ID with an invalid `left_ptr` in a throwaway home. The preflight accepted it, while libXcursor rejected the file. Validate the cursor data before switching.

The fresh retest used an offscreen Qt session with a private D-Bus.
The working-tree audit changed documentation only. The user's on-screen
cursor review is pending.

## 2026-11-21, Codex (GPT-6.2) — verify optional black cursors

Verified the working-tree cursor option with the black `macOS` folder
from upstream v2.0.1 in a disposable home. The Linux archive also contains
a white folder and the README extraction selects the black folder alone.
Plasma's list showed the exact black theme ID. Applying with the opt-in
wrote that ID to `kcminputrc`. Uninstall restored the previous Breeze
Light preference byte for byte and left the external package intact.
The offline suite confirmed the white-only pack is rejected before any
change and the black dry run is read-only. Install passed 332/332, live
install 36/36, Plasma artwork 19/19, Qt Widgets 135/135, and Qt Quick
29/29. No new findings. The desktop visual check remains pending.

## 2026-11-21, Codex (GPT-6.2) — fix wallpaper findings #75–77

- **#75 · P2 · fixed and verified** — Uninstall leaves selected wallpaper packages and their install records in place. It reads the running Plasma desktop when available and the saved config when logged out. A nested Breeze session selected a package and an individual image on different screens. Both survived the dry run and first uninstall. Switching both to solid colors let the next uninstall remove the packages. The panel layout remained intact. The offline test also covered a percent-encoded URL and confirmed that uninstall removes an unselected package immediately.
- **#76 · P3 · fixed and verified** — `install.sh --apply` uses a temporary Qt image-reader probe and warns before switching when it cannot open the JPEG XL files. The no-decoder test verified the warning precedes the successful theme switch. On the normal Qt installation the same probe opened both images and ran under ASan/UBSan with leak detection disabled.
- **#77 · P3 · fixed and verified** — The live test compares exposed areas on both virtual screens against a Qt render of the installed Pastel Ribbon Landscape. The normal suite passed 33/33. A disposable copy with a nonexistent default failed the wallpaper comparison while the other 32 checks passed.

The install and undo suite passed 326/326, Plasma artwork 19/19, Qt Widgets
135/135, and Qt Quick 29/29. These checks used disposable homes and nested
Plasma. The user's desktop remains available for visual review.

## 2026-11-21, Codex (GPT-6.2) — audit the wallpaper lifecycle

Reviewed both wallpaper packages, the global-theme default, and install
and uninstall in the working tree on `83b8bd8`.

- **#75 · P2** — `uninstall.sh:215–221` and `uninstall.sh:279–295`. The documented picker-only workflow can leave both desktops pointing to deleted images. In a two-screen nested session, kept Breeze active, ran the plain installer, and selected Pastel Ribbon Landscape on one screen and Lavender Desktop Pattern on the other through Plasma's image configuration. Tested a package-directory URL and an image-file URL. Both displayed before uninstall. Uninstall exited 0 and removed both packages while leaving the desktop config byte for byte. After restarting the disposable shell, both stored URLs still pointed to the deleted assets and neither selected image displayed. Treat references to the installed wallpapers separately from the global theme's active state and preserve unrelated desktop changes.
- **#76 · P3** — `install.sh:60–64`. The installer checks that the JPEG XL files are readable. It gives no warning if Plasma cannot decode them. Qt opened both files at 3840 × 2160 on this machine. With only the JPEG XL handler excluded from a disposable Qt plugin directory, Qt rejected both files as unsupported. Applying the global theme in a nested shell using that directory succeeded and rendered a white desktop. README.md documents the decoder dependency. Add a readable fallback format or warn before switching on systems without the handler.
- **#77 · P3** — `dev/test-install-live.sh:166–167`. The live test checks the wallpaper plugin name alone. Replaced the default wallpaper ID with a nonexistent ID in a disposable copy. The separate global-theme screenshot showed a different wallpaper, yet the live installer suite passed 25/25. Check the resolved wallpaper or representative rendered pixels as well.

The existing clean-build captures use the supplied artwork. All new
checks ran in disposable homes. This audit changed documentation only.

## 2026-11-21, Codex (GPT-6.2) — verify the second desktop wallpaper

Reviewed Lavender Desktop Pattern and the wallpaper installer changes
in the working tree on `83b8bd8`. No new findings. An upgrade from the
one-wallpaper installer copied both JPEG XL files byte for byte. KDE's
wallpaper picker model listed both titles. Uninstall removed both
packages and preserved the previous desktop config and a separate user
wallpaper.

Nested Plasma rendered Pastel Ribbon Landscape when Platinum was applied
and Lavender Desktop Pattern when selected. In three unobstructed areas
of the 1600 × 900 screenshots, the mean difference from the rescaled
source for each wallpaper was below one RGB level per channel. Installer
checks passed 316/316 and live install and undo passed 25/25. Plasma
artwork passed 19/19, Qt Widgets 135/135, and Qt Quick 29/29. The user's
desktop review is pending.

## 2026-11-21, Codex (GPT-6.2) — check the wallpaper integration

Reviewed the working-tree wallpaper integration on `83b8bd8`. No new
findings. The Plasma wallpaper picker listed Pastel Ribbon Landscape.
Applying the global theme rendered the original artwork in nested Plasma.
Three unobstructed areas of a 1600 × 900 screenshot matched a rescale of
the decoded 3840 × 2160 JPEG XL source with a mean error under one RGB
level per channel. The installer copied the image byte for byte and an
upgrade from the previous installer kept the existing desktop config.

In the two-screen suite a plain install kept each screen’s seeded
wallpaper. Applying Platinum selected the image plugin on both screens.
Uninstall restored both originals and removed the package. The installer
suite passed 314/314, nested install and undo 24/24, Plasma artwork 19/19,
Qt Widgets 135/135, and Qt Quick 29/29. The Qt Quick and decoration
previews ran under ASan/UBSan with leak detection disabled. Verification
used throwaway homes and nested Plasma. The user’s desktop test is pending.

## 2026-11-21, Codex (GPT-6.2) — fix Kwi tab close findings #72–74

Fixed all three findings in the working tree on `83b8bd8`.

- **#72 · P3 · fixed and verified** — `style/quick/Platinum/ToolButton.qml` uses the tab indicator when the Qt Quick caller supplies the tab's selected state and the default small, untinted tab-close icon. The generic QStyle interception is gone. The 32 px icon, custom tint, and ordinary matching button each rendered pixel-identically to their KDE ToolButton counterparts.
- **#73 · P3 · fixed and verified** — The Qt Quick control supplies selected, hover, press, focus, and enabled state to the Qt tab indicator. Disabled indicators are further dimmed so they differ from enabled inactive tabs. In a disposable two-tab Kwi session, the active tab was orange at rest, the inactive tab turned orange on hover, and clicking it closed that tab. Konsole's tab area was pixel-identical to the prior build. The native Kwi Qt Quick path is the reference for the selected color.
- **#74 · P3 · fixed and verified** — `dev/check-quick.sh` gained eight checks covering size, selection, disabled and pressed states, size and tint overrides, ordinary buttons, and fallback after switching to Fusion. All 29 checks passed. The new tests rejected the original oversized bevel and the first fix's missing selected and disabled cues and overwritten custom icons when tested against those builds.

The close indicator remained compact and its four states stayed distinct in offscreen renders at 150% and 200%. Qt Widgets passed 135/135, Plasma artwork 19/19, install and uninstall 312/312, and nested Plasma install and undo 19/19. Qt Quick and decoration previews rendered under ASan/UBSan with leak detection disabled and no sanitizer diagnostics. The user reviewed the follow-up fix on their desktop and reported that it worked well. The automated coverage and detailed state checks are recorded above.

## 2026-11-21, Codex (GPT-6.2) — audit of the Kwi tab close fix

Reviewed the #71 working-tree patch on `83b8bd8` using Kwi `395b1de` and a Qt Quick probe. The fix removes the oversized frame and retains hover and press feedback. A fresh two-tab Kwi session confirmed the close button highlights on hover and closes the clicked tab. The neighboring New Tab button matched the earlier build pixel for pixel. Konsole's tab area also matched the earlier build pixel for pixel.

- **#72 · P3** — `style/platinum/platinumstyle.cpp:1168–1173`. The rule applies to any matching Qt Quick tool button with the icon name `tab-close-other`. Drawing the Qt indicator discards the caller's icon size and tint. An offscreen button requesting a 32 px magenta icon rendered with magenta pixels before the patch and a 14 × 14 gray indicator after it. Preserve explicit icon requests or narrow the rule to the intended control.
- **#73 · P3** — `style/platinum/platinumstyle.cpp:1171–1173`. The active tab loses its colored close cue. In nested KWin, Kwi's native Qt Quick style showed an orange close indicator on the active tab and a gray one on the inactive tab. Both were gray at rest under Platinum. In the offscreen probe the enabled idle and disabled icons also matched pixel for pixel, while press and keyboard focus each changed the icon. Qt's tab primitive draws the idle option as disabled when the style does not supply a selected or raised state. The reference tabs in docs/REFERENCE.md have no close control, so the comparison uses Kwi's native indicator.
- **#74 · P3** — `dev/check-quick.sh:46`. The automated checks miss the original regression. Removed the #71 patch in a disposable project copy and reproduced the 25 px bevel in the named Qt Quick close-button probe. The existing Qt Quick suite still passed 21/21 and Qt Widgets passed 135/135. Add a focused check for this button and its states.

The audit ran in an isolated compositor and offscreen Qt. The other applications that might request the same icon name and the user's physical desktop were outside the verification. This audit changed documentation only.

## 2026-11-21, Codex (GPT-6.2) — Kwi tab close indicator

- **#71 · P3 · fixed and verified in nested KWin** — `style/platinum/platinumstyle.cpp:1166`. Kwi `395b1de` requests the `tab-close-other` icon on a flat, icon-only tool button under the Platinum Qt Quick style. The style drew its 25 px toolbar bevel over the tab. The corresponding Konsole control uses Qt's tab close indicator. Platinum now routes this semantic close control through the tab close primitive, keeping its existing button geometry. No reference tab in docs/REFERENCE.md has a close control, so this uses Qt's artwork.
- Reproduced the user's raised button in nested KWin before the change. After the change, Kwi showed compact gray indicators that highlighted on hover, and clicking one closed the intended tab. The New Tab button was pixel-identical to the baseline, and Konsole showed its usual close indicator. The updated visual awaits the user's desktop test.
- A Qt Quick probe rendered the indicator at 100%, 150% and 200% display scale. Qt Widgets passed 135/135, Qt Quick 21/21, Plasma artwork 19/19, install and uninstall 312/312, and nested Plasma install and undo 19/19. The close control and window decoration rendered under ASan/UBSan with leak detection disabled.

## 2026-11-21, Codex (GPT-6.2) — verify panel fixes #69 and #70

Fixed both findings in the working tree on `83b8bd8`.

- **#69 · P3 · fixed and verified** — `dev/check-plasma.sh` now compares every pixel of both rounded ends and the divider after live resizes to 32, 34, 38, and 40 px. All 19 Plasma comparisons passed, including the seven native-height checks. Erasing rows 5–23 of all three pieces in a disposable 38 px capture failed each of the three corresponding comparisons.
- **#70 · P3 · fixed and verified** — The divider skips a trailing dot if its highlight would land in the bottom margin. The repeat uses both rows of each dot as measured in `reference/desktop-first-check.png` (docs/REFERENCE.md, right end of the menu bar). The new checker rejected both previous captures at 34 and 40 px, and the corresponding fixed captures matched all divider pixels. The 32 and 38 px comparisons also passed.

Nested Plasma artwork was checked at 100% display scale. The updated artwork has yet to be checked on the user's physical displays. Qt Widgets passed 135/135, Qt Quick 21/21, install and uninstall 312/312, and nested Plasma install and undo 19/19. Eleven SVGs, three Plasma metadata files and both color schemes parsed successfully. The Qt Quick and window decoration previews rendered with ASan/UBSan and leak detection disabled, with no sanitizer diagnostics.

## 2026-11-21, Codex (GPT-6) — review of the panel-resize fix

Reviewed the working tree on `83b8bd8`. In the user’s 32 px screenshot at 100% display scale, both ends reach the screen edges, the bottom border is on row 31, and the final divider dot has both its dark and light rows at 25–26. The Plasma artwork suite passed 8/8 in a fresh nested session, including the original 20 px reference checks.

- **#69 · P3** — `dev/check-plasma.sh:69–74`. The 38 px check can pass with most of the resized artwork missing. In a disposable copy of the captured image, erased rows 5–23 of both ends and the divider. The checker still passed 8/8. Compare the complete end and divider regions so a missing curve or interrupted run of dots fails the check.
- **#70 · P3** — `plasma/make-plasma.py:549`. At some heights the divider’s bottom margin cuts off the highlight of its last dot. In fresh 100% captures at 34 and 40 px, the last dark dot row (28 and 34 respectively) was followed by panel gray (`#DDDDDD`). Every complete dot has a light row (`#BBBBBB`) directly below the dark row. End the repeat on a complete dot before drawing the margin. The 32 px desktop capture and the 38 px test capture both have a complete final dot.

Additional captures used a disposable Plasma session. Physical mixed-scale display moves and other live panel configurations were outside this check. The installer and unrelated theme components were outside the scope of this review.

## 2026-11-21, Codex (GPT-6) — #23 top panel resizing

#23 (P3), corner and divider geometry fixed in the working tree. The 38 px desktop screenshot showed the pieces ending at row 19. The generated menu-bar widget now sizes them from the allocated height. The round ends compensate for the extra end padding Plasma adds to thicker panels.

The seven existing comparisons passed at 20 px. A new eighth check resizes the running panel to 38 px and samples the screen corners, lower border and extended dotted grip. Separately captured all combinations of panel heights 20, 32, 38 and 52 with virtual display scales 100%, 125%, 150% and 200%. All 16 panel heights matched the expected rounded physical size, with black corner pixels at both screen edges at the top and bottom of the bar. Fractional-scale bevel shading is not reference-measured. The updated widget has only run on a disposable desktop.

## 2026-11-21, Codex (GPT-6) — audit and repair Claude's latest changes

Reviewed commits `e1fe656` and `49c340b`. Locations below refer to the audited commit so they remain usable after the fixes. All findings were fixed locally and checked in disposable homes.

| Finding | Location at `49c340b` | Reproduction and repair |
|---|---|---|
| #59 · P1 · fixed | `scripts/common.sh:835` | Saved copies of the generated login hook as `-saved.sh` and `-2.sh`. Reinstall deleted both. Reinstall now identifies the hook by its own path and contents and reads it as data. The copies survived, and an edited hook survived simulated login and reinstall byte for byte. |
| #60 · P1 · fixed | `scripts/common.sh:811` | Appended a personal line to the temporary `qmldir`. The next login deleted the file because its first line still matched. Cleanup now checks the whole regular file. The edited contents survived login and a subsequent install/uninstall round trip. |
| #61 · P2 · fixed | `uninstall.sh:148` | Applied over a GTK asset whose filename ended in a newline, changed its contents, and ran uninstall. It refused the intact backup because command substitution stripped the final newline. Decoding directly into a variable restored the original name and bytes. |
| #62 · P2 · fixed | `scripts/common.sh:800` | Forced creation of the temporary Kirigami link to fail. Uninstall exited 1, then its retry exited 0 with a QML module and no cleanup hook. The hook now goes in first, the complete module is published last, and a retry retires the interrupted attempt. Forced both link and module publication failures. In each case a retry restored the session module and the next login removed its directories. |
| #63 · P2 · fixed | `style/quick/Platinum/ComboBox.qml:51` | Renamed a model item without changing the item count. The list stayed 65 px wide for text needing 292 px. A widget comparison with “Mountain Lavender” differed in 3,406 of 7,803 pixels. The width now observes the delegates' text. The 153 × 51 popup matched the widget pixel for pixel after the rename. |
| #64 · P3 · fixed | `scripts/common.sh:771`, `uninstall.sh:345` | Seeded a personal file at the module path, installed, then moved the installed module out of the way. The dry run promised a pass-through at that empty path. The real run restored the personal file there. The preview now accounts for both removals and restorations. |
| #65 · P3 · fixed | `scripts/common.sh:772`, `README.md:69` | With that personal file restored, a launcher still requesting Platinum failed with “module Platinum is not installed”. Uninstall had exited silently on the occupied path despite the README's assurance. It now explains the need for a fresh login and preserves the personal file. |
| #66 · P3 · fixed | `install.sh:213`, `PLAN.md:17` | Followed the documented first switch from Breeze. An app started after apply still reported `org.kde.desktop`. It reported `Platinum` after sourcing the login environment again. The installer and first-install instructions now call out the login after apply. |
| #67 · P3 · fixed | `README.md:17` | The dependency list omitted the providers of Qt Quick/QML and KF6 CoreAddons development files. Checked the build commands and the installed packages owning the three pkg-config files, then updated the list. |
| #68 · P3 · fixed | `dev/quick-regions.qml:113` | A repeat of the Fusion fallback check differed in 977 pixels of the File title by one blue level. Both renders placed the idle test bar under the offscreen pointer while KDE animated the highlight. After moving the bar clear of the pointer, three fresh pairs of fallback and KDE renders were byte-identical. |

The installer suite passed 312/312, nested two-screen Plasma 19/19, Qt Widgets 135/135, Qt Quick 21/21 and Plasma artwork 7/7. Also tested migration from both `0cd95a2` and `e1fe656` with untouched files, an edited module and an edited hook. Built the three plugins with ASan/UBSan and rendered the Quick scenes and decoration preview without sanitizer diagnostics, with leak detection disabled. Rendered the widget gallery at 1, 1.25, 1.5 and 2 times scale and a maximized window in nested KWin.

The private reference matched the desktop sample at (5,500), all 20 rows of the menu-bar column at x=700, and the selected and unselected file-dialog samples. Inspected the checkbox comparison, nested menu and renamed combo. All 11 SVGs, three Plasma metadata files and the color scheme parsed. A binary-diff and filename scan of 44 reachable Git commits found no tracked private capture or font file. The publication review of pixel tables remains deferred under #25.

The tests used private sessions, software rendering for Qt Quick, simulated logins and a stand-in for user systemd. A real login, the user's systemd service, physical mixed-DPI moves, a live package upgrade and the user's visual judgment remain unverified.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #53–#58

Verified each by reading the code (and, for #57, sha256sum's output for
such a name), then fixed them with a test for each. Uncommitted at the time
of writing.

| Finding | Verified | Fix |
|---|---|---|
| #53 (reopened) | yes (read: QComboBox::showPopup widens the list to the combo box's width hint, its widest text through `CT_ComboBox`; the Qt Quick list took the rows' width, 2 px more) | The item works out the same hint (`comboWidthHint`); the list is the wider of it and the button. New narrow fixture (60 px, narrower than its items) on both sides: both lists 90 px, pixel exact. |
| #54 | yes (read: the script was written with `>`) | The pass-through's login script takes a free name (`macos9-theme-cleanup-2.sh`, ...); install finds any of them by its first line. Tested with a script of the user's at the name. |
| #55 | yes (read: the cleanup removed any link pointing at KDE's plugin) | The link is made only if none is there, and the cleanup removes it only if it made it. Tested with a link of the user's. |
| #56 | yes (read: only `qmldir` was checked; `mkdir` on a file fails) | No pass-through if anything is at the module's place (or a folder can't be made there). Tested with a file and with a folder of the user's. |
| #57 | yes (sha256sum writes `\<hash>  name\\x` for such names) | The parser takes the leading `\` and unescapes the name. Tested with `custom\blue.svg` in `gtk-3.0/assets`. |
| #58 | yes (read: the dry run saw the module still there) | In a dry run, what the real run will have removed counts as free, unless something is put back there (which also fixed the real run's check: it now looks only at what's on disk). Tested. |

### Checks

- `dev/test-install.sh`: 272 of 272. `dev/test-install-live.sh`: 19 of 19.
- `dev/check-quick.sh`: 21 of 21. Style and Plasma unchanged since 135/135
  and 7/7.

### Limits

- Not on the user's desktop; no real login.

## 2026-11-21, Codex (GPT-6) — review the fixes for #49–53

Reviewed main at `0cd95a2`. All 429 project checks passed. The new pass-through lets an existing launcher start Qt Quick apps after an ordinary uninstall. The additional cases below concern what happens when uninstall encounters files that already belong to the user. All cases used fresh throwaway homes and the project's scripts.

| Finding | Location | What happened and how it was verified |
|---|---|---|
| #54 · P1 · fixed (next section up) | `scripts/common.sh:792`, `scripts/common.sh:786` | Uninstall overwrites an existing login script. Seeded a personal `plasma-workspace/env/macos9-theme-cleanup.sh`, then ran plain install and uninstall. Both exited 0. The original contents were replaced with the generated cleanup script. Running that script to simulate the next login deleted the file. The hook needs the same ownership protection as other install targets. |
| #55 · P1 · fixed (next section up) | `scripts/common.sh:766`, `scripts/common.sh:777` | The next login deletes a user's restored Kirigami link. Seeded the target link to KDE's desktop plugin before install. Uninstall restored it. The generated cleanup script subsequently removed it because it pointed to the expected plugin, even though this cleanup had never created that link. Verified the link existed immediately after uninstall and was gone after running the hook. |
| #56 · P2 · fixed (next section up) | `uninstall.sh:372`, `scripts/common.sh:755`, `scripts/common.sh:764` | Uninstall tries to create the pass-through inside a path it just restored to the user. Seeded a regular file at the Platinum QML module path. Install succeeded and uninstall restored its contents, but then failed at mkdir. A second uninstall failed identically. With a pre-existing directory containing only a personal file, uninstall instead succeeded and added its own qmldir inside the restored directory. |
| #57 · P2 · fixed (next section up) | `uninstall.sh:143`, `uninstall.sh:150` | A valid GTK asset filename can block rollback. Seeded a regular file named `custom\blue.svg` in gtk-3.0/assets. Apply succeeded. Uninstall refused the untouched backup as damaged. Running GNU sha256sum in strict check mode directly on that same SUMS file reported OK. Its escaped filename format includes a leading backslash before the hash, which the new parser rejects. |
| #58 · P3 · fixed (next section up) | `scripts/common.sh:755`, `uninstall.sh:372` | Uninstall preview misses the pass-through and login cleanup. In another fresh home, plain install, preview and uninstall all exited 0. The preview omitted the pass-through; the actual run created it and reported doing so. The preview checks for the existing qmldir while the real uninstall first removes it. |

**Previous findings.** The nested suite now launches a Qt Quick app from an environment inherited before uninstall, covering the original #49 failure. Empty backups, the named menu icon and slider focus checks passed (#50–52). **#53 (P3, reopened for narrow controls):** the replacement fixture at `dev/quick-regions.qml:93` sets the button to 140 px and passes. Restoring just the original 102 px width in temporary copies of the two fixtures reproduced the original difference: a 103×51 Quick popup beside a 102×51 widget popup and 145 differing pixels along the right edge. The wider test does not establish narrow-popup parity.

**Other checks and limits.** Installer 249/249, nested live 19/19, Qt Widgets 135/135, Qt Quick 19/19 and Plasma 7/7. Built all three plugins with ASan/UBSan and ran the Quick scenes and decoration preview without sanitizer diagnostics (leak detection disabled). Rendered widget galleries at scales 1, 1.25, 1.5 and 2. Inspected the nested maximized window and desktop menu. Compared checkbox, radio and disclosure-triangle crops with the private reference at 4×. Independent samples matched the documented desktop color (#63639C) and menu-bar column. Parsed 11 SVGs, three Plasma metadata files and the color scheme. A path and binary-diff scan of 42 reachable commits found no reference assets or font binaries; the text-table provenance question remains deferred under #25.

Physical screens, a real login or systemd session, library upgrades and a screen reader session remain unverified. Deferred login behavior was exercised by running the actual generated hook in throwaway homes. This review changed only the two logs.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #49–#53

Verified each by reading the code (and Codex's reproductions), then fixed
them with a test for each. Uncommitted at the time of writing.

| Finding | Verified | Fix |
|---|---|---|
| #49 | yes (read: the session's processes keep `QT_QUICK_CONTROLS_STYLE=Platinum` from the login script; uninstall removed the module; a running environment can't be changed from outside) | uninstall.sh leaves a pass-through: the module only forwarding to KDE's style (`import org.kde.desktop 1.0`) and Kirigami's link, so apps started from the old environment still start, with KDE's look. A one-shot login script (`macos9-theme-cleanup.sh`) removes what it recognizes, the folders it made, and itself at the next login. A reinstall before that runs it first. Tests: an app started from the session's environment after uninstall starts (offline), a launcher held across the uninstall starts one (live test, real Plasma), a reinstall takes the pass-through's place, nothing is left after the next login. |
| #50 | yes (read: `sha256sum -c` exits 1 on an empty list) | The copy's files are compared with the checksum list: each file must be listed, each listed file there and unchanged. An empty list with no files passes; a list cut short is now caught (it wasn't before). Tests for both. |
| #51 | yes (read: the row item had no icon) | The row item takes the action's icon (theme name, file or qrc URL) and the style lays it out as in QMenu (18 px row, label at 41 px). The checked menu now has an icon row on both sides: still pixel exact. |
| #52 | yes; also true for widget sliders (the style drew no focus) | While the keyboard moves the focus, two 1 px #6666CC lines either side of the focused thumb (a ring would be cut off: the thumb fills the slider's height). Drawn by the style, so QSlider, Qt Quick's Slider (through KDE's bridge) and each RangeSlider handle show it. Checked with real Tab focus in `dev/quickkeys.cpp`. |
| #53 | yes (the fixture's combo box was only as wide as its rows, so another font made the list 1 px wider; read: a Binding's value runs even while off) | The fixture's combo box is 140 px on both sides. The combo's width binding reads rows only while Platinum, and only rows still in Platinum's look while the style changes. KDE's Menu still logs one binding loop of its own during a live switch (FINDINGS.md). |

### Checks

- `dev/test-install.sh`: 249 of 249. `dev/test-install-live.sh`: 19 of 19.
- `dev/check-quick.sh`: 19 of 19 (menus with an icon row; focus on
  three kinds of slider). `dev/check-style.sh`: 135 of 135.
  `dev/check-plasma.sh`: 7 of 7.

### Limits

- The pass-through covers apps started before the next login; the
  session's environment itself only changes with that login.
- Icons from image providers (`image://`) aren't drawn in menu rows.
- No screen reader session; not on the user's desktop.

## 2026-11-21, Codex (GPT-6) — full audit after the Qt Quick implementation

Reviewed main at `88a3732`. All installer and desktop runs used a fresh archive, throwaway homes and private runtime directories. The checks in the audit request passed 407/408. Additional cases uncovered two ways the normal rollback tests can give a user false confidence.

| Finding | File and line | Impact and verification |
|---|---|---|
| #49 · P1 · fixed (next section up) | `install.sh:142`, `uninstall.sh:272`, `dev/test-install-live.sh:163` and `:190` | New Qt Quick apps can fail to start after a successful uninstall until the login environment is refreshed. In a seeded home, applied Platinum, sourced the generated login script, and successfully opened the gallery. Ran uninstall in that same shell (exit 0), then launched the same gallery again. It exited 2 with “module Platinum is not installed”. Clearing the two Qt Quick exports let it start with KDE's style (exit 0). Uninstall deletes the selected QML module while existing launchers retain its name. The live test sources the hook in a child for its first probe and runs its final probe from a parent that never inherited those exports. Verify the fix with one long-lived launcher across uninstall. |
| #50 · P2 · fixed (next section up) | `scripts/common.sh:703`, `uninstall.sh:138`, `uninstall.sh:148` | Normal uninstall refuses a valid backup if no original settings files existed. Applied in a disposable fresh profile. The generated SUMS file was present and zero bytes because there were zero regular files to hash. Uninstall exited 1 and reported damage before restoring the original absence of the files. A separate profile seeded with a single kwinrc passed the same restore. Handle a verified empty inventory while continuing to reject a truncated checksum list for a nonempty backup. |
| #51 · P2 · fixed (next section up) | `style/quick/Platinum/MenuItem.qml:34`, `style/quick/platinumitem.cpp:60` | Qt Quick menu items lose their action icons. Rendered an open menu twice, changing only the row's icon from empty to `document-open`. Platinum's two images were identical. KDE's control under the same widget style changed 348 pixels. The override hides the content containing KDE's icon and its replacement never sets the icon in the menu style option. The measured menu layout includes a 16 px icon row (`docs/REFERENCE.md`, “Menu items”). |
| #52 · P2 · fixed (next section up) | `style/quick/Platinum/RangeSlider.qml:48`, `style/quick/platinumitem.cpp:297` | Keyboard focus is invisible on a range slider. Compared the slider crop before and after giving its first handle focus with Qt.TabFocusReason. The control and handle reported active focus. Platinum changed zero pixels; KDE's control visibly changed. Both original handles are hidden and the new painted thumb receives pressed and enabled state only. Include focus on each handle in the accessibility checks. |
| #53 · P3 · fixed (next section up) | `style/quick/Platinum/ComboBox.qml:40`, `dev/quick-regions.qml:92`, `dev/quickref.cpp:78` | The 19/19 Qt Quick result did not reproduce with a clean home. The suite reported “FAIL combo 145 of 5202 px differ (bbox (99, 0, 102, 50))”. In a second run instrumented only to read geometry, the 102 px button opened a 103×51 Quick popup; the widget reference was 102×51. The right bevel falls outside the expected column. The fallback log also reports a width binding loop during the switch to Fusion, although its final image matched. The one-pixel difference was measured against the widget fixture; its width is not a fixed OS 9 reference measurement. |

### Checks and limits

1. **Installation and undo.** The stock installer suite passed 230/230, including the changed Kirigami link ownership checks and earlier rollback regressions. The nested two-output live suite passed 17/17 and restored both panels, their widgets, the clock setting and the seeded config files. The extra rollback cases above used the actual generated login hook, a private runtime and a stand-in systemctl. A real systemd session, upgrade in place and physical login were outside this test.
2. **Application style and Qt Quick.** All 135 widget comparisons passed. Qt Quick passed 18/19, including menu-edge, dialog, drawer, range-slider geometry, switch keyboard/accessibility and Fusion fallback fixtures. Visually inspected gallery output and a nested System Settings Application Style page. Rendered widget galleries at 1, 1.25, 1.5 and 2. Built the widget, Quick and decoration plugins with ASan/UBSan; the Quick control scenes and decoration preview completed without sanitizer diagnostics (leak detection disabled). The System Settings window rendered, although portal and KDE helper services logged startup failures in its private bus. Physical mixed-DPI transitions, a screen reader session, exhaustive interactive control states and performance under load remain unverified.
3. **Decoration.** Inspected the maximized window in nested KWin and the instrumented preview, including inactive and long-title windows. The decoration implementation itself has no change since the prior audit. Interactive tiling and library upgrades were not retested.
4. **Plasma.** All seven menu-bar/dock crops matched. Inspected the menu and desktop image. Parsed 11 SVGs (also checked for duplicate IDs within each), three Plasma metadata JSON files and the color scheme. The installed layout and source match apart from the generated-file comment. This pass did not repeat edit-mode, auto-hide, crowded-dock or vertical-panel interaction checks.
5. **Fidelity.** Compared checkbox, radio and disclosure-triangle reference/render pairs at 4×. Re-sampled the private desktop image: (5,500) was #63639C, and the column at x=700 was white at row 0, #DDDDDD at 17, #999999 at 18 and black at 19. The popup-window placement issue already recorded under #3 remains unverified against a KDE control on real hardware.
6. **Documentation.** The audit request lists the correct five suites. Its 19/19 Quick expectation differs from the clean-home result. The live test's “after uninstall” result covers a fresh process environment; #49 describes the missing inherited-environment case.
7. **Publication.** Scanned all 41 locally reachable commits for binary diff entries and reference, image, font and ROM filenames. No matching entries surfaced. Text-encoded pixel tables and naming remain subject to the existing publication decision under #25. The private checkout was used read-only.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick dialogs, drawers and range sliders (finding 3, step 6)

Working tree after `6e3d450`; uncommitted at the time of writing.

### What was done

- **Measured** the plain modal dialog frame (`dialog-modal-plain.png`) and
  the movable alert frame (`dialog-save-changes.png`) into REFERENCE.md
  "Dialog frames".
- **Style**: `PE_PlatinumModalFrame` (a custom primitive) draws the plain
  modal frame; the slider draws its groove and thumb only when
  `subControls` asks (QSlider always asks for both).
- **Qt Quick**: `Dialog` in the modal frame on its white (View) body,
  without KDE's dimmed backdrop; `Drawer` framed like a menu on its open
  side (derived: Mac OS 9 had none); `RangeSlider` from the QSlider's groove
  and two thumbs, KDE's hidden handles kept on the thumbs.

### Checks

- `dev/check-style.sh`: 135 of 135 (new: the frame's four edge bands
  against the capture, 0 differing pixels; the 131 others unchanged).
- `dev/check-quick.sh`: 19 of 19 (new: the dialog's frame bands, the range
  slider against a QSlider with a second thumb, KDE's handles within 1 px
  of the thumbs, the drawer's edge against a menu's; each also after a
  switch to Fusion against KDE's style).
- `dev/test-install.sh`: 230 of 230.

### Limits

- KDE's dialog header keeps its close button (Mac OS 9 modal dialogs had
  none); the dialog's title stays KDE's heading.
- Vertical range sliders and the other drawer edges (right, top, bottom)
  are drawn but not checked.
- Not seen on the user's screens.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick style installed (finding 3, step 8), switch and real-session checks

Working tree after `f00439e`; uncommitted at the time of writing.

### What was done

- **Packaging.** install.sh builds `style/quick` and installs it in
  `~/.local/lib/macos9-theme/qml/Platinum` (a folder target with checksums)
  and links `kf6/kirigami/platform/Platinum.so` to KDE's plugin in the
  style's plugin folder. Links are a new target kind: recorded with where
  they point, put in place under a recorded temporary name, removed only
  while they still point there (a re-pointed link is left alone), and a
  link already in the way is moved aside and put back. The login script
  sets `QT_QUICK_CONTROLS_STYLE=Platinum` and `QML_IMPORT_PATH` only when
  `widgetStyle` is Platinum (`kdeglobals`, else `kdedefaults/kdeglobals`),
  the user hasn't set the variable, and KDE's `org.kde.desktop`
  (`kde-qmlmodule.version`) is the version install.sh saw (finding 44's
  login part). If KDE's Qt Quick style or Kirigami's plugin is missing,
  the Qt Quick style is left out.
- **Switches** (plan step 5): `dev/quickkeys.cpp` presses Space on a
  `Switch` and a `SwitchDelegate` and reads their accessible role and
  state: the same as with KDE's style. Part of `dev/check-quick.sh` now.
- **Real session**: `dev/quick-live.qml` in the nested KWin with the
  Platinum decoration: the menu, the combo box's list over its button and
  the help balloon render right as in-window pop-ups (Qt Quick's default).
  A menu as its own window, opened by a real click, draws its frame and
  shadow with see-through corners.

### Checks

- `dev/test-install.sh`: 230 of 230 (new: the Qt Quick folder and link
  installed and removed, a user's link moved aside and back, a re-pointed
  link left alone, the login script on with Platinum, off with Breeze, not
  over the user's own choice, not after a KDE Frameworks upgrade, no
  duplicate path).
- `dev/test-install-live.sh`: 17 of 17 (new: a Qt Quick app started with
  the login script's environment after `--apply` gets the Platinum Qt
  Quick style; after uninstall KDE's).
- `dev/check-quick.sh`: 13 of 13.

### Limits

- A menu opened as its own window lands at the window's corner, not where
  asked; KDE's style wasn't compared (its menu didn't open in that test).
- Not on the user's desktop; no real login.
- Dialogs, drawers and the range slider are still KDE's.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick style built (finding 3, steps 2-5 and 7)

Built `style/quick` from the spike (menus, menu bar, combo box list,
tooltips, switches) and a pixel check for it, `dev/check-quick.sh`.
Working tree after `3fd0e68`; uncommitted at the time of writing.

### Checks

- `dev/check-quick.sh`: 12 of 12. Each Qt Quick piece equals its widget
  counterpart pixel for pixel (menu with the first and with the last row
  selected, the combo box's open list, the menu bar, a switch's indicator,
  a tooltip); after switching the app to Fusion while running, each equals
  KDE's own style under Fusion. The fallback half found two bugs first
  (rows kept a bound width; KDE's list stayed over the button), both fixed.
- System Settings (`kcm_mouse`) in the nested KWin with the style: runs, no
  QML errors, the sidebar's switch is a Platinum check box.
- `dev/check-style.sh` and `dev/check-plasma.sh` not rerun: the widget
  style is unchanged since 131/131 and 7/7.

### Limits

- Software renderer and offscreen windows; real pop-up windows (menus as
  their own Wayland surfaces) not checked; no menu opened in a real app.
- Switches: Space toggling and the accessible checked state not checked.
- Not installed: install.sh and the login script don't know the Qt Quick
  style yet (step 8).
- Dialog, drawer and range slider still KDE's (step 6).

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick spike (finding 3, step 1)

Built the spike in `spikes/qtquick/` (sandbox only) and ran the checks the
plan lists; full results in docs/FINDINGS.md "Qt Quick style spike". Also
changed `style/platinum/platinumstyle.cpp`: with no widget, a menu row's
place and the shortcut gap come from properties on `styleObject`.

| Finding | What the spike showed |
|---|---|
| #43 | `import org.kde.desktop 1.0` loads; fallback controls are KDE's (`KQuickStyleItem` button background), ours are used. |
| #44 | The run-time part works: switching the app's QStyle to Fusion brings KDE's look back and back again (after two fixes: a hidden `QWidget` for `StyleChange`, and hiding KDE's parts by opacity instead of replacing them). The login-script part is for step 8. |
| #45 | Rows drawn through our item with the row's place on `styleObject` match the widget `QMenu` pixel for pixel, selected first and last rows included. |
| #46 | Not exercised (lists are step 6). |
| #47 | Same pattern found in `Menu` itself: KDE's `Menu.delegate` makes KDE's `MenuItem` for actions and submenus, so ours overrides it; the combo box is step 3. |
| #48 | Menus ignored the asked position; comparisons find the pop-up by its pixels and fail if it's missing. |

### Checks

- Menu vs widget `QMenu`: 16,376 of 16,380 pixels equal (the other 4 are
  see-through in both), first and last row selected.
- Kirigami's seven color sets and units: identical to KDE's style with the
  link, different without it.
- `QGuiApplication` with and without KDE's platform theme: opens, KDE's
  look.
- System Settings (`kcm_mouse`) in the nested KWin: runs, our module and
  KDE's Kirigami plugin loaded, no QML errors.
- `dev/check-style.sh` 131/131 and `dev/check-plasma.sh` 7/7 after the
  style change; no build warnings.

### Limits

- Software Qt Quick renderer and the nested KWin only; no keyboard or
  screen reader checks yet; real pop-up windows not checked.
- The spike's code isn't installed by install.sh.

## 2026-11-21, Claude Code (Claude Opus 5.5) — the Qt Quick plan revised for findings #43–#48

All six are about the plan for #3 (PLAN.md), not shipped code; nothing was
built. Checked each claim against the installed files, the style source
and the captures, then rewrote the plan.

| Finding | Verified | Change to the plan |
|---|---|---|
| #43 | yes (read): KDE's `qmldir` exports all 52 controls at 1.0 only | The fallback is pinned, `import org.kde.desktop 1.0`; the spike checks where each control actually comes from. |
| #44 | yes (read: the planned conditions didn't include the selected style) | Two layers: the login script sets the variable only when `widgetStyle=Platinum` at login (plus the user-override and version checks), and every override applies only while the app's QStyle is Platinum (`Binding { when }` restores KDE's look), so switching away takes effect at once, in running apps and in apps started later in the same session. Activation cases added to the checks. |
| #45 | yes (read): `platinumstyle.cpp` takes the first/last-row and combo branches from `QMenu`/`QComboBox` pointers; KDE's bridge passes no widget | Draw through our own small C++ Qt Quick item instead of KDE's bridge; it passes row context through `QStyleOption::styleObject` properties. Spike compares selected first/last rows, a separator and a combo row with the widget renders. |
| #46 | yes: sampled `dialog-file-open.png` (780,341) = #CCCCFF and `popup-open.png` (700,306) = #333399; REFERENCE.md lines 95, 123, 158 agree | Menus and combo rows #333399 with white text; list rows #CCCCFF with black text; Finder's label inversion not used; selection, keyboard focus (the #16 ring) and hover kept apart; separate fixtures for views and menus. |
| #47 | yes (read): `ComboBox.qml` declares its own `popup: Menu` and `delegate: MenuItem` | Our `ComboBox` keeps KDE's closed control and replaces only `popup` and `delegate`; its real pop-up is tested. |
| #48 | yes (read): `dev/quickshot.cpp` grabs only the main window | Region tests set `popupType: Popup.Item` and assert the pop-up's pixels are present; real pop-up windows are checked in the nested KWin. |

Also from Codex's notes: the Kirigami platform plugin link is now a spike
question (needed or not); if it ships, install.sh gets a link target kind
with its own tests. Using KDE's private `StyleItem` bridge is put to the
user as a decision (the project rule allows only officially supported
hooks); the plan recommends our own item, which needs no private module.
Switches keep their role, checked state and Space toggling.

### Checks

- Plan text only. The claims above were checked by reading the installed
  qqc2-desktop-style 6.32 files, `style/platinum/platinumstyle.cpp`,
  `dev/quickshot.cpp`, and by sampling two private captures.

### Limits

- Nothing was built or run; Codex's probes (#43, #44, #47, #48) weren't
  repeated here. The spike is where the plan gets proven.

## 2026-11-21, Codex (GPT-6) — Qt Widgets and Qt Quick plan review

Reviewed the proposal for #3 at `7b20bd8`. Keep the existing Platinum QStyle. A one-control Qt Quick style successfully reused KDE's widget-backed button after correcting the fallback import. All findings below concern the proposed work or its acceptance tests.

| Finding | Location | Evidence and change needed in the plan |
|---|---|---|
| #43 · P2 · addressed in the plan (next section up) | `PLAN.md:184` | The proposed fallback can prevent a Qt Quick app from opening. Tested a minimal custom module exporting ToolTip 2.0. With `import org.kde.desktop auto`, the loader requested KDE's nonexistent module version 2.0 and quickshot exited 2, with and without the KDE platform theme. Using `import org.kde.desktop 1.0` loaded our marked tooltip and a fallback button whose background was a KDE KQuickStyleItem. The installed KDE qmldir exports its controls at 1.0. Pin the tested import and check actual control origins in the spike. |
| #44 · P2 · addressed in the plan (next section up) | `PLAN.md:194`, `PLAN.md:234`, `README.md:24` | The login script as proposed selects custom controls even after a plain install or after switching back to Breeze. Its conditions check an existing environment override and a package version, but omit the selected application style. The custom tooltip loaded in a fresh home with no Platinum widget style configured. Define how activation follows the selected style and verify install-only, apply, switching away, and launching another app in the same session. A check performed only at login cannot update the environment of an already-running app launcher. |
| #45 · P2 · addressed in the plan (next section up) | `PLAN.md:188`, `style/platinum/platinumstyle.cpp:1333` | Reusing the menu renderer loses edge information. KDE 6.32 calls CE_MenuItem without a QWidget; Platinum takes its first/last-row and combo-popup bevel branches from a QMenu or QComboBox pointer. A selected first row therefore cannot get the first-row treatment through that call alone. Include a selected first and last row, separator, and combo row in the spike. Pass row context explicitly to shared painting code if those comparisons fail. Verified by tracing both implementations and the measured top-edge rule in `docs/REFERENCE.md:129`. [KDE bridge source](https://github.com/KDE/qqc2-desktop-style/blob/v6.32.0/plugin/kquickstyleitem.cpp#L1699) |
| #46 · P2 · addressed in the plan (next section up) | `PLAN.md:228`, `docs/REFERENCE.md:95`, `docs/REFERENCE.md:123` | Applying dark lavender and white to every selected delegate conflicts with the reference and the existing widget palette. Re-read the private captures: the file-dialog list at (780,341) was #CCCCFF; the popup menu at (700,306) was #333399. Finder label inversion is another distinct case documented at reference line 158. Give ordinary views and menus separate reference fixtures and distinguish keyboard focus, hover and selection. |
| #47 · P2 · addressed in the plan (next section up) | `PLAN.md:228`, installed `org/kde/desktop/ComboBox.qml:37` and `:141` | A top-level menu override does not restyle the fallback combo's popup. Exported marked Menu and MenuItem overrides and instantiated both a standalone Menu and a fallback ComboBox. The standalone menu had our marker; the combo's popup retained KDE's Menu with no marker. KDE's ComboBox constructs its menu and delegate locally. Include an explicit combo override or adaptation and test its actual popup while preserving the existing widget-backed closed control. |
| #48 · P3 · addressed in the plan (next section up) | `PLAN.md:231`, `dev/quickshot.cpp:45` | A valid screenshot can omit the popup being tested. Rendered the same 80×50 solid-color popup inside a 200×120 root. With Popup.Item the PNG contained all 4,000 popup pixels. With Popup.Window it contained zero. Both captures exited 0. Set Popup.Item for deterministic region tests, assert popup pixels, and use the nested compositor to verify separate popup windows. |

**Kirigami and packaging.** With the custom import fixed, the sampled grid unit and text color were identical with and without a per-style plugin link (18 and #232629). Qt's loader trace showed the actual KDE platform plugin loading through the alias; those two values alone cannot verify plugin selection. If the link ships, give it an ownership and uninstall test: the present installer recognizes file and directory targets and explicitly excludes links in `scripts/common.sh:458`. The installed private bridge is also a dependency under the project's supported-hooks rule; decide whether using it is acceptable before building the overrides around it.

**Scope.** Used Qt 6.12.0, qqc2-desktop-style/Kirigami 6.32.0 and the existing QApplication-based quickshot with temporary homes, private runtime paths and offscreen rendering. These probes establish module selection and capture behavior. They did not exercise System Settings, a QGuiApplication-only client, keyboard or assistive technology interaction, or a login/upgrade cycle. For switches, retain switch semantics and verify keyboard toggling and accessible checked state when changing their appearance. No shipping implementation, plan text or private assets were changed.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #39–#42

Wrote a test for each first and ran it against `cdbde37`: #39, #40 and #42
failed as described; the run stopped before #41's case (read instead).
Then fixed all four. Uncommitted at the time of writing.

### Verification and what was done

| Finding | Verified | Fix |
|---|---|---|
| #39 | yes, reproduced (`first` lost, `second` in place) | When more than one thing was moved aside from the same place, uninstall first moves every later one into the dated folder (`later-versions/`, with a warning naming it), then puts back the one from before the first install. Later ones go first, so a second run after an interruption can't put a later one over the original. Tested: `first` back in place, `second` kept and named. |
| #40 | yes, reproduced (a missing `kdedefaults/custom-settings` passed) | The `SUMS` check no longer drops "open or read" failures (only duplicates of a top-level entry already reported) and no longer ignores the check's exit status: a missing or changed file anywhere in the copy, or an unreadable `SUMS`, stops uninstall before any change. Tested, including the way out the message gives (move the copy away, run again). |
| #41 | yes (read; tested after the fix) | `installed_tree` also counts folders: a folder that holds no installed file is the user's, so the installed folder counts as changed and a reinstall moves it aside (put back by uninstall). Uninstall already kept such folders (#35); tested both. The theme's own sources have no empty folders. |
| #42 | yes, reproduced (three "No such file" lines) | `record_sums` does nothing in a dry run (no build to read, no record written). The main scenario checks a fresh-home dry run prints no errors. |

### Checks

- `dev/test-install.sh`: 214 of 214 (21 new).
- `dev/test-install-live.sh`: 15 of 15.
- Style and Plasma checks not rerun: no style or Plasma file changed.

### Limits

- Still no real desktop, real login or real systemd failure.
- Which version goes back in place for #39 is a choice: the one from
  before the first install (README says so); later ones are kept, not put
  back.

## 2026-11-21, Codex (GPT-6) — fourth pre-install audit

Reviewed main at `cdbde37`, including the fixes for #34–38. Used a fresh archive, disposable homes and private runtime directories. The regression tests for all five fixes passed. The first two cases below exercise variants the regression tests miss.

| Finding | Location | Verification and consequence |
|---|---|---|
| #39 · P1 · fixed (next section up) | `uninstall.sh:223`, `uninstall.sh:270`, `uninstall.sh:278`, `uninstall.sh:282` | Two displacements of the same regular file lose the oldest original. Seeded a custom `Platinum.colors`, installed, replaced the installed file with different custom contents, installed again, then uninstalled. All three commands returned 0. Only the second custom version remained anywhere in the test home. Uninstall marks the destination as gone when it removes the installed file, restores the first saved file, then uses the same stale marker to move the second saved file over it. This can happen with plain installs, before applying the theme. |
| #40 · P2 · fixed (next section up) | `uninstall.sh:124`, `uninstall.sh:133`, `uninstall.sh:163` | A missing file inside a backed-up directory passes validation. Seeded `kdedefaults/custom-settings`, applied the theme, and removed only that file from the backup. Uninstall reported a successful restore and exited 0. The file disappeared from the active config. The top-level directory still passes the existence check, and the checksum pipeline filters out the missing-file diagnostic and ignores the exit status. The dated copy of the pre-uninstall state can aid manual recovery if it still contains the wanted version. |
| #41 · P3 · fixed (next section up) | `scripts/common.sh:395`, `scripts/common.sh:399`, `scripts/common.sh:530` | Reinstall drops user-added empty folders. Created an empty `user-templates/` under the installed desktop theme and ran plain install again. The folder disappeared. The ownership check skips directories, so an empty addition does not trigger preservation before the tree is replaced. |
| #42 · P3 · fixed (next section up) | `install.sh:69`, `scripts/common.sh:349`, `scripts/common.sh:495` | In a fresh disposable home, `install.sh --dry-run` returned 0 but emitted three “No such file or directory” diagnostics for the two plugins and the login script. The checksum step tries to inspect build outputs under `/nonexistent` before the dry-run return. This makes an otherwise successful preview look broken. |

### Checks, in audit-request order

1. **Packaging.** `dev/test-install.sh` passed 193/193, including repeat installs, interruption/retry fixtures, symlink checks and the new checksum cases. `dev/test-install-live.sh` passed 15/15 in nested Plasma, including shell replacement and restoration of both panels, their widgets, a clock setting and the fixture's config and GTK files. The four findings above came from additional runs independent of the stock assertions. No login on a physical desktop, real systemd service failure, or upgrade of the installed Qt/KWin libraries was exercised.
2. **Application style.** All 131 native-scale region comparisons passed. Rendered the widget gallery, dialog, menu and focus sheets at 1, 1.25, 1.5 and 2. Inspected the fractional-scale renders and ran the instrumented style renderer with ASan/UBSan and leak checking disabled. No sanitizer diagnostic. The style source is unchanged since the prior audit. Runtime style changes, all keyboard paths, physical mixed-DPI transitions and painting performance were not exhaustively exercised. Qt Quick controls outside the QStyle remain tracked in #3.
3. **Decoration.** Built both plugins and inspected the maximized nested KWin screenshot and the ASan/UBSan decoration preview, including the long title. No sanitizer diagnostic. Interactive tiling, physical scaling and behavior across a KWin upgrade remain unverified.
4. **Plasma.** All seven menu-bar and dock comparisons passed. Parsed 11 theme SVGs, three package metadata JSON files and the color scheme. The generated layout matches the source apart from its generated-file comment. Inspected the nested menu and desktop render. The two-output fixture covers the chosen main-screen layout. This pass did not repeat edit-mode, vertical/auto-hide or crowded-dock interaction tests.
5. **Fidelity.** Compared fresh check-box, radio and disclosure-triangle renders to the corresponding private captures side by side at 4×. Independently sampled the desktop base at (5,500), RGB (99,99,156), and the menu bar at x=700, rows 0, 17, 18 and 19 (white, #DDDDDD, #999999 and black). Those values match the reference notes.
6. **Documentation.** All four expected suite counts in the request match the observed results. The README's put-back guarantee at line 62 does not cover the observed outcome in #39. The changelog accurately describes the single-displacement and top-level backup fixtures that passed.
7. **Publication.** Scanned names and binary diff entries across all 35 locally reachable commits. No tracked reference paths or binary entries surfaced. This does not establish provenance of pixel values encoded as text. The existing measured-glyph and naming decisions remain for public release. No reference assets were added to the project.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #34–#38

Wrote a test scenario for each first and ran it against `1c47e23`: #34 and
#35 failed as described (the run stopped in #35's second case). Then fixed
all five. Uncommitted at the time of writing.

### Verification and what was done

| Finding | Verified | Fix |
|---|---|---|
| #34 | yes, reproduced (a link `kdedefaults/kdeglobals` → a dotfile: the switch rewrote the dotfile, uninstall put back only the link) | `check_backup_links` also looks inside every copied folder (`kdedefaults`, GTK `assets`) and stops before any change, naming the link. Tested: install `--apply` refuses, nothing changes, the dotfile keeps `ColorScheme=Custom`. The live test now runs `install.sh` again after the switch, which passes, so Plasma itself puts no links there. The user's real config has none either (checked read-only). |
| #35 | yes, reproduced (an added `my-variant.svg`, a changed `metadata.json` and a replaced color scheme were all deleted) | The record keeps a checksum of every file installed, inside folders too (record format 4; written before each copy, old ones dropped after it). Uninstall removes only files that still match, then the folders that held them if empty; anything else stays and is listed in a warning. A changed installed file is left as the user's. A reinstall moves a changed installed file or folder aside like anything else in its way, and uninstall puts it back. Tested both. |
| #36 | yes (read; reproduced in the new test) | The config copy has a `SUMS` file. Before stopping the shell, uninstall checks every listed entry is in the copy (or was absent) and every checksum matches; if not, it stops with nothing changed, names what's wrong, and says how to remove the theme without restoring (move the copy away). Tested with a missing and with a changed `kwinrc`. |
| #37 | yes, reproduced (the dry run warned the earlier color scheme would stay aside) | The dry run remembers what the real run would have removed, so it reports the same put-backs. |
| #38 | yes (read; reproduced with a stand-in systemd whose starts fail) | Uninstall writes `shell-stopped` in its state folder before stopping the shell and removes it once the shell is up (the direct route now waits for the shell on the session bus). If the start fails, it finishes the rest, exits 1 and says how to start the shell; the next run starts it first, even when nothing else is left. Tested: first run exits 1 with the config restored, second run starts the service and exits 0. |

### Checks

- `dev/test-install.sh`: 193 of 193 (38 new).
- `dev/test-install-live.sh`: 15 of 15 (new: `install.sh` again after the
  switch).
- Style and Plasma checks not rerun: no style or Plasma file changed since
  131/131 and 7/7.

### Limits

- Still no real desktop, real login or real systemd failure.
- The checksum check costs one `sha256sum` per installed file (about 50)
  on install and uninstall.
- A record or config copy from an earlier version (format 3, no `SUMS`) is
  refused; only test homes had them.

## 2026-11-21, Codex (GPT-6) — third pre-install audit

Reviewed main at `05cd9bd`. All desktop operations used throwaway homes. The following cases are additional to the project's passing tests.

| Finding | Location | Impact and verification |
|---|---|---|
| #34 · P1 · fixed (next section up) | `scripts/common.sh:496`, `scripts/common.sh:525` | A link inside a backed-up directory can lose its target's original contents. Linked `kdedefaults/kdeglobals` to a custom dotfile in the test home, then ran apply and uninstall. Both exited 0. The dotfile's original `ColorScheme=Custom` became `Platinum` and stayed that way. The link check visits the listed entries only, and the recursive backup preserves the child link itself. |
| #35 · P1 · fixed (next section up) | `uninstall.sh:181`, `uninstall.sh:184`, `README.md:62` | Uninstall deletes user additions inside an installed package. Added `my-variant.svg` to the installed Platinum desktop theme after an ordinary install. Uninstall succeeded and no copy of that file remained in the throwaway home. The removal checks only the recorded path's type before recursively deleting it. The same type check also treats a replacement regular file as installed, despite the README's promise to preserve a user's replacement. |
| #36 · P2 · fixed (next section up) | `uninstall.sh:96`, `uninstall.sh:136`, `uninstall.sh:146` | An incomplete backup can produce a successful partial restore. After apply, moved the saved original `kwinrc` out of the backup while retaining its entry and the absence list. Uninstall reported success and archived the backup. The left button setting stayed at Platinum's `X` instead of the original `M`. |
| #37 · P3 · fixed (next section up) | `uninstall.sh:184`, `uninstall.sh:203` | Dry-run reports a collision that the real uninstall resolves. Installed over an existing Platinum color scheme, then ran preview and actual uninstall consecutively. Preview warned that the earlier file would stay displaced. Actual uninstall returned 0 and put it back. Preview checks the path while the installed file is still there. |
| #38 · P2 · fixed (next section up) | `uninstall.sh:144`, `uninstall.sh:148`, `scripts/common.sh:597` | If both shell start attempts fail, retrying uninstall can succeed while Plasma remains stopped. A private systemctl stub recorded a successful stop and two failed starts. Uninstall exited 1. Enabled starts and retried. Uninstall exited 0 without calling systemctl, and the simulated service remained inactive. The script had already archived the backup and only starts the shell inside the restore branch. |

### Coverage and limits

1. **Install and restore.** The installer suite passed 155/155. The nested live suite passed 14/14, including replacement of the shell process, both original panels with their widgets, the clock's seconds setting, and byte-for-byte restoration of the fixture's config and GTK files. The extra cases above identify configurations outside those tests. Coverage applies to the tested plugin builds, service paths and config files. A real login, a Qt/KWin upgrade, and a real systemd failure were outside this run.
2. **Application style.** The build passed and all 131 reference regions matched. Rendered the gallery at 1, 1.25, 1.5 and 2. The fractional-scale gallery views retained recognizable controls and visible selection. The exact pixel count applies to the native-scale test. ASan/UBSan completed the stock style render with leak detection disabled. These exercises do not cover every style transition, null option, keyboard traversal, or hot path.
3. **Decoration.** The instrumented decoration renderer completed and displayed title bars and controls for the fixture windows. Physical mixed-DPI output, interactive tiling and compositor upgrades remain unverified in this pass.
4. **Plasma.** All seven measured parts matched. All 11 theme SVGs parsed. Inspected the nested desktop with the menu open. The main-screen-only panel layout remains the accepted #21 behavior. Edit mode, vertical/auto-hide docks and two physical 4K screens were outside this run.
5. **Fidelity.** Independently sampled the private desktop capture. Pixel (5,500) was `#63639C`. At x=700 the menu bar was white at y=0, `#DDDDDD` at y=1 and 17, `#999999` at y=18 and black at y=19, matching the reference notes. Visually compared the enlarged check, radio and disclosure triangle crops.
6. **Documentation.** The four requested check counts in the audit request matched this checkout. The README's recovery promises need qualification for #35 and #38.
7. **Publication.** A filename and binary-diff scan of the 33 reachable commits found no reference image paths, font binaries or ROMs. That scan cannot establish provenance of numeric tables. The glyph-derived menu data and naming decision remain release questions under #25 and PLAN.md. The private reference checkout was read only.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #27–#33

Verified all seven by reading the code and reproducing them, then fixed
them. Working tree after `ece4355`; uncommitted at the time of writing.

### Verification and what was done

| Finding | Verified | Fix |
|---|---|---|
| #27 | yes, reproduced (new test: a target replaced by the user's folder made the first uninstall exit 1 with the record intact, so a second run removed the login hook it had just put back) | `uninstall.sh` takes each entry off the record as soon as it's done (`manifest_drop`): removed files, put-back items, emptied folders. A target that isn't the installed kind any more is left alone as the user's and taken off too, so it's never removed later. What can't be done (a moved-aside item whose place is taken) stays on the record; uninstall then exits 1 and says to run it again. The `rmdir` of a non-empty displaced folder no longer stops the run. **New test: an uninstall interrupted after its 1st…119th file operation (16 points of 120), then run again, leaves the home as before the install** (both moved-aside items back, config restored). That test found two more leftovers (an empty state folder with a lock after a second run, or after a stop just before the end), now removed. |
| #28 | yes, reproduced (button order X/AI kept after uninstall) | If Platinum is already the global theme and there's no copy, install now copies the settings as they are (`TAKEN=apply`) before anything changes, with a warning that this state, not the one before Platinum, is what uninstall puts back. Tested: the user's `ButtonsOnRight=HIAX` and every config file come back. |
| #29 | yes, reproduced (with `~/.config` a link to profile A, repointed to a copy B after install: uninstall would have written into B) | The record keeps where every path led when it was recorded (`real_path`: folders above it resolved, the path itself not), and the config copy's `ENTRIES` does the same per entry. Both scripts compare before any change and stop if anything leads elsewhere, listing the paths. Tested for a repointed `~/.config` (install and uninstall refuse, profile B untouched, uninstall works after pointing it back) and a repointed `gtk-4.0` link (uninstall refuses before stopping the shell). |
| #30 | yes (read) | Temporary copies are recorded before they're created (`make_temp`, random name, `mkdir` or `noclobber` so an existing name is never taken over) and taken off the record once renamed or removed. Leftovers are removed only from the record. Uninstall's own temporaries (restoring config files) work the same way. Tested: look-alike files `.macos9-theme.abc123` and a folder `.macos9-theme.XYZ789` survive install and uninstall. `backup.*` folders in the theme's own state folder are still cleaned by name. |
| #31 | yes, reproduced | The record keeps the data and config folders it was made with (record format 3). Install and uninstall stop before any change if `XDG_DATA_HOME` or `XDG_CONFIG_HOME` now differ, and say which value to use. Tested both. |
| #32 | yes, reproduced (real `QTest` clicks: track click left of the thumb on a reversed bar moved it right) | On a reversed bar (`upsideDown`), the page and arrow parts are swapped in `subControlRect` (and the pressed arrow follows), so clicks page and step towards the click. Probe: every track and arrow click on normal and reversed, horizontal and vertical bars now goes the right way. Fusion itself still moves away there (Qt's common style doesn't swap). |
| #33 | yes (read) | The live test now records the shell's pid before uninstall and checks that the process is gone afterwards and a new one runs. The user's second panel gets a clock widget with a setting (seconds shown), and the widgets of every panel, in order, with that setting, must come back. |

Correction to the #19 row below: right-to-left horizontal scroll bars aren't
`upsideDown` (Qt mirrors them with `visualRect` instead), and Platinum
doesn't mirror them. They work consistently (clicks match what's drawn)
but run left to right. Added to #26.

**#26 (P3, closed later by the user) widened:** besides menu items, horizontal scroll bars
don't mirror in right-to-left layouts.

### Checks

- `dev/check-style.sh`: 131 of 131 regions pixel exact.
- `dev/check-plasma.sh`: 7 of 7.
- `dev/test-install.sh`: 155 of 155 (61 new: findings 27–31, the
  interrupted uninstall, and an empty-state check).
- `dev/test-install-live.sh`: 14 of 14 (shell pid replaced, widgets and
  their setting back).
- Scroll bar probe (scratch, `QTest` clicks on Platinum and Fusion): results
  in the #32 row.
- Style builds with no warnings.

### Limits

- Not run on the user's desktop or with a real login.
- The systemd path of uninstall's shell stop and start still isn't
  exercised.
- No sanitizer run for the scroll bar change (it only swaps which
  rectangle answers which part).
- A record from an earlier version (format 2) is refused; only test homes
  ever had one.
- The temporary-name window: between recording a name and creating it, a
  file of that exact random name could appear; it would then be taken for
  a leftover on the next run. Not tested.

## 2026-11-21, Codex (GPT-6) — second independent pre-install audit

Reviewed the uncommitted working tree on main over `ece4355`, including
`dev/test-install-live.sh`. Tests ran from a private temporary copy with its
own HOME, runtime and session bus. **Hold the first install.** The ordinary
two-screen round trip now works, but retrying a failed uninstall can erase a
file that belonged to the user before installation.

### New findings

| Finding | Where | Verification and effect |
|---|---|---|
| **#27 P1, fixed (next section up) — retry deletes an already-restored original** | `uninstall.sh:150`, `uninstall.sh:174`, `uninstall.sh:194` | Seeded an original login hook and color scheme. After plain install, changed the installed color target from a file to a directory. The first uninstall restored the original hook but exited 1 during cleanup of a nonempty displaced folder. The second uninstall processed the same manifest, deleted the restored hook, and warned that its moved-aside copy was gone. Neither the hook nor its original copy remained. A retry needs to distinguish completed restores from installed files. |
| **#28 P1, fixed (next section up) — reset proceeds without any backup when Platinum is already selected** | `install.sh:131`, `install.sh:148`, `uninstall.sh:78` | Seeded kdeglobals with `LookAndFeelPackage=platinum.desktop`, kwinrc with a custom left button and no install record. Apply warned and ran the reset. After uninstall there was no backup and kwinrc still held X/AI instead of the original button order. This also exposes an existing custom panel layout to reset. The lost button order was reproduced offscreen. |
| **#29 P1, fixed (next section up) — a changed parent symlink can send restore to a different directory** | `scripts/common.sh:392`, `scripts/common.sh:409`, `uninstall.sh:94`, `uninstall.sh:106` | Traced backup and restore paths. ROOTS records the spelling of the config path. If a linked .config or GTK parent is repointed between installation and removal, the final-entry link check passes for an ordinary file under the new parent. Restore can overwrite or remove that other profile's files. The manifest target check at `scripts/common.sh:248` also checks only the final component. Static finding. An unchanged parent link is a different case. |
| **#30 P1, fixed (next section up) — staging cleanup deletes unrecorded siblings** | `scripts/common.sh:346`, `install.sh:64` | Reviewed the cleanup before the build. Every non-link sibling matching the six-character staging suffix is recursively removed, including on a first install with no record. Matching names alone cannot establish ownership. No destructive probe was needed. |
| **#31 P2, fixed (next section up) — changing XDG_DATA_HOME strands installed assets** | `scripts/common.sh:103`, `uninstall.sh:148`, `uninstall.sh:197` | Installed normally, then supplied a different absolute data home during uninstall with the same state home. The command exited successfully and discarded the manifest. The color scheme remained at its original path. The warning for skipped targets does not preserve the record for a retry. |
| **#32 P2, fixed (next section up) — reversed scrollbars page away from the click** | `style/platinum/platinumstyle.cpp:183`, `style/platinum/platinumstyle.cpp:194`, `style/platinum/platinumstyle.cpp:900` | Sent a real QtTest left-click at x=10 on a 300 px horizontal QScrollBar with inverted appearance, range 0–100, value 50. Its thumb center moved right from 134 to 158 and its value fell to 40. The position calculation reverses the thumb but leaves the page hit regions in their original order. |
| **#33 P3, fixed (next section up) — the live restart assertion checks an unrelated message** | `dev/test-install-live.sh:142` | Read the assertion against the uninstall output. It passes on the config-restore message without comparing shell process IDs. Subsequent assertions establish service availability and restored panel geometry. They do not independently establish process replacement or preservation of panel widgets and their settings. |

### Retests, scope and limits

- **Install and undo.** The clean-home suite passed **94/94**, including collisions, GTK files, backup refresh, repeat apply, failed apply, quoting, version guard, lock contention and 12 interrupted-install cases. The nested live suite passed **10/10**. Before apply the panels were screen 0 bottom 46 and screen 1 left 48. After apply both were on screen 0 (bottom 52, top 20). After undo the two original geometries and the fixture's config/GTK snapshot returned. These runs support the earlier fixes on their covered paths. They do not cover interrupted uninstall (#27). The real systemd branch, physical login, stale ABI after an actual OS upgrade and loss of power while writing the journal remain unverified. The login guard compares resolved library paths, so a same-path binary replacement is outside its detection. The old record format is explicitly refused at `scripts/common.sh:193`.
- **Style and decoration.** A fresh normal build and ASan+UBSan builds of both plugins rendered the widget state sheet and KWin decoration preview without sanitizer diagnostics (leak detection disabled). The widget gallery rendered at 1, 1.25, 1.5 and 2×. Reviewed 64-bit arithmetic, bounded ticks, keyboard-focus and mixed-state drawing, widget property restoration, RTL fallback and the decoration's button factory. The earlier report covers unchanged minimum-size, narrow-title, tiled-edge, private popup, vertical-control and timer behavior. Reviewed active/inactive, long-title and pressed decoration previews. No new physical mixed-DPI, tiled-window, exhaustive malformed-option, assistive-technology or frame-time test was run.
- **Plasma and fidelity.** Fresh comparisons passed **131/131** widget regions and **7/7** Plasma regions. Inspected the state sheet, menu, dock, 1.5× gallery and a 4× checked-box pair. Independently sampled (5,500) in `reference/desktop-first-check.png` as #63639C and (620,282) in `reference/progress-determinate-55.png` as #EEEEEE, matching REFERENCE.md. All 11 SVGs parsed with unique IDs per file. JSON metadata and the four scheme/config inputs parsed. The current selection palette addresses #22. Layout, resizing, edit-mode and dock geometry code are unchanged from the prior audit. The earlier non-default dock and 32 px results still apply. Monitor placement (#21) remains a user decision.
- **Documentation and provenance.** DEVELOPMENT.md now distinguishes the isolation provided by each runner. The current README and the prior status summary overstate rollback in #27–#31. AUDIT-REQUEST.md still quotes the superseded 31-check install suite. Reviewed local history across all 32 reachable commits: no reference path, PNG or font in the filename scan and no Git binary numstat entries. The only commit since the prior blob review changed the audit and changelog. The working-tree generator omits the old raw pointer tables, but committed history still contains them, and `style/platinum/menu.h:19` still ships the sampled check glyph. #25 and the public-name decision remain outstanding. No publication clearance or remote visibility check was performed.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #4–#25

Verified every finding by reading the code and reproducing the testable
ones, then fixed them. Working tree after `ece4355`; uncommitted at the
time of writing.

### Verification and what was done

| Finding | Verified | Fix |
|---|---|---|
| #4 | yes (read; reproduced in the new test) | Anything in the way of a target that install.sh didn't install is moved to `~/.local/state/macos9-theme/displaced/` and recorded. Uninstall puts it back. Staging names are unique (`mktemp`), never a fixed `.new`. |
| #5 | yes, **reproduced live**: with plasmashell and kded6 running, the switch rewrote `gtk-3.0/{gtk,colors}.css`, `gtk-4.0/colors.css`, `xsettingsd/xsettingsd.conf`, `~/.gtkrc-2.0` | The backup now covers those (plus `gtk-*/settings.ini`, `window_decorations.css`, `assets/`, `kscreenlockerrc`). Note: the user's real `~/.config/gtk-4.0/gtk.css` holds the Vapor libadwaita import, so this would have hit them. dconf is not copied (applying the theme keeps the GTK theme name; a re-login resyncs). |
| #6 | yes (read) | Any linked entry in the backup list (dangling or not) stops install before any change, with a message naming it. |
| #7 | yes, reproduced | Every parent folder is checked before any write. The record is written **before** each change (`madedir`, `displaced`, `file`, `dir` entries). The new test interrupts install after its 1st…40th file operation (12 points) and checks uninstall leaves the home as before. That found one more gap (a half-written staging file uninstall didn't remove), now fixed. |
| #8 | yes (read) | The config copy is taken by a plain install already (`TAKEN=install`), refreshed on every run until the switch, and frozen after it (`TAKEN=apply`). Uninstall restores it after `--apply`, or after a switch in System Settings (Platinum active). If Platinum isn't active it leaves the config alone and keeps the copy as `unused/`. |
| #9 | yes (read) | Uninstall removes only paths that are both recorded and one of the 7 install targets, of the recorded kind, never through a link. It rmdirs only recorded `madedir` folders above a target, and only when empty. The record stores and checks the home it was made for. Relative XDG values are ignored (spec). HOME must be an absolute existing folder; tabs and newlines in paths are refused. |
| #10 | yes (read; reproduced with a seeded leftover) | Fresh `mktemp` staging per backup, leftovers removed. One run at a time (`flock` on `$state/lock`). |
| #11 | yes (read; reproduced with a failing stand-in) | A failing `plasma-apply-lookandfeel` exits 1 before the button order is written. |
| #12 | yes, and worse than reported: plasmashell saves its layout when it quits, so a file restored under a running shell can be overwritten at the next logout | Uninstall stops the shell first (systemd service if active, else `kquitapp6` over the session bus and waits for the pid), restores, then starts it again (also on failure, via a trap). The copy is never deleted: it moves to `~/.local/state/macos9-theme-uninstalled-*/original/`, next to `current/`. **Live test: both panels (one per screen) back after uninstall.** The systemd path is not tested (it would need the real user session). |
| #13 | yes | Every step has a "would …" line in a dry run; no temporary folder or lock in a dry run; cache removal only for the exact names Plasma uses for this style, and only if the record had it. |
| #14 | yes | test-install.sh rewritten: exit statuses checked, the backup is re-read after the second `--apply` and a plain install, 94 checks over 11 scenarios. |
| #15 | yes (expression types) | Scroll bar layout and slider ticks in 64-bit; at most one tick per 3 px. Full `INT_MIN..INT_MAX` ranges place the thumb at 0/90/180 of 270 px; a full-range slider with interval 1 paints instantly. |
| #16 | yes, reproduced (0 px change with real Tab key events on button and tab bar) | Not Mac OS 9: while the keyboard moves the focus, a 1 px #6666CC ring (the text field's focus color) around the focus rect of buttons, check boxes, radio buttons and tabs. Mouse focus shows nothing, as before. Measured with real Tab key events: 366/122/98 px change (button/check box/tab) at 1×, 0 for mouse focus; also at 1.5× and 2×. |
| #17 | yes, reproduced | Partly checked: a 6×2 px bar in the empty box (derived, not captured). Differs from unchecked by 12 px and from checked by 31 px at 1×. |
| #18 | yes, reproduced | polish keeps the widget's earlier translucency, margins, frame and fill in properties; unpolish puts them back. Menu margins (3,4,5,6) are back after switching to Fusion. |
| #19 | yes | Scroll bars honor `upsideDown` (right-to-left horizontal bars; corrected two sections up: Qt doesn't set `upsideDown` for those). Pop-up menus, spin boxes and group boxes in a right-to-left layout use Fusion's mirrored layout and drawing (consistent hit areas). Menu items stay left to right: new finding #26. |
| #20 | yes (read) | Only close, zoom (Maximize) and collapse (Minimize/Shade) boxes are created; other buttons are left out. Rendered in nested KWin with `ButtonsOnLeft=MSX`, `ButtonsOnRight=HFBAIL`: only the three boxes show. |
| #21 | yes, reproduced in the live test (panels on screens 0 and 1 → menu bar and dock both on screen 0) | **Not changed: the user's decision** (decided later the same day: main screen only, PLAN.md decision 10; closed). Mac OS 9 shows the menu bar on the main screen only, which is what this does. The other choice is a menu bar on every screen (like macOS since 10.9). The user's second-screen panel does come back on uninstall. |
| #22 | yes | Plasma's selection text roles are light colors on #333399 (derived; all ≥ 4.5:1, white 10.1:1, inactive and link #CCCCFF 6.6:1). |
| #23 | yes (read) | Not changed: a known limit (docs/FINDINGS.md "20 px panel"). Stays open, P3. |
| #24 | yes | DEVELOPMENT.md says exactly what each tool isolates. AGENTS.md, PLAN.md and README.md stale lines fixed. |
| #25 | yes | The raw crops with mouse-pointer pixels (`TrianglePressedRaw`, `CheckOffPressedRaw`, `RadioOffPressedRaw`, `PopupArrowPressedA/B`) are no longer written to `sprites.h`. The clean sprites are byte-identical. README no longer says "everything is redrawn". Stays open: the measured tables and git history need the user's decision before anything goes public. |

**#26 P3, closed (user: right-to-left isn't supported, PLAN.md decision 11) — menu items don't mirror in right-to-left layouts.**
`style/platinum/platinumstyle.cpp` CE_MenuItem uses fixed left offsets
(check, icon, text) and a right-hand shortcut and submenu arrow. Found while
fixing #19 (read only). Mac OS 9 had no right-to-left menus.

Also found while fixing:
- The decoration only loads if it matches the installed KDecoration, so a
  Plasma upgrade can't crash KWin. The login script compares
  `readlink -f` of `libkdecorations3.so.6` and `libkdecorations3private.so.2`
  with what the plugin was built against. If they differ, it leaves the
  decoration's folder off `QT_PLUGIN_PATH` and KWin falls back to Breeze.
- The plugins now live in their own folder, `~/.local/lib/macos9-theme/`,
  not the shared `~/.local/lib/qt6/plugins`.
- The login script quotes its paths for `sh`. It's tested with a home whose
  path has spaces, quotes and `$`.

### Checks

- `dev/check-style.sh`: 131 of 131 regions pixel exact.
- `dev/check-plasma.sh`: 7 of 7.
- `dev/test-install.sh`: 94 of 94.
- `dev/test-install-live.sh` (new; nested KWin with two virtual screens,
  plasmashell, kded6): 10 of 10.
- Style regression program (scratch, not in the repo), checking #15–#19 at
  1×, 1.5× and 2×: results in the table above.
- ASan+UBSan builds of the style, run with `styleshot` and that program: no
  diagnostics (leak detection off).
- Style and decoration build with no warnings. The decoration render was
  checked with extra buttons configured.

### Limits

- The user hasn't seen any of this on screen.
- The systemd path of uninstall's shell stop and start isn't exercised.
- No real login: the login script was sourced in bash and sh only.
- dconf (GSettings) isn't backed up.
- The focus ring and the mixed check box are derived, not measured.
- #16's ring was checked offscreen only, not on the user's displays.

## 2026-11-21, Codex (GPT-6) — independent review before first install

Reviewed all seven sections of `docs/AUDIT-REQUEST.md` at `591e96d` on
`main`. **Hold both the plain install and `--apply`.** The clean-home tests
pass. An existing color scheme was lost even on a plain install. A running
Plasma session also exposed settings that uninstall leaves behind.

### 1. Install, apply and undo

| Finding | Where | Consequence and verification |
|---|---|---|
| **#4 P1, fixed** — existing install targets are lost | `install.sh:67`, `install.sh:87`, `install.sh:92`, `scripts/common.sh:153`, `uninstall.sh:64` | Seeded a custom `Platinum.colors` and an extra file inside an existing `desktoptheme/platinum`. Plain install replaced both. After uninstall neither original existed. The first install assumes ownership of all seven destinations, including whole directories. It also removes the fixed directory staging name before copying. |
| **#5 P1, fixed** — applying the theme changes GTK settings outside the backup | `scripts/common.sh:32`, `install.sh:132`, `uninstall.sh:47` | Hashed the config and data trees before apply, after apply and after uninstall with real plasmashell and kded6 on a private bus. Existing GTK 3 `colors.css`, `gtk.css`, `settings.ini` and `xsettingsd/xsettingsd.conf` still had different hashes after undo. GTK 3 decoration assets and GTK 4 CSS files were also added. Neither the backup nor the dated archive covers these paths. The seeded Plasma panel file itself was restored byte for byte. |
| **#6 P1, fixed** — a linked config entry can back up its own changes | `install.sh:119`, `uninstall.sh:50` | Tested an absolute `kdedefaults` symlink. `cp -a` preserved the link, so the backup and live path resolved to the same directory. After apply **and** uninstall its original `ColorScheme=MyOriginalScheme` was `Platinum`. Relative links can resolve differently inside the backup, and `-e` classifies dangling links as absent. Separately, linking the entire `.config` parent worked when its entries were regular files/directories. |
| **#7 P1, fixed** — a partial first install has no usable removal record | `install.sh:67`, `install.sh:107`, `scripts/common.sh:155` | Made the color-schemes parent an ordinary file in a throwaway home. Install exited 1 after placing both plugins and the login script. No manifest existed. Uninstall exited 0 and the style plugin remained. A Ctrl+C between those writes and manifest save has the same ordering. Directory replacement also has a gap between removal and rename. Both builds finish in a temporary directory before the first install write, so a build failure alone avoids this window. |
| **#8 P1, fixed** — the suggested System Settings switch bypasses the only snapshot | `install.sh:109`, `install.sh:153`, `uninstall.sh:36` | Plain install followed by plain uninstall produced no config snapshot. Traced the printed instruction to select the global theme manually. That route can replace panels before any snapshot exists. A later first `--apply` would save the already-switched desktop. Uninstall then has no copy of the original layout to restore. |
| **#9 P1, fixed** — recursive removal has no destination or ownership checks | `scripts/common.sh:8`, `scripts/common.sh:121`, `uninstall.sh:47`, `uninstall.sh:64` | Traced the manifest loader to deletion. Both file and directory entries use recursive removal with no check against the seven expected paths, their recorded types, or the home that created the record. A previously installed file replaced by a directory would be deleted with its contents. Config restore also uses today's XDG config root with yesterday's snapshot. Relative XDG roots are accepted. Empty XDG values fall back to HOME, but an empty HOME passes the root-user check for a non-root caller. Reviewed statically. |
| **#10 P1, fixed** — an interrupted backup can contaminate the next snapshot | `install.sh:116`, `install.sh:120`, `install.sh:125` | Traced a retry after a partial copy of an existing `kdedefaults/`. The same `backup.new` is reused. Copying the directory again into that existing destination nests it one level deeper and leaves stale entries in the outer copy. Only the ABSENT list is truncated. Concurrent invocations also share the staging names with no lock. The final rename only protects an uninterrupted, single-writer copy. |
| **#11 P2, fixed** — theme application can fail with a successful exit | `install.sh:132`, `install.sh:139`, `install.sh:155` | A stand-in theme applier returned 1 on a private bus. Install warned, wrote `ButtonsOnRight=AI`, printed “Done” and exited 0. Uninstall recovered the seeded kwinrc in this case. A caller cannot distinguish this partial switch by its exit status. |
| **#12 P2, fixed** — the original snapshot is discarded before panel recovery is confirmed | `uninstall.sh:51`, `uninstall.sh:55`, `uninstall.sh:82` | The two-output sandbox had the original panel file back on disk while the running shell still reported the Platinum panels. The restart happens after both backup and manifest removal. A failed restart leaves no retryable original snapshot, and a dirty shell could write during shutdown. The dated archive contains the outgoing setup. A real user-systemd stop/start and a shutdown overwrite were not demonstrated. |
| **#13 P3, fixed** — the dry run omits backup and cleanup steps | `scripts/common.sh:39`, `install.sh:114`, `uninstall.sh:39`, `uninstall.sh:69` | Read the dry-run logs. They showed the theme reset and restoration commands but suppressed the “would copy/keep” lines via `say`. Manifest writes/removal and empty-parent cleanup were also absent from the preview. Install briefly creates and removes a temporary directory even in dry mode. The stock before/after checks found no persistent file-content changes from dry install. |
| **#14 P2, fixed** — a repeat-apply regression can pass the installer suite | `dev/test-install.sh:95`, `dev/test-install.sh:102` | Both apply exit statuses are discarded. The repeat assertion compares a copy made **before** the second apply with the seed. It never rereads the backup for that assertion. Final uninstall gives some indirect coverage. Independently compared the entire backup after both successful applies in a home with a pre-existing defaults tree. The bytes matched on this revision. |

Other packaging checks and limits

- Plain install twice, uninstall without applying, uninstall again, then reinstall
  and apply twice all ran in a home with spaces. Existing nested defaults and
  markers for `kscreenlockerrc`, `kxkbrc` and `Trolltech.conf` survived the
  offscreen round trip. In the running session the dconf file hash also matched.
  These fixtures do not establish a complete list of writes for other modules.
- Inspected the other cleanup paths. The build trap uses the result of
  `mktemp -d`. Cache globs at `scripts/common.sh:111` match other names starting
  with “platinum” and run on uninstall even without a manifest. The untracked
  parent-folder cleanup at `uninstall.sh:73` can remove pre-existing empty
  folders. Conversely, some empty data directories created by install survive.
- At `install.sh:82` the login hook preserves existing search paths and the
  stock test verified duplicate suppression and a successful style load. It
  prepends a shared per-user Qt plugin directory to inheriting processes.
  An empty directory contributes no plugin. Shell quoting handles ordinary
  spaces, but the installer embeds the literal path as shell source without
  escaping shell metacharacters. Existing processes do not inherit a later
  login hook. No package upgrade or real login was exercised. Both plugins
  are rebuilt by rerunning install. The decoration also depends on the
  installed KDecoration ABI. [Qt plugin search and compatibility rules](https://doc.qt.io/qt-6/deployment-plugins.html)
- No actual Ctrl+C, concurrent install, disk-full restore or real systemd
  restart was performed. All systemctl checks during installer runs used a
  stand-in. The stock fixture has no running shell. Its regular-file hash
  snapshot also omits empty directories, symlinks, permissions and ownership.

### 2. Application style

| Finding | Where | Consequence and verification |
|---|---|---|
| **#15 P2, fixed** — scroll and slider arithmetic exceeds the supported int range | `style/platinum/platinumstyle.cpp:165`, `style/platinum/platinumstyle.cpp:953` | Range, position offset and range plus page step are evaluated as signed int before the 64-bit scrollbar calculation. Valid int endpoints can overflow or yield the wrong thumb geometry. The tick-spacing limits also add/subtract an interval as int, and the paint loop scales with the number of values even when many ticks map to one pixel. Verified by reviewing expression types and loop bounds. The ordinary render sanitizer pass below does not cover these extremes. |
| **#16 P2, fixed** — keyboard focus is invisible on common controls | `style/platinum/platinumstyle.cpp:1443`, `style/platinum/platinumstyle.cpp:1396` | In an active offscreen widget window, moved Tab focus from another field to a normal push button, check box and tab bar, verified `hasFocus()`, then compared each widget grab. Each changed **0 pixels**, at 1, 1.25, 1.5 and 2×. The line edit changed 1,734 pixels at 1×. This prevents a keyboard user from identifying the current target even when the measured decoration is accurate. |
| **#17 P2, fixed** — partially checked looks unchecked | `style/platinum/platinumstyle.cpp:1557` | A real tristate QCheckBox gave identical grabs for Unchecked and PartiallyChecked at all four scales. The painter tests only `State_On`. A settings dialog can therefore misrepresent a mixed selection. |
| **#18 P2, fixed** — switching styles loses widget-owned appearance settings | `style/platinum/platinumstyle.cpp:1648`, `style/platinum/platinumstyle.cpp:1686` | Set QMenu margins to (3,4,5,6), polished with Platinum and switched to Fusion. The resulting margins were (0,0,0,0). The tooltip and combo container also acquire translucent backgrounds, and the popup view loses its frame and autofill without symmetric restoration. Filters are removed and the named progress timer is deleted. |
| **#19 P2, fixed in part (rest is #26)** — control geometry does not mirror in RTL | `style/platinum/platinumstyle.cpp:831`, `style/platinum/platinumstyle.cpp:168` | A 120×20 non-editable combo returned the same right-hand arrow rectangle (98,0,22,20) in both directions. The custom spin, group and menu geometry also uses fixed left/right offsets. The scrollbar calculation ignores `upsideDown`, so its thumb geometry also ignores reversed direction. |

- Normal style build completed without compiler warnings. ASan+UBSan
  `styleshot` selected Platinum and rendered the state sheet without
  diagnostics (leak detection disabled). Reviewed option casts, null widget
  paths, generated table dimensions and nine-slice minimum-size guards.
  Small nine-slices skip drawing and fixed sprites can paint beyond a tiny
  requested rectangle without caller clipping. No exhaustive size or
  unexpected-option test was performed.
- At 1× the button's top and bottom black rules were one device row each.
  They measured 1/2 rows at 1.25×, 2/1 at 1.5× and 2/2 at 2×. The sampled
  column remained filled without gaps. This is offscreen raster behavior.
  North/document-mode panes intercept paint and return true, which can
  suppress a subclass's own painting. Combo popup handling depends on Qt's
  private class name. Neither hook has been tested across Qt versions.
- South/east/west tab shapes and vertical progress fall through to Fusion.
  Vertical sliders transpose the measured horizontal shape. Disabled and
  inactive cases in the fixture passed. A balloon uses a bounded number of
  fills per row. Wider busy bars do 14 pixel writes per interior column and
  every polished progress bar starts a 100 ms timer, including hidden and
  determinate bars. Menu sizing can rescan all actions per item. No frame-time
  profile or assistive-technology session was run.

### 3. Window decoration

**#20 P2, fixed — custom title-bar actions look like Close.**
At `decoration/platinum.cpp:482` the factory accepts Menu, OnAllDesktops,
KeepAbove and other actions. At `decoration/platinum.cpp:496` only zoom and
collapse receive distinct glyphs. All other actions get the plain close-box
drawing. Reviewed the switch and inspected the KWin preview's default layout,
which showed multiple plain boxes. The installer's X/AI arrangement avoids
these extra actions.

The warning-enabled build and the ASan+UBSan KDecoration preview produced
active, inactive, long-title and pressed frames. A maximized window in virtual
KWin had a 22-row title and no side frame. The code sets a fixed 6-pixel
normal frame and checks horizontal/vertical maximization independently. It
does not consult the selected border size or individual tiled edges. Narrow
titles drop the text, then the icon. The 100/92/85/78 font-stretch sequence at
`decoration/platinum.cpp:415` has no measured thresholds in the reference
table. With asymmetrical button groups the room calculation uses the gap
between groups, while the content is centered on the whole window. Extreme
narrow widths, tiling and fractional decoration damage were reviewed only.
The Wayland collapse button is Minimize as documented. X11 shading and a
post-upgrade load were not tested.

### 4. Plasma

| Finding | Where | Consequence and verification |
|---|---|---|
| **#21 P2, closed (user's decision: main screen only, PLAN.md decision 10)** — the second monitor loses its panel | `plasma/layout.js:16`, `plasma/layout.js:53` | Seeded a bottom panel on virtual output 0 and a left panel on output 1. Queried the running shell before and after the actual installer's `--resetLayout`. Both new panels reported screen 0, top and bottom. Output 1 had no panel. The layout also changes wallpaper on every desktop at line 65. This affects the user's two-screen setup. |
| **#22 P2, fixed** — selected secondary text can have zero contrast | `plasma/make-plasma.py:413`, `plasma/platinum/colors:105` | The generated Selection group sets both `ForegroundInactive` and `BackgroundNormal` to RGB (51,51,153), a 1:1 contrast ratio. A consumer using that pair will hide the text. Normal selected text is white and readable in the rendered File menu. No particular applet using the inactive role was identified. |
| **#23 P3, on hold (user, PLAN.md decision 12)** — resizing the top panel breaks the corner treatment | `plasma/make-plasma.py:216`, `plasma/plasmoids/platinum.menubarpiece/contents/ui/main.qml:23` | In the 20 px render the top-left pixel is black as in `reference/desktop-first-check.png` (REFERENCE “Menu bar”). At 32 px it was white and the bar gained a blended #F4F4F4 second row at x=300. The applet's rows remain fixed at 0–19. The 1.5× virtual output showed uneven device-pixel steps in the corner. |

- Inspected desktop, open menu, launcher, edit mode, auto-hide and vertical
  dock renders. Edit mode opened with its controls visible. The left dock
  hid when requested and reappeared when set always visible. It uses the
  unprefixed panel art there. Only the south edge has pop-up-tab artwork.
  With 24 separately registered test windows and three pins on a 1,000 px
  output the dock used the full width and compressed its task buttons.
  Input on every task and reveal timing were not checked. Real dual-4K
  output, moving a window between mixed-DPI screens and GPU-specific
  artifacts remain unverified.
- Regenerating Plasma assets in the temporary tree produced the checked-in
  files. The packaged layout matched the source after its generated comment.
  All 11 SVGs parsed with xmllint and had unique element IDs within each
  document. Inspected center/edge families, directional and mask IDs. Some
  pieces intentionally provide only a center and the border they paint.
  The 5 JSON and 4 scheme/config files parsed.

### 5. Fidelity

The requested suites independently returned **131/131 style regions exact,
7/7 Plasma regions exact and 31/31 install assertions passed**. For the
seven Plasma checks the differences were 0/20, 0/160, 0/160, 0/120, 0/20,
0/57 and 0/57 pixels. These are selected regions at 1×.

Re-measured the desktop base at (5,500) as #63639C, and x=700, y=0–19 as
one white row, 17 #DDDDDD rows, #999999, then black in
`reference/desktop-first-check.png`. The empty trough in
`reference/progress-copy-window.png` at x=650, y=276–289 matched all 14
documented rows including eight #BBBBBB rows. The filled-bar highlight in
`reference/progress-determinate-55.png` at (620,282) was #EEEEEE. The
empty-trough column and the bar's left corner independently diffed 0/14 and
0/160 against the fresh renders. Inspected 4× views of the checked box,
corner and trough alongside the state sheet. Text substitution and derived
states remain outside those matches.

### 6. Documentation and process

**#24 P2, fixed — the general sandbox instructions promise more isolation
than the launcher provides.** `docs/DEVELOPMENT.md:4` describes the development commands collectively
as isolated. `dev/run.sh:107` exports config/data/cache/state directories
and disconnects the session bus, but inherits HOME and XDG_RUNTIME_DIR.
`dev/plasma-test.sh:63` starts a private bus with the inherited runtime.
Programs using HOME directly or contacting user systemd can therefore reach
outside the advertised sandbox. The install fixture does isolate both in its
outer launcher at `dev/test-install.sh:31`. Its inner-mode flag at line 20
assumes the caller has already done that setup. Verified by reading the exec
environments. All runs for this audit also set an outer throwaway HOME and
runtime.

The changelog accurately labels its original packaging run as running without plasmashell.
Its “puts every config file back” claim describes the seed in that fixture.
README's broader undo promise at line 35 fails in #4–#8. AGENTS.md:288 still
calls the style engine undecided although PLAN.md:53 records the decision.
PLAN.md:144 and :151 still ask about the known VM and Wayland shading.
The top of DEVELOPMENT.md describes decoration tools as forthcoming even
though `dev/build.sh` builds them. FINDINGS.md correctly calls out the
20 px panel assumption, the limited global-theme button-order support, and
the need to isolate user systemd.

### 7. Provenance and publication

**#25 P1, open for publication, deferred until the user goes public (PLAN.md decision 12) — the generated source includes sampled
glyph and pointer pixels.** `tools/gen-style-data.sh:182` and :209 emit the
9×8 normal menu check and its highlighted RGB version from the captures.
The clean and raw inputs also coexist in `style/platinum/sprites.h:120`
and :369. The generator appends the corrected shapes at
`tools/gen-style-data.sh:150`, retaining crops explicitly identified as
containing pointer fragments. Checked every retained RGB value against the private reference. All 63
nontransparent values in TrianglePressedRaw and all 434 in PopupArrowPressedA
matched their source crops. The source
also contains sampled slider thumbs, spin arrows, disclosure triangles,
panel corners and button slices. README.md:44 says everything is redrawn.
That description and the project's own no-Apple-material rule need a
provenance review before publication, including already-reachable history.

Inspected local `git log --all --stat`, paths and all **271 distinct blobs
across 31 reachable commits**. No tracked reference capture, standalone
font, binary blob containing NUL, or base64 data URI was found. The
text-encoded tables above survive a binary scan. The reference checkout
was accessed locally and read-only. No remote visibility or unreachable
Git objects were audited. The installable IDs use Platinum/platinum. The
public name remains open under PLAN decision 4. The association with Apple's
appearance warrants a naming review before release. No trademark status or
license clearance for that name was established. [Apple's guidelines for third parties](https://www.apple.com/legal/intellectual-property/guidelinesfor3rdparties.html)

## 2026-11-21, Claude Code (Claude Opus 5.5) — install and uninstall scripts

Audited: `install.sh`, `uninstall.sh`, `scripts/common.sh` in a throwaway
home (`dev/test-install.sh`); working tree after 160b3b6. Not run on the
user's desktop.

Findings: none open. Found and fixed during development: the global theme
skipped the widget style before a re-login (now gets `QT_PLUGIN_PATH`);
install reported a switch even when `plasma-apply-lookandfeel` failed;
uninstall left empty `plasma-workspace/env` folders.

### Checks

`dev/test-install.sh`: 31 of 31: dry runs change nothing; install puts the
7 recorded parts in place and leaves the config files alone; the login
script adds the plugin folder once; the installed style plugin loads;
`--apply` copies the config files (noting absent ones), applies the global
theme (widget style via `kdedefaults`), sets the button order; a second
`--apply` keeps the first copies; uninstall puts every config file back
byte for byte, removes `kdedefaults` (absent before), every installed file
and the record, keeps the replaced files, and only asked systemd whether
Plasma was running.

### Limits

Throwaway home without a running Plasma: the panel layout switch
(`--resetLayout` talks to plasmashell) and the shell restart on uninstall
weren't exercised; a real session is the user's call. Restoring whole
files also undoes settings the user changed while the theme was on (they
are kept in `~/.local/state/macos9-theme-uninstalled-*`).

## 2026-11-21, Claude Code (Claude Opus 5.5) — the dock

Audited: the dock (PLAN.md decision 9): `south-` panel background,
`widgets/tasks.svg`, the dock in `plasma/layout.js`; headless
(`dev/plasma-test.sh`), working tree after 2b3465b.

Findings: none. Fixed during development: one missing white pixel inside
the tab's top-left corner; task frames spanned the dock's full thickness
(now inset inside the frame).

### Checks

`dev/check-plasma.sh`: 7 of 7 exact; new: the dock's top-left and
top-right corners against `finder-popup-tab.png` (57 tab pixels each,
desktop pixels around the tab left out). Looked at (4x): pinned apps as
bare icons, a running app in the raised bevel, the active one in the
selected bevel, both 40 px tall like the Monitors buttons.

### Limits

Headless only; not seen by the user. The bevels are wider than the
Monitors ones (icontasks sizes items by the dock's thickness), the icons
are the icon theme's, attention / progress looks are derived, and the
dock's design itself is ours (Mac OS 9 had no dock).

## 2026-11-21, Claude Code (Claude Opus 5.5) — menu bar ends, divider, look-and-feel package

Audited: `plasma/plasmoids/platinum.menubarpiece`, `plasma/look-and-feel/
platinum.desktop` and the updated layout, headless (`dev/plasma-test.sh`,
also with `M9_APPLY=lnf`); working tree after ca530b0.

Findings: none new. Found: a global theme can't set the title bar button
order (docs/FINDINGS.md), so it moved to the install script's to-do.

### Checks

`dev/check-plasma.sh`: 5 of 5 exact (bar column 0/20, left end 0/160,
right end 0/160, divider 0/120, open title 0/20). Applying the package in
the sandbox set widget style Platinum, color scheme Platinum, Plasma style
platinum, decoration platinum (icons and cursors stay Breeze), and the
layout; the desktop came up Platinum except the button order. JSON and
kcfg files parse; SVGs valid. `dev/check-style.sh` still 131 of 131.

### Limits

Headless only; not seen by the user. The spacing between the clock, the
divider and the Window List follows the applets' own padding (not
measured against Mac OS 9's 7 / 6 px yet). The Apple menu stand-in still
has a placeholder icon. Install / uninstall scripts don't exist yet.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Plasma style and menu bar, first check

Audited: `plasma/platinum/` (generated by `plasma/make-plasma.py`) and
`plasma/layout.js` in a headless nested plasmashell (`dev/plasma-test.sh`,
1440x900), with the decoration and style; working tree before commit.

Findings: none new. Found and fixed during development: Plasma gives panel
applets the panel's full height (the panel's margin hints didn't keep the
open title off the bar's black line), so the open title draws that row
itself; title padding 6 px gives Mac OS 9's 7 / 8 px ink padding.

### Checks

`dev/check-plasma.sh`: the empty bar's column (x=700) and an open global
menu title's column match `desktop-first-check.png` and `menu-file-open.png`
exactly (0 of 20 each). Looked at: the demo's menus move into the global
menu (with `kded6` running), "View" opens under its Lavender title with
the app's Platinum QMenu; the launcher (Kicker) opens in the menu frame
with a focused search field; the clock, tray and Window List (the
Application menu's place) sit at the right; the desktop color matches the
capture's. All SVGs pass `xmllint`, `metadata.json` parses.

### Limits

Headless only; not seen by the user. Not done or not matched: the rounded
screen corners (Plasma drops a top panel's side and top borders), the
divider before the Application menu, the Apple menu icon (a neutral icon
is still to pick), menus open 1 px below the bar's black line (Mac OS 9
overlaps it) and 1 px right of the title, the panel must stay 20 px thick
(its center piece holds the white top row), hover highlights titles
(Plasma's global menu would draw hovered titles in white otherwise).
Plasma tooltips, buttons and fields in popups are generated from measured
data but not compared; the open-applet look (#CCCCFF) is derived.

## 2026-11-21, Claude Code (Claude Opus 5.5) — real-app pass (headless) and tooltips, finding 3

Audited: the whole theme (decoration + style + colors) in Dolphin, Kate
and System Settings (`kcm_mouse`, `kcm_style`) via `dev/app-test.sh`
(headless nested KWin, 1440x900), plus the QML and Kirigami galleries;
style tooltips added in the same session. Working tree after 36673ab.

### Findings

3. **P3, open (plan in PLAN.md, 2026-11-21): Qt Quick menus, tooltips and switches aren't Platinum.**
   qqc2-desktop-style draws them itself (rounded panels with shadows,
   Breeze-like switch) instead of through the QStyle
   (`dev/shots/platinum-quick.png`). Reference: menus `menu-view-checked.png`,
   balloons `help-balloon.png`. Mac OS 9 has no switch; a check box would be
   the closest. Needs a different hook (a Qt Quick Controls style of our
   own, or palette-only tweaks); not done yet.

Found and fixed during the pass (sandbox, not the theme): `dev/run.sh`
wrote `widgetStyle=Union` regardless of `QSTYLE`, so Qt Quick apps fell
back to `org.kde.union`; now `QSTYLE` is written (docs/FINDINGS.md).

### Checks

Dolphin and Kate: frames, toolbars and bevel buttons, menus and menu bar,
document tabs, buttons, scroll bars all Platinum; nothing left in Fusion
that showed. System Settings: with `org.kde.desktop` its controls (search
field with focus ring, buttons, check boxes, radios, sliders, spin boxes,
pop-ups, tool buttons, scroll bars) are Platinum; the style page lists
"Platinum" with a working preview. Tooltip balloon: `dev/check-style.sh`
compares its outline by pixel class with `help-balloon.png` (10 px band,
tail corner left out): 0 of 4880 differ; 131 of 131 regions in total. A
real `QToolTip` renders with see-through corners. ASan + UBSan: styleshot,
the tooltip test and the Kirigami gallery, no reports.

### Limits

Headless and offscreen only; not seen by the user. One window size, empty
data (no mouse found, no recent files). The balloon's top-right corner is
derived; tooltips have no tail.

## 2026-11-21, Claude Code (Claude Opus 5.5) — style batch 7 fidelity check (tool buttons)

Audited: `style/platinum/` tool buttons, toolbars, working tree before
commit. Reference: `controls-monitors.png`, `help-viewer.png` (regions in
`dev/check-style.sh`).

Findings: none.

### Checks

`dev/check-style.sh`: 130 of 130 regions pixel exact. New (12): the large
bevel button normal and selected, the small toolbar bevel (3 px bands on
all four sides, icons excluded). A real `QMainWindow` toolbar (offscreen,
looked at 2x): normal, disabled and checked actions, a separator, a menu
button, text beside icon; a standalone "…" tool button and a checked
large one. ASan + UBSan: no reports, identical render.

### Limits

Offscreen only; not seen by the user yet. Derived: the small bevel's
pressed / checked look (colors mapped like the large bevel's), the menu
triangle on tool buttons with a menu, the toolbar separator (etched pair),
no toolbar background or handle. Which bevel goes where is a judgment:
auto-raise (toolbar) buttons get the small one, others the large one;
Mac OS 9 has no hover-only buttons, so both are always drawn. The size
grip is still Fusion.

## 2026-11-21, Claude Code (Claude Opus 5.5) — style batch 6 fidelity check (groups, lists)

Audited: `style/platinum/` group boxes, separators, list headers,
disclosure triangles and scroll-area frames, working tree before commit.
Reference: `controls-general-controls.png`, `disclosure-triangles.png`,
`appearance-3-fonts-clean.png` (regions in `dev/check-style.sh`).

Findings: none. Found during development: Qt applies `PM_HeaderMargin` on
all four sides and `CE_Header` asks the base style for the label rect, so
the 8 px label inset is drawn by our own `CE_Header`.

### Checks

`dev/check-style.sh`: 118 of 118 regions pixel exact. New (15): the
"Desktop" group box (left 12 columns, top lines right of the title, right
8 columns, bottom 2 rows), both header sections (3 px bands on all sides),
closed and open triangles (whole 17x17), the separator line. Real widgets
(offscreen, looked at 2x): titled, checkable and flat group boxes, a
sorted `QTreeWidget` with header and triangles, an HLine, a text area.
ASan + UBSan: no reports, identical render.

### Limits

Offscreen only; not seen by the user yet. Derived, not captured: the
list / text area frame (the text field's sunken edge and black line, no
focus ring), flat group boxes (top line pair only), pressed header
sections (unchanged), the pressed triangle (sprite generated but Qt gives
branch indicators no pressed state). Titles use the substitute font, so
the title gap's width differs from the capture.

## 2026-11-21, Claude Code (Claude Opus 5.5) — style batch 5 fidelity check (text fields)

Audited: `style/platinum/` text fields (`QLineEdit`), focus ring and spin
boxes, working tree before commit. Reference:
`appearance-3-fonts-clean.png` (regions in `dev/check-style.sh`).

Findings: none.

### Checks

`dev/check-style.sh`: 103 of 103 regions pixel exact. New (10): the Fonts
tab's two size spin boxes, unfocused and focused: the field's outer 5 rows
and columns on all four sides (margin or ring, edge, black line, 2 white)
and the little arrows with the 2 px gap. Real widgets (offscreen): a
framed `QLineEdit` and a `QSpinBox` are both 26 px tall, text and selection
start 3 px inside the black line; focused, read-only (no ring), disabled
fields looked at (2x). ASan + UBSan: no reports, identical render.

### Limits

Offscreen only; not seen by the user yet. Not captured: pressed arrow
halves (drawn like a pressed push button), disabled fields and arrows
(frame unchanged, gray text; arrows washed out), a focus ring in an
inactive window (hidden). Editable combo boxes, multi-line text areas and
list/text frames are still Fusion.

## 2026-11-21, Claude Code (Claude Opus 5.5) — style batch 4 fidelity check (menus)

Audited: `style/platinum/` menus, pop-up menu lists and the menu bar,
working tree before commit. Reference: `menu-view-checked.png`,
`popup-open.png`, `menu-file-open.png` (regions in `dev/check-style.sh`).

Findings: none new. Finding 2 fixed: checked items now show the Mac OS 9
check mark 4 px in, left of the icon (icon 19 px in, as in the Apple
menu), no frame around the icon. Found during development: the capture's
View menu is 180 px wide (not 181); Qt's combo popup delegate covers any
frame behind the list (docs/FINDINGS.md); the check mark on the highlight
differed by up to 2 levels when blended from the black-on-gray mask, so it
is its own measured sprite.

### Checks

`dev/check-style.sh`: 93 of 93 regions pixel exact. New (15): the View
menu rendered by a real `QMenu` (left 20 columns over the whole height,
right 14 columns minus the capture's pointer, the shadow's corners), the
open pop-up list rendered by a real `QComboBox` (left 18 and right 5
columns, minus the pointer), the menu bar's empty stretch and the open
"File" title outside its label. Labels aren't compared (no Charcoal), so
menu widths differ. ASan + UBSan: styleshot and a menu/menu bar/pop-up
test, no reports, identical render. A menu with icons, check marks, a
shortcut and a submenu was looked at (2x), not diffed: no Mac capture has
a checked item with an icon (layout follows the Apple menu's icon offset).

### Limits

The user tried it live (`dev/live-test.sh`: demo menu bar and context
menu, pop-up lists, Dolphin, Kate) on 2026-11-21: "everything looks good
so far", no findings. Not captured: a highlighted last
item (bottom row derived), disabled check marks (`#777777` from the mask),
radio-style menu items (same check mark), tear-off and scroll arrows
(Fusion). A menu opened from a menu bar sits below the bar's black line;
Mac OS 9 overlaps it by 1 px (not checked in Qt). Menu titles use the
substitute font.

## 2026-11-21, Claude Code (Claude Opus 5.5) — first live test (user), findings 1-2

Audited: the user ran `dev/live-test.sh` (nested KWin window on their
desktop, Platinum decoration + style + colors) with Dolphin, Kate and the
demo, at commit c2e581f plus the uncommitted test scripts.

### Findings

1. **P2, fixed (853468b, 2026-11-21): tabs without a pane in document
   mode.** Dolphin's settings
   (`reference/testing/dolphin-settings-tab-lines-seam.png`) use a document-mode
   `QTabWidget`, for which Qt draws no pane: the tabs' pane rows (black,
   `#CCCCCC`, white) and the current tab's `#EEEEEE` opening ended loose
   over the `#DDDDDD` window, a white seam under the tabs. Reference:
   Mac OS 9 tabs always sit on a pane (`appearance-1-themes.png`, REFERENCE
   "Tab pane"). Fix: the style draws the Platinum pane for document-mode
   tab widgets too (event filter on their paint event) and puts the pane
   rect under the tab bar's last 3 rows in both modes. Verified: a
   document-mode tab widget now renders pixel-identical to a normal one
   (offscreen). Also found there: tabs with icons fell back to Fusion's
   label (no white label when pressed, text 3 px low and clipped once the
   padding was right); they now use the Platinum label area and colors
   with Qt's icon + text layout, and `PM_TabBarTabVSpace` is 0.
2. **P3, fixed (menu batch, 2026-11-21): checked menu items with an icon.** Dolphin's
   view-mode menu
   (`reference/testing/dolphin-menu-icon-selected-close-to-border.png`): the
   checked first item gets Fusion's sunken frame around its icon, touching
   the menu's top border. Reference: `menu-view-checked.png` (Mac OS 9 marks
   checked items with a check mark, no icon frame). Menus are still Fusion;
   fix with the menu batch (item metrics, check marks, `#333399` highlight).

### Checks

`dev/check-style.sh`: 78 of 78 regions pixel exact after the fix.
Document-mode vs normal tab widget render: identical. Icon tabs in
document mode, pressed: label centered like plain tabs, white on the
pressed tab (looked at 2x, not diffed: no capture of icon tabs).

### Limits

The fix itself was checked offscreen only; the user hasn't rerun the live
test since. Standalone document-mode tab bars (Dolphin's and Kate's own
document tabs, no `QTabWidget`) still draw the pane rows under the tabs
with no pane below: Mac OS 9 had no document tabs, so that look is still
undecided. Tab scroll buttons are Fusion's.

## 2026-11-20, Claude Code (Claude Opus 5.5) — style batch 3 fidelity check (tabs)

Audited: `style/platinum/` tabs and tab pane, working tree before commit.
Reference: `appearance-1-themes.png`, `appearance-6-options.png`,
`tab-pressed.png` (regions in `dev/check-style.sh`).

Findings: none open. Found during development: above the pane, the
captures' two outermost columns belong to the window (frame black line,
then its content area's white / `#AAAAAA` edge), not to the tabs; the check
leaves them out. The window content edge itself is a note for the
decoration / window background, not a tab issue.

### Checks

`dev/check-style.sh`: 78 of 78 regions pixel exact. New (31): for each of
the three tab rows, the 6 rows above the labels and the 10 rows from below
the labels into the pane (pressed row: split around the pointer), and the
label-free columns at both ends and between all six tabs; the pane's left,
right and bottom bands (whole 466×280 pane). Live `QTabWidget` offscreen:
geometry as measured, selection on release. ASan + UBSan build: no reports
from styleshot or the tab test, render identical to the normal build.

### Limits

Offscreen only; not seen by the user on screen. Label pixels not compared
(Charcoal substitute). Vertical / south tabs, pressed-current and disabled
tabs not captured or themed.

## 2026-11-20, Claude Code (Claude Opus 5.5) — style batch 2 fidelity check

Audited: `style/platinum/` pop-up menus, sliders and progress bars, working
tree before commit. Reference: captures named in `dev/check-style.sh`.

Findings: none open. Fixed during development: the pop-up body's own right
corners showed through the arrow box's transparent corners (the body now
stops where the box starts); both open-menu captures have the pointer over
the pressed arrow box, in different columns, so the pressed box is merged
from the two (columns 0-1 from popup-open-no-hover, the rest from
popup-open) and each part is checked against the capture where it's clean.

### Checks

`dev/check-style.sh`: 47 of 47 regions pixel exact. New: pop-up normal and
disabled (top/bottom 3 rows, left 6 columns, arrow box), pressed arrow box
(two clean parts), slider with ticks (whole 91×23 slider), pressed thumb,
disabled slider (140×16), progress bar at 55 % and empty (188×14 each),
barber pole stripes (60×10, phase pinned with `PLATINUM_BARBER_PHASE=4`).
The gallery renders its real combo boxes, sliders and progress bar with the
style, without warnings.

### Limits

- Pop-up labels and the label position not compared (no Charcoal); the
  pressed pop-up's body is hidden by its menu in both captures, so the body
  isn't checked pressed.
- The slider drag ghost isn't implemented (Qt moves the thumb live); vertical
  sliders are drawn transposed, not captured.
- The barber pole's speed (20 px/s) comes from two frames 0.2 s apart; its
  animation isn't checked frame by frame. Its frame comes from the
  determinate bar (Sherlock draws its own).
- Editable combo boxes and the opened pop-up list are still Fusion.
- Offscreen at 1x only; nothing installed.

## 2026-11-20, Claude Code (Claude Opus 5.5) — style batch 1 fidelity check

Audited: `style/platinum/` (C++ Qt style), working tree before its first
commit. Reference: the captures named in `dev/check-style.sh`; values in
REFERENCE.md and FINDINGS.md.

Findings: none open. Fixed during development: derived marks for uncaptured
radio states first took the whole shading (now only black mark pixels);
push button corner diffs turned out to be the white dialog behind the
captures (the render now matches it); the default button's bottom band
included the "p" of "Open" (now starts a row lower).

### Checks

`dev/check-style.sh`: 31 of 31 regions pixel exact (0 differing pixels each):
push buttons normal / pressed / disabled / default / default pressed (four
edge bands each), check box off / on / off pressed / on disabled, radio off
/ on / off pressed / off disabled, vertical scroll bars with the thumb at
the top and partway down, and the horizontal scroll bar (drawn by
transposing the vertical one, exact on the first try). The style also
renders the real widget gallery without warnings.

### Limits

- Labels not compared (no Charcoal); the label color rule (black, white when
  pressed, `#777777` disabled) is from REFERENCE.md, not diffed.
- Not captured, so derived and unchecked: check box on + pressed, off +
  disabled; radio on + pressed, on + disabled; the mixed (partial) check
  box isn't themed yet.
- The pressed captures' pointer hides a few pixels; those were taken from
  the unpressed outline (gen-style-data.sh says where).
- Rendered offscreen at 1x only; not in a running app in a real compositor,
  not at scale 2. Nothing installed; the user hasn't seen it.

## 2026-11-20, Claude Code (Claude Opus 5.5) — decoration fidelity check

Audited: `decoration/` (Platinum KDecoration3 plugin), working tree before
its first commit. Reference: `window-document-active.png`,
`window-document-inactive.png`, `window-close-pressed.png`,
`window-zoom-pressed.png`; values in REFERENCE.md "Window frame".

Findings: none open. Fixed during development, before this check: the
pinstripes started 1 px late (QRectF::right() is one past the group), the
inactive window's lines and shadow are `#555555`, not black, and the
collapse box was missing on Wayland (see FINDINGS.md; now drawn on the
minimize button).

### Checks

All with `tools/compare.py diff`, reference region against the plugin's
output; 0 differing pixels in every case:

- Active, nested KWin (`kwin-test.sh`, `VT_SINGLE=1`): title bar left end
  60×22 (frame, close box, pinstripe start), left side 6×20, right side
  6×20, bottom edge 20×6, bottom-left corner frame 16×6.
- Active, KWrite in nested KWin (`app-test.sh`): title bar right end 60×22
  (pinstripe end, zoom and collapse boxes, frame), left end 60×22.
- Inactive, KWin's decoration preview (`shoot-deco.sh`): title bar left and
  right 150×22 each, left side, right side, bottom edge.
- Pressed, preview: zoom box top 13×8, close box top 13×7 (the capture's
  pointer covers the rest).

### Limits

- Title text and icon not compared: no Charcoal, and the reference icons
  are Apple artwork. Condensing and dropping long titles was seen working
  in the preview, not measured against Mac OS 9's thresholds.
- Drop shadow not seen: the nested KWin background is black and the
  preview draws no shadow. Code path reviewed only.
- Not tested: maximized windows, X11 apps (real shading), Plasma scale 2,
  the user's real session. Nothing installed. The user hasn't seen it on
  screen yet.

<!--
Template for a new section (copy above the previous newest one):

## YYYY-MM-DD, <Agent> (<model>) — <what was audited>

Audited: <component(s)>, <git commit or "working tree">.
Reference: <reference/ files and docs/REFERENCE.md entries used>.

### Finding N (P1/P2/P3, open): <short title>

What: ...
Where: <file:line or screenshot>
Expected (reference): ...
Measured: ...
Suggested fix: ...

### Checks

- <command or method>: <result with numbers>

### Limits

- <offscreen only / not seen by the user / one app / one scale / ...>
-->
