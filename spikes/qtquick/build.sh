#!/bin/bash
# Builds the spike's QML plugin into Platinum/ (next to its qmldir).
set -euo pipefail
here=$(dirname "$(readlink -f "$0")")
cd "$here"
flags=$(pkg-config --cflags Qt6Widgets Qt6Quick Qt6Qml)
# shellcheck disable=SC2086
/usr/lib/qt6/moc $flags platinumitem.h -o moc_platinumitem.cpp
# shellcheck disable=SC2086
/usr/lib/qt6/moc $flags platinumitem.cpp -o platinumitem.moc
# shellcheck disable=SC2086
g++ -std=c++17 -O1 -g -fPIC -shared platinumitem.cpp moc_platinumitem.cpp -o Platinum/libplatinumquickspike.so \
    $flags $(pkg-config --libs Qt6Widgets Qt6Quick Qt6Qml) -Wall -Wextra
echo "built $here/Platinum/libplatinumquickspike.so"
