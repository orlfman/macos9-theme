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
