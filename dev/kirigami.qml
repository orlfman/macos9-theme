// Kirigami page test, rendered by quickshot.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    width: 820
    height: 560
    visible: false
    title: "Kirigami test"
    globalDrawer: Kirigami.GlobalDrawer {
        modal: false
        collapsible: false
        actions: [
            Kirigami.Action { text: "Home"; icon.name: "go-home"; checked: true },
            Kirigami.Action { text: "Downloads"; icon.name: "folder-download" },
            Kirigami.Action { text: "Settings"; icon.name: "settings-configure" }
        ]
    }
    pageStack.initialPage: Kirigami.ScrollablePage {
        title: "Appearance"
        actions: [
            Kirigami.Action { text: "Apply"; icon.name: "dialog-ok-apply" },
            Kirigami.Action { text: "Reset"; icon.name: "edit-undo" }
        ]
        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.SearchField { Layout.fillWidth: true }
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: true
                text: "Changes will apply to new windows."
                type: Kirigami.MessageType.Information
            }
            Kirigami.FormLayout {
                Layout.fillWidth: true
                QQC2.ComboBox { Kirigami.FormData.label: "Style:"; model: ["Platinum", "Breeze"] }
                QQC2.Switch { Kirigami.FormData.label: "Animations:"; checked: true }
                QQC2.Slider { Kirigami.FormData.label: "Speed:"; value: 0.4 }
                QQC2.CheckBox { Kirigami.FormData.label: "Options:"; text: "Show icons in menus"; checked: true }
                QQC2.RadioButton { text: "Small" }
                QQC2.RadioButton { text: "Large"; checked: true }
            }
            Kirigami.AbstractCard {
                Layout.fillWidth: true
                contentItem: QQC2.Label { text: "A Kirigami card"; padding: Kirigami.Units.largeSpacing }
            }
            RowLayout {
                QQC2.Button { text: "Cancel" }
                QQC2.Button { text: "Save"; highlighted: true; icon.name: "document-save" }
                Kirigami.Chip { text: "Chip" }
            }
        }
    }
}
