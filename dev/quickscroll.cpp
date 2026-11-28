// Qt Quick scroll bar pressed-state and KDE fallback checks.
// SPDX-License-Identifier: BSD-2-Clause
#include <QApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QImage>
#include <QPainter>
#include <QQmlApplicationEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QStyle>
#include <QStyleOptionSlider>
#include <QTest>
#include <array>
#include <cstdio>

static QStyleOptionSlider styleOption(const QRect &rect, Qt::Orientation orientation)
{
    QStyleOptionSlider option;
    option.rect = rect;
    option.orientation = orientation;
    option.state = QStyle::State_Enabled | QStyle::State_Active;
    option.subControls = QStyle::SC_All;
    option.maximum = 100;
    option.pageStep = 30;
    option.singleStep = 1;
    option.sliderPosition = option.sliderValue = 30;
    option.palette = QApplication::palette();
    return option;
}

static QImage widgetArrow(QStyleOptionSlider option, QStyle::SubControl subcontrol, const QRect &arrow, bool pressed)
{
    if (pressed) {
        option.state |= QStyle::State_Sunken;
    }
    option.activeSubControls = subcontrol;
    QImage image(option.rect.size(), QImage::Format_RGB32);
    image.fill(Qt::magenta);
    QPainter painter(&image);
    QApplication::style()->drawComplexControl(QStyle::CC_ScrollBar, &option, &painter);
    painter.end();
    return image.copy(arrow);
}

static bool checkBar(QQuickWindow *window, const char *name, QQuickItem *bar, bool fusion)
{
    bool passed = true;
    const auto check = [&](bool ok, const char *what) {
        if (!ok) {
            fprintf(stderr, "%s: %s\n", name, what);
            passed = false;
        }
        return ok;
    };
    if (!check(bar && bar->isVisible(), "missing visible scrollbar")) {
        return false;
    }
    const auto area = bar->property("background").value<QQuickItem *>();
    if (!check(area, "missing KDE scrollbar background")) {
        return false;
    }
    const auto sunkenPainters = [&] {
        int count = 0;
        for (auto *item : area->childItems()) {
            if (item->property("elementType").toString() == QStringLiteral("scrollbar")
                && item->property("sunken").toBool()) {
                ++count;
            }
        }
        return count;
    };
    const auto orientation = bar->property("orientation").value<Qt::Orientation>();
    const QRect barRect = bar->mapRectToScene(QRectF(0, 0, bar->width(), bar->height())).toAlignedRect();
    const auto option = styleOption(QRect(QPoint(0, 0), barRect.size()), orientation);
    const std::array directions = {QStyle::SC_ScrollBarAddLine, QStyle::SC_ScrollBarSubLine};
    const auto part = [&](QStyle::SubControl sc) {
        return QApplication::style()->subControlRect(QStyle::CC_ScrollBar, &option, sc);
    };
    const std::array arrows = {part(directions[0]), part(directions[1])};
    const std::array points = {arrows[0].center() + barRect.topLeft(), arrows[1].center() + barRect.topLeft()};
    const auto grab = [&](const QRect &rect) {
        return window->grabWindow().convertToFormat(QImage::Format_RGB32).copy(rect.translated(barRect.topLeft()));
    };

    const QPoint track = barRect.center();
    const auto position = [&] { return bar->property("position").toDouble(); };

    // Let both upstream painters reach their normal hover opacities before
    // comparing screenshots. Other checks read changes while the button is held.
    QTest::mouseMove(window, track, 0);
    QTest::qWait(300);
    QCryptographicHash trace(QCryptographicHash::Sha256);
    const QString dump = qEnvironmentVariable("M9_SCROLL_DUMP");
    for (size_t i = 0; i < arrows.size(); ++i) {
        if (!check(!arrows[i].isEmpty() && barRect.contains(points[i]), "invalid arrow geometry")) {
            continue;
        }
        const size_t opposite = 1 - i;
        QTest::mouseMove(window, points[i], 0);
        const QImage idle = grab(arrows[i]);
        const QImage otherIdle = grab(arrows[opposite]);
        const QImage expected = fusion ? idle : widgetArrow(option, directions[i], arrows[i], true);
        const double before = position();
        QTest::mousePress(window, Qt::LeftButton, {}, points[i], 0);
        check(QTest::qWaitFor([&] { return position() != before; }, 300), "left press did not scroll");
        const QImage held = grab(arrows[i]);
        check(sunkenPainters() == (fusion ? 0 : 1), "unexpected number of pressed painters");
        if (!fusion) {
            check(idle == widgetArrow(option, directions[i], arrows[i], false), "idle arrow differs from Qt Widgets");
            check(held == expected && held != idle,
                  i == 0 ? "increase arrow press pixels" : "decrease arrow press pixels");
            check(grab(arrows[opposite]) == otherIdle, "opposite arrow changed during press");
            if (!dump.isEmpty() && QByteArrayView(name) == "vertical") {
                const QDir directory(dump);
                const QString arrowName = i == 0 ? QStringLiteral("addline") : QStringLiteral("subline");
                idle.save(directory.filePath(arrowName + QStringLiteral("-idle.png")));
                held.save(directory.filePath(arrowName + QStringLiteral("-down.png")));
                expected.save(directory.filePath(arrowName + QStringLiteral("-down-ref.png")));
            }
        }
        QTest::mouseMove(window, points[opposite], 0);
        const QImage away = grab(arrows[i]);
        const QImage crossed = grab(arrows[opposite]);
        if (!fusion) {
            check(away == idle, "original arrow stays down away from press");
            check(crossed == otherIdle, "press transferred to the opposite arrow");
        }
        QTest::mouseMove(window, points[i], 0);
        const QImage returned = grab(arrows[i]);
        if (!fusion) {
            // A parent Flickable may take the grab during the pointer move.
            const bool stillHeld = area->property("pressed").toBool();
            check(returned == (stillHeld ? expected : idle), "incorrect arrow state after returning");
        }
        QTest::mouseRelease(window, Qt::LeftButton, {}, points[i], 0);
        const QImage released = grab(arrows[i]);
        check(sunkenPainters() == 0, "release left a painter pressed");
        if (!fusion) {
            check(released == idle, "release left an arrow pressed");
        } else {
            for (const auto &image : {idle, held, away, crossed, returned, released}) {
                trace.addData(QByteArrayView(reinterpret_cast<const char *>(image.constBits()), image.sizeInBytes()));
            }
        }
    }

    if (!fusion && QByteArrayView(name) == "vertical") {
        // Start paging below the thumb, then cross to the lower arrow.
        const QPoint pagePoint = barRect.topLeft() + QPoint(barRect.width() / 2, barRect.height() * 2 / 3);
        QTest::mouseMove(window, pagePoint, 0);
        const QImage idle = grab(arrows[0]);
        const double before = position();
        QTest::mousePress(window, Qt::LeftButton, {}, pagePoint, 0);
        check(QTest::qWaitFor([&] { return position() > before + 0.1; }, 300), "page press did not advance a page");
        QTest::mouseMove(window, points[0], 0);
        check(sunkenPainters() == 0 && grab(arrows[0]) == idle, "page press transferred to an arrow");
        QTest::mouseRelease(window, Qt::LeftButton, {}, points[0], 0);

        QTest::mousePress(window, Qt::MiddleButton, {}, points[0], 0);
        check(sunkenPainters() == 0 && grab(arrows[0]) == idle, "middle click pushed a scrollbar part");
        QTest::mouseRelease(window, Qt::MiddleButton, {}, points[0], 0);

        QTest::mouseMove(window, points[1], 0);
        QTest::mousePress(window, Qt::LeftButton, {}, points[1], 0);
        check(sunkenPainters() == 1, "missing press before disable");
        bar->setEnabled(false);
        check(!area->property("pressed").toBool() && sunkenPainters() == 0, "disable did not cancel the press");
        const double stopped = position();
        QTest::qWait(190);
        check(position() == stopped, "repeat continued after cancelling the press");
        QTest::mouseRelease(window, Qt::LeftButton, {}, points[1], 0);
        bar->setEnabled(true);
        QTest::mouseMove(window, track, 0);
        QTest::mouseMove(window, points[0], 0);
        check(grab(arrows[0]) == idle, "cancel left an arrow pressed");
    }
    if (fusion) {
        printf("%s %dx%d %s\n", name, barRect.width(), barRect.height(), trace.result().toHex().constData());
    } else if (passed) {
        printf("%s passed\n", name);
    }
    return passed;
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    const bool fusion = app.arguments().contains(QStringLiteral("--fusion"));
    QQmlApplicationEngine engine;
    engine.loadData(R"(
import QtQuick
import QtQuick.Controls as C
import org.kde.kirigami as K

C.ApplicationWindow {
    width: 680; height: 360; visible: true; color: "magenta"
    property Item vertical: standaloneV
    property Item horizontal: standaloneH
    property Item attached: attachedV
    property Item viewV: view.C.ScrollBar.vertical
    property Item viewH: view.C.ScrollBar.horizontal
    property Item kirigami: page.contentItem.C.ScrollBar.vertical
    property Item custom: customV

    C.ScrollBar {
        id: standaloneV
        x: 20; y: 20; height: 220; orientation: Qt.Vertical; size: 0.3; position: 0.3
    }
    C.ScrollBar {
        id: standaloneH
        x: 50; y: 305; width: 220; orientation: Qt.Horizontal; size: 0.3; position: 0.3
    }
    C.ScrollView {
        id: view
        x: 60; y: 20; width: 120; height: 220
        contentWidth: 260; contentHeight: 730
        Item { width: 260; height: 730 }
    }
    Flickable {
        x: 200; y: 20; width: 110; height: 220; contentWidth: 110; contentHeight: 730
        C.ScrollBar.vertical: C.ScrollBar { id: attachedV }
    }
    K.ScrollablePage {
        id: page
        x: 340; y: 20; width: 155; height: 220
        ListView { model: 70; delegate: Item { width: 100; height: 16 } }
    }
    C.ScrollView {
        id: customView
        x: 525; y: 20; width: 120; height: 220
        contentWidth: 70; contentHeight: 730
        Item { width: 70; height: 730 }
        C.ScrollBar.vertical: C.ScrollBar {
            id: customV
            parent: customView
            x: parent.width - width
            height: parent.height
        }
    }
})");
    if (engine.rootObjects().isEmpty()) {
        return 2;
    }
    auto *window = qobject_cast<QQuickWindow *>(engine.rootObjects().constFirst());
    window->requestActivate();
    if (!QTest::qWaitForWindowActive(window)) {
        fprintf(stderr, "window did not activate\n");
        return 2;
    }
    if (fusion) {
        QApplication::setStyle(QStringLiteral("Fusion"));
        QTest::qWait(300);
    }
    bool passed = true;
    for (const char *name : {"vertical", "horizontal", "attached", "viewV", "viewH", "kirigami", "custom"}) {
        passed &= checkBar(window, name, window->property(name).value<QQuickItem *>(), fusion);
    }
    return passed ? 0 : 1;
}
