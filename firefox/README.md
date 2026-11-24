# Platinum for Firefox (IE5 Mac layout)

Optional Firefox `userChrome.css` theme inspired by Internet Explorer 5 for Mac
on Mac OS 9.2.2, using the measured Platinum Lavender palette instead of IE's
aqua/teal (see `PLAN.md` decision 14 and `docs/FIREFOX-PLAN.md`).

## Scope and rules

- **Inspired by IE5, not a 1:1 clone:** Platinum colors, bevels, pinstripes,
  focus rings, selection, menus, and tabs follow `docs/REFERENCE.md` on whole
  pixels at 1×; IE5 guides the toolbar/address/favorites/sidebar/status layout.
- **Pure `userChrome.css` + CSS gradients:** loaded through Firefox's profile
  `chrome/userChrome.css` (`toolkit.legacyUserProfileCustomizations.stylesheets`).
  No `userChrome.js`, autoconfig, patched `omni.ja`, or privileged extensions.
- **No Microsoft or Apple artwork:** zero logos, icons, or copied bitmaps from
  Internet Explorer or Mac OS 9.
- **Separate install and full undo:** never touched by the root `./install.sh`;
  profile installation and byte-for-byte restoration live in
  `firefox/install.sh` and `firefox/uninstall.sh`.

## Install and undo

Close Firefox first, then run from the repository root:

```bash
./firefox/install.sh
```

`firefox/install.sh` discovers profiles from both `~/.config/mozilla/firefox/profiles.ini`
(XDG) and `~/.mozilla/firefox/profiles.ini`, prioritizing `[Install*]` `Default=`
over legacy `[Profile*]` `Default=1`, warns if the installed Firefox major
version is outside `firefox/version.json`, lists all discovered profiles, and
asks you to pick one (`--list` shows profiles; `--profile <index|name|path>`
selects non-interactively; `--dry-run` previews without changing anything).

Before modifying anything in the chosen profile, it journals and backs up any
existing `chrome/` directory, `user.js`, and the prior values (or absence) of
its three managed prefs (`toolkit.legacyUserProfileCustomizations.stylesheets`,
`browser.tabs.inTitlebar`, and `browser.toolbars.bookmarks.visibility`) under
`~/.local/state/macos9-theme-firefox/`. It installs `chrome/platinum/`, prepends
one marker-delimited `@import` block to `chrome/userChrome.css` (keeping any
existing `@charset`, `@namespace`, and user rules intact), and appends one
marker-delimited `user_pref` block to `user.js`.

To switch between horizontal tabs below the Favorites bar (`1A`) and vertical
Platinum sidebar tabs (`1C`) at any time inside Firefox, right-click the toolbar
or tab strip and click **Turn on Vertical Tabs** / **Turn off Vertical Tabs**.

To remove the theme and restore your profile (with Firefox closed):

```bash
./firefox/uninstall.sh
```

`firefox/uninstall.sh` restores untouched files byte for byte (including any
pre-existing `chrome/` content and file permissions), preserves any rules or
prefs you added outside the `macos9-theme-firefox` markers, restores each
managed pref's original value or absence directly in `prefs.js`, and refuses
with a conflict message instead of overwriting if markers or files inside
`chrome/platinum/` were edited.

## Sandbox testing and selector checks

- `tools/check-firefox-selectors.py`: checks every `#id` and `::part()` selector
  in `firefox/chrome/` against the installed Firefox `omni.ja` archives and
  validates `firefox/version.json`.
- `dev/firefox-test.sh`: launches Firefox inside a headless nested
  `kwin_wayland --virtual` session with the Platinum window decoration,
  Platinum GTK 3 theme, and a disposable `HOME`/XDG/profile directory under
  `dev/build/` (never touches `~/.mozilla` or `~/.config/mozilla`).
- Suites: `dev/check-firefox-m1.sh` (46/46 discovery), `dev/render-firefox-m2.sh`
  (mockups), `dev/check-firefox-m3.sh` (34/34 top bands), `dev/check-firefox-m4.sh`
  (34/34 full chrome), `dev/check-firefox-m5.sh` (29/29 selector/version/scaling/focus),
  and `dev/check-firefox-m6.sh` (40/40 throwaway-HOME install/undo + live cold launch).
