// KDE's Switch with a Platinum check box as its indicator (Mac OS 9 had no
// switches). Still a switch for the keyboard and screen readers: only the
// indicator's look changes. SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.Switch {
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
    // KDE's indicator shrinks to the box (the label follows it) and hides.
    Binding { target: control.indicator; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.indicator; property: "implicitWidth"; value: control.box.implicitWidth; when: control.platinum }
    Binding { target: control.indicator; property: "implicitHeight"; value: control.box.implicitHeight; when: control.platinum }
}
