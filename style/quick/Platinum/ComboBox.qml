// KDE's ComboBox (its closed control already draws through the QStyle)
// with a Mac OS 9 pop-up list: KDE's own list, restyled like our Menu (its
// background hidden, the Platinum menu panel behind it), with our rows,
// the current one checked, opened over the button as the widget combo box
// does (SH_ComboBox_Popup). KDE builds its list inside ComboBox.qml, so a
// Menu override alone doesn't reach it (AUDIT.md finding 47); replacing the
// list would leave KDE's created too, holding the rows.
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.ComboBox {
    id: control
    readonly property bool platinum: listPanel.active
    readonly property Item listBackground: popup && popup.background ? popup.background : null
    property PlatinumItem listPanel: PlatinumItem {
        elementType: "menu"
        parent: control.listBackground ? control.listBackground.parent : null
        width: control.popup ? control.popup.width : 0
        height: control.popup ? control.popup.height : 0
        z: control.listBackground ? control.listBackground.z : -1
        visible: active
    }
    delegate: MenuItem {
        required property var model
        required property int index
        text: model[control.textRole]
        highlighted: control.highlightedIndex === index
        // The current row's check mark (Platinum only; KDE's list has none).
        checkable: platinum
        checked: control.currentIndex === index
    }
    Binding { target: control.listBackground; property: "opacity"; value: 0; when: control.platinum }
    // Inside the 1 px black line; the shadow takes 1 more px right and below.
    Binding { target: control.popup; property: "leftPadding"; value: 1; when: control.platinum }
    Binding { target: control.popup; property: "topPadding"; value: 1; when: control.platinum }
    Binding { target: control.popup; property: "rightPadding"; value: 2; when: control.platinum }
    Binding { target: control.popup; property: "bottomPadding"; value: 2; when: control.platinum }
    // As wide as the widget combo box's list: the button, or its width hint
    // for the longest item if that's more (QComboBox::showPopup; finding
    // 53). The rows stretch to it. As tall as its rows (KDE's list adds 1 px).
    readonly property int platinumListWidthHint: {
        // The closed control only needs its own width. Measure the list
        // on opening and keep tracking live edits while it is visible.
        if (!platinum || !popup || !popup.visible) return 0;
        const texts = [];
        // Observe delegate text so same-count model edits also invalidate the hint.
        for (let i = 0; i < popup.count; ++i) {
            const item = popup.itemAt(i);
            texts.push(item && item.text !== undefined ? item.text : textAt(i));
        }
        return listPanel.comboWidthHint(texts);
    }
    Binding {
        target: control.popup; property: "implicitWidth"; when: control.platinum
        value: Math.max(control.width, control.platinumListWidthHint)
    }
    Binding {
        target: control.popup; property: "implicitHeight"; when: control.platinum
        value: control.popup.contentItem.contentHeight + 3
    }
    // Over the button, the current row on it; KDE's own place (just below
    // the button, KDE's ComboBox.qml) otherwise. One binding for both: a
    // Binding element on a pop-up's y doesn't give KDE's binding back.
    function placeList() {
        if (!popup) {
            return;
        }
        popup.y = Qt.binding(function () {
            if (!control.platinum) {
                return control.height;
            }
            const row = control.popup.count > 0 ? control.popup.itemAt(Math.max(0, control.currentIndex)) : null;
            return row ? Math.round((control.height - row.height) / 2) - 1 - row.y : 0;
        });
    }
    Component.onCompleted: placeList()
    onPopupChanged: placeList()
}
