// The Qt Quick counterparts of dev/quickref.cpp's widget pieces, one per
// step on a magenta window (so dev/check-quick.sh finds each piece by its
// own pixels): 0/1 menu with the first/last row selected, 2 the combo
// box's open list, 3 the menu bar, 4 a checked switch, 5 a tooltip, 6 a
// dialog (its frame), 7 a range slider, 8 a drawer (its open edge), 9 a
// combo box narrower than its items (its list widens as QComboBox's). With
// --switch-to-fusion it switches the app to Fusion first (the fallback
// check: it must then look exactly like KDE's own style).
import QtQuick
import QtQuick.Controls as QQC2

QQC2.ApplicationWindow {
    id: root
    width: 480
    height: 360
    visible: false
    color: "#ff00ff"
    property int steps: 10
    property int step: -1
    // dev/check-quick.sh's fallback run: switch the app's style to Fusion
    // first (only works with M9_QUICK_TEST set and this project's style).
    property bool switchedAway: false
    function prepare(i) {
        if (!switchedAway && Qt.application.arguments.indexOf("--switch-to-fusion") >= 0) {
            switchedAway = true
            if (toggle.box) toggle.box.setApplicationStyle("Fusion")
        }
        step = i
        if (i === 0) menu.popup(root.contentItem, 20, 20)
        if (i === 0 || i === 1) menu.currentIndex = i === 0 ? 0 : menu.count - 1
        else menu.close()
        if (i === 2) combo.popup.open()
        if (i === 9) narrowCombo.popup.open(); else narrowCombo.popup.close()
        // (no fade-in, so the shot holds the finished tooltip)
        tipAnchor.QQC2.ToolTip.toolTip.enter = null
        tipAnchor.QQC2.ToolTip.toolTip.exit = null
        tipAnchor.QQC2.ToolTip.visible = i === 5
        // (no fade or slide, so the shots hold the finished pop-ups)
        dialog.enter = null; dialog.exit = null
        if (i === 6) dialog.open(); else dialog.close()
        // (a drawer slides by its position; set it rather than wait)
        drawer.enter = null; drawer.exit = null
        if (i === 8) { drawer.open(); drawer.position = 1 } else drawer.close()
        // Where each piece is, for dev/check-quick.sh (after layout).
        logLater.step = i
        logLater.restart()
    }
    Timer {
        id: logLater
        property int step: -1
        interval: 80
        onTriggered: {
            const i = step
            if (i === 0 || i === 1) console.log("REGION", "menu-" + i, menu.x, menu.y)
            if (i === 2) {
                const p = (combo.listPanel || combo.popup.background).mapToItem(root.contentItem, 0, 0)
                console.log("REGION combo", Math.round(p.x), Math.round(p.y))
            }
            if (i === 3) console.log("REGION menubar", 0, 0)
            if (i === 4) {
                const p = (toggle.box || toggle.indicator).mapToItem(root.contentItem, 0, 0)
                console.log("REGION checkbox", Math.round(p.x), Math.round(p.y))
            }
            if (i === 5) {
                const tip = tipAnchor.QQC2.ToolTip.toolTip
                const p = (tip.balloon || tip.background).mapToItem(root.contentItem, 0, 0)
                console.log("REGION tooltip", Math.round(p.x), Math.round(p.y))
            }
            if (i === 6) {
                const p = (dialog.frame || dialog.background).mapToItem(root.contentItem, 0, 0)
                console.log("REGION dialog", Math.round(p.x), Math.round(p.y))
            }
            if (i === 7) {
                console.log("REGION rangeslider", range.x, range.y)
                // KDE's (hidden) handles take the clicks: where they are.
                console.log("HANDLES", range.first.handle.x, range.second.handle.x)
            }
            if (i === 8) console.log("REGION drawer", 0, 0, drawer.width, drawer.height)
            if (i === 9) {
                const p = (narrowCombo.listPanel || narrowCombo.popup.background).mapToItem(root.contentItem, 0, 0)
                console.log("REGION combo-narrow", Math.round(p.x), Math.round(p.y))
            }
        }
    }
    QQC2.Menu {
        id: menu
        QQC2.MenuItem { text: "First" }
        QQC2.MenuItem { text: "Second" }
        QQC2.MenuItem { text: "Open"; icon.name: "document-open" }
        QQC2.MenuSeparator {}
        QQC2.MenuItem { text: "Checked"; checkable: true; checked: true }
        QQC2.Action { text: "Save"; shortcut: "Ctrl+S" }
        QQC2.Menu { title: "More"; QQC2.MenuItem { text: "Inside" } }
        QQC2.MenuItem { text: "Last" }
    }
    QQC2.ComboBox {
        id: combo
        x: 100; y: 100
        width: 140  // wider than its rows need in any font; dev/quickref.cpp's widget combo box gets the same width
        visible: root.step === 2
        model: ["Lavender", "Purple", "Platinum"]
        currentIndex: 1
    }
    QQC2.ComboBox {
        id: narrowCombo
        x: 300; y: 100
        width: 60  // narrower than any item; dev/quickref.cpp's gets the same width
        visible: root.step === 9
        model: ["Lavender", "Purple", "Platinum"]
        currentIndex: 1
    }
    QQC2.MenuBar {
        width: 200
        visible: root.step === 3
        QQC2.Menu { title: "File"; QQC2.MenuItem { text: "Open" } }
        QQC2.Menu { title: "Edit"; QQC2.MenuItem { text: "Copy" } }
    }
    QQC2.Switch {
        id: toggle
        x: 20; y: 20
        visible: root.step === 4
        text: "Switch on"
        checked: true
    }
    QQC2.Dialog {
        id: dialog
        width: 220
        height: 120
        title: "Dialog"
    }
    QQC2.RangeSlider {
        id: range
        x: 20; y: 150
        width: 200
        visible: root.step === 7
        from: 0; to: 100
        first.value: 20
        second.value: 70
    }
    QQC2.Drawer {
        id: drawer
        width: 160
        height: root.height
    }
    Item {
        id: tipAnchor
        x: 100; y: 200; width: 10; height: 10
        QQC2.ToolTip.text: "A help balloon"
        QQC2.ToolTip.delay: 0
        QQC2.ToolTip.timeout: -1
    }
}
