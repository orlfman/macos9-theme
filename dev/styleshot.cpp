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
//   the captures.
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
    QImage img(700, 420, QImage::Format_RGB32);
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
    p.end();
    return img.save(QString::fromLocal8Bit(argv[1])) ? 0 : 1;
}
