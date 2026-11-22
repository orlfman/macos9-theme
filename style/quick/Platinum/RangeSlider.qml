// KDE's RangeSlider with the Platinum slider groove and two Platinum
// thumbs (Mac OS 9 had no two-thumb slider; the parts are the QSlider's).
// KDE's handles stay where the style draws the thumbs (same size, the
// groove's 3 px inset as padding), only hidden, so dragging and the
// keyboard work as before. SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import org.kde.desktop 1.0 as KDE

KDE.RangeSlider {
    id: control
    readonly property bool platinum: groove.active
    readonly property bool alongX: orientation === Qt.Horizontal
    property PlatinumItem groove: PlatinumItem {
        elementType: "slidergroove"
        parent: control
        width: control.width
        height: control.height
        z: -1
        visible: active
        horizontal: control.alongX
        enabled: control.enabled
    }
    property PlatinumItem firstThumb: PlatinumItem {
        elementType: "sliderthumb"
        parent: control
        width: control.width
        height: control.height
        z: 1
        visible: active
        horizontal: control.alongX
        position: control.first.visualPosition
        pressed: control.first.pressed
        keyboardFocus: control.visualFocus && control.first.handle !== null && control.first.handle.activeFocus
        enabled: control.enabled
    }
    property PlatinumItem secondThumb: PlatinumItem {
        elementType: "sliderthumb"
        parent: control
        width: control.width
        height: control.height
        z: 1
        visible: active
        horizontal: control.alongX
        position: control.second.visualPosition
        pressed: control.second.pressed
        keyboardFocus: control.visualFocus && control.second.handle !== null && control.second.handle.activeFocus
        enabled: control.enabled
    }
    Binding { target: control.background; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.first.handle; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.second.handle; property: "opacity"; value: 0; when: control.platinum }
    Binding { target: control.first.handle; property: "implicitWidth"; value: control.firstThumb.implicitWidth; when: control.platinum }
    Binding { target: control.first.handle; property: "implicitHeight"; value: control.firstThumb.implicitHeight; when: control.platinum }
    Binding { target: control.second.handle; property: "implicitWidth"; value: control.secondThumb.implicitWidth; when: control.platinum }
    Binding { target: control.second.handle; property: "implicitHeight"; value: control.secondThumb.implicitHeight; when: control.platinum }
    Binding { target: control; property: "leftPadding"; value: control.alongX ? 3 : 0; when: control.platinum }
    Binding { target: control; property: "rightPadding"; value: control.alongX ? 3 : 0; when: control.platinum }
    Binding { target: control; property: "topPadding"; value: control.alongX ? 0 : 3; when: control.platinum }
    Binding { target: control; property: "bottomPadding"; value: control.alongX ? 0 : 3; when: control.platinum }
    Binding {
        target: control; property: control.alongX ? "implicitHeight" : "implicitWidth"; when: control.platinum
        value: control.alongX ? control.groove.implicitHeight : control.groove.implicitWidth
    }
}
