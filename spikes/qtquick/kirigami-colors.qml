// Spike probe: Kirigami's colors in every color set.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

QQC2.ApplicationWindow {
    width: 200; height: 100; visible: false
    Repeater {
        model: [["View", Kirigami.Theme.View], ["Window", Kirigami.Theme.Window], ["Button", Kirigami.Theme.Button],
                ["Selection", Kirigami.Theme.Selection], ["Tooltip", Kirigami.Theme.Tooltip],
                ["Complementary", Kirigami.Theme.Complementary], ["Header", Kirigami.Theme.Header]]
        delegate: Item {
            required property var modelData
            Kirigami.Theme.colorSet: modelData[1]
            Kirigami.Theme.inherit: false
            Component.onCompleted: console.log("COLORS", modelData[0], "text", Kirigami.Theme.textColor, "bg", Kirigami.Theme.backgroundColor,
                "alt", Kirigami.Theme.alternateBackgroundColor, "hl", Kirigami.Theme.highlightColor, "hltext", Kirigami.Theme.highlightedTextColor,
                "link", Kirigami.Theme.linkColor, "neg", Kirigami.Theme.negativeTextColor, "pos", Kirigami.Theme.positiveTextColor,
                "focus", Kirigami.Theme.focusColor, "hover", Kirigami.Theme.hoverColor, "disabled", Kirigami.Theme.disabledTextColor)
        }
    }
    Component.onCompleted: console.log("COLORS units gridUnit", Kirigami.Units.gridUnit, "small", Kirigami.Units.smallSpacing, "large", Kirigami.Units.largeSpacing, "corner", Kirigami.Units.cornerRadius, "font", Kirigami.Theme.defaultFont)
}
