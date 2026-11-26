// Exercises real QWidget style options and painting for audit #273–276 and #279–280.
// SPDX-License-Identifier: BSD-2-Clause
#include <QApplication>
#include <QImage>
#include <QMenu>
#include <QProgressBar>
#include <QSlider>
#include <QSpinBox>
#include <QStyleOptionSpinBox>
#include <QTest>
#include <QTimer>

namespace
{
int failures = 0;

void check(const char *name, bool ok)
{
    qInfo().noquote() << (ok ? "ok     " : "FAIL   ") << name;
    failures += !ok;
}

QImage capture(QWidget &widget)
{
    return widget.grab().toImage();
}

class SpinBox : public QSpinBox
{
public:
    QImage buttons(QStyle::SubControl part)
    {
        QStyleOptionSpinBox option;
        initStyleOption(&option);
        return capture(*this).copy(style()->subControlRect(QStyle::CC_SpinBox, &option, part, this));
    }
};

void checkMenu()
{
    QMenu menu;
    menu.addAction("Before");
    QAction *separator = menu.addSeparator();
    QAction *section = menu.addSection("File operations");
    QAction *action = menu.addAction("HgÅyj");
    menu.popup(QPoint(10, 10));
    QTest::qWait(40);
    const QRect first = menu.actionGeometry(section);
    const QImage heading = capture(menu).copy(first);
    section->setText("Edit operations");
    const QImage renamed = capture(menu).copy(menu.actionGeometry(section));
    check("menu section renders its label and reacts to renames", first.height() >= 16 && heading != renamed);
    check("plain menu separator stays six pixels high", menu.actionGeometry(separator).height() == 6);

    QFont font = menu.font();
    font.setPixelSize(28);
    menu.setFont(font);
    const QFontMetrics metrics(font);
    check("large menu text fits its action and section rows",
          menu.actionGeometry(action).height() >= metrics.boundingRect(action->text()).height()
          && menu.actionGeometry(section).height() >= metrics.height());
}

void checkProgress()
{
    QProgressBar bar;
    bar.resize(200, 24);
    bar.setRange(0, 100);
    bar.setValue(25);
    bar.show();
    const QRect track(2, 5, 196, 14);
    const QImage ltr = capture(bar).copy(track);
    bar.setInvertedAppearance(true);
    const QImage inverted = capture(bar).copy(track);
    bar.setLayoutDirection(Qt::RightToLeft);
    const QImage invertedRtl = capture(bar).copy(track);
    bar.setInvertedAppearance(false);
    check("progress fill and divider mirror in RTL and inverted LTR",
          ltr != inverted && inverted == ltr.flipped(Qt::Horizontal)
          && capture(bar).copy(track) == inverted && invertedRtl == ltr);

    bar.setRange(0, 0);
    capture(bar);
    const auto *timer = bar.findChild<QTimer *>("platinum-barber-pole");
    check("zero-to-zero range starts the barber-pole timer", timer && timer->isActive());

    bar.setRange(5, 5);
    const QImage reset = capture(bar).copy(track);
    bar.setValue(5);
    const QImage singleValue = capture(bar).copy(track);
    check("single-value range starts empty and finishes full without animation",
          timer && !timer->isActive() && singleValue != reset && bar.text() == "100%");
    bar.setRange(0, 100);
    bar.setValue(100);
    check("single-value completion matches a fully filled progress bar", capture(bar).copy(track) == singleValue);
}

void checkTicks(Qt::Orientation orientation)
{
    const bool horizontal = orientation == Qt::Horizontal;
    QSlider slider(orientation);
    slider.resize(horizontal ? QSize(200, 34) : QSize(34, 200));
    slider.setRange(0, 100);
    slider.setValue(50);
    slider.setTickInterval(10);
    const auto band = [horizontal](int at) {
        return horizontal ? QRect(0, at, 200, 7) : QRect(at, 0, 7, 200);
    };

    const int base = horizontal ? slider.sizeHint().height() : slider.sizeHint().width();
    const QImage noLeadingTicks = capture(slider).copy(band(0));
    slider.setTickPosition(QSlider::TicksAbove);
    const QImage leading = capture(slider).copy(band(0));
    slider.setTickPosition(QSlider::TicksBelow);
    const QImage trailing = capture(slider).copy(band(16));
    slider.setTickPosition(QSlider::TicksBothSides);
    const QImage both = capture(slider);
    const int thick = horizontal ? slider.sizeHint().height() : slider.sizeHint().width();
    check(horizontal ? "horizontal slider paints above and below" : "vertical slider paints left and right",
          leading != noLeadingTicks && leading == both.copy(band(0))
          && trailing == both.copy(band(23)) && thick == base + 14);
}

void checkSpin()
{
    SpinBox spin;
    spin.setRange(0, 2);
    spin.resize(108, 26);
    spin.setValue(1);
    const QImage up = spin.buttons(QStyle::SC_SpinBoxUp);
    const QImage down = spin.buttons(QStyle::SC_SpinBoxDown);
    spin.setValue(0);
    check("spin box lower bound disables only the down button",
          spin.buttons(QStyle::SC_SpinBoxUp) == up && spin.buttons(QStyle::SC_SpinBoxDown) != down);
    spin.setValue(2);
    check("spin box upper bound disables only the up button",
          spin.buttons(QStyle::SC_SpinBoxUp) != up && spin.buttons(QStyle::SC_SpinBoxDown) == down);
    spin.setValue(1);
    spin.setButtonSymbols(QAbstractSpinBox::PlusMinus);
    check("spin box draws plus and minus in their respective halves",
          spin.buttons(QStyle::SC_SpinBoxUp) != up && spin.buttons(QStyle::SC_SpinBoxDown) != down);
}
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    checkMenu();
    checkProgress();
    checkTicks(Qt::Horizontal);
    checkTicks(Qt::Vertical);
    checkSpin();
    return failures != 0;
}
