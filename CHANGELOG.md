# macos9-theme: changelog

Newest first. Format and rules: AGENTS.md "CHANGELOG entries".

## 2026-11-21, Claude Code (Claude Opus 5.5) — step 4: application style, batch 4 (menus)

Claimed `style` (and `shared` for tools/dev/docs), released at the end.
Done from the user's phone over Remote Control; nothing needed the VM.

- Menus (`QMenu`): measured frame (black line, white/`#999999` bevel,
  `#222222` drop shadow, see-through outer corners via
  `WA_TranslucentBackground` and a 1 px right/bottom contents margin),
  16 px items (18 with an icon), 6 px separators, Lavender highlight
  bevel, check mark 4 px in (left of the icon; icon 19 px in, label 22 or
  41 px in), submenu arrow, shortcut column ending 21 px before the edge.
  Fixes AUDIT finding 2 (Fusion's frame around a checked icon).
- Pop-up menu lists (`QComboBox` popups): the same menu look; the list is
  see-through and each item draws its slice of the bevel, because Qt's
  delegate fills items first (docs/FINDINGS.md).
- Menu bar (`QMenuBar`): 20 px bar (white top row, `#999999` and black at
  the bottom), open title in the Lavender bevel, titles padded 7 px.
- `tools/gen-style-data.sh` writes `style/platinum/menu.h`: the check mark
  as a coverage mask (any color) and as a sprite on the highlight (Mac OS 9
  blends it to `#FEFEFE` there).
- `dev/styleshot.cpp` renders a real QMenu (the Finder's View menu), a
  real combo popup (Appearance's Highlight Color list) and menu bar
  titles; `dev/check-style.sh` compares them. `dev/livedemo.cpp` has a menu
  bar (File / View / Special with checks, icons, a submenu, shortcuts) and
  a right-click menu.
- `docs/REFERENCE.md`: menu frame, items, separator, highlight, check mark
  and arrow, pop-up list, menu bar title.

Checks: `dev/check-style.sh` 93 of 93 regions pixel exact; ASan + UBSan
clean. The user tried it live (`dev/live-test.sh`): looks good, no findings.

Next batch: text fields and the 2 px `#6666CC` focus ring, then group
boxes, list headers + disclosure triangles, mixed check box, size grip.

## 2026-11-21, Claude Code (Claude Opus 5.5) — live test script, document-mode tabs

- `dev/live-test.sh` + `dev/live-session.sh` + `dev/livedemo.cpp`: the
  theme on the user's own desktop for trying by hand: a windowed nested
  KWin (sandboxed config, private D-Bus, nothing installed) with the
  Platinum decoration, style and colors, running an interactive demo of
  every themed control, Dolphin and Kate. Documented in
  `docs/DEVELOPMENT.md`.
- First live test by the user: two findings (AUDIT.md 1-2).
- Style fix (finding 1): document-mode tab widgets (KDE settings pages)
  now get the Platinum pane; Qt draws none there, which left a white seam
  under the tabs. The pane rect is computed the same way in both modes.
  Icon tabs use the Platinum label area and colors (were Fusion's, text
  clipped); `PM_TabBarTabVSpace` = 0.
- Finding 2 (Fusion's frame around a checked menu item's icon, touching
  the menu border) waits for the menu batch.

Checks: `dev/check-style.sh` 78 of 78; document mode renders identical to
normal mode offscreen. Not yet seen by the user after the fix.

Next (user's call, asked 2026-11-21): the menu batch (finding 2,
`menu-view-checked.png`, `menu-file-open.png`, `menu-submenu.png`,
`popup-open.png`) or text fields + focus ring first. Also open: how
standalone document-mode tab bars (Dolphin/Kate document tabs) should look.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: application style, batch 3 (tabs)

Claimed `style` (and `shared` for the tools/dev/docs edits), released at
the end.

- Tabs (north tab bars): drawn row by row from measured edges. New
  `tools/tabs.py` reads each tab state's left and right edge, row by row,
  from a tab whose edge has no neighbor (first tab's left, last tab's
  right) and writes `style/platinum/tabs.h`; the pressed tab's right edge
  turned out to be clean in `tab-pressed.png` (the pointer is inside the
  tab), so nothing is derived. Fill per row = first color repeated 3 times
  after the edge (labels can start right after the edge).
- Tab pane (`PE_FrameTabWidget`): a measured 9-slice (`TabPane`, added to
  `tools/gen-style-data.sh`); `PE_FrameTabBarBase` draws the pane's top
  3 rows under a lone `QTabBar`.
- Metrics: tab height 24 (21 + the 3 pane rows it overlaps), width = text
  + 24, no tab overlap, first tab 5 px in from the pane, contents 3 px
  inside the pane. Label centered in the 20 rows below the top line, black,
  white on the pressed tab, `#777777` disabled. No focus rectangle on tab
  bars. `SH_TabBar_SelectMouseType` = release: the tab shows pressed while
  held and switches on release, as in Mac OS 9.
- `dev/styleshot.cpp` lays out the Appearance control panel's six tabs
  three times (Themes current with the whole pane; Appearance current with
  Sound pressed; Options current); `dev/check-style.sh` compares them.
- `docs/REFERENCE.md`: tab shape, tab row layout and pane rows.

Checks: `dev/check-style.sh` 78 of 78 regions pixel exact (31 new tab
regions). A live `QTabWidget` (offscreen) lays out as measured: tab bar at
x=5, tab widths = text + 24, page at the pane's inside; a press on "Sound"
keeps "Themes" current until release. First ASan + UBSan run of the style
(styleshot and the tab test): no reports, identical render.

Not done: vertical (west/east) and south tabs still come from Fusion;
pressing the current tab and disabled tabs were not captured (current look
kept / normal shape with gray label); labels use the substitute font, so
widths differ from Charcoal's by a few pixels.

Next batch: text fields and the 2 px `#6666CC` focus ring, then group
boxes, list headers + disclosure triangles, menus, mixed check box, size
grip.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: application style, batch 2

Claimed `style`, released at the end. Tabs moved to their own batch: their
slanted, overlapping edges need clean ends from several captures.

- Pop-up menus (non-editable combo boxes): measured body 9-slice plus a
  22-column arrow box sprite, normal / pressed / disabled; label black or
  `#777777`. The pressed box is merged from two captures (pointer in each).
- Sliders: 7-row groove from measured end pieces and a stretched middle
  column (disabled: 5 rows, no outer lines), 15×16 thumb sprites (normal,
  pressed, disabled), tick marks (white, black, `#888888`) under the
  thumb's center; vertical sliders transposed.
- Progress bars: drawn column by column from profiles measured in the 55 %
  frame (frame, fill start, fill middle, fill end, black divider, 2-column
  trough shadow, trough, last column); 0 % matches the empty copy window.
  The barber pole uses the measured stripe ramps, 8 px Lavender / 8 px
  gray, slanting one pixel per row, moving 20 px/s; busy bars get a
  100 ms repaint timer from `polish()`. No text, as in Mac OS 9.
- `tools/gen-style-data.sh` also writes `progress.h` and the new sprites;
  `dev/styleshot.cpp` and `dev/check-style.sh` cover the new widgets.

Checks: 47 of 47 regions pixel exact; the gallery renders. Limits in
AUDIT.md.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: application style, batch 1

Claimed `style`, released at the end (more batches to come).

- `style/platinum/`: a Qt style plugin ("Platinum", a QProxyStyle over
  Fusion, built by `style/build.sh`). Themed so far: scroll bars (vertical
  from the spike, horizontal by transposition), push buttons (normal,
  pressed, disabled, default ring, default pressed), check boxes and radio
  buttons (captured states plus derived pressed-on / disabled states), no
  focus rectangle on buttons. Metrics in `Metrics` in `platinumstyle.h`.
- Measured data instead of hand-coded pixels: `tools/nineslice.py`
  (9-slice tables, checks edge uniformity, marks only background connected
  to the outside), `tools/sprite.py` (fixed-size parts), and
  `tools/gen-style-data.sh`, which regenerates `slices.h` and `sprites.h`
  from the captures and repairs the few pointer-covered pixels from the
  unpressed outline. The default ring measured from two different captures
  came out identical (289 values).
- `dev/styleshot.cpp` + `dev/check-style.sh`: render every state through
  the style's draw calls at the captures' sizes and diff them;
  `dev/run.sh` now puts the built style and decoration on QT_PLUGIN_PATH
  and only links folders with `contents/` as Union styles.

Checks: `dev/check-style.sh` 31 of 31 regions pixel exact; the widget
gallery renders with the style. Limits in AUDIT.md (labels, derived states,
offscreen only). PLAN.md notes that the measured check mark and radio dot
should be redrawn by hand before any public release.

Next batches: pop-up menus (combo boxes), tabs, sliders, progress bars
(determinate and barber pole), text fields and focus ring, group boxes,
list headers and disclosure triangles, menus, the mixed check box, the size
grip.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: window decoration plugin

Claimed `decoration`, released at the end.

- `decoration/platinum.{h,cpp,json}` + `build.sh`: a KDecoration3 plugin,
  structure adapted from the user's windows2000-union decoration. 6 px
  frame with raised and sunken bevels, 22-row title bar, close / zoom /
  collapse boxes (normal and pressed), etched pinstripes, centered icon and
  title (condensed, then dropped when too long), flat inactive look with
  `#555555` lines, hard 1 px drop shadow (black / `#555555`). All metrics in
  `Metrics` in `platinum.h` (true 1x). Builds with no warnings.
- Measured on the way: the full window frame, inactive lines `#555555`,
  pressed box ramp `#44`→`#CC` capped at `#99` on its last row/column.
  REFERENCE.md "Window frame".
- Found: Wayland windows report `isShadeable() == false` in KWin 6.8.3, so
  the Shade button never shows; the minimize button now wears the collapse
  box and the Mac layout is `X` | `AI`. KWin's decoration preview ignores
  the button layout, draws no shadow and is 1 px smaller. FINDINGS.md.
- `dev/`: `decoshot.cpp`, `decoration.qml`, `shoot-deco.sh` from
  windows2000-union, adapted; `kwin-test.sh` / `app-test.sh` set the Mac
  layout with `M9_DECORATION=platinum`; `VT_SINGLE=1` for one window.
  DEVELOPMENT.md section "The window decoration".

Checks: every frame region compared is pixel exact against the captures,
active (nested KWin, KWrite), inactive and pressed (preview). Details and
limits in AUDIT.md: title text, the drop shadow, maximized and X11 windows
aren't verified, nothing is installed, and the user hasn't seen it.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: color scheme

Claimed `colors`, released at the end.

- Measured the remaining text colors: disabled text is `#777777` everywhere
  (menu items, button labels), inactive title and header text `#777777`,
  inactive title bar face `#DDDDDD`, links `#0000FF`. Added to REFERENCE.md.
- `colors/Platinum.colors`: Window/Button/Header `#DDDDDD`, View and
  Tooltip `#FFFFFF`, Selection `#CCCCFF` with black text, focus/hover
  decoration `#6666CC`, links `#0000FF`, `[WM]` title faces
  `#CCCCCC`/`#DDDDDD`. Disabled text comes from a contrast fade of 0.54,
  which turns black on `#DDDDDD` into exactly `#777777` without touching
  backgrounds. Inactive-window effects off. Not measured (Mac OS 9 has no
  such colors): negative/neutral/positive, visited links, Complementary;
  the file's header says so. The menu highlight (`#333399`, white text)
  can't share KDE's single Selection group with text selection; the C++
  style will draw it.

Checks: the file parses (13 sections, all 12 keys in each of the 8 color
groups, every value a valid RGB triple); `dev/shoot.sh breeze platinum`
renders the widgets, Quick and Kirigami galleries with it; in the widgets
render the selected row is exactly `#CCCCFF`, views `#FFFFFF`, and disabled
button and check box labels exactly `#777777` on `#DDDDDD`. Shapes are still
Breeze's (no Platinum style yet). Not installed or applied to the desktop.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 3 spikes: style and decoration engines

Claimed `style` and `decoration` for the spikes, released at the end.
Details and numbers in the new `docs/FINDINGS.md`.

- `spikes/scrollbar/probe.cpp`: Union 6.8.3 gives a scroll bar's arrow,
  groove and page areas 0×0 (Qt Windows/Fusion give 16×16 arrows), so
  Union can't draw Platinum scroll arrows.
- `spikes/scrollbar/platinum.cpp`: a C++ QProxyStyle (over Fusion) drawing
  a vertical Platinum scroll bar from the measured values. After three
  fixes (thumb shadow start, grip `#EEEEEE` pixels, track starting below
  the bar's top edge) it matches two captures pixel exact: 0 of 5536 px
  (System Folder, thumb at top) and 0 of 5152 px (Applications, thumb
  partway down).
- Aurorae (read in `/usr/share/kwin/aurorae/aurorae.qml`): the title is
  elided `Text` over a fixed FrameSvg, so no pinstripe gap around the
  title, no condensing, no dropping.
- `spikes/titlebar/titlebar.cpp`: a QPainter Platinum title bar (frame,
  drop shadow, three boxes with their gradient and glyphs, etched
  pinstripes); first try pixel exact on both sides of the title in the
  417 px Mac OS window (0 of 6940 px) and in the 289 px long-title window
  (0 of 920 px left; 2 of 980 px right, both in the drop-shadow corner
  where the window behind shows).

PLAN.md decisions 2 and 3: the user approved C++ for both (C++ QStyle,
C++ KDecoration3), same day. Not checked: pressed/inactive states in the spikes, horizontal bars,
title text, real KDecoration3 plugin, Qt Quick apps through
qqc2-desktop-style, Kvantum (not installed).

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 2: sandbox, compare tool, scale

Claimed `shared` for PLAN step 2, released at the end.

- `dev/`: ported the generic parts of the user's windows2000-union test rig
  (BSD-2-Clause): `run.sh` (sandbox; schemes `platinum`/`breeze`/`user`/file,
  every folder under `style/` linked as a Union style, new `EXTRA_FONT_DIRS`
  for stand-in fonts, Wine Tahoma bits dropped), `build.sh` (gallery,
  quickshot, tabdemo, fakeinput; decoration tools deferred), `shoot.sh`,
  `kwin-test.sh` / `app-test.sh` (decoration chosen with `M9_DECORATION`,
  default Breeze), session scripts, test QML/C++ and the fake-input
  protocol. `dev/shots/` git-ignored.
- `tools/compare.py`: `row`, `col`, `colors`, `bbox`, `zoom`, and `diff`
  (same-size regions, any image with an `@X,Y,W,H` crop; counts, max
  difference, bounding box, side-by-side picture, exit 1 on differences).
- `docs/DEVELOPMENT.md`: how to use both. AGENTS.md and PLAN.md point to it.

Checks: `dev/build.sh` builds all four tools; `dev/shoot.sh breeze breeze`
renders the widgets, Quick and Kirigami galleries; `dev/kwin-test.sh breeze`
screenshots two Breeze windows in a nested KWin. `compare.py` reproduces
earlier hand measurements (selected bevel button column, 12×12 check box),
gives 0 / 120 differing pixels for identical / normal-vs-pressed check box
crops, refuses crops outside the image, and runs clean under
`-W error::DeprecationWarning`. No shellcheck on this machine. Found on the
way: the watch cursor crop has two `#9C9C63` pixels (the desktop color
inverted), so Mac OS cursors can invert pixels, not just paint them.

Decision 1 (scale) settled by the user: true 1x at Plasma 100%, to be
tweaked after testing; recorded in PLAN.md with the numbers behind it.

Next: step 3 spikes (style engine, decoration engine), or measuring passes
per component.

## 2026-11-20, Claude Code (Claude Opus 5.5) — reference capture tool

The user set up Mac OS 9.2.2 in QEMU (`/mnt/storage1/local/VM/mac-os-9`,
QEMU 9.1 screamer fork). It was started without a QMP socket, so it can't be
captured yet.

- `tools/capture.py`: connects to QEMU's QMP socket, runs `screendump`
  (PPM, because this QEMU build has no libpng), converts it to PNG with
  Pillow, checks that the PNG matches the PPM pixel for pixel, and logs time,
  size, and sha256 in `reference/INDEX.tsv`. Never overwrites, names limited
  to `[a-z0-9._-]`.
- Tested against a second, throwaway headless QEMU (OpenBIOS, no disk):
  800×600 capture saved and logged, overwrite and bad name refused. Not yet
  run against the real VM.
- AGENTS.md: reference VM facts and capture rules. PLAN.md: step 1 status.

Later the same day: the user relaunched the VM with
`-boot c -qmp unix:$XDG_RUNTIME_DIR/mac9-qmp.sock,server=on,wait=off`;
`--check` reported QMP ok. First real capture
`reference/desktop-first-check.png`: 1440×1050, crisp 1x, logged in
INDEX.tsv, and git ignores it as intended. Started `docs/REFERENCE.md` with
the guest resolution, desktop base color `#63639C`, and the 20 px menu bar
(1 px `#FFFFFF`, 17 px `#DDDDDD`, 1 px `#999999`, 1 px `#000000`).

Then captured every tab of the Appearance control panel
(`reference/appearance-1-themes.png` … `appearance-6-options.png`) and
recorded the settings in `docs/REFERENCE.md`: Mac OS Default theme, Apple
platinum, Purple highlight, Lavender variation, Charcoal / Geneva / Geneva
10, smoothing from 12 pt, Mac OS Default pattern, Platinum Sounds, Smart
Scrolling on, double-click collapse off. Alt+Tab out of the VM typed `^` into
the focused size box twice; the user retyped 10 and 12, and
`appearance-3-fonts-clean.png` is the clean Fonts capture. Release the VM
with Ctrl+Alt+G before switching away.

Then wrote `docs/CAPTURES.md`: the checklist of states to capture (eight
groups, priority A/B/C, with names, setup steps, and which theme part each
serves), and added `--delay SECONDS` to `tools/capture.py` so the user can
hold a button down while it captures (countdown, then a terminal beep;
tested 2.5 s against a throwaway QEMU). Linked from AGENTS.md and PLAN.md.

Group 1 started: `window-close-pressed.png` (user ran it with `--delay`;
the pressed close box is a dark gradient, the cursor covers its lower-right
corner). INDEX.tsv had two entries for it because the user deleted a
failed first try (empty shot) and retook it; I removed the deleted one's
line. While checking, I found that two overlapping runs with the same name
could both pass the exists check before `--delay` ends, so the PNG is now
created with `open(..., "xb")` and each run uses its own temp PPM: an
overlapping run refuses instead of overwriting (tested with two overlapping
runs against a throwaway QEMU). Deleting a bad capture and retaking it
under the same name is fine; remove its INDEX line too.

Group 1 (windows and title bars) finished, 12 captures; details are in
the ticked items of `docs/CAPTURES.md`. Findings for the decoration:

- Pressed close/zoom/collapse boxes fill with a dark gradient, glyphs stay.
- Inactive windows drop the pinstripes, all three boxes, scroll arrows, and
  the size box grip; title and header text turn gray.
- Long titles are drawn condensed first; when even that doesn't fit, the
  text is dropped and only the title icon stays (no "…" seen; an
  in-between ellipsis stage is unchecked).
- Moving and resizing draw an outline (every other pixel color-inverted)
  instead of moving the window; the resize outline sketches the frame and
  title bar. KWin likely can't do this; to check.
- A collapsed window keeps its full title bar and frame.

At the user's request, `reference/` became its own git repo, pushed to the
**private** GitHub repo `orlfman/macos9-theme-reference` as a cloud backup
(21 captures, INDEX.tsv, a README warning it must stay private, and a
.gitignore for capture.py's temp PPMs). This repo keeps ignoring
`reference/`. AGENTS.md says how to clone it and when to push captures.

Group 2 (dialogs and alerts) finished: 8 captures plus the user's extra
System Profiler list shot (`list-view-profiler-applications.png`). Findings:

- Alerts and movable modals share a frame with a pinstriped drag strip and
  no title. The Finder's Empty Trash alert has a **red-tinted** strip
  (`#FFCCCC`/`#FF6666`/`#FF9999` instead of `#CCCCCC`/`#777777`/
  `#999999`); unconfirmed, check against real hardware.
- SimpleText uses the classic Standard File Open and Save As dialogs (plain
  modal frame, no title bar); a Navigation Services dialog is still to get.
- Get Info windows have no zoom box. Classic Dialog Manager text fields
  (SimpleText Find) have no focus ring; Appearance-aware ones do.
- First list and scroll bar values went into REFERENCE.md: Purple
  selection `#CCCCFF`, active track `#AAAAAA`, Lavender scroll box
  `#CCCCFF` with `#333399` grip lines, sorted column header `#888888`.
- Renamed two captures: the accidental Save As shot is
  `dialog-save-as-standard-file.png`, the user's extra shot is
  `list-view-profiler-applications.png` (INDEX.tsv updated).

Group 3 (buttons and toggles) finished: General Controls, Memory, Monitors,
open pop-ups, Finder list with disclosure triangles, and pressed states for
check box, radio, slider, triangle, push and default buttons. Measured into
REFERENCE.md (sizes and pixel rows):

- Check boxes and radios are 12×12; disabled ones are flat `#888888`
  outlines; pressed ones go dark with the bevel reversed.
- Pressed push buttons, selected bevel buttons, and the inside of a pressed
  default button share one look: `#444444`/`#555555` top, `#666666` fill,
  `#777777`/`#888888` bottom, white label. The default ring never changes.
- Sliders don't track live: the real thumb darkens to `#6666CC` and a gray
  ghost follows the pointer.
- Menus: `#DDDDDD`, highlight `#333399` with white text, `#999999` inner
  shadow, black border, 1 px `#222222` drop shadow. Pop-up menus open over
  the control with the current item in place; Mac OS 9 menus stay open after
  one click, so open menus need no `--delay`.
- Disclosure triangles: Lavender with black outline and gray shadow, dark
  `#333399` when pressed, Lavender even in inactive windows.

Two missed captures (radio, pop-up) were deleted and retaken. From
`controls-monitors.png` on, the VM runs at 1920×1080 (user's change), still
1x. Little arrows pressed is skipped for now (pressing changes settings);
a mixed check box is optional. Captures pushed to the reference repo
(`ce910d1`, 41 captures).

Group 4 started: `scroll-vertical-inactive` (inactive windows hide the
scroll box and arrows even when content overflows), `scroll-arrow-pressed`,
`scroll-thumb-dragging` (scroll box one step darker, Finder scrolls live, no
ghost), `scroll-track-pressed` (no visual change). Corrected REFERENCE.md:
the normal scroll box is highlight `#CCCCFF` / fill `#9999FF` / shadow
`#6666CC`; the earlier "fill `#CCCCFF`" came from the top row of a 16 px box.

A Finder copy is too quick to capture by hand, so `tools/capture.py` got
`--burst SECONDS` (and `--interval`, default 0.1 s): one QMP connection,
PPM frames to a temp dir under `$XDG_RUNTIME_DIR`, consecutive identical
frames dropped, the rest saved as `NAME-001.png`... with the same PNG check
and INDEX lines. Refuses if `NAME-001.png` etc. exist; limits 0–120 s and
≥ 0.02 s. Tested against throwaway QEMUs: 5 s burst while typing 5 keys
into the console = 50 frames, 5 kept; a static 2 s burst = 1 kept; reuse
and limits refused; no temp dirs left. Not yet run on the real VM.

Burst mode worked on the real VM. Group 4 finished:

- A small file copies too fast for the progress window to stay up
  (`progress-copy-window.png`, empty bar, under 0.3 s); duplicating the
  625 MB Starcraft zip gave a 35 s copy: `progress-determinate-early`,
  `-40`, `-55`, `-80`, `-expanded`. The fill is a Lavender tube
  (`#333399`→`#EEEEEE` center→`#000055`), the empty part a sunken
  `#BBBBBB` trough.
- Barber pole from a Sherlock 2 search (`progress-indeterminate-a/-b`):
  diagonal 8 px Lavender / 8 px gray stripes, tube-shaded, moving 4 px
  right per 0.2 s.
- Bonus frames kept: `menu-file-open.png` (File menu with disabled items,
  shortcuts, submenu arrows, pressed menu title) and
  `dialog-get-info-inactive.png` (dimmed controls in an inactive window).
- Bursts are pruned by hand: only the useful frames are kept (renamed),
  the rest deleted with their INDEX lines.

Group 5 (text, lists, tabs) finished. Most items were already covered
by earlier captures; new ones:

- Text selection by burst: `text-selection-word.png` (`#CCCCFF` fill),
  `text-selection-to-line-end.png` (fills to the right edge past the line
  end), `cursor-ibeam.png`. Inactive window: `text-selection-inactive.png`
  shows only a 1 px `#CCCCFF` outline.
- Finder list selection inverts just the name label (black box) and darkens
  the icon, no row highlight (`list-view-selection.png`); in an inactive
  window it isn't shown at all (`list-view-selection-inactive.png`).
- Tabs: normal `#CCCCCC`, current `#EEEEEE` (joined to the panel), pressed
  `#666666` with a white label (`tab-pressed.png`).

Group 6 (menus) finished, plus an extra `help-viewer.png` (the user's
idea: toolbar bevel buttons with Lavender icons, the 2 px `#6666CC` text
field focus ring, an inactive Appearance panel with every control dimmed).
Menus: `menu-view-checked` (hover and pressed title both `#333399`, check
marks, disabled item, submenu arrow, shortcut), `menu-submenu` (Apple menu
with icons; submenu's top edge 1 px above the highlighted parent row, left
edge at the parent's right edge; 1 px white inner top/left edge),
`menu-application` (Hide/Show items, running apps with icons, front app
checked), `menu-contextual` (plain menu, Help first, opens at the click
point). A scrolling menu is optional and skipped (nothing is long enough at
1920×1080).

Group 7 (Finder and desktop) finished; icon view, icon selection, desktop
pattern, and both Trash icons were already covered. New: `finder-marquee-many`
/ `-partial` (burst; the selection rectangle is a dotted line of inverted
pixels, like the window drag outline), `finder-button-view` (square bevel
buttons), `finder-rename` (black-framed edit box, `#CCCCFF` selection),
`finder-popup-open` / `-zoom-outline` / `-tab` (pop-up windows dock to the
bottom edge, animate as a gray zoom outline, and close to a rounded
`#CCCCCC` tab; the tab hid behind the Control Strip until dragged), and four
Control Strip frames from a burst (volume slider pop-up, module menus that
open upward). Launcher and spring-loaded folders are optional and skipped.
Bursts pruned to the useful frames.

Group 8 (help, cursors, misc) finished as far as practical:
`help-balloon.png` (white rounded balloon, black outline heavier right and
bottom, pointed tail). The user saw the watch and hand cursors during two
bursts, but no dump contains them; probably they aren't in the guest
framebuffer that `screendump` reads (unverified). Skipped for now (see
CAPTURES.md for options). Bonus keepers: `finder-icon-opening.png` (opening items get a
dark dotted "open" icon) and `dialog-modal-plain.png` ("About Balloon Help":
plain modal, thick double frame, no drag strip). Note and stop alert icons
and the startup screen are optional.

**Capture pass done**: 81 captures in the private reference repo, all
priority A and B items in CAPTURES.md ticked. PLAN.md step 1 updated.

At the user's request, `tools/capture.py` got `--fast` (burst every 0.01 s,
interval floor lowered to 0.005 s) and stops a burst early when the temp dir
has under 1 GiB free. Measured on the real VM first (20 dumps to scratch,
nothing written to `reference/`): a 1920×1080 dump takes 4.0–4.5 ms, hashing
it ~2 ms. Tested on a throwaway QEMU: a 2 s `--fast` burst took 199 frames
and kept the 4 that changed while 3 keys were typed; `--fast` without
`--burst` and too small intervals are refused; no temp dirs left. Then run on
the real VM: an 8 s `--fast` burst took 791 frames (175 different) while the
user opened Apple System Profiler and caught the watch cursor, three steps of
the spinning-disc cursor, and the contextual-menu cursor. So those cursors
are in the framebuffer after all, just very brief; the earlier guess was
wrong and the notes are corrected. The user also confirmed an earlier
all-identical fast burst was their own miss, not the VM freezing.

**Mistake:** while pruning that burst I used a zsh `for` loop with
`set -- $p`; zsh doesn't word-split, every rename failed, and the following
`rm` still ran and deleted all 175 frames, keepers included (not yet backed
up). Recovered the five cursor crops (32×32 around the pointer) pixel-exact
from the 4× nearest-neighbour zoom image I'd made just before, verified by
round trip, and logged them in INDEX.tsv. Full-frame context is lost.
CAPTURES.md now has a pruning rule: rename keepers, verify, then delete, in
one Python script.

Next: commit; then PLAN.md step 2 (sandbox tooling from windows2000-union,
plus a screenshot comparison tool) and settle decision 1 (scale).

## 2026-11-19, Claude Code (Claude Opus 5.5) — project setup

Started the project at the user's request. Created the shared agent docs,
modeled on htop-gpu's setup and extended for several agents working on
separate components:

- `AGENTS.md`: purpose, read-first order, layout, claims-based multi-agent
  rules, audit procedure and severities, fidelity rules (measured reference
  only), legal rules (no Apple material in git), general rules, checks, prior
  work to reuse (windows2000-union), machine facts.
- `CLAUDE.md`: points Claude Code at AGENTS.md.
- `PLAN.md`: status with the Claims table, open decisions (scale, style engine,
  decoration engine, name, fonts, menu bar), components, order of work.
- `AUDIT.md`: empty log with the entry template.
- `README.md`, `.gitignore` (`reference/` and build output ignored).

Checked: Plasma/KWin/union/aurorae/kdecoration 6.8.3 and Qt 6.12.0 installed;
both displays 3840×2160 at scale 1.

At the user's request: `git init` (branch `main`, identity `orlfman` with
the GitHub noreply address), first commit, and a **private** GitHub repo
https://github.com/orlfman/macos9-theme as `origin`, pushed.

Not done: no reference captures, no theme files. Next: step 1 in PLAN.md (reference captures), which
needs Mac OS 9.2.2 media from the user.
