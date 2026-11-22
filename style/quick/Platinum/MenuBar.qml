// KDE's MenuBar on the Platinum menu bar (white top row, #999999 and black
// bottom rows) while the application's style is Platinum. Like every
// override here, KDE's own parts are only hidden (opacity 0 through a
// Binding), never replaced, so they come back as they were when the style
// changes. SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.MenuBar {
    id: control
    readonly property bool platinum: bar.active
    property PlatinumItem bar: PlatinumItem {
        elementType: "menubar"
        parent: control
        width: control.width
        height: control.height
        z: -1
        visible: active
    }
    // Titles made from menus are ours too.
    delegate: MenuBarItem {}
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control; property: "implicitHeight"; value: control.bar.implicitHeight; when: control.platinum }
    Binding { target: control; property: "padding"; value: 0; when: control.platinum }
    Binding { target: control; property: "spacing"; value: 0; when: control.platinum }
}
