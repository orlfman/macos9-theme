// SPDX-License-Identifier: BSD-2-Clause
import org.kde.desktop 1.0 as KDE

KDE.ScrollBar {
    id: control

    readonly property ScrollBarPress arrowPress: ScrollBarPress {
        bar: control
    }
}
