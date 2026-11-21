// Step 3 spike: draw a Mac OS 9 Platinum title bar with plain QPainter, the
// way a C++ KDecoration3 plugin would, and compare it with
// reference/window-document-active.png (Mac OS window, active). The title
// text and icon are left out (no Charcoal); the spike leaves their gap empty.
//
// usage: titlebar OUT.png WIDTH GAP_LEFT GAP_RIGHT
//   WIDTH      outer window width including the 1 px drop shadow column
//   GAP_*      first and last column of the title gap (white pinstripe rows
//              end at GAP_LEFT-1 and start again at GAP_RIGHT)
#include <QtGui>

namespace {
QColor gray(int v) { return QColor(v, v, v); }
void px(QPainter &p, int x, int y, const QColor &c) { p.fillRect(x, y, 1, 1, c); }
void hline(QPainter &p, int x0, int x1, int y, const QColor &c) { if (x1 >= x0) p.fillRect(x0, y, x1 - x0 + 1, 1, c); }
void vline(QPainter &p, int x, int y0, int y1, const QColor &c) { if (y1 >= y0) p.fillRect(x, y0, 1, y1 - y0 + 1, c); }

enum class Glyph { None, Zoom, Collapse };

// A 13x13 title bar box at (x, y): etched frame, 9x9 diagonal gradient.
void drawBox(QPainter &p, int x, int y, Glyph g)
{
    static const int ramp[] = {0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
    hline(p, x, x + 11, y, gray(0x88));             // etched shadow, top
    vline(p, x, y, y + 11, gray(0x88));             // and left
    px(p, x + 12, y, gray(0xCC));
    px(p, x, y + 12, gray(0xCC));
    hline(p, x + 1, x + 12, y + 12, gray(0xFF));    // etched highlight, bottom
    vline(p, x + 12, y + 1, y + 12, gray(0xFF));    // and right
    const QColor frame = gray(0x22);
    hline(p, x + 1, x + 11, y + 1, frame);
    hline(p, x + 1, x + 11, y + 11, frame);
    vline(p, x + 1, y + 1, y + 11, frame);
    vline(p, x + 11, y + 1, y + 11, frame);
    // Inside (cols/rows 2..10): highlight top/left, shadow bottom/right.
    px(p, x + 2, y + 2, gray(0xFF));
    hline(p, x + 3, x + 10, y + 2, gray(0xCC));
    vline(p, x + 2, y + 3, y + 10, gray(0xCC));
    hline(p, x + 3, x + 10, y + 10, gray(0x88));
    vline(p, x + 10, y + 3, y + 9, gray(0x88));
    for (int r = 0; r < 7; ++r)
        for (int c = 0; c < 7; ++c)
            px(p, x + 3 + c, y + 3 + r, gray(ramp[(r + c) / 2]));
    if (g == Glyph::Zoom) {                          // small box, top left
        vline(p, x + 7, y + 2, y + 7, frame);
        hline(p, x + 2, x + 7, y + 7, frame);
    } else if (g == Glyph::Collapse) {               // two bars
        hline(p, x + 2, x + 10, y + 5, frame);
        hline(p, x + 2, x + 10, y + 7, frame);
    }
}

// Etched pinstripes: 6 white rows, each with a #777777 row under it that
// is shifted one pixel right.
void pinstripes(QPainter &p, int x0, int x1, int y)
{
    for (int i = 0; i < 6; ++i) {
        hline(p, x0, x1, y + 2 * i, gray(0xFF));
        hline(p, x0 + 1, x1 + 1, y + 2 * i + 1, gray(0x77));
    }
}
} // namespace

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    if (argc < 5) {
        std::fprintf(stderr, "usage: titlebar OUT.png WIDTH GAP_LEFT GAP_RIGHT\n");
        return 2;
    }
    const int width = atoi(argv[2]), gapL = atoi(argv[3]), gapR = atoi(argv[4]);
    const int height = 20;            // title bar rows above the content edge
    QImage img(width, height, QImage::Format_RGB32);
    img.fill(QColor(0x63, 0x63, 0x9C)); // desktop, shows in the shadow corner
    QPainter p(&img);
    const int r = width - 2;          // right window edge (black)

    // Frame: black edge, white highlight, #CCCCCC face; on the right a
    // #999999 shadow inside the black edge and a 1 px black drop shadow.
    hline(p, 0, r, 0, Qt::black);
    vline(p, 0, 0, height - 1, Qt::black);
    vline(p, r, 0, height - 1, Qt::black);
    vline(p, r + 1, 2, height - 1, Qt::black);
    p.fillRect(1, 1, r - 1, height - 1, gray(0xCC));
    hline(p, 1, r - 2, 1, gray(0xFF));
    vline(p, 1, 1, height - 1, gray(0xFF));
    vline(p, r - 1, 2, height - 1, gray(0x99));

    // Boxes: close at the left, zoom and collapse at the right.
    const int boxY = 4, closeX = 4, collapseX = r - 16, zoomX = collapseX - 16;
    drawBox(p, closeX, boxY, Glyph::None);
    drawBox(p, zoomX, boxY, Glyph::Zoom);
    drawBox(p, collapseX, boxY, Glyph::Collapse);

    // Pinstripes from 5 px after the close box to 5 px before the zoom box,
    // with the title gap left open.
    const int stripeL = closeX + 13 + 4, stripeR = zoomX - 6;
    pinstripes(p, stripeL, gapL - 1, boxY);
    pinstripes(p, gapR, stripeR, boxY);
    p.end();
    return img.save(QString::fromLocal8Bit(argv[1])) ? 0 : 1;
}
