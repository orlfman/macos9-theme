# macos9-theme: audit log

Rules: AGENTS.md "Audits". Newest sections first. Finding numbers run across
the whole project and are never reused.

Status: Findings #49–#53 are fixed and tested; nothing blocks the first desktop install except the user's go-ahead. Open: #3 (P3) waits for the user's review of the Qt Quick style. User decisions still apply to #21 (main screen only), #26 (RTL unsupported), #23 (resizing on hold) and #25 (deferred until publication).

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
