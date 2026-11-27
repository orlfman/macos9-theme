# macos9-theme

Mac OS 9 for your KDE Plasma 6 desktop. Specifically 9.2.2 with the default
Platinum appearance: the gray pinstriped title bars, the beveled buttons and
the lavender highlights.

I didn't want another theme that's "inspired by" the old Mac look. I wanted
the actual thing. So the colors, bevels and sizes were measured off a real
9.2.2 install running in a VM and drawn to match it pixel for pixel at 100%
scale. Where Plasma just can't do what OS 9 did, I got as close as I could and
listed the differences [further down](#known-limitations).

It's a personal project and still being worked on, but I run it as my daily
desktop.

## What's in it

- **Window title bars** with pinstripes, the close box on the left, and the
  zoom and collapse boxes on the right.
- **An application style** for Qt apps, so Dolphin, Kate, Konsole, System
  Settings and friends get Platinum buttons, scroll bars with arrows, tabs,
  check boxes, menus and so on.
- **A menu bar** across the top with an Apple menu stand in (no Apple logo),
  the global menu, the system tray, the clock, and an application menu on the
  right like OS 9 had.
- **A dock** along the bottom with Dolphin, Kate and System Settings pinned,
  and a Trash that fills up when there's something in it.
- **GTK 3 and GTK 4 themes** so apps like Lutris, Audacious and pavucontrol
  match, plus an extra layer that gets most libadwaita (GNOME) apps on board.
- **Lavender icons** built from the WhiteSur icon theme, **black Mac style
  cursors**, and **seven 4K wallpapers**.
- **A terminal color scheme** (Platinum Lavender) for Konsole and Kwi.
- **An optional Firefox theme** laid out like Internet Explorer 5 for Mac.

## What you need

- KDE Plasma 6.8
- Build tools for the application style, window decoration, and Platinum
  Global Menu. These plugins are compiled on your machine.

I built and tested this on Arch (CachyOS), so these are Arch package names. It
should work on other distros if you can find the equivalents, but I haven't
tried it.

```bash
sudo pacman -S --needed base-devel git python cmake ninja gettext extra-cmake-modules libplasma plasma-workspace ki18n kwindowsystem qt6-base qt6-declarative kcoreaddons kdecoration kconfig util-linux libxml2 librsvg gtk-update-icon-cache python-gobject gtk3 kimageformats
```

`kimageformats` is what lets Plasma open the wallpapers (they're JPEG XL).
You don't need to get the list perfect: the installer checks for everything
before it touches anything and tells you exactly what's missing.

The first install also needs an internet connection, since it downloads the
WhiteSur icon theme from GitHub to build the lavender icons from.

**Fonts:** the theme leaves your fonts alone. OS 9's own fonts (Charcoal and
Geneva) can't be shipped with it. I use SF Pro Text and SF Mono, which are
in the AUR as `apple-fonts`, and set them in System Settings under Fonts. Use
whatever you like though.

## Installing

Everything goes into your home folder. No sudo, nothing touched in `/usr`.

1. Grab the theme:

   ```bash
   git clone https://github.com/orlfman/macos9-theme
   ```

   ```bash
   cd macos9-theme
   ```

2. Install it:

   ```bash
   ./install.sh
   ```

   This builds the plugins and puts all the theme files in place. It doesn't
   change how your desktop looks yet.

3. **Log out and back in.** The login script lets Plasma and Qt find the
   new global menu, window decoration, and application style.

4. Switch to it:

   ```bash
   ./install.sh --apply
   ```

   On the first switch, this **replaces your panels** with the menu bar and the dock. It
   also sets the wallpaper, icons and cursors, and moves the close box to the
   left. Your current config gets backed up first, and the uninstaller puts
   it all back exactly how it was. Only your main screen gets the menu bar
   and dock, same as OS 9.

5. If you were on Breeze before, log out and back in one more time so apps
   like System Settings and Discover pick up the Platinum controls.

Want to see what a step will do first? Add `--dry-run` to either command.

You can also skip step 4 and pick **Platinum** in System Settings under
Global Theme yourself. Your config was already backed up during step 2, so
that's just as safe. Platinum shows up as a light theme, so if you use
automatic day and night switching you can set it as your daytime theme.

### Updating

```bash
git pull
```

```bash
./install.sh
```

**Run `./install.sh` again after every Plasma update too.** The window
decoration and global menu are built against the KDE libraries on your
machine. KWin falls back to Breeze title bars when its decoration library
changes. On the next Plasma login after a change to the menu's runtime
libraries, the panel switches to the stock Global Menu in the same slot.

If your Platinum panel still has the stock Global Menu, log out and back in
after installing, then run `./install.sh --apply` while Platinum is active.
Plasma restarts briefly during the swap and keeps the panel layout and widget
settings.

Run `tools/check-global-menu-upstream.sh` to see whether the bundled applet
has new upstream commits available for review.

## Extras and tweaks

### Wallpapers

The default is Lavender Desktop Pattern. The other six are Pastel Ribbon
Landscape, Platinum Waves, Platinum Glass, Platinum Nebula, Finder Waves and
Retro Lavender Ripples. Pick them the usual way: right click the desktop and
go to Desktop and Wallpaper. They're all 3840 × 2160.

If they don't show up, you're probably missing `kimageformats`. The
`--apply` step checks for this and warns you before switching.

### GTK apps

The installer adds **Platinum** as a GTK theme, but it doesn't switch GTK
apps over on its own yet. To turn it on, go to System Settings, Application
Style, and use the button for configuring GNOME/GTK application style.

To try it on a single app first, close the app and start it like this:

```bash
GTK_THEME=Platinum lutris
```

**libadwaita apps** (most GNOME apps) normally ignore GTK themes completely.
While Platinum is your global theme, the installer adds one marked line to
the top of `~/.config/gtk-4.0/gtk.css` that gives them Platinum colors and
controls anyway. The rest of that file is left alone and the uninstaller
takes the line back out. It only kicks in for light mode at normal contrast.
One side effect: while that line is there, plain GTK 4 apps look Platinum no
matter which GTK theme you picked.

### Terminal colors

Pick **Platinum Lavender** in the Appearance tab of your Konsole profile, or
in Kwi under Settings, Appearance, Terminal Color Scheme.

### Apple logo on the menu

By default the menu in the top left corner (the Apple menu's place) uses a
neutral icon. If you'd like the Apple logo there for your own desktop, add
`--apple-menu-icon` when you switch:

```bash
./install.sh --apply --apple-menu-icon
```

The logo is `folder-apple` from your icon theme (the WhiteSur icons this
theme installs have it); the theme itself doesn't ship it. It's only changed
when your active icon theme provides it and there's exactly one launcher in
the top bar. Uninstalling puts back the icon you had before, unless you've
changed it yourself in the meantime. Run uninstall from a Plasma session
when the previous icon needs to be restored on a panel you are keeping.

### Cursors

The cursors are Apple Cursor v2.0.1 by ful1e5 (GPL 3.0, details in
[cursors/README.md](cursors/README.md)). `--apply` turns them on with the
rest of the theme, or you can pick **macOS** in System Settings under
Cursors. If they don't show up, log out and back in once so Plasma finds
them.

### Firefox

This one's optional and kept separate from everything else. It gives Firefox
an Internet Explorer 5 for Mac layout with a lavender address bar, beveled
tabs and a proper status bar along the bottom. I've tested it on Firefox 160
and 161.

Close Firefox completely, then run this and pick the profile you want to
theme:

```bash
./install.sh --firefox
```

Open Firefox again and you're done. Keep Firefox on its **System theme** with
your desktop in light mode. Vertical tabs work too (right click the tab strip
and choose Turn on Vertical Tabs), and you can collapse the sidebar down to
just icons.

To take it off, close Firefox and run:

```bash
./uninstall.sh --firefox
```

Both commands take `--list` to show your profiles, `--profile "Name"` to
pick one directly, and `--dry-run`. There's more in the
[Firefox readme](firefox/README.md).

## Uninstalling

```bash
./uninstall.sh
```

This restores the backed-up colors, style, and icons. A first switch with
`--apply` also restores the old panels. If you upgraded the menu in place on
an existing Platinum layout, uninstall puts the stock widget in its current
slot if it is still present. Plasma's shell restarts during the restore. Log
out and back in afterwards.

A few things worth knowing:

- It won't delete something you're still using. If the Platinum wallpaper,
  cursors, GTK theme or terminal colors are still selected somewhere, it
  leaves that piece in place and tells you. Switch to something else and run
  `./uninstall.sh` again.
- If you edited any of the theme's files (say you tweaked the color scheme),
  your edited copy is left alone. Only the theme's own untouched files get
  removed.
- If it hits a problem halfway, it stops, tells you what's wrong, and picks
  up where it left off when you run it again.
- Copies of your config from right before the uninstall are kept in
  `~/.local/state/macos9-theme-uninstalled-*`, just in case.

## Known limitations

- Only the main screen gets the menu bar and dock. That's on purpose, it's
  how OS 9 worked.
- After a Plasma update, title bars go back to Breeze until you run
  `./install.sh` again.
- There's no dark version. OS 9 didn't have one either.
- GTK 4 scroll bars don't have arrow buttons, GTK 4 switches don't show a
  pressed state, and GTK 4 alert buttons get spread across the bottom instead
  of grouped on the right. GTK 4 doesn't give themes a way to fix those.
- libadwaita apps in dark mode or high contrast keep their normal GNOME look.
- In Qt Quick apps (System Settings, Discover and other Kirigami apps), the
  menus, pop up lists, help balloons, switches, sliders and dialogs are drawn
  as Platinum directly. The rest of their controls go through KDE's own
  style, which draws with Platinum anyway, so it mostly looks right. If you
  set your own Qt Quick style, the theme leaves it alone.
- The Firefox theme only works with Firefox's System theme in light mode.
- The package names above are Arch's. Other distros are untested.

## Credits and legal stuff

Not affiliated with Apple in any way. No Apple images, fonts or sounds are
included.

- Icons: built from [WhiteSur](https://github.com/vinceliuice/WhiteSur-icon-theme)
  by vinceliuice (GPL 3.0), see [icons/README.md](icons/README.md)
- Cursors: Apple Cursor v2.0.1 by ful1e5 (GPL 3.0), see
  [cursors/README.md](cursors/README.md)

If you want to dig into how it's put together, [PLAN.md](PLAN.md) has the
current state of each part and [AUDIT.md](AUDIT.md) has the open issues.
Notes for contributors (and the AI agents I use on this) are in
[AGENTS.md](AGENTS.md).
