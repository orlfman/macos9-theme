# Mac OS 9.2.2 reference measurements

Measured from captures of the reference VM (AGENTS.md "The reference VM"),
taken with `tools/capture.py`. Every value names its capture (in
`reference/`, see `reference/INDEX.tsv` for its sha256) and the pixel(s) it
came from. Unmeasured values stay `TBD`.

Confidence: **measured** = read from a capture at the given pixels;
**inferred** = derived from measured values but not read directly;
**TBD** = not measured yet.

## Capture setup

- Guest resolution: 1440×1050, millions of colors (24-bit RGB in the dump),
  for captures up to `button-default-pressed.png`; **1920×1080** from
  `controls-monitors.png` on (user changed it in Monitors, 2026-11-20).
  Always 1x; positions differ between the two sizes, sizes don't.
- Appearance control panel (captured 2026-11-20, one capture per tab):

| Tab | Setting | Value | Capture |
|-----|---------|-------|---------|
| Themes | Current theme | Mac OS Default (Save Theme… disabled = unmodified) | `appearance-1-themes.png` |
| Appearance | Appearance | Apple platinum | `appearance-2-appearance.png` |
| Appearance | Highlight color (selected text) | Purple | same |
| Appearance | Variation (menus and controls) | Lavender | same |
| Fonts | Large system font (menus, headings) | Charcoal | `appearance-3-fonts-clean.png` |
| Fonts | Small system font (labels) | Geneva | same |
| Fonts | Views font (lists, icons) | Geneva 10 | same |
| Fonts | Smooth all fonts on screen | on, for 12 pt and larger | same |
| Desktop | Pattern | Mac OS Default, 128×128 tile | `appearance-4-desktop.png` |
| Desktop | Picture | None | same |
| Sound | Sound track | Platinum Sounds; menus, windows, controls, Finder all on | `appearance-5-sound.png` |
| Options | Smart Scrolling | **on**: both arrows at the bottom/right end, proportional scroll box | `appearance-6-options.png` |
| Options | Double-click title bar to collapse | off | same |

  Smart Scrolling on is taken as part of the Mac OS Default theme because
  the Themes tab showed the theme unmodified (inferred; recheck the Themes
  tab still says Mac OS Default after the Fonts-tab edits below).

  Not clean: `appearance-3-fonts.png` and `appearance-3-fonts-fixed.png`
  have a stray `^` in a size box (Alt+Tab out of the VM types into the
  focused field; release the VM with Ctrl+Alt+G first). The Views size was
  retyped as 10 and the smoothing size as 12 before the clean capture. Both
  flawed captures still show the lavender focus ring on a text field.

## Desktop

| What | Value | Source | Confidence |
|------|-------|--------|------------|
| Default desktop pattern, base color | `#63639C` | `desktop-first-check.png` (5,500) | measured |

## Menu bar

Column x=700 of `desktop-first-check.png`, top to bottom:

| Rows (y) | Height | Color | What |
|----------|--------|-------|------|
| 0 | 1 px | `#FFFFFF` | top highlight |
| 1–17 | 17 px | `#DDDDDD` | fill |
| 18 | 1 px | `#999999` | bottom shadow |
| 19 | 1 px | `#000000` | bottom line |

Total height 20 px. Confidence: measured (one column; corners, rounded
screen corners, and the menu title highlight are TBD).

## Lists and scroll bars (first samples)

Single pixels from `list-view-profiler-applications.png` (Apple System
Profiler list, active window). Measured; edges, bevels, and other states TBD.

| What | Value | Pixel |
|------|-------|-------|
| List header, sorted column | `#888888` | (450,297) |
| List header, other columns | `#CCCCCC` | (560,297) |
| List cell, sorted column | `#DDDDDD` | (500,322) |
| List cell, other columns | `#EEEEEE` | (620,322) |
| Scroll track (active) | `#AAAAAA` | (912,350) |
| Scroll box (Lavender), normal | highlight `#CCCCFF` (top/left), fill `#9999FF`, shadow `#6666CC` (bottom/right), black frame | `disclosure-triangles.png` row y=250; `scroll-vertical-inactive.png` row y=330 (corrected 2026-11-20: (912,423) is the top highlight row of a 16 px box, not its fill) |
| Scroll box grip | 4 dark `#333399` lines alternating with light `#CCCCFF` lines, centered on the box | x=912, y=426–433 |
| List selection (highlight color "Purple") | `#CCCCFF` | `dialog-file-open.png` (780,341) |
| List background (Standard File) | `#FFFFFF` | `dialog-file-open.png` (780,377) |

## Check boxes, radio buttons, sliders (first samples)

From `controls-general-controls.png` (General Controls, active). Measured
bounding boxes of non-background pixels on the `#DDDDDD` window fill.

| What | Size | Notes |
|------|------|-------|
| Check box, off | 12×12 px (550,327) | 1 px black frame, white top-left inner highlight, `#888888` inner shadow right/bottom, `#DDDDDD` fill |
| Check box, on | 14×12 px (550,280) | the check mark overhangs the box 2 px to the right |
| Radio button, off | 12×12 px (553,534) | shaded sphere, light top-left to dark bottom-right |
| Radio button, on | 12×12 px (553,552) | dark ring, black center dot |
| Slider thumb | Lavender pointer, 3 vertical `#333399`-ish grip lines, points down at the tick marks | sizes TBD |
| Check box, pressed (off) | 12×12 px (`checkbox-pressed.png`) | bevel reversed and darkened: row 333 = black, `#555555` (inner top-left shadow), `#777777` fill, `#999999` (inner bottom-right), black |
| Radio button, pressed (off) | 12×12 px (`radio-pressed.png`) | dark sphere, gradient reversed: middle row 539 runs `#444444` → `#999999` left to right (unpressed: `#FFFFFF` → `#888888`) |
| Slider thumb fill | `#9999FF` normal, `#6666CC` while dragging | (766,442) in `controls-general-controls.png` / `slider-pressed.png` |
| Slider drag ghost | a gray copy of the thumb (`#DDDDDD`/`#AAAAAA` with `#666666` grip lines, see-through look) follows the pointer; the real thumb stays put, darkened, until release | `slider-pressed.png` around (790,442) |

## Menus (first samples)

From `popup-open.png` (Highlight Color pop-up menu open, pointer on the
current item). Measured.

| What | Value | Pixel |
|------|-------|-------|
| Menu background | `#DDDDDD` | (700,330) |
| Highlighted item (Lavender variation) | `#333399`, white text | (700,306) |
| Menu edge, right and bottom, outward | `#999999` (inner shadow), `#000000` (border), `#222222` (1 px drop shadow) | row 330 x=749–751; column 700 y=378–380 |
| Current item | check mark in the left margin, same row stays highlighted when hovered | (598,306) |
| Check box, disabled (on) | 13×12 px (`controls-memory.png` (553,511)) | flat: only `#888888` (frame and check mark) on `#DDDDDD`, no bevel |
| Slider thumb, disabled | `controls-memory.png` (672–692,481–500) | outline only: `#777777` edge, `#BBBBBB` track, no Lavender fill or grip |
| Disclosure triangle (closed / open) | `disclosure-triangles.png` (108–124,194–210) and (108–124,270–286) | black outline, Lavender fill `#CCCCFF`/`#9999FF`, `#BBBBBB` drop shadow down-right; the open one points down. Same pixels in an inactive Finder window (712,341) |
| Finder list, sorted column cells | `#DDDDDD` (others `#EEEEEE`), active and inactive alike | `disclosure-triangles.png` (300,190), (800,500) |
| Sort direction button | top-right corner of the list header: a small stepped pyramid of lines | `disclosure-triangles.png` (490–508,156–172) |
| Disclosure triangle, pressed | `triangle-pressed.png` (108–124,213–229) | fill turns dark `#333399`, no gray shadow; outline stays black |
| Push button, pressed | `button-push-pressed.png` (Cancel, column x=650, y=469–488) | 20 px tall: black, `#444444`, `#555555`, `#666666` fill, `#777777`, `#888888`, black; **white** label |
| Default button (normal) | `button-push-pressed.png` (Find, column x=740, y=466–492) | ring outside the button: black, `#DDDDDD`, `#AAAAAA` on top and `#AAAAAA`, `#777777`, black at the bottom; then the button: black, `#DDDDDD`, `#FFFFFF` highlight, `#DDDDDD` fill, `#AAAAAA`, `#777777`, black |
| Default button, pressed | `button-default-pressed.png` (Find, column x=716, y=510–535) | ring unchanged (black, `#DDDDDD`, `#AAAAAA` / `#AAAAAA`, `#777777`, black); the button inside has exactly the pressed push-button rows (black, `#444444`, `#555555`, `#666666`…, `#777777`, `#888888`, black), white label |
| Radio button, disabled (off) | `controls-monitors.png` (731–745,404–418) | flat: only a `#888888` circle outline on `#DDDDDD`, no shading |
| Bevel button, normal | `controls-monitors.png` (Color, column x=860, y=315–354) | rounded corners; black, `#DDDDDD`, `#FFFFFF` highlight, `#DDDDDD` fill, `#AAAAAA`, `#777777`, black |
| Bevel button, selected (on) | `controls-monitors.png` (Monitor, column x=805) | same as a pressed push button: black, `#444444`, `#555555`, `#666666` fill, `#777777`, `#888888`, black; icon drawn dark on it |
| Scroll bar track, active (vertical) | `scroll-vertical-inactive.png` (System Folder, row y=480, x=787–802) | 16 px wide: black, `#777777`, `#888888`, `#AAAAAA` ×10, `#BBBBBB`, `#CCCCCC`, black (sunken track) |
| Scroll bar, inactive (scrollable content) | `scroll-vertical-inactive.png` (Applications, row y=400, x=1656–1671) | flat `#EEEEEE` with a `#555555` frame line; **no scroll box and no arrows** even though the content overflows |
| Scroll arrow, pressed | `scroll-arrow-pressed.png` (System Folder down arrow, x=780–806, y=578–594) | column x=790: normal = black, `#FFFFFF`, `#DDDDDD` fill, `#BBBBBB`, black; pressed = black, `#555555`, `#777777` fill, `#999999`, black (same as the pressed check box); black arrow glyph unchanged; the two arrow boxes are stacked at the end of the bar (Smart Scrolling) |
| Scroll box, dragging | `scroll-thumb-dragging.png` (System Folder, row y=380, x=787–803) | one step darker: highlight `#9999FF`, fill `#6666CC`, shadow `#333399` (normal `#CCCCFF` / `#9999FF` / `#6666CC`); **the Finder list scrolls live**, no ghost outline (unlike the slider) |
| Scroll track, pressed | `scroll-track-pressed.png` (System Folder) | **no visible change**: track rows and scroll box look the same as unpressed; the list just pages |
| Progress bar track, empty | `progress-copy-window.png` (column x=650, y=276–289) | 12 px between the outer lines: `#AAAAAA` (outer shadow above), black, `#888888`, `#BBBBBB` ×8, `#DDDDDD`, black, `#FFFFFF` (outer highlight below) — a sunken gray trough |
| Menu bar title, pressed | `menu-file-open.png` ("File") | title highlighted `#333399` with white text while its menu is open (same as a menu item highlight) |
| Progress bar, filled part | `progress-determinate-55.png` (column x=620, y=277–287) | a Lavender "tube", 10 px between black lines, top to bottom: `#333399`, `#6666CC`, `#9999FF`, `#CCCCFF`, `#EEEEEE` (center highlight), `#CCCCFF`, `#9999FF`, `#6666CC`, `#333399`, `#000055` |
| Progress bar, end of fill | `progress-determinate-55.png` (row y=282, x=690–696) | the fill ends in `#CCCCFF`, `#333399`, `#000055`, black; the empty trough right after it starts with a `#555555`, `#888888` shadow before its `#BBBBBB` |
| Barber pole (indeterminate progress) | `progress-indeterminate-a.png` / `-b.png` (Sherlock 2 "Searching…", bar at x≈1076–1175, y≈470–483) | diagonal stripes, 8 px Lavender + 8 px gray along a row (16 px period), each stripe tube-shaded top to bottom: gray `#555555`, `#777777`, `#AAAAAA`, `#BBBBBB`…; blue `#CCCCFF`, `#9999FF`, `#6666CC`, `#333399`, `#000088`, `#000055`; black frame. Moves **4 px to the right** between frames 0.2 s apart |
| Text selection, active | `text-selection-word.png` | solid `#CCCCFF` behind normal black text; past the line end it fills to the right edge of the text area (`text-selection-to-line-end.png`) |
| Text selection, inactive window | `text-selection-inactive.png` ("Apple") | **outline only**: a 1 px `#CCCCFF` rectangle around the selected text, white inside |
| Finder list, selected item (active) | `list-view-selection.png` ("Documents") | **not a row highlight**: only the name label is inverted (black box, text in the column color `#DDDDDD`), and the icon is darkened; the rest of the row is unchanged |
| Finder list, selected item (inactive window) | `list-view-selection-inactive.png` | **selection not shown at all**: label and icon look unselected; column header and window header text turn gray |
| Tab, pressed | `tab-pressed.png` ("Sound", held while "Appearance" is current) | tab fills: normal `#CCCCCC` with black label, current `#EEEEEE` (same as the panel it joins), pressed `#666666` with **white** label |
| Text field focus ring | `help-viewer.png` (Help search field, column x=200, y=51–75) | 2 px `#6666CC` ring directly outside the field's 1 px black frame; white field |
| Toolbar bevel buttons | `help-viewer.png` (back / forward / home, x≈14–90, y≈50–74) | small square bevel buttons with Lavender icons; the disabled one (forward) shows a washed-out icon |
| Submenu placement | `menu-submenu.png` (Apple menu > Control Panels) | the parent item stays highlighted `#333399`; the submenu's top black edge (y=131) sits 1 px above the parent item's highlight (y=132), so first items line up; its left black edge (x=201) starts right at the parent menu's right edge |
| Menu inner edge, top/left | `menu-submenu.png` (x=202, y=132) | 1 px `#FFFFFF` highlight inside the black border, then `#DDDDDD` |
| Apple menu | `menu-submenu.png` | "About This Computer" alone above a separator; every item has a 16 px icon; submenu arrows on folders |
| Finder selection rectangle (marquee) | `finder-marquee-many.png` (corner near (683,378)) | 1 px dotted line made by **inverting every other pixel** (black dots on white, yellowish where it crosses an icon), like the window drag outline; icons inside darken and their names invert as soon as the rectangle touches them |
| Finder name being edited | `finder-rename.png` ("Sherlock 2") | name sits in a 1 px black-framed edit box, text selected with the `#CCCCFF` highlight (black text), icon stays darkened |
| Pop-up window tab (closed) | `finder-popup-tab.png` (x≈632–818, y=1061–1080, column x=720) | sits on the bottom screen edge; rounded top corners; black edge, `#FFFFFF` highlight, `#CCCCCC` fill; folder icon + title in the large system font |
| Help balloon | `help-balloon.png` (x≈1688–1852, y≈138–272) | white fill, 1 px black outline with a heavier black edge right and bottom (shadow), rounded corners, a pointed tail to the hovered spot (top right here), text in the small system font |
