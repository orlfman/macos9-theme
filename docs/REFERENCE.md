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
- Appearance control panel not yet confirmed at defaults (theme, highlight
  and accent colors, fonts, smoothing). Until it is, treat colors below as
  provisional.

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
