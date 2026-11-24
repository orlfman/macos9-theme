# Platinum for Firefox (IE5 Mac layout)

Plan for PLAN.md decision 14: an optional Firefox theme that gives Firefox a
Mac OS 9 Platinum look and feel, using Internet Explorer 5 for Mac as the
layout inspiration, with IE's teal replaced by Platinum Lavender. Written 2026-11-23 by Antigravity (Claude Opus 5.5); updated 2026-11-24 after
Milestone 1 (`dev/firefox-test.sh`, `dev/check-firefox-m1.sh`, **46/46 PASS**,
recorded in `docs/FINDINGS.md`).

## Fidelity target (user, 2026-11-23)

**Inspired by IE5, not a 1:1 clone.** Go as far as `userChrome.css` allows.
That changes the rules for this component only:

- **Platinum is exact, IE5 is a guide.** Colors, bevels, pinstripes, focus
  rings, selection, menus and tabs use measured values from
  docs/REFERENCE.md and the IE5 measurements below, landing on whole pixels at
  1×. Layout, proportions and the order of the bars follow IE5 loosely.
- **No pixel comparison against IE5 crops.** Firefox's DOM, fonts and
  features differ; acceptance is crisp 1× rendering, palette-only colors, no
  broken Firefox features, and the user's on-screen approval.
- **Firefox features win.** Where IE5 has no equivalent (tabs, extensions
  button, permission icons, app menu, downloads, sync), give it a Platinum
  treatment instead of hiding it.
- **Further IE5 captures are optional**, nice to have for a detail, never a
  blocker.

## Target and scope

- Host Firefox observed 2026-11-23: `/usr/bin/firefox`, **160.0.1** (Arch
  package, `omni.ja` in `/usr/lib/firefox/browser/`). Firefox ships monthly,
  so every selector this theme uses must be re-checked on each update
  (milestone 5).
- Technique: a profile `chrome/userChrome.css` plus assets, enabled by
  `toolkit.legacyUserProfileCustomizations.stylesheets`. The user approved this
  as the only exception to the supported-hooks rule (decision 14, AGENTS.md).
  No `userChrome.js`, no autoconfig, no patched `omni.ja`, no extension that
  injects into the chrome.
- Layout from top to bottom, matching `reference/ie5-window-blank.png`:
  KWin's Platinum title bar (our decoration, no change), button toolbar with
  icons and labels, Lavender address band, favorites (bookmarks) bar, content
  with an optional Explorer-bar tab strip on the left, and a status band at
  the bottom. Tabs get a slim Platinum design, because IE5 had none.
- No Microsoft material: no IE logo, no IE toolbar icons, no IE wording in
  IDs. The IE "e" spot becomes a neutral activity indicator. Icons are either
  Firefox's own MPL-2.0 icons recolored through `context-fill` or original
  drawings made here (license recorded in `firefox/README.md`).
- Separate from the main install: own `firefox/install.sh` and
  `firefox/uninstall.sh`, run only on request, with full undo. The global
  `install.sh` never touches a Firefox profile.
- Fonts stay the project's (SF Pro Text, PLAN.md). IE's Charcoal/Geneva look
  is out of scope.
- Native Firefox only. Flatpak/Snap and forks (LibreWolf, Zen, Floorp) are
  recorded as untested.

## Measured from the native IE5 capture

All values from `reference/ie5-window-blank.png` (native 1920×1080, 1×; IE5
window outer frame x=628–1613, y=163–816), used as layout/proportion guides
rather than a pixel-comparison target. Coordinates are reference pixels.

| Element | Rows / columns | Pixels |
|---|---|---|
| Window frame and title bar | x=628–633, y=163–184 | identical to the Platinum decoration already in REFERENCE.md (black, white, `#CCCCCC` ×2, `#999999`, black; pinstripes `#FFFFFF`/`#777777`) |
| Button toolbar | y=185–226 (42 rows) | row 185 `#FFFFFF`; rows 186–225 a 3-row horizontal pinstripe `#DEDEDE`, `#CCCCCC`, `#E8E6E8` (starts `#DEDEDE` at 186); row 226 `#ADADAD` |
| Toolbar buttons | centers x≈673, 729, 785, 841, 897 (56 px pitch); icons ≈ y=190–210; labels ≈ y=212–222 | no button frame at rest; enabled label `#111111`, disabled label `#777777`; enabled icon dark teal (`#0D7584`–`#168A9E`), disabled icon washed out (`#B5D1D6`, `#9FBCC1`) |
| Toolbar separator | x=931, y=190–219 | dotted: one `#107C8D` pixel every 3rd row on the pinstripe |
| Address band | y=227–252 (26 rows) | vertical teal tube, top to bottom `#15474D #1A565C #1F6268 #236A74 #277781 #2C838E #308F9B #339AA6 #37A5B2 #3CB2C0 #3EBACA #3DB8C6 #3DB8C6 #3DB8C6 #3EBACA #3BB1BF #36A4B1 #3399A6 #308F9A #2C838E #277580 #226A73 #1E6167 #1A575D #144248`, then `#010B0C` |
| Address label | x=634–701 | white text on the tube; the label block ends in a `#0A8593` column and a black column at x=701–702 |
| Address field | x=702–1557, y=230–249 | 1 px black frame, white inside (18 rows) |
| "go" button | x=1558–1606 | `#56D1DF` left highlight column, tube fill, dark chevron, white label |
| Favorites bar | y=253–276 (24 rows) | row 253 `#FFFFFF`, pinstripe as the toolbar, row 276 `#ADADAD`; label text `#111111` |
| Content top | y=277 | 1 px black line |
| Explorer-bar tab strip | x=634–654 (21 px) | columns `#FFFFFF`, `#EFEFEF`, fill, `#ADADAD`, then black at x=655; fill carries the horizontal pinstripe; rotated labels, diagonal `#515151` dividers; teal collapse arrow at y=283–294 |
| Status band | y=796–809 | black at 795, pinstripe, `#ADADAD` at 809, then the decoration's frame |
| Size grip | x≈1593–1606, y≈797–809 | diagonal `#777777`/`#FFFFFF` lines on `#CCCCCC` |

These are guides for proportions and Platinum detail. The teal must be
replaced, not copied. Measured Platinum Lavender ramps that
can stand in (REFERENCE.md): progress tube `#333399 #6666CC #9999FF #CCCCFF
#EEEEEE …`, menu highlight `#6666CC`/`#333399`/`#000088`, scroll box
`#CCCCFF`/`#9999FF`/`#6666CC`, grip `#333399`. Which ramp the 25-row address
tube uses is a user decision (open question 2), made from rendered mockups.

## Optional captures

Not required (see fidelity target). Useful if a detail is unclear, through
`tools/capture.py` with the VM's QMP socket (docs/CAPTURES.md):

- `ie5-toolbar-hover.png`, `ie5-toolbar-pressed.png` (`--delay`): a toolbar
  button under the pointer and held down.
- `ie5-address-focused.png`, `ie5-address-typed.png`: focus ring and text
  selection in the address field; the autocomplete list if IE shows one.
- `ie5-explorer-favorites.png`, `ie5-explorer-history.png`: Explorer bar open,
  with its tab selected and the splitter.
- `ie5-window-inactive.png`: the same window in the background.
- `ie5-status-loading.png`: status band text and the activity indicator while a
  page loads (any local or offline page).
- `ie5-favorites-menu.png`, `ie5-favorites-folder.png`: the Favorites menu and
  a folder on the favorites bar.
- `ie5-toolbar-text-only.png` / `-icons-only.png` if IE's preferences offer
  them (decides how the label-less mode looks).

## Milestones

1. **Discovery and harness.** Claim firefox and shared. Add a sandboxed
   launcher (`dev/firefox-test.sh`) built on `dev/app-test.sh`: nested
   `kwin_wayland --virtual`, Platinum decoration, a fresh profile under
   `dev/build/firefox-profile` started with `--no-remote --profile`, and a
   `user.js` that enables the stylesheet pref, turns off tabs-in-titlebar
   (`browser.tabs.inTitlebar=0`, so KWin draws the title bar), and removes
   first-run pages, telemetry and remote content for repeatable shots. Then:
   - Prove a marker `userChrome.css` loads through the normal profile path.
   - Inventory the 160.0.1 chrome DOM from `omni.ja` and the live window:
     `#navigator-toolbox`, `#TabsToolbar`, `#nav-bar`, `#urlbar-container`,
     `#PersonalToolbar`, `#sidebar-box`, `#sidebar-main`, `#statuspanel`,
     panels and menupopups. Record which parts are light DOM and which are
     shadow DOM (`<sidebar-main>` is a shadow-DOM custom element that exposes
     only `part="overflow-button"` and CSS variables; its launcher icons can't
     get IE's rotated text tabs; restyle what it exposes). Check whether the legacy sidebar
     (`sidebar.revamp=false`) still exists and is fully stylable.
   - Check that the urlbar can wrap onto its own row (flex-wrap on
     `#nav-bar-customization-target`) and that labels can be shown under icons
     (`.toolbarbutton-text`) without breaking overflow, customize mode or
     keyboard navigation.
   - Check the join between the decoration's bottom line and the toolbox top
     (no doubled or missing black line), and how much of Firefox already
     follows the new GTK Platinum theme (menus, scroll bars, form controls) so
     userChrome only covers what GTK doesn't.
   - Check behavior with the default, light, dark and alpenglow themes and
     `prefers-color-scheme: dark`; decide whether the stylesheet applies only
     under the default system theme.
   Record results in docs/FINDINGS.md.
2. **Mockups.** Render the toolbar, address band and tab options in the
   sandbox and show them to the user to settle open questions 1, 2, 4 and 5.
   Optional IE5 captures only if a detail needs one.
3. **Vertical slice: the three top bands.** Toolbar, Lavender address band and
   favorites bar at 1×. Pinstripes, highlight and shadow rows, black lines and
   the address tube use the measured colors on whole pixels (checked by pixel
   sampling in sandbox screenshots, not against IE5 crops). Buttons show icon
   plus label at the 56 px pitch; enabled, disabled, hover and pressed states.
   Address field with a Platinum focus ring (`#6666CC`, 2 px, as the Mac text
   field) and `#CCCCFF` selection. Generated pinstripe assets or
   `repeating-linear-gradient` at whole pixels, whichever stays crisp.
4. **Extend coverage in small batches.** Slim Platinum tabs (placement per
   open question 1; colors and bevels from REFERENCE.md's tab rows: normal
   `#CCCCCC`, current `#EEEEEE`, pressed `#666666` with white label), the
   activity indicator (`:has()` on a busy selected tab, if milestone 1 shows
   it works), Explorer-bar strip, status band (permanent band or styled
   `#statuspanel`, open question 5), urlbar results popup, menus and panels
   (Platinum menu rows from REFERENCE.md), find bar, notification bars,
   downloads panel, inactive windows (`:-moz-window-inactive`), private
   windows, popup windows without toolbars, fullscreen, customize mode.
5. **Robustness.** A selector check script that extracts element IDs from the
   installed `omni.ja` and fails when a selector the theme relies on is gone,
   run before every release and after each Firefox update. A version gate in
   the installer that warns on untested major versions. 150% and 200% checks
   for crispness and clipping (Firefox's own scaling), keyboard focus
   everywhere, no right-to-left work (decision 11).
6. **Install and undo** (`firefox/install.sh`, `firefox/uninstall.sh`, a
   throwaway-HOME suite like `dev/test-install.sh`). See the contract below.
7. **Release check.** Run the Firefox suites plus the project's existing ones
   that share code (none expected), record results in AUDIT.md, then the
   user's on-screen review in their real Firefox after an approved install.

## Installer contract for milestone 6

- Find profiles through `profiles.ini` in both `~/.mozilla/firefox/` and the
  XDG path `~/.config/mozilla/firefox/` (verified on this host: Firefox 160.0.1
  uses `~/.config/mozilla/firefox/profiles.ini`, where `[Install*]` `Default=`
  selects `*.default-release` while `[Profile1]` still carries legacy
  `Default=1` — prioritize `[Install*]` `Default=` over `[Profile*]`
  `Default=1`); list them and require the user to pick
  one (default: the profile marked as default for the installed Firefox).
  Never touch more than the chosen profile.
- Refuse while that profile is in use (its `lock`/`.parentlock`).
- Before any change, journal and back up: the whole existing `chrome/` folder,
  `user.js`, and the current values (or absence) of every pref the theme sets,
  read from `prefs.js`.
- Ship the theme as `chrome/platinum/` and add one marker-delimited `@import`
  block to `userChrome.css`, keeping any existing user rules after it.
- Set prefs in a marker-delimited `user.js` block. On undo, remove the block
  and restore each pref's original value or absence in `prefs.js` directly
  (Firefox closed), because deleting a `user.js` line leaves the last value in
  `prefs.js`.
- Undo restores untouched files byte for byte, keeps later user edits outside
  the markers, and reports conflicts instead of overwriting them.
- Test cases: fresh profile, profile with its own userChrome.css and user.js,
  reinstall, upgrade, interrupted install and undo, Firefox running, two
  profiles, and an XDG-path-only profile.

## Open questions for the user

1. **Tabs**: a slim Platinum tab row below the favorites bar, a row above the
   button toolbar, or vertical tabs in the left sidebar (closest to IE's
   Explorer bar)?
2. **Address band color**: which Lavender ramp replaces the teal tube (pick
   from mockups in milestone 2)?
3. **Which Firefox and profile** you use day to day. System Firefox is 160.0.1;
   no profile folder was visible from the agent's sandbox (`~/.mozilla`,
   `~/.config/mozilla`), so this may be a sandbox limit.
4. **Toolbar labels**: icons with labels as IE's default, or icons only?
5. **Status band**: a permanent IE-style band at the bottom (costs ~14 px of
   page) or only Firefox's floating status text restyled?

## References

- Native capture `reference/ie5-window-blank.png`; layout-only screenshot
  `/home/pieman/Pictures/Screenshots/Screenshot_20261122_225730.png`
  (slightly scaled, never measured).
- docs/REFERENCE.md for Platinum colors, tabs, menus, focus ring, selection.
- docs/DEVELOPMENT.md for `dev/app-test.sh` and the nested KWin.
- Firefox chrome sources in the installed `omni.ja`
  (`chrome/browser/content/browser/browser.xhtml`,
  `chrome/browser/content/browser/sidebar/sidebar-main.{mjs,css}`).
