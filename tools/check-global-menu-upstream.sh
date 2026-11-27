#!/bin/bash
# Report upstream changes without changing the theme checkout.
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
upstream=${M9_GLOBAL_MENU_UPSTREAM:-https://github.com/ChathurangaBW/global-menu-KDE.git}
if [[ -d $upstream ]]; then
    upstream=$(realpath -- "$upstream")
fi
pin=$(< "$here/plasma/globalmenu-upstream")
[[ $pin =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid global menu upstream pin" >&2; exit 1; }
latest=$(git ls-remote --exit-code "$upstream" HEAD | awk '$2 == "HEAD" {print $1}')
[[ $latest =~ ^[0-9a-f]{40}$ ]] || { echo "Couldn't read upstream HEAD" >&2; exit 1; }
printf 'Platinum pin: %s\nUpstream HEAD: %s\n' "$pin" "$latest"
if [[ $latest == "$pin" ]]; then
    echo "The bundled global menu is up to date."
    exit 0
fi

review=$(mktemp -d)
trap 'rm -rf -- "$review"' EXIT
git init --bare --quiet "$review"
git -C "$review" fetch --quiet --no-tags --update-shallow "$upstream" "$latest" "$pin"
if ! git -C "$review" merge-base --is-ancestor "$pin" "$latest"; then
    echo "Upstream no longer descends from the bundled pin. Review its history before updating." >&2
    exit 1
fi
git -C "$review" log --oneline "$pin..$latest"
