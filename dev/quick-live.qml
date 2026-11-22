// A visible Qt Quick window for dev/app-test.sh (the nested KWin): opens
// its own pop-up after a moment (no input needed), so the shot shows how
// pop-ups look in a real session. popup=menu (default), combo, tooltip,
// menubar, windowmenu (a menu as its own window) or windowclick (the same,
// opened by a click; send one with dev/build/fakeinput), after "--".
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

QQC2.ApplicationWindow {
    id: root
    width: 420
    height: 300
    visible: true
    title: "Qt Quick pop-ups"
    menuBar: QQC2.MenuBar {
        QQC2.Menu {
            id: fileMenu
            title: "File"
            QQC2.MenuItem { text: "New" }
            QQC2.MenuItem { text: "Open…" }
        }
        QQC2.Menu { title: "Edit"; QQC2.MenuItem { text: "Copy" } }
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        QQC2.ComboBox { id: combo; model: ["Lavender", "Purple", "Platinum"]; currentIndex: 1 }
        QQC2.Switch { text: "Switch"; checked: true }
        QQC2.Button {
            id: help
            text: "Help"
            QQC2.ToolTip.text: "A help balloon"
            QQC2.ToolTip.delay: 0
            QQC2.ToolTip.timeout: -1
        }
        Item { Layout.fillHeight: true }
    }
    QQC2.Menu {
        id: menu
        QQC2.MenuItem { text: "First" }
        QQC2.MenuItem { text: "Second" }
        QQC2.MenuSeparator {}
        QQC2.MenuItem { text: "Checked"; checkable: true; checked: true }
        QQC2.Action { text: "Save"; shortcut: "Ctrl+S" }
        QQC2.MenuItem { text: "Last" }
    }
    // The same as its own window (apps can ask for that).
    QQC2.Menu {
        id: windowMenu
        popupType: QQC2.Popup.Window
        QQC2.MenuItem { text: "First" }
        QQC2.MenuItem { text: "Second" }
        QQC2.MenuSeparator {}
        QQC2.MenuItem { text: "Last" }
    }
    // popup=windowclick: the window menu opens from a real click (Wayland
    // gives a pop-up window its grab only for an input event).
    MouseArea {
        anchors.fill: parent
        enabled: Qt.application.arguments.indexOf("popup=windowclick") >= 0
        onClicked: (mouse) => { windowMenu.popup(root.contentItem, mouse.x, mouse.y); windowMenu.currentIndex = 0 }
    }
    Timer {
        interval: 1500
        running: true
        onTriggered: {
            const which = Qt.application.arguments.find(a => a.startsWith("popup=")) || "popup=menu"
            if (which === "popup=combo") combo.popup.open()
            else if (which === "popup=tooltip") help.QQC2.ToolTip.visible = true
            else if (which === "popup=menubar") fileMenu.open()
            else if (which === "popup=windowmenu") { windowMenu.popup(root.contentItem, 300, 200); windowMenu.currentIndex = 0 }
            else { menu.popup(root.contentItem, 140, 60); menu.currentIndex = 0 }
            console.log("LIVE popupType", menu.popupType, combo.popup.popupType, "window", Window.window)
        }
    }
}
