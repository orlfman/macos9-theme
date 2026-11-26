// A Qt Quick header and footer TabBar (Kwi's footer tabs), drawn through
// KDE's Qt Quick bridge with the Platinum style; dev/check-tabs.sh checks the
// footer is the header upside down. Blank titles: only the shapes count.
import QtQuick
import QtQuick.Controls

Window {
    width: 360
    height: 330
    visible: true
    color: "#ffffff"
    TabBar {
        id: top
        x: 20
        y: 10
        width: 300
        position: TabBar.Header
        currentIndex: 1
        Repeater {
            model: 3
            TabButton { text: "" }
        }
    }
    TabBar {
        id: bottom
        x: 20
        y: 210 - height
        width: 300
        position: TabBar.Footer
        currentIndex: 1
        Repeater {
            model: 3
            TabButton { text: "" }
        }
    }
    // Taller tabs, as Kwi makes them (it reserves room for a progress bar):
    // the face must reach the bar's pane edge (AUDIT.md #266).
    TabBar {
        id: tallTop
        x: 20
        y: 220
        width: 300
        position: TabBar.Header
        currentIndex: 1
        Repeater {
            model: 3
            TabButton { text: ""; implicitHeight: 33; implicitWidth: 100 }
        }
    }
    TabBar {
        id: tallBottom
        x: 20
        y: 320 - height
        width: 300
        position: TabBar.Footer
        currentIndex: 1
        Repeater {
            model: 3
            TabButton { text: ""; implicitHeight: 33; implicitWidth: 100 }
        }
    }
    Timer {
        interval: 600
        running: true
        onTriggered: {
            console.log("BARS", top.x, top.y, top.width, top.height, bottom.y, bottom.height)
            console.log("TALL", tallTop.x, tallTop.y, tallTop.width, tallTop.height, tallBottom.y, tallBottom.height)
        }
    }
}
