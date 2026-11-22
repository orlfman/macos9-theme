// KDE's SwitchDelegate (a list row with a switch) with a Platinum check
// box as its indicator. SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.SwitchDelegate {
    id: control
    readonly property bool platinum: box.active
    property PlatinumItem box: PlatinumItem {
        elementType: "checkbox"
        parent: control
        x: control.indicator ? control.indicator.x : 0
        y: control.indicator ? control.indicator.y : 0
        width: implicitWidth
        height: implicitHeight
        visible: active
        checked: control.checked
        pressed: control.pressed
        enabled: control.enabled
    }
    Binding { target: control.indicator; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.indicator; property: "implicitWidth"; value: control.box.implicitWidth; when: control.platinum }
    Binding { target: control.indicator; property: "implicitHeight"; value: control.box.implicitHeight; when: control.platinum }
}
