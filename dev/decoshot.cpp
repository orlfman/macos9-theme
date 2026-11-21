// Loads decoration.qml, pins isPinned windows and puts buttons into hover and
// press states by sending the decoration real pointer events, then saves the
// window to a PNG.
// Usage: decoshot decoration.qml out.png
#include <KDecoration3/Decoration>
#include <KDecoration3/DecorationButton>

#include <QApplication>
#include <QDebug>
#include <QHoverEvent>
#include <QMouseEvent>
#include <QQmlApplicationEngine>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTimer>

static KDecoration3::DecorationButton *findButton(KDecoration3::Decoration *decoration, int type)
{
    const auto buttons = decoration->findChildren<KDecoration3::DecorationButton *>();
    for (auto *button : buttons) {
        if (int(button->type()) == type && button->isVisible()) {
            return button;
        }
    }
    return nullptr;
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    if (argc < 3) {
        qWarning() << "usage: decoshot file.qml out.png";
        return 1;
    }
    const QString out = QString::fromLocal8Bit(argv[2]);
    QQmlApplicationEngine engine;
    engine.load(QUrl::fromLocalFile(QString::fromLocal8Bit(argv[1])));
    if (engine.rootObjects().isEmpty()) {
        return 2;
    }
    auto *window = qobject_cast<QQuickWindow *>(engine.rootObjects().constFirst());

    QTimer::singleShot(800, [&] {
        const auto items = window->contentItem()->childItems();
        for (QQuickItem *item : items) {
            const int hover = item->property("hoverButton").toInt();
            const int press = item->property("pressButton").toInt();
            auto *decoration = qobject_cast<KDecoration3::Decoration *>(item->property("decoration").value<QObject *>());
            if (!decoration) {
                continue;
            }
            // The pin button toggles the preview client, like a real click.
            if (item->property("isPinned").toBool()) {
                if (auto *pin = findButton(decoration, int(KDecoration3::DecorationButtonType::OnAllDesktops))) {
                    const QPointF pos = pin->geometry().center();
                    QHoverEvent move(QEvent::HoverMove, pos, pos, pos);
                    QCoreApplication::sendEvent(decoration, &move);
                    QMouseEvent down(QEvent::MouseButtonPress, pos, pos, pos, Qt::LeftButton, Qt::LeftButton, Qt::NoModifier);
                    QCoreApplication::sendEvent(decoration, &down);
                    QMouseEvent up(QEvent::MouseButtonRelease, pos, pos, pos, Qt::LeftButton, Qt::NoButton, Qt::NoModifier);
                    QCoreApplication::sendEvent(decoration, &up);
                } else {
                    qWarning() << item->objectName() << "has no pin button";
                }
            }
            if (auto *button = findButton(decoration, hover)) {
                const QPointF pos = button->geometry().center();
                QHoverEvent enter(QEvent::HoverEnter, pos, pos, QPointF());
                QCoreApplication::sendEvent(decoration, &enter);
                QHoverEvent move(QEvent::HoverMove, pos, pos, pos);
                QCoreApplication::sendEvent(decoration, &move);
                qInfo() << item->objectName() << "hover" << int(button->type()) << button->geometry() << "hovered:" << button->isHovered();
            } else if (hover >= 0) {
                qWarning() << item->objectName() << "has no button of type" << hover;
            }
            if (auto *button = findButton(decoration, press)) {
                const QPointF pos = button->geometry().center();
                QMouseEvent down(QEvent::MouseButtonPress, pos, pos, pos, Qt::LeftButton, Qt::LeftButton, Qt::NoModifier);
                QCoreApplication::sendEvent(decoration, &down);
            }
        }
    });
    QTimer::singleShot(1400, [&] {
        // The pin button shows the click once the client reports it.
        for (QQuickItem *item : window->contentItem()->childItems()) {
            auto *decoration = qobject_cast<KDecoration3::Decoration *>(item->property("decoration").value<QObject *>());
            auto *pin = decoration ? findButton(decoration, int(KDecoration3::DecorationButtonType::OnAllDesktops)) : nullptr;
            if (item->property("isPinned").toBool() && pin) {
                qInfo() << item->objectName() << "pinned:" << pin->isChecked();
            }
        }
        if (!window->grabWindow().save(out)) {
            qWarning() << "grab failed";
        }
        QCoreApplication::quit();
    });
    return app.exec();
}
