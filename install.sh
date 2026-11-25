#!/bin/bash
# Installs the Platinum theme for KDE Plasma 6.8 for the current user, all
# inside your home (no root):
#   - the Platinum application style and window decoration (Qt and KWin
#     plugins, built here) in ~/.local/lib/macos9-theme, and the Platinum
#     style for Qt Quick apps (menus, tooltips, switches; KDE's style for
#     the rest) next to them
#   - a Plasma login script that lets Qt and KWin find them
#     (~/.config/plasma-workspace/env/macos9-theme.sh)
#   - the Platinum color scheme, Plasma style, menu bar piece widget,
#     the Platinum Lavender terminal palette for Kwi and Konsole,
#     WhiteSur Lavender icon themes, bundled cursors, and the Platinum
#     global theme (menu bar, dock, and wallpaper), and the named GTK 3 theme
# Run it again to update. When Platinum is not your active global theme,
# nothing is switched to unless you ask (--apply). When Platinum is already
# your active global theme, a plain install also selects WhiteSur-lavender
# once for both KDE and GTK (recording your prior KDE and GTK icon settings
# first without changing panels, wallpaper, cursors, or other settings; later
# updates preserve any icon theme you pick afterwards). uninstall.sh removes
# everything this installed and puts back anything it moved aside.
#
# usage: install.sh [--apply] [--dry-run]
#        install.sh --firefox [--profile PROFILE] [--list] [--dry-run]
#   --firefox  choose Firefox-only mode first, then pass Firefox options
#   (default)  install or update all theme files. If Platinum is already the
#              active global theme, also selects WhiteSur-lavender icons once
#              for KDE and GTK without touching panels, wallpaper, cursors, or
#              other settings; otherwise leaves your active settings alone.
#   --apply    also switch to the theme: applies the Platinum global theme
#              (replaces your panels, selects the wallpaper, cursors, and
#              WhiteSur-lavender icons) and sets the title bar buttons to
#              close-left, zoom and collapse right. Your config files are
#              copied first, so uninstall.sh puts them back exactly.
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

if [[ ${1:-} == --firefox ]]; then
    shift
    exec "$here/firefox/install.sh" "$@"
fi

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
need_pkg \
    g++:gcc pkg-config:pkgconf install:coreutils ldd:glibc readlink:coreutils \
    mktemp:coreutils tar:tar sha256sum:coreutils python3:python \
    flock:util-linux kreadconfig6:kconfig kwriteconfig6:kconfig
if ((apply)); then
    need_pkg plasma-apply-lookandfeel:plasma-workspace
fi

# Preflight Qt 6, KF6CoreAddons, moc, and KDecoration 3 development files
# before fetching, locking, or writing anything (#136).
preflight_plugin_build() {
    local missing=() moc_bin
    if ! pkg-config --exists Qt6Core Qt6Gui Qt6Widgets 2> /dev/null; then
        missing+=("Qt6Core/Qt6Gui/Qt6Widgets pkg-config modules (Arch package: qt6-base)")
    else
        moc_bin=$(pkg-config --variable=libexecdir Qt6Core 2> /dev/null)/moc
        [[ -x $moc_bin ]] || missing+=("Qt 6 moc (${moc_bin:-moc}; Arch package: qt6-base)")
    fi
    pkg-config --exists Qt6Quick Qt6Qml 2> /dev/null ||
        missing+=("Qt6Quick/Qt6Qml pkg-config modules (Arch package: qt6-declarative)")
    pkg-config --exists KF6CoreAddons 2> /dev/null ||
        missing+=("KF6CoreAddons pkg-config module (Arch package: kcoreaddons)")
    if [[ ! -r /usr/include/KDecoration3/KDecoration3/Decoration ]] ||
        ! g++ -std=c++20 -x c++ - -I/usr/include/KDecoration3 -lkdecorations3 -o /dev/null <<< 'int main() { return 0; }' 2> /dev/null; then
        missing+=("KDecoration 3 headers or libkdecorations3 (Arch package: kdecoration)")
    fi
    if ((${#missing[@]})); then
        local joined
        joined=$(printf '%s; ' "${missing[@]}")
        die "missing required C++/Qt/KDE build prerequisites: ${joined%; }. Install the missing Arch package(s) and try again; nothing was changed"
    fi
}
if [[ -z ${M9_PREBUILT:-} ]]; then
    preflight_plugin_build
fi

# Verify the exact reviewed archive before touching the installation, even
# on a dry run. This covers every cursor image and alias.
cursor_archive=$here/cursors/macOS-cursors.tar.xz
if ! cursor_sum=$(sha256sum < "$cursor_archive") ||
    [[ ${cursor_sum%% *} != 522ddd78562e4eadd0984cf743bd77f7efd8938c957227e780e2c48898c5ad3f ]]; then
    die "the bundled cursor archive is missing or has changed. Restore $cursor_archive from the project and try again; nothing was changed"
fi

for wallpaper_id in "${wallpaper_ids[@]}"; do
    wallpaper_source=$here/wallpapers/$wallpaper_id
    [[ -r $wallpaper_source/metadata.json && -r $wallpaper_source/contents/images/3840x2160.jxl ]] ||
        die "couldn't find the Platinum wallpaper package in $wallpaper_source"
done

gtk_source=$here/gtk/Platinum
python3 -I "$here/scripts/gtk_theme.py" validate "$gtk_source" || die "GTK 3 package preflight failed"
[[ ! -L $gtk_theme_dir ]] || die "$gtk_theme_dir is a symbolic link; cannot install into it"

terminal_scheme_source=$here/extras/terminal/$terminal_scheme
[[ -r $terminal_scheme_source && -f $terminal_scheme_source ]] ||
    die "couldn't find the Platinum Lavender terminal palette at $terminal_scheme_source; nothing was installed"

# Verify WhiteSur Lavender builder, custom icon layer, and upstream source
# before touching anything, even on a dry run (AUDIT.md #110).
# Resolution order:
#   1. M9_PREBUILT/icons (test-only prebuilt shortcut)
#   2. M9_WHITESUR_UPSTREAM (explicit local checkout; never fetched into)
#   3. Cache at $cache/macos9-theme/WhiteSur-icon-theme (auto-fetches exact
#      reviewed commit on real run if missing; --dry-run never downloads).
whitesur_remote=${M9_WHITESUR_REMOTE:-https://github.com/vinceliuice/WhiteSur-icon-theme.git}
whitesur_cache=$cache/macos9-theme/WhiteSur-icon-theme
whitesur_custom_dir=${M9_ICON_CUSTOM_DIR:-$here/icons/custom}
use_prebuilt_icons=0
whitesur_need_fetch=0
whitesur_upstream=""
if [[ -n ${M9_PREBUILT:-} && -r $M9_PREBUILT/icons/$icon_base_id/index.theme ]]; then
    use_prebuilt_icons=1
else
    [[ -x $here/icons/build-whitesur-lavender.sh && -x $here/icons/fetch-whitesur.sh && -r $here/icons/whitesur-lavender.py && -r $here/icons/whitesur-pin.json ]] ||
        die "WhiteSur Lavender builder files are missing in $here/icons; nothing was changed"
    # Preflight every icon builder/verifier tool and Python/GTK module BEFORE
    # taking the lock, cleaning temporaries, fetching, or placing files (#118).
    python3 -I "$here/icons/whitesur-lavender.py" --preflight "$whitesur_custom_dir" ||
        exit 1
    pinned_whitesur=$(python3 -I "$here/icons/whitesur-lavender.py" --print-pin) ||
        die "couldn't read pinned WhiteSur commit from $here/icons/whitesur-pin.json; nothing was changed"
    python3 -I "$here/icons/whitesur-lavender.py" --validate-custom "$whitesur_custom_dir" ||
        die "custom icon layer validation failed ($whitesur_custom_dir); nothing was changed"
    if [[ -n ${M9_WHITESUR_UPSTREAM:-} ]]; then
        whitesur_upstream=$M9_WHITESUR_UPSTREAM
        [[ -d $whitesur_upstream ]] ||
            die "upstream WhiteSur clone not found at $whitesur_upstream; nothing was changed"
        up_real=$(realpath -m -- "$whitesur_upstream")
        up_ceil=$(dirname -- "$up_real")
        up_gdir=$(GIT_CEILING_DIRECTORIES="$up_ceil" git -C "$up_real" rev-parse --absolute-git-dir 2> /dev/null || true)
        [[ -n $up_gdir && ( $up_gdir == "$up_real" || $up_gdir == "$up_real/.git" ) ]] ||
            die "upstream WhiteSur at $whitesur_upstream is not a valid git repository; nothing was changed"
        actual_whitesur=$(GIT_CEILING_DIRECTORIES="$up_ceil" git -C "$up_real" rev-parse --verify "HEAD^{commit}" 2> /dev/null || true)
        [[ $actual_whitesur == "$pinned_whitesur" ]] ||
            die "upstream WhiteSur at $whitesur_upstream is at ${actual_whitesur:-invalid}, expected reviewed pin $pinned_whitesur; nothing was changed"
    else
        whitesur_upstream=$whitesur_cache
        fetch_state=$("$here/icons/fetch-whitesur.sh" --check-only "$pinned_whitesur" "$whitesur_cache" "$whitesur_remote") ||
            die "cached WhiteSur check failed; nothing was changed"
        [[ $fetch_state == NEEDS_FETCH ]] && whitesur_need_fetch=1
    fi
fi

# Refuse to start or resume an install while an earlier uninstall.sh is unfinished (#140).
check_unfinished_uninstall() {
    if [[ -e $uninstall_marker || -L $uninstall_marker || -e $restore_decision_file || -L $restore_decision_file ]]; then
        die "an earlier uninstall.sh did not finish. Run uninstall.sh again to complete removal before running install.sh; nothing was changed"
    fi
    if [[ -f $icon_adoption && ! -L $icon_adoption ]]; then
        local tx_line tx_phase tx_dec
        tx_line=$(python3 -I "$icon_prefs" read-tx-status "$icon_adoption") ||
            die "couldn't read $icon_adoption; nothing was changed"
        IFS=$'\t' read -r tx_phase tx_dec <<< "$tx_line"
        if [[ $tx_phase == restoring || $tx_phase == restored || $tx_dec == restore_backup ]]; then
            die "an earlier uninstall.sh did not finish (icon transaction phase: $tx_phase). Run uninstall.sh again to complete removal before running install.sh; nothing was changed"
        fi
    fi
}

((dry_run)) && note "Dry run: nothing is changed."
# Everything that could stop the install halfway is checked first.
check_unfinished_uninstall
check_target_parents
check_backup_links
if ((!dry_run && !use_prebuilt_icons && whitesur_need_fetch)); then
    # Fetch into cache (with its own per-cache flock) before creating $state/lock,
    # so an offline miss leaves $HOME completely unchanged (#116, #122).
    "$here/icons/fetch-whitesur.sh" "$pinned_whitesur" "$whitesur_cache" "$whitesur_remote" > /dev/null ||
        die "couldn't obtain pinned WhiteSur commit $pinned_whitesur; nothing was installed"
fi
take_lock
check_unfinished_uninstall
manifest_load
check_record_paths
remove_temporaries
reconcile_displaced

# Build the plugins and WhiteSur Lavender icons in a temporary folder before
# installing anything.
if ((dry_run)); then
    build=/nonexistent
    plan "build the application style and the window decoration"
    if ((use_prebuilt_icons)); then
        plan "stage prebuilt WhiteSur Lavender icon themes"
    else
        if ((whitesur_need_fetch)); then
            plan "fetch pinned WhiteSur commit $pinned_whitesur from $whitesur_remote into $whitesur_cache"
        fi
        plan "build and verify WhiteSur Lavender icon themes from $whitesur_upstream"
    fi
else
    build=$(mktemp -d)
    trap 'rm -rf "${build:-/nonexistent}"' EXIT
    # Package GTK 3 with its shared palette and metadata for named-theme lookup.
    mkdir -p "$build/gtk-theme"
    cp -R "$gtk_source/"{index.theme,palette.css,gtk-3.0} "$build/gtk-theme/"
    mkdir -p "$build/cursors" "$build/icons"
    tar -xJf "$cursor_archive" -C "$build/cursors" "$black_cursor_id" ||
        die "couldn't unpack the bundled cursor theme; nothing was installed"
    if ((use_prebuilt_icons)); then
        icon_source_root=$M9_PREBUILT/icons
    else
        icon_source_root=$build/icons
        M9_ICON_CUSTOM_DIR="$whitesur_custom_dir" "$here/icons/build-whitesur-lavender.sh" "$whitesur_upstream" "$build/icons" > /dev/null ||
            die "building the WhiteSur Lavender icon themes failed; nothing was installed"
        for icon_id in "${icon_theme_ids[@]}"; do
            rm -f "$build/icons/$icon_id/.macos9-whitesur-lavender-build"
        done
    fi
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

# Plasma's cursor picker uses XCURSOR_PATH and can skip the XDG data
# directory when it is unset. Keep the other cursor themes searchable.
macos9_cursor_path=$(sh_quote "$data/icons")
if [ -z "\${XCURSOR_PATH:-}" ]; then
    XCURSOR_PATH="\$HOME/.local/share/icons:\$HOME/.icons:/usr/share/icons:/usr/share/pixmaps:/usr/X11R6/lib/X11/icons"
fi
case ":\$XCURSOR_PATH:" in
    *":\$macos9_cursor_path:"*) ;;
    *) XCURSOR_PATH="\$macos9_cursor_path:\$XCURSOR_PATH" ;;
esac
export XCURSOR_PATH
unset macos9_cursor_path
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

# Capture the single durable icon-selection transaction ($icon_adoption, v3 JSON)
# under the install lock BEFORE the very first change to installed targets or
# $manifest (AUDIT.md #110, #113, #117, #124, #128, #131, #139).
icons_already_tracked=0
if [[ -f $icon_adoption && ! -L $icon_adoption ]]; then
    icons_already_tracked=1
else
    for icon_id in "${icon_theme_ids[@]}"; do
        icon_path=$data/icons/$icon_id
        for entry in "${manifest_entries[@]:1}"; do
            IFS=$'\t' read -r ekind epath _ <<< "$entry"
            if [[ ($ekind == dir || $ekind == displaced) && $epath == "$icon_path" ]]; then
                icons_already_tracked=1
                break 2
            fi
        done
    done
fi
active=$(active_lnf)
taken=$(backup_taken || true)
intend_theme=""
if ((!icons_already_tracked)); then
    eff_line=$(python3 -I "$icon_prefs" effective-kde "$config_home/kdeglobals" "$config_home/kdedefaults") ||
        die "couldn't read existing icon theme settings; nothing was installed"
    IFS=$'\t' read -r eff_source eff_theme <<< "$eff_line"
    backup_predated=0
    if [[ -d $backup && ($taken == apply || ($taken == install && $active == "$lnf_id")) ]]; then
        backup_predated=1
    fi
    if ((!apply)) && [[ $active == "$lnf_id" ]] && ! is_managed_icon_id "$eff_theme"; then
        intend_theme=$icon_base_id
    fi
    pre_states=()
    for icon_id in "${icon_theme_ids[@]}"; do
        if [[ -e $data/icons/$icon_id || -L $data/icons/$icon_id ]]; then
            pre_states+=(manual)
        else
            pre_states+=(absent)
        fi
    done
    plan "record existing KDE and GTK icon preferences ($eff_source:${eff_theme:-default}) and manual Lavender state in $icon_adoption"
    if ((!dry_run)); then
        mkdir -p "$state"
        python3 -I "$icon_prefs" capture "$config_home" "$home" "$icon_adoption" "$backup_predated" "$intend_theme" "${pre_states[@]}" ||
            die "couldn't record existing icon preferences in $icon_adoption"
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
place_dir "$build/cursors/$black_cursor_id" "$cursor_theme_dir"
say "Installed the cursors into $cursor_theme_dir"
place_file "$here/colors/$scheme_name.colors" "$data/color-schemes/$scheme_name.colors" 644
say "Installed the color scheme \"Platinum\""
if manifest_lists dir "$gtk_theme_dir"; then
    # Prior installs recorded the entire directory, including displaced originals.
    place_dir "$build/gtk-theme" "$gtk_theme_dir"
else
    # Other toolkits can share this theme name. Own only our GTK 3 resources.
    if ((!dry_run)); then
        cp "$gtk_source/palette.css" "$build/gtk-theme/gtk-3.0/palette.css"
        sed -i 's|url("../palette.css")|url("palette.css")|' "$build/gtk-theme/gtk-3.0/gtk.css"
    fi
    if [[ ! -e $gtk_theme_dir/index.theme && ! -L $gtk_theme_dir/index.theme ]] ||
        manifest_lists file "$gtk_theme_dir/index.theme"; then
        place_file "$gtk_source/index.theme" "$gtk_theme_dir/index.theme" 644
    fi
    place_dir "$build/gtk-theme/gtk-3.0" "$gtk_theme_dir/gtk-3.0"
fi
say "Installed the Platinum GTK 3 theme. To use it for one app, launch it with GTK_THEME=Platinum."
place_file "$terminal_scheme_source" "$terminal_scheme_path" 644
say "Installed the Platinum Lavender terminal palette for Kwi and Konsole"
place_dir "$here/plasma/platinum" "$data/plasma/desktoptheme/$plasma_theme"
drop_plasma_caches
say "Installed the Plasma style \"Platinum\""
place_dir "$here/plasma/plasmoids/$piece_id" "$data/plasma/plasmoids/$piece_id"
place_dir "$here/plasma/plasmoids/$trash_id" "$data/plasma/plasmoids/$trash_id"
for wallpaper_id in "${wallpaper_ids[@]}"; do
    place_dir "$here/wallpapers/$wallpaper_id" "$data/wallpapers/$wallpaper_id"
done
say "Installed the Platinum wallpapers"
place_dir "$here/plasma/look-and-feel/$lnf_id" "$data/plasma/look-and-feel/$lnf_id"
say "Installed the global theme \"Platinum\" and its menu bar widget"

# Icon themes are placed last so their 44k checksums are appended after smaller
# targets and dropped first during uninstall.
for icon_id in "${icon_theme_ids[@]}"; do
    place_dir "${icon_source_root:-/nonexistent}/$icon_id" "$data/icons/$icon_id"
done
say "Installed the WhiteSur Lavender icon themes into $data/icons"

# The copy of your config files from before the switch. It's taken now
# already (before any plain-install active-Platinum icon selection or --apply),
# so uninstall.sh can put things back even if you switch in System Settings
# instead of with --apply. Until the switch it's refreshed on every run;
# after it, it's never replaced.
active=$(active_lnf)
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

# Apply or resume the durable one-time active-Platinum icon selection
# transaction (#128, #141), re-checking the active global theme before
# resuming so switching away from Platinum cancels stale intent.
if ((!apply)); then
    if ((dry_run)); then
        if [[ -f $icon_adoption && ! -L $icon_adoption ]]; then
            tx_out=$(python3 -I "$icon_prefs" apply-tx "$config_home" "$home" "$icon_adoption" --active-lnf "$active" --lnf-id "$lnf_id" --dry-run) ||
                die "couldn't preview icon selection transaction"
            while IFS=$'\t' read -r ttag tmsg; do
                [[ $ttag == PLAN ]] && plan "$tmsg"
            done <<< "$tx_out"
        elif [[ -n $intend_theme ]]; then
            plan "select $intend_theme icons for KDE and GTK (Platinum is active; other settings unchanged)"
        fi
    elif [[ -f $icon_adoption && ! -L $icon_adoption ]]; then
        tx_out=$(python3 -I "$icon_prefs" apply-tx "$config_home" "$home" "$icon_adoption" --active-lnf "$active" --lnf-id "$lnf_id") ||
            die "couldn't select $icon_base_id icons for KDE and GTK"
        while IFS=$'\t' read -r ttag tmsg; do
            if [[ $ttag == SAY ]]; then
                notify_icons
                say "$tmsg"
            fi
        done <<< "$tx_out"
    fi
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
        # Ensure a stale Theme[$d] marker in kdeglobals doesn't hide kdedefaults (#142).
        python3 -I "$icon_prefs" clear-deleted-marker "$config_home/kdeglobals"
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
