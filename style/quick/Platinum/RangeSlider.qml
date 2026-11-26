// KDE's RangeSlider with the Platinum slider groove and two Platinum
// thumbs (Mac OS 9 had no two-thumb slider; the parts are the QSlider's).
// The thumbs follow KDE's hidden handles, sized to the Platinum artwork
// and inset 3 px on the travel axis. KDE handles dragging and keyboard input.
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.RangeSlider {
    id: control
    readonly property bool platinum: groove.active
    readonly property bool alongX: orientation === Qt.Horizontal
    readonly property int thumbInset: 3

    property PlatinumItem groove: PlatinumItem {
        elementType: "slidergroove"
        parent: control
        x: control.alongX ? 0 : Math.round((control.width - width) / 2)
        y: control.alongX ? Math.round((control.height - height) / 2) : 0
        width: control.alongX ? control.width : implicitWidth
        height: control.alongX ? implicitHeight : control.height
        z: -1
        visible: active
        horizontal: control.alongX
        enabled: control.enabled
    }

    component Thumb: PlatinumItem {
        required property Item handle
        elementType: "sliderthumb"
        parent: control
        // Leave the QStyle's along-axis inset around the sprite and its
        // keyboard focus marks. Use the KDE handle's actual position.
        x: handle ? Math.round(handle.x + (handle.width - width) / 2) : 0
        y: handle ? Math.round(handle.y + (handle.height - height) / 2) : 0
        width: implicitWidth + (horizontal ? 2 * control.thumbInset : 0)
        height: implicitHeight + (horizontal ? 0 : 2 * control.thumbInset)
        z: 1
        visible: active && handle !== null
        horizontal: control.alongX
        keyboardFocus: control.visualFocus && handle !== null && handle.activeFocus
        enabled: control.enabled
    }
    property PlatinumItem firstThumb: Thumb {
        handle: control.first.handle
        pressed: control.first.pressed
    }
    property PlatinumItem secondThumb: Thumb {
        handle: control.second.handle
        pressed: control.second.pressed
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.first.handle; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.second.handle; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.first.handle; property: "implicitWidth"; value: control.firstThumb.implicitWidth; when: control.platinum }
    Binding { target: control.first.handle; property: "implicitHeight"; value: control.firstThumb.implicitHeight; when: control.platinum }
    Binding { target: control.second.handle; property: "implicitWidth"; value: control.secondThumb.implicitWidth; when: control.platinum }
    Binding { target: control.second.handle; property: "implicitHeight"; value: control.secondThumb.implicitHeight; when: control.platinum }
    Binding { target: control; property: "leftPadding"; value: control.alongX ? control.thumbInset : 0; when: control.platinum }
    Binding { target: control; property: "rightPadding"; value: control.alongX ? control.thumbInset : 0; when: control.platinum }
    Binding { target: control; property: "topPadding"; value: control.alongX ? 0 : control.thumbInset; when: control.platinum }
    Binding { target: control; property: "bottomPadding"; value: control.alongX ? 0 : control.thumbInset; when: control.platinum }
    Binding {
        target: control; property: control.alongX ? "implicitHeight" : "implicitWidth"; when: control.platinum
        value: control.alongX ? control.groove.implicitHeight : control.groove.implicitWidth
    }
}
