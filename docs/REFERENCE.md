# Mac OS 9.2.2 reference measurements

Measured from captures of the reference VM (AGENTS.md "The reference VM"),
taken with `tools/capture.py`. Every value names its capture (in
`reference/`, see `reference/INDEX.tsv` for its sha256) and the pixel(s) it
came from. Unmeasured values stay `TBD`.

Confidence: **measured** = read from a capture at the given pixels;
**inferred** = derived from measured values but not read directly;
**TBD** = not measured yet.

## Capture setup

- Guest resolution: 1440×1050, millions of colors (24-bit RGB in the dump).
  Source: `desktop-first-check.png` (2026-11-20). Measured.
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
