# Platinum for Firefox (IE5 Mac layout)

Optional Firefox `userChrome.css` theme inspired by Internet Explorer 5 for Mac
on Mac OS 9.2.2, using the measured Platinum Lavender palette instead of IE's
aqua/teal (see `PLAN.md` decision 14 and `docs/FIREFOX-PLAN.md`).

## Scope and rules

- **Inspired by IE5, not a 1:1 clone:** Platinum colors, bevels, pinstripes,
  focus rings, selection, menus, and tabs follow `docs/REFERENCE.md` on whole
  pixels at 1×; IE5 guides the toolbar/address/favorites/sidebar/status layout.
- **Pure `userChrome.css` + original/MPL-2.0 assets:** loaded through Firefox's
  profile `chrome/userChrome.css` (`toolkit.legacyUserProfileCustomizations.stylesheets`).
  No `userChrome.js`, autoconfig, patched `omni.ja`, or privileged extensions.
- **No Microsoft or Apple artwork:** zero logos, icons, or copied bitmaps from
  Internet Explorer or Mac OS 9.
- **Separate install and full undo:** never touched by the root `install.sh`;
  profile installation and byte-for-byte restoration will live in
  `firefox/install.sh` and `firefox/uninstall.sh` (Milestone 6).

## Sandbox testing

- `dev/firefox-test.sh`: launches Firefox inside a headless nested
  `kwin_wayland --virtual` session with the Platinum window decoration,
  Platinum GTK 3 theme, and a disposable `HOME`/XDG/profile directory under
  `dev/build/` (never touches `~/.mozilla` or `~/.config/mozilla`).
- `dev/check-firefox-m1.sh`: runs the Milestone 1 discovery and verification
  suite (cold normal-path `userChrome.css` loading + negative control, KWin SSD
  join pixel check, 160.0.1 DOM & Shadow DOM inventory, legacy vs revamped
  sidebar, two-row URL bar wrap + button labels + overflow/customize/keyboard
  checks, GTK 3 Platinum inheritance, and theme/dark-mode gating).
