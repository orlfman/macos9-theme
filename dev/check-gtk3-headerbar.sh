#!/bin/bash
# GTK 3 header bar stripe gaps with Lutris-like app widgets (#261) and the
# popover menu (#262), notebook tab scroll arrows (#263) and spin buttons
# (#267), in a disposable HOME and Broadway display.
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
dev=$(dirname "$(realpath "$0")")
project=$(dirname "$dev")
mkdir -p "$dev/build"
root=$(mktemp -d "$dev/build/gtk3-headerbar.XXXXXX")
runtime=$(mktemp -d)
chmod 700 "$runtime"
trap 'kill "${broadway:-}" 2> /dev/null || true; rm -rf "$runtime"' EXIT
mkdir -p "$root/home/.local/share/themes" "$root/home/.config"
cp -R "$project/gtk/Platinum" "$root/home/.local/share/themes/"
export HOME=$root/home XDG_CONFIG_HOME=$root/home/.config XDG_DATA_HOME=$root/home/.local/share \
    XDG_RUNTIME_DIR=$runtime GDK_BACKEND=broadway BROADWAY_DISPLAY=:8 GTK_A11Y=none NO_AT_BRIDGE=1
broadwayd :8 > "$root/broadway.log" 2>&1 &
broadway=$!
for _ in {1..40}; do [[ -S $runtime/broadway9.socket ]] && break; sleep 0.05; done
rc=0
timeout 60 python3 -I "$dev/gtk3-headerbar-gaps.py" "$root/headerbar.png" 2> "$root/stderr.log" | tee "$root/verdict.log" || rc=1
timeout 60 python3 -I "$dev/gtk3-popover-menu.py" "$root/popover.png" 2>> "$root/stderr.log" | tee -a "$root/verdict.log" || rc=1
timeout 60 python3 -I "$dev/gtk3-notebook-arrows.py" "$root/notebook.png" "$root/home/.local/share/themes/Platinum" \
    2>> "$root/stderr.log" | tee -a "$root/verdict.log" || rc=1
timeout 60 python3 -I "$dev/gtk3-spinbutton.py" "$root/spin.png" "$root/home/.local/share/themes/Platinum" \
    2>> "$root/stderr.log" | tee -a "$root/verdict.log" || rc=1
exit "$rc"
