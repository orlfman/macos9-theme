// Window decoration previews, drawn by KWin's own preview component (the one
// System Settings uses), rendered by decoshot, which also sets hover and
// press states from hoverButton and pressButton (KDecoration3 button types:
// 0 Menu, 3 Minimize, 4 Maximize, 5 Close, 7 Shade).
//
// The previews are sized like the reference windows so their frames can be
// diffed with the captures: 416x246 is the Mac OS window in
// reference/window-document-active.png without its drop shadow.
//
// Adapted from the user's windows2000-union project (BSD-2-Clause).
import QtQuick
import QtQuick.Window
import org.kde.kwin.private.kdecoration as KDecoration

Window {
    id: root
    width: 900
    height: 560
    visible: false
    // The Mac OS 9 default desktop's base color.
    color: "#63639c"

    KDecoration.Bridge {
        id: bridgeItem
        plugin: "platinum"
        theme: ""
    }

    KDecoration.Settings {
        id: settingsItem
        bridge: bridgeItem.bridge
        borderSizesIndex: 3 // Normal
    }

    component Preview: KDecoration.Decoration {
        property string caption: "Mac OS"
        property bool isActive: true
        property int hoverButton: -1
        property int pressButton: -1

        width: 416
        height: 246
        bridge: bridgeItem.bridge
        settings: settingsItem
        drawBackground: true

        Component.onCompleted: {
            client.caption = caption;
            client.iconName = "drive-harddisk";
            client.active = isActive;
        }
    }

    Preview {
        objectName: "active"
        x: 10
        y: 10
    }
    Preview {
        objectName: "inactive"
        x: 460
        y: 10
        isActive: false
    }
    Preview {
        objectName: "press-close"
        x: 10
        y: 280
        caption: "This Is A Very Long Folder Name That Will Not Fit"
        hoverButton: 5
        pressButton: 5
    }
    Preview {
        objectName: "press-maximize"
        x: 460
        y: 280
        caption: "Untitled"
        hoverButton: 4
        pressButton: 4
    }
}
