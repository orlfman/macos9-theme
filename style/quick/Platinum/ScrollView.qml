// SPDX-License-Identifier: BSD-2-Clause
import QtQuick.Templates as T
import org.kde.desktop 1.0 as KDE

KDE.ScrollView {
    id: view

    // KDE creates its default bars inside its own module. Apply the same
    // press feedback to those instances and keep KDE's layout and input.
    readonly property ScrollBarPress verticalArrowPress: ScrollBarPress {
        bar: view.T.ScrollBar.vertical instanceof ScrollBar ? null : view.T.ScrollBar.vertical
    }
    readonly property ScrollBarPress horizontalArrowPress: ScrollBarPress {
        bar: view.T.ScrollBar.horizontal instanceof ScrollBar ? null : view.T.ScrollBar.horizontal
    }
}
