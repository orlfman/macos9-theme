#!/bin/bash
# Offscreen software check for the Platinum KDecoration3 plugin: verifies
# reference frame/pinstripe crops against reference/window-document-active.png
# and reference/dialog-get-info.png, plus disabled button hiding, pinstripe
# extension across 3 -> 2 -> 1 -> 0 buttons, caption clearance, and live
# capability restoration (#281, #282, #284-286).
#
# usage: check-deco.sh        (exit 1 if anything fails)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
cd "$project"

mkdir -p "$dev/build"
out=$(mktemp -d "$dev/build/deco-check.XXXXXX")
trap 'rm -rf -- "$out"' EXIT

"$project/decoration/build.sh" > /dev/null
# shellcheck disable=SC2046
g++ -std=c++20 -O2 -fPIC -Wall -Wextra -I/usr/include/KDecoration3 "$dev/decoshot.cpp" -o "$out/decoshot" \
    $(pkg-config --cflags --libs Qt6Widgets Qt6Qml Qt6Quick KF6CoreAddons) -lkdecorations3

# Note: KDecoration.Preview's default layout places Menu (filtered out) on the
# left and Minimize (3), Maximize (4), Close (5) on the right.
cat > "$out/preview.qml" << 'QML'
import QtQuick
import QtQuick.Window
import org.kde.kwin.private.kdecoration as KDecoration

Window {
    id: root
    width: 900
    height: 600
    visible: true
    color: "#63639c"
    property int captureStep: 0

    KDecoration.Bridge {
        id: bridgeItem
        plugin: "platinum"
        theme: ""
    }

    KDecoration.Settings {
        id: settingsItem
        bridge: bridgeItem.bridge
        borderSizesIndex: 3
    }

    component Preview: KDecoration.Decoration {
        property string caption: "Info"
        property bool isActive: true
        property bool closeable: true
        property bool maximizable: true
        property bool minimizable: true
        property int hoverButton: -1
        property int pressButton: -1

        width: 354
        height: 201
        bridge: bridgeItem.bridge
        settings: settingsItem
        drawBackground: true

        onMaximizableChanged: if (client) client.maximizable = maximizable

        Component.onCompleted: {
            client.caption = caption;
            client.iconName = "drive-harddisk";
            client.active = isActive;
            client.shadeable = false;
            client.closeable = closeable;
            client.maximizable = maximizable;
            client.minimizable = minimizable;
        }
    }

    // 3 right boxes (353 px frame): boxes at 304, 320, 336; stripes end at 298
    Preview { objectName: "three-boxes"; x: 10; y: 10 }
    // 2 right boxes (Maximize disabled): boxes at 320, 336; stripes end at 314
    Preview { objectName: "two-boxes"; x: 420; y: 10; maximizable: false }
    // 1 right box (Maximize + Minimize disabled): box at 336; stripes end at 330 (matches Get Info)
    Preview { objectName: "one-box"; x: 10; y: 250; maximizable: false; minimizable: false }
    // 0 boxes (all disabled): stripes run 4..348
    Preview { objectName: "zero-boxes"; x: 420; y: 250; closeable: false; maximizable: false; minimizable: false }
    Preview { x: 10; y: 490; height: 80; maximizable: root.captureStep !== 1 }
    Preview {
        x: 420
        y: 490
        width: 231
        height: 80
        maximizable: false
        caption: "MMMMMMMMMMMMM"
    }
}
QML

shot=$out/deco.png
"$dev/run.sh" platinum breeze env QT_QUICK_BACKEND=software \
    "$out/decoshot" "$out/preview.qml" "$shot" "$out/disabled.png" "$out/restored.png"

python3 -I - "$shot" "$out" << 'PY'
import subprocess, sys
from PIL import Image

shot_path, out = sys.argv[1], sys.argv[2]
im = Image.open(shot_path).convert("RGB")
failed = 0
total = 0

def report(name, ok, detail=""):
    global failed, total
    total += 1
    if not ok:
        failed += 1
    suffix = f" ({detail})" if detail else ""
    print(f"{'ok' if ok else 'FAIL':<8}{name}{suffix}")

def diff_ref(name, ref_spec, ours_spec):
    res = subprocess.run(
        ["python3", "-I", "tools/compare.py", "diff", f"reference/{ref_spec}", f"{shot_path}@{ours_spec}", "--out", f"{out}/cmp.png"],
        capture_output=True, text=True
    )
    info = res.stdout.splitlines()[1].split()[3:6] if len(res.stdout.splitlines()) > 1 else []
    report(name, res.returncode == 0, " ".join(info))

def find_window(x_hint, y_hint, expected_w=353):
    for y in range(y_hint, y_hint + 15):
        for x in range(x_hint, x_hint + 15):
            if all(im.getpixel((x + dx, y)) == (0, 0, 0) for dx in range(expected_w)):
                return x, y
    raise RuntimeError(f"window not found near ({x_hint}, {y_hint})")

def right_metrics(wx, wy):
    row = [im.getpixel((wx + dx, wy + 4)) for dx in range(353)]
    stripe_end = max(dx for dx in range(200, 350) if row[dx] == (255, 255, 255))
    boxes = [dx for dx in range(stripe_end + 2, 351) if row[dx] != (204, 204, 204)]
    box_x = min(boxes) if boxes else None
    return stripe_end, box_x

x3, y3 = find_window(10, 10)
x2, y2 = find_window(420, 10)
x1, y1 = find_window(10, 250)
x0, y0 = find_window(420, 250)
xd, yd = find_window(10, 490)
xn, yn = find_window(420, 490, 230)

# 1-2. Reference pixel comparisons against Mac OS 9.2.2 captures.
diff_ref("side frame matches window-document-active", "window-document-active.png@426,432,6,20", f"{x3},{y3 + 22},6,20")
# In dialog-get-info.png (origin 216,494, w=353), x=293..335 (509..551) is the pinstripe + 5 px gap before the single right box at 336.
diff_ref("single-box right pinstripes and gap match dialog-get-info", "dialog-get-info.png@509,494,43,22", f"{x1 + 293},{y1},43,22")

# 3-6. Pinstripe extension across 3 -> 2 -> 1 -> 0 right buttons (always 5 px gap, never 21 px).
s3, b3 = right_metrics(x3, y3)
report("3 right boxes: stripes end 5 px before first box", s3 == 298 and b3 == 304, f"stripe={s3} box={b3}")

s2, b2 = right_metrics(x2, y2)
row2 = [im.getpixel((x2 + dx, y2 + 4)) for dx in range(353)]
report("disabled zoom extends pinstripes 16 px and keeps 3 px gap to last box",
       s2 == 314 and b2 == 320 and row2[333:336] == [(204, 204, 204)] * 3 and row2[336] == (136, 136, 136),
       f"stripe={s2} box={b2}")

s1, b1 = right_metrics(x1, y1)
report("two disabled boxes extend pinstripes 32 px to 5 px before last box", s1 == 330 and b1 == 336, f"stripe={s1} box={b1}")

row0 = [im.getpixel((x0 + dx, y0 + 4)) for dx in range(353)]
left0 = min(dx for dx, px in enumerate(row0) if px == (255, 255, 255) and dx >= 4)
right0 = max(dx for dx, px in enumerate(row0) if px == (255, 255, 255) and dx <= 349)
report("all boxes disabled extends pinstripes to both 4 px outer insets", left0 == 4 and right0 == 348, f"left={left0} right={right0}")

# 7-9. Compare three captures of the same preview with the static controls.
def title_bar(image, x, y):
    return image.crop((x, y, x + 353, y + 22)).tobytes()

initial = title_bar(im, xd, yd)
disabled = title_bar(Image.open(f"{out}/disabled.png").convert("RGB"), xd, yd)
restored = title_bar(Image.open(f"{out}/restored.png").convert("RGB"), xd, yd)
report("before toggle: title bar matches the three-box preview", initial == title_bar(im, x3, y3))
report("after disabling maximize: title bar matches the two-box preview",
       disabled != initial and disabled == title_bar(im, x2, y2))
report("after re-enabling maximize: title bar matches the initial capture", restored == initial)

# 10. The 230 px frame's first box starts at 197. The title needs 5 px
# before its pinstripe limit (191) as well as the gap before the box.
caption_ink = [x for x in range(130, 197) for y in range(4, 16)
               if im.getpixel((xn + x, yn + y)) == (0, 0, 0)]
last_ink = max(caption_ink, default=-1)
report("centered caption stays clear of asymmetric title-bar boxes",
       130 <= last_ink <= 186, f"rightmost caption ink={last_ink}, box starts at 197")

print(f"\n{total - failed} of {total} decoration checks passed")
sys.exit(1 if failed else 0)
PY
