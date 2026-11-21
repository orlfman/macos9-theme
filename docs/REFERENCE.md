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
| Scroll box fill (Lavender) | `#CCCCFF` | (912,423) |
| Scroll box grip lines | `#333399` on `#CCCCFF`, 4 lines 1 px apart, `#9999FF` above and below | x=912, y=424–435 |
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
