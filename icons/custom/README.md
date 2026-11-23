# Custom Icon Layer (`icons/custom/`)

Tracked custom icons and overrides applied on top of WhiteSur Lavender during
every build (`icons/build-whitesur-lavender.sh` and `install.sh`). Custom icons
override both upstream WhiteSur icons and Lavender-recolored folders, support
brand-new icon names and relative symlink aliases, and survive rebuilds and
upstream WhiteSur updates.

## Directory layout and precedence

Mirror standard icon theme paths (`<context>/<size>/<name>.svg` or `.png`, where
`<context>/<size>` is a directory listed in WhiteSur's `index.theme`, such as
`apps/scalable`, `places/scalable`, `places/16`, `actions/16`, `status/22`,
`mimes/scalable`, `devices/scalable`):

- `icons/custom/all/` — applied to **all three** themes (`WhiteSur-lavender`,
  `WhiteSur-lavender-light`, and `WhiteSur-lavender-dark`).
- `icons/custom/light/` — applied **only** to `WhiteSur-lavender-light`
  (overrides `all/` for `-light`).
- `icons/custom/dark/` — applied **only** to `WhiteSur-lavender-dark`
  (overrides `all/` for `-dark`).

Variant-only overrides in `light/` and `dark/` automatically materialize
symlinked directories inside the target variant so they never bleed into the
base `WhiteSur-lavender` theme. Do not create `@2x` directories here: `@2x`
symlinks in each built theme automatically pick up icons from the base context
directory.

## How to add a brand-new icon or alias

1. Save your SVG (or PNG) at the mirrored path, for example:
   - `icons/custom/all/apps/scalable/my-app.svg`
2. To add an alias pointing to a custom or upstream icon, create a **relative**
   symlink in the matching directory, for example:
   ```bash
   ln -s my-app.svg icons/custom/all/apps/scalable/my-app-alt.svg
   ```
3. Rebuild or reinstall (`icons/build-whitesur-lavender.sh` or `install.sh`).
   The builder validates the file, regenerates `icon-theme.cache`, and verifies
   that GTK resolves the new icon and alias.

## How to replace an upstream or Lavender icon

1. Find the icon's path in the built theme (for example
   `places/scalable/folder.svg` or `apps/scalable/firefox.svg`).
   - Note: some icons also exist in fixed monochrome sizes (`places/16/`,
     `places/22/`, `places/24/`, `actions/16/`). Replace those too if you want
     panel/list views at 16–24 px to change as well.
2. Place your replacement at the exact same relative path under
   `icons/custom/all/` (or `light/` / `dark/` for variant-only replacements).
3. Rebuild or reinstall. When reviewing a future WhiteSur release with
   `icons/review-whitesur-update.sh`, the report explicitly flags any upstream
   icon that changed underneath one of your overrides.

## How to remove a custom icon

1. Delete the file or alias from `icons/custom/{all,light,dark}/` (and remove
   any now-empty subdirectories you created, keeping `.gitkeep` at each layer
   root).
2. Re-run `icons/build-whitesur-lavender.sh` or `install.sh`. The original
   Lavender or upstream WhiteSur icon is automatically restored on rebuild.

## Validation rules (enforced before install)

Every custom entry is validated before any theme is published or installed:

- Only regular `.svg` and `.png` files and relative file symlinks are allowed
  (no dotfiles other than layer-root `.gitkeep`, no directory symlinks, no
  reserved root files like `index.theme` or `COPYING`, no paths outside
  directories listed in `index.theme`).
- Every `.svg` must be valid UTF-8 XML with root `{http://www.w3.org/2000/svg}svg`,
  pass `xmllint --nonet --noout`, and render cleanly via `rsvg-convert`.
- Every `.png` must verify and decode cleanly via Pillow.
- Every alias symlink must be relative, remain inside the theme root, and
  resolve to an existing icon in the built theme (zero broken links).
- Keep Apple artwork out of this repository (see `AGENTS.md` "Legal rules").
