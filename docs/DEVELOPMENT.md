# Development: sandbox and comparison

How to try the theme without installing it, and how to check it against the
Mac OS 9 reference. Commands run from the repository root. Everything here
runs in `dev/build/sandbox` (its own XDG folders, no D-Bus to your session,
offscreen rendering or a headless nested KWin), so your real desktop is never
touched. Renders go to `dev/shots/` (git-ignored).

The `dev/` tooling is adapted from the user's own windows2000-union project
(`/mnt/storage1/local/projects/windows2000-union`, BSD-2-Clause); its
`docs/DEVELOPMENT.md` has the full list of what Union 6.8 can and can't draw.
The decoration test tools (decoshot, damagetest, test-deco, shoot-deco) are
added with the decoration.

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
only) instead of evaluating the layout, and prints what the package set.
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

## Install and uninstall

```bash
dev/test-install.sh
```

Runs `install.sh` and `uninstall.sh` in a throwaway home
(`dev/build/test-home`) that starts as a Breeze setup with its own panel
layout: every XDG folder points there, D-Bus is a private session, the
runtime folder is its own, and a stand-in `systemctl` only logs (so nothing
reaches the real Plasma, KWin or systemd session). It checks dry runs,
what install puts where, that `--apply` copies the config files once and
switches (the global theme, the widget style through `kdedefaults`, the
button order), and that uninstall puts every config file back byte for
byte and removes everything it installed. It uses `dev/build/styleshot`
(from `dev/check-style.sh`) to check the installed style plugin loads.

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
