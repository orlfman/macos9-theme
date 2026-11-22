// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE
import org.kde.kirigami as Kirigami

KDE.ToolButton {
    id: control

    // Kwi's tab close control exposes the tab's selected state. Preserve
    // ordinary tool buttons and any explicitly customized icon.
    readonly property bool platinumTabClose: closeIndicator.item?.active ?? false

    Loader {
        id: closeIndicator
        anchors.fill: parent
        active: typeof control.selected === "boolean"
            && control.flat && !control.checkable
            && control.display === KDE.ToolButton.IconOnly
            && control.icon.name === "tab-close-other"
            && control.icon.source.toString() === "" && control.icon.color.a === 0
            && control.icon.width === Kirigami.Units.iconSizes.small
            && control.icon.height === Kirigami.Units.iconSizes.small
        sourceComponent: PlatinumItem {
            elementType: "tabclose"
            visible: active
            // Qt also uses the gray glyph for an enabled inactive tab.
            opacity: control.enabled ? 1 : 0.5
            selected: control.selected
            pressed: control.down
            hovered: control.hovered
            keyboardFocus: control.visualFocus
        }
    }
    Binding {
        target: control.background
        property: "opacity"
        value: 0
        when: control.platinumTabClose
    }
}
