// Asks the current QStyle where it puts a vertical scroll bar's parts, so we
// can tell whether a style can draw Mac OS 9 "Smart Scrolling" arrows at all.
#include <QtWidgets>
#include <cstdio>

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    QScrollBar bar(Qt::Vertical);
    bar.resize(16, 300);
    bar.setRange(0, 1000);
    bar.setPageStep(200);
    bar.setValue(300);
    QStyleOptionSlider opt;
    opt.initFrom(&bar);
    opt.orientation = Qt::Vertical;
    opt.minimum = 0; opt.maximum = 1000; opt.pageStep = 200; opt.singleStep = 20;
    opt.sliderPosition = opt.sliderValue = 300;
    opt.subControls = QStyle::SC_All;
    auto *s = bar.style();
    std::printf("style %s, extent %d\n", qPrintable(s->name()), s->pixelMetric(QStyle::PM_ScrollBarExtent, &opt, &bar));
    const struct { QStyle::SubControl sc; const char *name; } parts[] = {
        {QStyle::SC_ScrollBarSubLine, "SubLine (up arrow)"},
        {QStyle::SC_ScrollBarAddLine, "AddLine (down arrow)"},
        {QStyle::SC_ScrollBarGroove, "Groove"},
        {QStyle::SC_ScrollBarSlider, "Slider"},
        {QStyle::SC_ScrollBarSubPage, "SubPage"},
        {QStyle::SC_ScrollBarAddPage, "AddPage"},
    };
    for (auto p : parts) {
        QRect r = s->subControlRect(QStyle::CC_ScrollBar, &opt, p.sc, &bar);
        std::printf("  %-22s %3d,%3d %3dx%3d\n", p.name, r.x(), r.y(), r.width(), r.height());
    }
    return 0;
}
