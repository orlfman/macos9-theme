// KDE's Drawer as a Platinum panel: framed like a menu (black outline,
// bevel, 1 px shadow) on the side that slides in; its other sides lie
// outside the window. Mac OS 9 had no drawers, so this is derived.
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.Drawer {
    id: control
    readonly property bool platinum: panel.active
    property PlatinumItem panel: PlatinumItem {
        elementType: "drawer"
        edge: control.edge
        parent: control.background ? control.background.parent : null
        x: control.background ? control.background.x : 0
        y: control.background ? control.background.y : 0
        width: control.background ? control.background.width : 0
        height: control.background ? control.background.height : 0
        z: control.background ? control.background.z : -1
        visible: active
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    // The open side's frame is 3 px (bevel, outline, shadow on the right and
    // bottom; the panel's light edge and outline on the left and top).
    Binding { target: control; property: "rightPadding"; value: control.edge === Qt.LeftEdge ? 3 : 0; when: control.platinum }
    Binding { target: control; property: "leftPadding"; value: control.edge === Qt.RightEdge ? 2 : 0; when: control.platinum }
    Binding { target: control; property: "bottomPadding"; value: control.edge === Qt.TopEdge ? 3 : 0; when: control.platinum }
    Binding { target: control; property: "topPadding"; value: control.edge === Qt.BottomEdge ? 2 : 0; when: control.platinum }
}
