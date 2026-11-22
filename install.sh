#!/bin/bash
# Installs the Platinum theme for KDE Plasma 6.8 for the current user, all
# inside your home (no root):
#   - the Platinum application style and window decoration (Qt and KWin
#     plugins, built here) in ~/.local/lib/macos9-theme, and the Platinum
#     style for Qt Quick apps (menus, tooltips, switches; KDE's style for
#     the rest) next to them
#   - a Plasma login script that lets Qt and KWin find them
#     (~/.config/plasma-workspace/env/macos9-theme.sh)
#   - the Platinum color scheme, Plasma style, menu bar piece widget and the
#     Platinum global theme (menu bar, dock, and wallpaper)
# Run it again to update. Nothing is switched to unless you ask (--apply),
# and uninstall.sh removes everything this installed and puts back anything
# it moved aside.
#
# usage: install.sh [--apply] [--dry-run]
#   --apply    also switch to the theme: applies the Platinum global theme
#              (replaces your panels, selects the wallpaper and the
#              cursors) and
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

usage() {
    sed -n '/^# usage:/,/^# *-h, --help/s/^# \{0,1\}//p' "$0"
}

apply=0
dry=0
for arg in "$@"; do
    case $arg in
        --apply) apply=1 ;;
        --dry-run) dry=1 ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

# shellcheck source=scripts/common.sh
source "$here/scripts/common.sh"
dry_run=$dry

refuse_root
need g++ pkg-config install ldd readlink mktemp tar od stat
if ((apply)); then
    need plasma-apply-lookandfeel kwriteconfig6
fi


for wallpaper_id in "${wallpaper_ids[@]}"; do
    wallpaper_source=$here/wallpapers/$wallpaper_id
    [[ -r $wallpaper_source/metadata.json && -r $wallpaper_source/contents/images/3840x2160.jxl ]] ||
        die "couldn't find the Platinum wallpaper package in $wallpaper_source"
done

((dry_run)) && note "Dry run: nothing is changed."
# Everything that could stop the install halfway is checked first.
check_target_parents
check_backup_links
take_lock
manifest_load
check_record_paths
remove_temporaries

# Build the two plugins in a temporary folder before installing anything.
if ((dry_run)); then
    build=/nonexistent
    plan "build the application style and the window decoration"
else
    build=$(mktemp -d)
    trap 'rm -rf "${build:-/nonexistent}"' EXIT
    if [[ -n ${M9_PREBUILT:-} ]]; then # tests only: dev/test-install.sh builds once
        cp -R "$M9_PREBUILT/style" "$M9_PREBUILT/decoration" "$M9_PREBUILT/quick" "$build/"
    else
        "$here/style/build.sh" "$build/style" > /dev/null || die "building the application style failed (needs Qt 6 development files); nothing was installed"
        "$here/decoration/build.sh" "$build/decoration" > /dev/null || die "building the window decoration failed (needs KDecoration 3 development files); nothing was installed"
        "$here/style/quick/build.sh" "$build/quick" > /dev/null || die "building the Qt Quick style failed (needs Qt 6 Quick development files); nothing was installed"
    fi
fi

# The Qt Quick style builds on KDE's (qqc2-desktop-style) and needs
# Kirigami's plugin for it; it's left out if they aren't there.
find_kde_quick
kde_quick_version=""
if [[ -n $kde_quick_version_file && -n $kirigami_desktop ]]; then
    kde_quick_version=$(< "$kde_quick_version_file")
else
    note "KDE's Qt Quick style or Kirigami isn't installed: Qt Quick apps keep KDE's look."
fi

# The login script. The decoration is only put on the path while the
# KDecoration libraries are the ones it was built against: after a Plasma
# upgrade KWin uses Breeze's decoration until install.sh is run again,
# instead of loading a plugin built for another version.
guard=""
if ((!dry_run)); then
    while read -r lib; do
        [[ -n $lib ]] || continue
        guard+=" && [ \"\$(readlink -f $(sh_quote "$lib") 2> /dev/null)\" = $(sh_quote "$(readlink -f "$lib")") ]"
    done < <(ldd "$build/decoration/plugins/org.kde.kdecoration3/platinum.so" | awk '/libkdecorations3/ { print $3 }')
    [[ -n $guard ]] || die "couldn't find the KDecoration libraries the window decoration uses"
    cat > "$build/env.sh" << EOF
# Added by macos9-theme's install.sh; uninstall.sh removes it.
# Lets Qt find the Platinum application style, and KWin the window
# decoration while KDecoration is the version it was built against (after
# a Plasma upgrade, run install.sh again to rebuild it).
macos9_theme_path=$(sh_quote "$plugins")
if true$guard; then
    macos9_theme_path=\$macos9_theme_path:$(sh_quote "$deco_plugins")
fi
case ":\${QT_PLUGIN_PATH:-}:" in
    *":\$macos9_theme_path:"*) ;;
    *) export QT_PLUGIN_PATH="\$macos9_theme_path\${QT_PLUGIN_PATH:+:\$QT_PLUGIN_PATH}" ;;
esac
unset macos9_theme_path
EOF
    if [[ -n $kde_quick_version ]]; then
        cat >> "$build/env.sh" << EOF

# Qt Quick apps: the Platinum Qt Quick style, only while Platinum is the
# application style chosen in System Settings, you haven't chosen a Qt
# Quick style yourself, and KDE's Qt Quick style (which it builds on) is
# the version it was checked with. Each app also falls back to KDE's look
# by itself if its style changes later.
macos9_theme_style() {
    awk -F= '/^\[/ { kde = (\$0 == "[KDE]") } kde && \$1 == "widgetStyle" { v = substr(\$0, index(\$0, "=") + 1) } END { print v }' "\$1" 2> /dev/null
}
macos9_theme_config=\${XDG_CONFIG_HOME:-\$HOME/.config}
macos9_theme_widget_style=\$(macos9_theme_style "\$macos9_theme_config/kdeglobals")
[ -n "\$macos9_theme_widget_style" ] || macos9_theme_widget_style=\$(macos9_theme_style "\$macos9_theme_config/kdedefaults/kdeglobals")
if [ -z "\${QT_QUICK_CONTROLS_STYLE:-}" ] && [ "\$macos9_theme_widget_style" = Platinum ] &&
    [ "\$(cat $(sh_quote "$kde_quick_version_file") 2> /dev/null)" = $(sh_quote "$kde_quick_version") ]; then
    export QT_QUICK_CONTROLS_STYLE=Platinum
    case ":\${QML_IMPORT_PATH:-}:" in
        *:$(sh_quote "$quick_qml"):*) ;;
        *) export QML_IMPORT_PATH=$(sh_quote "$quick_qml")"\${QML_IMPORT_PATH:+:\$QML_IMPORT_PATH}" ;;
    esac
fi
unset -f macos9_theme_style
unset macos9_theme_config macos9_theme_widget_style
EOF
    fi
fi

# What an uninstall in this session left for running apps makes way.
remove_passthrough
place_file "$build/style/plugins/styles/platinumstyle.so" "$plugins/styles/platinumstyle.so" 755
place_file "$build/decoration/plugins/org.kde.kdecoration3/platinum.so" "$deco_plugins/org.kde.kdecoration3/platinum.so" 755
say "Installed the application style and the window decoration into $libdir"
place_file "$build/env.sh" "$env_script" 644
say "Installed the login script $env_script"
if [[ -n $kde_quick_version ]]; then
    place_dir "$build/quick/qml/Platinum" "$quick_module"
    place_link "$kirigami_desktop" "$kirigami_link"
    say "Installed the Qt Quick style into $quick_qml"
fi
# The cursors (cursors/README.md): unpacked from the archive, checked,
# installed as a theme folder; the global theme selects them.
if ((!dry_run)); then
    mkdir -p "$build/cursors"
    tar -xJf "$here/cursors/macOS-cursors.tar.xz" -C "$build/cursors" macOS-cursors ||
        die "couldn't unpack cursors/macOS-cursors.tar.xz; nothing more was installed"
    xcursor_ok "$build/cursors/macOS-cursors/cursors/left_ptr" ||
        die "cursors/macOS-cursors.tar.xz holds no usable cursor theme; nothing more was installed"
fi
place_dir "$build/cursors/macOS-cursors" "$cursor_theme_dir"
say "Installed the cursors into $cursor_theme_dir"
place_file "$here/colors/$scheme_name.colors" "$data/color-schemes/$scheme_name.colors" 644
say "Installed the color scheme \"Platinum\""
place_dir "$here/plasma/platinum" "$data/plasma/desktoptheme/$plasma_theme"
drop_plasma_caches
say "Installed the Plasma style \"Platinum\""
place_dir "$here/plasma/plasmoids/$piece_id" "$data/plasma/plasmoids/$piece_id"
for wallpaper_id in "${wallpaper_ids[@]}"; do
    place_dir "$here/wallpapers/$wallpaper_id" "$data/wallpapers/$wallpaper_id"
done
say "Installed the Platinum wallpapers"
place_dir "$here/plasma/look-and-feel/$lnf_id" "$data/plasma/look-and-feel/$lnf_id"
say "Installed the global theme \"Platinum\" and its menu bar widget"

# The copy of your config files from before the switch. It's taken now
# already, so uninstall.sh can put things back even if you switch in System
# Settings instead of with --apply. Until the switch it's refreshed on every
# run; after it, it's never replaced.
active=$(active_lnf)
taken=$(backup_taken || true)
if [[ $taken == apply ]]; then
    :
elif [[ $active == "$lnf_id" ]]; then
    if [[ $taken == install ]]; then
        mark_backup apply # switched in System Settings since the install
    else
        # Selected before this install (finding 28): copy the settings as
        # they are now, so at least what this run changes can be undone.
        warn "Platinum is already the global theme and there's no copy of your settings from before it. Copying them as they are now: uninstall.sh puts back this state (with its panels and title bar buttons), not what you had before Platinum"
        take_backup apply
    fi
elif ((apply)); then
    take_backup apply
else
    take_backup install
fi

if ((apply)); then
    # The global theme only sets a widget style Qt can find, and the login
    # script hasn't run yet on a first install: give it the plugin folders.
    plan "check whether Qt can read the Platinum wallpapers"
    if ((!dry_run)); then
        wallpaper_images=()
        for wallpaper_id in "${wallpaper_ids[@]}"; do
            wallpaper_images+=("$data/wallpapers/$wallpaper_id/contents/images/3840x2160.jxl")
        done
        # Use the Qt image loader rather than the presence of a plugin file.
        # shellcheck disable=SC2046
        if ! g++ -std=c++17 -fPIC "$here/tools/check-wallpaper.cpp" -o "$build/check-wallpaper" \
                $(pkg-config --cflags --libs Qt6Gui) > /dev/null 2>&1; then
            warn "couldn't check Qt's JPEG XL support for the wallpapers"
        elif ! "$build/check-wallpaper" "${wallpaper_images[@]}"; then
            warn "Qt can't read the JPEG XL wallpapers. Install your distribution's Qt JPEG XL support (kimageformats on Arch) to display them."
        fi
    fi
    plan "run plasma-apply-lookandfeel --apply $lnf_id --resetLayout"
    if ((!dry_run)); then
        if ! env QT_PLUGIN_PATH="$plugins:$deco_plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}" \
            plasma-apply-lookandfeel --apply "$lnf_id" --resetLayout > /dev/null 2>&1; then
            die "switching to the Platinum global theme failed (plasma-apply-lookandfeel). Your config files are copied: uninstall.sh puts them back, or try install.sh --apply again"
        fi
        say "Switched to the Platinum global theme"
    fi
    # A global theme can't set the title bar button order (docs/FINDINGS.md).
    plan "set the title bar buttons in kwinrc: close on the left, zoom and collapse on the right"
    if ((!dry_run)); then
        kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft X
        kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight AI
    fi
    reconfigure_kwin
    notify_style
    say "Set the title bar buttons: close on the left, zoom and collapse on the right"
    case ":${QT_PLUGIN_PATH:-}:" in
        *":$plugins:"*)
            if [[ -n $kde_quick_version && -z ${QT_QUICK_CONTROLS_STYLE:-} ]]; then
                note "Log out and back in for Qt Quick apps to use the Platinum controls."
            fi
            ;;
        *) note "Log out and back in once: the application style and the window decoration load from then on." ;;
    esac
fi

if ((dry_run)); then
    note "Dry run done."
elif ((!apply)); then
    say "Done. Log out and back in once, then run install.sh --apply to switch."
else
    say "Done. uninstall.sh puts your previous setup back."
fi
