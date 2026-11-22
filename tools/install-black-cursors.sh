#!/bin/bash
# Installs the optional black cursors (Apple Cursor v2.0.1's black "macOS"
# folder, from https://github.com/ful1e5/apple_cursor/releases/tag/v2.0.1)
# as the cursor theme macOS-cursors in ~/.icons, without touching anything
# already there (AUDIT.md finding 78): it unpacks into a temporary folder,
# checks the pointer file, and only then moves it into place. If
# ~/.icons/macOS-cursors already exists, it stops and changes nothing.
#
# usage: tools/install-black-cursors.sh macOS.tar.xz
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
program=install-black-cursors.sh
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
# shellcheck source=../scripts/common.sh
source "$here/scripts/common.sh"
refuse_root
[[ $# -eq 1 && -f $1 ]] || die "usage: tools/install-black-cursors.sh macOS.tar.xz"
need tar od stat

dest=$home/.icons/$black_cursor_id
[[ ! -e $dest && ! -L $dest ]] || die "$dest already exists; nothing was changed. Move it away first if you want it replaced."
mkdir -p "$home/.icons"
tmp=$(mktemp -d "$home/.icons/.macos9-theme-cursors.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
tar -xJf "$1" -C "$tmp" ./macOS 2> /dev/null || tar -xJf "$1" -C "$tmp" macOS ||
    die "$1 has no macOS folder (expected Apple Cursor v2.0.1's macOS.tar.xz); nothing was changed"
[[ -f $tmp/macOS/index.theme ]] && xcursor_ok "$tmp/macOS/cursors/left_ptr" ||
    die "the macOS folder in $1 isn't a usable cursor theme; nothing was changed"
mv -T "$tmp/macOS" "$dest"
echo "Installed the black cursors as $dest (theme ID $black_cursor_id)."
