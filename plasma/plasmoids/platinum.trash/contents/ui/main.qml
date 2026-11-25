// The Platinum dock's Trash. Plasma's own Trash widget forces a symbolic
// icon in panels and fills the panel's thickness; this one uses the icon
// theme's full-color user-trash / user-trash-full at the dock's task size.
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.ksvg as KSvg

PlasmoidItem {
    id: root

    readonly property bool full: trash.full
    readonly property bool inPanel: Plasmoid.formFactor === PlasmaCore.Types.Horizontal
        || Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property bool vertical: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property string summary: full ? (trash.count === 1 ? "1 item" : trash.count + " items") : "Empty"

    Plasmoid.icon: full ? "user-trash-full" : "user-trash"
    Plasmoid.title: "Trash"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    toolTipMainText: "Trash"
    toolTipSubText: summary
    preferredRepresentation: fullRepresentation

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: "Open"
            icon.name: "document-open"
            onTriggered: root.openTrash()
        },
        PlasmaCore.Action {
            text: "Empty Trash…"
            icon.name: "trash-empty"
            enabled: root.full
            // Asks first; without kdialog the Trash opens instead, so it can
            // be emptied from Dolphin (AUDIT #230).
            onTriggered: root.run("command -v kdialog > /dev/null || exit 127; "
                + "kdialog --title 'Empty Trash' --warningcontinuecancel "
                + "'Permanently delete all items in the Trash? This cannot be undone.' "
                + "--continue-label 'Empty Trash' || exit 0; ktrash6 --empty", "empty")
        }
    ]
    Plasmoid.onActivated: openTrash()

    TrashState {
        id: trash
    }

    function quote(s) {
        return "'" + String(s).replace(/'/g, "'\\''") + "'";
    }
    // Each command gets its own source name, so the same command run twice
    // isn't merged into one (AUDIT #230).
    property int serial: 0
    function run(command, tag) {
        serial += 1;
        executable.connectSource(command + " # platinum-trash " + tag + " " + serial);
    }
    // Through KIO, which knows trash:/ is a folder and opens it in the file
    // manager. Qt.openUrlExternally finds no handler for the trash: scheme
    // and asks which application to use.
    function openTrash() {
        run("kioclient exec 'trash:/'", "open");
    }
    // Moves local files to the trash in batches well under the kernel's
    // argument size limit (AUDIT #230).
    function trashFiles(urls) {
        let batch = [];
        let length = 0;
        for (const url of urls) {
            const arg = quote(url);
            if (batch.length > 0 && (batch.length >= 200 || length + arg.length > 65536)) {
                run("kioclient move " + batch.join(" ") + " trash:/", "move");
                batch = [];
                length = 0;
            }
            batch.push(arg);
            length += arg.length + 1;
        }
        if (batch.length > 0) {
            run("kioclient move " + batch.join(" ") + " trash:/", "move");
        }
    }

    P5Support.DataSource {
        id: executable
        engine: "executable"
        onNewData: (source, data) => {
            disconnectSource(source);
            if (source.indexOf(" # platinum-trash empty ") >= 0 && data["exit code"] === 127) {
                root.openTrash();
            }
        }
    }

    fullRepresentation: MouseArea {
        id: area
        readonly property int slot: Math.max(1, Math.min(width, height))
        // A square slot in a panel, like the dock's tasks; a normal icon on
        // the desktop (AUDIT #232).
        Layout.minimumWidth: !root.inPanel ? Kirigami.Units.iconSizes.large : (root.vertical ? -1 : Math.max(1, height))
        Layout.preferredWidth: !root.inPanel ? Kirigami.Units.iconSizes.huge : (root.vertical ? -1 : Math.max(1, height))
        Layout.maximumWidth: !root.inPanel ? -1 : (root.vertical ? -1 : Math.max(1, height))
        Layout.minimumHeight: !root.inPanel ? Kirigami.Units.iconSizes.large : (root.vertical ? Math.max(1, width) : -1)
        Layout.preferredHeight: !root.inPanel ? Kirigami.Units.iconSizes.huge : (root.vertical ? Math.max(1, width) : -1)
        Layout.maximumHeight: !root.inPanel ? -1 : (root.vertical ? Math.max(1, width) : -1)
        hoverEnabled: true
        activeFocusOnTab: true
        onClicked: root.openTrash()
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) {
                root.openTrash();
                event.accepted = true;
            }
        }
        Accessible.role: Accessible.Button
        Accessible.name: "Trash"
        Accessible.description: root.summary
        Accessible.onPressAction: root.openTrash()

        // The same frame the dock's tasks use when hovered or pressed.
        KSvg.FrameSvgItem {
            anchors.fill: parent
            imagePath: "widgets/tasks"
            prefix: area.pressed ? "focus" : "hover"
            visible: area.containsMouse || area.activeFocus || drop.containsDrag
        }
        Kirigami.Icon {
            anchors.centerIn: parent
            // The dock's task icons fill about three quarters of the slot
            // (32 px in the default 52 px dock).
            width: Math.max(Kirigami.Units.iconSizes.small, area.slot - Math.round(area.slot / 4))
            height: width
            source: Plasmoid.icon
            active: area.containsMouse
        }
        DropArea {
            id: drop
            anchors.fill: parent
            // Only local files can be moved to the trash (AUDIT #230).
            onEntered: drag => drag.accepted = drag.hasUrls && drag.urls.some(u => String(u).startsWith("file:"))
            onDropped: drop => {
                const urls = drop.urls.map(u => String(u)).filter(u => u.startsWith("file:"));
                if (urls.length > 0) {
                    root.trashFiles(urls);
                    // The move is done here, so the source must not delete
                    // anything itself.
                    drop.accept(Qt.CopyAction);
                }
            }
        }
    }
}
