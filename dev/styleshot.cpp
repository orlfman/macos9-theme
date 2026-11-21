// Renders individual Platinum style states, through the current QStyle's own
// draw calls, at the sizes of the reference captures, so tools/compare.py can
// diff them. Labels are left empty (no Charcoal); compare outside them.
//
// usage: styleshot OUT.png
//
// Layout (x, y, w, h) on a #DDDDDD sheet, listed on stdout as
// "name x,y,w,h" for the diff script:
//   push buttons 70x20 (normal, pressed), 80x20 disabled, default ring
//   86x26 (normal) and 78x26 (pressed); check boxes and radio buttons in
//   every state; two vertical scroll bars and one horizontal one sized like
//   the captures; pop-ups, sliders, progress bars; three tab rows laid out
//   like the Appearance control panel's six tabs on their pane; a real
//   QMenu laid out like the Finder's View menu (first item highlighted), and
//   menu bar titles (normal and open).
#include <QtWidgets>
#include <cstdio>

namespace
{
QStyle *style;
QWidget *host;

void report(const char *name, const QRect &r)
{
    std::printf("%s %d,%d,%d,%d\n", name, r.x(), r.y(), r.width(), r.height());
}

void button(QPainter &p, const char *name, const QRect &r, QStyle::State state, QStyleOptionButton::ButtonFeatures features)
{
    QStyleOptionButton o;
    o.initFrom(host);
    o.rect = r;
    o.state = state | QStyle::State_Active;
    o.features = features;
    style->drawControl(QStyle::CE_PushButton, &o, &p, host);
    report(name, r);
}

void toggle(QPainter &p, const char *name, QStyle::PrimitiveElement e, const QPoint &at, QStyle::State state)
{
    QStyleOption o;
    o.initFrom(host);
    const int w = style->pixelMetric(e == QStyle::PE_IndicatorCheckBox ? QStyle::PM_IndicatorWidth : QStyle::PM_ExclusiveIndicatorWidth);
    const int h = style->pixelMetric(e == QStyle::PE_IndicatorCheckBox ? QStyle::PM_IndicatorHeight : QStyle::PM_ExclusiveIndicatorHeight);
    o.rect = QRect(at, QSize(w, h));
    o.state = state | QStyle::State_Active;
    style->drawPrimitive(e, &o, &p, host);
    report(name, o.rect);
}

void popup(QPainter &p, const char *name, const QRect &r, QStyle::State state)
{
    QStyleOptionComboBox o;
    o.initFrom(host);
    o.rect = r;
    o.state = state | QStyle::State_Active;
    o.editable = false;
    o.subControls = QStyle::SC_All;
    if (state & QStyle::State_Sunken) {
        o.activeSubControls = QStyle::SC_ComboBoxArrow;
    }
    style->drawComplexControl(QStyle::CC_ComboBox, &o, &p, host);
    report(name, r);
}

void slider(QPainter &p, const char *name, const QRect &r, QStyle::State state, int max, int value, bool ticks)
{
    QStyleOptionSlider o;
    o.initFrom(host);
    o.rect = r;
    o.orientation = Qt::Horizontal;
    o.minimum = 0;
    o.maximum = max;
    o.singleStep = 1;
    o.pageStep = 1;
    o.tickInterval = 1;
    o.sliderPosition = o.sliderValue = value;
    o.tickPosition = ticks ? QSlider::TicksBelow : QSlider::NoTicks;
    o.subControls = QStyle::SC_All;
    o.state = state | QStyle::State_Active | QStyle::State_Horizontal;
    if (state & QStyle::State_Sunken) {
        o.activeSubControls = QStyle::SC_SliderHandle;
    }
    style->drawComplexControl(QStyle::CC_Slider, &o, &p, host);
    report(name, r);
}

void progress(QPainter &p, const char *name, const QRect &r, int min, int max, int value)
{
    QStyleOptionProgressBar o;
    o.initFrom(host);
    o.rect = r;
    o.minimum = min;
    o.maximum = max;
    o.progress = value;
    o.state = QStyle::State_Enabled | QStyle::State_Horizontal;
    style->drawControl(QStyle::CE_ProgressBar, &o, &p, host);
    report(name, r);
}

// The Appearance control panel's tab row: six tabs (Themes, Appearance,
// Fonts, Desktop, Sound, Options) on a pane, measured widths, starting 5 px
// inside the pane. `current` and `pressed` are tab indexes (-1 = none).
void tabRow(QPainter &p, const char *name, const QRect &pane, int current, int pressed)
{
    QStyleOptionTabWidgetFrame f;
    f.initFrom(host);
    f.rect = pane;
    f.shape = QTabBar::RoundedNorth;
    style->drawPrimitive(QStyle::PE_FrameTabWidget, &f, &p, host);
    static const int widths[] = {72, 101, 57, 74, 62, 71};
    int x = pane.x() + 5;
    const int y = pane.y() - 21;
    for (int i = 0; i < 6; ++i) {
        QStyleOptionTab o;
        o.initFrom(host);
        o.shape = QTabBar::RoundedNorth;
        o.rect = QRect(x, y, widths[i], 24);
        o.state = QStyle::State_Enabled | QStyle::State_Active;
        if (i == current) {
            o.state |= QStyle::State_Selected;
        }
        if (i == pressed) {
            o.state |= QStyle::State_Sunken;
        }
        style->drawControl(QStyle::CE_TabBarTabShape, &o, &p, host);
        x += widths[i];
    }
    report(name, pane);
}

void scrollbar(QPainter &p, const char *name, const QRect &r, Qt::Orientation orientation, int value, int page)
{
    QStyleOptionSlider o;
    o.initFrom(host);
    o.rect = r;
    o.orientation = orientation;
    o.minimum = 0;
    o.maximum = 1000;
    o.pageStep = page;
    o.singleStep = 20;
    o.sliderPosition = o.sliderValue = value;
    o.subControls = QStyle::SC_All;
    o.state = QStyle::State_Enabled | QStyle::State_Active;
    if (orientation == Qt::Horizontal) {
        o.state |= QStyle::State_Horizontal;
    }
    style->drawComplexControl(QStyle::CC_ScrollBar, &o, &p, host);
    report(name, r);
}
} // namespace

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    if (argc < 2) {
        std::fprintf(stderr, "usage: styleshot OUT.png\n");
        return 2;
    }
    style = app.style();
    QWidget w;
    host = &w;
    std::printf("style %s\n", qPrintable(style->name()));
    QImage img(1000, 1200, QImage::Format_RGB32);
    img.fill(QColor(0xDD, 0xDD, 0xDD));
    QPainter p(&img);
    using S = QStyle;
    using F = QStyleOptionButton;
    const S::State on = S::State_Enabled;
    // The normal, pressed and pressed-default captures sit on white dialogs
    // (their rounded corners show it); the others on #DDDDDD.
    p.fillRect(QRect(5, 2, 160, 36), Qt::white);
    p.fillRect(QRect(355, 2, 90, 36), Qt::white);
    button(p, "push-normal", QRect(10, 10, 70, 20), on, F::None);
    button(p, "push-pressed", QRect(90, 10, 70, 20), on | S::State_Sunken, F::None);
    button(p, "push-disabled", QRect(170, 10, 80, 20), S::State_None, F::None);
    button(p, "push-default", QRect(260, 7, 86, 26), on, F::DefaultButton);
    button(p, "push-default-pressed", QRect(360, 7, 78, 26), on | S::State_Sunken, F::DefaultButton);

    int x = 10;
    const struct {
        const char *name;
        S::State state;
    } checks[] = {
        {"check-off", on | S::State_Off},
        {"check-on", on | S::State_On},
        {"check-off-pressed", on | S::State_Off | S::State_Sunken},
        {"check-on-pressed", on | S::State_On | S::State_Sunken},
        {"check-off-disabled", S::State_Off},
        {"check-on-disabled", S::State_On},
    };
    for (const auto &c : checks) {
        toggle(p, c.name, S::PE_IndicatorCheckBox, QPoint(x, 50), c.state);
        x += 24;
    }
    x = 10;
    const struct {
        const char *name;
        S::State state;
    } radios[] = {
        {"radio-off", on | S::State_Off},
        {"radio-on", on | S::State_On},
        {"radio-off-pressed", on | S::State_Off | S::State_Sunken},
        {"radio-on-pressed", on | S::State_On | S::State_Sunken},
        {"radio-off-disabled", S::State_Off},
        {"radio-on-disabled", S::State_On},
    };
    for (const auto &r : radios) {
        toggle(p, r.name, S::PE_IndicatorRadioButton, QPoint(x, 70), r.state);
        x += 24;
    }

    // Sized like reference/scroll-vertical-inactive.png (System Folder) and
    // reference/disclosure-triangles.png (Applications, both bars).
    scrollbar(p, "vbar-top", QRect(560, 10, 16, 347), Qt::Vertical, 0, 975);
    scrollbar(p, "vbar-mid", QRect(600, 10, 16, 323), Qt::Vertical, 252, 708);
    scrollbar(p, "hbar", QRect(10, 380, 389, 16), Qt::Horizontal, 0, 1266);
    // Pop-ups sit on the #EEEEEE panel of the Appearance control panel.
    p.fillRect(QRect(5, 420, 690, 80), QColor(0xEE, 0xEE, 0xEE));
    popup(p, "popup", QRect(10, 430, 180, 20), on);
    popup(p, "popup-pressed", QRect(200, 430, 180, 20), on | S::State_Sunken);
    popup(p, "popup-disabled", QRect(390, 430, 194, 20), S::State_None);
    // Sliders like General Controls (91 px, 3 ticks, middle) and Memory.
    slider(p, "slider", QRect(10, 520, 91, 23), on, 2, 1, true);
    slider(p, "slider-pressed", QRect(120, 520, 91, 23), on | S::State_Sunken, 2, 1, true);
    slider(p, "slider-disabled", QRect(230, 520, 140, 16), S::State_None, 2, 0, false);
    // Progress bars like the copy window: 188 px, 55 % (101 of 184 inner
    // columns) and empty; the barber pole pinned to the first Sherlock frame.
    progress(p, "progress-55", QRect(10, 560, 188, 14), 0, 184, 101);
    progress(p, "progress-0", QRect(220, 560, 188, 14), 0, 184, 0);
    progress(p, "progress-busy", QRect(430, 560, 188, 14), 0, 0, 0);
    // Tabs like reference/appearance-1-themes.png (Themes current, the
    // whole pane), tab-pressed.png (Appearance current, Sound pressed) and
    // appearance-6-options.png (Options current).
    tabRow(p, "tabs-themes", QRect(5, 641, 466, 280), 0, -1);
    tabRow(p, "tabs-pressed", QRect(520, 641, 466, 40), 1, 4);
    tabRow(p, "tabs-options", QRect(520, 721, 466, 40), 5, -1);

    // The Finder's View menu (reference/menu-view-checked.png), "as Icons"
    // highlighted, rendered by the real QMenu (item layout is Qt's). Its
    // width comes from our font, not Charcoal's, so check-style.sh compares
    // the left and right ends.
    {
        QMenu menu;
        QAction *first = menu.addAction(QStringLiteral("as Icons"));
        menu.addAction(QStringLiteral("as Buttons"));
        QAction *list = menu.addAction(QStringLiteral("as List"));
        list->setCheckable(true);
        list->setChecked(true);
        menu.addSeparator();
        QAction *window = menu.addAction(QStringLiteral("as Window"));
        window->setCheckable(true);
        window->setChecked(true);
        menu.addAction(QStringLiteral("as Pop-up Window"));
        menu.addSeparator();
        menu.addAction(QStringLiteral("Clean Up"))->setEnabled(false);
        menu.addMenu(QStringLiteral("Sort List"))->addAction(QStringLiteral("by Name"));
        menu.addAction(QStringLiteral("Reset Column Positions"));
        menu.addSeparator();
        QAction *options = menu.addAction(QStringLiteral("View Options…"));
        options->setShortcut(QKeySequence(QStringLiteral("Ctrl+J")));
        options->setShortcutVisibleInContextMenu(true);
        menu.popup(QPoint(0, 0));
        menu.setActiveAction(first);
        QApplication::processEvents();
        const QPixmap pm = menu.grab();
        p.drawPixmap(520, 780, pm);
        report("menu-view", QRect(QPoint(520, 780), pm.size()));
        menu.hide();
    }
    // An open pop-up menu's list like reference/popup-open.png: ten items,
    // the 6th current (check mark + highlight), no icons.
    {
        QComboBox combo;
        for (const char *s : {"Bondi", "Blueberry", "Green", "Plum", "Poppy", "Purple", "Teal", "Yellow", "Gray", "Other…"}) {
            combo.addItem(QString::fromUtf8(s));
        }
        combo.setCurrentIndex(5);
        combo.move(0, 300);
        combo.show();
        combo.showPopup();
        QApplication::processEvents();
        QWidget *list = combo.view()->window();
        const QPixmap pm = list->grab();
        p.drawPixmap(800, 780, pm);
        report("popup-list", QRect(QPoint(800, 780), pm.size()));
        combo.hidePopup();
        combo.hide();
    }
    // Spin boxes like the Fonts tab's size fields
    // (reference/appearance-3-fonts-clean.png): 30x26 field + 2 px + 22x20
    // little arrows, unfocused ("10") and focused ("12"), on the tab pane's
    // #EEEEEE. Their text is the line edit's, not drawn here.
    p.fillRect(QRect(150, 924, 160, 34), QColor(0xEE, 0xEE, 0xEE));
    for (int i = 0; i < 2; ++i) {
        QStyleOptionSpinBox o;
        o.initFrom(host);
        o.rect = QRect(160 + i * 70, 928, 54, 26);
        o.frame = true;
        o.buttonSymbols = QAbstractSpinBox::UpDownArrows;
        o.stepEnabled = QAbstractSpinBox::StepUpEnabled | QAbstractSpinBox::StepDownEnabled;
        o.subControls = QStyle::SC_SpinBoxFrame | QStyle::SC_SpinBoxEditField | QStyle::SC_SpinBoxUp | QStyle::SC_SpinBoxDown;
        o.state = QStyle::State_Enabled | QStyle::State_Active;
        if (i == 1) {
            o.state |= QStyle::State_HasFocus;
        }
        style->drawComplexControl(QStyle::CC_SpinBox, &o, &p, host);
        report(i == 0 ? "spin" : "spin-focused", o.rect);
    }
    // The General Controls "Desktop" group box (frame 538..863 x 259..367 in
    // reference/controls-general-controls.png), its title 13 px in; the
    // box's rect starts where the title's top would be.
    {
        QStyleOptionGroupBox o;
        o.initFrom(host);
        o.text = QStringLiteral("Desktop");
        o.subControls = QStyle::SC_GroupBoxFrame | QStyle::SC_GroupBoxLabel;
        o.state = QStyle::State_Enabled | QStyle::State_Active;
        const int top = 1000 - (o.fontMetrics.ascent() - 1);
        o.rect = QRect(10, top, 326, 1109 - top);
        style->drawComplexControl(QStyle::CC_GroupBox, &o, &p, host);
        report("groupbox", QRect(10, 1000, 326, 109));
    }
    // Finder list header sections like reference/disclosure-triangles.png:
    // "Name" sorted (238 px), "Date Modified" (149 px); no labels.
    {
        QStyleOptionHeader o;
        o.initFrom(host);
        o.state = QStyle::State_Enabled | QStyle::State_Active | QStyle::State_Horizontal;
        o.rect = QRect(360, 1000, 238, 21);
        o.sortIndicator = QStyleOptionHeader::SortDown;
        style->drawControl(QStyle::CE_HeaderSection, &o, &p, host);
        o.rect = QRect(598, 1000, 149, 21);
        o.sortIndicator = QStyleOptionHeader::None;
        style->drawControl(QStyle::CE_HeaderSection, &o, &p, host);
        report("header", QRect(360, 1000, 387, 21));
    }
    // Disclosure triangles (closed, open) in 17x17 cells on the sorted
    // column's #DDDDDD, and a separator line (HLine).
    {
        QStyleOption o;
        o.initFrom(host);
        o.state = QStyle::State_Enabled | QStyle::State_Children;
        o.rect = QRect(360, 1040, 17, 17);
        style->drawPrimitive(QStyle::PE_IndicatorBranch, &o, &p, host);
        o.state |= QStyle::State_Open;
        o.rect = QRect(390, 1040, 17, 17);
        style->drawPrimitive(QStyle::PE_IndicatorBranch, &o, &p, host);
        report("triangles", QRect(360, 1040, 47, 17));
        QStyleOptionFrame f;
        f.initFrom(host);
        f.frameShape = QFrame::HLine;
        f.rect = QRect(360, 1080, 100, 4);
        p.fillRect(QRect(360, 1076, 100, 12), QColor(0xEE, 0xEE, 0xEE));
        style->drawControl(QStyle::CE_ShapedFrame, &f, &p, host);
        report("separator", f.rect);
    }
    // Menu bar: an empty stretch, and the "File" title open (35 px like the
    // capture's).
    {
        QStyleOptionMenuItem o;
        o.initFrom(host);
        o.menuItemType = QStyleOptionMenuItem::Normal;
        o.rect = QRect(10, 930, 80, 20);
        o.state = QStyle::State_Enabled;
        style->drawControl(QStyle::CE_MenuBarEmptyArea, &o, &p, host);
        o.rect = QRect(100, 930, 35, 20);
        o.state = QStyle::State_Enabled | QStyle::State_Selected | QStyle::State_Sunken;
        style->drawControl(QStyle::CE_MenuBarItem, &o, &p, host);
        report("menubar-file", o.rect);
    }
    p.end();
    return img.save(QString::fromLocal8Bit(argv[1])) ? 0 : 1;
}
