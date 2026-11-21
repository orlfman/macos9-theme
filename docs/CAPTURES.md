# Reference capture list

Everything to capture from the Mac OS 9.2.2 VM before the matching theme
part is built. Measurements go to `docs/REFERENCE.md`; the files go to
`reference/` (git-ignored).

## How to capture

- The user sets up each state in the VM; the agent runs
  `tools/capture.py <name>` when told it's ready. The agent can't click in
  the VM.
- **Pressed or dragging states** (mouse button held down): the user runs it
  themselves so they control the timing, e.g.

  ```bash
  python3 -I /home/pieman/Files/Archive/projects/macos9-theme/tools/capture.py --delay 5 <name>
  ```

  then switches to the VM and holds the button until the beep.
- Release the VM with **Ctrl+Alt+G** before Alt+Tab, or Alt+Tab gets typed
  into the focused field.
- Names: `<area>-<thing>-<state>`, lowercase, e.g.
  `window-document-inactive`. Never reuse a name; a retake gets a suffix
  (`-2`, `-clean`).
- Keep the Appearance settings at the defaults in `docs/REFERENCE.md`. Don't
  change Smart Scrolling, fonts, or colors during captures unless a row says
  so.
- One state per capture when practical; the whole screen is always saved,
  so several unrelated windows in one shot are fine as long as none overlaps
  the thing being captured.
- Tick the box (`[x]`) and add the file name when done; note anything odd.

Priority: **A** = needed for colors, decoration, and the application style
(do first). **B** = Plasma shell, menus, Finder look. **C** = polish.

## 1. Windows and title bars (A) — decoration

Use a Finder window (open the Mac OS hard disk) and a SimpleText window.

- [x] `window-document-active`: Finder window, front, with scroll bars and
      size box visible. Done 2026-11-20; content fits, so the scroll bars
      show no thumb (also serves as `scroll-nothing-to-scroll`).
- [x] `window-document-inactive`: same window behind another window.
      Done 2026-11-20 (deactivated by clicking the desktop).
- [x] `window-close-pressed`: hold the mouse on the close box (delay).
      Done 2026-11-20; cursor covers the box's lower-right corner.
- [x] `window-zoom-pressed`: hold on the zoom box (delay). Done
      2026-11-20; cursor covers the bottom edge, glyph visible.
- [x] `window-collapse-pressed`: hold on the collapse box (delay). Done
      2026-11-20; the window sits ~15 px lower/right than in the earlier
      shots (moved or zoomed between captures).
- [x] `window-collapsed`: window collapsed (window-shaded) to its title bar.
      Done 2026-11-20 (active, collapsed title bar only).
- [x] `window-long-title`: a window whose title is long enough to squeeze
      the pinstripes (rename a folder to something long and open it).
      Done 2026-11-20: 31-character folder name in a narrow window. The
      title is drawn **condensed** (tighter letter spacing) and the
      pinstripes shrink to a few px on each side; not truncated yet.
- [x] `window-long-title-2`: same window narrower still, until the title is
      truncated with "…" (does it condense first, then truncate? is there a
      minimum pinstripe width?). Done 2026-11-20 with a folder named
      `window-long-title-2` (0 items) in a very narrow window: the title
      text is **dropped entirely**, no "…"; the folder icon stays centered
      and pinstripes remain on both sides. Whether an ellipsis stage exists
      at in-between widths is not checked. Bonus: the inactive
      "This Is A Very Long Folder Name" window in the same shot shows a
      condensed inactive (gray) title.
- [x] `window-dragging`: drag a window by the title bar and hold (delay); is
      it a live move or an outline? Done 2026-11-20: **outline**, the
      window stays put. The outline is a 1 px dotted frame of the window's
      size made by inverting every other pixel (`#63639C` desktop →
      `#9C9C63`, exact RGB inversion), corner at (697,486). Whether KWin
      can do an outline move at all is still to check (FINDINGS).
- [x] `window-resizing`: drag the size box and hold (delay). Done
      2026-11-20: also an **outline** of the new size, same inverted-pixel
      dots, window unchanged until release. Not one rectangle: lines at
      y=487 (top) and y=508 (title bar bottom), and a double frame on the
      right/bottom (x=1377 and 1383, y=975 and 981), so the outer frame
      plus an inner rectangle 6 px in, i.e. a sketch of the window's frame
      and title bar. Left edge mostly hidden behind the window.
- [x] `window-simpletext`: a SimpleText document window (a non-Finder app
      window, for comparison). Done 2026-11-20: unsaved "untitled" has no
      title icon and no header; vertical scroll bar plus an empty
      horizontal bar strip; SimpleText's menus and the application menu
      (SimpleText) in the menu bar; three inactive Finder windows behind.
- [x] `window-simpletext-narrow`: the same window at its smallest. Done
      2026-11-20: SimpleText stops shrinking at about 140 px wide, where
      the short title "untitled" still fits with a few pixels of
      pinstripes, so the dropped-title case can't be reached here (an
      app minimum size, not a title rule).

## 2. Dialogs and alerts (A) — decoration + style

- [ ] `dialog-modal-alert`: Special > Empty Trash with something in the
      Trash ("are you sure" alert: caution icon, default + cancel buttons).
- [ ] `dialog-movable-modal`: a movable modal dialog with a title bar (e.g.
      SimpleText File > Save As, or Finder File > Get Info if it shows as
      one).
- [ ] `dialog-file-open`: SimpleText File > Open (Navigation Services
      dialog: list, pop-up, buttons).
- [ ] `dialog-get-info`: Finder File > Get Info on a file (Platinum
      window with pop-up, check boxes, text).
- [ ] `dialog-about-this-computer`: Apple menu > About This Computer
      (memory bars).

## 3. Buttons and toggles (A) — style

Most are in control panels: General Controls, Mouse, Keyboard, Monitors,
Sound, Memory, File Sharing, Date & Time, Appearance.

- [ ] `button-push-states`: a dialog with a default button (thick ring),
      a normal button, and a disabled button if possible.
- [ ] `button-push-pressed`: hold a normal push button (delay).
- [ ] `button-default-pressed`: hold the default button (delay).
- [ ] `checkbox-states`: checked, unchecked, disabled (General Controls,
      Memory, Appearance > Sound).
- [ ] `checkbox-pressed`: hold on a check box (delay).
- [ ] `checkbox-mixed`: a mixed (dash) check box, if one can be found (Get
      Info on several items, or Extensions Manager).
- [ ] `radio-states`: selected, unselected, disabled (General Controls,
      Memory, Monitors).
- [ ] `radio-pressed`: hold on a radio button (delay).
- [ ] `bevel-buttons`: bevel buttons (Control Strip popouts, Monitors, or
      Finder button view).
- [ ] `popup-closed`: pop-up menus closed (Appearance > Appearance tab
      already has three; get one disabled too: Appearance > Desktop
      "Position Automatically").
- [ ] `popup-open`: a pop-up menu held open (delay) with the current item
      checked.
- [ ] `little-arrows`: the up/down arrows next to a size box (already in
      `appearance-3-fonts-clean.png`; also capture one pressed, delay).
- [ ] `disclosure-triangles`: Finder list view with a folder closed and one
      open; also a triangle pressed (delay).

## 4. Scroll bars, sliders, progress (A) — style

Smart Scrolling is on (both arrows at one end, proportional thumb).

- [ ] `scroll-vertical-active`: Finder window with more items than fit,
      front window.
- [ ] `scroll-vertical-inactive`: same window inactive (no thumb, no arrows
      shown in Platinum?).
- [ ] `scroll-horizontal-active`: window wide enough content to need a
      horizontal bar.
- [ ] `scroll-nothing-to-scroll`: active window where all content fits
      (empty track?).
- [ ] `scroll-arrow-pressed`: hold the down arrow (delay).
- [ ] `scroll-thumb-dragging`: drag the scroll box and hold (delay); is
      there a ghost outline?
- [ ] `scroll-track-pressed`: hold in the track (delay).
- [ ] `slider-states`: sliders (Sound control panel volume, Mouse tracking
      speed, Keyboard repeat): horizontal, with tick marks if any.
- [ ] `slider-pressed`: drag a slider thumb and hold (delay).
- [ ] `progress-determinate`: copy a big file in the Finder (duplicate the
      Toast or Starcraft archive), capture mid-copy.
- [ ] `progress-indeterminate`: barber pole (start of a copy, "Preparing to
      copy", or Sherlock while searching).

## 5. Text, lists, tabs (A) — style

- [ ] `text-field-states`: an edit field focused (focus ring) and one not
      focused (Date & Time, File Sharing name fields, or Get Info comments).
- [ ] `text-selection`: text selected in a field and in SimpleText (Purple
      highlight color).
- [ ] `text-selection-inactive`: the same SimpleText window inactive
      (outlined selection?).
- [ ] `list-view-header`: Finder list view: column headers, sorted column
      highlighted, sort direction button.
- [ ] `list-view-selection`: Finder list view with one row selected, and
      the window inactive with a selection.
- [ ] `list-box`: a plain list box with a selection (Appearance > Desktop
      already has one; also Chooser or Extensions Manager).
- [ ] `tabs-states`: Appearance tabs (already captured); also a tab
      pressed (delay).
- [ ] `group-box`: a group box / separator (Memory, General Controls,
      Monitors).
- [ ] `window-header`: Finder window header ("N items, X MB available").

## 6. Menus (B) — style + Plasma

- [ ] `menubar-title-pressed`: a menu title held down in the menu bar
      (inverted title) with the menu open (delay).
- [ ] `menu-file-open`: Finder File menu open: enabled and disabled items,
      separators, ⌘ shortcuts.
- [ ] `menu-item-highlight`: mouse over an item while the menu is held open
      (delay): Lavender highlight.
- [ ] `menu-checkmark`: a menu with a checked item (View > as Icons /
      as List).
- [ ] `menu-submenu`: Apple menu > Control Panels submenu open (hierarchical
      arrow, submenu placement).
- [ ] `menu-apple`: Apple menu open.
- [ ] `menu-application`: application menu at the right end of the menu
      bar open (running apps list).
- [ ] `menu-contextual`: control-click on the desktop or a file
      (contextual menu).
- [ ] `menu-scrolling`: a menu too long for the screen, if one exists
      (scroll arrows in the menu).

## 7. Finder and desktop (B) — Plasma, icons

- [ ] `finder-icon-view`: icon view window with several items.
- [ ] `finder-icon-selected`: icons selected (icon darkening, name
      highlight) in a window and on the desktop.
- [ ] `finder-marquee`: drag a selection rectangle and hold (delay).
- [ ] `finder-button-view`: View > as Buttons.
- [ ] `finder-rename`: an icon name being edited.
- [ ] `finder-popup-window`: a pop-up window (tab at the bottom of the
      screen; View > as Pop-up Window), both closed tab and open.
- [ ] `finder-spring-loaded`: optional, a spring-loaded folder opening
      during a drag (delay).
- [ ] `desktop-pattern-tile`: the empty desktop (the 128×128 tile;
      `desktop-first-check.png` mostly covers it).
- [ ] `desktop-trash-full`: Trash icon empty and full.
- [ ] `control-strip`: Control Strip expanded, collapsed, and one module
      pop-up open.
- [ ] `launcher`: optional, Launcher control panel window.

## 8. Help, cursors, misc (C)

- [ ] `help-balloon`: Help > Show Balloons, hover something.
- [ ] `cursor-arrow`, `cursor-ibeam`, `cursor-watch`, `cursor-hand`,
      `cursor-crosshair`: the cursor is drawn into the framebuffer, so it
      shows in captures; position it over an empty area.
- [ ] `cursor-watch-frames`: several captures during a busy moment for the
      watch animation (C, optional).
- [ ] `alert-icons`: note, caution, and stop alert icons (measure only; the
      art can't be shipped).
- [ ] `sherlock`: Sherlock window (brushed-metal look is NOT Platinum;
      capture only to record the difference).
- [ ] `startup-screen`: optional, the "Welcome to Mac OS" startup screen
      and extension icons (for a splash screen idea); needs a VM restart,
      user's call.

## Not captured

- Sounds (can't ship Apple sounds; the Sound tab capture records which
  events had sounds).
- Apple artwork for reuse: captures are for measuring only.
