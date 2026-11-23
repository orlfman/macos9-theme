/*
 * Platinum window decoration for KWin.
 *
 * Draws the Mac OS 9.2.2 Platinum window frame from measured pixels
 * (docs/REFERENCE.md, reference captures in reference/, checks in
 * docs/FINDINGS.md):
 *
 * - a 6 px frame: black edge, raised bevel (white top/left, #999999
 *   bottom/right), 2 px #CCCCCC face, a sunken bevel around the content
 *   (#999999 top/left, white bottom/right) and a 1 px black content line;
 * - a title bar with the close box on the left, zoom and collapse boxes on the
 *   right (13x13, etched, diagonal gradient), etched pinstripes, and the
 *   window icon and title centered, with the stripes stopping around them;
 * - inactive windows flat #DDDDDD with #555555 lines, no boxes and no stripes;
 * - the collapse box on both the shade and the minimize button (Wayland
 *   windows can't be shaded in KWin 6.8);
 * - a hard 1 px drop shadow on the right and bottom (black, or #555555 on
 *   inactive windows).
 *
 * Long titles are condensed first and dropped (icon only) when they still
 * don't fit, as Mac OS 9 does. Everything is drawn in whole logical pixels
 * (true 1x, the user's choice); the metrics are in platinum.h.
 *
 * Structure (button groups, relayout, maximized handling) adapted from the
 * user's windows2000-union decoration (BSD-2-Clause).
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */

#include "platinum.h"

#include <KDecoration3/DecoratedWindow>
#include <KDecoration3/DecorationSettings>
#include <KPluginFactory>

#include <QFontMetricsF>
#include <QIcon>
#include <QPainter>
#include <QTimer>

#include <algorithm>

K_PLUGIN_FACTORY_WITH_JSON(PlatinumDecorationFactory, "platinum.json", registerPlugin<Platinum::Decoration>(); registerPlugin<Platinum::Button>(
    [](QWidget *, QObject *parent, const KPluginMetaData &, const QVariantList &args) -> QObject * {
        if (args.size() < 2 || !args[0].canConvert<KDecoration3::DecorationButtonType>()) {
            return nullptr;
        }
        return Platinum::Button::create(args[0].value<KDecoration3::DecorationButtonType>(),
                                        args[1].value<KDecoration3::Decoration *>(), parent);
    });)

namespace Platinum
{

using KDecoration3::DecorationButtonType;
using namespace Metrics;

namespace
{

QColor gray(int v)
{
    return QColor(v, v, v);
}

// Whole-pixel lines and dots; coordinates are inclusive.
void hline(QPainter *p, int x0, int x1, int y, const QColor &c)
{
    if (x1 >= x0) {
        p->fillRect(QRect(x0, y, x1 - x0 + 1, 1), c);
    }
}

void vline(QPainter *p, int x, int y0, int y1, const QColor &c)
{
    if (y1 >= y0) {
        p->fillRect(QRect(x, y0, 1, y1 - y0 + 1), c);
    }
}

void dot(QPainter *p, int x, int y, const QColor &c)
{
    p->fillRect(QRect(x, y, 1, 1), c);
}

enum class Glyph {
    None,
    Zoom, // small box in the top-left quadrant
    Collapse, // two bars
};

// A 13x13 title bar box with its top-left corner at (x, y). Measured from
// window-document-active.png (normal) and window-close-pressed.png /
// window-zoom-pressed.png (pressed).
void drawBox(QPainter *p, int x, int y, Glyph glyph, bool pressed)
{
    // Etched edge around the box: #888888 top/left, white bottom/right.
    hline(p, x, x + 11, y, gray(0x88));
    vline(p, x, y, y + 11, gray(0x88));
    dot(p, x + 12, y, gray(0xCC));
    dot(p, x, y + 12, gray(0xCC));
    hline(p, x + 1, x + 12, y + 12, Qt::white);
    vline(p, x + 12, y + 1, y + 12, Qt::white);

    const QColor frame = gray(0x22);
    hline(p, x + 1, x + 11, y + 1, frame);
    hline(p, x + 1, x + 11, y + 11, frame);
    vline(p, x + 1, y + 1, y + 11, frame);
    vline(p, x + 11, y + 1, y + 11, frame);

    // The 9x9 inside (columns and rows 2..10), a diagonal ramp in 2 px steps.
    if (pressed) {
        static const int ramp[] = {0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC};
        for (int r = 0; r < 9; ++r) {
            for (int c = 0; c < 9; ++c) {
                int v = ramp[(r + c) / 2];
                if (r == 8 || c == 8) {
                    v = std::min(v, 0x99); // the shadow edge stays at #999999
                }
                dot(p, x + 2 + c, y + 2 + r, gray(v));
            }
        }
    } else {
        static const int ramp[] = {0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
        dot(p, x + 2, y + 2, Qt::white);
        hline(p, x + 3, x + 10, y + 2, gray(0xCC));
        vline(p, x + 2, y + 3, y + 10, gray(0xCC));
        hline(p, x + 3, x + 10, y + 10, gray(0x88));
        vline(p, x + 10, y + 3, y + 9, gray(0x88));
        for (int r = 0; r < 7; ++r) {
            for (int c = 0; c < 7; ++c) {
                dot(p, x + 3 + c, y + 3 + r, gray(ramp[(r + c) / 2]));
            }
        }
    }

    switch (glyph) {
    case Glyph::Zoom:
        vline(p, x + 7, y + 2, y + 7, frame);
        hline(p, x + 2, x + 7, y + 7, frame);
        break;
    case Glyph::Collapse:
        hline(p, x + 2, x + 10, y + 5, frame);
        hline(p, x + 2, x + 10, y + 7, frame);
        break;
    case Glyph::None:
        break;
    }
}

// Etched pinstripes in the title bar: white rows, each with a #777777 row
// under it shifted one pixel right. x0..x1 are the white rows' ends.
void drawStripes(QPainter *p, int x0, int x1, int y)
{
    if (x1 < x0) {
        return;
    }
    for (int i = 0; i < StripeRows; ++i) {
        hline(p, x0, x1, y + 2 * i, Qt::white);
        hline(p, x0 + 1, x1 + 1, y + 2 * i + 1, gray(0x77));
    }
}

// The hard drop shadow: 1 px, right and bottom, starting 2 px in from the
// top-right and bottom-left corners; black on active windows, #555555 on
// inactive ones (window-document-active.png, window-document-inactive.png).
std::shared_ptr<KDecoration3::DecorationShadow> createShadow(QRgb color)
{
    QImage image(6, 6, QImage::Format_ARGB32_Premultiplied);
    image.fill(Qt::transparent);
    for (int i = 2; i < 6; ++i) {
        image.setPixel(5, i, color);
        image.setPixel(i, 5, color);
    }
    auto shadow = std::make_shared<KDecoration3::DecorationShadow>();
    shadow->setPadding(QMarginsF(0, 0, 1, 1));
    shadow->setInnerShadowRect(QRectF(2, 2, 1, 1));
    shadow->setShadow(image);
    return shadow;
}

} // namespace

/*
 * Decoration
 */

namespace
{
// KWin creates and destroys decorations on its GUI thread. Retain both
// variants across focus changes until the last decoration goes away.
int decorationCount = 0;
std::shared_ptr<KDecoration3::DecorationShadow> activeShadow, inactiveShadow;
} // namespace

Decoration::Decoration(QObject *parent, const QVariantList &args)
    : KDecoration3::Decoration(parent, args)
{
    ++decorationCount;
}

Decoration::~Decoration()
{
    if (--decorationCount == 0) {
        activeShadow.reset();
        inactiveShadow.reset();
    }
}

bool Decoration::isActiveLook() const
{
    return window()->isActive();
}

bool Decoration::maximized() const
{
    return window()->isMaximized();
}

bool Decoration::init()
{
    auto *w = window();
    auto *s = settings().get();
    using Window = KDecoration3::DecoratedWindow;
    using Settings = KDecoration3::DecorationSettings;

    connect(w, &Window::activeChanged, this, [this] {
        updateShadow();
        update();
    });
    connect(w, &Window::captionChanged, this, [this] {
        update(titleBarRect());
    });
    connect(w, &Window::iconChanged, this, [this] {
        update(titleBarRect());
    });
    connect(w, &Window::paletteChanged, this, [this] {
        update();
    });
    connect(w, &Window::widthChanged, this, &Decoration::updateButtonsGeometry);
    // setBorders() proposes a state. Lay out against the applied borders,
    // even when the compositor applies that state after the width change.
    connect(this, &KDecoration3::Decoration::bordersChanged, this, &Decoration::updateButtonsGeometry);
    connect(w, &Window::maximizedChanged, this, &Decoration::updateBorders);
    connect(w, &Window::maximizedHorizontallyChanged, this, &Decoration::updateBorders);
    connect(w, &Window::maximizedVerticallyChanged, this, &Decoration::updateBorders);
    connect(w, &Window::shadedChanged, this, &Decoration::recalculate);
    connect(w, &Window::resizeableChanged, this, &Decoration::recalculate);
    connect(s, &Settings::fontChanged, this, &Decoration::recalculate);
    connect(s, &Settings::reconfigured, this, &Decoration::recalculate);
    auto relayout = [this] {
        QTimer::singleShot(0, this, &Decoration::updateButtonsGeometry);
    };
    connect(s, &Settings::decorationButtonsLeftChanged, this, relayout);
    connect(s, &Settings::decorationButtonsRightChanged, this, relayout);

    using Group = KDecoration3::DecorationButtonGroup;
    m_leftButtons = new Group(Group::Position::Left, this, &Button::create);
    m_rightButtons = new Group(Group::Position::Right, this, &Button::create);
    setOpaque(true);
    m_leftButtons->setSpacing(BoxGap);
    m_rightButtons->setSpacing(BoxGap);
    recalculate();
    updateShadow();
    return true;
}

void Decoration::recalculate()
{
    updateBorders();
    updateButtonsGeometry();
}

void Decoration::updateBorders()
{
    auto *w = window();
    const int side = w->isMaximizedHorizontally() ? 0 : Frame;
    const int bottom = w->isMaximizedVertically() ? 0 : Frame;
    setBorders(QMarginsF(side, TitleBar, side, bottom));
    if (w->isResizeable() && !w->isMaximized()) {
        // The 6 px frame is enough to grab; a little more at the corners helps.
        setResizeOnlyBorders(QMarginsF(2, 0, 2, 2));
    } else {
        setResizeOnlyBorders(QMarginsF());
    }
}

QRectF Decoration::titleBarRect() const
{
    // Everything above the sunken bevel row moves the window.
    return QRectF(0, 0, size().width(), TitleBar - 2);
}

void Decoration::updateButtonsGeometry()
{
    if (!m_leftButtons || !m_rightButtons) {
        return;
    }
    const int width = int(size().width());
    // Boxes sit 4 px in from the window's edges; between boxes on one side
    // there are 3 px (16 px per box). The groups only lay themselves out now
    // and then, so every button is placed here.
    auto place = [&](KDecoration3::DecorationButtonGroup *group, bool left) {
        const auto buttons = group->buttons();
        QList<KDecoration3::DecorationButton *> shown;
        for (KDecoration3::DecorationButton *b : buttons) {
            if (b->isVisible()) {
                shown << b;
            } else {
                b->setGeometry(QRectF(0, 0, BoxSize, BoxSize));
            }
        }
        const int count = int(shown.size());
        const int span = count > 0 ? count * BoxSize + (count - 1) * BoxGap : 0;
        int x = left ? BoxInset : width - BoxInset - span;
        group->setPos(QPointF(x, BoxInset));
        for (KDecoration3::DecorationButton *b : std::as_const(shown)) {
            b->setGeometry(QRectF(x, BoxInset, BoxSize, BoxSize));
            x += BoxSize + BoxGap;
        }
    };
    place(m_leftButtons, true);
    place(m_rightButtons, false);
    setTitleBar(titleBarRect());
    update();
}

void Decoration::updateShadow()
{
    if (!activeShadow) {
        activeShadow = createShadow(qRgba(0, 0, 0, 255));
        inactiveShadow = createShadow(qRgba(0x55, 0x55, 0x55, 255));
    }
    setShadow(isActiveLook() ? activeShadow : inactiveShadow);
}

void Decoration::paint(QPainter *painter, const QRectF &repaintArea)
{
    painter->save();
    painter->setRenderHint(QPainter::Antialiasing, false);
    paintFrame(painter);
    if (repaintArea.isEmpty() || repaintArea.intersects(titleBarRect())) {
        paintTitle(painter);
    }
    m_leftButtons->paint(painter, repaintArea);
    m_rightButtons->paint(painter, repaintArea);
    painter->restore();
}

void Decoration::paintFrame(QPainter *painter)
{
    const int W = int(size().width());
    const int H = int(size().height());
    const int left = int(borderLeft());
    const int right = int(borderRight());
    const int bottom = int(borderBottom());
    const bool active = isActiveLook();
    const QColor face = active ? gray(0xCC) : gray(0xDD);
    // Black lines turn #555555 on inactive windows.
    const QColor line = active ? QColor(Qt::black) : gray(0x55);

    // Face color everywhere around the client.
    painter->fillRect(QRect(0, 0, W, TitleBar), face);
    painter->fillRect(QRect(0, TitleBar, left, H - TitleBar), face);
    painter->fillRect(QRect(W - right, TitleBar, right, H - TitleBar), face);
    painter->fillRect(QRect(0, H - bottom, W, bottom), face);

    const bool sides = left > 0;
    const bool hasBottom = bottom > 0;
    // Outer edge.
    hline(painter, 0, W - 1, 0, line);
    if (sides) {
        vline(painter, 0, 0, H - 1, line);
        vline(painter, W - 1, 0, H - 1, line);
    }
    if (hasBottom) {
        hline(painter, 0, W - 1, H - 1, line);
    }

    if (active) {
        // Raised bevel: white top/left, #999999 right/bottom.
        hline(painter, sides ? 1 : 0, W - (sides ? 3 : 1), 1, Qt::white);
        if (sides) {
            vline(painter, 1, 1, H - (hasBottom ? 3 : 1), Qt::white);
            vline(painter, W - 2, 2, H - (hasBottom ? 2 : 1), gray(0x99));
        }
        if (hasBottom) {
            hline(painter, 2, W - 2, H - 2, gray(0x99));
        }
        // Sunken bevel around the content: #999999 top/left, white right/bottom.
        const int inL = sides ? 4 : 0, inR = sides ? W - 5 : W - 1;
        const int inB = hasBottom ? H - 5 : H - 1;
        hline(painter, inL, inR - 1, TitleBar - 2, gray(0x99));
        if (sides) {
            vline(painter, inL, TitleBar - 2, inB - 1, gray(0x99));
            vline(painter, inR, TitleBar - 1, inB, Qt::white);
        }
        if (hasBottom) {
            hline(painter, inL + 1, inR, inB, Qt::white);
        }
    }

    // The 1 px line around the content.
    const int cL = sides ? Frame - 1 : 0, cR = sides ? W - Frame : W - 1;
    const int cB = hasBottom ? H - Frame : H - 1;
    hline(painter, cL, cR, TitleBar - 1, line);
    if (sides) {
        vline(painter, cL, TitleBar - 1, cB, line);
        vline(painter, cR, TitleBar - 1, cB, line);
    }
    if (hasBottom) {
        hline(painter, cL, cR, cB, line);
    }
}

void Decoration::paintTitle(QPainter *painter)
{
    const int W = int(size().width());
    const bool active = isActiveLook();

    // Where the pinstripes may go: 5 px after the left boxes, 5 px before
    // the right ones (white rows; the gray rows reach one pixel further).
    int stripeL = BoxInset;
    int stripeR = W - 1 - BoxInset;
    if (!m_leftButtons->buttons().isEmpty()) {
        // QRectF::right() is the first column past the group.
        stripeL = int(m_leftButtons->geometry().right()) - 1 + StripeGap;
    }
    if (!m_rightButtons->buttons().isEmpty()) {
        stripeR = int(m_rightButtons->geometry().left()) - StripeGap - 1;
    }

    // Title: icon + text, centered on the window. Too wide: condense the
    // text; still too wide: drop it and keep the icon (as Mac OS 9 does).
    const QString caption = window()->caption();
    QFont font = settings()->font();
    const int room = stripeR - stripeL + 1 - 2 * StripeGap;
    QString text = caption;
    qreal textWidth = 0;
    if (!text.isEmpty()) {
        for (int stretch : {100, 92, 85, 78}) {
            font.setStretch(stretch);
            textWidth = QFontMetricsF(font).horizontalAdvance(text);
            if (IconSize + IconTextGap + textWidth <= room) {
                break;
            }
        }
        if (IconSize + IconTextGap + textWidth > room) {
            text.clear();
            textWidth = 0;
        }
    }
    const bool showIcon = room >= IconSize;
    const int content = (showIcon ? IconSize : 0) + (text.isEmpty() ? 0 : (showIcon ? IconTextGap : 0) + int(std::ceil(textWidth)));
    const int contentL = (W - content) / 2;
    const int contentR = contentL + content - 1;

    if (active) {
        if (content > 0) {
            drawStripes(painter, stripeL, contentL - StripeGap - 1, BoxInset);
            drawStripes(painter, contentR + StripeGap + 1, stripeR, BoxInset);
        } else {
            drawStripes(painter, stripeL, stripeR, BoxInset);
        }
    }

    int x = contentL;
    if (showIcon) {
        const QIcon icon = window()->icon();
        const QPixmap pm = icon.pixmap(QSize(IconSize, IconSize), painter->device()->devicePixelRatioF(),
                                       active ? QIcon::Normal : QIcon::Disabled);
        painter->drawPixmap(QRect(x, 2, IconSize, IconSize), pm);
        x += IconSize + IconTextGap;
    }
    if (!text.isEmpty()) {
        const auto group = active ? KDecoration3::ColorGroup::Active : KDecoration3::ColorGroup::Inactive;
        painter->setFont(font);
        painter->setPen(window()->color(group, KDecoration3::ColorRole::Foreground));
        painter->drawText(QRectF(x, BoxInset, textWidth + 1, 2 * StripeRows), Qt::AlignLeft | Qt::AlignVCenter | Qt::TextSingleLine, text);
    }
}

/*
 * Buttons
 */

Button::Button(DecorationButtonType type, Decoration *decoration, QObject *parent)
    : KDecoration3::DecorationButton(type, decoration, parent)
{
    connect(this, &DecorationButton::visibilityChanged, decoration, &Decoration::updateButtonsGeometry, Qt::QueuedConnection);
}

KDecoration3::DecorationButton *Button::create(DecorationButtonType type, KDecoration3::Decoration *decoration, QObject *parent)
{
    auto *d = qobject_cast<Decoration *>(decoration);
    // Only Mac OS 9's three boxes. Other buttons someone adds in System
    // Settings (window menu, on all desktops, keep above, help, ...) have no
    // Platinum look and would otherwise all look like the close box, so
    // they're left out (AUDIT.md finding 20).
    switch (type) {
    case DecorationButtonType::Close:
    case DecorationButtonType::Maximize:
    case DecorationButtonType::Minimize:
    case DecorationButtonType::Shade:
        break;
    default:
        return nullptr;
    }
    return d ? new Button(type, d, parent) : nullptr;
}

void Button::paint(QPainter *painter, const QRectF &repaintArea)
{
    Q_UNUSED(repaintArea)
    auto *d = qobject_cast<Decoration *>(decoration());
    // Inactive Platinum windows show no boxes at all.
    if (!d || !isVisible() || geometry().isEmpty() || !d->isActiveLook()) {
        return;
    }
    Glyph glyph = Glyph::None;
    switch (type()) {
    case DecorationButtonType::Maximize:
        glyph = Glyph::Zoom;
        break;
    // Mac OS 9's collapse box rolls the window up (shade). KWin 6.8 doesn't
    // shade Wayland windows (isShadeable() is false, so the Shade button
    // never shows), so the minimize button wears the collapse box too: same
    // look, minimizes instead (docs/FINDINGS.md).
    case DecorationButtonType::Shade:
    case DecorationButtonType::Minimize:
        glyph = Glyph::Collapse;
        break;
    default:
        break;
    }
    painter->save();
    painter->setRenderHint(QPainter::Antialiasing, false);
    const QPoint at = geometry().topLeft().toPoint();
    drawBox(painter, at.x(), at.y(), glyph, isPressed() && isHovered());
    painter->restore();
}

} // namespace Platinum

#include "platinum.moc"
