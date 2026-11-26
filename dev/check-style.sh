#!/bin/bash
# Renders the Platinum style's states with dev/styleshot (sandbox,
# QSTYLE=Platinum) and diffs every captured one with its reference capture.
# Labels are skipped (no Charcoal): push buttons are compared on their four
# edge bands. Regions the captures' mouse pointer covers are left out.
#
# usage: check-style.sh        (exit 1 if anything differs)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
cd "$project"
"$project/style/build.sh" > /dev/null
mkdir -p dev/build dev/shots
# shellcheck disable=SC2046
g++ -std=c++17 -O1 -fPIC dev/styleshot.cpp -o dev/build/styleshot $(pkg-config --cflags --libs Qt6Widgets)
shot=dev/shots/styleshot.png
# Pin a ≤ 16 px font when FONT is unset so menu/popup-list reference crops stay
# 16 px tall even in sandboxes without kdeglobals or under Noto Sans 10 (#283).
style_font=${FONT:-}
if [[ -z $style_font ]]; then
    style_font="SF Pro Text,10"
    [[ $(fc-match -f '%{family}' 'SF Pro Text' 2> /dev/null) == *"SF Pro Text"* ]] || style_font="DejaVu Sans,10"
fi
FONT=$style_font PLATINUM_BARBER_PHASE=4 QSTYLE=Platinum dev/run.sh platinum breeze dev/build/styleshot "$shot" > dev/shots/styleshot.txt 2> /dev/null

failed=0
total=0
check() { # name reference.png@x,y,w,h ours-x,ours-y,w,h
    local name=$1 ref=$2 ours=$3
    total=$((total + 1))
    local result
    if result=$(python3 -I tools/compare.py diff "reference/$ref" "$shot@$ours" --zoom 6 --out "dev/shots/cmp-style-$name.png"); then
        printf 'ok      %-30s %s\n' "$name" "$(sed -n 2p <<< "$result" | cut -d' ' -f4-6)"
    else
        printf 'DIFF    %-30s %s\n' "$name" "$(sed -n 2p <<< "$result" | cut -d' ' -f4-6)"
        failed=$((failed + 1))
    fi
}
# Four edge bands of a W x H button at reference (rx,ry) and ours (ox,oy);
# BW = how much of the bottom band to compare (pointer in some captures).
bands() { # name ref.png rx ry ox oy W H depth BW
    local n=$1 img=$2 rx=$3 ry=$4 ox=$5 oy=$6 W=$7 H=$8 d=$9 bw=${10}
    check "$n-top" "$img@$rx,$ry,$W,$d" "$ox,$oy,$W,$d"
    local bd=$d
    [[ $n == push-default ]] && bd=$((d - 1))
    check "$n-bottom" "$img@$rx,$((ry + H - bd)),$bw,$bd" "$ox,$((oy + H - bd)),$bw,$bd"
    check "$n-left" "$img@$rx,$ry,$d,$H" "$ox,$oy,$d,$H"
    check "$n-right" "$img@$((rx + W - d)),$ry,$d,$((H - (bw < W ? d : 0)))" "$((ox + W - d)),$oy,$d,$((H - (bw < W ? d : 0)))"
}

bands push-normal button-default-pressed.png 617 513 10 10 70 20 4 70
bands push-pressed button-push-pressed.png 641 469 90 10 70 20 4 56
bands push-disabled dialog-file-open.png 851 335 170 10 80 20 4 80
bands push-default dialog-file-open.png 848 435 260 7 86 26 8 86
# (its bottom band starts one row lower: the "p" of "Open" reaches into row 18)
bands push-default-pressed button-default-pressed.png 697 510 360 7 78 26 8 56

check check-off controls-general-controls.png@550,327,14,12 10,50,14,12
check check-on controls-general-controls.png@550,280,14,12 34,50,14,12
check check-off-pressed checkbox-pressed.png@550,327,14,10 58,50,14,10
check check-on-disabled controls-memory.png@553,511,14,12 130,50,14,12
check radio-off controls-general-controls.png@553,534,12,12 10,70,12,12
check radio-on controls-general-controls.png@553,552,12,12 34,70,12,12
check radio-off-pressed radio-pressed.png@553,534,12,8 58,70,12,8
check radio-off-disabled controls-monitors.png@732,405,12,12 106,70,12,12

# Scroll bars: the top row is the list header's edge in the Finder.
check vbar-top scroll-vertical-inactive.png@787,249,16,346 560,11,16,346
check vbar-mid disclosure-triangles.png@492,175,16,322 600,11,16,322
# Horizontal: its left edge is the window's content line.
check hbar disclosure-triangles.png@105,496,388,16 11,380,388,16

# Pop-up menus (label area skipped: top/bottom 3 rows, left 6 columns, and
# the 22-column arrow box). The pressed capture's body is under its menu.
popup_check() { # name ref.png rx ry ox oy W
    local n=$1 img=$2 rx=$3 ry=$4 ox=$5 oy=$6 W=$7
    check "$n-top" "$img@$rx,$ry,$W,3" "$ox,$oy,$W,3"
    check "$n-bottom" "$img@$rx,$((ry + 17)),$W,3" "$ox,$((oy + 17)),$W,3"
    check "$n-left" "$img@$rx,$ry,6,20" "$ox,$oy,6,20"
    check "$n-arrow" "$img@$((rx + W - 22)),$ry,22,20" "$((ox + W - 22)),$oy,22,20"
}
popup_check popup appearance-2-appearance.png 591 257 10 430 180
check popup-pressed-arrow-a popup-open.png@751,298,20,20 360,430,20,20
check popup-pressed-arrow-b popup-open-no-hover.png@749,298,12,20 358,430,12,20
popup_check popup-disabled appearance-4-desktop.png 710 451 390 430 194

# Sliders: the whole slider with ticks; the pressed one's thumb only (the
# capture also has the drag ghost); the disabled one.
check slider controls-general-controls.png@726,438,91,23 10,520,91,23
check slider-pressed-thumb slider-pressed.png@764,438,15,16 158,520,15,16
check slider-disabled controls-memory.png@672,483,140,16 230,520,140,16

# Progress bars: 55 %, empty (copy window), barber pole stripes (inside
# the frame; Sherlock draws its own frame around it).
check progress-55 progress-determinate-55.png@590,276,188,14 10,560,188,14
check progress-0 progress-copy-window.png@590,276,188,14 220,560,188,14
check progress-busy-stripes progress-indeterminate-a.png@1077,473,60,10 432,562,60,10

# Tabs: the strip above the labels, the strip below them down into the pane,
# and the 12 label-free columns on both sides of every tab. tabs_check
# compares a capture's tab row (pane at rx,ry) with ours (pane at ox,oy).
# Above the pane, the capture's two outermost columns on each side are the
# window's (frame black line, then its content area's white / #AAAAAA edge:
# the pane fills the window there), so columns 2-463 are compared.
tab_widths=(72 101 57 74 62 71)
tabs_check() { # name ref.png rx ry ox oy [skip-x0 skip-x1]: columns (pane-relative) to leave out below the labels
    local n=$1 img=$2 rx=$3 ry=$4 ox=$5 oy=$6 s0=${7:-} s1=${8:-}
    local ty=$((ry - 21)) oty=$((oy - 21))
    check "$n-top" "$img@$((rx + 2)),$ty,462,6" "$((ox + 2)),$oty,462,6"
    if [[ -n $s0 ]]; then
        check "$n-bottom-a" "$img@$((rx + 2)),$((ty + 17)),$((s0 - 2)),10" "$((ox + 2)),$((oty + 17)),$((s0 - 2)),10"
        check "$n-bottom-b" "$img@$((rx + s1)),$((ty + 17)),$((464 - s1)),10" "$((ox + s1)),$((oty + 17)),$((464 - s1)),10"
    else
        check "$n-bottom" "$img@$((rx + 2)),$((ty + 17)),462,10" "$((ox + 2)),$((oty + 17)),462,10"
    fi
    # left of the first tab's label, between labels, right of the last one
    local x=5 i
    check "$n-sides-0" "$img@$((rx + 2)),$((ty + 6)),15,11" "$((ox + 2)),$((oty + 6)),15,11"
    for i in 0 1 2 3 4; do
        x=$((x + tab_widths[i]))
        check "$n-sides-$((i + 1))" "$img@$((rx + x - 12)),$((ty + 6)),24,11" "$((ox + x - 12)),$((oty + 6)),24,11"
    done
    x=$((x + tab_widths[5]))
    check "$n-sides-6" "$img@$((rx + x - 12)),$((ty + 6)),$((464 - x + 12)),11" "$((ox + x - 12)),$((oty + 6)),$((464 - x + 12)),11"
}
tabs_check tabs-themes appearance-1-themes.png 469 235 5 641
# the whole pane frame: left, right and bottom bands
check tabs-pane-left appearance-1-themes.png@469,235,4,280 5,641,4,280
check tabs-pane-right appearance-1-themes.png@931,235,4,280 467,641,4,280
check tabs-pane-bottom appearance-1-themes.png@469,511,466,4 5,917,466,4
# the pointer is over the pressed tab's lower right and the pane below it
tabs_check tabs-pressed tab-pressed.png 773 225 520 641 357 373
tabs_check tabs-options appearance-6-options.png 469 235 520 721

# Menus: the Finder's View menu (180x165 at 109,19; "as Icons"
# highlighted). Our width follows our font, so the left 20 columns (check
# marks; text starts at 22, its anti-aliasing at 21) and the right 14 (arrow, black line, shadow;
# the capture's "⌘J" ends just left of them) are compared, from our menu's
# own right end. Left out: the capture's top row past the menu (it's the
# menu bar's black line), the shadow's see-through outer corners, and the
# pointer (right band, rows 12-31).
mw=$(awk '$1 == "menu-view" { split($2, a, ","); print a[3] }' dev/shots/styleshot.txt)
mr=$((520 + mw - 14))
check menu-left menu-view-checked.png@109,19,20,164 520,780,20,164
check menu-bottom-left menu-view-checked.png@111,183,19,1 522,944,19,1
check menu-right-top menu-view-checked.png@275,19,12,12 "$mr,780,12,12"
check menu-right-shadow-top menu-view-checked.png@287,21,2,10 "$((mr + 12)),782,2,10"
check menu-right menu-view-checked.png@275,51,14,114 "$mr,812,14,114"
# Pop-up menu list (popup-open.png: 161x163 at 591,218, "Purple" current
# and highlighted): the left 18 columns (check mark; the capture's color
# swatches start at 19) and the right 5, from our list's own right end.
# The pointer sits on the right end of rows 81-112.
pw=$(awk '$1 == "popup-list" { split($2, a, ","); print a[3] }' dev/shots/styleshot.txt)
pr=$((800 + pw - 5))
check popup-list-left popup-open.png@591,218,18,162 800,780,18,162
check popup-list-bottom-left popup-open.png@593,380,16,1 802,942,16,1
check popup-list-right-top popup-open.png@747,218,4,2 "$pr,780,4,2"
check popup-list-right-a popup-open.png@747,220,5,79 "$pr,782,5,79"
check popup-list-right-b popup-open.png@747,331,5,50 "$pr,893,5,50"
# Menu bar: an empty stretch and the open "File" title (outside its label).
check menubar-empty menu-file-open.png@72,0,7,20 10,930,7,20
check menubar-title-left menu-file-open.png@37,0,7,20 100,930,7,20
check menubar-title-right menu-file-open.png@64,0,8,20 127,930,8,20

# The plain modal dialog frame (Qt Quick dialogs): its four edge bands,
# frame and shadow (the shadow's open corners left out: the capture's
# desktop shows there).
check modal-frame-top dialog-modal-plain.png@766,194,386,4 10,1220,386,4
check modal-frame-left dialog-modal-plain.png@766,194,4,189 10,1220,4,189
check modal-frame-right dialog-modal-plain.png@1149,196,4,188 393,1222,4,188
check modal-frame-bottom dialog-modal-plain.png@768,380,385,4 12,1406,385,4
check menubar-title-top menu-file-open.png@37,0,35,2 100,930,35,2
check menubar-title-bottom menu-file-open.png@37,17,35,3 100,947,35,3

# Text fields: the Fonts tab's size spin boxes (field 30x26 + arrows),
# unfocused at 846,346 and focused (focus ring) at 846,432. The field's
# outer 5 rows / columns (margin or ring, edge, black line, 2 white) are
# compared; inside them are the text and its selection.
field_check() { # name rx ry ox oy
    local n=$1 rx=$2 ry=$3 ox=$4 oy=$5
    check "$n-top" "appearance-3-fonts-clean.png@$rx,$ry,30,5" "$ox,$oy,30,5"
    check "$n-bottom" "appearance-3-fonts-clean.png@$rx,$((ry + 21)),30,5" "$ox,$((oy + 21)),30,5"
    check "$n-left" "appearance-3-fonts-clean.png@$rx,$ry,5,26" "$ox,$oy,5,26"
    check "$n-right" "appearance-3-fonts-clean.png@$((rx + 25)),$ry,5,26" "$((ox + 25)),$oy,5,26"
    check "$n-arrows" "appearance-3-fonts-clean.png@$((rx + 30)),$ry,24,26" "$((ox + 30)),$oy,24,26"
}
field_check spin 846 346 160 928
field_check spin-focused 846 432 230 928

# Group box ("Desktop" in General Controls, frame 538,259 to 863,367): the
# left 12 columns (to the title gap; its check boxes start at 13), the top
# lines right of the title, the right 8 columns and the bottom 2 rows. The
# title itself isn't compared.
check groupbox-left controls-general-controls.png@538,259,12,109 10,1000,12,109
check groupbox-top-right controls-general-controls.png@620,259,244,2 92,1000,244,2
check groupbox-right controls-general-controls.png@856,259,8,109 328,1000,8,109
check groupbox-bottom controls-general-controls.png@538,366,326,2 10,1107,326,2
# Finder list header: sorted "Name" (105,154, 238x21) and "Date Modified"
# (343,154, 149x21), outside their labels (3 px bands).
section_check() { # name rx ry ox oy W
    local n=$1 rx=$2 ry=$3 ox=$4 oy=$5 W=$6
    check "$n-top" "disclosure-triangles.png@$rx,$ry,$W,3" "$ox,$oy,$W,3"
    check "$n-bottom" "disclosure-triangles.png@$rx,$((ry + 18)),$W,3" "$ox,$((oy + 18)),$W,3"
    check "$n-left" "disclosure-triangles.png@$rx,$ry,3,21" "$ox,$oy,3,21"
    check "$n-right" "disclosure-triangles.png@$((rx + W - 3)),$ry,3,21" "$((ox + W - 3)),$oy,3,21"
}
section_check header-sorted 105 154 360 1000 238
section_check header-normal 343 154 598 1000 149
check triangle-closed disclosure-triangles.png@108,194,17,17 360,1040,17,17
check triangle-open disclosure-triangles.png@108,270,17,17 390,1040,17,17
check separator appearance-3-fonts-clean.png@600,400,100,4 360,1080,100,4

# Bevel buttons outside their icons: large (controls-monitors.png, 38x40,
# 3 px bands; its icons reach the 4th column) normal and selected, small
# (help-viewer.png, 25x25, 3 px bands).
bevel_check() { # name ref.png rx ry ox oy W H
    local n=$1 img=$2 rx=$3 ry=$4 ox=$5 oy=$6 W=$7 H=$8
    check "$n-top" "$img@$rx,$ry,$W,3" "$ox,$oy,$W,3"
    check "$n-bottom" "$img@$rx,$((ry + H - 3)),$W,3" "$ox,$((oy + H - 3)),$W,3"
    check "$n-left" "$img@$rx,$ry,3,$H" "$ox,$oy,3,$H"
    check "$n-right" "$img@$((rx + W - 3)),$ry,3,$H" "$((ox + W - 3)),$oy,3,$H"
}
bevel_check bevel-large controls-monitors.png 855 315 10 1130 38 40
bevel_check bevel-large-selected controls-monitors.png 800 315 60 1130 38 40
bevel_check bevel-small help-viewer.png 14 50 110 1130 25 25

# Tooltip balloon: its outline by pixel class (black / white / outside),
# since the capture's desktop shows around it. A 10 px band around the
# edge (the text starts 12 px in), without the tail's corner (top right).
total=$((total + 1))
if result=$(python3 -I - "reference/help-balloon.png" "$shot" << 'EOF'
import sys
from PIL import Image
ref = Image.open(sys.argv[1]).convert("RGB")
ours = Image.open(sys.argv[2]).convert("RGB")
cls = lambda p: "B" if p == (0, 0, 0) else "W" if p == (255, 255, 255) else "-"
n = bad = 0
for y in range(121):
    for x in range(160):
        if not (x < 10 or y < 10 or x >= 150 or y >= 111) or (x >= 130 and y < 14):
            continue
        n += 1
        bad += cls(ref.getpixel((1690 + x, 149 + y))) != cls(ours.getpixel((500 + x, 1060 + y)))
print(f"{bad} of {n}")
sys.exit(1 if bad else 0)
EOF
); then
    printf 'ok      %-30s %s\n' balloon-outline "$result"
else
    printf 'DIFF    %-30s %s\n' balloon-outline "$result"
    failed=$((failed + 1))
fi

echo "$((total - failed)) of $total regions pixel exact"

# Real widget regressions for states outside the reference captures.
# shellcheck disable=SC2046
g++ -std=c++17 -O1 -fPIC dev/widget-states.cpp -o dev/build/widget-states $(pkg-config --cflags --libs Qt6Widgets Qt6Test)
QSTYLE=Platinum dev/run.sh platinum breeze dev/build/widget-states || failed=$((failed + 1))
exit $((failed > 0))
