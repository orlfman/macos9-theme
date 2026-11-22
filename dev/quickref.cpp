// The widget counterparts of the Qt Quick style's pieces, for
// dev/check-quick.sh: saves OUT-menu-0.png / -1.png (first / last row
// selected), OUT-combo.png (the open list), OUT-menubar.png,
// OUT-checkbox.png (the indicator of a checked QCheckBox),
// OUT-tooltip.png, OUT-dialog.png (the modal dialog frame, 220x120),
// OUT-rangeslider.png (a QSlider at 20 with a second thumb at 70) and
// OUT-menuedge.png (a menu's right edge, for the drawer's), and prints
// their sizes. Run with the Platinum style.
#include <QApplication>
#include <QCheckBox>
#include <QComboBox>
#include <QEventLoop>
#include <QMenu>
#include <QMenuBar>
#include <QPainter>
#include <QSlider>
#include <QStyleOptionSlider>
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
    rows << menu.addAction("First") << menu.addAction("Second");
    // A row with an icon (finding 51).
    const QIcon openIcon = QIcon::fromTheme(QStringLiteral("document-open"));
    printf("menu icon %s\n", openIcon.isNull() ? "missing" : "found");
    rows << menu.addAction(openIcon, QStringLiteral("Open")) << menu.addSeparator();
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
    // As wide as dev/quick-regions.qml's (wider than the rows need in any
    // font, so both lists are the button's width).
    combo.resize(140, combo.sizeHint().height());
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

    // The same, narrower than its items: its list widens to the combo
    // box's width hint.
    QComboBox narrow;
    narrow.addItems({"Lavender", "Purple", "Platinum"});
    narrow.setCurrentIndex(1);
    narrow.resize(60, narrow.sizeHint().height());
    narrow.move(300, 100);
    narrow.show();
    settle(150);
    narrow.showPopup();
    settle(300);
    if (QWidget *list = topLevel("QComboBoxPrivateContainer")) {
        list->grab().save(out + QStringLiteral("-combo-narrow.png"));
        printf("combo-narrow %d %d button %d %d\n", list->width(), list->height(), narrow.width(), narrow.height());
    }
    narrow.hidePopup();
    narrow.hide();

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

    // The modal dialog frame at the Qt Quick dialog's size, on its white
    // body (Platinum::PE_PlatinumModalFrame).
    {
        QImage frame(220, 120, QImage::Format_ARGB32_Premultiplied);
        frame.fill(Qt::transparent);
        QPainter p(&frame);
        QStyleOption o;
        o.rect = frame.rect();
        o.palette = QApplication::palette();
        o.palette.setColor(QPalette::Window, o.palette.color(QPalette::Base));
        o.state = QStyle::State_Enabled;
        QApplication::style()->drawPrimitive(QStyle::PrimitiveElement(QStyle::PE_CustomBase + 1), &o, &p, nullptr);
        p.end();
        frame.save(out + QStringLiteral("-dialog.png"));
        printf("dialog 220 120\n");
    }

    // The range slider: a QSlider (200 wide, 0..100) at 20, and the second
    // thumb at 70 drawn by the style on top.
    {
        QSlider slider(Qt::Horizontal);
        slider.setRange(0, 100);
        slider.setValue(20);
        slider.resize(200, slider.sizeHint().height());
        slider.show();
        settle(150);
        QPixmap shot(slider.size());
        shot.fill(Qt::transparent);
        slider.render(&shot, QPoint(), QRegion(), QWidget::DrawChildren);
        QStyleOptionSlider o;
        o.initFrom(&slider);
        o.orientation = Qt::Horizontal;
        o.minimum = 0;
        o.maximum = 100;
        o.sliderPosition = o.sliderValue = 70;
        o.subControls = QStyle::SC_SliderHandle;
        o.rect = slider.rect();
        QPainter p(&shot);
        slider.style()->drawComplexControl(QStyle::CC_Slider, &o, &p, &slider);
        p.end();
        shot.save(out + QStringLiteral("-rangeslider.png"));
        const QRect h1 = slider.style()->subControlRect(QStyle::CC_Slider, &o, QStyle::SC_SliderHandle, &slider);
        o.sliderPosition = o.sliderValue = 20;
        const QRect h0 = slider.style()->subControlRect(QStyle::CC_Slider, &o, QStyle::SC_SliderHandle, &slider);
        printf("rangeslider %d %d handles %d %d\n", slider.width(), slider.height(), h0.x(), h1.x());
        slider.hide();
    }

    // A tooltip.
    QToolTip::showText(QPoint(300, 300), QStringLiteral("A help balloon"));
    settle(300);
    if (QWidget *tip = topLevel("QTipLabel")) {
        tip->grab().save(out + QStringLiteral("-tooltip.png"));
        printf("tooltip %d %d\n", tip->width(), tip->height());
    }
    return 0;
}
