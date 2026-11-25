// A Qt Quick header and footer TabBar (Kwi's footer tabs), drawn through
// KDE's Qt Quick bridge with the Platinum style; dev/check-tabs.sh checks the
// footer is the header upside down. Blank titles: only the shapes count.
import QtQuick
import QtQuick.Controls

Window {
    width: 360
    height: 220
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
    Timer {
        interval: 600
        running: true
        onTriggered: console.log("BARS", top.x, top.y, top.width, top.height, bottom.y, bottom.height)
    }
}
