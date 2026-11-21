/*
 * Platinum: a Qt application style that draws Mac OS 9.2.2's Platinum
 * appearance from measured pixels (docs/REFERENCE.md). Built over Fusion,
 * which still draws everything not themed yet.
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */
#pragma once

#include <QProxyStyle>

class QStyleOptionSlider;
class QStyleOptionSpinBox;
class QStyleOptionGroupBox;
class QStyleOptionToolButton;

namespace Platinum
{

// All Platinum metrics at 1x (the user's decision), in one place.
namespace Metrics
{
constexpr int ScrollBarExtent = 16; // both black edges included
constexpr int ScrollArrowBox = 16;  // each arrow box, both black edges
constexpr int ScrollThumbMin = 16;
constexpr int ButtonHeight = 20;
constexpr int DefaultRing = 3;      // around default buttons
constexpr int ButtonMinWidth = 58;
constexpr int ButtonTextPadding = 12;
constexpr int CheckWidth = 14;      // 12 px box + 2 px check overhang
constexpr int CheckHeight = 12;
constexpr int RadioSize = 12;
constexpr int PopupHeight = 20;
constexpr int PopupArrowWidth = 22;  // the arrow box, divider included
constexpr int SliderThumbWidth = 15;
constexpr int SliderThumbHeight = 16;
constexpr int SliderInset = 3;       // thumb travel starts 3 px inside the groove
constexpr int SliderGrooveTop = 3;   // groove (with its outer lines) below the thumb's top
constexpr int SliderGrooveHeight = 7;
constexpr int SliderTickHeight = 7;
constexpr int ProgressHeight = 14;
constexpr int TabHeight = 24;        // 21 rows of tab + the pane's 3 top rows
constexpr int TabPaneOverlap = 3;    // black line, #CCCCCC, white
constexpr int TabTextPadding = 12;   // each side; tab width = text + 24
constexpr int TabInset = 5;          // first tab's left edge from the pane's
constexpr int TabPaneFrame = 3;      // black outline + 2 px bevel
// Menus: offsets from an item's left edge (1 px inside the menu's black
// line) and from its right edge.
constexpr int MenuItemHeight = 16;
constexpr int MenuIconItemHeight = 18;
constexpr int MenuSeparatorHeight = 6;
constexpr int MenuCheckLeft = 3;
constexpr int MenuIconLeft = 18;
constexpr int MenuTextLeft = 21;
constexpr int MenuIconTextLeft = 40;
constexpr int MenuTextRight = 20;      // last text column to the item's right edge
constexpr int MenuShortcutGap = 18;    // label end to shortcut column
constexpr int MenuArrowRight = 6;      // submenu arrow's last column to the item's right edge
constexpr int MenuArrowWidth = 6;
constexpr int MenuArrowHeight = 11;
constexpr int MenuBarHeight = 20;
constexpr int MenuBarItemPadding = 7;  // each side of a menu title
// Text fields: 1 px margin (the focus ring's outer row), 1 px sunken edge
// (or the ring's inner row), 1 px black line; text 3 px inside the black.
constexpr int FieldFrame = 3;
constexpr int FieldMinHeight = 26;
constexpr int SpinArrowsWidth = 22;
constexpr int SpinArrowsHeight = 20;
constexpr int SpinArrowsGap = 2;        // field edge to the arrows
// Group boxes: etched #888888 / white rectangle, title 13 px in with a
// 4 px gap each side, its bottom row on the top line.
constexpr int GroupTitleLeft = 13;
constexpr int GroupTitleGap = 4;
constexpr int HeaderHeight = 21;        // Finder list header
constexpr int HeaderMargin = 8;         // label from the section's left line
constexpr int FrameWidth = 2;           // list / text area frame: sunken edge + black line
constexpr int ToolButtonPadding = 9;   // 16 px icon -> 25 px bevel (Mac Help's toolbar)
constexpr int ToolTipFrame = 10;       // balloon outline to text (Mac pads ~12)
} // namespace Metrics

class Style : public QProxyStyle
{
    Q_OBJECT

public:
    Style();

    QString name() const;
    int pixelMetric(PixelMetric metric, const QStyleOption *option, const QWidget *widget) const override;
    QSize sizeFromContents(ContentsType type, const QStyleOption *option, const QSize &size, const QWidget *widget) const override;
    QRect subElementRect(SubElement element, const QStyleOption *option, const QWidget *widget) const override;
    QRect subControlRect(ComplexControl control, const QStyleOptionComplex *option, SubControl sub, const QWidget *widget) const override;
    SubControl hitTestComplexControl(ComplexControl control, const QStyleOptionComplex *option, const QPoint &pos, const QWidget *widget) const override;
    void drawComplexControl(ComplexControl control, const QStyleOptionComplex *option, QPainter *painter, const QWidget *widget) const override;
    void drawControl(ControlElement element, const QStyleOption *option, QPainter *painter, const QWidget *widget) const override;
    void drawPrimitive(PrimitiveElement element, const QStyleOption *option, QPainter *painter, const QWidget *widget) const override;
    int styleHint(StyleHint hint, const QStyleOption *option, const QWidget *widget, QStyleHintReturn *returnData) const override;
    void polish(QWidget *widget) override;
    void unpolish(QWidget *widget) override;
    bool eventFilter(QObject *object, QEvent *event) override;
    using QProxyStyle::polish;
    using QProxyStyle::unpolish;

private:
    void drawScrollBar(const QStyleOptionSlider *option, QPainter *painter, const QWidget *widget) const;
    void drawSlider(const QStyleOptionSlider *option, QPainter *painter, const QWidget *widget) const;
    void drawSpinBox(const QStyleOptionSpinBox *option, QPainter *painter, const QWidget *widget) const;
    void drawGroupBox(const QStyleOptionGroupBox *option, QPainter *painter, const QWidget *widget) const;
    void drawToolButton(const QStyleOptionToolButton *option, QPainter *painter, const QWidget *widget) const;
};

} // namespace Platinum
