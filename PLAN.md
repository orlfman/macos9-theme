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
| style      | style/                    | nobody | batches 1-7 + tooltips done (pixel exact); audit fixes #15-#19, #32 (keyboard focus ring, mixed check box, polish symmetry, RTL fallback, 64-bit scroll math, reversed scroll bars); Qt Quick style in style/quick: menus, menu bar, combo list, tooltips, switches (AUDIT 3, check-quick 21/21; installed by install.sh); also dialogs (measured modal frame), drawers, range sliders; open: editable combo, size grip |
| plasma     | plasma/                   | nobody | menu bar, global theme, dock done (headless); selection text contrast fixed (AUDIT 22); main screen only (decision 10); menu bar resizing on hold (AUDIT 23, user) |
| icons      | icons/                    | nobody     | not started |
| cursors    | cursors/                  | nobody     | not started |
| gtk        | gtk/                      | nobody     | not started |
| extras     | extras/, wallpapers/      | nobody     | not started |
| packaging  | install.sh, uninstall.sh, packaging/ | nobody | install.sh / uninstall.sh rebuilt after Codex's four audits (#4-#14, #27-#31, #34-#42 fixed: moved-aside targets, record written first and taken off step by step so a retry never redoes a step, GTK files in the backup, shell stopped while restoring, decoration version guard, paths checked against where they led, recorded temporaries, same XDG folders required, checksums so your own additions and changes stay, a checked config copy, a stopped shell started by the next run); also installs the Qt Quick style (with a link target kind for Kirigami's plugin); test-install 272/272, test-install-live 19/19 (running Plasma, two screens; after uninstall a pass-through keeps the session's Qt Quick apps working until the next login); not run on the real desktop yet |

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
13. **Qt Quick drawing.** **Decided 2026-11-21 (user):** our own small C++
    Qt Quick item, public Qt API only, not KDE's private `StyleItem`
    bridge (see "Plan: Qt Quick menus, tooltips and switches").

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

Asked for by the user 2026-11-21. Revised the same day after Codex's
review (AUDIT.md findings 43-48). **Step 1 (spike) done 2026-11-21**:
results in docs/FINDINGS.md "Qt Quick style spike", code in
`spikes/qtquick/`. It confirmed the approach with these changes: KDE's
parts are hidden (`opacity: 0` through a `Binding`), never replaced, and
our item sits next to them; a hidden `QWidget` tells the items when the
app's style changes; `Menu.delegate` is overridden too; the Kirigami link
is needed. **Built in `style/quick` 2026-11-21 (steps 2-5, 7):** menus,
menu bar, combo box list, tooltips and switches; `dev/check-quick.sh` 12
of 12 (each piece equals its widget counterpart, and after a switch to
Fusion equals KDE's own style). **Then (same day):** step 8 (install.sh
installs it, the login script turns it on as planned), switches checked
(Space, accessible role and state as with KDE's style), and real pop-ups
in the nested KWin (in-window pop-ups, which is what Qt Quick uses by
default, and a menu as its own window: frame, shadow and see-through
corners right). **Step 6 done (same day):** dialogs in the measured plain
modal frame (white body, no dimming), drawers framed like menus on their
open side, the range slider from the QSlider's groove and thumbs; list
rows were already right. Left: step 9 (audit, the user's review).
Open: a menu opened as its own window lands at the window's corner, not
where asked (KDE's style not compared: its menu didn't open in that
test).

**What's wrong.** Qt Quick apps (System Settings pages, Discover, other
Kirigami apps) use KDE's Qt Quick Controls style, `org.kde.desktop`
(qqc2-desktop-style 6.32). It draws buttons, check boxes, radios, sliders,
progress bars, fields, spin boxes, closed combo boxes, tabs, scroll bars
and tool buttons through the QStyle, so those are Platinum already. These
are drawn in its own QML instead (read in
`/usr/lib/qt6/qml/org/kde/desktop/`):
- `Menu`: a `Kirigami.ShadowedRectangle` with rounded corners and a soft
  shadow; `MenuItem`: a highlight `Rectangle` in the focus color at 30%
  opacity; `MenuSeparator`, `MenuBar`, `MenuBarItem` likewise.
- The combo box's pop-up list: `ComboBox.qml` builds its own `Menu` and
  `MenuItem` delegate inside the file, so a `Menu` override alone doesn't
  reach it (finding 47).
- `ToolTip`: a rounded `ShadowedRectangle`.
- `Switch` and `SwitchDelegate`: a Breeze-like sliding switch. Mac OS 9
  had no switches.
- List rows (`ItemDelegate`, `CheckDelegate`, `RadioDelegate`,
  `SwipeDelegate`), `Popup`, `Dialog`, `Drawer`, `RangeSlider`,
  `BusyIndicator`, `PageIndicator`, `RoundButton`.
- Kirigami's own components (cards, inline messages, page headers) are
  drawn by Kirigami, not by any Qt Quick Controls style: only their colors
  follow the theme.
Plasma's own panels and pop-ups use Plasma Components and the Plasma
style, so they're not part of this.

**Approach.** Keep the Platinum QStyle as the one source of the look. Add
a small Qt Quick Controls style of our own that overrides only the
controls above and falls back to KDE's for everything else. The fallback
import is pinned to the version KDE exports, `import org.kde.desktop 1.0`
in our `qmldir`: with `auto` the loader asks for KDE's module at our own
version and the app doesn't open (finding 43).

Drawing: the overrides paint through the QStyle with a small C++ Qt Quick
item of our own (`QQuickPaintedItem` calling the application's QStyle;
public Qt API only). It hands the style what a widget would: menu row
position (first, last, separator), combo pop-up row, checked state, and so
on, through `QStyleOption::styleObject` properties the Platinum style
reads next to the `QMenu`/`QComboBox` pointers it uses today. That keeps
the measured first-row and last-row bevels (REFERENCE.md "Menu
highlight"), which KDE's own bridge can't pass on: it calls `CE_MenuItem`
without a widget (finding 45). The tooltip uses the same item with the
QStyle's tooltip drawing.

**Decided by the user (decision 13): that item.** The other choice was
KDE's private `StyleItem` bridge from `org.kde.qqc2desktopstyle.private` (less
code, but a private module this project would depend on, against the
"only officially supported theming hooks" rule; it can change with any KDE
Frameworks update, and it loses the row context above).

Colors, from the captures (finding 46):
- Menus, menu bar titles and combo pop-up rows: #333399 with white text,
  the measured bevel on first and last rows (`popup-open.png` (700,306),
  `menu-view-checked.png`), as the widget menus already draw it.
- List rows in ordinary views: #CCCCFF with black text, as in the file
  dialog list (`dialog-file-open.png` (780,341)).
- Finder's selected name (an inverted label, not a row) is a Finder
  look, not used here.
- Selection, keyboard focus and hover are kept apart: selection is the
  color above; keyboard focus gets the 1 px #6666CC ring the widget style
  draws (AUDIT.md finding 16); lists get no hover highlight (Mac OS 9
  had none); menu rows highlight under the pointer as menus do.

Switches keep everything that makes them switches (their role and checked
state for screen readers, Space to toggle); only the indicator is drawn
as a Platinum check box.

**When it's on** (finding 44). Two layers:
1. The login script sets `QT_QUICK_CONTROLS_STYLE` and adds our folder to
   `QML_IMPORT_PATH` only when `kdeglobals` `[KDE] widgetStyle` is
   `Platinum` at login, you haven't set the variable yourself, and KDE's
   module is the version our overrides were checked with. After a plain
   install (no switch) nothing changes.
2. Each override only takes effect while the running app's QStyle is
   Platinum (our C++ item reports it and follows style changes; the
   overrides use `Binding { when: ... }`, which puts KDE's own look back
   when it's false). So switching to Breeze in System Settings gives KDE's
   look straight away, in apps already running and in apps the session's
   launcher starts later with the old environment; the variable itself is
   gone from the next login.

Kirigami finds its color and size plugin by the style's name
(`kf6/kirigami/platform/<style>.so`). Codex's probe saw the same grid unit
and text color with and without a link to `org.kde.desktop.so`, but those
two values don't prove which plugin loaded. The spike settles whether the
link is needed. If it ships, install.sh gets a link kind of target (the
record keeps where it points; uninstall removes only that link), with
install tests; today the installer handles only files and folders.

Not chosen: patching or copying `org.kde.desktop` (57 files plus a
compiled plugin; breaks with every KDE Frameworks update), or the Union
style engine (the whole style would have to be redone in its format).

**Steps.**
1. **Spike, sandbox only.** (Done; combo rows and real pop-up windows in
   the nested KWin moved to steps 3 and 7.) A minimal style: `ToolTip` and `Menu`/
   `MenuItem` overrides drawn with our item, `import org.kde.desktop 1.0`.
   Check in `dev/kirigami.qml`, `dev/gallery.qml` and System Settings in
   the nested KWin (`dev/app-test.sh`), and in a Qt Quick app without
   KDE's platform theme (`QGuiApplication` only):
   - the app opens, and each control comes from where it should (ours
     marked; the others KDE's, e.g. a button background that is KDE's
     `KQuickStyleItem`);
   - Kirigami's colors and sizes, and which platform plugin loaded (Qt's
     plugin loader trace), with and without the link;
   - KDE's platform theme leaves an already-set `QT_QUICK_CONTROLS_STYLE`
     alone;
   - a selected first row, a selected last row, a separator and a combo
     pop-up row against the widget renders;
   - the `Binding` fallback: switching the QStyle at run time brings back
     KDE's look.
   Record the results in docs/FINDINGS.md. If the variable route or the
   fallback doesn't hold, stop and bring the options to the user.
2. **Inventory.** Render the galleries and a few System Settings pages,
   list every control from the list above that's visible and wrong, and
   pair each with its Mac OS 9 capture, with separate fixtures for
   ordinary views and for menus.
3. **Menus** (most visible): `Menu`, `MenuItem`, `MenuSeparator`,
   `MenuBar`, `MenuBarItem`, and the combo box's pop-up: our `ComboBox`
   keeps KDE's closed control and replaces only its `popup` and
   `delegate` (finding 47). Compare against the widget menu renders,
   which are already pixel exact.
4. **Tooltips**: the help balloon, as the widget tooltip draws it.
5. **Switches**: Platinum check boxes, switch behavior kept; check Space
   toggling and the accessible checked state.
6. **List rows and pop-ups**: #CCCCFF rows with black text, focus ring
   for keyboard focus; square pop-up, dialog and drawer frames like the
   widget ones.
7. **Checks**: Qt Quick regions in `dev/check-style.sh` rendered with
   `dev/build/quickshot`. A pop-up is a separate window by default and a
   window grab silently leaves it out (finding 48), so region tests set
   `popupType: Popup.Item` and assert the pop-up's own pixels are in the
   image; real pop-up windows are checked in the nested KWin. Sanitizer
   run; app pass with System Settings; activation cases: plain install,
   `--apply`, switching away in a running session, an app launched after
   that, next login.
8. **Packaging**: the style folder, our plugin and (if needed) the
   Kirigami link become install targets (record, checksums, uninstall);
   the login script's conditions as above. Install tests and the live
   test cover it.
9. **Audit and the user's on-screen review.**

**Risks.** The variable reaches every Qt Quick app in the session, KDE or
not (the spike's `QGuiApplication` case). KDE's controls we fall back to
can change with an update (the version guard turns our style off then).
Kirigami's own components keep Kirigami's shapes.

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
