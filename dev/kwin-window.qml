// A plain window for kwin-test.sh; its title is the last argument, and a
// "maximized" argument before it opens it maximized.
import QtQuick
import QtQuick.Controls

ApplicationWindow {
    width: 520
    height: 300
    visible: true
    visibility: Qt.application.arguments.indexOf("maximized") >= 0 ? Window.Maximized : Window.AutomaticVisibility
    title: Qt.application.arguments[Qt.application.arguments.length - 1]

    Label {
        anchors.centerIn: parent
        text: "Decoration test window"
    }
}
