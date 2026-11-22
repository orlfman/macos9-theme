// Keyboard checks for the Platinum Qt Quick style: switches stay switches
// (drawn as check boxes, PLAN.md "Plan: Qt Quick menus, tooltips and
// switches" step 5): for a Switch and a SwitchDelegate, Space toggles them
// and screen readers see their role and checked state; and keyboard focus
// shows on a RangeSlider's handle and on a QSlider (AUDIT.md finding 52).
// Prints one line per check; dev/check-quick.sh compares the output with
// KDE's own style.
#include <QAccessible>
#include <QApplication>
#include <QImage>
#include <QSlider>
#include <QVBoxLayout>
#include <QWidget>
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
        QQC2.RangeSlider { objectName: "range"; width: 200; from: 0; to: 100; first.value: 20; second.value: 70 }
        QQC2.Slider { objectName: "slider"; width: 200; from: 0; to: 100; value: 40 }
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
    // Keyboard focus shows on the range slider's first handle, and on a
    // Slider (KDE's, drawn through the QStyle).
    for (const char *name : {"range", "slider"}) {
        auto *range = window->findChild<QQuickItem *>(QLatin1String(name));
        if (!range) {
            continue;
        }
        window->contentItem()->forceActiveFocus();
        QTest::qWait(50);
        const QRectF area = range->mapRectToScene(QRectF(0, 0, range->width(), range->height()));
        const QImage before = window->grabWindow().copy(area.toAlignedRect());
        range->forceActiveFocus(Qt::TabFocusReason);
        QTest::qWait(50);
        const QImage after = window->grabWindow().copy(area.toAlignedRect());
        printf("%s focus-shows=%d\n", name, before != after);
    }
    // And on a QSlider moved to by the Tab key.
    {
        QWidget host;
        auto *layout = new QVBoxLayout(&host);
        auto *first = new QSlider(Qt::Horizontal);
        auto *slider = new QSlider(Qt::Horizontal);
        layout->addWidget(first);
        layout->addWidget(slider);
        slider->setValue(30);
        host.resize(220, 80);
        host.show();
        QTest::qWaitForWindowExposed(&host);
        first->setFocus(Qt::OtherFocusReason);
        QTest::qWait(50);
        const QImage before = slider->grab().toImage();
        QTest::keyClick(&host, Qt::Key_Tab);
        QTest::qWait(50);
        const QImage after = slider->grab().toImage();
        printf("qslider focus-shows=%d (has focus %d)\n", before != after, slider->hasFocus());
    }
    return 0;
}
