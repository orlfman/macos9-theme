# macos9-theme: agent guide

Shared instructions for every AI agent working on this project. Codex reads this
file directly; Claude Code reads it through `CLAUDE.md`. Anything an agent needs
to know lives in this folder, never only in one agent's private memory. If you
learn something the next agent needs, write it here, in `PLAN.md`, or in
`docs/`.

## What this is

A full KDE Plasma 6.8 theme that makes the desktop look as close as possible
to Mac OS 9.2.2 with its default Platinum appearance. The goal is fidelity, not
"inspired by": colors, bevels, metrics, and widget shapes are measured from
the real system and matched pixel for pixel wherever Plasma allows it. Where
Plasma can't match, the gap is written down (README "Known limitations" and
`docs/FINDINGS.md`), not hidden.

Pieces, roughly in the order they matter for the look (details and status are
in `PLAN.md`):

- Color scheme (`.colors`)
- Window decoration (Platinum title bar: pinstripes, close box left, zoom and
  collapse boxes right): a C++ KDecoration3 plugin (decided 2026-11-20)
- Application style for Qt Widgets and Qt Quick apps (Platinum buttons,
  scroll bars with arrows, tabs, check boxes, etc.): a C++ QStyle (decided
  2026-11-20; Union and Aurorae can't do it, see docs/FINDINGS.md)
- Plasma style + layout: top menu bar (Apple-menu stand-in, global menu, clock,
  application menu on the right); optional Control Strip-like panel
- Icons, cursors, fonts (substitutes), wallpaper
- GTK 3/4 and terminal colors (Konsole, Alacritty, kitty)
- Splash, SDDM, lock screen (later)

Personal project first. It may become public later, so the legal rules below
apply from the start.

## Read first

1. `PLAN.md`: goal, fidelity rules, components, decisions, order of work, and
   the **status block** (who is working on what).
2. The newest entries in `CHANGELOG.md`: what the last session did and what's
   next.
3. The status lines at the top of `AUDIT.md`: open findings.
4. `docs/REFERENCE.md` before drawing anything: the measured Mac OS 9.2.2
   colors and metrics, each with its source.
5. `docs/CAPTURES.md` when capturing: the checklist of states still to
   capture, naming, and how pressed states are timed (`--delay`).
6. `docs/DEVELOPMENT.md` before testing anything: the sandbox and the
   comparison tool.
7. `docs/FINDINGS.md` before choosing a technique: what Plasma, KWin, Union,
   Aurorae, and Qt can and can't draw, as verified in this project.

## Layout

```
AGENTS.md  CLAUDE.md  PLAN.md  CHANGELOG.md  AUDIT.md  README.md
docs/        REFERENCE.md (measured spec), FINDINGS.md (verified platform facts),
             plus one file per larger component plan when PLAN.md gets long
reference/   Mac OS 9.2.2 captures: ignored here, its own private repo (below)
colors/      color scheme(s)
decoration/  KWin decoration (C++ KDecoration3 or Aurorae, see PLAN.md)
style/       application style (Union style or C++ QStyle, see PLAN.md)
plasma/      Plasma style (desktoptheme), look-and-feel package, layout script
icons/  cursors/  wallpapers/  gtk/  extras/ (konsole, alacritty, kitty, ...)
dev/         sandbox and screenshot tooling, builds go in dev/build (ignored)
spikes/      throwaway experiments that settled a decision (docs/FINDINGS.md)
tools/       checkers and generators
packaging/   later: PKGBUILD
install.sh  uninstall.sh   later: user-scope install and full undo
```

Create folders when their step starts, not ahead of time.

- This folder is its own git repo, branch `main`, remote `origin` =
  https://github.com/orlfman/macos9-theme (**private** since 2026-11-19; it
  stays private until the user says otherwise). The `gh` CLI is logged in as
  `orlfman`, and git uses it for github.com over HTTPS.
- Nothing from `reference/`, `dev/build/`, or any Apple file ever goes into
  this repo.
- `reference/` is a separate git checkout: private repo
  https://github.com/orlfman/macos9-theme-reference (created 2026-11-20 as
  the cloud backup of the captures; **never make it public**, it contains
  Apple artwork). On a fresh clone of this repo, get it with
  `git clone https://github.com/orlfman/macos9-theme-reference reference`.
  Commit and push new captures there (with `INDEX.tsv`) whenever this repo
  is committed or a capture group is finished; that's the user's standing
  request, since `/home` has no other backup. Same identity and
  `Co-Authored-By:` rules.
- `reference/testing/` (same private repo): the user's screenshots of
  problems found while testing our theme (`dev/live-test.sh`), copied from
  `~/Pictures/Screenshots/testing/`, each listed in `testing/INDEX.tsv`
  with its `AUDIT.md` finding number. Cite them in findings by that path.
  They show our theme, not Mac OS 9: never measure from them.

## Working together (multiple agents)

Agents on this project: Codex and Claude Code, sometimes more than one session
of each, and subagents started by either. The rules below keep them from
overwriting each other.

### Claims

`PLAN.md` starts with a status block containing a **Claims** table: one row
per component (colors, decoration, style, plasma, icons, ...) plus a `shared`
row for the project-wide files.

- Before starting, read the Claims table. If the component you need is claimed
  by someone else, stop and ask the user. Don't take over a claim on your own,
  even if it looks stale. The user decides.
- When starting, put your claim in the row:
  `<agent> (<model>), <session or short task>, <date>`.
- Only edit files inside your claimed component. Changes to another component
  (even a one-line fix) need that claim or the user's OK. If you find a
  problem there, write it up as an `AUDIT.md` finding instead of fixing it.
- `shared` covers `AGENTS.md`, `PLAN.md` outside the status block,
  `docs/REFERENCE.md`, `docs/FINDINGS.md`, `tools/`, `dev/`, the install
  scripts, and `.gitignore`. Claim `shared` for any non-trivial edit to those.
  Exceptions that any agent may do without the `shared` claim: its own
  CHANGELOG entry, its own Claims row, and appending a new finding or a new
  verified fact (append only, don't rewrite other agents' text).
- Default is **one agent at a time**. Parallel work on different components is
  allowed only when the user started it (e.g. "Codex on icons, Claude on the
  decoration"), and only on components with disjoint folders.
- Subagents work under their parent's claim and report back to the parent.
  They don't edit `PLAN.md`, `CHANGELOG.md`, or `AUDIT.md`; the parent records
  their results.

### Finishing a session

When finishing or stopping, even partway:

1. Add a dated entry at the top of `CHANGELOG.md` (format below).
2. Update the component status in `PLAN.md` and clear your Claims row
   (`nobody`).
3. If you audited or re-tested anything, update `AUDIT.md` (see Audits).
4. Describe any uncommitted or half-done work in the CHANGELOG entry: which
   files, what state, what's next. The next agent must be able to continue
   without asking you.

### CHANGELOG entries

Newest first. Heading:
`## YYYY-MM-DD, <Agent> (<model>) — <short title>`

Body: what changed (files and why), check results with numbers, what wasn't
verified, what's left and who should pick it up. No marketing tone. Times and
dates in the user's timezone (America/Phoenix).

## Audits

`AUDIT.md` is the shared review log. Any agent may audit any component, but
auditing doesn't give you the right to edit a component you haven't claimed.

- After every audit or re-test, record it in `AUDIT.md` without waiting to be
  asked: date, auditor (agent + model), what was audited (component and git
  commit or "working tree"), findings (or explicitly "none"), checks run with
  results, and the limits of the test (offscreen only, one app tested, not
  seen by the user, etc.).
- Findings get a project-wide running number that never gets reused, a
  severity, and a status:
  - P1: broken (crash, unreadable text, install or uninstall damages the
    user's setup, Apple material in git).
  - P2: clearly wrong against the reference, or a real usability problem.
  - P3: small visual differences, missing polish, docs.
  - Status: open, fixed (commit), verified (by whom), accepted (user decision),
    deferred (user decision).
- A visual finding cites the reference (file in `reference/` plus the value in
  `docs/REFERENCE.md`) and the measured mismatch (e.g. "title bar 2 px taller",
  "#CCCCCC vs #DDDDDD").
- When another agent reports a finding against your work and you verify it,
  fix it in the same session (if you hold the claim). Don't ask "who fixes
  this?". If you disagree, say why in `AUDIT.md` and leave it for the user.
- Keep the status summary at the top of `AUDIT.md` current.

## Fidelity rules

- **The reference is real Mac OS 9.2.2**, default Platinum appearance, default
  highlight and accent colors, at its native 1x pixel size. Not memory, not
  Mac OS 8, not later "Platinum-like" Linux themes. Existing themes (NineIcons,
  Platinum9, Chi-Nata, etc.) may be used to learn from, not as the reference.
- **Measure, don't guess.** Every color and metric in the theme comes from
  `docs/REFERENCE.md`, and every entry there names its source (reference
  screenshot and pixel position, or documented Apple value) and confidence. An
  unmeasured value stays marked `TBD` until measured.
- **The reference VM** (set up by the user 2026-11-19, outside this repo):
  `/mnt/storage1/local/VM/mac-os-9/`, launcher `mac9` (passes extra
  arguments to QEMU), disk `system.qcow2`, install ISO next to it, QEMU 9.1
  "screamer" fork in `screamer/` (mac99, G4, 512 MB, GTK display). The VM
  belongs to the user: don't edit the launcher, disk, or fork, and don't
  start or stop the VM without asking (only one QEMU can use the disk).
- **Captures**: the VM must run with a QMP socket. The user's launch command
  for that is `/mnt/storage1/local/VM/mac-os-9/mac9 -boot c -qmp
  unix:$XDG_RUNTIME_DIR/mac9-qmp.sock,server=on,wait=off`. Then
  `tools/capture.py <name>` saves the guest framebuffer (1x, unscaled, from
  QEMU's own PPM dump, converted to PNG and checked pixel for pixel) as
  `reference/<name>.png` and logs it in `reference/INDEX.tsv`. Never use
  desktop screenshots of the QEMU window: they are scaled.
  `tools/capture.py --check` tests the connection; `--delay` and `--burst`
  (continuous capture, keeps changed frames) are described in
  `docs/CAPTURES.md`. When asking the user to
  set something up in the VM, remind them to release it with Ctrl+Alt+G
  before Alt+Tab: Alt+Tab is typed into the focused field otherwise (stray
  `^`), and the agent can't click in the VM (no absolute pointer device).
- Compare results against the reference with screenshots at the same scale,
  not by eye alone: `tools/compare.py diff` (see `docs/DEVELOPMENT.md`).
  Record the comparison in `AUDIT.md`.
- Pixel art must land on whole pixels. Check at the scale factors the user
  actually uses (see Machine facts), not only at 1x offscreen.
- Where Plasma can't match the reference, pick the closest option, document
  the limit, and move on. Don't fake it with hacks that break on Plasma updates.

## Legal rules (from day one)

- **No Apple material in the repo**: no icons, pixmaps, fonts (Chicago,
  Charcoal, Geneva), sounds, cursors, desktop pictures, or ROM/system files,
  not even "temporarily". Everything shipped is redrawn or generated here, or
  comes from a third party with a license that allows it (license recorded in
  the component's folder).
- Reference screenshots live only in `reference/`, i.e. in the private
  reference repo, never in this one.
- Mac OS install media and ROMs come from the user. Don't download them from
  abandonware sites or other unofficial sources.
- Measured facts (hex colors, pixel sizes, layout) are fine to record and use.
- Use neutral names in anything installable (theme IDs, package names) until
  the user picks a name; "Apple" and "Mac OS" stay out of IDs.

## General rules

- Commit and push only when the user asks. Never create, delete, or change
  GitHub repos or their visibility without asking.
- Commits: small and self-contained, imperative subject with a component
  prefix (`decoration: draw title bar pinstripes`), a body explaining why.
  Every AI-assisted commit ends with a `Co-Authored-By:` trailer naming the
  agent and model, e.g. `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  Other agents use their own name.
- Git identity is set per repo (`orlfman` with the GitHub noreply address).
  Don't change it.
- **Never touch the live desktop without the user's OK**: no installing into
  `~/.local/share` or `/usr`, no `plasma-apply-*`, `kwriteconfig6`,
  `lookandfeeltool`, or restarting plasmashell/KWin in the user's session.
  Test in the sandbox (`dev/`). When the user OKs an install: back up every
  config file first, install user-scope, and make sure `uninstall.sh` gets
  them back exactly to where they were.
- Ask before installing packages or changing system configuration. Commands
  that need root go to the user, to run in the app's Terminal panel.
- Commands handed to the user use absolute paths (their terminal opens in `~`).
- Only officially supported theming hooks. No patched Plasma/KWin, no
  injecting into apps (Discord/Steam client mods are out of scope).
- Keep the user's other work alone: `/mnt/storage1/local/projects/*`
  (windows2000-union, vaulttec-union) and `~/Files/Archive/themes/*` are
  read-only references for this project.

## Checks

These grow as components land; every component's step in `PLAN.md` lists its
own. Always, before finishing:

- `.colors`, `.desktop`, `metadata.json`: parse cleanly
  (`python3 -I -c 'import configparser,json; ...'` or the checker in `tools/`
  once it exists).
- SVGs: `xmllint --noout` clean; Plasma SVG element IDs present (checker in
  `tools/` once it exists).
- C++ (decoration/style): builds with no warnings, run once under ASan/UBSan.
- `git status`: nothing from `reference/` or `dev/build/`, no Apple files.
- Visual: render in the sandbox (`dev/shoot.sh`, `dev/kwin-test.sh`,
  `dev/app-test.sh`), compare with the reference (`tools/compare.py diff`),
  and record the result. A change isn't "done" until the user has seen it on screen, so
  say plainly when they haven't.

## Prior work to reuse

The user's own earlier classic-theme project already solved the testing
problem; read it before writing new tooling, and copy what fits into `dev/`
(it's the user's code; keep its license headers):

- `/mnt/storage1/local/projects/windows2000-union/docs/DEVELOPMENT.md`:
  sandbox (own XDG folders, offscreen and headless nested KWin), screenshot
  scripts, decoration test harness, and a list of what Union 6.8 verifiably
  can and can't draw.
- `/mnt/storage1/local/projects/windows2000-union/docs/FINDINGS.md`:
  research, including Mac OS 9 icon candidates.
- `/mnt/storage1/local/projects/windows2000-union/dev/`,
  `decoration/` (C++ KDecoration), `plasma/make-plasma.py`.

Union facts from there that matter for Platinum (verify again on 6.8.3): Qt
Widgets output draws no `outline`/`box-shadow` (one bevel layer only), scroll
bars get **no arrow buttons**, no dotted lines, `background-image` is stretched
and can crash the Qt Widgets style without `mask`. Platinum needs scroll bar
arrows, which is why the application style is a C++ QStyle (decided
2026-11-20, `PLAN.md`).

## Machine facts

- Plasma 6.8.3, KWin 6.8.3 (Wayland), Qt 6.12.0, union 6.8.3, aurorae 6.8.3,
  kdecoration 6.8.3, breeze 6.8.3 (CachyOS builds, checked 2026-11-19).
- Two 3840×2160 displays at 120 Hz, **both at scale 1** (DP-1 27" Dell
  S2725QS on the left, DP-2 32" S3225QS on the right). The user sometimes
  scales the 32" up to read. The theme draws at true 1x at Plasma 100% (user's
  decision 2026-11-20, may be tweaked after testing): keep metrics in one
  place so a later change is cheap.
- Current look: stock Breeze, fonts SF Pro Text + SF Mono. Terminals:
  Alacritty (default), kitty, Kwi. kmscon on tty3-6.
- The live tests (nested KWin, screenshots) need a working Wayland/DRM
  session. If a sandbox blocks that, report it as a sandbox limit instead of
  changing code or tests.
