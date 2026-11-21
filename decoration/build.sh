#!/bin/bash
# Builds the Platinum window decoration with moc and g++ (no CMake needed).
# Adapted from the user's windows2000-union project (BSD-2-Clause).
# The plugin lands in OUT/plugins/org.kde.kdecoration3/platinum.so, so
# QT_PLUGIN_PATH=OUT/plugins lets the test harness find it without installing.
#   usage: build.sh [OUT]   (default: decoration/build)
# CXXFLAGS and LDFLAGS from the environment are used when set (makepkg).
set -euo pipefail
src=$(dirname "$(readlink -f "$0")")
out=${1:-$src/build}
mkdir -p "$out/moc" "$out/plugins/org.kde.kdecoration3"

moc=$(pkg-config --variable=libexecdir Qt6Core)/moc
# pkg-config output is meant to be word split here.
# shellcheck disable=SC2207
flags=($(pkg-config --cflags Qt6Gui KF6CoreAddons) -I/usr/include/KDecoration3)
"$moc" "${flags[@]}" "$src/platinum.h" -o "$out/moc/moc_platinum.cpp"
"$moc" "${flags[@]}" "$src/platinum.cpp" -o "$out/moc/platinum.moc"

# shellcheck disable=SC2086,SC2046
g++ -std=c++20 ${CXXFLAGS:--O2} -fPIC -shared -Wall -Wextra \
    "${flags[@]}" -I"$out/moc" \
    "$src/platinum.cpp" "$out/moc/moc_platinum.cpp" \
    -o "$out/plugins/org.kde.kdecoration3/platinum.so" \
    ${LDFLAGS:-} $(pkg-config --libs Qt6Gui KF6CoreAddons) -lkdecorations3

echo "Built $out/plugins/org.kde.kdecoration3/platinum.so"
