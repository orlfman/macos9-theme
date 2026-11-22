// The widget counterparts of the Qt Quick style's pieces, for
// dev/check-quick.sh: saves OUT-menu-0.png / -1.png (first / last row
// selected), OUT-combo.png (the open list), OUT-menubar.png,
// OUT-checkbox.png (the indicator of a checked QCheckBox) and
// OUT-tooltip.png, and prints their sizes. Run with the Platinum style.
#include <QApplication>
#include <QCheckBox>
#include <QComboBox>
#include <QEventLoop>
#include <QMenu>
#include <QMenuBar>
#include <QPixmap>
#include <QStyle>
#include <QStyleOptionButton>
#include <QTimer>
#include <QToolTip>
#include <cstdio>

static void settle(int ms)
{
    QEventLoop l;
    QTimer::singleShot(ms, &l, &QEventLoop::quit);
    l.exec();
}

static QWidget *topLevel(const char *className)
{
    const auto widgets = QApplication::topLevelWidgets();
    for (QWidget *w : widgets) {
        if (w->isVisible() && w->inherits(className)) {
            return w;
        }
    }
    return nullptr;
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    if (argc < 2) {
        return 1;
    }
    const QString out = QString::fromLocal8Bit(argv[1]);

    // The menu (the same rows as dev/quick-regions.qml).
    QMenu menu;
    QList<QAction *> rows;
    rows << menu.addAction("First") << menu.addAction("Second") << menu.addSeparator();
    QAction *checked = menu.addAction("Checked");
    checked->setCheckable(true);
    checked->setChecked(true);
    QAction *save = menu.addAction("Save");
    save->setShortcut(QKeySequence("Ctrl+S"));
    QMenu *sub = menu.addMenu("More");
    sub->addAction("Inside");
    rows << checked << save << sub->menuAction() << menu.addAction("Last");
    menu.popup(QPoint(0, 0));
    settle(200);
    for (int step = 0; step < 2; ++step) {
        menu.setActiveAction(step == 0 ? rows.first() : rows.last());
        settle(150);
        menu.grab().save(out + QStringLiteral("-menu-%1.png").arg(step));
    }
    printf("menu %d %d\n", menu.width(), menu.height());
    menu.close();

    // The combo box's open list, current item Purple.
    QComboBox combo;
    combo.addItems({"Lavender", "Purple", "Platinum"});
    combo.setCurrentIndex(1);
    // As wide as the Qt Quick list's rows need (dev/quick-regions.qml).
    combo.resize(102, combo.sizeHint().height());
    combo.move(100, 100);
    combo.show();
    settle(150);
    combo.showPopup();
    settle(300);
    if (QWidget *list = topLevel("QComboBoxPrivateContainer")) {
        list->grab().save(out + QStringLiteral("-combo.png"));
        printf("combo %d %d button %d %d\n", list->width(), list->height(), combo.width(), combo.height());
    }
    combo.hidePopup();
    combo.hide();

    // The menu bar.
    QMenuBar bar;
    bar.addMenu("File")->addAction("Open");
    bar.addMenu("Edit")->addAction("Copy");
    bar.resize(200, bar.sizeHint().height());
    bar.show();
    settle(150);
    bar.grab().save(out + QStringLiteral("-menubar.png"));
    printf("menubar %d %d\n", bar.width(), bar.height());
    bar.hide();

    // A checked check box's indicator.
    QCheckBox box("Switch on");
    box.setChecked(true);
    box.adjustSize();
    box.show();
    settle(150);
    QStyleOptionButton opt;
    opt.initFrom(&box);
    const QRect indicator = box.style()->subElementRect(QStyle::SE_CheckBoxIndicator, &opt, &box);
    // Without the window's background (the Qt Quick side is see-through
    // around the indicator too).
    QPixmap boxShot(indicator.size());
    boxShot.fill(Qt::transparent);
    box.render(&boxShot, QPoint(), QRegion(indicator), QWidget::DrawChildren);
    boxShot.save(out + QStringLiteral("-checkbox.png"));
    printf("checkbox %d %d\n", indicator.width(), indicator.height());
    box.hide();

    // A tooltip.
    QToolTip::showText(QPoint(300, 300), QStringLiteral("A help balloon"));
    settle(300);
    if (QWidget *tip = topLevel("QTipLabel")) {
        tip->grab().save(out + QStringLiteral("-tooltip.png"));
        printf("tooltip %d %d\n", tip->width(), tip->height());
    }
    return 0;
}
