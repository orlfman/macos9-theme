// Every Qt Quick control the Qt Quick style plan lists (PLAN.md "Plan: Qt
// Quick menus, tooltips and switches"), for dev/build/quickshot. Step 0:
// the controls that sit in a window; steps 1-5 each open one pop-up
// (menu, combo box list, tooltip, dialog, drawer).
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

QQC2.ApplicationWindow {
    id: root
    width: 640
    height: 420
    visible: false
    title: "Qt Quick inventory"
    property int steps: 6
    function prepare(i) {
        menu.close(); combo.popup.close(); dialog.close(); drawer.close()
        if (i === 1) { menu.popup(); menu.currentIndex = 0 }
        if (i === 2) { combo.popup.open(); Qt.callLater(() => console.log("WIDTHS combo", combo.width, "popup", combo.popup.width, "avail", combo.popup.availableWidth, "list", combo.popup.contentItem.width, "row0", combo.popup.itemAt(0).width, "row0 menu", combo.popup.itemAt(0).menu, "platinum", combo.popup.itemAt(0).platinum, "implicit", combo.popup.itemAt(0).implicitWidth, "menu avail", combo.popup.itemAt(0).menu.availableWidth, "same menu", combo.popup.itemAt(0).menu === combo.popup, "row menu name", combo.popup.itemAt(0).menu.objectName, "popup name", combo.popup.objectName, "row menu visible", combo.popup.itemAt(0).menu.visible))  }
        tipButton.QQC2.ToolTip.visible = i === 3
        if (i === 4) dialog.open()
        if (i === 5) drawer.open()
    }
    menuBar: QQC2.MenuBar {
        QQC2.Menu { title: "File"; QQC2.MenuItem { text: "Open" } }
        QQC2.Menu { title: "Edit"; QQC2.MenuItem { text: "Copy" } }
    }
    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 16
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            QQC2.Switch { text: "Switch on"; checked: true }
            QQC2.Switch { text: "Switch off" }
            QQC2.RangeSlider { from: 0; to: 100; first.value: 20; second.value: 70 }
            QQC2.BusyIndicator { running: true; implicitWidth: 32; implicitHeight: 32 }
            QQC2.PageIndicator { count: 4; currentIndex: 1 }
            QQC2.RoundButton { text: "+" }
            QQC2.ComboBox { id: combo; model: ["Lavender", "Purple", "Platinum"] }
            QQC2.Button {
                id: tipButton
                text: "Help"
                QQC2.ToolTip.text: "A help balloon"
                QQC2.ToolTip.delay: 0
                QQC2.ToolTip.timeout: -1
            }
        }
        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            QQC2.GroupBox {
                title: "Group box"
                ColumnLayout {
                    QQC2.CheckDelegate { text: "Check delegate"; checked: true }
                    QQC2.RadioDelegate { text: "Radio delegate"; checked: true }
                    QQC2.SwitchDelegate { text: "Switch delegate"; checked: true }
                }
            }
            QQC2.Frame {
                Layout.preferredWidth: 220
                ListView {
                    implicitHeight: 80
                    implicitWidth: 200
                    model: ["Applications", "Documents", "System Folder"]
                    currentIndex: 1
                    delegate: QQC2.ItemDelegate {
                        required property string modelData
                        required property int index
                        width: ListView.view.width
                        text: modelData
                        highlighted: ListView.isCurrentItem
                    }
                }
            }
        }
    }
    QQC2.Menu {
        id: menu
        QQC2.MenuItem { text: "Open" }
        QQC2.MenuItem { text: "Close" }
        QQC2.MenuSeparator {}
        QQC2.MenuItem { text: "Checked"; checkable: true; checked: true }
    }
    QQC2.Dialog {
        id: dialog
        title: "Dialog"
        standardButtons: QQC2.Dialog.Ok | QQC2.Dialog.Cancel
        QQC2.Label { text: "Are you sure?" }
    }
    QQC2.Drawer { id: drawer; width: 160; height: root.height; QQC2.Label { text: "Drawer"; padding: 10 } }
}
