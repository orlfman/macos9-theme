#!/bin/bash
# Installs the Platinum theme for KDE Plasma 6.8 for the current user, all
# inside your home (no root):
#   - the Platinum application style (a Qt style plugin, built here)
#   - the Platinum window decoration (a KWin plugin, built here)
#   - a Plasma login script that lets Qt find those two
#     (~/.config/plasma-workspace/env/macos9-theme.sh)
#   - the Platinum color scheme, Plasma style, menu bar piece widget and the
#     Platinum global theme (menu bar on top, dock at the bottom)
# Run it again to update. Nothing is switched to unless you ask (--apply),
# and uninstall.sh removes everything this installed.
#
# usage: install.sh [--apply] [--dry-run]
#   --apply    also switch to the theme: applies the Platinum global theme
#              (replaces your panels with the menu bar and the dock) and
#              sets the title bar buttons to close-left, zoom and collapse
#              right. Your config files are copied first, so uninstall.sh
#              puts them back exactly.
#   --dry-run  only show what would be done
#   -h, --help show this help
#
# The style and the decoration only load after you log out and back in once
# (the login script has to run). Installing, logging in again, then running
# install.sh --apply gives the cleanest switch.
#
# SPDX-License-Identifier: BSD-2-Clause
set -euo pipefail
umask 022
program=install.sh
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
# shellcheck source=scripts/common.sh
source "$here/scripts/common.sh"

usage() {
    sed -n '/^# usage:/,/^# *-h, --help/s/^# \{0,1\}//p' "$0"
}

apply=0
for arg in "$@"; do
    case $arg in
        --apply) apply=1 ;;
        --dry-run) dry_run=1 ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

refuse_root
need g++ pkg-config install
if ((apply)); then
    need plasma-apply-lookandfeel kwriteconfig6
fi

((dry_run)) && note "Dry run: nothing is changed."
manifest_load

# Build the two plugins in a temporary folder.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if ((dry_run)); then
    run "$here/style/build.sh" "$tmp/style"
    run "$here/decoration/build.sh" "$tmp/decoration"
else
    "$here/style/build.sh" "$tmp/style" > /dev/null || die "building the application style failed (needs Qt 6 development files)"
    "$here/decoration/build.sh" "$tmp/decoration" > /dev/null || die "building the window decoration failed (needs KDecoration 3 development files)"
fi
run install -Dm755 "$tmp/style/plugins/styles/platinumstyle.so" "$plugins/styles/platinumstyle.so"
manifest_add file "$plugins/styles/platinumstyle.so"
run install -Dm755 "$tmp/decoration/plugins/org.kde.kdecoration3/platinum.so" "$plugins/org.kde.kdecoration3/platinum.so"
manifest_add file "$plugins/org.kde.kdecoration3/platinum.so"
say "Installed the application style and the window decoration into $plugins"

# The login script: Qt looks for plugins in $plugins too. Plasma runs every
# script in plasma-workspace/env at login.
if ((dry_run)); then
    run install -Dm644 /dev/stdin "$env_script"
else
    mkdir -p "$(dirname "$env_script")"
    cat > "$env_script.new" << EOF
# Added by macos9-theme's install.sh; uninstall.sh removes it.
# Lets Qt (apps and KWin) find the Platinum style and window decoration.
case ":\${QT_PLUGIN_PATH:-}:" in
    *":$plugins:"*) ;;
    *) export QT_PLUGIN_PATH="$plugins\${QT_PLUGIN_PATH:+:\$QT_PLUGIN_PATH}" ;;
esac
EOF
    mv -f "$env_script.new" "$env_script"
fi
manifest_add file "$env_script"
say "Installed the login script $env_script"

run install -Dm644 "$here/colors/$scheme_name.colors" "$data/color-schemes/$scheme_name.colors"
manifest_add file "$data/color-schemes/$scheme_name.colors"
say "Installed the color scheme \"Platinum\""

install_dir "$here/plasma/platinum" "$data/plasma/desktoptheme/$plasma_theme"
manifest_add dir "$data/plasma/desktoptheme/$plasma_theme"
drop_plasma_caches
say "Installed the Plasma style \"Platinum\""

install_dir "$here/plasma/plasmoids/$piece_id" "$data/plasma/plasmoids/$piece_id"
manifest_add dir "$data/plasma/plasmoids/$piece_id"
install_dir "$here/plasma/look-and-feel/$lnf_id" "$data/plasma/look-and-feel/$lnf_id"
manifest_add dir "$data/plasma/look-and-feel/$lnf_id"
say "Installed the global theme \"Platinum\" and its menu bar widget"

manifest_save

if ((apply)); then
    # Copy the config files the switch changes, once: a second --apply
    # mustn't keep our own settings as "before".
    if [[ ! -d $backup ]]; then
        if ((dry_run)); then
            say "  would copy your config files to $backup"
        else
            mkdir -p "$backup.new"
            : > "$backup.new/ABSENT"
            for file in "${backup_files[@]}" "${backup_dirs[@]}"; do
                if [[ -e $config_home/$file ]]; then
                    cp -a "$config_home/$file" "$backup.new/$file"
                else
                    printf '%s\n' "$file" >> "$backup.new/ABSENT"
                fi
            done
            mv "$backup.new" "$backup"
            say "Copied your current config files to $backup"
        fi
    fi

    # The global theme only sets a widget style Qt can find, and the login
    # script hasn't run yet on a first install: give it the plugin folder.
    if run_quiet env QT_PLUGIN_PATH="$plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}" \
        plasma-apply-lookandfeel --apply "$lnf_id" --resetLayout; then
        say "Switched to the Platinum global theme"
    else
        warn "plasma-apply-lookandfeel failed; pick \"Platinum\" in System Settings > Global Theme instead (your config files are copied already)"
    fi
    # A global theme can't set the title bar button order (docs/FINDINGS.md).
    run kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft X
    run kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight AI
    reconfigure_kwin
    notify_style
    say "Set the title bar buttons: close on the left, zoom and collapse on the right"
    case ":${QT_PLUGIN_PATH:-}:" in
        *":$plugins:"*) ;;
        *) note "Log out and back in once: the application style and the window decoration load from then on." ;;
    esac
fi

if ((dry_run)); then
    note "Dry run done."
elif ((!apply)); then
    say "Done. Log out and back in once, then pick \"Platinum\" in System Settings > Global Theme, or run install.sh --apply."
else
    say "Done. uninstall.sh puts your previous setup back."
fi
