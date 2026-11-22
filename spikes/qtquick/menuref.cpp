// Spike: the widget QMenu the Qt Quick menu is compared with. Saves
// OUT-0.png (first row selected) and OUT-1.png (last row selected) and
// prints each row's rectangle.
#include <QApplication>
#include <QMenu>
#include <QTimer>
#include <QEventLoop>
#include <QDebug>
#include <cstdio>

static void settle(int ms) { QEventLoop l; QTimer::singleShot(ms, &l, &QEventLoop::quit); l.exec(); }

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    QMenu menu;
    QList<QAction *> rows;
    rows << menu.addAction("First") << menu.addAction("Second") << menu.addSeparator();
    QAction *checked = menu.addAction("Checked");
    checked->setCheckable(true);
    checked->setChecked(true);
    rows << checked;
    QAction *save = menu.addAction("Save");
    save->setShortcut(QKeySequence("Ctrl+S"));
    rows << save;
    QMenu *sub = menu.addMenu("More");
    sub->addAction("Inside");
    rows << sub->menuAction() << menu.addAction("Last");
    menu.popup(QPoint(0, 0));
    settle(200);
    for (int step = 0; step < 2; ++step) {
        menu.setActiveAction(step == 0 ? rows.first() : rows.last());
        settle(150);
        menu.grab().save(QString::fromLocal8Bit(argv[1]) + QStringLiteral("-%1.png").arg(step));
    }
    printf("MENU %d %d\n", menu.width(), menu.height());
    for (QAction *a : rows) {
        const QRect r = menu.actionGeometry(a);
        printf("ROW %d %d %d %d\n", r.x(), r.y(), r.width(), r.height());
    }
    return 0;
}
