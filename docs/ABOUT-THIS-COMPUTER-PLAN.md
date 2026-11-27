# Plan: About This Computer

Written 2026-11-26 by Claude Code (Opus 5.5) at the user's request. Design
only: nothing built yet, no claim taken. The user prefers this and the
Control Strip over a fake window shade (KWin removed shading on Wayland in
2025; a script could only imitate it).

## Goal

A small app that recreates Mac OS 9.2.2's **About This Computer** window
for any Linux distribution running the theme: the banner, the memory
summary and the list of running applications with memory bars, drawn by
the Platinum style and decoration. Opened from the Apple-menu stand-in,
as its first item, like on OS 9.

Reference: `reference/dialog-about-this-computer.png` (1440×1050, window at
about x 178–656, y 292–571; measure properly first, see Order of work).

## User decisions (2026-11-26)

1. **Banner = Tux plus the distribution's name.** The name is read from the
   system, so it works on any distro, not only CachyOS. The logo is always
   a regular Tux the penguin, since every distro runs the Linux kernel
   (changed the same day from per-distro logos: simpler, and no logo
   lookup). No Mac OS logo, no "Mac OS" wordmark, no Apple copyright line
   (AGENTS.md legal rules).
2. **Memory bars show each app's share of total RAM.** OS 9's bars showed
   use of a fixed per-app partition, which Linux doesn't have.

## What the window shows

| Mac OS 9.2.2 | This app | Source |
| --- | --- | --- |
| Banner: Mac OS logo + "Mac OS 9.2" | Tux + banner name (below) | Bundled Tux image; name from `/etc/os-release` (`/usr/lib/os-release` fallback) via `KOSRelease` (KF6 CoreAddons, already a theme dependency) |
| Version: Mac OS 9.2.2 | `PRETTY_NAME` | os-release |
| Built-in Memory: 512 MB | Total RAM | `MemTotal` in `/proc/meminfo` |
| Virtual Memory: 513 MB used on Mac OS | Swap total and where it lives (below) | `/proc/swaps` |
| Largest Unused Block: 479.7 MB | Available memory | `MemAvailable` in `/proc/meminfo` |
| Mac OS ROM 9.2.1 (right column, top) | `Linux <kernel release>` | `uname()` |
| ™ & © Apple Computer, Inc. (right column, bottom) | `KDE Plasma <version>` | `X-KDE-PluginInfo-Version` in `plasma.desktop` under `$XDG_DATA_DIRS/wayland-sessions` or `xsessions` (upstream file, so every distro has it; 6.8.3 here); fall back to `plasmashell --version` |
| App list: icon, name, size, bar | Running apps plus one system row (below) | cgroups and `/proc/<pid>/smaps_rollup` |

Sizes: MB with one decimal below 1 GB, GB with one decimal above, as OS 9
printed them. Refresh every 2 s, as the original updated live.

### Banner name

`NAME` plus `VERSION_ID` when the version is a release number, so
"Fedora Linux 43", "Ubuntu 26.04", "Debian GNU/Linux 13", "Arch Linux",
"CachyOS Linux". Leave the version out when `BUILD_ID=rolling` or
`VERSION_ID` is a date stamp (openSUSE Tumbleweed's `20261120`). Shrink or
horizontally condense the text to fit the banner rather than wrap.

### Tux

A regular Tux the penguin, bundled with the app (distros don't reliably
ship one), drawn at the size of OS 9's logo square (measure). Use Larry
Ewing's original Tux or a faithful SVG of it: its terms allow use and
modification with credit to Larry Ewing and The GIMP. Record the source
and that credit in the component folder and README credits. **Downloaded
2026-11-26** at the user's request: `apps/about-this-computer/tux/sit3-shine.7.gif`
(327×360 GIF with transparency, the Internet Archive copy since the
original page is gone), with source, checksum and terms in `CREDITS.md`
there. The README credit is still to add. The os-release `LOGO` key is
not used.

### Virtual Memory line

One device: `16 GB on nvme2n1p2`, `8 GB swap file`, or `62 GB compressed
(zram)`. Several: the total and the count (`78 GB on 2 devices`), with the
breakdown in a tooltip. None: `Off`. (This machine has zram 62 GB plus a
16 GB partition.)

### App list and memory

- **Grouping.** On systemd systems Plasma starts each app in its own
  cgroup under `user@<uid>.service/app.slice`: `app-<id>@<uuid>.service`
  or `app-<id>-<pid>.scope` (seen here for Dolphin, Firefox, Claude,
  Chromium). Unescape `\x2d`, drop the `@…`/`-<pid>` suffix, and merge
  entries with the same id. Recognise `app-flatpak-<id>-<n>.scope` and
  Ubuntu's `snap.<snap>.<app>-<uuid>.scope`. Skip `@autostart` services,
  D-Bus activated slices (`app-dbus…`) and ids with no visible desktop
  file, so the list shows apps the user opened, like OS 9's.
- **Measure.** Sum PSS (`Pss:` in `/proc/<pid>/smaps_rollup`) over the
  group's `cgroup.procs`, recursively. Not `memory.current`, which counts
  page cache: for Firefox here it read 2.47 GiB against 1.9 GiB PSS (2026-11-26).
  The user's own processes are readable without root.
- **Name and icon** from `<id>.desktop` in `$XDG_DATA_DIRS/applications`
  (which includes Flatpak's export directories): `Name` and `Icon`.
- **System row.** One row named after the distro (`PRETTY_NAME`) with a
  small Tux, like OS 9's "Mac OS" row: `MemTotal − MemAvailable − Σ apps`,
  clamped at 0.
- **Order.** Alphabetical, system row included, as in the capture.
- **Bars.** Share of `MemTotal` (decision 2). On a 64 GB machine most bars
  will be short (Firefox at 1.9 GB is about 3%), so give any non-zero value
  at least one filled pixel.
- **Without per-app cgroups** (non-systemd distros such as Artix, Void,
  Gentoo with OpenRC, Alpine): group the user's processes by their
  top-level ancestor in the session and match `/proc/<pid>/exe` to a
  desktop file's `Exec`. Coarser, but the window still works. Apps started
  from a terminal count under the terminal on every system.

## Implementation

- C++ Qt 6 Widgets app, so it picks up the Platinum QStyle and KWin
  decoration on its own. Dependencies stay within what the theme already
  needs: Qt 6 (Widgets, DBus), KF6 CoreAddons, and CMake from #318.
- Keep the data layer (os-release, meminfo, swaps, cgroup walking, PSS,
  desktop file lookup) in plain functions that take a root directory, so
  tests run on fixture trees.
- One window per session: a second launch raises the existing window
  (unique D-Bus name through Qt DBus).
- Window title "About This Computer". Fixed width, resizable height for the
  list, as OS 9's window had a grow box.
- Banner font: OS 9 used a condensed light serif that can't ship. Use the
  system serif condensed to fit, unless the user picks a bundled font with
  an open license.
- Folder: `apps/about-this-computer/` (new component, own Claims row when
  work starts).

## Install and integration

- `install.sh` builds it with the other compiled parts, installs it
  user-scope with the theme's other files and a `.desktop` entry in
  `~/.local/share/applications`; `uninstall.sh` removes both.
- `--apply` adds it as the first entry in the Apple-menu stand-in (Kicker).
  That edits `plasma/layout.js`, so it needs the `plasma` claim, currently
  Codex's for the global menu.
- The preflight and README follow from #318; nothing new beyond CMake.

## Names for the user to pick (AGENTS.md)

The window title "About This Computer" is OS 9's generic wording. The
executable and desktop file id need the user's choice; the theme's other
IDs suggest `platinum-about` / `platinum.about`.

## Order of work

1. **Measure** the reference into `docs/REFERENCE.md`: window and banner
   size, logo square, label and value columns, line spacing, list row
   height, bar size and colors, fonts.
2. **Data layer and tests**: os-release samples (Arch, CachyOS, Fedora,
   Debian, Ubuntu, openSUSE Tumbleweed, NixOS, Alpine; missing `LOGO`;
   quoted and escaped values), `/proc/swaps` (zram, partition, file, none),
   cgroup names (service, scope, flatpak, snap, escapes, autostart and D-Bus
   skipped), PSS sums and the system row on a fixture `/proc`.
3. **Window**: render offscreen in the sandbox with the Platinum style,
   compare with the reference (`tools/compare.py diff`), record in AUDIT.
4. **Install and uninstall**, with `dev/test-install.sh` coverage.
5. **Apple-menu entry** (needs the `plasma` claim).
6. **Audit and the user's on-screen review.**

## Open questions

- Executable and desktop file names (above).
- Banner font: system serif or a bundled open-license font.
