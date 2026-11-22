// KDE's MenuItem drawn as a whole Platinum menu row (bevel, check,
// text, shortcut, arrow) while the style is Platinum; KDE's parts are only
// hidden, so they come back as they were (with their own bindings).
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.MenuItem {
    id: control
    objectName: "platinum-menuitem"
    readonly property bool platinum: row.active
    property PlatinumItem row: PlatinumItem {
        parent: control
        width: control.width
        height: control.height
        z: -1
        visible: active
        elementType: "menuitem"
        text: control.text
        shortcut: control.action && control.action.shortcut ? control.action.shortcut.toString() : ""
        selected: control.highlighted
        enabled: control.enabled
        checkable: control.checkable
        checked: control.checked
        subMenu: control.subMenu !== null
        first: control.menu !== null && control.menu.count > 0 && control.menu.itemAt(0) === control
        last: control.menu !== null && control.menu.count > 0 && control.menu.itemAt(control.menu.count - 1) === control
        shortcutColumn: control.menu && control.menu.platinumShortcutColumn !== undefined ? control.menu.platinumShortcutColumn : 0
        // The row paints its slice of the menu panel first, as QMenu does.
        panel: control.menu ? Qt.rect(-(control.menu.leftPadding + control.x), -(control.menu.topPadding + control.y), control.menu.width, control.menu.height)
                            : Qt.rect(0, 0, 0, 0)
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.contentItem; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.indicator; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.arrow; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control; property: "implicitWidth"; value: control.row.implicitWidth; when: control.platinum }
    Binding { target: control; property: "implicitHeight"; value: control.row.implicitHeight; when: control.platinum }
}
