// The Mac OS 9 menu bar as a Plasma layout (Plasma's desktop scripting API).
// Replaces every panel with one 20 px top panel:
//   Kicker (cascading menu; the Apple menu's place, neutral icon)
//   Platinum Global Menu, with Plasma's stock menu as the recovery choice
//   spacer
//   system tray, clock
//   Window List (the Application menu's place: active window icon + name)
// with platinum.menubarpiece at both ends (the rounded corners) and before
// the Window List (the divider), and adds the dock at the bottom.
// The global theme selects the wallpaper through its defaults.
// Both panels go on the main screen only (screen 0, which Plasma 6 keeps as
// the primary one), as on Mac OS 9; other screens get none (the user's
// choice, PLAN.md decision 10).
//
// Used by dev/plasma-test.sh (evaluated inside a sandboxed plasmashell);
// later the look-and-feel package's layout. SPDX-License-Identifier: BSD-2-Clause

panels().forEach(function (p) { p.remove(); });

var bar = new Panel;
bar.location = "top";
bar.height = 20;
bar.floating = false;
bar.hiding = "none";
bar.alignment = "left";
bar.lengthMode = "fill";

function piece(name) {
    var w = bar.addWidget("platinum.menubarpiece");
    w.currentConfigGroup = ["General"];
    w.writeConfig("piece", name);
}

piece("cornerLeft");
var apple = bar.addWidget("org.kde.plasma.kicker");
apple.currentConfigGroup = ["General"];
apple.writeConfig("icon", "start-here-kde-plasma");
apple.writeConfig("useCustomButtonImage", false);

var menu;
if (knownWidgetTypes.indexOf("platinum.globalmenu") >= 0) {
    try {
        menu = bar.addWidget("platinum.globalmenu");
    } catch (error) {
        print("Could not add Platinum Global Menu: " + error);
    }
}
if (!menu || menu.type !== "platinum.globalmenu") {
    bar.addWidget("org.kde.plasma.appmenu");
}
bar.addWidget("org.kde.plasma.panelspacer");
bar.addWidget("org.kde.plasma.systemtray");

var clock = bar.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);
clock.writeConfig("use24hFormat", 0);

piece("divider");
bar.addWidget("org.kde.plasma.windowlist");
piece("cornerRight");

// The dock (the user's choice, PLAN.md decision 9): a bottom panel sized to
// its apps, styled like Mac OS 9's pop-up window tab, apps as bevel buttons.
var dock = new Panel;
dock.location = "bottom";
dock.height = 52;
dock.floating = false;
dock.hiding = "none";
dock.alignment = "center";
dock.lengthMode = "fit";
var apps = dock.addWidget("org.kde.plasma.icontasks");
apps.currentConfigGroup = ["General"];
apps.writeConfig("launchers", "applications:org.kde.dolphin.desktop,applications:org.kde.kate.desktop,applications:systemsettings.desktop");
apps.writeConfig("iconSpacing", 0);
// The Trash at the dock's end, as on Mac OS X (user, 2026-11-24). Our own
// widget: Plasma's forces a symbolic icon and fills the panel's thickness.
dock.addWidget("platinum.trash");
