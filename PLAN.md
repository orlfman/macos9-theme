# macos9-theme: plan

## Status

Updated: 2026-11-21 (Claude Code). Phase: colors, decoration, style, Plasma
(menu bar, dock, global theme) and install scripts built and checked headless;
not yet installed on the real desktop. Next: icons, cursors, fonts, GTK.

### Claims

One row per component. `nobody` = free. See AGENTS.md "Working together".

| Component  | Folder(s)                 | Claimed by | Status      |
|------------|---------------------------|------------|-------------|
| shared     | docs, tools, dev, scripts | nobody | dev/ sandbox + tools/compare.py done; test-install-live.sh added; docs fixed (AUDIT 24) |
| reference  | reference/, docs/REFERENCE.md | nobody | capture pass done (81 captures, CAPTURES.md); measurements partial |
| colors     | colors/                   | nobody     | Platinum.colors done (sandbox-checked) |
| decoration | decoration/               | nobody | plugin works in nested KWin; frame pixel exact; only the three Mac OS 9 boxes are created (AUDIT 20) |
| style      | style/                    | nobody | batches 1-7 + tooltips done (pixel exact); audit fixes #15-#19, #32 (keyboard focus ring, mixed check box, polish symmetry, RTL fallback, 64-bit scroll math, reversed scroll bars); next: Qt Quick menus/tooltips/switches (AUDIT 3, plan below); open: editable combo, size grip |
| plasma     | plasma/                   | nobody | menu bar, global theme, dock done (headless); selection text contrast fixed (AUDIT 22); main screen only (decision 10); menu bar resizing on hold (AUDIT 23, user) |
| icons      | icons/                    | nobody     | not started |
| cursors    | cursors/                  | nobody     | not started |
| gtk        | gtk/                      | nobody     | not started |
| extras     | extras/, wallpapers/      | nobody     | not started |
| packaging  | install.sh, uninstall.sh, packaging/ | nobody | install.sh / uninstall.sh rebuilt after Codex's three audits (#4-#14, #27-#31, #34-#38 fixed: moved-aside targets, record written first and taken off step by step so a retry never redoes a step, GTK files in the backup, shell stopped while restoring, decoration version guard, paths checked against where they led, recorded temporaries, same XDG folders required, checksums so your own additions and changes stay, a checked config copy, a stopped shell started by the next run); test-install 193/193, test-install-live 15/15 (running Plasma, two screens); not run on the real desktop yet |

## Goal

Make Plasma 6.8 look as close as possible to Mac OS 9.2.2 with the default
Platinum appearance, measured against the real system. See AGENTS.md
"Fidelity rules" and "Legal rules".

## Decisions

Open decisions need the user. Record the answer here with the date.

1. **Scale.** Both 4K screens run at scale 1, where 1x Mac OS 9 metrics are
   tiny. **Decided 2026-11-20 (user): true 1x at Plasma 100%**: draw every
   metric at its real Mac OS 9 pixel size, pixel exact; "from my testing,
   we can tweak it from there." Facts behind it: a 20 px menu bar is 3.1 mm
   on the 27" (163 ppi) and 3.7 mm on the 32" (138 ppi), against ~6.4 mm on
   a 2001 Mac at ~80 ppi; Plasma 200% would double that and give a
   1920×1080 workspace. So keep metrics in one place (no hard-coded sizes
   scattered around) so a later 2x variant or tweak stays cheap. Other
   options considered: Plasma 200%, a fixed 2x theme at 100%, a build-time
   multiplier.
2. **Application style engine.** Union can't draw scroll bar arrows or two
   bevel layers in Qt Widgets. **Step 3 spike (2026-11-20, see
   docs/FINDINGS.md):** Union gives scroll bar arrows zero size on 6.8.3;
   a C++ QStyle drew the Platinum scroll bar pixel exact in two captured
   cases. **Recommended: a C++ QStyle** (Qt Widgets; Qt Quick / Kirigami
   apps would get it through KDE's qqc2-desktop-style, to verify). Kvantum
   not evaluated (not installed). **Decided 2026-11-20 (user): C++ QStyle.**
3. **Decoration engine.** **Step 3 spike:** Aurorae draws the title as
   elided text over a fixed SVG, so it can't stop pinstripes around the
   title, condense it, or drop it; a C++ QPainter title bar matched the
   captures pixel exact in two window widths (title text excluded).
   **Recommended: C++ KDecoration3**, like windows2000-union. **Decided
   2026-11-20 (user): C++ KDecoration3.**
4. **Name and IDs.** Neutral installable IDs without "Apple"/"Mac OS".
   *Open.*
5. **Fonts.** Charcoal (system) and Geneva (small) can't ship. Find the
   closest freely licensed substitutes, or let the user point at their own
   copies at install time. *Open.*
6. **Menu bar.** How close to get: global menu + Apple-menu stand-in
   (launcher) + clock + application switcher on the right. *Details open.*
   Started 2026-11-21 (Claude Code): top panel 20 px, Kicker (cascading
   menu) as the Apple menu stand-in with a neutral icon (no Apple logo),
   the global menu (`appmenu`), a spacer, the system tray (kept: network,
   volume), the clock, and the Window List applet as the Application menu.
7. **Icons.** **Decided 2026-11-21 (user):** use an existing icon set
   ("what's out there at the moment"); pick after checking licenses
   (NineIcons Redux, Platinum9, Chi-Nata and others).
8. **Cursors.** **Decided 2026-11-21 (user):** our own, or one of the many
   Mac OS X cursor packs as a temporary stand-in ("not ideal but a temp
   thing ... while focusing more on the meat").
9. **Dock.** **Decided 2026-11-21 (user):** window management may stray
   from Mac OS 9: "even though the dock came in OS X, I would like to use
   it in 'os 9.' Bring the dock over, but make it designed around os 9
   look." Design (Claude Code, same day): a bottom panel styled like Mac OS
   9's pop-up window tab (`finder-popup-tab.png`, the OS 9 element that
   already sits on the bottom screen edge), apps as bevel buttons like the
   Launcher control panel (running = raised bevel, active = selected
   bevel, pinned but not running = bare icon).
10. **Screens.** **Decided 2026-11-21 (user):** "Menu bar and dock on
    master monitor": the menu bar and the dock go on the main screen only,
    as on Mac OS 9, and other screens get no panel (AUDIT.md finding 21).
    In Plasma 6 the primary screen is always screen 0, where the layout
    script's new panels go.
11. **Right-to-left layouts.** **Decided 2026-11-21 (user):** not
    supported ("I don't plan on supporting that"). AUDIT.md finding 26 is
    closed. The fallbacks already in the style stay (they keep clicks and
    drawing consistent), but nothing more is done for right-to-left.
12. **Deferred by the user, 2026-11-21:** AUDIT.md finding 25 (measured
    pixel tables and git history) waits until the user is ready to go
    public; finding 23 (menu bar drawn wrong when resized) is on hold.

## Components

Short list of what each one must match. `docs/REFERENCE.md` holds the
measurements.

- **colors**: Platinum grays, default highlight color, text colors, disabled
  text, window and view backgrounds; scheme groups for Window, View, Button,
  Selection, Tooltip, Header/WM (note: KWin uses `[Colors:Header]` for title
  bars if present).
- **decoration**: active title bar with horizontal pinstripes and centered
  title, inactive title bar flat; close box left; zoom and collapse boxes
  right; window frame and bevels; collapse = shade.
- **style**: push buttons (default button with thick ring), bevel buttons,
  check boxes and radio buttons, pop-up menus, scroll bars (arrows, grip lines
  on the thumb, track), sliders, progress bars (barber pole when
  indeterminate), tabs, list views with header, text fields with inset frame,
  group boxes, menus (incl. highlight), tool tips (help balloons?).
- **plasma**: menu bar panel on top, Apple-menu stand-in, global menu, clock,
  application menu; panel popups; optional Control Strip; desktop with
  volume icons? (scope TBD); task switching.
- **icons**: evaluate NineIcons Redux, Platinum9, Chi-Nata (licenses!) vs
  drawing our own; fallback chain for missing names.
- **cursors**: arrow, I-beam, watch (busy), crosshair, hand; redrawn.
- **gtk**: GTK 3 and GTK 4/libadwaita colors and shapes as far as supported.
- **extras**: Konsole/Alacritty/kitty colors, wallpaper (redrawn Platinum
  pattern/default desktop look), SDDM, splash, lock screen.

## Order of work

0. **Setup** (done 2026-11-19): AGENTS.md, PLAN.md, CHANGELOG.md, AUDIT.md,
   README.md, .gitignore, git repo + private GitHub repo orlfman/macos9-theme.
1. **Reference.** Mac OS 9.2.2 runs in QEMU (user set it up 2026-11-19, see
   AGENTS.md "The reference VM"); `tools/capture.py` takes lossless 1x
   captures (tested 2026-11-20 against a throwaway QEMU). Next: relaunch the
   VM with a QMP socket (done), confirm the Appearance control panel is at
   defaults (done 2026-11-20, see REFERENCE.md), then work through
   `docs/CAPTURES.md` (priority A first) and measure into
   `docs/REFERENCE.md`. A part of the theme starts once its A captures are
   measured. **Capture pass done 2026-11-20** (81 captures, all A and B
   items). REFERENCE.md has first measurements for most widgets; a full
   measuring pass per component (exact sizes, corners, fonts) is still to
   do, ideally right before that component is built.
2. **Sandbox.** Port windows2000-union's `dev/` tooling (sandbox, offscreen
   gallery, nested KWin, screenshot scripts) and add a screenshot comparison
   tool. Settle decision 1 (scale). **Tooling done 2026-11-20** (see
   `docs/DEVELOPMENT.md`); decoration test tools come with the decoration.
3. **Spikes.** Decide the style engine (decision 2) and decoration engine
   (decision 3) by drawing one scroll bar and one title bar each way.
   **Done 2026-11-20** (`spikes/`, docs/FINDINGS.md); both point to C++.
4. **colors** → **decoration** → **style** (the bulk of the look).
5. **plasma**: menu bar layout, Plasma style, look-and-feel package.
6. **icons**, **cursors**, fonts.
7. **gtk**, **extras**.
8. **packaging**: install/uninstall to user scope with backups; full audit;
   user's on-screen review.

## Plan: Qt Quick menus, tooltips and switches (AUDIT.md finding 3)

Asked for by the user 2026-11-21. Plan only; nothing built yet.

**What's wrong.** Qt Quick apps (System Settings pages, Discover, other
Kirigami apps) use KDE's Qt Quick Controls style, `org.kde.desktop`
(qqc2-desktop-style 6.32). It draws buttons, check boxes, radios, sliders,
progress bars, fields, spin boxes, combo boxes, tabs, scroll bars and
tool buttons through the QStyle, so those are Platinum already. These are
drawn in its own QML instead (read in
`/usr/lib/qt6/qml/org/kde/desktop/`):
- `Menu`: a `Kirigami.ShadowedRectangle` with rounded corners and a soft
  shadow; `MenuItem`: a highlight `Rectangle` in the focus color at 30%
  opacity, Kirigami icons and labels; `MenuSeparator`, `MenuBar`,
  `MenuBarItem` likewise.
- `ToolTip`: a rounded `ShadowedRectangle` (its own source has a TODO to
  use the QStyle).
- `Switch` and `SwitchDelegate`: a Breeze-like sliding switch
  (`private/SwitchIndicator.qml`). Mac OS 9 had no switches.
- `ItemDelegate`, `CheckDelegate`, `RadioDelegate`, `SwipeDelegate`
  (list rows), `Popup`, `Dialog`, `Drawer`, the combo box's pop-up list,
  `RangeSlider`, `BusyIndicator`, `PageIndicator`, `RoundButton`.
- Kirigami's own components (cards, inline messages, page headers) are
  drawn by Kirigami, not by any Qt Quick Controls style: only their colors
  follow the theme.
Plasma's own panels and pop-ups use Plasma Components and the Plasma
style, so they're not part of this.

**Approach.** A small Qt Quick Controls style of our own that overrides
only those controls and falls back to `org.kde.desktop` for everything
else (Qt 6 style modules can fall back through `import org.kde.desktop
auto` in their `qmldir`). Where qqc2-desktop-style's `StyleItem` bridge
has an element for it, the override draws through our QStyle (`menu`,
`menuitem`, `menubaritem`, `checkbox`, `itemrow`, `focusrect` and others
are in its plugin), so Qt Quick menus are the same pixels as the widget
menus and nothing is drawn twice. The tooltip has no such element: it
gets either a small C++ Qt Quick item of ours that paints with the
QStyle's tooltip drawing (preferred, one source of truth) or QML drawing
from the measured balloon values.

How it's switched on: the login script sets `QT_QUICK_CONTROLS_STYLE` to
our style (only if you haven't set it yourself) and adds our folder to
`QML_IMPORT_PATH`. Kirigami finds its color and size plugin by the style's
name (`kf6/kirigami/platform/<style>.so`; `org.kde.breeze` and
`org.kde.union` ship one each), so ours needs one too: a link to
`org.kde.desktop.so` (same colors and sizes, always the installed
version) in our plugin folder.

Not chosen: patching or copying `org.kde.desktop` (57 files plus a
compiled plugin; breaks with every KDE Frameworks update), or the Union
style engine (the whole style would have to be redone in its format).

**Steps.**
1. **Spike, sandbox only.** A minimal style with one override (`ToolTip`)
   and the fallback. Check in `dev/kirigami.qml`, `dev/gallery.qml` and
   System Settings in the nested KWin (`dev/app-test.sh`): the override is
   used; every other control still comes from `org.kde.desktop`;
   Kirigami's colors and sizes still load through the linked plugin (and
   what happens without it); KDE's platform theme leaves an already-set
   `QT_QUICK_CONTROLS_STYLE` alone (it chooses the style from
   `widgetStyle` otherwise); a Qt Quick app without KDE's platform theme
   still runs. Record the results in docs/FINDINGS.md. If the variable
   route doesn't hold, stop and bring the options to the user.
2. **Inventory.** Render the galleries and a few System Settings pages,
   list every control from the list above that's visible and wrong, and
   pair each with its Mac OS 9 capture (menus `menu-view-checked.png`,
   balloons `help-balloon.png`, list highlight from REFERENCE.md
   "Highlighted item").
3. **Menus** (most visible): `Menu`, `MenuItem`, `MenuSeparator`,
   `MenuBar`, `MenuBarItem` through `StyleItem`. Compare against the
   widget menu renders, which are already pixel exact.
4. **Tooltips**: the help balloon, as the widget tooltip draws it.
5. **Switches**: drawn as Platinum check boxes (`checkbox` element), as
   Mac OS 9 would have used one.
6. **List rows and pop-ups**: the Lavender highlight (#333399, white text)
   for delegates; square pop-up, dialog, drawer and combo list frames
   like the widget ones.
7. **Checks**: Qt Quick regions added to `dev/check-style.sh` (rendered
   with `dev/build/quickshot`), compared with the widget renders and the
   captures; sanitizer run; app pass with System Settings.
8. **Packaging**: the style folder and the Kirigami link become install
   targets (record, checksums, uninstall); the login script sets the two
   variables, guarded like the decoration: only while `org.kde.desktop` is
   installed at the version it was checked with (our overrides use its
   private `StyleItem` module). Install tests and the live test cover it.
9. **Audit and the user's on-screen review.**

**Risks.** `StyleItem` is qqc2-desktop-style's private module and can
change with a KDE Frameworks update (hence the guard). The variable
reaches every Qt Quick app in the session, KDE or not. Kirigami's own
components keep Kirigami's shapes.

## Open questions

- Include Mac OS 9 sound set equivalents? (Can't ship Apple sounds.)
- Before going public (AUDIT.md finding 25; the user: it waits until
  they're ready to go public): the style's check box and radio sprites and
  button corners (`style/platinum/sprites.h`, `slices.h`) are measured
  pixel by pixel from the captures. They're tiny generic UI shapes, but
  redrawing the check mark and radio dot by hand is the safe choice for a
  public release, and the git history still has the older raw tables.
- Window shade (collapse) vs minimize: settled for Wayland (KWin 6.8 doesn't
  shade Wayland windows, so the collapse box minimizes; docs/FINDINGS.md).
  X11 shading is untested.
