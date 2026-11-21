// 9-slice and sprite drawing for measured Platinum parts. Values are
// 0xRRGGBB or -1 (not drawn).
//
// SPDX-License-Identifier: BSD-2-Clause
#pragma once

#include <QPainter>
#include <QRect>

#include <array>

namespace Platinum
{

template<int K>
struct NineSlice {
    int tl[K][K], tr[K][K], bl[K][K], br[K][K];
    int top[K], bottom[K], left[K], right[K];
    int fill;
};

inline void putPixel(QPainter *p, int x, int y, int v)
{
    if (v >= 0) {
        p->fillRect(QRect(x, y, 1, 1), QColor::fromRgb(QRgb(v)));
    }
}

// Draws s over r: corners as measured, edges stretched, center filled.
template<int K>
void drawNineSlice(QPainter *p, const QRect &r, const NineSlice<K> &s, bool fillCenter = true)
{
    const int x = r.x(), y = r.y(), w = r.width(), h = r.height();
    if (w < 2 * K || h < 2 * K) {
        return;
    }
    if (fillCenter) {
        p->fillRect(QRect(x + K, y + K, w - 2 * K, h - 2 * K), QColor::fromRgb(QRgb(s.fill)));
    }
    for (int i = 0; i < K; ++i) {
        p->fillRect(QRect(x + K, y + i, w - 2 * K, 1), QColor::fromRgb(QRgb(s.top[i])));
        p->fillRect(QRect(x + K, y + h - K + i, w - 2 * K, 1), QColor::fromRgb(QRgb(s.bottom[i])));
        p->fillRect(QRect(x + i, y + K, 1, h - 2 * K), QColor::fromRgb(QRgb(s.left[i])));
        p->fillRect(QRect(x + w - K + i, y + K, 1, h - 2 * K), QColor::fromRgb(QRgb(s.right[i])));
    }
    for (int row = 0; row < K; ++row) {
        for (int col = 0; col < K; ++col) {
            putPixel(p, x + col, y + row, s.tl[row][col]);
            putPixel(p, x + w - K + col, y + row, s.tr[row][col]);
            putPixel(p, x + col, y + h - K + row, s.bl[row][col]);
            putPixel(p, x + w - K + col, y + h - K + row, s.br[row][col]);
        }
    }
}

} // namespace Platinum
