// Checks that switches stay switches with the Platinum Qt Quick style
// (drawn as check boxes, PLAN.md "Plan: Qt Quick menus, tooltips and
// switches" step 5): for a Switch and a SwitchDelegate, Space toggles them
// and screen readers see their role and checked state. Prints one line per
// control; dev/check-quick.sh compares the output with KDE's own style.
#include <QAccessible>
#include <QApplication>
#include <QQmlApplicationEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTest>
#include <cstdio>

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    QQmlApplicationEngine engine;
    engine.loadData(R"(
import QtQuick
import QtQuick.Controls as QQC2
QQC2.ApplicationWindow {
    width: 300; height: 200; visible: true
    Column {
        QQC2.Switch { objectName: "switch"; text: "Switch" }
        QQC2.SwitchDelegate { objectName: "switchdelegate"; text: "Switch delegate"; width: 200 }
    }
})");
    if (engine.rootObjects().isEmpty()) {
        return 2;
    }
    auto *window = qobject_cast<QQuickWindow *>(engine.rootObjects().constFirst());
    QTest::qWaitForWindowExposed(window);
    for (const char *name : {"switch", "switchdelegate"}) {
        auto *item = window->findChild<QQuickItem *>(QLatin1String(name));
        if (!item) {
            printf("%s missing\n", name);
            continue;
        }
        item->forceActiveFocus(Qt::TabFocusReason);
        const bool before = item->property("checked").toBool();
        QTest::keyClick(window, Qt::Key_Space);
        QTest::qWait(50);
        const bool after = item->property("checked").toBool();
        QAccessibleInterface *a = QAccessible::queryAccessibleInterface(item);
        printf("%s space-toggles=%d role=%d checkable=%d checked=%d\n", name, before != after, a ? int(a->role()) : -1,
               a ? int(a->state().checkable) : -1, a ? int(a->state().checked) : -1);
    }
    return 0;
}
