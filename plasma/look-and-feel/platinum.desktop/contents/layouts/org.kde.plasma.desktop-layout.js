// Copied from plasma/layout.js by plasma/make-plasma.py; edit that one.
// The Mac OS 9 menu bar as a Plasma layout (Plasma's desktop scripting API).
// Replaces every panel with one 20 px top panel:
//   Kicker (cascading menu; the Apple menu's place, neutral icon)
//   global menu (appmenu)
//   spacer
//   system tray, clock
//   Window List (the Application menu's place: active window icon + name)
// with platinum.menubarpiece at both ends (the rounded corners) and before
// the Window List (the divider),
// and gives every desktop a plain color close to the Mac OS 9 default
// desktop pattern's average (the pattern itself is Apple artwork).
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

bar.addWidget("org.kde.plasma.appmenu");
bar.addWidget("org.kde.plasma.panelspacer");
bar.addWidget("org.kde.plasma.systemtray");

var clock = bar.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);
clock.writeConfig("use24hFormat", 0);

piece("divider");
bar.addWidget("org.kde.plasma.windowlist");
piece("cornerRight");

desktops().forEach(function (d) {
    d.wallpaperPlugin = "org.kde.color";
    d.currentConfigGroup = ["Wallpaper", "org.kde.color", "General"];
    d.writeConfig("Color", "99,99,156");
});
