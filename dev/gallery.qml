// Offscreen QtQuick Controls gallery: renders once, saves a PNG, quits.
// Usage: qml6 gallery.qml -- output.png
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 820
    height: 560
    visible: false
    title: "Quick gallery"

    readonly property string out: {
        const args = Qt.application.arguments;
        return args.length > 0 && args[args.length - 1].endsWith(".png") ? args[args.length - 1] : "quick.png";
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            spacing: 8
            Button { text: "Button" }
            Button { text: "Default"; highlighted: true }
            Button { text: "Checked"; checkable: true; checked: true }
            Button { text: "Disabled"; enabled: false }
            Button { text: "Flat"; flat: true }
            ToolButton { icon.name: "document-open"; text: "Tool"; display: AbstractButton.TextBesideIcon }
            RoundButton { icon.name: "list-add" }
        }

        RowLayout {
            spacing: 8
            CheckBox { text: "Unchecked" }
            CheckBox { text: "Checked"; checked: true }
            CheckBox { text: "Partial"; tristate: true; checkState: Qt.PartiallyChecked }
            CheckBox { text: "Disabled"; checked: true; enabled: false }
            RadioButton { text: "Radio" }
            RadioButton { text: "Selected"; checked: true }
        }

        RowLayout {
            spacing: 8
            Switch { text: "Off" }
            Switch { text: "On"; checked: true }
            Switch { text: "Disabled"; enabled: false }
            Slider { value: 0.6; Layout.preferredWidth: 180 }
            ProgressBar { value: 0.6; Layout.preferredWidth: 160 }
        }

        RowLayout {
            spacing: 8
            TextField { id: focused; text: "Focused text"; focus: true }
            TextField { placeholderText: "Placeholder" }
            SpinBox { value: 42 }
            ComboBox { model: ["Combo box", "Second", "Third"] }
            ComboBox { editable: true; model: ["Editable"] }
        }

        TabBar {
            Layout.preferredWidth: 360
            currentIndex: 0
            TabButton { text: "General" }
            TabButton { text: "Appearance" }
            TabButton { text: "Advanced" }
        }

        RowLayout {
            spacing: 12
            Layout.fillHeight: true

            Frame {
                Layout.preferredWidth: 260
                Layout.fillHeight: true
                padding: 4
                ListView {
                    anchors.fill: parent
                    clip: true
                    model: 8
                    currentIndex: 1
                    delegate: ItemDelegate {
                        width: ListView.view.width
                        text: "Item " + (index + 1)
                        icon.name: "folder"
                        highlighted: ListView.isCurrentItem
                    }
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AlwaysOn }
                }
            }

            Pane {
                id: menuHost
                Layout.fillWidth: true
                Layout.fillHeight: true
                Menu {
                    id: menu
                    x: 10
                    y: 0
                    MenuItem { text: "Copy"; icon.name: "edit-copy" }
                    MenuItem { text: "Paste"; icon.name: "edit-paste" }
                    MenuItem { text: "Disabled item"; enabled: false }
                    MenuSeparator {}
                    MenuItem { text: "Checkable item"; checkable: true; checked: true }
                    Menu { title: "Submenu"; MenuItem { text: "Inner" } }
                }
                ToolTip {
                    x: 260
                    y: 20
                    visible: true
                    text: "A tooltip"
                }
            }
        }
    }

    Timer {
        interval: 200
        running: true
        onTriggered: {
            menu.open();
            menu.currentIndex = 1;
        }
    }

}
