# macos9-theme: plan

## Status

Updated: 2026-11-19 (Claude Code). Phase: project setup, nothing built yet.

### Claims

One row per component. `nobody` = free. See AGENTS.md "Working together".

| Component  | Folder(s)                 | Claimed by | Status      |
|------------|---------------------------|------------|-------------|
| shared     | docs, tools, dev, scripts | nobody     | docs set up |
| reference  | reference/, docs/REFERENCE.md | nobody | capture pass done (81 captures, CAPTURES.md); measurements partial |
| colors     | colors/                   | nobody     | not started |
| decoration | decoration/               | nobody     | not started |
| style      | style/                    | nobody     | not started |
| plasma     | plasma/                   | nobody     | not started |
| icons      | icons/                    | nobody     | not started |
| cursors    | cursors/                  | nobody     | not started |
| gtk        | gtk/                      | nobody     | not started |
| extras     | extras/, wallpapers/      | nobody     | not started |
| packaging  | install.sh, uninstall.sh, packaging/ | nobody | not started |

## Goal

Make Plasma 6.8 look as close as possible to Mac OS 9.2.2 with the default
Platinum appearance, measured against the real system. See AGENTS.md
"Fidelity rules" and "Legal rules".

## Decisions

Open decisions need the user. Record the answer here with the date.

1. **Scale.** Both 4K screens run at scale 1, where 1x Mac OS 9 metrics are
   tiny. Options: (a) draw at 1x and let the user set Plasma scale 2,
   (b) build the theme at a fixed 2x pixel size (every 1 px edge = 2 px) so it
   works at scale 1, (c) make the multiplier a build option. *Open.*
2. **Application style engine.** Union can't draw scroll bar arrows or two
   bevel layers in Qt Widgets (windows2000-union findings, recheck on 6.8.3).
   Options: Union style (supported, limited), a C++ QStyle (full control, more
   work, must follow Plasma/Qt updates), or Union now and C++ later.
   Kvantum is another candidate to evaluate. *Open; a spike in step 3 decides.*
3. **Decoration engine.** C++ KDecoration3 (like windows2000-union, exact
   pixels, collapse = window shade) vs Aurorae SVG (simpler, less control).
   *Leaning C++, open.*
4. **Name and IDs.** Neutral installable IDs without "Apple"/"Mac OS".
   *Open.*
5. **Fonts.** Charcoal (system) and Geneva (small) can't ship. Find the
   closest freely licensed substitutes, or let the user point at their own
   copies at install time. *Open.*
6. **Menu bar.** How close to get: global menu + Apple-menu stand-in
   (launcher) + clock + application switcher on the right. *Details open.*

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
- **icons**: evaluate NineIcons Redux, Platinum9, Chi-Nata (licenses!) vs
  drawing our own; fallback chain for missing names.
- **cursors**: arrow, I-beam, watch (busy), crosshair, hand; redrawn.
- **gtk**: GTK 3 and GTK 4/libadwaita colors and shapes as far as supported.
- **extras**: Konsole/Alacritty/kitty colors, wallpaper (redrawn Platinum
  pattern/default desktop look), SDDM, splash, lock screen.

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
   tool. Settle decision 1 (scale).
3. **Spikes.** Decide the style engine (decision 2) and decoration engine
   (decision 3) by drawing one scroll bar and one title bar each way.
4. **colors** → **decoration** → **style** (the bulk of the look).
5. **plasma**: menu bar layout, Plasma style, look-and-feel package.
6. **icons**, **cursors**, fonts.
7. **gtk**, **extras**.
8. **packaging**: install/uninstall to user scope with backups; full audit;
   user's on-screen review.

## Open questions

- Which Mac OS 9.2.2 media/emulator does the user have?
- Include Mac OS 9 sound set equivalents? (Can't ship Apple sounds.)
- Window shade (collapse) vs minimize: KWin supports shading; check that the
  collapse box can trigger it and how it looks.
