# WhiteSur Lavender

Builds the Platinum Lavender folder variant (`WhiteSur-lavender`,
`WhiteSur-lavender-light`, and `WhiteSur-lavender-dark`) plus the tracked
`icons/custom/` override layer from upstream
[WhiteSur](https://github.com/vinceliuice/WhiteSur-icon-theme) without
modifying any upstream checkout or touching the live desktop.

## Pinned upstream revision

All reviewed pin metadata and SHA-256 digests live in `icons/whitesur-pin.json`:

- Release: `2026-09-10`
- Reviewed full commit: `73d8040da51a9ed74e47c7366e7e9ff437601a5c`
- Upstream files stay outside this repository.

## Automatic WhiteSur caching in `install.sh`

When `install.sh` builds WhiteSur Lavender:

1. If `M9_WHITESUR_UPSTREAM` is set, it uses that local checkout read-only
   (requiring it to be at the exact reviewed commit).
2. Otherwise, it uses a bare git cache at
   `${XDG_CACHE_HOME:-$HOME/.cache}/macos9-theme/WhiteSur-icon-theme` via
   `icons/fetch-whitesur.sh`.
   - If the cache does not exist yet, it fetches **only** the exact reviewed
     commit from `https://github.com/vinceliuice/WhiteSur-icon-theme.git` into
     a private temporary bare repo (`core.hooksPath=/dev/null`,
     `core.symlinks=false`), verifies `FETCH_HEAD`, runs `git fsck`, and moves
     it atomically into place. `build-whitesur-lavender.sh` then verifies all
     pinned digests before running any upstream code.
   - Once cached, subsequent runs work completely offline.
   - Corrupt caches, symlinked caches, caches at the wrong commit, offline
     misses, and interrupted downloads all fail with a clear error and leave
     the installed theme untouched.
   - `install.sh --dry-run` never downloads or writes anything.

## Prerequisites (Arch Linux)

Both `icons/build-whitesur-lavender.sh` and `install.sh` preflight all required
tools before taking locks, fetching, or writing files, and name any missing Arch
package:

- `git` (`git`)
- `python3` ≥ 3.11 (`python`)
- `tar` (`tar`)
- `flock` (`util-linux`, required by `icons/fetch-whitesur.sh`, `install.sh`, and `uninstall.sh`)
- `xmllint` (`libxml2`)
- `rsvg-convert` (`librsvg`)
- `gtk-update-icon-cache` (`gtk-update-icon-cache`)
- Python `gi` (`python-gobject`) and GTK 3 GI typelib (`gtk3`)
- `PIL` (`python-pillow`, only required when `icons/custom/` contains `.png` icons)
- `kreadconfig6` / `kwriteconfig6` (`kconfig`, required by `install.sh` and `uninstall.sh`)

## Standalone build

Build into the ignored `dev/build/icons/` folder:

```bash
/home/pieman/Files/Archive/projects/macos9-theme/icons/build-whitesur-lavender.sh
```

You may pass an explicit `[UPSTREAM_CLONE]` and `[OUTPUT_DIR]`. When running
from an extracted source archive (without `.git`), both the default
`dev/build/icons/` output and any explicit external `[OUTPUT_DIR]` work cleanly
while still refusing to write into source directories, `reference/`, or the
upstream checkout (primary and linked Git worktrees both enforce full Git
ignore/untracked safeguards). The builder exports the pinned commit into a
private staging directory, runs upstream's installer with a minimal explicit
environment (`env -i`, private `HOME`/`XDG_*`/`TMPDIR`, fixed `PATH`, no
display or session bus) and `-p` (KDE Plasma launcher), applies validated
`icons/custom/{all,light,dark}/` overrides (materializing cross-directory
variant aliases automatically), rebuilds icon caches, verifies all three themes
together, and publishes under a destination lock with a durable recovery
journal (`.whitesur-lavender-publish.json`). Note: during standalone
replacement of an existing output directory, the three theme directories are
switched by sequential `rename()` calls, so concurrent readers inspecting the
output directory directly can briefly see a partial trio during the switch;
if interrupted mid-switch, the next `--publish` (or `--recover-dest`) rolls
back cleanly to the prior complete trio before removing staging.

## Tracked custom icon layer (`icons/custom/`)

Place custom icons, replacements, and relative symlink aliases under
`icons/custom/{all,light,dark}/` mirroring WhiteSur's icon theme directories
(e.g. `apps/scalable/`, `places/scalable/`, `places/16/`, `actions/16/`,
`status/22/`).

- `icons/custom/all/` applies to all three themes (`WhiteSur-lavender`,
  `-light`, `-dark`).
- `icons/custom/light/` applies only to `WhiteSur-lavender-light` (overrides
  `all/`).
- `icons/custom/dark/` applies only to `WhiteSur-lavender-dark` (overrides
  `all/`).

See `icons/custom/README.md` for full step-by-step instructions on adding,
replacing, aliasing, and removing icons, plus the pre-install validation rules.

### Why full-copy + custom layer (instead of a small overlay)

We evaluated installing pinned upstream WhiteSur once and shipping thin
`WhiteSur-lavender{,-light,-dark}` overlays inheriting it, testing both GTK3
(`Gtk.IconTheme`) and KDE (`KIconLoader`). The small overlay fails four
requirements:

1. **Size vs. theme precedence (GTK3 & KDE):** Under the Freedesktop Icon Theme
   Spec, a theme's own `places/scalable/folder.svg` matches `folder` at 16, 22,
   and 24 px before descending into `Inherits=WhiteSur`, replacing 19 monochrome
   16 px icons (and 15 at 22/24 px) with scaled 64 px color folders.
2. **KDE generic-name prefix fallback:** `KIconLoader` strips hyphenated
   suffixes within the active theme before checking `Inherits=`, so
   `folder-blue@64` resolved to `WhiteSur-lavender/places/scalable/folder.svg`
   instead of `WhiteSur/places/scalable/folder-blue.svg`.
3. **Dark-variant inheritance conflict:** `Inherits=WhiteSur-lavender,WhiteSur-dark`
   resolves dark icons to light `WhiteSur` (depth-first), while
   `Inherits=WhiteSur-dark,WhiteSur-lavender` resolves `folder@64` to blue
   `WhiteSur-dark`.
4. **Picker clutter and undo collision:** Installing upstream `WhiteSur*`
   themes adds 3 extra themes to Plasma's picker and collides with any existing
   manual `WhiteSur` theme during adoption/undo.

Keeping the full-copy build with the tracked `icons/custom/` layer (and O(N)
manifest checksums in `scripts/manifest_ops.py`) resolves every size, alias,
and variant identically in GTK3 and KDE with clean undo.

## Testing (disposable output only)

Run the full builder, custom-layer, auto-fetch, fault-injection, and
update-review test suite using only disposable temporary directories (never
writes to `dev/build/icons/`, `~/.local/share/icons`, or `../WhiteSur-icon-theme`):

```bash
/home/pieman/Files/Archive/projects/macos9-theme/dev/test_icons_phase1.py
```

## Updating to a new upstream WhiteSur release

To review a new upstream tag or commit safely (never executes the candidate
`install.sh`, never modifies `icons/whitesur-pin.json`, and never modifies the
upstream clone):

```bash
/home/pieman/Files/Archive/projects/macos9-theme/icons/review-whitesur-update.sh <TAG_OR_COMMIT>
```

You may pass an explicit `[UPSTREAM_CLONE]` and `[PROPOSED_PIN_OUT]` (default:
ignored `dev/build/whitesur-pin-proposed.json`). The report covers `install.sh`
(unified diff + patch-anchor + `bash -n`), the 25 `colors/color-purple/`
inputs, launcher files, `COPYING`/`AUTHORS`, symlinks (blocking on absolute or
escaping links), SVG namespace exceptions, and **every custom override in
`icons/custom/`** (flagging when upstream changed, added, or removed an
overridden icon or broke a custom alias target).

Only after reviewing the report and
`diff -u icons/whitesur-pin.json dev/build/whitesur-pin-proposed.json` should
you copy the reviewed pin into `icons/whitesur-pin.json` and re-run the test
suite.

## Palette and patches

- **Folder recolor** (25 SVGs derived from `colors/color-purple/` using the
  Mac OS 9.2.2 Finder folder measurements in `docs/REFERENCE.md`):
  - `#f299ff` → `#DDDDFE` (lit bevel)
  - `#e791f3` → `#B5B4F9` (front face)
  - `#c75cd6` → `#7E7DD9` (dark rim)
- **Launcher (`start-here-kde-plasma`)**: built with upstream's `-p`
  (`--kde-plasma`) option for `places/{16,22,24,scalable}/` and a derived 32 px
  KDE Plasma `status/32/start-here.svg` from upstream's
  `plasma/places/24/start-here.svg`, so panel sizes (16–64 px) resolve to KDE
  Plasma artwork rather than the Apple logo.
- **SVG namespaces**: normalizes the 64 pinned upstream `src/` SVGs that omit
  `xmlns="http://www.w3.org/2000/svg"` in the disposable export.

## Licensing

- **Scripts in `icons/`** (`whitesur-lavender.py`, `build-whitesur-lavender.sh`,
  `review-whitesur-update.sh`, `fetch-whitesur.sh`): `BSD-2-Clause`.
- **Derived WhiteSur Lavender icon artwork**: GNU General Public License v3
  only (`GPL-3.0-only`), as evidenced by upstream `COPYING` (GNU GPL v3) and
  `AUTHORS` (Vince Liuice) in commit `73d8040da51a9ed74e47c7366e7e9ff437601a5c`;
  no later-version grant is evidenced for the upstream assets.
- Each built theme directory includes verbatim upstream `COPYING`, `AUTHORS`,
  and a dated `LAVENDER-NOTICE.txt` describing the source revision and
  modifications.
