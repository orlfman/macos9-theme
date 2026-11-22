// Spike: KDE's Menu with the Platinum menu panel (frame and shadow), its
// rows ours too. SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.Menu {
    id: control
    objectName: "platinum-menu"
    readonly property bool platinum: panel.active
    property PlatinumItem panel: PlatinumItem {
        elementType: "menu"
        parent: control.background ? control.background.parent : null
        width: control.width
        height: control.height
        z: control.background ? control.background.z : -1
        visible: active
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    // Rows made from actions and submenus are ours too (KDE's Menu would
    // make KDE's MenuItem).
    delegate: MenuItem {}
    // The widest shortcut, added to every row as QMenu does.
    readonly property int platinumShortcutColumn: {
        let column = 0;
        for (let i = 0; i < count; ++i) {
            const item = itemAt(i);
            if (item && item.row) {
                column = Math.max(column, item.row.shortcutWidth);
            }
        }
        return column;
    }
    // Inside the 1 px black line; the shadow takes 1 more px right and below.
    Binding { target: control; property: "leftPadding"; value: 1; when: control.platinum }
    Binding { target: control; property: "topPadding"; value: 1; when: control.platinum }
    Binding { target: control; property: "rightPadding"; value: 2; when: control.platinum }
    Binding { target: control; property: "bottomPadding"; value: 2; when: control.platinum }
    // KDE's list adds 1 px to the rows' height; QMenu doesn't.
    Binding {
        target: control; property: "implicitHeight"; when: control.platinum
        value: control.contentItem.contentHeight + control.topPadding + control.bottomPadding
    }
}
