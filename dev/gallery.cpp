// Offscreen widget gallery: builds a window with common QtWidgets controls,
// renders it (plus an open menu and combo popup) to PNG, then exits.
#include <QtWidgets>

static QWidget *row(std::initializer_list<QWidget *> ws)
{
    auto w = new QWidget;
    auto l = new QHBoxLayout(w);
    l->setContentsMargins(0, 0, 0, 0);
    for (auto x : ws)
        l->addWidget(x);
    l->addStretch();
    return w;
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    const QString out = argc > 1 ? QString::fromLocal8Bit(argv[1]) : QStringLiteral("gallery.png");

    QWidget win;
    win.setWindowTitle(QStringLiteral("Gallery"));
    auto grid = new QGridLayout(&win);

    // Buttons
    auto normal = new QPushButton(QStringLiteral("Button"));
    auto def = new QPushButton(QStringLiteral("Default"));
    def->setDefault(true);
    auto checked = new QPushButton(QStringLiteral("Checked"));
    checked->setCheckable(true);
    checked->setChecked(true);
    auto disabled = new QPushButton(QStringLiteral("Disabled"));
    disabled->setEnabled(false);
    auto flat = new QPushButton(QStringLiteral("Flat"));
    flat->setFlat(true);
    auto tool = new QToolButton;
    tool->setText(QStringLiteral("Tool"));
    tool->setIcon(QIcon::fromTheme(QStringLiteral("document-open")));
    tool->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    auto toolMenu = new QMenu(tool);
    toolMenu->addAction(QStringLiteral("One"));
    tool->setMenu(toolMenu);
    tool->setPopupMode(QToolButton::MenuButtonPopup);
    auto autoRaise = new QToolButton;
    autoRaise->setIcon(QIcon::fromTheme(QStringLiteral("go-next")));
    autoRaise->setAutoRaise(true);
    grid->addWidget(row({normal, def, checked, disabled, flat, tool, autoRaise}), 0, 0, 1, 2);

    // Checks and radios
    auto cb1 = new QCheckBox(QStringLiteral("Unchecked"));
    auto cb2 = new QCheckBox(QStringLiteral("Checked"));
    cb2->setChecked(true);
    auto cb3 = new QCheckBox(QStringLiteral("Partial"));
    cb3->setTristate(true);
    cb3->setCheckState(Qt::PartiallyChecked);
    auto cb4 = new QCheckBox(QStringLiteral("Disabled"));
    cb4->setChecked(true);
    cb4->setEnabled(false);
    auto rb1 = new QRadioButton(QStringLiteral("Radio"));
    auto rb2 = new QRadioButton(QStringLiteral("Selected"));
    rb2->setChecked(true);
    grid->addWidget(row({cb1, cb2, cb3, cb4, rb1, rb2}), 1, 0, 1, 2);

    // Inputs
    auto le = new QLineEdit(QStringLiteral("Focused text"));
    auto le2 = new QLineEdit;
    le2->setPlaceholderText(QStringLiteral("Placeholder"));
    auto spin = new QSpinBox;
    spin->setValue(42);
    auto combo = new QComboBox;
    combo->addItems({QStringLiteral("Combo box"), QStringLiteral("Second"), QStringLiteral("Third")});
    auto ecombo = new QComboBox;
    ecombo->setEditable(true);
    ecombo->addItem(QStringLiteral("Editable"));
    grid->addWidget(row({le, le2, spin, combo, ecombo}), 2, 0, 1, 2);

    // Ranges
    auto slider = new QSlider(Qt::Horizontal);
    slider->setValue(60);
    slider->setMinimumWidth(180);
    auto tslider = new QSlider(Qt::Horizontal);
    tslider->setTickPosition(QSlider::TicksBelow);
    tslider->setValue(30);
    tslider->setMinimumWidth(140);
    auto progress = new QProgressBar;
    progress->setValue(60);
    progress->setMinimumWidth(180);
    auto hscroll = new QScrollBar(Qt::Horizontal);
    hscroll->setRange(0, 100);
    hscroll->setPageStep(30);
    hscroll->setValue(20);
    hscroll->setMinimumWidth(180);
    grid->addWidget(row({slider, tslider, progress, hscroll}), 3, 0, 1, 2);

    // Hover states: WA_UnderMouse is what underMouse() reads, so the style
    // sees State_MouseOver without a real pointer.
    auto hButton = new QPushButton(QIcon::fromTheme(QStringLiteral("dialog-ok")), QStringLiteral("Hovered"));
    auto hCombo = new QComboBox;
    hCombo->addItem(QStringLiteral("Hovered combo"));
    auto hCheck = new QCheckBox(QStringLiteral("Hovered"));
    hCheck->setChecked(true);
    auto hTool = new QToolButton;
    hTool->setText(QStringLiteral("Hovered tool"));
    hTool->setIcon(QIcon::fromTheme(QStringLiteral("document-save")));
    hTool->setToolButtonStyle(Qt::ToolButtonTextBesideIcon);
    hTool->setAutoRaise(true);
    auto hSlider = new QSlider(Qt::Horizontal);
    hSlider->setValue(40);
    hSlider->setMinimumWidth(120);
    for (QWidget *w : {static_cast<QWidget *>(hButton), static_cast<QWidget *>(hCombo), static_cast<QWidget *>(hCheck),
                       static_cast<QWidget *>(hTool), static_cast<QWidget *>(hSlider)})
        w->setAttribute(Qt::WA_UnderMouse);
    grid->addWidget(row({hButton, hCombo, hCheck, hTool, hSlider}), 6, 0, 1, 2);

    // Tabs
    auto tabs = new QTabWidget;
    auto page = new QWidget;
    auto pl = new QVBoxLayout(page);
    auto group = new QGroupBox(QStringLiteral("Group box"));
    auto gl = new QVBoxLayout(group);
    gl->addWidget(new QLabel(QStringLiteral("Label inside a group box")));
    gl->addWidget(new QCheckBox(QStringLiteral("Option")));
    pl->addWidget(group);
    tabs->addTab(page, QStringLiteral("General"));
    tabs->addTab(new QWidget, QStringLiteral("Appearance"));
    tabs->addTab(new QWidget, QStringLiteral("Advanced"));
    tabs->setMinimumSize(300, 170);
    grid->addWidget(tabs, 4, 0);

    // Views
    auto list = new QListWidget;
    for (int i = 1; i <= 12; ++i)
        new QListWidgetItem(QIcon::fromTheme(QStringLiteral("folder")), QStringLiteral("Item %1").arg(i), list);
    list->setCurrentRow(1);
    list->setMinimumSize(200, 170);
    grid->addWidget(list, 4, 1);

    auto tree = new QTreeWidget;
    tree->setHeaderLabels({QStringLiteral("Name"), QStringLiteral("Size"), QStringLiteral("Modified")});
    for (int i = 1; i <= 3; ++i) {
        auto top = new QTreeWidgetItem(tree, {QStringLiteral("Folder %1").arg(i), QString(), QStringLiteral("Today")});
        top->setIcon(0, QIcon::fromTheme(QStringLiteral("folder")));
        for (int j = 1; j <= 2; ++j)
            new QTreeWidgetItem(top, {QStringLiteral("File %1.txt").arg(j), QStringLiteral("%1 KB").arg(j * 4), QStringLiteral("Yesterday")});
    }
    tree->expandItem(tree->topLevelItem(0));
    tree->setCurrentItem(tree->topLevelItem(0)->child(0));
    tree->setMinimumHeight(150);
    grid->addWidget(tree, 5, 0, 1, 2);

    win.resize(820, 690);
    win.show();
    win.activateWindow();
    le->setFocus();
    QApplication::processEvents();

    QTimer::singleShot(300, [&] {
        win.grab().save(out);

        // Context menu rendered on its own
        QMenu menu;
        menu.addAction(QIcon::fromTheme(QStringLiteral("edit-copy")), QStringLiteral("Copy"))->setShortcut(QKeySequence::Copy);
        menu.addAction(QIcon::fromTheme(QStringLiteral("edit-paste")), QStringLiteral("Paste"))->setShortcut(QKeySequence::Paste);
        auto dis = menu.addAction(QStringLiteral("Disabled item"));
        dis->setEnabled(false);
        menu.addSeparator();
        auto chk = menu.addAction(QStringLiteral("Checkable item"));
        chk->setCheckable(true);
        chk->setChecked(true);
        auto sub = menu.addMenu(QStringLiteral("Submenu"));
        sub->addAction(QStringLiteral("Inner"));
        menu.addAction(QStringLiteral("Last item"));
        menu.popup(QPoint(0, 0));
        QApplication::processEvents();
        menu.setActiveAction(menu.actions().at(1));
        QApplication::processEvents();
        QString menuOut = out;
        menuOut.replace(QStringLiteral(".png"), QStringLiteral("-menu.png"));
        menu.grab().save(menuOut);
        menu.hide();

        // Tooltip-like label and dialog button box
        QDialog dlg;
        auto dl = new QVBoxLayout(&dlg);
        dl->addWidget(new QLabel(QStringLiteral("Dialog with standard buttons")));
        auto bb = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel | QDialogButtonBox::Apply);
        dl->addWidget(bb);
        dlg.show();
        QApplication::processEvents();
        QString dlgOut = out;
        dlgOut.replace(QStringLiteral(".png"), QStringLiteral("-dialog.png"));
        dlg.grab().save(dlgOut);
        dlg.hide();

        // Keyboard focus, one control at a time (only one can have it), so
        // the focus ring of each can be checked. KeyboardFocusChange makes
        // the style show focus as it does after pressing Tab.
        win.setAttribute(Qt::WA_KeyboardFocusChange);
        // The dialog above took over as the active window, and focus only
        // shows in the active one.
        win.activateWindow();
        QApplication::processEvents();
        const QList<QWidget *> focusables = {normal, cb2, rb2, combo, ecombo, spin, le2, slider, tabs->tabBar(), list, tree};
        const int pad = 8;
        int sheetWidth = 0, sheetHeight = 0;
        QList<QPixmap> shots;
        for (QWidget *w : focusables) {
            w->setFocus(Qt::TabFocusReason);
            // The focus frame is a separate widget that moves after the
            // focus change; let it get there and paint.
            QEventLoop wait;
            QTimer::singleShot(60, &wait, &QEventLoop::quit);
            wait.exec();
            const QRect area = QRect(w->mapTo(&win, QPoint(0, 0)), w->size()).adjusted(-pad, -pad, pad, pad).intersected(win.rect());
            const QPixmap shot = win.grab(area.height() > 160 ? area.adjusted(0, 0, 0, 160 - area.height()) : area);
            shots.append(shot);
            sheetWidth += shot.width() + pad;
            sheetHeight = std::max(sheetHeight, shot.height());
        }
        QPixmap sheet(sheetWidth, sheetHeight);
        sheet.fill(win.palette().color(QPalette::Window));
        {
            QPainter p(&sheet);
            int x = 0;
            for (const QPixmap &shot : shots) {
                p.drawPixmap(x, 0, shot);
                x += shot.width() + pad;
            }
        }
        QString focusOut = out;
        focusOut.replace(QStringLiteral(".png"), QStringLiteral("-focus.png"));
        sheet.save(focusOut);

        QApplication::quit();
    });
    return app.exec();
}
