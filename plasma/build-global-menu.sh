#!/bin/bash
# Configure or build the applet without using upstream's system installer.
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
out=$1
if [[ ${2:-} != --build-configured ]]; then
    cmake -S "$here/globalmenu" -B "$out/build" -G Ninja \
        -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DCMAKE_INSTALL_PREFIX=/usr
    [[ ${2:-} != --configure-only ]] || exit 0
fi
cmake --build "$out/build" --target platinum.globalmenu --parallel "${CMAKE_BUILD_PARALLEL_LEVEL:-4}"
install -D -m 755 "$out/build/bin/plasma/applets/platinum.globalmenu.so" "$out/plugins/plasma/applets/platinum.globalmenu.so"
msgfmt --check -o "$out/plasma_applet_platinum.globalmenu.mo" \
    "$here/globalmenu/po/fr/plasma_applet_platinum.globalmenu.po"
