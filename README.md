# macos9-theme

A KDE Plasma 6.8 theme that aims to look as close as possible to Mac OS 9.2.2
with the Platinum appearance: colors, window decoration, application style,
menu bar, icons, and cursors. Colors and shapes are measured from the real
system and drawn pixel for pixel at 1x.

Status: early, but usable. Done: the color scheme, the window decoration,
the application style (Qt Widgets and Qt Quick apps), and the Plasma side
(the menu bar with a global menu, and a dock designed around the Mac OS 9
look). Still to come: icons, cursors, fonts, GTK, extras. Details in
[PLAN.md](PLAN.md); open issues in [AUDIT.md](AUDIT.md).

## Install

Everything goes into your home; no root. It needs a C++ compiler and the
Qt 6 and KDecoration 3 development files (on Arch: `base-devel`, `qt6-base`,
`kdecoration`).

```bash
./install.sh
```

Then log out and back in once (a Plasma login script lets Qt find the
style and the window decoration), and switch:

```bash
./install.sh --apply
```

`--apply` copies your config files first, then applies the Platinum global
theme. It replaces your panels with the menu bar and the dock, and puts
the close box on the left. `--dry-run` shows what either step would do.

To undo everything and get your previous setup back:

```bash
./uninstall.sh
```

Your config files as they were just before uninstalling are kept in
`~/.local/state/macos9-theme-uninstalled-*`.

Not affiliated with Apple. No Apple artwork, fonts, or sounds are included;
everything is redrawn.

For contributors and AI agents: [AGENTS.md](AGENTS.md).
