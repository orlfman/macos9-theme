// Keyboard focus in QtWidgets as a real user sees it. QtWidgets draws the
// focus ring as a separate QFocusFrame widget, which offscreen grabs miss, so
// this runs inside the nested KWin (kwin-test.sh style): it presses Tab on
// itself and has Spectacle capture the screen after each press, into
// OUT-N.png. Usage: tabdemo OUT
#include <QApplication>
#include <QCheckBox>
#include <QComboBox>
#include <QHBoxLayout>
#include <QKeyEvent>
#include <QProcess>
#include <QPushButton>
#include <QRadioButton>
#include <QSlider>
#include <QTabWidget>
#include <QTimer>
#include <QVBoxLayout>

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    const QString out = argc > 1 ? QString::fromLocal8Bit(argv[1]) : QStringLiteral("tab");

    QWidget window;
    window.setWindowTitle(QStringLiteral("Keyboard focus"));
    auto *layout = new QVBoxLayout(&window);
    auto *row = new QHBoxLayout;
    row->addWidget(new QPushButton(QStringLiteral("Button")));
    auto *check = new QCheckBox(QStringLiteral("Checked"));
    check->setChecked(true);
    row->addWidget(check);
    auto *radio = new QRadioButton(QStringLiteral("Radio"));
    radio->setChecked(true);
    row->addWidget(radio);
    auto *combo = new QComboBox;
    combo->addItem(QStringLiteral("Combo box"));
    row->addWidget(combo);
    auto *slider = new QSlider(Qt::Horizontal);
    slider->setValue(50);
    row->addWidget(slider);
    layout->addLayout(row);
    auto *tabs = new QTabWidget;
    tabs->addTab(new QWidget, QStringLiteral("General"));
    tabs->addTab(new QWidget, QStringLiteral("Advanced"));
    tabs->setMinimumHeight(90);
    layout->addWidget(tabs);
    window.resize(620, 180);
    window.show();

    const int presses = 6; // button, check, radio, combo, slider, tab bar
    auto *step = new QTimer(&window);
    int done = 0;
    QObject::connect(step, &QTimer::timeout, [&] {
        if (done >= presses) {
            QApplication::quit();
            return;
        }
        QKeyEvent press(QEvent::KeyPress, Qt::Key_Tab, Qt::NoModifier);
        QKeyEvent release(QEvent::KeyRelease, Qt::Key_Tab, Qt::NoModifier);
        QWidget *target = QApplication::focusWidget() ? QApplication::focusWidget() : &window;
        QApplication::sendEvent(target, &press);
        QApplication::sendEvent(target, &release);
        QTimer::singleShot(400, [&, n = done] {
            QProcess::execute(QStringLiteral("spectacle"), {QStringLiteral("-b"), QStringLiteral("-n"), QStringLiteral("-a"), QStringLiteral("-o"), QStringLiteral("%1-%2.png").arg(out).arg(n)});
        });
        ++done;
    });
    QTimer::singleShot(1500, [step] {
        step->start(2500);
    });
    return app.exec();
}
