#!/bin/bash
# Builds the Platinum Qt style plugin with moc and g++ (no CMake needed).
# It lands in OUT/plugins/styles/platinumstyle.so, so QT_PLUGIN_PATH=OUT/plugins
# and QT_STYLE_OVERRIDE=Platinum use it without installing (dev/run.sh does
# that with QSTYLE=Platinum).
#   usage: build.sh [OUT]   (default: style/build)
# CXXFLAGS and LDFLAGS from the environment are used when set (makepkg).
set -euo pipefail
src=$(dirname "$(readlink -f "$0")")/platinum
out=${1:-$(dirname "$src")/build}
mkdir -p "$out/moc" "$out/plugins/styles"

moc=$(pkg-config --variable=libexecdir Qt6Core)/moc
# shellcheck disable=SC2207
flags=($(pkg-config --cflags Qt6Widgets))
"$moc" "${flags[@]}" "$src/platinumstyle.h" -o "$out/moc/moc_platinumstyle.cpp"
"$moc" "${flags[@]}" -I"$src" "$src/plugin.cpp" -o "$out/moc/plugin.moc"

# shellcheck disable=SC2086,SC2046
g++ -std=c++20 ${CXXFLAGS:--O2} -fPIC -shared -Wall -Wextra \
    "${flags[@]}" -I"$src" -I"$out/moc" \
    "$src/platinumstyle.cpp" "$src/plugin.cpp" "$out/moc/moc_platinumstyle.cpp" \
    -o "$out/plugins/styles/platinumstyle.so" \
    ${LDFLAGS:-} $(pkg-config --libs Qt6Widgets)

echo "Built $out/plugins/styles/platinumstyle.so"
