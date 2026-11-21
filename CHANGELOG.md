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

Next: recheck the Themes tab still says Mac OS Default after the Fonts edits,
then CAPTURES.md group 2 (dialogs and alerts).

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
