#!/bin/bash
# Milestone 6 verification suite for firefox/install.sh and firefox/uninstall.sh.
# Runs entirely in throwaway HOME / XDG directories under dev/build/ (plus one
# isolated nested kwin_wayland --virtual smoke test of a real installed profile),
# never touching the user's real ~/.mozilla, ~/.config/mozilla, or ~/.local/state.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
work=$(mktemp -d "$repo_root/dev/build/firefox-m6.XXXXXX")
echo "Firefox Milestone 6 evidence: $work"

python3 -I "$repo_root/dev/firefox-m6/test_suite.py" "$repo_root" "$work"
