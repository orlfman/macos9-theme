# Plan: Platinum as a declared light theme

Original draft by Claude Code (Opus 5.5), 2026-11-26.
Codex audited the draft and implemented the corrected approach below.

## Audit and implementation

- KDE Plasma 6.8.3 reads the package palette to classify a global theme.
  Ship the canonical Platinum palette inside the installed package. Plasma's
  light picker, Settings portal and kde-gtk-config classify Window
  `qGray >= 192` as light. View is checked as a palette regression guard.
- Preserve the automatic switching configuration and the two user-selected
  slots. Platinum is available in the light picker. Use the base WhiteSur
  variant as a visible choice and dependency of the light variant.
- The script strips the standalone builder's ownership stamp during
  installation. Use the install manifest and its recorded checksums when
  retiring dark from older desktop installs. Preserve selected dark copies,
  edited trees and user-installed copies. Standalone publish recovery
  understands prior journals covering three variants.
- Adopt `WhiteSur-lavender-light` as the default. Migrate inherited legacy
  selections and leave explicit KDE selections and later GTK choices in
  place. Notify kde-gtk-config after apply so Wayland clients see the icon
  change. Undo restores the captured Wayland GTK icon preference when the
  adopted light value is still selected.
- Firefox System uses the real KDE portal. The sandbox check exercises
  Platinum → BreezeDark → Platinum with the installed userChrome. Firefox
  carries its existing appearance preferences.

`AUDIT.md` records the findings and test results. The original proposal
follows.

## Goal

Platinum is a light theme. Mac OS 9.2.2 windows are light gray, content areas
white, text black (`docs/REFERENCE.md`, `colors/Platinum.colors`: Window
`BackgroundNormal=221,221,221`). The desktop should say so to everything that
asks, so that:

- Firefox "Website appearance: System" and any site using
  `prefers-color-scheme` render light (the user's
  `~/Pictures/Screenshots/Screenshot_20261126_094333.png`).
- GTK 3/4, libadwaita, Electron, Qt and portal clients pick their light look.
- Icons are the light-panel WhiteSur variant, so no white status icons
  appear on light gray or white.

Second goal: stop building and installing `WhiteSur-lavender-dark`, which
Platinum never uses.

## Where it stands (checked live, 2026-11-26)

The live desktop runs the theme (`LookAndFeelPackage=platinum.desktop`,
color scheme `Platinum`, GTK `Platinum`). It **already** reports light:

| Signal | Value now | Set by |
|---|---|---|
| Portal `org.freedesktop.appearance color-scheme` | `2` (prefer light) | xdg-desktop-portal-kde, derived from the color scheme |
| `gsettings org.gnome.desktop.interface color-scheme` | `prefer-light` | kde-gtk-config, derived |
| `~/.config/gtk-{3,4}.0/settings.ini` `gtk-application-prefer-dark-theme` | `false` | kde-gtk-config, derived |
| Icon theme | `WhiteSur-lavender` (base) | global theme `defaults` |

So the Firefox case in the screenshot should already resolve to light. But
none of this is declared by the theme. It works because Plasma computes it
from how bright the Window background is. Nothing tests it, so a color
change, a Plasma update or a different portal backend could flip it silently.
The icon theme is the one real mismatch: the base WhiteSur variant is made
for dark panels.

## Part A: declare and test "light"

### A1. Color scheme (`colors/`)

- Look up the exact rule xdg-desktop-portal-kde 6.8.3 and kde-gtk-config
  6.8.3 use to call a scheme dark or light (believed: gray value of Window
  `BackgroundNormal` below 192 means dark; verify in source and record in
  `docs/FINDINGS.md`).
- Platinum's 221 is light with a margin of 29. Add a check to the colors
  checker that fails if Window or View background falls under the threshold,
  so a future color edit can't flip the system to dark.

### A2. Global theme (`plasma/`)

- Plasma 6 has automatic light/dark global theme switching (day/night).
  Verify on 6.8.3 which `kdeglobals [KDE]` keys hold the light and dark
  global themes (believed: `DefaultLightLookAndFeel`,
  `DefaultDarkLookAndFeel`, `AutomaticLookAndFeel`) and whether a
  look-and-feel package can mark itself as light in `metadata.json`.
- If supported: register `platinum.desktop` as the light global theme. Leave
  the dark slot and automatic switching alone (the user's settings).
- Change `defaults` `[kdeglobals][Icons] Theme=` to `WhiteSur-lavender-light`
  (Part B) and update `plasma/make-plasma.py`, which writes the same file.

### A3. GTK (`gtk/`)

- The Platinum GTK theme has no dark variant. Confirm that GTK 3 and GTK 4
  with `gtk-application-prefer-dark-theme=true` still draw Platinum and not a
  half-dark mix, and that libadwaita apps follow `prefer-light` with our
  `libadwaita.css` layer.
- Don't write `settings.ini` or gsettings ourselves while kde-gtk-config owns
  them. Only document and test the derived values.

### A4. Firefox (`firefox/`)

- Verify in the sandbox that with the Platinum userChrome theme,
  "Website appearance: System" follows the portal: a test page with
  `prefers-color-scheme` media queries renders light, and renders dark if
  the sandbox portal is switched to dark (proves it's really following).
- Check whether Firefox's own `browser.theme.content-theme` /
  `browser.theme.toolbar-theme` need setting with the userChrome theme
  active. Only touch `user.js` if the test shows they do; the install must
  back them up and undo them.

### A5. End-to-end check (`dev/`)

One sandbox test that installs the theme into a disposable home and asserts:
portal `color-scheme` = 2, gsettings `prefer-light`, GTK `prefer-dark=false`,
icon theme `WhiteSur-lavender-light`, Firefox test page light. Record in
`AUDIT.md`.

## Part B: icons, base + light only

### Why

WhiteSur's three variants (sizes from a build of pin `73d8040`):

| Variant | On disk | Files / links | What it is |
|---|---|---|---|
| `WhiteSur-lavender` | 63 MB | 11,550 / 15,981 | full set; white `#f2f2f2` status icons for dark panels |
| `WhiteSur-lavender-light` | 7 MB | 1,458 / 1,834 | dark `#363636` status icons at 16–32 px; everything else is links into the base |
| `WhiteSur-lavender-dark` | 32 MB | 7,339 / 6,469 | own recolored actions/places/devices/apps for dark windows |

`-light` can't stand alone: its `actions`, `places`, `apps` and other folders
are symlinks into the base, so the base stays. Dropping `-dark` saves about
32 MB and 13,800 files per build and install, plus build and test time.

In the base variant, hundreds of 16 and 24 px status icons are white with no
`ColorScheme-Text` class, so neither Plasma nor GTK recolors them. Most 22 px
tray icons do carry the class, which is why the Plasma menu bar looks right
today. GTK never recolors.

### B1. Builder (`icons/`)

- Build only `''` and `-light`. Upstream `install.sh` loops over
  `COLOR_VARIANTS=('' '-light' '-dark')` and accepts a color option; check
  whether that option can pick the two we want, otherwise patch the variant
  list the same way `whitesur-lavender.py` already patches `THEME_VARIANTS`
  (#106), with the same refusal if the anchor moves.
- `icons/whitesur-lavender.py --verify`: expect two themes, not three.
- Custom layer: remove `icons/custom/dark/` and its support in the generator
  and validator. Update `icons/custom/README.md`.
- `icons/review-whitesur-update.sh`: stop reporting dark-only changes.

### B2. Install, upgrade, uninstall (`shared`: `install.sh`, `uninstall.sh`, `scripts/`)

- Install and select `WhiteSur-lavender-light`. The base stays installed
  (the light variant links into it) and stays selectable.
- Upgrade: an existing install has an owned `WhiteSur-lavender-dark` in
  `~/.local/share/icons` (it's there on the live desktop now). Remove it if it
  carries our build marker and is not the selected icon theme. If the user
  selected it, keep it and warn, following the `kept_packages` contract
  (#110, #126).
- Uninstall: still remove a leftover owned `-dark` from older installs.
- Users who had `WhiteSur-lavender` selected by our auto-select move to
  `-light`; a theme the user chose by hand is left alone.
- `scripts/icon_prefs.py` and `scripts/common.sh`: update the theme ID list.

### B3. Tests (`dev/`)

- `dev/test_icons_phase1.py`: `THEME_IDS` becomes two; #111 baseline
  recounted for two trees (the custom-entry margin stays); #119
  cross-directory alias test reworked for base and `-light`; add a check that
  no `-dark` tree is produced.
- `dev/test-install.sh` and `dev/test-install-live.sh`: install, upgrade from
  a three-variant install (dark removed, or kept when selected), uninstall.
- Rerun Plasma (`dev/check-plasma`), GTK and Trash suites, since the icon
  default changes.
- `docs/FINDINGS.md` and `icons/README.md`: update the variant facts.

## Order

1. A1 and A2 research (rules and keys, record in FINDINGS). No code.
2. Part B (bigger, self-contained): builder, install/upgrade/uninstall, tests.
3. A2 icon default and global theme registration, A1 color check.
4. A3, A4 checks; A5 end-to-end test.
5. User reinstalls and reviews: tray and menu bar icons, a GTK app, Dolphin
   at small icon sizes, Firefox with a `prefers-color-scheme` site.

## Open questions for the user

- Should Platinum also be registered as the light half of Plasma's automatic
  day/night switching, or only set as the current global theme?
- Keep `WhiteSur-lavender` (base) visible in System Settings as a choice, or
  hide it (it must stay installed either way)?
