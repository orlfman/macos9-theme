# macos9-theme: audit log

Rules: AGENTS.md "Audits". Newest sections first. Finding numbers run across
the whole project and are never reused.

Status: eight checks so far (decoration, style batches 1-6, first live test; 2026-11-21). Open findings: none.

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
