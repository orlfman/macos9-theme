# macos9-theme: audit log

Rules: AGENTS.md "Audits". Newest sections first. Finding numbers run across
the whole project and are never reused.

Status: 23 open findings. First-install blockers include #4–#12 (asset ownership, backup coverage, failure recovery and panel restoration). #21 affects a second monitor. #25 blocks publication under the project’s asset rules. Open by severity: P1 #4–#10 and #25. P2 #11–#12, #14–#22 and #24. P3 #3, #13 and #23. #1 and #2 remain fixed.

## 2026-11-21, Codex (GPT-6) — independent review before first install

Reviewed all seven sections of `docs/AUDIT-REQUEST.md` at `591e96d` on
`main`. **Hold both the plain install and `--apply`.** The clean-home tests
pass. An existing color scheme was lost even on a plain install. A running
Plasma session also exposed settings that uninstall leaves behind.

### 1. Install, apply and undo

| Finding | Where | Consequence and verification |
|---|---|---|
| **#4 P1, open** — existing install targets are lost | `install.sh:67`, `install.sh:87`, `install.sh:92`, `scripts/common.sh:153`, `uninstall.sh:64` | Seeded a custom `Platinum.colors` and an extra file inside an existing `desktoptheme/platinum`. Plain install replaced both. After uninstall neither original existed. The first install assumes ownership of all seven destinations, including whole directories. It also removes the fixed directory staging name before copying. |
| **#5 P1, open** — applying the theme changes GTK settings outside the backup | `scripts/common.sh:32`, `install.sh:132`, `uninstall.sh:47` | Hashed the config and data trees before apply, after apply and after uninstall with real plasmashell and kded6 on a private bus. Existing GTK 3 `colors.css`, `gtk.css`, `settings.ini` and `xsettingsd/xsettingsd.conf` still had different hashes after undo. GTK 3 decoration assets and GTK 4 CSS files were also added. Neither the backup nor the dated archive covers these paths. The seeded Plasma panel file itself was restored byte for byte. |
| **#6 P1, open** — a linked config entry can back up its own changes | `install.sh:119`, `uninstall.sh:50` | Tested an absolute `kdedefaults` symlink. `cp -a` preserved the link, so the backup and live path resolved to the same directory. After apply **and** uninstall its original `ColorScheme=MyOriginalScheme` was `Platinum`. Relative links can resolve differently inside the backup, and `-e` classifies dangling links as absent. Separately, linking the entire `.config` parent worked when its entries were regular files/directories. |
| **#7 P1, open** — a partial first install has no usable removal record | `install.sh:67`, `install.sh:107`, `scripts/common.sh:155` | Made the color-schemes parent an ordinary file in a throwaway home. Install exited 1 after placing both plugins and the login script. No manifest existed. Uninstall exited 0 and the style plugin remained. A Ctrl+C between those writes and manifest save has the same ordering. Directory replacement also has a gap between removal and rename. Both builds finish in a temporary directory before the first install write, so a build failure alone avoids this window. |
| **#8 P1, open** — the suggested System Settings switch bypasses the only snapshot | `install.sh:109`, `install.sh:153`, `uninstall.sh:36` | Plain install followed by plain uninstall produced no config snapshot. Traced the printed instruction to select the global theme manually. That route can replace panels before any snapshot exists. A later first `--apply` would save the already-switched desktop. Uninstall then has no copy of the original layout to restore. |
| **#9 P1, open** — recursive removal has no destination or ownership checks | `scripts/common.sh:8`, `scripts/common.sh:121`, `uninstall.sh:47`, `uninstall.sh:64` | Traced the manifest loader to deletion. Both file and directory entries use recursive removal with no check against the seven expected paths, their recorded types, or the home that created the record. A previously installed file replaced by a directory would be deleted with its contents. Config restore also uses today's XDG config root with yesterday's snapshot. Relative XDG roots are accepted. Empty XDG values fall back to HOME, but an empty HOME passes the root-user check for a non-root caller. Reviewed statically. |
| **#10 P1, open** — an interrupted backup can contaminate the next snapshot | `install.sh:116`, `install.sh:120`, `install.sh:125` | Traced a retry after a partial copy of an existing `kdedefaults/`. The same `backup.new` is reused. Copying the directory again into that existing destination nests it one level deeper and leaves stale entries in the outer copy. Only the ABSENT list is truncated. Concurrent invocations also share the staging names with no lock. The final rename only protects an uninterrupted, single-writer copy. |
| **#11 P2, open** — theme application can fail with a successful exit | `install.sh:132`, `install.sh:139`, `install.sh:155` | A stand-in theme applier returned 1 on a private bus. Install warned, wrote `ButtonsOnRight=AI`, printed “Done” and exited 0. Uninstall recovered the seeded kwinrc in this case. A caller cannot distinguish this partial switch by its exit status. |
| **#12 P2, open** — the original snapshot is discarded before panel recovery is confirmed | `uninstall.sh:51`, `uninstall.sh:55`, `uninstall.sh:82` | The two-output sandbox had the original panel file back on disk while the running shell still reported the Platinum panels. The restart happens after both backup and manifest removal. A failed restart leaves no retryable original snapshot, and a dirty shell could write during shutdown. The dated archive contains the outgoing setup. A real user-systemd stop/start and a shutdown overwrite were not demonstrated. |
| **#13 P3, open** — the dry run omits backup and cleanup steps | `scripts/common.sh:39`, `install.sh:114`, `uninstall.sh:39`, `uninstall.sh:69` | Read the dry-run logs. They showed the theme reset and restoration commands but suppressed the “would copy/keep” lines via `say`. Manifest writes/removal and empty-parent cleanup were also absent from the preview. Install briefly creates and removes a temporary directory even in dry mode. The stock before/after checks found no persistent file-content changes from dry install. |
| **#14 P2, open** — a repeat-apply regression can pass the installer suite | `dev/test-install.sh:95`, `dev/test-install.sh:102` | Both apply exit statuses are discarded. The repeat assertion compares a copy made **before** the second apply with the seed. It never rereads the backup for that assertion. Final uninstall gives some indirect coverage. Independently compared the entire backup after both successful applies in a home with a pre-existing defaults tree. The bytes matched on this revision. |

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
| **#15 P2, open** — scroll and slider arithmetic exceeds the supported int range | `style/platinum/platinumstyle.cpp:165`, `style/platinum/platinumstyle.cpp:953` | Range, position offset and range plus page step are evaluated as signed int before the 64-bit scrollbar calculation. Valid int endpoints can overflow or yield the wrong thumb geometry. The tick-spacing limits also add/subtract an interval as int, and the paint loop scales with the number of values even when many ticks map to one pixel. Verified by reviewing expression types and loop bounds. The ordinary render sanitizer pass below does not cover these extremes. |
| **#16 P2, open** — keyboard focus is invisible on common controls | `style/platinum/platinumstyle.cpp:1443`, `style/platinum/platinumstyle.cpp:1396` | In an active offscreen widget window, moved Tab focus from another field to a normal push button, check box and tab bar, verified `hasFocus()`, then compared each widget grab. Each changed **0 pixels**, at 1, 1.25, 1.5 and 2×. The line edit changed 1,734 pixels at 1×. This prevents a keyboard user from identifying the current target even when the measured decoration is accurate. |
| **#17 P2, open** — partially checked looks unchecked | `style/platinum/platinumstyle.cpp:1557` | A real tristate QCheckBox gave identical grabs for Unchecked and PartiallyChecked at all four scales. The painter tests only `State_On`. A settings dialog can therefore misrepresent a mixed selection. |
| **#18 P2, open** — switching styles loses widget-owned appearance settings | `style/platinum/platinumstyle.cpp:1648`, `style/platinum/platinumstyle.cpp:1686` | Set QMenu margins to (3,4,5,6), polished with Platinum and switched to Fusion. The resulting margins were (0,0,0,0). The tooltip and combo container also acquire translucent backgrounds, and the popup view loses its frame and autofill without symmetric restoration. Filters are removed and the named progress timer is deleted. |
| **#19 P2, open** — control geometry does not mirror in RTL | `style/platinum/platinumstyle.cpp:831`, `style/platinum/platinumstyle.cpp:168` | A 120×20 non-editable combo returned the same right-hand arrow rectangle (98,0,22,20) in both directions. The custom spin, group and menu geometry also uses fixed left/right offsets. The scrollbar calculation ignores `upsideDown`, so its thumb geometry also ignores reversed direction. |

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

**#20 P2, open — custom title-bar actions look like Close.**
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
| **#21 P2, open** — the second monitor loses its panel | `plasma/layout.js:16`, `plasma/layout.js:53` | Seeded a bottom panel on virtual output 0 and a left panel on output 1. Queried the running shell before and after the actual installer's `--resetLayout`. Both new panels reported screen 0, top and bottom. Output 1 had no panel. The layout also changes wallpaper on every desktop at line 65. This affects the user's two-screen setup. |
| **#22 P2, open** — selected secondary text can have zero contrast | `plasma/make-plasma.py:413`, `plasma/platinum/colors:105` | The generated Selection group sets both `ForegroundInactive` and `BackgroundNormal` to RGB (51,51,153), a 1:1 contrast ratio. A consumer using that pair will hide the text. Normal selected text is white and readable in the rendered File menu. No particular applet using the inactive role was identified. |
| **#23 P3, open** — resizing the top panel breaks the corner treatment | `plasma/make-plasma.py:216`, `plasma/plasmoids/platinum.menubarpiece/contents/ui/main.qml:23` | In the 20 px render the top-left pixel is black as in `reference/desktop-first-check.png` (REFERENCE “Menu bar”). At 32 px it was white and the bar gained a blended #F4F4F4 second row at x=300. The applet's rows remain fixed at 0–19. The 1.5× virtual output showed uneven device-pixel steps in the corner. |

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

**#24 P2, open — the general sandbox instructions promise more isolation
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

**#25 P1, open for publication — the generated source includes sampled
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

3. **P3, open: Qt Quick menus, tooltips and switches aren't Platinum.**
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
