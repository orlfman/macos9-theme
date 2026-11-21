// An interactive window with every control the Platinum style draws so far
// (with a menu bar and a right-click menu), laid out a bit like a Mac OS 9
// control panel, plus a few controls that are
// still Fusion (marked "not themed yet"), for trying the style by hand in
// dev/live-test.sh. Nothing is grabbed or saved.
//
// usage: livedemo
#include <QtWidgets>

namespace
{
QWidget *page(QLayout *layout)
{
    auto *w = new QWidget;
    w->setLayout(layout);
    return w;
}

QWidget *controlsPage()
{
    auto *grid = new QGridLayout;
    int row = 0;

    auto *buttons = new QHBoxLayout;
    buttons->addWidget(new QPushButton(QStringLiteral("Normal")));
    auto *disabled = new QPushButton(QStringLiteral("Disabled"));
    disabled->setEnabled(false);
    buttons->addWidget(disabled);
    auto *def = new QPushButton(QStringLiteral("Default"));
    def->setDefault(true);
    buttons->addWidget(def);
    buttons->addStretch();
    grid->addWidget(new QLabel(QStringLiteral("Push buttons:")), row, 0);
    grid->addLayout(buttons, row++, 1);

    auto *checks = new QHBoxLayout;
    auto *c1 = new QCheckBox(QStringLiteral("Checked"));
    c1->setChecked(true);
    checks->addWidget(c1);
    checks->addWidget(new QCheckBox(QStringLiteral("Unchecked")));
    auto *c3 = new QCheckBox(QStringLiteral("Disabled"));
    c3->setChecked(true);
    c3->setEnabled(false);
    checks->addWidget(c3);
    checks->addStretch();
    grid->addWidget(new QLabel(QStringLiteral("Check boxes:")), row, 0);
    grid->addLayout(checks, row++, 1);

    auto *radios = new QHBoxLayout;
    auto *r1 = new QRadioButton(QStringLiteral("On"));
    r1->setChecked(true);
    radios->addWidget(r1);
    radios->addWidget(new QRadioButton(QStringLiteral("Off")));
    auto *r3 = new QRadioButton(QStringLiteral("Disabled"));
    r3->setEnabled(false);
    radios->addWidget(r3);
    radios->addStretch();
    grid->addWidget(new QLabel(QStringLiteral("Radio buttons:")), row, 0);
    grid->addLayout(radios, row++, 1);

    auto *popups = new QHBoxLayout;
    auto *p1 = new QComboBox;
    p1->addItems({QStringLiteral("Mac OS Default"), QStringLiteral("Platinum"), QStringLiteral("Graphite")});
    popups->addWidget(p1);
    auto *p2 = new QComboBox;
    p2->addItem(QStringLiteral("Disabled pop-up"));
    p2->setEnabled(false);
    popups->addWidget(p2);
    popups->addStretch();
    grid->addWidget(new QLabel(QStringLiteral("Pop-up menus:")), row, 0);
    grid->addLayout(popups, row++, 1);

    auto *sliders = new QHBoxLayout;
    auto *s1 = new QSlider(Qt::Horizontal);
    s1->setRange(0, 2);
    s1->setValue(1);
    s1->setTickPosition(QSlider::TicksBelow);
    s1->setTickInterval(1);
    s1->setPageStep(1);
    s1->setFixedWidth(91);
    sliders->addWidget(s1);
    auto *s2 = new QSlider(Qt::Horizontal);
    s2->setRange(0, 100);
    s2->setValue(40);
    s2->setFixedWidth(160);
    sliders->addWidget(s2);
    auto *s3 = new QSlider(Qt::Horizontal);
    s3->setEnabled(false);
    s3->setFixedWidth(140);
    sliders->addWidget(s3);
    sliders->addStretch();
    grid->addWidget(new QLabel(QStringLiteral("Sliders:")), row, 0);
    grid->addLayout(sliders, row++, 1);

    auto *bars = new QHBoxLayout;
    auto *b1 = new QProgressBar;
    b1->setFixedWidth(188);
    b1->setRange(0, 100);
    auto *timer = new QTimer(b1);
    QObject::connect(timer, &QTimer::timeout, b1, [b1] {
        b1->setValue((b1->value() + 1) % 101);
    });
    timer->start(60);
    bars->addWidget(b1);
    auto *b2 = new QProgressBar;
    b2->setFixedWidth(188);
    b2->setRange(0, 0);
    bars->addWidget(b2);
    bars->addStretch();
    grid->addWidget(new QLabel(QStringLiteral("Progress:")), row, 0);
    grid->addLayout(bars, row++, 1);

    grid->setRowStretch(row, 1);
    grid->setColumnStretch(1, 1);
    return page(grid);
}

QWidget *scrollingPage()
{
    auto *layout = new QHBoxLayout;
    auto *text = new QPlainTextEdit;
    QString lines;
    for (int i = 1; i <= 200; ++i) {
        lines += QStringLiteral("Line %1: scroll bars with both arrows at the bottom/right end, as in Mac OS 9 Smart Scrolling. "
                                "This line is long so the horizontal bar has something to do.\n")
                     .arg(i);
    }
    text->setPlainText(lines);
    text->setLineWrapMode(QPlainTextEdit::NoWrap);
    layout->addWidget(text, 1);
    auto *v = new QSlider(Qt::Vertical);
    v->setRange(0, 4);
    v->setTickPosition(QSlider::TicksBelow);
    v->setTickInterval(1);
    layout->addWidget(v);
    return page(layout);
}

QWidget *notYetPage()
{
    auto *form = new QFormLayout;
    form->addRow(new QLabel(QStringLiteral("These are still drawn by Fusion (later batches):")));
    form->addRow(QStringLiteral("Text field:"), new QLineEdit(QStringLiteral("Focus ring comes next")));
    auto *spin = new QSpinBox;
    spin->setValue(12);
    form->addRow(QStringLiteral("Spin box:"), spin);
    auto *edit = new QComboBox;
    edit->setEditable(true);
    edit->addItem(QStringLiteral("Editable combo"));
    form->addRow(QStringLiteral("Editable combo:"), edit);
    auto *group = new QGroupBox(QStringLiteral("Group box"));
    auto *gl = new QVBoxLayout(group);
    gl->addWidget(new QCheckBox(QStringLiteral("Inside a group box")));
    form->addRow(group);
    auto *tree = new QTreeWidget;
    tree->setHeaderLabels({QStringLiteral("Name"), QStringLiteral("Size")});
    auto *folder = new QTreeWidgetItem(tree, {QStringLiteral("System Folder"), QStringLiteral("—")});
    new QTreeWidgetItem(folder, {QStringLiteral("Finder"), QStringLiteral("1.2 MB")});
    new QTreeWidgetItem(folder, {QStringLiteral("System"), QStringLiteral("8.4 MB")});
    tree->expandAll();
    form->addRow(tree);
    return page(form);
}
} // namespace

QMenuBar *menuBar(QWidget *parent)
{
    auto *bar = new QMenuBar(parent);
    QMenu *file = bar->addMenu(QStringLiteral("&File"));
    file->addAction(QStringLiteral("New Folder"))->setShortcut(QKeySequence::New);
    file->addAction(QStringLiteral("Open"))->setShortcut(QKeySequence::Open);
    file->addAction(QStringLiteral("Close Window"))->setEnabled(false);
    file->addSeparator();
    QMenu *label = file->addMenu(QStringLiteral("Label"));
    for (const char *s : {"None", "Essential", "Hot", "In Progress", "Cool"}) {
        label->addAction(QString::fromLatin1(s));
    }
    file->addSeparator();
    file->addAction(QStringLiteral("Quit"), QKeySequence::Quit, qApp, &QApplication::quit);
    QMenu *view = bar->addMenu(QStringLiteral("&View"));
    auto *modes = new QActionGroup(view);
    QAction *first = nullptr;
    for (const char *s : {"as Icons", "as Buttons", "as List"}) {
        QAction *a = view->addAction(QString::fromLatin1(s));
        a->setCheckable(true);
        modes->addAction(a);
        first = first ? first : a;
    }
    first->setChecked(true);
    view->addSeparator();
    QAction *previews = view->addAction(QIcon::fromTheme(QStringLiteral("view-preview")), QStringLiteral("Show Previews"));
    previews->setCheckable(true);
    previews->setChecked(true);
    view->addAction(QIcon::fromTheme(QStringLiteral("view-sort")), QStringLiteral("Sort List"))->setMenu(label);
    view->addAction(QStringLiteral("View Options…"))->setShortcut(QKeySequence(QStringLiteral("Ctrl+J")));
    bar->addMenu(QStringLiteral("&Special"))->addAction(QStringLiteral("Empty Trash…"));
    return bar;
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    QWidget window;
    window.setWindowTitle(QStringLiteral("Platinum Controls"));
    auto *layout = new QVBoxLayout(&window);
    layout->setMenuBar(menuBar(&window));
    window.setContextMenuPolicy(Qt::ActionsContextMenu);
    for (const char *s : {"Get Info", "Duplicate", "Make Alias"}) {
        window.addAction(new QAction(QString::fromLatin1(s), &window));
    }
    auto *tabs = new QTabWidget;
    tabs->addTab(controlsPage(), QStringLiteral("Controls"));
    tabs->addTab(scrollingPage(), QStringLiteral("Scrolling"));
    tabs->addTab(notYetPage(), QStringLiteral("Not Themed Yet"));
    auto *off = new QWidget;
    tabs->addTab(off, QStringLiteral("Disabled"));
    tabs->setTabEnabled(3, false);
    layout->addWidget(tabs);
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    QObject::connect(buttons, &QDialogButtonBox::accepted, &app, &QApplication::quit);
    QObject::connect(buttons, &QDialogButtonBox::rejected, &app, &QApplication::quit);
    layout->addWidget(buttons);
    window.resize(560, 420);
    window.show();
    return app.exec();
}
