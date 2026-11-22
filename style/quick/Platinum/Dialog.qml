// KDE's Dialog in the Mac OS 9 plain modal dialog frame (black outline,
// bevel, 1 px shadow; measured, Platinum::PE_PlatinumModalFrame) on its
// white body, and without the dimmed window behind it (Mac OS 9 didn't
// dim). A dialog inside a Qt Quick window can't be moved, like the plain
// modal dialog (no drag strip). SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import QtQuick.Templates as T
import org.kde.desktop 1.0 as KDE

KDE.Dialog {
    id: control
    readonly property bool platinum: frame.active
    property PlatinumItem frame: PlatinumItem {
        elementType: "dialog"
        parent: control.background ? control.background.parent : null
        x: control.background ? control.background.x : 0
        y: control.background ? control.background.y : 0
        width: control.background ? control.background.width : 0
        height: control.background ? control.background.height : 0
        z: control.background ? control.background.z : -1
        visible: active
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    // KDE's modal backdrop (rgba(0, 0, 0, 0.3), KDE's Dialog.qml), clear
    // while Platinum.
    T.Overlay.modal: Rectangle {
        color: control.platinum ? "transparent" : Qt.rgba(0, 0, 0, 0.3)
    }
}
