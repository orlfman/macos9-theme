// Spike: the same menu in Qt Quick, opened as an item (popupType Item) so
// the window grab holds it; step 0 = first row selected, step 1 = last.
import QtQuick
import QtQuick.Controls as QQC2

QQC2.ApplicationWindow {
    id: root
    width: 600
    height: 420
    visible: false
    color: "#ff00ff" // to see the menu's own pixels against
    property int steps: 2
    function prepare(i) {
        menu.popup(root.contentItem, 10, 10)
        console.log("POS", menu.x, menu.y, "parent", menu.parent, "window", root.width, root.height, "type", menu.popupType)
        menu.currentIndex = i === 0 ? 0 : menu.count - 1
        if (i === 1) {
            console.log("MENU", menu.width, menu.height)
            for (let n = 0; n < menu.count; ++n) {
                const it = menu.itemAt(n)
                const p = it.mapToItem(menu.background, 0, 0)
                console.log("ROW", Math.round(p.x), Math.round(p.y), Math.round(it.width), Math.round(it.height))
            }
        }
    }
    QQC2.Menu {
        id: menu
        x: 0; y: 0
        popupType: QQC2.Popup.Item
        QQC2.MenuItem { text: "First" }
        QQC2.MenuItem { text: "Second" }
        QQC2.MenuSeparator {}
        QQC2.MenuItem { text: "Checked"; checkable: true; checked: true }
        QQC2.Action { text: "Save"; shortcut: "Ctrl+S" }
        QQC2.Menu { title: "More"; QQC2.MenuItem { text: "Inside" } }
        QQC2.MenuItem { text: "Last" }
    }
}
