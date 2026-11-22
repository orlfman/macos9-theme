// KDE's MenuBarItem as a Platinum menu title: highlighted only while its
// menu is open, as on Mac OS 9. SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.MenuBarItem {
    id: control
    readonly property bool platinum: title.active
    property PlatinumItem title: PlatinumItem {
        elementType: "menubaritem"
        parent: control
        width: control.width
        height: control.height
        z: -1
        visible: active
        text: control.text
        selected: control.highlighted && control.menu !== null && control.menu.visible
        enabled: control.enabled
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.contentItem; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control; property: "implicitWidth"; value: control.title.implicitWidth; when: control.platinum }
    Binding { target: control; property: "implicitHeight"; value: control.title.implicitHeight; when: control.platinum }
    Binding { target: control; property: "padding"; value: 0; when: control.platinum }
}
