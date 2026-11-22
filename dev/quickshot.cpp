// Loads a QML file in a QApplication (like real Kirigami apps), then saves
// the whole window, popups included, to a PNG.
//
// A scene with an int property "steps" and a function prepare(i) is shot
// once per step instead: prepare(i) is called, then the window is saved as
// OUT-i.png. Windows are never shown on a real display (only on the
// offscreen platform, see below), so this is how a scene shows states that
// can't exist side by side, like keyboard focus.
#include <QApplication>
#include <QEventLoop>
#include <QQmlApplicationEngine>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QTimer>
#include <QDebug>

static void settle(int ms)
{
    QEventLoop loop;
    QTimer::singleShot(ms, &loop, &QEventLoop::quit);
    loop.exec();
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    if (argc < 3) {
        qWarning() << "usage: quickshot file.qml out.png";
        return 1;
    }
    const QString out = QString::fromLocal8Bit(argv[2]);
    QQmlApplicationEngine engine;
    engine.load(QUrl::fromLocalFile(QString::fromLocal8Bit(argv[1])));
    if (engine.rootObjects().isEmpty())
        return 2;
    qInfo() << "QtQuick style:" << QQuickStyle::name();
    // On the offscreen platform (no real screen) the window is shown, so
    // its pop-up layer gets the window's size: pop-ups that place
    // themselves when they open (menus, combo box lists) land where they
    // would on a real screen. Never shown on a real display.
    if (QGuiApplication::platformName() == QLatin1String("offscreen")) {
        if (auto window = qobject_cast<QQuickWindow *>(engine.rootObjects().constFirst())) {
            window->show();
        }
    }
    QTimer::singleShot(1200, [&] {
        auto window = qobject_cast<QQuickWindow *>(engine.rootObjects().constFirst());
        if (!window) {
            qWarning() << "grab failed: no window";
            QCoreApplication::quit();
            return;
        }
        const int steps = window->property("steps").toInt();
        if (steps <= 0) {
            if (!window->grabWindow().save(out))
                qWarning() << "grab failed";
        }
        for (int i = 0; i < steps; ++i) {
            QMetaObject::invokeMethod(window, "prepare", Q_ARG(QVariant, i));
            settle(150);
            QString name = out;
            name.replace(QStringLiteral(".png"), QStringLiteral("-%1.png").arg(i));
            if (!window->grabWindow().save(name))
                qWarning() << "grab failed for step" << i;
        }
        QCoreApplication::quit();
    });
    return app.exec();
}
