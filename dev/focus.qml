// QtQuick keyboard focus, one control at a time: quickshot gives each focus
// as if tabbed to and saves the window as OUT-N.png.
import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: root
    width: 980
    height: 90
    visible: false

    Row {
        id: row
        x: 16
        y: 20
        spacing: 14
        Button { id: button; text: "Button" }
        CheckBox { id: check; text: "Check"; checked: true }
        RadioButton { id: radio; text: "Radio"; checked: true }
        Switch { id: toggle; text: "Switch"; checked: true }
        Slider { id: slider; value: 0.5; width: 120 }
        ComboBox { id: combo; model: ["Combo box"] }
        SpinBox { id: spin; value: 7 }
        TabBar {
            id: tabs
            width: 180
            TabButton { text: "One" }
            TabButton { text: "Two" }
        }
    }

    // quickshot calls prepare(i) for each step and saves the window after.
    readonly property var targets: [button, check, radio, toggle, slider, combo, spin, tabs.itemAt(0)]
    property int steps: targets.length

    function prepare(i) {
        targets[i].forceActiveFocus(Qt.TabFocusReason);
    }
}
