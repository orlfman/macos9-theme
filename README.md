# macos9-theme

A KDE Plasma 6.8 theme that aims to look as close as possible to Mac OS 9.2.2
with the Platinum appearance: colors, window decoration, application style,
menu bar, icons, and cursors. Colors and shapes are measured from the real
system and drawn pixel for pixel at 1x.

Status: early, but usable. Done: the color scheme, the window decoration,
the application style (Qt Widgets and Qt Quick apps), and the Plasma side
(the menu bar with a global menu, and a dock designed around the Mac OS 9
look). The installer also includes the named GTK 3 widget theme. Details in
[PLAN.md](PLAN.md); open issues in [AUDIT.md](AUDIT.md).

The optional [Firefox theme](#firefox-optional) is production-ready on Linux.

## Install

Everything goes into your home; no root. It needs a C++ compiler, Qt 6 and
KDecoration 3 development files, and the WhiteSur Lavender icon builder tools
(on Arch: `base-devel`, `qt6-base`, `qt6-declarative`, `kcoreaddons`,
`kdecoration`, `kconfig`, `util-linux`, `git`, `python`, `libxml2`, `librsvg`,
`gtk-update-icon-cache`, `python-gobject`, and `gtk3`; plus `python-pillow` if
you add custom `.png` icons under `icons/custom/`). `install.sh` preflights
these (including `pkg-config` modules, `moc`, and KDecoration 3 headers/library)
before taking locks, fetching, or writing files.

```bash
./install.sh
```

If Platinum is already your active global theme, a plain `./install.sh` also
selects `WhiteSur-lavender` once for both KDE and GTK without touching your
panels, wallpaper, cursors, or other settings (recording your previous KDE and
GTK icon preferences first so `./uninstall.sh` restores them cleanly). Later
plain updates preserve whatever icon theme you pick afterwards; when Platinum
is not active, a plain `./install.sh` never changes your icon selection.

The installer makes **Platinum** available to GTK 3 apps under
`$XDG_DATA_HOME/themes/Platinum` (normally `~/.local/share/themes/Platinum`).
To try it for one app, close that app and launch it with `GTK_THEME=Platinum`,
for example `GTK_THEME=Platinum gtk3-demo` if the GTK demos are installed.
This choice lasts for that launch. To use it across GTK apps, select **Platinum**
in Plasma’s GTK application style settings. If Platinum is still selected,
`./uninstall.sh` keeps its resources until you choose another GTK style and
rerun the command. An earlier GTK 3 theme displaced by installation is
restored on removal. GTK 4 resources can coexist in the same theme directory.

The installer also makes **Platinum Lavender** available as a terminal color
scheme. Select it under **Settings → Appearance → Terminal Color Scheme** in
Kwi, or in the **Appearance** tab of a Konsole profile. If a terminal still
selects the installed palette when you uninstall, the uninstaller keeps it
until you choose another scheme and rerun `./uninstall.sh` or a usable copy
is already available through the same scheme name.

Then log out and back in once (a Plasma login script lets Qt find the
style and the window decoration), and switch:

```bash
./install.sh --apply
```

`--apply` applies the Platinum global theme. It replaces your panels with
the menu bar and the dock, sets the Lavender Desktop Pattern wallpaper, and
puts the close box on the left. Only the main screen gets the menu bar and
the dock (like Mac OS 9). `--dry-run` shows what either step would do. On a
first switch from Breeze, log out and back in after applying so Qt Quick
apps start with Platinum controls.

To try another wallpaper on an existing installation, rerun `./install.sh`
and choose **Pastel Ribbon Landscape**, **Lavender Desktop Pattern**,
**Platinum Waves**, **Platinum Glass**, **Platinum Nebula**, **Finder Waves**
or **Retro Lavender Ripples** in Plasma's desktop wallpaper settings. All
seven 3840 × 2160 JPEG XL images use
Qt's JPEG XL decoder, provided by `kimageformats` on Arch. The
`--apply` option checks all seven images and warns before switching if Qt
cannot open them.

Your config files (panels, colors, style, decoration, and the GTK
settings Plasma rewrites when the colors change) are copied when you
install and again right before `--apply` switches, so it's safe to switch
in System Settings > Global Theme instead. If a file or folder is already
where the theme installs to, it's moved aside and put back on uninstall.
If one of the copied config files is a symbolic link, install stops
without changing anything and tells you which. If Platinum is already your
global theme when you install, your settings are copied as they are then,
so uninstalling brings back that state, not what you had before Platinum.

Qt Quick apps (System Settings, Discover and other Kirigami apps) get
Platinum menus, menu bars, pop-up lists, help balloons, check-box
switches, two-thumb sliders, dialogs in the Mac OS 9 modal frame, and
slide-out panels framed like menus; their other controls come from KDE's style, which draws through
the Platinum style already. The login script turns this on only while
Platinum is your application style, you haven't chosen a Qt Quick style
yourself, and KDE's Qt Quick style is the version it was checked with; an
app also goes back to KDE's look by itself when you switch styles.

After a Plasma upgrade, run `./install.sh` again: the window decoration is
built for one KDecoration version, and until it's rebuilt KWin uses
Breeze's title bars instead of loading it.

To undo everything and get your previous setup back:

```bash
./uninstall.sh
```

It stops Plasma's shell while it puts your panel layout back (the shell
saves its layout when it quits) and starts it again. Your config files as
they were just before uninstalling, and the copy that was put back, are
kept in `~/.local/state/macos9-theme-uninstalled-*`. Log out and back in
once afterwards. Until you do, launchers from the old session still request
the Platinum Qt Quick style. Uninstall normally leaves a temporary module
that forwards those apps to KDE's style and removes itself at the next
login. If a personal file or folder occupies its location, uninstall keeps
it and reports that those apps may need a fresh login to start.

If either Platinum wallpaper is still selected when uninstall reaches
it, that package stays in place. Choose a different wallpaper on the
affected desktops and run `./uninstall.sh` again to finish.

Files and folders you added to or changed in what the theme installed (an
extra SVG in its Plasma style, an edited color scheme) are left where they
are; only the theme's own files, unchanged, are removed. Running
`./install.sh` again moves such a changed file or folder aside first. If
that happens more than once to the same place, uninstall puts back what
was there before the first install and keeps your later versions in the
dated folder. If something is in the way
(say you put a file of your own where the theme had one moved aside),
uninstall leaves it alone, keeps a list of what's left, and exits with an
error. Sort it out and run `./uninstall.sh` again: it picks up
where it stopped and never redoes a finished step. Run both scripts with
the same `XDG_CONFIG_HOME` and `XDG_DATA_HOME` (they refuse otherwise),
and if a folder link such as `~/.config` was pointed elsewhere since the
install, point it back first: both scripts stop without changing anything
rather than follow it. If Plasma's shell can't be started again after
uninstalling, it says how to start it, and running `./uninstall.sh` again
starts it.

Not affiliated with Apple. No Apple image files, fonts, or sounds are
included. The application style's small parts (bevels, arrows, the check
mark and similar) are pixel tables measured from screenshots of Mac OS 9;
they'll be redrawn before any public release (AUDIT.md finding 25).

For contributors and AI agents: [AGENTS.md](AGENTS.md).

### Cursors

The theme comes with black Mac-style cursors: Apple Cursor v2.0.1 by
ful1e5 (GPL-3.0, see `cursors/README.md`). `./install.sh` installs them as
the cursor theme `macOS-cursors`, and `--apply` selects them along with the
rest of the global theme. Log out and back in after installing so Plasma
can find the pack. You can also pick **macOS** in Plasma's Cursors
settings on its own.
Uninstalling after applying Platinum restores your previous cursor setting.
If the pack is still selected after that, or you picked it separately in
Plasma, choose another cursor theme and rerun the uninstaller to remove it.

### Firefox (optional)

Platinum Lavender gives Firefox an Internet Explorer 5 for Mac layout, with a
lavender address bar, beveled tabs, and a classic status bar. It is
production-ready and tested on Firefox 160.0.1 on Linux. Use Firefox’s
**System theme** with a light, normal-contrast desktop appearance. Private
Browsing windows in the same profile use the same styling.

**Install or update.** Close Firefox completely, then run this from the
repository root and select the profile you want to theme. Reopen Firefox to
load the changes.

```bash
./install.sh --firefox
```

**Vertical tabs.** Right-click the toolbar or tab strip and choose **Turn on
Vertical Tabs**. Collapse the sidebar for an icon-only strip. In both regular
and Private Browsing windows, the icons stay centered in their frames and
line up with the new-tab button. Choose **Turn off Vertical Tabs** to return
the tabs below the Favorites bar.

**Uninstall.** Close Firefox, then run this command and select the profile to
restore.

```bash
./uninstall.sh --firefox
```

Both commands accept `--list` to list profiles, `--profile "Profile Name"` to
select one, and `--dry-run` to preview changes. See the [Firefox guide](firefox/README.md)
for backup details, appearance settings, and compatibility checks.
