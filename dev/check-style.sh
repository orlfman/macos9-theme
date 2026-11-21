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
QSTYLE=Platinum dev/run.sh platinum breeze dev/build/styleshot "$shot" > /dev/null 2>&1

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

echo "$((total - failed)) of $total regions pixel exact"
exit $((failed > 0))
