# Verified platform findings

What Plasma 6.8.3, KWin, Union, Aurorae, and Qt 6.12 can and can't draw, as
verified in this project. Each entry says how it was checked. The user's
windows2000-union `docs/DEVELOPMENT.md` has more Union 6.8.2 facts (no
outlines or box-shadows in Qt Widgets, no dotted lines, stretched
`background-image`, no `:not()`, ...).

## Step 3 spikes (2026-11-20, Claude Code)

### Union can't draw scroll bar arrows in Qt Widgets apps

Checked with `spikes/scrollbar/probe.cpp`, which asks the active style for
the rectangles of a vertical scroll bar's parts, run in the sandbox:

| Style | Extent | Up arrow | Down arrow | Groove |
|-------|--------|----------|------------|--------|
| Union (breeze, 6.8.3) | 20 | 0×0 | 0×0 | 0×0 |
| Qt Windows | 16 | 16×16 at the top | 16×16 at the bottom | 16×268 |
| Qt Fusion | 14 | 16×14 at the top | 16×14 at the bottom | 16×272 |

Union's widget style gives the arrow areas no size at all, and its CSS has
only a `scrollbar > handle` element. Platinum scroll bars need two arrow
boxes at the bottom (Smart Scrolling), so Union alone can't do them.

### A C++ QStyle draws the Platinum scroll bar pixel for pixel

`spikes/scrollbar/platinum.cpp`: a QProxyStyle over Fusion that handles
vertical scroll bars (layout in `subControlRect`, drawing in
`drawComplexControl`), with the measured colors. Compared with
`tools/compare.py diff`:

- System Folder list (`scroll-vertical-inactive.png`, bar 16×347, thumb at
  the top): **0 of 5536 px differ**.
- Applications list (`disclosure-triangles.png`, bar 16×323, thumb partway
  down): **0 of 5152 px differ**.

The top row of each bar was left out: in the Finder it's the list header's
bottom line. Getting there took three fixes, all now in the code: the
thumb's right shadow starts one row below its top, every grip highlight
line starts with an `#EEEEEE` pixel, and the track (with its two shadow
rows) starts one row below the bar's own top edge.

Not checked yet: pressed arrow and dragged thumb against their captures
(colors are in the code from REFERENCE.md), horizontal bars, the inactive
bar, and real widgets in a running app.

### Aurorae can't do Platinum title bars

Read in `/usr/share/kwin/aurorae/aurorae.qml` (KWin 6.8.3): the title is a
`Text` item with `elide: Text.ElideRight` drawn over a fixed `FrameSvg`
background. So an Aurorae theme can't stop the pinstripes around the title,
squeeze a long title, or drop the title when it doesn't fit (all captured in
group 1); it would run the stripes under the text or show "…".

### A C++ title bar is pixel exact

`spikes/titlebar/titlebar.cpp` draws the frame, the 1 px drop shadow, the
close / zoom / collapse boxes (13×13, etched, 9×9 diagonal gradient
`#99`→`#FF` in 2 px steps) and the etched pinstripes with plain QPainter, as
a KDecoration3 plugin would. Title text and icon left out (no Charcoal).

- Mac OS window (`window-document-active.png`, 417 px wide): left of the
  title **0 of 3440 px**, right of it **0 of 3500 px** differ.
- Narrow long-title window (`window-long-title.png`, 289 px wide): left
  **0 of 920 px**; right **2 of 980 px**, both at the top of the drop-shadow
  column, where whatever is behind the window shows (white there, desktop
  in the spike). Same layout rules, so they aren't tuned to one width.

Layout rules found: boxes 4 px in from the left/right window edges and 4 px
down; pinstripes 6 white + 6 `#777777` rows, each gray row shifted 1 px
right; stripes start 5 px after the close box and end 5 px before the zoom
box; zoom and collapse boxes 3 px apart.

Not checked yet: the inactive title bar, pressed boxes, the title text
(font, condensing, dropping), the collapsed window, and the KDecoration3
plugin itself (the windows2000-union decoration shows the plugin side
works on 6.8).

### Not evaluated

Kvantum isn't installed here; it wasn't tested.

## Decoration plugin (2026-11-20, Claude Code)

### Wayland windows can't be shaded, so the collapse box is the minimize button

A probe in the plugin logged `window()->isShadeable()` as `0` for a Wayland
window in the nested KWin 6.8.3, so KDecoration never shows a Shade button
(layout letter `L`) there; the collapse box was missing in both the test
window and KWrite. The plugin draws both the Shade and the Minimize button
as the collapse box, and the Mac layout is `ButtonsOnLeft=X`,
`ButtonsOnRight=AI` (zoom, collapse). It looks identical; clicking it
minimizes instead of rolling the window up. Not checked: X11 apps, where
shading works.

### KWin's decoration preview: no button layout, no shadow, 1 px smaller

`org.kde.kwin.private.kdecoration` (used by `dev/decoration.qml`) has no
button layout setting (the `Settings` type exposes only `bridge`, `settings`,
`borderSizesIndex`) and ignores the sandbox kwinrc, so previews use KDE's
default buttons. It doesn't draw the drop shadow (the compositor does), and
a 416×246 item came out 415×245. Use it for inactive and pressed states;
check layout and shadow in the nested KWin (`dev/kwin-test.sh`,
`dev/app-test.sh` with `M9_DECORATION=platinum`).

## Menus in the Qt style (2026-11-21, Claude Code)

### QMenu honors contents margins, combo popups fill their items

- `QMenu` lays its items inside `PM_MenuPanelWidth` plus the widget's
  contents margins, so `setContentsMargins(0, 0, 1, 1)` makes room for the
  1 px drop shadow, and `WA_TranslucentBackground` keeps the shadow's two
  outer corners see-through. Forcing a QMenu narrower than its items with
  `setFixedWidth` does not relayout them (they overflow the frame); natural
  width is correct.
- `QComboBox`'s popup list (`QComboBoxPrivateContainer`, with
  `SH_ComboBox_Popup`) paints each item through a delegate that first fills
  it with the palette's window color, then calls `CE_MenuItem` with the
  combo box as the widget. A frame painted behind the list gets covered, so
  the style draws each item's slice of the bevel itself, knowing first and
  last item from the list's viewport height. The list view is created after
  its container is polished.
- Qt hides shortcuts in context menus by default on this platform
  (`QAction::isShortcutVisibleInContextMenu`); tests set it per action.

### Qt Quick apps follow the widget style (2026-11-21, Claude Code)

- KDE's platform theme picks the Qt Quick Controls style from
  `kdeglobals` `[KDE] widgetStyle`: `org.kde.union` when it is Union,
  otherwise `org.kde.desktop` (qqc2-desktop-style), which draws buttons,
  check boxes, radios, sliders, progress bars, fields, spin boxes, combo
  boxes, tabs, scroll bars and tool buttons through the application's
  QStyle. With `widgetStyle=Platinum`, System Settings and other Kirigami
  apps get the Platinum controls (checked in the sandbox: `kcm_mouse`,
  `kcm_style`, `dev/kirigami.qml`, `dev/gallery.qml`).
- Not drawn through the QStyle there: Qt Quick menus and tooltips (their
  own rounded panels with shadows), switches, Kirigami cards and the
  inline message's frame. `dev/run.sh` used to write `widgetStyle=Union`
  even with `QSTYLE=Platinum`, so Qt Quick apps in the sandbox and in the
  first live tests used Union; fixed 2026-11-21.
- Qt tooltips (`QTipLabel`) take `WA_TranslucentBackground` from
  `polish()`, and `SH_ToolTip_Mask` = 0 keeps the window unmasked, so a
  rounded balloon's corners stay see-through.

## Plasma (2026-11-21, Claude Code)

### What a top panel, the global menu and a global theme do

- A top panel touching the screen edges loses its top, left and right
  borders, so a panel background can't draw a white top row or rounded
  ends: the white row lives in the center piece (exact only at 20 px), and
  the ends are drawn by our own plasmoid (`platinum.menubarpiece`).
  On taller bars the widget widens both corners, anchors their bottom two
  rows to the bevel and repeats the divider grip. The desktop shell adds
  end padding to thick panels even when theme margins are zero. The end
  pieces offset their artwork into that padding (finding 23).
- Plasma gives panel applets the panel's full height; the panel
  background's margin hints didn't move them off the bottom rows. An open
  global menu title therefore draws the bar's black line itself.
- The global menu (`org.kde.plasma.appmenu`) draws titles with
  `widgets/menubaritem` and colors non-resting titles with the theme's
  highlighted text color; apps only hand their menus over while `kded6`'s
  appmenu module runs. A Plasma style's own `colors` file changes Plasma's
  colors without touching apps (used for white-on-`#333399` titles while
  apps keep the `#CCCCFF` text selection).
- Applying a global theme (`plasma-apply-lookandfeel`) writes its values
  into `~/.config/kdedefaults/` and clears the user's own overrides;
  startplasma puts that folder on `XDG_CONFIG_DIRS`. Of the decoration
  group only `library`, `theme` and `NoPlugin` are applied: the button
  order (`ButtonsOnLeft` / `ButtonsOnRight`) must be written by the
  installer. `xrdb` fails without X11 (harmless).
- Menus opened from the global menu sit 1 px below the bar's black line and
  1 px right of the title (Mac OS 9: on the black line, aligned); placed by
  Plasma, not reachable from the style.
- A bottom panel picks the `south-` elements of `widgets/panel-background`
  (falling back to the unprefixed ones), so the menu bar and the dock can
  look different with one Plasma style. The dock's apps (icontasks) also
  get the panel's full thickness, so the task frames carry their own inset
  (transparent margins inside the frame) to stay off the dock's border.
- `plasma-apply-lookandfeel` only sets a widget style Qt can find: on a
  first install the login script that adds our plugin folder hasn't run
  yet, so `install.sh --apply` passes `QT_PLUGIN_PATH` to it. Without a
  display it aborts (the install test uses `QT_QPA_PLATFORM=offscreen`).
- `systemctl --user` reaches the real user session even inside a private
  D-Bus session; tests need their own `XDG_RUNTIME_DIR` and a stand-in.


## Installing and undoing (2026-11-21, Claude Code, from Codex's audit)

- Applying a global theme with kded6 running makes Plasma's GTK sync
  (kded `gtkconfig`) rewrite `~/.config/gtk-3.0/{gtk.css,colors.css}`,
  `gtk-4.0/colors.css` (and `gtk.css`, `window_decorations.css`,
  `assets/` where present), `xsettingsd/xsettingsd.conf` and
  `~/.gtkrc-2.0`. Seen in `dev/test-install-live.sh`. Copying the files
  back doesn't make it sync again (no KConfig change notification); a
  re-login does.
- plasmashell writes its panel layout
  (`plasma-org.kde.plasma.desktop-appletsrc`) from memory, including when
  it quits. A layout file restored while it runs can be overwritten, so it
  has to be stopped first. `kquitapp6 plasmashell` stops it over the
  session bus. Restarting it rebuilds the restored panels on their
  screens, two screens included (live test).
- Plasma's scripting API puts a `new Panel` on screen 0. Moving it to
  another screen means setting `lastScreen` in the layout file while the
  shell is stopped.
- `libkdecorations3.so.6` keeps its soname across 6.x releases, so a
  decoration built for one version would still load into another. The
  login script compares the resolved library files with the ones it was
  built against and leaves the decoration off the plugin path when they
  differ.
- Qt's own styles don't swap a scroll bar's page and arrow parts when it's
  reversed (`invertedAppearance`, `upsideDown` in the option): clicking
  the track moves the thumb away from the click. Right-to-left horizontal
  bars aren't `upsideDown` at all; Qt mirrors them with `visualRect`.
- Qt sets `State_KeyboardFocusChange` only when focus moves by a real Tab
  key event (or a shortcut), not on `setFocus(Qt::TabFocusReason)` alone.
  Fusion draws no `PE_FrameFocusRect` for push buttons (its bevel does
  that), so a style that replaces the bevel has to draw it in
  `CE_PushButton`.

## Qt Quick style spike (2026-11-21, Claude Code)

Step 1 of PLAN.md "Plan: Qt Quick menus, tooltips and switches", in
`spikes/qtquick/`, sandbox only (`dev/run.sh`, software Qt Quick renderer,
and System Settings in the nested KWin). Qt 6.12, qqc2-desktop-style and
Kirigami 6.32.

- **Loading.** A style module with `import org.kde.desktop 1.0` in its
  `qmldir` and four overrides (`ToolTip`, `Menu`, `MenuItem`,
  `MenuSeparator`) loads; every other control is KDE's (a button's
  background is KDE's `KQuickStyleItem`). KDE's platform theme leaves an
  already-set `QT_QUICK_CONTROLS_STYLE` alone. System Settings runs with
  it (module loaded, no QML errors).
- **Kirigami needs the link.** Kirigami looks for
  `kf6/kirigami/platform/<style name>.so`. Without one it falls back to
  its basic theme: the colors come from the palette, but link, negative,
  positive, focus and hover colors are Breeze's, and the Complementary set
  is wrong (white instead of #333333). With `Platinum.so` linked to
  `org.kde.desktop.so`, all seven color sets and the units are identical
  to KDE's style.
- **Menus match the widget menus pixel for pixel.** A Qt Quick menu drawn
  through our C++ item (QQuickPaintedItem calling the QStyle) equals a
  widget `QMenu` with the same rows in 16,376 of 16,380 pixels, with the
  first and with the last row selected; the other 4 are see-through
  shadow corners in both. What it took:
  - the row's place passed to the style on `QStyleOption::styleObject`
    (`_platinum_first`, `_platinum_last`, `_platinum_combo`,
    `_platinum_shortcuts`), read only when there's no widget;
  - the menu's shortcut column (its widest shortcut) added to every row,
    as `QMenu` does;
  - each row painting its slice of the menu panel first, so text blends
    with the same pixels (on a transparent item it's antialiased
    differently);
  - `Menu.delegate` overridden too: KDE's `Menu` makes rows for actions
    and submenus with its own `MenuItem` (the same pattern as the combo
    box's pop-up);
  - the menu's height from its rows: KDE's list adds 1 px.
- **Following the app's style at run time** took two things:
  - `QApplication::setStyle()` tells only widgets (`QEvent::StyleChange`).
    One hidden, never shown `QWidget` hears it for all items.
  - KDE's parts are never replaced, only hidden with `opacity: 0` through
    a `Binding` (our item sits next to them). Qt hides an item it takes
    out of a control and doesn't show it again when it's put back. A
    `Binding` on `visible` doesn't work either: `visible` reads false
    while the pop-up is closed, and that's the value it restores.
  With both, switching to Fusion brings KDE's look back and switching back
  brings Platinum's, in a running app.
- **A plain Qt Quick app** (`QGuiApplication`, with or without KDE's
  platform theme) opens normally with the style set; it has no QStyle, so
  our items stay off and it looks as with KDE's style.
- **Captures.** Menus opened at the window's center whatever position was
  asked (`popupType` read back as 0), so the comparison finds the menu by
  its pixels in a window big enough to hold it.

## The Qt Quick Controls style (2026-11-21, Claude Code)

From building `style/quick` (PLAN.md "Plan: Qt Quick menus, tooltips and
switches", steps 2-5 and 7):

- **Inventory** (`dev/quick-inventory.qml`, before the style): wrong and
  visible were the menu bar, menus, the combo box's list, switches (also
  in list rows), the range slider, the dialog frame and the drawer edge.
  Already right: buttons, check boxes, radios, the closed combo box, group
  boxes, frames, and list selection (#CCCCFF with black text from the
  color scheme, as `dialog-file-open.png`). The busy indicator, page
  indicator and round button have no Mac OS 9 counterpart. Kirigami's own
  cards, inline messages and drawer highlight keep Kirigami's shapes.
- **KDE's ComboBox makes its list even when a derived type replaces
  `popup`**: both lists exist and the rows register with KDE's. So the
  style restyles KDE's list (as the Menu override does) and only replaces
  the rows (`delegate`).
- **Qt Quick menus size a row to the list only while the row has no width
  of its own**; binding a width stops that for good (and a Binding gives
  back a stale width when it ends).
- **A Binding element on a pop-up's `y` doesn't give the original binding
  back** when it ends (KDE's list stayed over the button after switching
  to Fusion); one `Qt.binding` that covers both looks does.
- **The widget tooltip's geometry** (`QTipLabel`): margin 1 +
  `PM_ToolTipLabelFrameWidth` on each side, a 1 px indent, and 1 px more
  width; text left-aligned in `QToolTip::font()` and `ToolTipText`. Drawn
  that way by our item, the Qt Quick tooltip equals the widget one. KDE's
  tooltip fades in (`enter` transition), so a shot right after opening it
  is still see-through.
- **quickshot's never-shown window has a 0x0 pop-up layer**, so menus and
  combo lists placed themselves at the window's center. Showing the window
  on the offscreen platform fixes it.
- **Pop-ups in a real session**: `popupType` reads 0 in a real Wayland
  window too, so Qt Quick menus, lists and tooltips are drawn inside the
  app's window unless an app asks for `Popup.Window`. A pop-up window gets
  its grab on Wayland only for an input event ("Failed to create grabbing
  popup ... has received input" otherwise, KDE's style as well), so tests
  open it from a real click (`dev/build/fakeinput`). Opened that way, a
  Platinum menu window draws its frame and shadow with see-through
  corners, but lands at the window's corner rather than where asked.
- **qInfo goes to the journal** when stderr isn't a terminal; tests that
  read Qt's own lines (`QtQuick style: ...`) set `QT_FORCE_STDERR_LOGGING=1`.
- **Switches stay switches**: with the Platinum style, Space still toggles
  `Switch` and `SwitchDelegate`, and screen readers get the same role and
  state as with KDE's style (`dev/quickkeys.cpp`).
- **Dialogs, drawers, range sliders** (2026-11-21): KDE's Qt Quick dialogs
  use the View colors, so their body is white, like the captured Mac OS 9
  dialogs; the plain modal frame (measured, `PE_PlatinumModalFrame`) fits
  them since an in-window dialog can't be dragged. The style draws the
  slider's groove and thumb only when `subControls` asks (QSlider asks for
  both), so a range slider gets one groove and two thumbs; KDE's hidden
  handles, given the thumb's size and the groove's 3 px inset as padding,
  sit exactly on the drawn thumbs. Qt's `RangeSlider` has a FINAL
  `horizontal` property (a derived type can't declare one). A drawer with
  its `enter` transition removed stays at position 0; tests set `position`.
- **The session keeps the login script's environment** (finding 49):
  Plasma's shell, KRunner and terminals started at login still name the
  Platinum Qt Quick style after uninstall, and a Qt Quick app started from
  them fails ("module Platinum is not installed") until the next login.
  uninstall.sh therefore leaves a pass-through module (just `import
  org.kde.desktop 1.0`) and Kirigami's link, removed by a one-shot login
  script at the next login.
- **A Binding element's `value` is evaluated even while `when` is false**;
  guard it, or it reads (and loops with) bindings of the look it isn't
  driving. While an app's style changes, our items flip one by one, so a
  value that reads rows also checks each row's own state. KDE's Menu still
  logs one binding loop of its own then (its list width), harmlessly.
- **sha256sum -c fails on an empty list**; a copy with no files has one
  (finding 50). The check compares the copy's files with the list instead,
  which also catches a list cut short.
- **Keyboard focus on sliders**: the Platinum slider showed none (widgets
  included), and a ring around the thumb would be cut off (the thumb fills
  the slider's height). Two #6666CC lines beside the focused thumb show it,
  also on Qt Quick sliders (KDE's bridge passes keyboard focus) and on each
  range slider handle (finding 52).
- **QComboBox's list width** (finding 53): the wider of the button and the
  combo box's width hint (its widest item text through `CT_ComboBox`), not
  the rows' own width. The Qt Quick list now asks the style the same way.
- **sha256sum escapes names** with a backslash or line break: a `\` before
  the line, `\\` and `\n` in the name (finding 57).
- **The pass-through after uninstall** (findings 54-56, 58) goes only where
  nothing is: not over a file or folder of the user's at the module's
  place, its login script under a free name, Kirigami's link only if none
  is there (and only a link it made is removed at the next login). A dry
  run counts what the real run will remove as free, unless something is put
  back there.

## GTK 3, GTK 4 and libadwaita discovery (2026-11-23, Antigravity / Gemini 4 Neon)

Verified in disposable `HOME` + `XDG_*` + private `dbus-run-session` runs via
`dev/gtk-discovery.sh broadway` (`dev/build/gtk-discovery-broadway.bT4yG8`) on
GTK 3.24.52, GTK 4.24.1, libadwaita 1.10.0, and `kde-gtk-config` 6.8.3.

- **Disposable isolation & `dconf`:** `HOME` and all `XDG_*` directories must
  be exported **before** launching `dbus-run-session` so `dconf-service` writes
  to `$XDG_CONFIG_HOME/dconf/user` instead of the user's real home. Verified
  write/readback (`DiscoveryDconf` -> reset `'Adwaita'`) inside the disposable
  home (`isolation.log`).
- **Named theme lookup & CSS precedence:**
  - Both GTK 3.24.52 and plain GTK 4.24.1 load named themes from
    `$XDG_DATA_HOME/themes/<Name>/gtk-{3,4}.0/gtk.css` via `gtk-theme-name` in
    `$XDG_CONFIG_HOME/gtk-{3,4}.0/settings.ini` (`DiscoveryIni` -> `#112233` /
    `#11aa33`), with zero CSS errors. (`$HOME/.themes/` also loads, though GTK
    4 logs a deprecation message.)
  - Unmodified libadwaita 1.10.0 (`AdwApplication`) forces `gtk-theme-name` to
    `Adwaita-empty` and ignores named themes completely (`#probe` and
    `#ind-theme` stay stock `#000006`).
  - Layer precedence verified on all three stacks with independent indicators
    (`#ind-theme`, `#ind-app`, `#ind-user`) and a competing `#probe` color:
    `user gtk.css` (`PRIORITY_USER` 800, `#abcdef`) > diagnostic app provider
    (`PRIORITY_APPLICATION` 600, `#654321`) > named theme (`PRIORITY_THEME`
    200, `#112233` on GTK 3 and plain GTK 4; not loaded on libadwaita).
  - Under `GdkBroadwayDisplay`, `settings.ini` drives named themes while
    GSettings `org.gnome.desktop.interface gtk-theme` and X11-only
    `xsettingsd.conf` are ignored on cold launch.
- **What `kded6` (`gtkconfig` 6.8.3) writes on select & global-theme reapply:**
  - `org.kde.GtkConfig.setGtkTheme` writes `gtk-theme-name` to five stores:
    `gtk-3.0/settings.ini` (`0600`), `gtk-4.0/settings.ini` (`0600`),
    `~/.gtkrc-2.0`, `xsettingsd/xsettingsd.conf`, and GSettings
    `org.gnome.desktop.interface gtk-theme` (in `$XDG_CONFIG_HOME/dconf/user`).
  - `kded6` creates regular files (no symlinks) for `gtk-3.0/{gtk.css,colors.css}`
    and `gtk-4.0/{gtk.css,colors.css}` containing `@import 'colors.css';` and 84
    `@define-color *_breeze` definitions (no generic selector or libadwaita
    `@window_*` overrides). Both GTK 3 and plain GTK 4 load `DiscoveryKde`
    cleanly while unmodified `AdwApplication` remains unaffected (`Adwaita-empty`,
    stock `#000006`).
  - Reapplying `platinum.desktop` (`plasma-apply-lookandfeel -a platinum.desktop`,
    with no synthetic `KGlobalSettings.notifyChange` signal) updates `colors.css`
    directly to Platinum colors (`#b1b1b1`, `#cc0000`, `#dddddd`) while
    preserving `gtk-theme-name=DiscoveryKde` in all five stores. When a user
    `gtk-4.0/gtk.css` already exists, `kded6` preserves its existing rules and
    appends `@import 'colors.css';` (and syncs `WhiteSur-lavender` /
    `macOS-cursors` across GTK 3/4/2/`xsettingsd` on the second reapply once
    `kdedefaults/` exists).
- **Live preference delivery & toolkit CSS limits:**
  - Even on `GdkBroadwayDisplay` without a Wayland portal, a running
    `AdwApplication` receives live `org.gnome.desktop.a11y.interface high-contrast`
    GSettings changes (`adw_hc` and `gtk-interface-contrast` toggled `0 -> 1 -> 0`
    with immediate `notify` callbacks), while `adw_sys_cs=0` and `adw_sys_acc=0`
    (accent stayed `blue` / `rgb(53,132,228)`).
  - Verified CSS boundaries on installed toolkits: GTK 3 `GtkEntry`/`GtkTextView`
    and GTK 4 `GtkTextView` ignore `border`/`outline`/`box-shadow` on `selection`
    (no hollow Mac OS 9 inactive selection outline via CSS); GTK 4 removed
    scrollbar steppers (`-GtkScrollbar-has-backward-stepper` is a parser error);
    GTK 3 rejects `@media (prefers-contrast: more)` (`unknown @ rule`);
    `AdwAccentColor` is fixed to 9 discrete enum values.
- **Native Wayland (`GdkWaylandDisplay`), dual Settings portals & live updates (verified in user terminal via `dev/gtk-discovery.sh plasma`, `dev/build/gtk-discovery-plasma.Qn9Pwd` — 38/38 PASS, 0 FAIL, 0 BLOCKED; initial discovery in `dxtZOy`):**
  - **Primary theme store on Wayland is GSettings, NOT `settings.ini`:** On
    `GdkWaylandDisplay`, GTK 3.24.52 and plain GTK 4.24.1 read
    `org.gnome.desktop.interface gtk-theme` from GSettings (whose schema default
    is `'Adwaita'`), completely overriding `gtk-{3,4}.0/settings.ini` when only
    `settings.ini` is edited (`theme=Adwaita` for `DiscoveryIni` in
    `settings.ini` alone; `theme=DiscoveryGSettings` -> `#223344`/`#22bb44` when
    set via GSettings alone). Under `GdkBroadwayDisplay` the reverse holds
    (`settings.ini` wins, GSettings is ignored). `kded6`'s
    `org.kde.GtkConfig.setGtkTheme` writes **both** GSettings and
    `settings.ini`/`.gtkrc-2.0`/`xsettingsd.conf`, so both GTK 3 and plain GTK 4
    load `DiscoveryKde` (`#123456`/`#1188ee`) on Wayland and survive
    `plasma-apply-lookandfeel -a platinum.desktop`. (Critical for Milestone 6:
    `uninstall.sh` MUST restore GSettings `org.gnome.desktop.interface gtk-theme`,
    not only `settings.ini`!)
  - **Dual Settings portal backends (`kde;gtk;`):** With
    `dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM`,
    both `org.freedesktop.impl.portal.desktop.kde` and
    `org.freedesktop.impl.portal.desktop.gtk` activate cleanly and own their bus
    names. `kde` supplies `org.freedesktop.appearance` `color-scheme` (`2` light
    for Platinum, `1` dark for BreezeDark), `accent-color` (`(0.8, 0.8, 1.0)` =
    `#CCCCFF` from `Platinum.colors` `[Colors:Selection] BackgroundNormal`), and
    `reduced-motion` (`0`), with no `contrast` key. `gtk` supplies `contrast`
    (`0` / `1` from GSettings `org.gnome.desktop.a11y.interface high-contrast`)
    plus `org.gnome.desktop.interface` and `org.gnome.desktop.a11y.interface`.
    The frontend `org.freedesktop.portal.Desktop` merges all four
    `org.freedesktop.appearance` keys cleanly (`portal.log`).
  - **Live preference delivery on already-running Wayland apps:**
    - `AdwApplication` (`watch-plasma-adw.log`): reports `adw_sys_cs=1`,
      `adw_sys_acc=1`. Under Platinum, `xdg-desktop-portal-kde`'s `(0.8, 0.8, 1.0)`
      maps to **`ADW_ACCENT_COLOR_PURPLE` (enum `7`, `rgb(145,65,172)` / `#9141AC`)**.
      Switching KDE color scheme `BreezeDark` ↔ `Platinum` (`plasma-apply-colorscheme`)
      flips `adw_dark` `0 → 1 → 0` and accent `purple(7) → blue(0) → purple(7)` live;
      toggling GSettings `high-contrast` flips `adw_hc` `0 → 1 → 0` live; calling
      `setGtkTheme` leaves `AdwApplication` untouched (`Adwaita-empty`).
    - Plain GTK 4 (`watch-plasma-gtk4.log`): receives live
      `gtk-interface-color-scheme` (`3 → 2 → 3`), `gtk-interface-contrast`
      (`1 → 2 → 1`), and `gtk-theme-name` (`DiscoveryKde → DiscoveryGSettingsLive`,
      `#123456 → #334455`) without restarting.
    - GTK 3 (`watch-plasma-gtk3.log`): `prefer_dark` remained `0` across all
      poll rows including `BreezeDark` (measured GTK 3 limitation: GTK 3.24.52
      does not map `org.freedesktop.appearance color-scheme` to
      `gtk-application-prefer-dark-theme`). Toggling GSettings `high-contrast`
      automatically switches a running GTK 3 app live to `HighContrast`
      (`#probe=#272c2e` in `Qn9Pwd`; `#929595` when `:backdrop` in `dxtZOy`)
      and back to `DiscoveryKde` (`#123456`); calling `setGtkTheme` switches
      live to `DiscoveryGSettingsLive` (`#334455`/`#33cc55`) and back to
      `DiscoveryKde` (`#123456`/`#1188ee`).
  - **FFmpeg Converter GTK (`dev/shots/gtk-discovery-ffmpeg-plasma.png`):**
    Launched cleanly on Wayland in light mode with zero breakage from KDE's
    `gtk-4.0/{gtk,colors}.css`. Distinguish the manager accent from rendered
    button pixels and active theme: `AdwStyleManager` reported
    `ADW_ACCENT_COLOR_PURPLE` (`enum=7`, `rgb(145,65,172)` / `#9141AC`), while
    the insensitive "Convert" button fill at `(900, 620)` rendered as
    `#C69ED3` (alpha-blended over the light `#FAFAFB` surface). In `Qn9Pwd`,
    FFmpeg launched after Step 5 had switched GSettings `gtk-theme` to
    `DiscoveryGSettingsLive` (which stock libadwaita ignores via
    `Adwaita-empty`); post-fix `session.sh` adds Step 6 to restore
    `DiscoveryKde` before launch, logs exact active settings, and records KWin
    window identity (`ffmpeg-window.log`). Note: FFmpeg's log contains an
    AT-SPI registry critical in the minimal virtual session, so accessibility
    behavior remains unverified.
  - **Virtual KWin renderer note:** Under `kwin_wayland --virtual`
    (`kwin_scene_opengl`), `AdwApplicationWindow` hit Wayland `Error 71` with
    GTK 4's default `radv` Vulkan renderer before running via `g_application_run()`
    + `GSK_RENDERER=cairo`; running `AdwApplication` through `g_application_run()`
    with `GSK_RENDERER=cairo` ran all trials cleanly.

In the 2026-11-23 re-test after the GTK discovery repairs, the second
Platinum reapply preserved the existing GTK 4 user rule and imported
KDE's generated colors. Cold launches of plain GTK 4 and Adw with the
resulting CSS both rendered the user marker as `#AA4499` and the marker
using `@error_color_breeze` as `#CC0000`. See the `kde-reapplied-user`
rows in `dev/build/gtk-discovery-plasma.celTLF/results.log` and
`dev/build/gtk-discovery-broadway.5RQc7I/results.log`.

## GTK 3.24 CSS engine behaviors (2026-11-23, Antigravity Gemini 4 Neon)

Verified during Milestone 2 and Milestone 3 Batch 1 (`gtk/Platinum/gtk-3.0/gtk.css`):

- **`border-image` ignores CSS `fill` and paints over `background-image`:** GTK 3.24.52 does not fill the center region of a `border-image` even when `fill` is specified; fill interiors with `background-color` + `background-clip: padding-box` while keeping outer corner cut-outs transparent. Because `border-image` paints *above* `background-image` on the same node, an opaque right-cap `border-image` (such as Platinum's pop-up button) hides any `background-image` on `button.combo`; placing the non-stretched 14×10 double-arrow PNG on the child `combobox button.combo arrow` node paints it cleanly on top at any natural height.
- **`GtkTreeView` `:selected:backdrop` requires a property change on `treeview.view:backdrop`:** In GTK 3.24.52, if `treeview.view:backdrop` computes the exact same style values as `treeview.view` (or is absent), GTK treats the `:backdrop` transition on `treeview.view` as a no-op and does not invalidate the cached transient row style for `treeview.view:selected:backdrop`, leaving selected rows in their active `#CCCCFF` color. Changing a non-intrusive property on `treeview.view:backdrop` (e.g., `border-color: #999999;` vs `@platinum_shadow` `#888888`, while the visible frame belongs to `scrolledwindow.frame`) forces invalidation so `treeview.view:selected:backdrop` renders `#DCDCEF` while keeping the pure `#FFFFFF` view background.
- **Global `label { color: ... }` specificity:** A top-level `label` rule overrides inherited `color` inside `menubar > menuitem:hover` and `menu > menuitem:hover` unless `menubar > menuitem label` and `menu > menuitem label` explicitly set `color: inherit;`.
- **Internal `GtkComboBox` children:** `gtk_container_get_children()` skips `GtkComboBox`'s internal `GtkToggleButton`; test harnesses must traverse with `gtk_container_forall()`.

The Batch 1 audit tested native GtkTreeView column sorting on GTK 3.24.52.
The header button's CSS node retains its ordinary class when the sort
indicator is enabled, and GTK displays the indicator in its child image
node. Platinum keeps that native glyph and offers the measured sorted
header through the explicit `.sorted` class. The natural gallery tests
the native indicator, while the reference crop exercises the explicit
class. GtkTreeMenu overflow arrows are direct `menu > arrow.top` and
`menu > arrow.bottom` nodes. Giving them explicit minima prevented the
Wayland popup's negative-dimension warnings.
