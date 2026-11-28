# Development: sandbox and comparison

How to try the theme without installing it, and how to check it against the
Mac OS 9 reference. Commands run from the repository root. Renders go to
`dev/shots/` (git-ignored).

How isolated each tool is (AUDIT.md finding 24):

- `dev/run.sh` and everything built on it (`shoot.sh`, `app-test.sh`,
  `kwin-test.sh`, `plasma-test.sh`, `live-test.sh`, `check-*.sh`): their own
  XDG config, data, cache and state folders in `dev/build/sandbox`, and
  either no D-Bus at all or a private one (`dbus-run-session`). They keep
  your real `HOME` and `XDG_RUNTIME_DIR`, so a program that writes to
  `~/something` directly, or talks to your systemd user session
  (`systemctl --user`), could still reach your real setup. None of the
  programs they start are known to do that; it's a limit, not a seen
  problem.
- `dev/test-install.sh` and `dev/test-install-live.sh`: fully separate:
  `env -i`, their own `HOME`, every XDG folder and `XDG_RUNTIME_DIR` in a
  throwaway home, a private D-Bus and a stand-in `systemctl`.

The `dev/` tooling is adapted from the user's own windows2000-union project
(`/mnt/storage1/local/projects/windows2000-union`, BSD-2-Clause); its
`docs/DEVELOPMENT.md` has the full list of what Union 6.8 can and can't draw.

## Build the test programs

```bash
dev/build.sh
```

Builds `gallery` (Qt Widgets), `quickshot` (QML to PNG), `tabdemo` (keyboard
focus in a real compositor) and `fakeinput` (real pointer and key input inside
the nested KWin) into `dev/build/`.

## Render the galleries

```bash
dev/shoot.sh breeze breeze
```

`shoot.sh [STYLE] [SCHEME...]`: Qt Widgets gallery (+ menu, dialog, focus
sheet), Qt Quick gallery and a Kirigami page, as
`dev/shots/STYLE-SCHEME-*.png`. STYLE is a Union style id (any folder under
`style/`, or `breeze`); SCHEME is `platinum`, `breeze`, `user` or a `.colors`
file. Needs a running Wayland session for the Qt Quick renders.

`dev/run.sh SCHEME STYLE command...` runs any command in the sandbox. Options
(environment): `FONT`, `TITLEFONT`, `EXTRA_FONT_DIRS` (stand-in fonts visible
to the sandbox only), `SCALE` (Qt scale factor), `QSTYLE` (a QStyle instead
of Union; also written as the sandbox's `widgetStyle`, so Qt Quick apps use
`org.kde.desktop` and draw through it), `PLATFORM=wayland` (for Qt Quick).

## Real KWin, real apps

```bash
dev/kwin-test.sh breeze
```

```bash
dev/app-test.sh dolphin "dolphin --new-window /usr/share"
```

A headless nested `kwin_wayland --virtual` with its own D-Bus, two test
windows (or any app) screenshotted by Spectacle. `M9_STYLE`, `M9_DECORATION`
(KDecoration plugin id, default `org.kde.breeze`), `M9_SIZE`, `M9_WAIT`;
`VT_MAXIMIZED=1` for a maximized window. When `decoration/build/plugins`
exists, it's on `QT_PLUGIN_PATH`.

### Trying it by hand

```bash
dev/live-test.sh
```

Opens a nested KWin as a normal window on the user's desktop (windowed
Wayland backend, 1600×1000 at 1x, `M9_SIZE` to change) with the Platinum
decoration, style and colors, sandboxed like `run.sh` (own XDG folders,
private D-Bus, nothing installed). It rebuilds the style, the decoration
and `dev/build/livedemo` (every themed control on its tabs, the few
still-Fusion ones marked "Still Fusion"), then starts the demo, Dolphin and Kate, or the commands given as
arguments. With `M9_PLASMA=1` (the default) the Plasma shell runs too, with
the Platinum Plasma style and `plasma/layout.js` (the menu bar; app menus
move into it); `M9_PLASMA=0` for apps only. Closing the apps or the nested
KWin window ends it; the logs are `dev/build/live-*.log`. Agents can't
screenshot inside it (its D-Bus is private), so it's for the user's eyes.

## The Plasma style and the menu bar

```bash
dev/check-plasma.sh
```

`plasma/make-plasma.py` writes the Plasma style into `plasma/platinum/`
(regenerate, don't edit). `dev/plasma-test.sh [THEME]` runs plasmashell in a
headless nested KWin with a fresh layout from `plasma/layout.js` (your own
panel files are never read), opens a plain window and then
`dev/build/livedemo` (so the dock shows a running and an active app),
clicks the first
global menu title (`dev/build/fakeinput`), opens the launcher, and saves
`dev/shots/plasma-THEME-{desktop,menu,launcher}.png`. The sandbox gets its
own empty Desktop folder. With `M9_APPLY=lnf` it applies the
look-and-feel package (`plasma-apply-lookandfeel --resetLayout`, sandbox
only) instead of evaluating the layout, and prints what the package set. That
mode previews Lavender Desktop Pattern. The panel artwork comparisons use
a solid backdrop.
`dev/check-plasma.sh` runs it and compares the bar, its rounded ends, the
divider, an open title and the dock's top corners with the captures. Plasma needs
`kactivitymanagerd` and, for the global menu, `kded6` started by hand in the
private session (no systemd there).

## The window decoration

```bash
decoration/build.sh
```

```bash
dev/shoot-deco.sh platinum
```

```bash
M9_DECORATION=platinum VT_SINGLE=1 M9_SIZE=900x500 dev/kwin-test.sh platinum
```

```bash
M9_DECORATION=platinum dev/app-test.sh kwrite kwrite platinum
```

`decoration/build.sh` builds `decoration/build/plugins/org.kde.kdecoration3/platinum.so`
(moc + g++, no install). `dev/shoot-deco.sh` renders `dev/decoration.qml`
through KWin's own decoration preview: active, inactive, a long title and
pressed boxes, at the reference window's size (but see docs/FINDINGS.md: no
button layout, no shadow, 1 px smaller). With `M9_DECORATION=platinum`,
`kwin-test.sh` and `app-test.sh` load the plugin and set the Mac layout
(close left, zoom and collapse right); `VT_SINGLE=1` opens one window titled
"Mac OS". The nested KWin's background is black, so the black drop shadow
doesn't show there.

## The application style

```bash
style/build.sh
```

```bash
dev/check-style.sh
```

```bash
QSTYLE=Platinum dev/run.sh platinum breeze dev/build/gallery dev/shots/platinum-widgets.png
```

`style/build.sh` builds the C++ Qt style into
`style/build/plugins/styles/platinumstyle.so` (no install); `dev/run.sh` puts
it on `QT_PLUGIN_PATH`, and `QSTYLE=Platinum` selects it.
`dev/check-style.sh` renders every state with `dev/styleshot` through the
style's own draw calls, at the captures' sizes, and diffs each captured one
with its reference (push buttons on their edge bands, since labels need
Charcoal; regions the captures' pointer covers are left out). It exits 1 on
any difference.

The bevelled parts are data measured from the captures:
`tools/gen-style-data.sh` regenerates `style/platinum/slices.h` (9-slices,
via `tools/nineslice.py`), `style/platinum/sprites.h` (fixed-size parts,
via `tools/sprite.py`), `style/platinum/progress.h` (progress bar column
profiles) and `style/platinum/tabs.h` (tab edges row by row, via
`tools/tabs.py`). It needs `reference/`.

### The Qt Quick Controls style

```bash
style/quick/build.sh
```

```bash
dev/check-quick.sh
dev/check-tabs.sh
```

```bash
M9_QUICK=1 QSTYLE=Platinum dev/run.sh platinum breeze env QT_QUICK_BACKEND=software dev/build/quickshot dev/quick-inventory.qml /tmp/inventory.png
```

`style/quick/build.sh` builds the Platinum Qt Quick Controls style into
`style/build/qml/Platinum` (QML overrides of KDE's `org.kde.desktop` plus
the C++ item that paints with the QStyle) and links Kirigami's platform
plugin for it (`style/build/plugins/kf6/kirigami/platform/Platinum.so`).
`M9_QUICK=1` with `QSTYLE=Platinum` makes `dev/run.sh` use it.
`dev/check-tabs.sh` (50 checks) checks that bottom tabs are the top tabs upside down: tab faces in every state, the tab bar base, the pane, and whole tab widgets, plain and in document mode, at 1x to 2x (at 1.25x and 1.5x against the 1x mirror scaled the way Qt scales whole pixels), that tab titles stay out of close buttons top and bottom in both directions, that every tab part ignores an antialiasing painter at 1.25x to 1.75x, and that a Qt Quick footer TabBar (Kwi) is the header upside down.

`dev/check-quick.sh` (33 checks) renders the Qt Quick menus (first and last row
selected), combo box list, menu bar, switch indicator, tooltip, dialog
frame, range slider (and where KDE's hidden handles sit), drawer edge and a
combo box whose longest label changes while its item count stays the same
(`dev/quick-regions.qml`) and compares each with its widget counterpart
(`dev/quickref.cpp`) pixel for pixel; then it switches the app to Fusion
while running and compares the same pieces with KDE's own style under
Fusion (the fallback); and it checks with `dev/quickkeys.cpp` that switches
still toggle with Space and look the same to screen readers as with KDE's
style, and that keyboard focus shows on Qt Quick sliders and range sliders
and on a QSlider. The tab close checks cover compact geometry, selected,
disabled and pressed states, custom icon size and tint, and fallback to KDE.
`dev/quickscroll.cpp` compares both arrows with the Qt Widgets drawing in
standalone horizontal and vertical bars, a Flickable, default and custom
ScrollView bars, and Kirigami. It checks pointer movement across arrows,
paging, middle click, release and cancellation. The suite requires the
probe to exit successfully and compares screenshots after switching to
Fusion with stock KDE's screenshots. `M9_SCROLL_DUMP=DIR` saves the
standalone vertical crops.
`dev/quick-live.qml` is a visible window for `dev/app-test.sh` that
opens its own pop-up (`-- popup=menu|combo|tooltip|menubar|windowmenu|
windowclick`; `windowclick` needs a real click: chain
`dev/build/fakeinput click X Y` in the app command, as Wayland gives a
pop-up window its grab only for input). `dev/quick-inventory.qml` shows every control the
plan covers, one pop-up per step. On the offscreen platform `quickshot`
shows its window (nothing reaches a real display), so pop-ups place
themselves as on a screen.

## Install and uninstall

```bash
dev/test-install.sh
```

Runs `install.sh` and `uninstall.sh` in a throwaway home
(`dev/build/test-home`): `env -i`, its own `HOME` and XDG folders, a
private D-Bus session, its own runtime folder, and a stand-in `systemctl`
that only logs (so nothing reaches the real Plasma, KWin or systemd
session). Every scenario starts from a fresh Breeze home with a panel
layout and GTK files of its own. It covers dry runs, what install puts
where, the login script (including leaving the decoration out after a
KDecoration upgrade), `--apply` and repeats, uninstall putting every
config and GTK file back byte for byte, and the failure cases from AUDIT.md
findings 4-14 and 27-31: things already in the way of a target, a linked
config folder, a file where a folder is needed, an install that fails or
is interrupted at a dozen points, an uninstall that fails or is
interrupted at 16 points and is run again, a failing theme switch,
switching in System Settings instead of `--apply`, Platinum already
selected before the install, `~/.config` or a GTK folder link pointed
elsewhere between install and uninstall, files that only look like
leftovers, a different data or config folder at uninstall time, and from
findings 34-38: a link inside a copied folder, files the user added to or
changed in what was installed (kept by uninstall, moved aside by a
reinstall), an incomplete or changed config copy, a dry run that matches
the real run, and a shell that won't start again (a stand-in systemd);
from findings 39-42: two versions of the same file moved aside, a file
missing inside a copied folder, an empty folder the user added, and a dry
run on a fresh home printing no errors; the Qt Quick style (its folder and
Kirigami's plugin link installed and removed, a link of the user's moved
aside and back, a re-pointed link left alone, and the login script turning
it on only with Platinum selected, never over the user's own choice, and
not after a KDE Frameworks upgrade); a
leftover half-made backup, a held lock, and a home path with spaces and
quotes. From findings 49 and 50: apps started from the session's old
environment after uninstall (the pass-through it leaves until the next
login; `next_login` runs the one-shot cleanup), a reinstall before that
login, a profile with none of the copied files, a cut-short checksum list;
from findings 54-58: a login script of the user's at the pass-through
script's name, a Kirigami link of the user's, a file or folder of the
user's at the Qt Quick module's place, a backslash in a copied file's
name, and a dry run that shows the pass-through. The suite also checks
saved copies and edits to the cleanup hook, edits to its QML module, backup
filenames ending in a newline, a dry run with a displaced folder waiting
for a vacant path, and retries after a failure creating either the temporary
plugin link or the QML module. It also checks a selected wallpaper
recorded in the desktop config and the warning from Qt without a JPEG XL
decoder. The plugins are built once and
handed to install.sh through `M9_PREBUILT` (tests only). It uses
`dev/build/styleshot` (from `dev/check-style.sh`) to check the installed
style plugin loads.

```bash
dev/test-install-live.sh
```

The same against a running Plasma: a headless nested KWin with two
virtual screens, `plasmashell`, `kded6` (with its GTK settings sync) and
the activity manager, in a throwaway home (`dev/build/test-home-live`). It
puts a panel of the user's own on each screen, runs `install.sh` and
`install.sh --apply`, lists what the switch changed (Plasma's GTK sync
rewrites `gtk-3.0`, `gtk-4.0`, `xsettingsd` and `~/.gtkrc-2.0`), then
runs `uninstall.sh` and checks that it stopped the shell (the old process
is gone) and started a new one (the `kquitapp6` path; the systemd path
can't be tested without your real user session), that both panels are
back on their screens with their widgets and a widget setting of the
user's (a clock with seconds), both screens have their previous wallpapers,
and every config and GTK file is back byte for byte. The same test checks
that installing alone leaves both wallpapers in place and switching to
the global theme renders Lavender Desktop Pattern on both screens. The
picker-only case verifies that uninstall keeps both selected wallpapers
under Breeze and removes their packages after the selections change. The
suite runs `install.sh` again after the switch (an update), and
checks that a Qt Quick app started with the login script's environment
gets the Platinum Qt Quick style, that a launcher holding the session's
environment across the uninstall still starts Qt Quick apps, and that the
next login leaves nothing behind and Qt Quick apps get KDE's style again.

### Light appearance

```bash
dev/test-install-live.sh --appearance
```

This extends the two-screen disposable install test. It reads the installed
package through Plasma's own light/dark classifier, checks the portal and GTK
preferences and loads the Firefox userChrome in a new test profile. Firefox
renders a local page first with Platinum, then with BreezeDark and finally
with Platinum again, with Website appearance set to System. The check needs
Firefox, the KDE Settings portal and development headers for KPackage and
KLookAndFeel.
For a palette-only check run `python3 -I dev/light-theme.py colors/Platinum.colors`.

## Firefox (`userChrome.css` sandbox)

```bash
dev/firefox-test.sh [NAME] [URL]
dev/check-firefox-m1.sh
dev/render-firefox-m2.sh
dev/check-firefox-m3.sh
dev/check-firefox-m4.sh
dev/check-firefox-m5.sh
dev/check-firefox-m6.sh
tools/check-firefox-selectors.py
```

`dev/firefox-test.sh` runs Firefox inside a headless nested `kwin_wayland
--virtual` with its own `env -i`, private D-Bus, isolated `HOME`, `XDG_*`, and
`XDG_RUNTIME_DIR`, the Platinum KWin decoration (`browser.tabs.inTitlebar=0`),
the Platinum GTK 3 theme, and a fresh profile in the per-run sandbox under `dev/build/`
(never touching `~/.mozilla` or `~/.config/mozilla`), screenshotting into
`dev/shots/firefox-NAME.png`. `dev/check-firefox-m1.sh` runs the 46-check
Milestone 1 discovery and verification suite; `dev/render-firefox-m2.sh` renders
the Milestone 2 visual mockup variants and comparison sheets;
`dev/check-firefox-m3.sh` runs the 36-check Milestone 3 verification suite
(whole-pixel row sampling across the three top bands, hover/pressed states,
urlbar focus/selection/dropdown, narrow overflow, Customize Mode, and gating);
`dev/check-firefox-m4.sh` runs the 34-check Milestone 4 full-coverage suite
(live-switchable `1A`+`1C` tabs, `5A` permanent status band, busy activity
indicator, Platinum menus/panels/urlbar popup, find & notification bars,
sidebar, real inactive window flattening, Private/popup/fullscreen windows,
Customize Mode, and theme gating); `tools/check-firefox-selectors.py` validates
every `#id` and `::part()` selector in `firefox/chrome/` against the installed
Firefox `omni.ja` archives and checks the major version against
`firefox/version.json` (exiting `3` on untested major versions unless
`--allow-untested-version` is passed); `dev/check-firefox-m5.sh` runs the
32-check Milestone 5 robustness suite (selector checker + negative controls,
version gate, keyboard focus across all chrome controls, and 150%/200% Wayland
scaling crispness and zero-clipping checks in a `2400×1600` virtual KWin);
`dev/check-firefox-m6.sh` runs the Milestone 6 throwaway-`HOME`
installer and undo suite for `firefox/install.sh` and `firefox/uninstall.sh`
(fresh and pre-customized profiles, `@charset`/`@namespace` ordering, post-install
user edits outside markers, conflict & symlink refusal, reinstall & pref-retiring
upgrade, fault-injected mid-install and mid-uninstall recovery, `lock` symlink
and live `.parentlock` `fcntl` lock refusal, two-profile `[Install*]` `Default=`
precedence, XDG-only profile + untested version warning, and a live nested
Wayland Firefox 160.0.1 cold-launch + full undo check).

## Measure and compare

`tools/compare.py` works on reference captures and sandbox renders alike.
Any image argument can carry a crop: `file.png@X,Y,W,H`.

```bash
python3 -I tools/compare.py col reference/controls-monitors.png 805 315 335
```

| Subcommand | What |
|------------|------|
| `row IMAGE Y X0 X1` / `col IMAGE X Y0 Y1` | runs of colors along a row or column |
| `colors IMAGE [--top N]` | most common colors |
| `bbox IMAGE [--bg RRGGBB]` | bounding box of everything that isn't the background |
| `zoom IMAGE [--zoom N]` | enlarged copy without smoothing |
| `diff REF OURS [--zoom N] [--tolerance T]` | pixel diff of two same-size regions: counts, max difference, bounding box, and a side-by-side picture (reference, ours, differences in magenta); exit 1 when they differ |

Use `diff` for every fidelity claim in `AUDIT.md`: the reference region, our
region, the numbers it prints, and the picture.

## Checked so far

2026-11-20 (Claude Code): `dev/build.sh` builds all four tools;
`dev/shoot.sh breeze breeze` renders all three galleries; `dev/kwin-test.sh
breeze` runs the nested KWin and screenshots two Breeze-decorated windows.
`tools/compare.py` reproduces hand measurements from earlier sessions (the
selected bevel button column, the 12×12 check box) and reports 0 / 120
differing pixels for identical / normal-vs-pressed check box crops.

## libadwaita check (GTK Milestone 5)

`dev/check-adw.sh [broadway|plasma]` runs a stock PyGObject
`AdwApplication` (`dev/adw-check/fixture.py`, no app CSS) in a disposable
HOME/XDG tree and private bus. `plasma` adds virtual KWin, both Settings
portals and Platinum colors. Each run logs `AdwStyleManager` state and renders
the window itself to a PNG (gallery, narrow 360 px, alert dialog, keyboard
focus, disabled, high contrast). Then the runs repeat as `layer-*` with the theme's
`gtk-4.0/libadwaita.css` imported from `~/.config/gtk-4.0/gtk.css`; in
`plasma` mode FFmpeg Converter GTK, Mission Center, Faugus Launcher and a
zenity alert are screenshotted stock and layered (`*-app-*.png`).
`dev/adw-check/montage.py <run> [modes]` puts stock over layer.
`dev/adw-check/verify.py` checks state, counts #CCCCFF/#DDDDDD pixels,
that high contrast is identical to stock, and that the layer adds no GTK
criticals. `GTK4_CHECK_ADW_LAYER=1 dev/check-gtk4.sh` runs the plain GTK 4
suite with the layer imported too. To look at it yourself:
`dev/live-adw.sh` (live-test.sh's nested KWin with the layer in its
sandbox).
Today: broadway 78/78, plasma 118/118 (also checks both parentless alert kinds, the header bar edges and close boxes 4 px in, with the user's `close:maximize,minimize` layout).

## GTK 3 header bar gaps

`dev/check-gtk3-headerbar.sh` (Broadway, disposable home) renders a GTK 3
header bar laid out like Lutris's (stretched start box around one button,
linked search box as title, nested end box with a linked pair and a menu
button) and checks that the pinstripes show in exactly two open stretches,
none within 6 px of a widget (#261), then a Lutris-style popover menu
(`dev/gtk3-popover-menu.py`: face, black outline, highlight, separator,
check mark; #262) and a narrow notebook whose tab scroll arrows must be the
Platinum scroll arrows pixel for pixel, the left one closed on its right,
with a tab-row "+" button that stays above the pane
and a tab with a close button no taller than a plain one
(`dev/gtk3-notebook-arrows.py`, #263–265), and spin buttons with the
Platinum arrow boxes 2 px right of the field (`dev/gtk3-spinbutton.py`,
#267). Today: 16/16.
