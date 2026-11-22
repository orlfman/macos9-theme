// Spike: the overrides follow the application's style at run time.
import QtQuick
import QtQuick.Controls as QQC2

QQC2.ApplicationWindow {
    width: 300; height: 200; visible: false
    property int steps: 3
    QQC2.ToolTip { id: tip; text: "A help balloon"; x: 10; y: 10; timeout: -1; delay: 0 }
    QQC2.Menu { id: menu; QQC2.MenuItem { id: row; text: "Row" } }
    function prepare(i) {
        if (i === 1) tip.balloon.setApplicationStyle("Fusion")
        if (i === 2) tip.balloon.setApplicationStyle("Platinum")
        tip.open()
        menu.popup()
        const bg = tip.background
        console.log("SWITCH step", i, "platinum", tip.platinum, "tip opened", tip.opened, "menu opened", menu.opened,
                    "KDE tip bg", bg, "explicit visible", bg.QQuickItem ? "" : "", "opacity", bg.opacity, "w", bg.width, "h", bg.height,
                    "parent", bg.parent, "parent visible", bg.parent ? bg.parent.visible : "-", "color", bg.color)
    }
}
