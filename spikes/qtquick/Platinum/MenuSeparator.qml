// Spike: KDE's MenuSeparator drawn as the Platinum etched line.
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.MenuSeparator {
    id: control
    objectName: "platinum-separator"
    readonly property bool platinum: line.active
    property PlatinumItem line: PlatinumItem {
        parent: control
        width: control.width
        height: control.height
        z: -1
        visible: active
        elementType: "separator"
        // (a separator has no menu property; found through the list)
        readonly property var menu: control.parent && control.parent.parent ? control.parent.parent.parent : null
        panel: menu && menu.leftPadding !== undefined ? Qt.rect(-(menu.leftPadding + control.x), -(menu.topPadding + control.y), menu.width, menu.height)
                                                      : Qt.rect(0, 0, 0, 0)
    }
    Binding { target: control.contentItem; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control; property: "implicitHeight"; value: control.line.implicitHeight; when: control.platinum }
}
