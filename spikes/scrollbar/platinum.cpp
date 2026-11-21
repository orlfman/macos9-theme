// Step 3 spike: can a plain C++ QStyle draw a Mac OS 9 Platinum scroll bar
// pixel for pixel? A QProxyStyle over Fusion that handles only vertical
// scroll bars, with "Smart Scrolling" (both arrows at the bottom) and the
// colors and metrics measured from reference/scroll-vertical-inactive.png
// (System Folder list, active). Renders one bar to PNG for tools/compare.py.
//
// usage: platinum OUT.png [HEIGHT VALUE PAGE]
#include <QtWidgets>

namespace {
// Measured Platinum colors (docs/REFERENCE.md)
const QColor Black(0x00, 0x00, 0x00), White(0xFF, 0xFF, 0xFF);
const QColor G77(0x77, 0x77, 0x77), G88(0x88, 0x88, 0x88), GAA(0xAA, 0xAA, 0xAA);
const QColor GBB(0xBB, 0xBB, 0xBB), GCC(0xCC, 0xCC, 0xCC), GDD(0xDD, 0xDD, 0xDD), GEE(0xEE, 0xEE, 0xEE);
const QColor L1(0xCC, 0xCC, 0xFF), L2(0x99, 0x99, 0xFF), L3(0x66, 0x66, 0xCC), L4(0x33, 0x33, 0x99);

constexpr int Extent = 16;   // bar width, both black edges included
constexpr int ArrowBox = 16; // each arrow box, its two black edges included
// The two arrow boxes share their middle edge, so they take 31 rows.
constexpr int Arrows = ArrowBox * 2 - 1;

void hline(QPainter &p, int x0, int x1, int y, const QColor &c) { p.fillRect(x0, y, x1 - x0 + 1, 1, c); }
void vline(QPainter &p, int x, int y0, int y1, const QColor &c) { p.fillRect(x, y0, 1, y1 - y0 + 1, c); }

// One arrow box: r covers both black edges (16x16), up or down glyph.
void drawArrow(QPainter &p, const QRect &r, bool up, bool pressed)
{
    const int x = r.x(), y = r.y(), w = r.width(), h = r.height();
    hline(p, x, x + w - 1, y, Black);
    hline(p, x, x + w - 1, y + h - 1, Black);
    vline(p, x, y, y + h - 1, Black);
    vline(p, x + w - 1, y, y + h - 1, Black);
    const QColor hi = pressed ? QColor(0x55, 0x55, 0x55) : White;
    const QColor fill = pressed ? G77 : GDD;
    const QColor lo = pressed ? QColor(0x99, 0x99, 0x99) : GBB;
    p.fillRect(x + 1, y + 1, w - 2, h - 2, fill);
    hline(p, x + 1, x + w - 3, y + 1, hi);       // top highlight
    vline(p, x + 1, y + 1, y + h - 3, hi);       // left highlight
    vline(p, x + w - 2, y + 2, y + h - 2, lo);   // right shadow
    hline(p, x + 2, x + w - 2, y + h - 2, lo);   // bottom shadow
    // Triangle 2, 4, 6, 8 px wide on rows 6..9, centered.
    const int cx = x + w / 2 - 1;
    for (int i = 0; i < 4; ++i) {
        const int half = up ? i : 3 - i;
        hline(p, cx - half, cx + 1 + half, y + 6 + i, Black);
    }
}

void drawThumb(QPainter &p, const QRect &r, bool pressed)
{
    const int x = r.x(), y = r.y(), w = r.width(), h = r.height();
    const QColor hi = pressed ? L2 : L1, fill = pressed ? L3 : L2, lo = pressed ? L4 : L3;
    hline(p, x, x + w - 1, y, Black);
    hline(p, x, x + w - 1, y + h - 1, Black);
    vline(p, x, y, y + h - 1, Black);
    vline(p, x + w - 1, y, y + h - 1, Black);
    p.fillRect(x + 1, y + 1, w - 2, h - 2, fill);
    vline(p, x + 1, y + 1, y + h - 3, hi);
    hline(p, x + 1, x + w - 3, y + 1, hi);
    p.fillRect(x + 1, y + 1, 1, 1, pressed ? L1 : GEE);   // top-left corner
    vline(p, x + w - 2, y + 2, y + h - 2, lo);
    hline(p, x + 2, x + w - 2, y + h - 2, lo);
    // Grip: 4 dark lines with a light line above each, centered.
    const int gy = y + (h - 8) / 2;
    for (int i = 0; i < 4; ++i) {
        hline(p, x + 5, x + 10, gy + 2 * i, L1);
        p.fillRect(x + 4, gy + 2 * i, 1, 1, GEE);
        hline(p, x + 5, x + 11, gy + 2 * i + 1, L4);
    }
}

// Sunken track. topShadow: the two shadow rows right under the thumb (or at
// the top of the track).
void drawTrack(QPainter &p, const QRect &r, bool topShadow)
{
    if (r.isEmpty())
        return;
    const int x = r.x(), y = r.y(), w = r.width(), h = r.height();
    vline(p, x, y, y + h - 1, Black);
    vline(p, x + w - 1, y, y + h - 1, Black);
    p.fillRect(x + 1, y, w - 2, h, GAA);
    vline(p, x + 1, y, y + h - 1, G77);
    vline(p, x + 2, y, y + h - 1, G88);
    vline(p, x + w - 3, y, y + h - 1, GBB);
    vline(p, x + w - 2, y, y + h - 1, GCC);
    if (topShadow) {
        hline(p, x + 1, x + w - 3, y, G77);
        if (h > 1)
            hline(p, x + 3, x + w - 4, y + 1, G88);
    }
}
} // namespace

class PlatinumStyle : public QProxyStyle
{
public:
    PlatinumStyle() : QProxyStyle(QStringLiteral("Fusion")) {}

    int pixelMetric(PixelMetric m, const QStyleOption *o, const QWidget *w) const override
    {
        if (m == PM_ScrollBarExtent)
            return Extent;
        if (m == PM_ScrollBarSliderMin)
            return 16;
        return QProxyStyle::pixelMetric(m, o, w);
    }

    QRect subControlRect(ComplexControl cc, const QStyleOptionComplex *opt, SubControl sc,
                         const QWidget *w) const override
    {
        const auto *sb = qstyleoption_cast<const QStyleOptionSlider *>(opt);
        if (cc != CC_ScrollBar || !sb || sb->orientation != Qt::Vertical)
            return QProxyStyle::subControlRect(cc, opt, sc, w);
        const QRect r = sb->rect;
        const int track = r.height() - Arrows; // rows above the arrows
        const int range = sb->maximum - sb->minimum;
        int len = range > 0 ? int(qint64(track) * sb->pageStep / (range + sb->pageStep)) : track;
        len = qBound(pixelMetric(PM_ScrollBarSliderMin, opt, w), len, track);
        const int pos = range > 0 ? int(qint64(track - len) * (sb->sliderPosition - sb->minimum) / range) : 0;
        switch (sc) {
        case SC_ScrollBarSubLine: return QRect(r.x(), r.y() + track, r.width(), ArrowBox);
        case SC_ScrollBarAddLine: return QRect(r.x(), r.y() + track + ArrowBox - 1, r.width(), ArrowBox);
        case SC_ScrollBarGroove: return QRect(r.x(), r.y(), r.width(), track);
        case SC_ScrollBarSlider: return QRect(r.x(), r.y() + pos, r.width(), len);
        case SC_ScrollBarSubPage: return QRect(r.x(), r.y(), r.width(), pos);
        case SC_ScrollBarAddPage: return QRect(r.x(), r.y() + pos + len, r.width(), track - pos - len);
        default: return QProxyStyle::subControlRect(cc, opt, sc, w);
        }
    }

    SubControl hitTestComplexControl(ComplexControl cc, const QStyleOptionComplex *opt,
                                     const QPoint &pt, const QWidget *w) const override
    {
        if (cc == CC_ScrollBar)
            for (SubControl sc : {SC_ScrollBarSlider, SC_ScrollBarSubLine, SC_ScrollBarAddLine,
                                  SC_ScrollBarSubPage, SC_ScrollBarAddPage})
                if (subControlRect(cc, opt, sc, w).contains(pt))
                    return sc;
        return QProxyStyle::hitTestComplexControl(cc, opt, pt, w);
    }

    void drawComplexControl(ComplexControl cc, const QStyleOptionComplex *opt, QPainter *p,
                            const QWidget *w) const override
    {
        const auto *sb = qstyleoption_cast<const QStyleOptionSlider *>(opt);
        if (cc != CC_ScrollBar || !sb || sb->orientation != Qt::Vertical) {
            QProxyStyle::drawComplexControl(cc, opt, p, w);
            return;
        }
        p->save();
        const bool active = sb->state & State_Active;
        const auto rect = [&](SubControl sc) { return subControlRect(cc, opt, sc, w); };
        const auto down = [&](SubControl sc) { return (sb->activeSubControls & sc) && (sb->state & State_Sunken); };
        if (!active) {
            // Inactive window: flat empty bar, no thumb, no arrows (captured).
            p->fillRect(sb->rect, GEE);
            vline(*p, sb->rect.left(), sb->rect.top(), sb->rect.bottom(), QColor(0x55, 0x55, 0x55));
            p->restore();
            return;
        }
        // The bar's own top edge; the track (and its shadow) starts below it.
        // When the thumb is at the top, its black edge is this row.
        hline(*p, sb->rect.left(), sb->rect.right(), sb->rect.top(), Black);
        drawTrack(*p, rect(SC_ScrollBarSubPage).adjusted(0, 1, 0, 0), true);
        drawTrack(*p, rect(SC_ScrollBarAddPage), true);
        drawThumb(*p, rect(SC_ScrollBarSlider), down(SC_ScrollBarSlider));
        drawArrow(*p, rect(SC_ScrollBarSubLine), true, down(SC_ScrollBarSubLine));
        drawArrow(*p, rect(SC_ScrollBarAddLine), false, down(SC_ScrollBarAddLine));
        p->restore();
    }
};

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    if (argc < 2) {
        std::fprintf(stderr, "usage: platinum OUT.png [HEIGHT VALUE PAGE]\n");
        return 2;
    }
    const int height = argc > 2 ? atoi(argv[2]) : 347;
    const int value = argc > 3 ? atoi(argv[3]) : 0;
    const int page = argc > 4 ? atoi(argv[4]) : 975;
    auto *style = new PlatinumStyle;
    QScrollBar bar(Qt::Vertical);
    bar.setStyle(style);
    bar.setRange(0, 1000);
    bar.setPageStep(page);
    bar.setValue(value);
    bar.resize(Extent, height);
    bar.setAttribute(Qt::WA_DontShowOnScreen);
    bar.show();
    // Offscreen windows aren't active; force the active look.
    bar.activateWindow();
    QPixmap pm(bar.size());
    pm.fill(Qt::magenta);
    {
        QStyleOptionSlider opt;
        opt.initFrom(&bar);
        opt.orientation = Qt::Vertical;
        opt.minimum = bar.minimum(); opt.maximum = bar.maximum();
        opt.pageStep = bar.pageStep(); opt.singleStep = bar.singleStep();
        opt.sliderPosition = opt.sliderValue = bar.value();
        opt.subControls = QStyle::SC_All;
        opt.state |= QStyle::State_Active | QStyle::State_Enabled;
        QPainter p(&pm);
        style->drawComplexControl(QStyle::CC_ScrollBar, &opt, &p, &bar);
    }
    return pm.save(QString::fromLocal8Bit(argv[1])) ? 0 : 1;
}
