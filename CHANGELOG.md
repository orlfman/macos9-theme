# macos9-theme: changelog

Newest first. Format and rules: AGENTS.md "CHANGELOG entries".

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

Next: commit; then CAPTURES.md group 6 (menus).

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
