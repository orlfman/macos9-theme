// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import QtQuick.Templates as T
import org.kde.qqc2desktopstyle.private as KDEStyle

QtObject {
    id: press

    property T.ScrollBar bar
    readonly property MouseArea area: bar?.background instanceof MouseArea ? bar.background : null
    property KDEStyle.StyleItem painter
    property string arrow: ""

    // KDE handles line and page presses in the background MouseArea.
    // Only the painter under the pointer has an active arrow. Save that
    // arrow at press time so hovering over another part cannot push it in.
    readonly property Connections mouse: Connections {
        target: press.area
        function onPressed(event) {
            if (event.button !== Qt.LeftButton) {
                return;
            }
            for (const item of press.area.children) {
                if (item instanceof KDEStyle.StyleItem && item.elementType === "scrollbar"
                    && (item.activeControl === "up" || item.activeControl === "down")) {
                    press.arrow = item.activeControl;
                    press.painter = item;
                    return;
                }
            }
        }
        function onReleased(event) {
            if (event.button === Qt.LeftButton) {
                press.painter = null;
            }
        }
        function onCanceled() {
            press.painter = null;
        }
    }

    onAreaChanged: painter = null

    readonly property Binding sunken: Binding {
        target: press.painter
        property: "sunken"
        value: true
        // KDE's style name can include a "::" suffix.
        when: press.painter !== null && press.painter.styleName.split("::")[0].toLowerCase() === "platinum"
              && press.painter.activeControl === press.arrow
              && Boolean(press.area?.pressedButtons & Qt.LeftButton)
        restoreMode: Binding.RestoreBindingOrValue
    }
}
