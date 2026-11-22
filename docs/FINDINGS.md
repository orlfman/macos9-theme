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

