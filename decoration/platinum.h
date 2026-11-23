/*
 * Platinum window decoration for KWin: a Mac OS 9.2.2 Platinum window frame
 * drawn from measured pixels (docs/REFERENCE.md, docs/FINDINGS.md).
 *
 * Structure adapted from the user's windows2000-union decoration
 * (BSD-2-Clause).
 *
 * SPDX-License-Identifier: BSD-2-Clause
 */

#pragma once

#include <KDecoration3/Decoration>
#include <KDecoration3/DecorationButton>
#include <KDecoration3/DecorationButtonGroup>
#include <KDecoration3/DecorationShadow>

#include <QVariantList>

namespace Platinum
{

// All Platinum metrics, at 1x (the user's decision: true 1x pixels). Kept in
// one place so a later scale change is cheap.
namespace Metrics
{
constexpr int Frame = 6;        // each side and the bottom, content line included
constexpr int TitleBar = 22;    // top border: title bar rows + bevel + content line
constexpr int BoxSize = 13;     // close / zoom / collapse box, etched edge included
constexpr int BoxInset = 4;     // from the window's left/right/top edge
constexpr int BoxGap = 3;       // between zoom and collapse
constexpr int StripeGap = 5;    // from a box to the pinstripes, and around the title
constexpr int StripeRows = 6;   // white rows (each with a gray row under it)
constexpr int IconSize = 16;
constexpr int IconTextGap = 4;
} // namespace Metrics

class Decoration : public KDecoration3::Decoration
{
    Q_OBJECT

public:
    explicit Decoration(QObject *parent = nullptr, const QVariantList &args = QVariantList());
    ~Decoration() override;

    bool init() override;
    void paint(QPainter *painter, const QRectF &repaintArea) override;

    bool isActiveLook() const;

private:
    friend class Button;
    void recalculate();
    void updateBorders();
    void updateButtonsGeometry();
    void updateShadow();

    bool maximized() const;
    QRectF titleBarRect() const;
    void paintFrame(QPainter *painter);
    void paintTitle(QPainter *painter);

    KDecoration3::DecorationButtonGroup *m_leftButtons = nullptr;
    KDecoration3::DecorationButtonGroup *m_rightButtons = nullptr;
};

class Button : public KDecoration3::DecorationButton
{
    Q_OBJECT

public:
    Button(KDecoration3::DecorationButtonType type, Decoration *decoration, QObject *parent = nullptr);

    static KDecoration3::DecorationButton *create(KDecoration3::DecorationButtonType type, KDecoration3::Decoration *decoration, QObject *parent);

    void paint(QPainter *painter, const QRectF &repaintArea) override;
};

} // namespace Platinum
