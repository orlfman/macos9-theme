// Fixed-size measured parts (check boxes, radio buttons).
//
// SPDX-License-Identifier: BSD-2-Clause
#pragma once

#include "nineslice.h"

namespace Platinum
{

struct Sprite {
    int w, h;
    std::array<int, 24 * 24> data; // up to 24x24
};

inline void drawSprite(QPainter *p, int x, int y, const Sprite &s)
{
    for (int r = 0; r < s.h; ++r) {
        drawRow(p, x, y + r, s.data.data() + r * s.w, s.w);
    }
}

} // namespace Platinum
