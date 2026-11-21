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
} // namespace Metrics

class Style : public QProxyStyle
{
    Q_OBJECT

public:
    Style();

    QString name() const;
    int pixelMetric(PixelMetric metric, const QStyleOption *option, const QWidget *widget) const override;
    QSize sizeFromContents(ContentsType type, const QStyleOption *option, const QSize &size, const QWidget *widget) const override;
    QRect subControlRect(ComplexControl control, const QStyleOptionComplex *option, SubControl sub, const QWidget *widget) const override;
    SubControl hitTestComplexControl(ComplexControl control, const QStyleOptionComplex *option, const QPoint &pos, const QWidget *widget) const override;
    void drawComplexControl(ComplexControl control, const QStyleOptionComplex *option, QPainter *painter, const QWidget *widget) const override;
    void drawControl(ControlElement element, const QStyleOption *option, QPainter *painter, const QWidget *widget) const override;
    void drawPrimitive(PrimitiveElement element, const QStyleOption *option, QPainter *painter, const QWidget *widget) const override;
    int styleHint(StyleHint hint, const QStyleOption *option, const QWidget *widget, QStyleHintReturn *returnData) const override;

private:
    void drawScrollBar(const QStyleOptionSlider *option, QPainter *painter, const QWidget *widget) const;
};

} // namespace Platinum
