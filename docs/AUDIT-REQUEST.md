# Audit request: full review before the first real install

Requested by the user on 2026-11-21, written by Claude Code (Claude Opus 5.5),
for Codex (or any other agent). Covers everything up to commit 5680c10 plus
the status-line fixes after it.

So far everything has been checked only by the agent that built it
(Claude Code), in the sandbox, and much of it headless. The user hasn't
installed the theme on their real desktop yet. Before they do, a second,
independent look is wanted: what's wrong, what's risky, and what was
claimed but isn't true.

## Ground rules

- Read `AGENTS.md` first (it's the shared guide), then `PLAN.md`, the
  newest `CHANGELOG.md` entries, `AUDIT.md`, and `docs/DEVELOPMENT.md`.
- **This is an audit, not a fix pass.** Record what you find in `AUDIT.md`
  as described in AGENTS.md "Audits": one new dated section by you, findings
  numbered from **4** (1–3 are taken), each with severity (P1/P2/P3),
  status `open`, the file and line, and how you verified it. Don't edit code
  in any component unless the user tells you to and you claim it in
  `PLAN.md`'s Claims table.
- **Never touch the live desktop.** Don't run `install.sh` or
  `uninstall.sh` against the real home, don't run `plasma-apply-*`,
  `kwriteconfig6` on the real config, or restart plasmashell / KWin. Use the
  sandbox scripts in `dev/` (they use their own XDG folders and a private
  D-Bus). `dev/test-install.sh` runs the scripts in a throwaway home and is
  safe.
- `reference/` is a separate **private** repository of Mac OS 9 screenshots
  (Apple artwork). Read it, never copy anything from it into this repo, and
  never make it public. On a fresh clone:
  `git clone https://github.com/orlfman/macos9-theme-reference reference`.
- Say plainly what you couldn't check (no Wayland session, missing package,
  and so on) rather than guessing.

## Setup and the checks to run

On this machine (Plasma 6.8.3, Qt 6.12, Wayland), from the project root:

```bash
dev/check-style.sh
```

```bash
dev/check-plasma.sh
```

```bash
dev/test-install.sh
```

```bash
dev/test-install-live.sh
```

Expected: 131 of 131 style regions pixel exact, 7 of 7 Plasma parts exact,
230 of 230 install checks, 17 of 17 live checks, 13 of 13 Qt Quick checks (`dev/check-quick.sh`). Report any difference with its output. Then look
at the renders yourself (`dev/shots/`), not only the numbers.

## What to audit

### 1. Install and uninstall (highest priority: these will run on the real desktop)

Files: `install.sh`, `uninstall.sh`, `scripts/common.sh`,
`dev/test-install.sh`.

- Can either script delete or overwrite something it shouldn't? Every
  `rm -rf` and `cp`, unset or empty variables, paths with spaces, a
  `~/.config` that is a symlink.
- Partial failures: the plugin build fails halfway; `plasma-apply-lookandfeel`
  fails after the backup was made; the user presses Ctrl+C mid-run. Is the
  state still recoverable by `uninstall.sh`?
- Repeats and odd orders: install twice, `--apply` twice, uninstall without
  `--apply` ever having run, uninstall twice, install again after
  uninstall, an existing `~/.config/kdedefaults` before `--apply`.
- Does `--dry-run` match what a real run does, and change nothing?
- The whole-file backup and restore: is the list of files
  (`backup_files`, `backup_dirs`) complete for what applying a global theme
  and `--resetLayout` change? Anything else written (e.g. other Plasma or
  KWin files, `kscreenlockerrc`, `kxkbrc`, `Trolltech.conf`, GTK settings
  synced by kde-gtk-config)?
- The login script (`~/.config/plasma-workspace/env/macos9-theme.sh`): is
  `QT_PLUGIN_PATH` set safely for every Qt program (KWin, plasmashell,
  apps)? Any risk if the plugin folder is empty or the plugins are stale
  after a Qt / Plasma upgrade (a decoration built against an older KWin)?
- `uninstall.sh` restarts `plasma-plasmashell.service`: is that safe and
  enough to bring the user's panels back?
- Are there gaps in `dev/test-install.sh` that a real run would hit (it has
  no running Plasma, so `--resetLayout` and the restart aren't exercised)?

### 2. The application style (C++)

Files: `style/platinum/platinumstyle.{h,cpp}`, `plugin.cpp`, the generated
headers (`slices.h`, `sprites.h`, `progress.h`, `tabs.h`, `menu.h`) and
their generators (`tools/gen-style-data.sh`, `tools/tabs.py`,
`tools/nineslice.py`, `tools/sprite.py`).

- Crashes and undefined behavior: rects smaller than a nine-slice or a
  sprite, zero or negative sizes, indexes past a table, null `widget`
  pointers (Qt Quick passes none), options of an unexpected type.
- `polish` / `unpolish` symmetry: attributes, event filters, contents
  margins and timers it adds (menus, tooltips, combo popups, tab widgets,
  progress bars). Anything left behind when the style changes at run time?
- The event filter that paints document-mode tab widget panes, and the
  combo popup handling that relies on the private class name
  `QComboBoxPrivateContainer`: robust, or fragile across Qt versions?
- **Scaling:** everything is drawn with 1 px `fillRect`s at logical
  coordinates. What happens at device pixel ratios 1.25, 1.5 and 2 (seams,
  gaps, blurry or misplaced pixels)? The user may scale one 4K screen.
  Check with `QT_SCALE_FACTOR` in the sandbox (`SCALE=1.5 dev/run.sh ...`).
- Right-to-left layouts (never handled on purpose), vertical and south tabs,
  vertical sliders and progress bars, disabled and inactive-window states.
- Accessibility: the style hides focus rectangles on buttons, check boxes
  and tab bars (Mac OS 9 has none). Is keyboard focus still visible enough
  anywhere? Flag it if not.
- Performance: per-pixel drawing in balloons, menus, tabs, check marks.
  Any hot path worth worrying about?
- Builds with no warnings (`style/build.sh`); a run under ASan/UBSan
  (CHANGELOG has the commands) if you can.

### 3. The window decoration (C++)

Files: `decoration/platinum.{h,cpp,json}`, `decoration/build.sh`.

- The same crash, scaling and rebuild questions as for the style.
- Behavior KWin users hit: maximized and tiled windows, border sizes,
  narrow windows, long titles, the collapse box being minimize on Wayland
  (docs/FINDINGS.md).

### 4. Plasma

Files: `plasma/make-plasma.py`, `plasma/layout.js`, the generated
`plasma/platinum/`, `plasma/plasmoids/platinum.menubarpiece/`,
`plasma/look-and-feel/platinum.desktop/`, `dev/plasma-test.sh`,
`dev/plasma-session.sh`, `dev/check-plasma.sh`.

- **Multiple monitors:** the user has two 4K screens. `layout.js` removes
  every panel and creates one menu bar and one dock. Which screen do they
  land on, and what does the second screen get? Is that acceptable or a
  finding?
- `layout.js` removes all existing panels without asking; it's applied by
  the global theme's `--resetLayout`. Combined with section 1: is the old
  layout always recoverable?
- The menu bar is only pixel exact at 20 px thickness (its white top row
  is in the SVG's center piece). What happens if the user resizes it, or at
  other scale factors?
- The `platinum.menubarpiece` plasmoid draws runs of 1 px rectangles:
  anything that breaks at fractional scaling or in Plasma's edit mode?
- SVG validity, element names Plasma looks for, the `colors` file (it makes
  Plasma's selection `#333399` with white text): any Plasma text that
  becomes unreadable because of it?
- The dock (`south-` panel background, `widgets/tasks.svg` with insets
  built into the frames): does it hold up with many apps, hidden or
  auto-hide, or a vertical screen edge?

### 5. Fidelity spot checks

- Pick a few claims in `docs/REFERENCE.md` at random and re-measure them in
  the captures yourself (`tools/compare.py` can read pixels and crops).
- Look for places where the code uses a value that isn't in
  `docs/REFERENCE.md` or is marked as derived without saying so.
- Compare a few renders with the captures by eye at 4x
  (`tools/compare.py zoom`).

### 6. Documentation and process

- Are `AGENTS.md`, `PLAN.md`, `README.md`, `docs/DEVELOPMENT.md` and
  `docs/FINDINGS.md` accurate for the current code? Stale statements,
  commands that no longer work, claims without a check behind them.
- Is the `CHANGELOG.md` honest about what was and wasn't verified?

### 7. Legal (before anything goes public)

- Nothing from `reference/` or any Apple file in this repo's git history
  (`git log --all --stat`, binary files, fonts).
- The generated tables (`sprites.h`, `tabs.h`, `menu.h`, `slices.h`) are
  pixel values measured from Apple's rendering; `menu.h`'s check mark is a
  rendered Charcoal font glyph. PLAN.md already says the check mark and
  radio dot should be redrawn before a public release. Is anything else in
  the same category?
- Names: installable IDs use "platinum" / "Platinum" (Apple's name for the
  appearance). Note any trademark concern; PLAN.md decision 4 (the name) is
  still open.

## What to hand back

1. Your section in `AUDIT.md` (findings from #4, checks run with results,
   limits of your test), and the status line at its top updated.
2. Your own `CHANGELOG.md` entry.
3. A short summary for the user: the findings that should block the first
   real install (P1/P2), and what can wait.
