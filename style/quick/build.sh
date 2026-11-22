#!/bin/bash
# Builds the Platinum Qt Quick Controls style (QML files and its C++ item)
# into OUT/qml/Platinum, and links Kirigami's color and size plugin for it
# (OUT/plugins/kf6/kirigami/platform/Platinum.so -> KDE's, which Kirigami
# looks up by the style's name). With QML_IMPORT_PATH=OUT/qml,
# QT_PLUGIN_PATH=OUT/plugins and QT_QUICK_CONTROLS_STYLE=Platinum, Qt Quick
# apps use it without installing (dev/run.sh does that with M9_QUICK=1).
#   usage: build.sh [OUT]   (default: style/build)
# CXXFLAGS and LDFLAGS from the environment are used when set.
set -euo pipefail
src=$(dirname "$(readlink -f "$0")")
out=${1:-$(dirname "$src")/build}
module=$out/qml/Platinum
mkdir -p "$out/moc-quick" "$module" "$out/plugins/kf6/kirigami/platform"

moc=$(pkg-config --variable=libexecdir Qt6Core)/moc
# shellcheck disable=SC2207
flags=($(pkg-config --cflags Qt6Widgets Qt6Quick Qt6Qml))
"$moc" "${flags[@]}" "$src/platinumitem.h" -o "$out/moc-quick/moc_platinumitem.cpp"
"$moc" "${flags[@]}" -I"$src" "$src/platinumitem.cpp" -o "$out/moc-quick/platinumitem.moc"

# shellcheck disable=SC2086,SC2046
g++ -std=c++20 ${CXXFLAGS:--O2} -fPIC -shared -Wall -Wextra \
    "${flags[@]}" -I"$src" -I"$out/moc-quick" \
    "$src/platinumitem.cpp" "$out/moc-quick/moc_platinumitem.cpp" \
    -o "$module/libplatinumquick.so" \
    ${LDFLAGS:-} $(pkg-config --libs Qt6Widgets Qt6Quick Qt6Qml)
cp "$src"/Platinum/qmldir "$src"/Platinum/*.qml "$module/"

kirigami=$(pkg-config --variable=libdir Qt6Core)/qt6/plugins/kf6/kirigami/platform/org.kde.desktop.so
[[ -e $kirigami ]] || kirigami=/usr/lib/qt6/plugins/kf6/kirigami/platform/org.kde.desktop.so
ln -sfn "$kirigami" "$out/plugins/kf6/kirigami/platform/Platinum.so"

echo "Built $module"
