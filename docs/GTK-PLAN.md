# Platinum for GTK 3, GTK 4 and libadwaita

## Target and scope

Target the host versions observed on 2026-11-23: GTK 3.24.52, GTK 4.24.1 and libadwaita 1.10.0. Implement named Platinum stylesheets for GTK 3 and plain GTK 4. For libadwaita, first establish which desktop appearance settings reach an unmodified application on Plasma. Keep its adaptive layouts, application-defined colors and accessibility preferences functional. Treat native applications as the initial release target. Record Flatpak results separately because runtimes and theme availability can differ.

## Milestones

1. **Prove theme discovery and establish a baseline.** In the project's disposable Plasma session, launch one process per stack under fresh XDG directories. Capture the stock controls, select a temporary named theme through Plasma's GTK settings and relaunch. Run the layer and setting-store controls below for each stack. Record the actual theme search path, setting and rendered result, including after global-theme reapplication with kded6 running. A process-local override is useful for diagnosis. Acceptance requires the normal launch path. Record the observed behavior in FINDINGS.md.
2. **Build one GTK 3 vertical slice.** Start with a dialog containing a normal button, default button, text entry, checkbox and radio button. Use the measured palette, border layers, lavender controls and purple text selection from REFERENCE.md. Check normal, pressed, insensitive, mixed and keyboard-focus states where applicable. Match reference crops at 1× with compare.py and record the remaining differences. Use original CSS and generated geometry. Keep native text metrics and usable hit areas where enforcing classic dimensions would clip text.
3. **Extend GTK 3 coverage.** Add menus, lists and selection, notebook tabs, scales, scrollbars, progress bars, tooltips and dialogs in small batches. Verify GTK 3 stepper clicks in classic scrollbar mode and test overlay scrolling separately. Exercise client-side header bars separately from KWin-decorated windows, including active, backdrop and maximized states. Use a real GTK 3 application alongside the gallery before marking each batch ready.
4. **Port the same slice and batches to plain GTK 4.** Share measured values and original assets. Keep GTK 4 selectors and widget structure in their own stylesheet. Inspect the installed toolkit's CSS nodes, especially popovers, list views and scrollbars. Record any missing control or interaction as a platform limitation. Prove the same fixture loads through standard named-theme discovery and that an ordinary GTK 4 app picks it up.
5. **Verify libadwaita appearance integration.** Use a minimal PyGObject AdwApplication with stock controls and zero application CSS as the toolkit baseline. Compare FFmpeg Converter GTK alongside it for application compatibility. Check the desktop light/dark preference, accent propagation where exposed, high contrast, focus, destructive actions, disabled controls, header bars, dialogs and narrow layouts. Record what the portal advertises, what AdwStyleManager reports and what appears on screen. Report the closest supported accent if exact Lavender is unavailable. Application-owned CSS through AdwApplication is a separate option for an app whose author opts in. Keep that outside the desktop theme milestone. Report coverage per feature before promising Platinum widget shapes.
6. **Integrate installation and undo.** Package the verified GTK 3 and GTK 4 named stylesheets under the proven user theme path. Reuse the installer's manifest, backup and rollback handling. Keep installing theme files distinct from selecting Platinum. Exercise fresh install, upgrade from the current release, reinstall, interrupted apply, switching to another GTK theme and uninstall. Seed existing GTK settings and CSS, run kded6 through apply and undo, then verify byte-for-byte restoration of pre-existing files, preservation of later user choices and the existing WhiteSur icon selection. Document the selection mechanism only after milestone 1 proves it.
7. **Release check.** Extend the screenshot command introduced with the first GTK 3 dialog. Fail on CSS parser errors. Compare reference crops at 100%, then inspect clipping, crispness and keyboard focus at 150% and 200%. Keep baselines per toolkit and distinguish exact reference pixels from known differences in AUDIT.md. Run the project's existing widget, Quick, Plasma, icon and install/undo suites. Obtain user visual review before closing GTK support.

## Milestone 1 decision and evidence

Claim gtk and shared. Create a tiny GTK 3 fixture, plain GTK 4 fixture and stock AdwApplication. Record three stock screenshots and cold-launch GtkSettings values. For the Adw fixture also log AdwStyleManager effective dark, high contrast and accent on launch and after preference changes. FFmpeg Converter GTK has its own CSS and drawing code. Check it as an application after the baseline. Record the actual libadwaita accent enum and RGBA.

1. Use a disposable HOME and all XDG directories **before** starting the private session bus, following dev/test-install-live.sh. Check a disposable dconf write and readback. Inside virtual KWin publish its WAYLAND_DISPLAY, XDG_CURRENT_DESKTOP and QT_QPA_PLATFORM to that private bus activation environment before activating either portal. Check the frontend Settings API, bus owners and direct Settings replies from both KDE and GTK backends. Exercise color scheme and contrast separately. Trace each change from source to backend to frontend to the fixture. A missing key is an unsupported result only after verifying the responsible backend responds.
2. Capture stock fallback. Use different theme names in isolated settings.ini, GSettings and applicable XSettings trials, then exercise KDE's GtkConfig selection with kded6 running. Log the active display backend and effective name. Use distinct markers in the named stylesheet, diagnostic fixture's application provider and disposable user CSS. Run each alone and then in conflict on the same property, retaining separate visible indicators for loaded layers. Remove diagnostic providers and overrides for the normal launch. Inspect actual GTK CSS imports and link targets before selection, after selection and after reapplying the global theme. Compare plain GTK 4 and clean Adw under the same configuration.
3. **Pass** when each stack's baseline, source of styling and preference results are explainable across normal selection and reapply. A verified toolkit limitation is a valid result. **Fail** on unexplained precedence or an observed integration regression. **Blocked** identifies an unavailable prerequisite or a backend that fails to start. Broadway can exercise fixture and CSS controls in isolation. When the sandbox denies virtual KWin, run the disposable compositor test in the user's terminal and leave those rows pending until it runs.

Publish the result matrix and private or ignored screenshot paths. Milestone 1 ends here. Start the measured GTK 3 dialog in milestone 2 after the discovery result passes.

## Visual acceptance for milestones 2–5 and 7

Build a GTK screenshot and widget-crop command with the first dialog. At 1× use fixed geometry and zero differing pixels on equal-sized chrome regions. The table uses x,y,width,height in reference pixels. For buttons use the cursor-free bands in dev/check-style.sh. Run natural-size fixtures separately for text clipping, keyboard focus and hit areas.

| State | Reference | Crop and comparison |
|---|---|---|
| Normal button | button-default-pressed.png | 617,513,70,20; four outer 4 px bands |
| Pressed button | button-push-pressed.png | 641,469,70,20; use push-pressed band exclusions |
| Default button | dialog-file-open.png | 848,435,86,26; use push-default bands |
| Entry, unfocused / focused | appearance-3-fonts-clean.png | 846,346,30,26 / 846,432,30,26; outer 5 px bands |
| Checkbox, off / on | controls-general-controls.png | 550,327,14,12 / 550,280,14,12 |
| Radio, off / on | controls-general-controls.png | 553,534,12,12 / 553,552,12,12 |

Test active selection fill against the measured #CCCCFF. On real window deactivation check readable muted backdrop selection. The hollow Mac inactive text selection is a documented gap for GTK 3 and GTK 4 text views. Mark mixed checkbox, focused button/check/radio, pressed-on check/radio, disabled default button and disabled entry TBD for reference fidelity until captured. Functional checks can run immediately.

GTK 4 scrollbars lack steppers. Preserve scrolling and keyboard operation. GTK 3 overlay scrolling cannot guarantee a permanent classic gutter. Exercise HighContrast theme switching on GTK 3 and prefers-contrast rules on GTK 4. For client-side header bars preserve app controls, button layout and natural height. Test narrow widths and maximization. Record the resulting title-bar differences. Set 150% and 200% on the virtual output with kscreen-doctor and verify its reported scale. Inspect compositor output at both scales, including GTK 3 downsampling at 150%. Log the GTK 4 surface scale and actual render result. Keep pixel-exact comparisons at 1×.

## Milestone 4 initial slice

Platinum's named GTK 4 stylesheet shares the GTK 3 palette and measured artwork.
The first slice covers framed buttons with labels or custom children, default
buttons, entries, checkboxes and grouped check buttons. The named theme
imports GTK's default resources for widgets outside the slice. GTK's dark and high-contrast styles take over when
their corresponding preference is active. The stylesheet targets GTK 4.20+
for CSS media queries and was tested with GTK 4.24.1. [GTK CSS media queries](https://docs.gtk.org/gtk4/css-properties.html#media-queries).

Run `dev/check-gtk4.sh broadway` for the 1× reference crops and control checks
using Cairo and `settings.ini`. Run `dev/check-gtk4.sh plasma` for the same
checks in nested Wayland using the default GTK renderer and GSettings theme
selection. Wayland also verifies actual window deactivation, focus reassignment
while inactive, a live high-contrast round trip in one window, Widget Factory
against Adwaita, and exact comparisons with stock button groups and toolbars.
Compositor captures cover layout at 150% and 200%, plus exact indicator artwork
at 200%. Each run prints its disposable evidence
directory.

## Milestone 4 menus, dropdowns and lists

The named GTK 4 theme now styles GtkPopoverMenuBar, model-backed popover menus,
GtkDropDown, GtkListView and GtkColumnView in light mode. It reuses the measured
GTK 3 menu sprites and generates filtered frame slices for dropdowns and column
headers. GTK controls row height, search, focus, sorting, scrolling and submenu
navigation. Sorted columns retain GTK’s direction indicator. GTK 4.24.1 exposes
the sort class on that child only, so the header keeps its normal face after a
sort. GTK’s native popover pointer and submenu page navigation are retained.

The same `dev/check-gtk4.sh` commands now cover this batch. Wayland checks
43-item dropdown overflow, filtering and selection, checked and radio menu
actions, submenu navigation, native sorting, list scrolling and actual backdrop
selection. The GTK Settings demo renders the measured header corner and Lavender
row under normal named-theme selection. The 150% and 200% compositor captures
cover the additional gallery. The 200% dropdown arrow matches the doubled 1×
reference exactly. The audit records the virtual compositor's buffer limitation.

## Milestone 4 tabs, scales, progress bars and scrollbars

`gtk-4.0/tabs-ranges.css` ports the measured GTK 3 notebook, scale, progress
and scrollbar rules to GTK 4's nodes. GTK 4 draws a top notebook's pane after
its header, so the header paints the pane's first three rows and the tabs
cover them; bottom tabs keep the GTK 3 overlap. GTK 4 has no scrollbar
steppers, so the Smart Scrolling arrows are left out rather than drawn as
inert areas; the trough runs to the end of the bar. Overlay indicators keep
the compact Lavender bar and expand to the classic bar while hovered.

GTK 4 samples past nine-slice strips whenever it scales them. Guarded GTK 4
variants copy each stretch strip into the inner edge of both neighboring
slices (`guard_strip` in `gtk/gen-assets.py`), which keeps 1× pixel-exact on
Cairo and Vulkan and avoids seams at 150%.

`dev/check-gtk4.sh` gains a `ranges` fixture. Both backends compare the GTK 3
Batch 2 reference crops (scrollbars minus the 31 px of arrows, sliders, three
tab rows and the pane, progress and barber pole), bottom tabs against the
mirrored top tabs, reversed and tiny fills, the disabled well, the overlay
indicator and hover state, and GTK's own slider, notebook and scroll actions.
Wayland adds the real backdrop and a compact layout at 150% and 200%; at 200%
the tab bands, slider and progress equal the doubled references.

## Milestone 4 header bars, tooltips and alerts

On Plasma, GTK 4 windows without a header bar use KWin's server-side Platinum
decoration. Apps that set a GtkHeaderBar draw their own title bar, so
`gtk-4.0/windows.css` redraws those windows as the decoration does: the 6 px
frame with its hard shadow, the 22-row title bar with etched pinstripes and
13 px close, zoom and collapse boxes (none on inactive bars), a flat inactive
look, and a frameless maximized or tiled bar. `gen-assets.py` renders the
frame and title-bar slices with a Python port of the decoration's
`paintFrame()`. App widgets share the box row; stripes show only in the gaps.
Tooltips use the Help Balloon outline. GtkAlertDialog is the movable alert
from `dialog-save-changes.png`: the pinstriped drag strip, `#DDDDDD` ring and
bevels around a white body (the strip cannot be dragged; GTK gives alerts no
drag area).

`dev/check-gtk4.sh` gains a `windows` fixture. Both backends check the balloon
outline against `help-balloon.png` and the title-bar metrics. Wayland compares
compositor captures of an active, inactive and maximized header-bar window
with `window-document-active/inactive.png`, including the stripe ends around
the title, an app bar with push buttons, the alert frame against
`dialog-save-changes.png`, the zoom and close actions, and 150%/200% output.

## Milestone 4 menu buttons and level bars

`gtk-4.0/menubuttons-levels.css`: GtkMenuButton uses the measured push-button
frame, pressed while its menu is open, with the submenu triangle turned to
point down (generated GTK 4 assets). GtkLevelBar uses the progress tube; low,
high and full levels all fill with Lavender, and discrete levels are separate
segments. Continuous fills stop 3 px short of their value so the tube's
shadow always stays inside the trough (user's choice, audit #248); each level
bar equals a progress bar filled 3 px less.

The installer packages GTK 4 alongside GTK 3 (see below). Remaining: user
review on the desktop, automatic selection, then libadwaita (step 5).

## Milestone 5 libadwaita (started 2026-11-25)

Harness: `dev/check-adw.sh` (DEVELOPMENT.md). Result per feature, Plasma
path, unmodified app, no layer:

| Feature | Reaches libadwaita | On screen |
|---|---|---|
| Named theme (Platinum) | no (`Adwaita-empty`) | Adwaita shapes and colors |
| Light/dark preference | yes (portal `color-scheme`) | light |
| Accent | yes, snapped to 9 values | purple #9141AC, not Lavender |
| High contrast | yes (`adw_hc=1`) | libadwaita HC |
| Focus, destructive, disabled, header bar, alert dialog, narrow breakpoint | stock behaviour | Adwaita look, accent purple |

**Scope decided 2026-11-25 (user): colors and shapes** (PLAN.md decision 15).

`gtk-4.0/libadwaita.css` is loaded from the user stylesheet with
`@import url("file://<theme dir>/gtk-4.0/libadwaita.css");`. Inside the
light, normal-contrast media block it imports `adw-colors.css` (libadwaita's
CSS variables in the Platinum palette), the five plain GTK 4 component files,
and `adw-widgets.css` (libadwaita-only shapes). At user priority every rule
wins over libadwaita regardless of specificity; only properties our rules
leave unset keep libadwaita's values.

| libadwaita feature | Under the layer |
|---|---|
| Push, suggested (default ring), destructive, pill buttons | Platinum push / default buttons; destructive is a plain push button |
| Framed icon buttons | small square bevel button (Help toolbar, normal measured, pressed derived) |
| Header bar (`AdwHeaderBar`, `AdwToolbarView`) | plain GTK 4 Platinum title bar (pinstripes, boxes at the edges, #256); an empty title widget leaves a plain gap in the stripes (no `:empty` in GTK CSS) |
| Entry, check, radio, progress, scale, dropdown | plain GTK 4 Platinum controls |
| Switch | the Platinum check box (as the Qt Quick style) |
| Boxed lists, cards (`AdwPreferencesGroup`, rows) | list box: 1 px black frame on white, square |
| `AdwAlertDialog` (in window or parentless), `AdwMessageDialog` (zenity) | the movable alert, white body, no dimming (#257) |
| Floating dialogs (`AdwPreferencesDialog`, `AdwAboutDialog`) | document window frame, close box 4 px in (#260); bottom sheets not done |
| Spin button +/- | Platinum entry field + Platinum arrow boxes side by side (#267; GTK can't stack them like the little arrows) |
| View switcher, tab bar, sidebar, toasts, banners, status pages, `AdwPreferencesDialog`, `AdwAboutDialog` | colors only, not yet checked |
| Dark, high contrast | libadwaita's own (verified identical to stock) |

Checked: `dev/check-adw.sh` fixture runs and real apps (FFmpeg Converter GTK,
Mission Center, Faugus Launcher, zenity). FFmpeg Converter's path fields are
its own breadcrumb widget and stay app-drawn. Plain GTK 4 with the layer:
`GTK4_CHECK_ADW_LAYER=1 dev/check-gtk4.sh`, broadway 149/149; plasma 220/222,
the two failures being the Adwaita-control comparisons that the layer turns
Platinum (the consequence in decision 15). Not checked: 150 %/200 %, Flatpak,
user review. Installed (2026-11-25): `install.sh` adds a marked
`@import` line at the top of `~/.config/gtk-4.0/gtk.css` on `--apply`, or on a
reinstall while Platinum is the global theme (`gtk_theme.py adw-import add`,
idempotent, keeps the file's mode and other rules, refuses links; the config
preflight already stops on a linked `gtk.css`). `uninstall.sh` restores the
pre-switch copy and then removes our line if still there, unless the GTK 4
theme stays installed because Platinum is still selected. With the real kded
GTK sync the line stays first and kded appends `@import 'colors.css';`
(`test-install-live`). Next: the user's live findings.

Plain GTK 4 `GtkComboBox` (gtkmm apps such as pavucontrol) is drawn as the
pop-up menu like `GtkDropDown` (#259, `menus-lists.css`); combo boxes with an
entry are not styled yet.

## Installer contract for milestone 6

GTK 3 and GTK 4 file packaging and manifest-based undo are implemented in the main scripts. The installed `gtk-4.0` folder stands alone: `scripts/gtk_theme.py self-contain` copies the GTK 3 artwork and palette it uses into `gtk-4.0/assets/gtk3/` and `gtk-4.0/palette.css` and rewrites its links. A selection in any GTK store, or an inherited `GTK_THEME`, keeps both toolkit folders on uninstall. Undo carries forward a widget-theme name chosen after `--apply`: Plasma's GTK sync never changes that name, so a value that differs from the pre-install copy is the user's, including a removed key (`gtk_theme.py later-choices`/`carry`, #249, #251); a missing key the sync fills in with the name the other stores already held is not. The list is saved to `$state/gtk-later-choices` before any file is put back and reused when an interrupted undo is resumed (#252). Launching an app with `GTK_THEME=Platinum` loads the installed theme. Automatic selection is still pending.

Claim packaging before changing the scripts. A plain upgrade installs the named theme files and preserves the current GTK widget-theme choice. Enable selection on explicit apply only after milestone 1 demonstrates a viable route and the following recovery tests pass.

- Under the existing installer lock, journal pre-adoption values, unset versus explicit keys, original file contents/link metadata and intended changes before mutation. Track GTK 3 and 4 settings.ini, GTK 2 gtkrc, xsettingsd and the GSettings gtk-theme user value. Use isolated persistent dconf for tests. Capture generated CSS/imports and the post-apply state so undo can identify subsequent edits. Share the existing icon transaction's ownership rules for icon keys.
- Integrate with the whole-file backup restoration path. Stage a restore that reverts still-owned theme keys and generated imports/colors while carrying forward later widget-theme choices, icon choices, unrelated keys and CSS edits. Restore untouched files byte for byte. If generated and user CSS edits overlap ambiguously, preserve the user's version and report the conflict. Keep legacy backups intact and distinguish the original desktop backup from the GTK adoption snapshot.
- Preflight gtk.css and assets symlinks before changes. Preserve existing link identity and target contents. If the implementation cannot safely manage a link, report the specific path and stop activation before mutation. Before removing the theme directory, resolve surviving selections in all five stores. Preserve resources still selected or report an unresolved store and defer removal.
- Exercise the current Platinum + WhiteSur install with a legacy backup, plain upgrade, explicit adoption, later switch to another GTK theme and edit gtk.css, then undo. Verify all five stores, later edits, original icon recovery or a later icon choice, and the next normal app launch. Repeat with untouched files, pre-existing symlinks and interruptions before/after selection, before journal completion and during undo. Reinstall and retry must converge on the documented result.

## References

- Project measurements and sandbox: docs/REFERENCE.md, docs/DEVELOPMENT.md and the kded GTK-sync observations in docs/FINDINGS.md.
- [GTK 3 CSS provider and theme lookup](https://docs.gtk.org/gtk3/class.CssProvider.html)
- [GTK 4 CSS provider and theme lookup](https://docs.gtk.org/gtk4/class.CssProvider.html)
- [libadwaita styles and appearance](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/styles-and-appearance.html). Check API availability against the installed version.
