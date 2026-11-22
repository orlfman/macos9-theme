// KDE's ToolTip with the Platinum help balloon while the
// application's style is Platinum. KDE's own background is only hidden
// (opacity 0 through a Binding, so it comes back as it was; not "visible",
// which reads false while the pop-up is closed and would be restored so),
// never replaced: Qt hides an item
// it takes out of a control and doesn't show it again when it's put back.
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.ToolTip {
    id: control
    objectName: "platinum-tooltip"
    readonly property bool platinum: balloon.active
    property PlatinumItem balloon: PlatinumItem {
        elementType: "tooltip"
        text: control.text
        parent: control.background ? control.background.parent : null
        x: control.background ? control.background.x : 0
        y: control.background ? control.background.y : 0
        width: control.background ? control.background.width : 0
        height: control.background ? control.background.height : 0
        z: control.background ? control.background.z : -1
        visible: active
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    // Plain text: drawn by our item, sized as QTipLabel sizes itself. Rich
    // text: KDE's label, inside the same margin.
    readonly property bool platinumText: platinum && balloon.drawsText
    Binding { target: control.contentItem; property: "opacity"; value: 0; when: control.platinumText }
    Binding { target: control; property: "implicitWidth"; value: control.balloon.implicitWidth; when: control.platinumText }
    Binding { target: control; property: "implicitHeight"; value: control.balloon.implicitHeight; when: control.platinumText }
    Binding { target: control; property: "padding"; value: control.balloon.margin; when: control.platinum }
}
