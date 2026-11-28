# Plan: Platinum Kirigami navigation tabs (AUDIT #342)

Draft by Claude Code (Opus 5.5), 2026-11-27.

**Decision, 2026-11-27.** The user chose option 3. The Window Behavior
page buttons keep KDE’s styling as a documented limitation. The
[review findings](../AUDIT.md#2026-11-27-codex-gpt-6--review-the-kirigami-navigation-tab-plan)
are retained for reference.

## Problem

System Settings > Window Behavior shows four icon-over-text buttons at the
top (Focus, Titlebar Actions, Window Actions, Movement & Placement). They
look like KDE, not Platinum: a light lavender tint with rounded corners
when hovered or selected, a slightly stronger tint while pressed, and no
bevel or push-in. The user's screenshot:
`~/Pictures/Screenshots/Screenshot_20261126_220546.png` (copy into
`reference/testing/` with the AUDIT number when this is picked up).

Ordinary flat Qt Quick buttons are not affected: a flat `ToolButton` and a
flat `Button` already draw the Platinum pressed bevel (sandbox probe,
2026-11-27).

## Cause

- The page (`kcm_kwinoptions`, kwin 6.8.3) uses `Kirigami.NavigationTabBar`.
- Its buttons are Kirigami's own `controls/NavigationTabButton.qml`
  (kirigami 6.32.0). The background is two `Rectangle`s with colors from
  `Kirigami.Theme.highlightColor` (20% hovered or checked, 30% down). There
  is no `StyleItem` and no QStyle call.
- It is a Kirigami type, not a Qt Quick Controls type, so our module
  (`style/quick/Platinum`, selected by `QT_QUICK_CONTROLS_STYLE`) can't
  replace it the way it replaces ScrollBar or Switch.
- Details: `docs/FINDINGS.md`, "Kirigami NavigationTabButton ignores the
  QStyle".

## Scope

On this machine only `kcm_kwinoptions` uses `NavigationTabBar` (a search
of the system KCMs, `/usr/bin` and `/usr/lib/qt6/qml` outside Kirigami).
Other KDE apps can use it in the future, mobile-style apps most of all.

## The official hook

Kirigami's `StyleSelector` looks for
`styles/<Qt Quick Controls style>/<File>.qml` before its default control.
With our style named `Platinum`, that means
`/usr/lib/qt6/qml/org/kde/kirigami/styles/Platinum/NavigationTabButton.qml`.
Union (`styles/org.kde.union/`) and Material use this same hook for this
same control. Union's file is a model: it starts from
`org.kde.kirigami.templates` `KT.NavigationTabButton` and replaces only the
look.

The folder is resolved relative to Kirigami's own install folder (from
`setBaseUrl`/`installRoot` in `libKirigamiPlatform`; the path search wasn't
read in source). So a user-scope install (our `install.sh`) can't put the
file there.

## Options

1. **System file via a package (recommended).** Put
   `style/kirigami/Platinum/NavigationTabButton.qml` (and maybe
   `NavigationTabBar.qml`) in the repo and install them into Kirigami's
   `styles/Platinum/` through a small pacman package (a PKGBUILD in
   `packaging/`, which the plan already lists for later). pacman tracks the
   files, a Kirigami update doesn't remove them (different package), and
   uninstalling the package removes them. `install.sh` stays user-scope and
   only reports whether the package is installed.
2. **System file copied by a root step in `install.sh`.** Simpler for the
   user, but unowned files in `/usr` that `uninstall.sh` must remove with
   root, against the project's user-scope rule so far.
3. **Leave it.** Document it as a known limitation in the README. It's one
   page on this system.

Not considered: shipping a full copy of `org.kde.kirigami` earlier in the
QML import path (replaces all of Kirigami; breaks on every Kirigami
update), or patching Kirigami (AGENTS.md: only supported hooks).

## What it should look like

Mac OS 9 has this exact control: the Monitors control panel
(`reference/controls-monitors.png`, around x=800–892, y=315–354) switches
its pages with a row of large icon **bevel buttons**, each with its label
below the button. The selected page's button stays pushed in ("Monitor"),
the others are raised ("Color"). Both states are measured
(`docs/REFERENCE.md`, "Bevel button, normal / selected / sizes": 38×40,
rounded black outline) and already drawn by the QStyle for tool buttons
(`drawBevel` in `style/platinum/platinumstyle.cpp`, `Slices::BevelNormal` /
`Slices::BevelPressed` in `slices.h`).

So the target is Monitors-style bevel buttons:

- the icon inside a large bevel button, the label below it (outside the
  button), as in the capture;
- raised when unselected, pushed in when checked, and pushed in while held
  (Mac OS 9 bevel buttons show the pressed look on mouse-down);
- the icon drawn dark on the pushed-in button, as the capture shows
  (whether that needs anything beyond the QStyle's existing icon handling
  is part of step 2);
- keyboard focus as the QStyle draws it for other buttons.

The drawing comes from the QStyle through `PlatinumItem`
(`style/quick/platinumitem.cpp`), as the other overrides do, and falls back
to Kirigami's own look when the app's style isn't Platinum (the `active`
check `PlatinumItem` already uses), like the Fusion fallback checks in
`dev/check-quick.sh`.

Platinum tabs were the other candidate (the control is a page switcher),
but Mac OS 9's own icon page switcher is the bevel row above, so tabs are
not proposed.

## Steps (if option 1)

1. (No capture needed: `controls-monitors.png` has both states.)
2. Add a `PlatinumItem` element type for the bevel button, drawing through
   the QStyle's existing large bevel, with the icon inside and the label
   below.
3. Write `style/kirigami/Platinum/NavigationTabButton.qml` from
   `KT.NavigationTabButton`: Platinum background, Kirigami's content item,
   same sizes and keyboard focus. Check whether `NavigationTabBar.qml`
   needs an override too (its separator line and background).
4. Sandbox test without root: copy Kirigami's module into
   `dev/build/` and add the file there, or point the test at it another
   way. Compare idle, hover, checked, pressed and focused pixels with the
   QStyle drawing, and the fallback under Fusion with stock Kirigami.
   Add it to `dev/check-quick.sh`.
5. PKGBUILD in `packaging/` for the Kirigami style files; `install.sh`
   prints whether it's installed; README says how to install and remove it.
6. User review on the desktop (Window Behavior page).

## Questions for the reviewer

1. Is the base-folder-only lookup right? Read `StyleSelector` in
   Kirigami 6.32 source: does it ever search the QML import path or a
   user folder? If it does, a user-scope install is possible and options
   1–2 change.
2. Do you agree with Monitors-style bevel buttons as the look (label
   below the button), or see a reason to prefer something else?
3. Option 1, 2 or 3? Is a package worth it for one page?
4. Does the Kirigami style name have to equal `QQuickStyle::name()`
   exactly (`Platinum`), and does `styleChain` fall back to
   `org.kde.desktop` for the files we don't provide?
5. Anything in `NavigationTabBar` (footer position, `TextBesideIcon` in
   narrow windows) the override must handle?
