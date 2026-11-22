// Spike probe: where each control comes from, and Kirigami's values.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ApplicationWindow {
    id: root
    width: 420
    height: 300
    visible: false
    QQC2.Button { id: button; x: 10; y: 10; text: "Button" }
    QQC2.ToolTip { id: tip; text: "Balloon"; x: 10; y: 60; popupType: QQC2.Popup.Item; visible: true }
    QQC2.Menu {
        id: menu
        popupType: QQC2.Popup.Item
        QQC2.MenuItem { id: item1; text: "First" }
        QQC2.MenuSeparator { id: sep }
    }
    Component.onCompleted: {
        console.log("PROBE button.background:", button.background)
        console.log("PROBE tooltip:", tip.objectName || "(KDE's)", "background:", tip.background)
        console.log("PROBE menu:", menu.objectName || "(KDE's)", "background:", menu.background)
        console.log("PROBE menuitem:", item1.objectName || "(KDE's)", "separator:", sep.objectName || "(KDE's)")
        console.log("PROBE kirigami textColor", Kirigami.Theme.textColor, "highlight", Kirigami.Theme.highlightColor, "gridUnit", Kirigami.Units.gridUnit)
    }
}
