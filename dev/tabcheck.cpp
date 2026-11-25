// Checks that bottom (south) Platinum tabs are the top (north) tabs upside
// down: tab faces in every state, the tab bar base, the tab pane, and whole
// tab widgets (plain and document mode): exact mirrors at whole scales,
// the 1x mirror scaled the way Qt scales whole pixels at fractional ones. Labels stay
// upright, so a bottom label is the top label 2 rows lower.
// usage: tabcheck   (run with QT_PLUGIN_PATH set to the style's plugins)
#include <QApplication>
#include <QImage>
#include <QPainter>
#include <QStyleFactory>
#include <QStyleOption>
#include <QTabBar>
#include <QTabWidget>
#include <QWidget>
#include <cstdio>
#include <functional>

static int failures = 0;
static void check(const char *name, bool ok)
{
    std::printf("%s %s\n", ok ? "ok     " : "FAIL   ", name);
    failures += !ok;
}
static QImage blank(QSize logical, qreal dpr)
{
    QImage img((QSizeF(logical) * dpr).toSize(), QImage::Format_ARGB32_Premultiplied);
    img.setDevicePixelRatio(dpr);
    img.fill(QColor(0x63, 0x63, 0x9c));
    return img;
}
static int differences(const QImage &a, const QImage &b)
{
    if (a.size() != b.size()) {
        return -1;
    }
    int n = 0;
    for (int y = 0; y < a.height(); ++y) {
        for (int x = 0; x < a.width(); ++x) {
            n += a.pixel(x, y) != b.pixel(x, y);
        }
    }
    return n;
}
static QImage flipped(const QImage &img)
{
    QImage f = img.flipped(Qt::Vertical);
    f.setDevicePixelRatio(img.devicePixelRatio());
    return f;
}
// What a whole-pixel drawing at 1x becomes at a fractional scale: logical
// row (column) n covers device rows qRound(n * dpr) up to qRound((n + 1) *
// dpr), as Qt's raster engine fills whole-pixel rectangles.
static QImage scaledLikeQt(const QImage &logical, qreal dpr)
{
    const auto map = [dpr](int count) {
        QList<int> device(qRound(count * dpr), 0);
        for (int n = 0; n < count; ++n) {
            for (int d = qRound(n * dpr); d < qRound((n + 1) * dpr) && d < device.size(); ++d) {
                device[d] = n;
            }
        }
        return device;
    };
    const QList<int> xs = map(logical.width()), ys = map(logical.height());
    QImage out(xs.size(), ys.size(), QImage::Format_ARGB32_Premultiplied);
    for (int y = 0; y < ys.size(); ++y) {
        for (int x = 0; x < xs.size(); ++x) {
            out.setPixel(x, y, logical.pixel(xs[x], ys[y]));
        }
    }
    out.setDevicePixelRatio(dpr);
    return out;
}
// A bottom part mirrors the top one: exactly at whole scales; at fractional
// scales it must be the 1x top part flipped and then scaled the way Qt
// scales whole pixels (and the top part must scale that way too, which
// checks the model, AUDIT.md #237).
static bool mirrors(const QImage &south, const QImage &north, const QImage &north1x, qreal dpr)
{
    if (dpr == qRound(dpr)) {
        return differences(south, flipped(north)) == 0;
    }
    return differences(north, scaledLikeQt(north1x, dpr)) == 0 && differences(south, scaledLikeQt(flipped(north1x), dpr)) == 0;
}

int main(int argc, char **argv)
{
    QApplication app(argc, argv);
    QStyle *style = QStyleFactory::create(QStringLiteral("Platinum"));
    if (!style) {
        std::printf("FAIL    the Platinum style isn't available\n");
        return 1;
    }
    QApplication::setStyle(style);

    // Tab faces and the tab bar base, drawn directly.
    struct State { const char *name; QStyle::State state; };
    const State states[] = {
        {"normal", QStyle::State_Enabled},
        {"current", QStyle::State_Enabled | QStyle::State_Selected},
        {"pressed", QStyle::State_Enabled | QStyle::State_Sunken},
        {"disabled", QStyle::State_None},
    };
    const auto face = [&](const State &s, QTabBar::Shape shape, qreal dpr) {
        QImage img = blank(QSize(90, 24), dpr);
        QPainter p(&img);
        QStyleOptionTab tab;
        tab.rect = QRect(0, 0, 90, 24);
        tab.state = s.state;
        tab.shape = shape;
        style->drawControl(QStyle::CE_TabBarTabShape, &tab, &p, nullptr);
        return img;
    };
    const auto base = [&](QTabBar::Shape shape, qreal dpr) {
        QImage img = blank(QSize(120, 6), dpr);
        QPainter p(&img);
        QStyleOptionTabBarBase o;
        o.rect = QRect(0, 0, 120, 6);
        o.shape = shape;
        style->drawPrimitive(QStyle::PE_FrameTabBarBase, &o, &p, nullptr);
        return img;
    };
    const auto pane = [&](QTabBar::Shape shape, qreal dpr) {
        QImage img = blank(QSize(160, 90), dpr);
        QPainter p(&img);
        QStyleOptionTabWidgetFrame o;
        o.rect = QRect(0, 0, 160, 90);
        o.shape = shape;
        style->drawPrimitive(QStyle::PE_FrameTabWidget, &o, &p, nullptr);
        return img;
    };
    const auto N = QTabBar::RoundedNorth, S = QTabBar::RoundedSouth;
    for (qreal dpr : {1.0, 1.25, 1.5, 2.0}) {
        for (const State &s : states) {
            const QByteArray name = QStringLiteral("%1 tab face mirrors the top tab at %2x").arg(QLatin1String(s.name)).arg(dpr).toUtf8();
            check(name.constData(), mirrors(face(s, S, dpr), face(s, N, dpr), face(s, N, 1.0), dpr));
        }
        const QByteArray baseName = QStringLiteral("tab bar base mirrors the top one at %1x").arg(dpr).toUtf8();
        check(baseName.constData(), mirrors(base(S, dpr), base(N, dpr), base(N, 1.0), dpr));
        const QByteArray paneName = QStringLiteral("tab pane mirrors the top one at %1x").arg(dpr).toUtf8();
        check(paneName.constData(), mirrors(pane(S, dpr), pane(N, dpr), pane(N, 1.0), dpr));
    }

    // Every tab part draws whole pixels even for a caller whose painter
    // antialiases (AUDIT.md #238).
    const auto antialiased = [&](QSize size, qreal dpr, const std::function<void(QPainter &)> &draw) {
        QImage img[2];
        for (int aa = 0; aa < 2; ++aa) {
            img[aa] = blank(size, dpr);
            QPainter p(&img[aa]);
            p.setRenderHint(QPainter::Antialiasing, aa);
            draw(p);
        }
        return differences(img[0], img[1]) == 0;
    };
    for (qreal dpr : {1.25, 1.5, 1.75}) {
        for (QTabBar::Shape shape : {N, S}) {
            const QString where = QStringLiteral("%1 at %2x").arg(QLatin1String(shape == N ? "top" : "bottom")).arg(dpr);
            bool ok = antialiased(QSize(120, 6), dpr, [&](QPainter &p) {
                QStyleOptionTabBarBase o;
                o.rect = QRect(0, 0, 120, 6);
                o.shape = shape;
                style->drawPrimitive(QStyle::PE_FrameTabBarBase, &o, &p, nullptr);
            });
            check(QStringLiteral("tab bar base ignores an antialiasing painter, %1").arg(where).toUtf8().constData(), ok);
            ok = antialiased(QSize(90, 24), dpr, [&](QPainter &p) {
                QStyleOptionTab tab;
                tab.rect = QRect(0, 0, 90, 24);
                tab.state = QStyle::State_Enabled | QStyle::State_Selected;
                tab.shape = shape;
                style->drawControl(QStyle::CE_TabBarTabShape, &tab, &p, nullptr);
            });
            check(QStringLiteral("tab face ignores an antialiasing painter, %1").arg(where).toUtf8().constData(), ok);
            ok = antialiased(QSize(160, 90), dpr, [&](QPainter &p) {
                QStyleOptionTabWidgetFrame o;
                o.rect = QRect(0, 0, 160, 90);
                o.shape = shape;
                style->drawPrimitive(QStyle::PE_FrameTabWidget, &o, &p, nullptr);
            });
            check(QStringLiteral("tab pane ignores an antialiasing painter, %1").arg(where).toUtf8().constData(), ok);
        }
    }

    // Labels stay upright: a bottom label is the top label 2 rows lower.
    {
        QImage img[2];
        for (int south = 0; south < 2; ++south) {
            img[south] = blank(QSize(90, 24), 1.0);
            QPainter p(&img[south]);
            QStyleOptionTab tab;
            tab.rect = QRect(0, 0, 90, 24);
            tab.state = QStyle::State_Enabled;
            tab.shape = south ? QTabBar::RoundedSouth : QTabBar::RoundedNorth;
            tab.text = QStringLiteral("General");
            tab.fontMetrics = QFontMetrics(QApplication::font());
            style->drawControl(QStyle::CE_TabBarTabLabel, &tab, &p, nullptr);
        }
        QImage moved = blank(QSize(90, 24), 1.0);
        QPainter(&moved).drawImage(QPoint(0, 2), img[0]);
        check("bottom label is the top label 2 rows lower (upright)", differences(img[1].copy(0, 2, 90, 22), moved.copy(0, 2, 90, 22)) == 0);
    }

    // A long title in a closable tab stays out of the close button, top and
    // bottom, left to right and right to left (AUDIT.md #236).
    for (QTabBar::Shape shape : {N, S}) {
        for (Qt::LayoutDirection dir : {Qt::LeftToRight, Qt::RightToLeft}) {
            QTabBar bar;
            bar.setLayoutDirection(dir);
            bar.setShape(shape);
            bar.setTabsClosable(true);
            bar.setElideMode(Qt::ElideRight);
            bar.setUsesScrollButtons(false);
            bar.setExpanding(false);
            bar.addTab(QStringLiteral("macos9-theme : pieman@linux64:~/Files/Archive/projects/macos9-theme"));
            bar.addTab(QStringLiteral("other"));
            bar.resize(230, bar.sizeHint().height());
            bar.show();
            QCoreApplication::processEvents();
            QWidget *button = bar.tabButton(0, QTabBar::RightSide);
            if (!button) {
                button = bar.tabButton(0, QTabBar::LeftSide);
            }
            const QRect area = button ? button->geometry() : QRect();
            if (button) {
                button->hide();
            }
            QCoreApplication::processEvents();
            const QImage img = bar.grab().toImage();
            int text = 0;
            for (int y = area.top(); y <= area.bottom(); ++y) {
                for (int x = area.left(); x <= area.right(); ++x) {
                    text += img.pixelColor(x, y).value() < 110;
                }
            }
            const QByteArray name = QStringLiteral("%1 %2 tab title stays out of the close button (%3 px inside)")
                                        .arg(QLatin1String(shape == N ? "top" : "bottom"), QLatin1String(dir == Qt::LeftToRight ? "LTR" : "RTL"))
                                        .arg(text)
                                        .toUtf8();
            check(name.constData(), button && text == 0);
        }
    }

    // Whole tab widgets, with blank titles so only the shapes count.
    for (bool document : {false, true}) {
        QImage shot[2];
        for (int south = 0; south < 2; ++south) {
            QTabWidget tabs;
            tabs.setDocumentMode(document);
            tabs.setTabPosition(south ? QTabWidget::South : QTabWidget::North);
            for (int i = 0; i < 3; ++i) {
                tabs.addTab(new QWidget, QString());
            }
            tabs.setCurrentIndex(1);
            tabs.resize(320, 160);
            tabs.ensurePolished();
            tabs.show();
            QCoreApplication::processEvents();
            shot[south] = tabs.grab().toImage().convertToFormat(QImage::Format_ARGB32_Premultiplied);
        }
        const int diff = differences(shot[1], flipped(shot[0]));
        const QByteArray name = QStringLiteral("%1 tab widget with bottom tabs mirrors the top one (%2 px differ)")
                                    .arg(QLatin1String(document ? "document-mode" : "plain")).arg(diff).toUtf8();
        check(name.constData(), diff == 0);
    }
    return failures ? 1 : 0;
}
