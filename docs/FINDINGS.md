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

