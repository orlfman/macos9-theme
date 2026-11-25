# Platinum for Firefox (IE5 Mac layout)

Optional Firefox `userChrome.css` theme inspired by Internet Explorer 5 for Mac
on Mac OS 9.2.2, using the measured Platinum Lavender palette instead of IE's
aqua/teal (see `PLAN.md` decision 14 and `docs/FIREFOX-PLAN.md`).

**Production-ready on Linux.** Verified with Firefox 160.0.1 using Firefox’s System theme in light, normal-contrast mode, including Private Browsing windows.

## Scope and rules

- **Inspired by IE5, not a 1:1 clone:** Platinum colors, bevels, pinstripes,
  focus rings, selection, menus, and tabs follow `docs/REFERENCE.md` on whole
  pixels at 1×; IE5 guides the toolbar/address/favorites/sidebar/status layout.
- **Pure `userChrome.css` / `userContent.css` + CSS gradients:** loaded through
  Firefox's profile `chrome/userChrome.css` and `chrome/userContent.css`
  (`toolkit.legacyUserProfileCustomizations.stylesheets`). No `userChrome.js`,
  autoconfig, patched `omni.ja`, or privileged extensions.
- **No Microsoft or Apple artwork:** zero logos, icons, or copied bitmaps from
  Internet Explorer or Mac OS 9.
- **Separate install and full undo:** select Firefox-only mode with `--firefox` on either root script;
  profile installation and byte-for-byte restoration live in
  `firefox/install.sh` and `firefox/uninstall.sh`.

## Install and undo

Close Firefox first, then run from the repository root:

```bash
./install.sh --firefox
```

`firefox/install.sh` discovers profiles from both `~/.config/mozilla/firefox/profiles.ini`
(XDG) and `~/.mozilla/firefox/profiles.ini`, prioritizing `[Install*]` `Default=`
over legacy `[Profile*]` `Default=1`, warns if the installed Firefox major
version is outside `firefox/version.json`, lists all discovered profiles, and
asks you to pick one (`--list` shows profiles; `--profile <index|name|path>`
selects non-interactively; `--dry-run` previews without changing anything).

Before modifying anything in the chosen profile, it journals and backs up any
existing `chrome/` directory, `user.js`, and the prior values (or absence) of
its managed prefs (`toolkit.legacyUserProfileCustomizations.stylesheets`,
`browser.tabs.inTitlebar`, `browser.toolbars.bookmarks.visibility`,
`browser.theme.dark-private-windows`, plus classic
16 px square scrollbar prefs `widget.gtk.overlay-scrollbars.enabled`,
`widget.non-native-theme.scrollbar.style`,
`widget.non-native-theme.scrollbar.size.override`, and
`widget.gtk.theme-scrollbar-colors.enabled`) under
`~/.local/state/macos9-theme-firefox/`. It installs `chrome/platinum/`, prepends
one marker-delimited `@import` block to `chrome/userChrome.css` and
`chrome/userContent.css` (keeping any existing `@charset`, `@namespace`, and
user rules intact), and appends one marker-delimited `user_pref` block to
`user.js`.

To switch between horizontal tabs below the Favorites bar (`1A`) and vertical
Platinum sidebar tabs (`1C`) at any time inside Firefox, right-click the toolbar
or tab strip and click **Turn on Vertical Tabs** / **Turn off Vertical Tabs**. Collapse the sidebar for an icon-only strip. The tab icons stay centered in their frames and align with the new-tab button in regular and Private Browsing windows.

To remove the theme and restore your profile (with Firefox closed):

```bash
./uninstall.sh --firefox
```

`firefox/uninstall.sh` restores untouched files byte for byte (including any
pre-existing `chrome/` content and file permissions), preserves any rules or
prefs you added outside the `macos9-theme-firefox` markers, restores each
managed pref's original value or absence directly in `prefs.js`, and refuses
with a conflict message instead of overwriting if markers or files inside
`chrome/platinum/` were edited.

## Known limitations

- **Requires `userChrome.css` support:** Firefox only loads profile stylesheets
  when `toolkit.legacyUserProfileCustomizations.stylesheets = true` (set
  automatically in `user.js` by `firefox/install.sh`). Because Firefox updates
  monthly, run `python3 -I tools/check-firefox-selectors.py` after browser
  upgrades to verify all chrome element IDs and `::part()` hooks still exist.
- **Browser chrome in System light mode:** The browser chrome stylesheet is gated to Firefox's default
  System theme (`default-theme@mozilla.org`) in normal-contrast light mode so
  explicit built-in themes (Compact Light/Dark, Alpenglow), System Dark mode,
  and High Contrast keep their native contrast and legibility. Setting
  `browser.theme.dark-private-windows = false` lets Private Browsing windows
  follow the same System light/dark scheme (rendering Platinum in light mode
  while keeping Firefox's Private mask icon on the tab strip, and restoring the
  prior pref value on undo).
- **Revamped sidebar launcher Shadow DOM:** Firefox 160's `<sidebar-main>` tool
  buttons live inside a Shadow DOM exposing only limited parts/variables, so
  IE5's rotated vertical text tabs cannot be drawn on the revamp launcher icons
  via `userChrome.css` (vertical browser tabs in `#vertical-tabs` and the
  legacy `sidebar.revamp = false` header are light DOM and fully styled).
- **Content scrollbars and form controls:** Firefox 160 removed native GTK
  scrollbar painting (`widget.non-native-theme.enabled`) and restricts anonymous
  scrollbar CSS to privileged UA sheets, so 3D Mac OS 9 scrollbar bevels, grip
  dimples, and arrows cannot be drawn via `userChrome.css`/`userContent.css`.
  The installer pairs Firefox's built-in classic 16 px square non-overlay
  scrollbar prefs (`widget.gtk.overlay-scrollbars.enabled=false`,
  `scrollbar.style=4`, `scrollbar.size.override=16`,
  `theme-scrollbar-colors.enabled=true`) with `chrome/platinum/content.css`
  (`scrollbar-color: #9999FF #CCCCCC;` via `chrome/userContent.css`, gated on
  the page’s preferred light color scheme and normal contrast). A site can
  override the tint with its own `scrollbar-color` declaration. The installer
  applies the preferences and restores all previous
  files and pref values on undo. The scrollbar size/square-shape prefs apply
  profile-wide across Firefox themes, including dark mode.

Light-mode pages use lavender (`#CCCCFF`) with black text for selection by
default. Sites can supply their own selection colors.

In the light System theme, Firefox Settings uses Platinum gray surfaces and
square cards. The open address bar uses a white results panel and lavender
hover and selection colors.

The Firefox menu doubles as the loading indicator. While the selected tab
loads, the menu icon changes to the Firefox logo with moving lavender stripes.
With reduced motion enabled, the stripes stay still. The menu remains clickable.

## Sandbox testing and selector checks

- `tools/check-firefox-selectors.py`: checks every `#id` and `::part()` selector
  in `firefox/chrome/` against the installed Firefox `omni.ja` archives and
  validates `firefox/version.json`.
- `dev/firefox-test.sh`: launches Firefox inside a headless nested
  `kwin_wayland --virtual` session with the Platinum window decoration,
  Platinum GTK 3 theme, and a disposable `HOME`/XDG/profile directory under
  `dev/build/` (never touches `~/.mozilla` or `~/.config/mozilla`).
- Suites: `dev/check-firefox-m1.sh` (46/46 discovery), `dev/render-firefox-m2.sh`
  (mockups), `dev/check-firefox-m3.sh` (36/36 top bands and Go navigation), `dev/check-firefox-m4.sh`
  (34/34 full chrome), `dev/check-firefox-m5.sh` (32 selector/version/scaling/focus and RTL checks),
  and `dev/check-firefox-m6.sh` (throwaway-HOME install/undo, fault recovery, and live cold launch).
