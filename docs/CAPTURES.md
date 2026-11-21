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
- **States too short to time by hand** (a Finder copy's progress bar, an
  animation): the user runs a burst, which captures every 0.1 s and keeps
  each frame that changed as `<name>-001.png`, `-002`, ...:

  ```bash
  python3 -I /home/pieman/Files/Archive/projects/macos9-theme/tools/capture.py --delay 5 --burst 20 <name>
  ```

  then triggers the action in the VM during the burst. Afterwards the agent
  keeps the useful frames and deletes the rest (with their INDEX lines).
- **Menus and pop-ups stay open after one click** (Mac OS 8+ sticky
  menus): click to open, hover the item, Ctrl+Alt+G, and the agent
  captures. No `--delay` needed for open menus.
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
- Tick the box (`[x]`) and add the file name when done; `[~]` = partly
  done (the note says what's missing); note anything odd.

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

- [x] `dialog-save-changes`: SimpleText "Save changes … before closing?"
      alert. Done 2026-11-20: movable alert (pinstriped strip, no title),
      caution icon, Don't Save / Cancel / Save with the default ring on
      Save; menu titles dimmed except Help while it's up.
- [x] `dialog-save-as-standard-file`: SimpleText Save As, the classic
      Standard File dialog (folder pop-up, list with dimmed entries,
      Eject / Desktop / New, name field, format radio buttons). Done
      2026-11-20 (caught by accident; Navigation Services dialogs are
      still `dialog-file-open`).
- [x] `dialog-modal-alert`: Special > Empty Trash with something in the
      Trash. Done 2026-11-20: same movable-alert shape as
      `dialog-save-changes`, but the top strip is **red-tinted**: where the
      SimpleText alert has `#CCCCCC` / `#777777` / `#999999`, this one has
      `#FFCCCC` / `#FF6666` / `#FF9999` (same values with red forced to
      `FF`). Consistent and exact, so probably deliberate (a "danger"
      strip for irreversible actions?), but unconfirmed: compare with a
      screenshot from real hardware before relying on it. Bonus: full
      Trash icon, Apple menu icon dimmed while the alert is up.
- [x] `dialog-movable-modal`: a movable modal dialog with a title bar (e.g.
      SimpleText File > Save As, or Finder File > Get Info if it shows as
      one). Done 2026-11-20 with SimpleText Edit > Find: pinstriped drag
      strip without a title (same frame as `dialog-save-changes`), text
      field **without** a focus ring (classic Dialog Manager field), two
      check boxes, Cancel + default Find. The field reads "apple pie^": the
      `^` is the Alt+Tab artifact again; harmless for measuring.
- [x] `dialog-file-open`: SimpleText File > Open (Navigation Services
      dialog: list, pop-up, buttons). Done 2026-11-20: SimpleText uses the
      classic Standard File dialog with a QuickTime preview pane, not
      Navigation Services: plain modal frame (no title bar), folder pop-up,
      list in the large font with the selected row highlighted, Lavender
      scroll box, disabled Eject and Create buttons, default ring on Open,
      Show Preview check box. A Navigation Services dialog is still
      wanted (another app's Open).
- [x] `dialog-get-info`: Finder File > Get Info on a file (Platinum
      window with pop-up, check boxes, text). Done 2026-11-20 (Late
      Breaking News, an alias): close + collapse boxes but no zoom box;
      name field with selected text (highlight color); "Show:" pop-up in
      the large font and a smaller "Label:" pop-up; group box; empty
      comments field; check box; push button. Bonus: selected alias icon
      in the Finder (dark icon, white-on-black italic name), View menu
      dimmed.
- [x] `dialog-get-info-inactive` (extra, 2026-11-20): an inactive Get Info
      window (Applications folder) next to an active one: inactive pop-ups,
      labels, and group box drawn dimmed, title bar without pinstripes.
- [x] `dialog-about-this-computer`: Apple menu > About This Computer
      (memory bars). Done 2026-11-20: Lavender memory bars, a list with
      scroll bar, active window with close/zoom/collapse. Bonus: Apple
      System Profiler behind it, inactive: a row of small tabs, open and
      closed disclosure triangles, group boxes with the title on the frame
      line, and inactive scroll bars.

- [x] `list-view-profiler-applications` (extra, the user's idea): Apple
      System Profiler, Applications tab, active. Sorted column header and
      cells darker, active vertical scroll bar with the Lavender scroll box
      and grip, horizontal bar, small tabs, two-pane info area. Counts
      toward `list-view-header` and `scroll-vertical-active`; the Finder
      versions are still wanted.

## 3. Buttons and toggles (A) — style

Most are in control panels: General Controls, Mouse, Keyboard, Monitors,
Sound, Memory, File Sharing, Date & Time, Appearance.

- [x] `button-push-states`: a dialog with a default button (thick ring),
      a normal button, and a disabled button if possible. Covered by
      `dialog-file-open.png`: default Open, normal Desktop/Cancel,
      disabled Eject/Create (2026-11-20).
- [x] `button-push-pressed`: hold a normal push button (delay). Done
      2026-11-20 (SimpleText Find, Cancel): dark gray fill, white label.
- [x] `button-default-pressed`: hold the default button (delay). Done
      2026-11-20 (SimpleText Find): the button goes dark with a white label,
      the default ring around it stays as it was. The dialog moved and the
      field reads "Welcome^" (Alt+Tab artifact).
- [x] `checkbox-states`: checked, unchecked, disabled (General Controls,
      Memory, Appearance > Sound). Checked + unchecked in
      `controls-general-controls.png`, disabled (checked) in
      `controls-memory.png` (2026-11-20).
- [x] `checkbox-pressed`: hold on a check box (delay). Done 2026-11-20:
      unchecked box pressed = dark `#777777` fill with a reversed bevel.
- [ ] `checkbox-mixed` (optional, not found yet): a mixed (dash) check box, if one can be found (Get
      Info on several items, or Extensions Manager).
- [x] `radio-states`: selected, unselected, disabled (General Controls,
      Memory, Monitors). Selected + unselected in
      `controls-general-controls.png` and `controls-memory.png`; disabled
      in `controls-monitors.png` ("Grays").
- [x] `radio-pressed`: hold on a radio button (delay). Done 2026-11-20
      (second try, `--delay 10`): dark sphere with the shading reversed.
- [x] `bevel-buttons`: bevel buttons (Control Strip popouts, Monitors, or
      Finder button view). Done 2026-11-20 in `controls-monitors.png`
      (Monitors panel: one selected, one normal, plus the help button).
      Note: the user switched the VM to **1920×1080** here; later
      captures may be at that size (metrics are the same, it's still 1x).
- [x] `popup-closed` (normal in `appearance-2-appearance.png`, disabled
      "Position Automatically" in `appearance-4-desktop.png`): pop-up menus closed (Appearance > Appearance tab
      already has three; get one disabled too: Appearance > Desktop
      "Position Automatically").
- [x] `popup-open`: a pop-up menu held open (delay) with the current item
      checked. Done 2026-11-20 (Highlight Color, clicked open: Mac OS 9
      menus stay open after one click, no delay needed). Menu pops up
      over the control with the current item (Purple) at the control's
      position, check mark, color swatches, highlighted row.
- [x] `popup-open-no-hover` (extra): same menu with the pointer on the
      pop-up's arrow part instead of a row: no row highlighted, the arrow
      part drawn pressed (dark).
- [~] `little-arrows` (normal done; pressed skipped for now because
      pressing changes the setting at once): the up/down arrows next to a size box (already in
      `appearance-3-fonts-clean.png`; also capture one pressed, delay).
- [x] `disclosure-triangles`: Finder list view with a folder closed and one
      open; also a triangle pressed (delay). Closed + open done
      2026-11-20 (Applications list, SimCity2000 open); pressed in
      `triangle-pressed.png` (dark `#333399` fill, shadow gone). The same capture also has: an active Finder list with
      header, sorted column, sort direction button, **Lavender vertical and
      horizontal scroll boxes**, and an inactive Finder list window
      (Mac OS) whose triangles stay Lavender.

## 4. Scroll bars, sliders, progress (A) — style

Smart Scrolling is on (both arrows at one end, proportional thumb).

- [x] `scroll-vertical-active` (also in `disclosure-triangles.png`): Finder window with more items than fit,
      front window.
- [x] `scroll-vertical-inactive`: same window inactive (no thumb, no arrows
      shown in Platinum?). Done 2026-11-20: confirmed, an inactive window
      with overflowing content shows a flat empty `#EEEEEE` bar, no scroll
      box, no arrows. Active System Folder list alongside for comparison.
- [x] `scroll-horizontal-active` (in `disclosure-triangles.png`): window wide enough content to need a
      horizontal bar.
- [ ] `scroll-nothing-to-scroll`: active window where all content fits
      (empty track?).
- [x] `scroll-arrow-pressed`: hold the down arrow (delay). Done 2026-11-20
      (System Folder): arrow box goes dark, glyph stays black.
- [x] `scroll-thumb-dragging`: drag the scroll box and hold (delay); is
      there a ghost outline? Done 2026-11-20: no ghost; the scroll box
      darkens to `#6666CC` and the Finder list scrolls live. (Other apps
      might not scroll live; the Finder does.)
- [x] `scroll-track-pressed`: hold in the track (delay). Done 2026-11-20:
      no visual change to the track or scroll box, only paging.
- [x] `slider-states` (sliders with tick marks in
      `controls-general-controls.png`, a disabled one in
      `controls-memory.png`): sliders (Sound control panel volume, Mouse tracking
      speed, Keyboard repeat): horizontal, with tick marks if any.
- [x] `slider-pressed`: drag a slider thumb and hold (delay). Done
      2026-11-20: the real thumb stays and darkens to `#6666CC`; a gray
      ghost thumb follows the pointer (no live tracking).
- [~] `progress-copy-window` (burst, 2026-11-20): the Finder's "Copy to
      the Desktop" window, visible for under 0.3 s when duplicating
      Starcraft_BSNG.sit: collapse box only, empty progress bar (sunken
      gray trough), Stop button, closed "Time remaining" triangle. The bar
      never showed any fill; a longer copy is needed for a partly filled
      one.
- [x] `progress-determinate` (2026-11-20, burst while duplicating the
      625 MB Starcraft zip: `progress-determinate-early`, `-40`, `-55`,
      `-80`, and `-expanded` with the "Time remaining" details open): copy a big file in the Finder (duplicate the
      Toast or Starcraft archive), capture mid-copy.
- [x] `progress-indeterminate` (2026-11-20, burst during a Sherlock 2
      search; two frames, `-a` and `-b`, 4 px apart in the animation): barber pole (start of a copy, "Preparing to
      copy", or Sherlock while searching).

## 5. Text, lists, tabs (A) — style

- [ ] `text-field-states`: an edit field focused (focus ring) and one not
      focused (Date & Time, File Sharing name fields, or Get Info comments).
- [ ] `text-selection`: text selected in a field and in SimpleText (Purple
      highlight color).
- [ ] `text-selection-inactive`: the same SimpleText window inactive
      (outlined selection?).
- [x] `list-view-header` (Finder version in `disclosure-triangles.png`): Finder list view: column headers, sorted column
      highlighted, sort direction button.
- [ ] `list-view-selection`: Finder list view with one row selected, and
      the window inactive with a selection.
- [ ] `list-box`: a plain list box with a selection (Appearance > Desktop
      already has one; also Chooser or Extensions Manager).
- [ ] `tabs-states`: Appearance tabs (already captured); also a tab
      pressed (delay).
- [x] `group-box` (titled group boxes, title on the frame line, in
      `controls-general-controls.png`): a group box / separator (Memory, General Controls,
      Monitors).
- [ ] `window-header`: Finder window header ("N items, X MB available").

## 6. Menus (B) — style + Plasma

- [x] `menubar-title-pressed` (in `menu-file-open.png`): a menu title held down in the menu bar
      (inverted title) with the menu open (delay).
- [x] `menu-file-open` (caught in the copy burst, 2026-11-20; no item
      highlighted, pointer on Duplicate): Finder File menu open: enabled and disabled items,
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
