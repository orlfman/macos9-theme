# User-scope global menu discovery and panel migration.
# SPDX-License-Identifier: BSD-2-Clause

panel_layout=$config_home/plasma-org.kde.plasma.desktop-appletsrc
menu_layout_mode_file=$state/global-menu-layout
menu_layout_mode=""

read_menu_layout_mode() {
    [[ -e $menu_layout_mode_file || -L $menu_layout_mode_file ]] || return 0
    [[ -f $menu_layout_mode_file && ! -L $menu_layout_mode_file ]] ||
        die "couldn't read $menu_layout_mode_file; nothing was changed"
    menu_layout_mode=$(< "$menu_layout_mode_file")
    [[ $menu_layout_mode == in-place || $menu_layout_mode == reset ]] ||
        die "$menu_layout_mode_file is damaged; nothing was changed"
}

set_menu_layout_mode() {
    ((dry_run)) && return 0
    local temporary
    temporary=$(mktemp "$state/.global-menu-layout.XXXXXX") || return 1
    if ! printf '%s\n' "$1" > "$temporary" || ! mv -fT "$temporary" "$menu_layout_mode_file"; then
        rm -f "$temporary"
        return 1
    fi
    menu_layout_mode=$1
}

# The global theme recorded in the config backup, or nothing when the copy
# has no kdeglobals. A backup taken before Platinum was active holds the
# user's original panels, which a full uninstall must put back (#321).
backup_lnf() {
    local copy=$backup/config/kdeglobals
    [[ -f $copy && ! -L $copy ]] || return 0
    awk -F= '/^\[/ { kde = ($0 == "[KDE]") } kde && $1 == "LookAndFeelPackage" { v = substr($0, index($0, "=") + 1) } END { print v }' \
        "$copy"
}

# The policy for a first in-place swap. In-place keeps the current panels on
# uninstall; that is only right when the backup already shows Platinum's
# panels. An install from before the menu marker whose backup predates
# Platinum still owns the original layout, so record a full reset.
first_swap_layout_mode() {
    if [[ -d $backup && $(backup_lnf) != "$lnf_id" ]]; then
        printf '%s\n' reset
    else
        printf '%s\n' in-place
    fi
}

panel_menu() {
    python3 -I "$here/scripts/global_menu_layout.py" "$panel_layout" "$@"
}

menu_shell_script() {
    shell_running_on_bus || return 1
    dbus-send --session --print-reply=literal --reply-timeout=4000 --dest=org.kde.plasmashell \
        /PlasmaShell org.kde.PlasmaShell.evaluateScript "string:$1" \
        2> /dev/null
}

global_menu_discovery() {
    local result
    result=$(menu_shell_script 'print(knownWidgetTypes.indexOf("platinum.globalmenu") >= 0 ? "M9_GLOBAL_MENU_READY" : "M9_GLOBAL_MENU_MISSING");') || result=""
    case $result in
        *M9_GLOBAL_MENU_READY*) printf '%s\n' ready ;;
        *M9_GLOBAL_MENU_MISSING*) printf '%s\n' missing ;;
        *) printf '%s\n' unknown ;;
    esac
}

shell_has_panel_menu() {
    # The ID is always one of our literal plugin IDs.
    menu_shell_script "if (panels().concat(desktops()).some(function (p) { return p.widgets(\"$1\").length; })) print(\"M9_GLOBAL_MENU_MATCH\");" |
        grep -q 'M9_GLOBAL_MENU_MATCH'
}

resume_panel_shell() {
    if [[ -f $global_menu_plugin ]]; then
        QT_PLUGIN_PATH="$global_menu_plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}" shell_resume
    else
        shell_resume
    fi
}

# Run only after the transaction has planned a change to the saved layout.
# Re-read it after stopping Plasma, which flushes settings when it exits.
switch_panel_menu() {
    local direction=$1 count=0 status=0
    shell_stop || return 1
    if [[ $direction == migrate ]]; then
        count=$(panel_menu migrate --check) || status=1
        if ((status == 0)) && [[ $count != 0 && -z $menu_layout_mode ]]; then
            set_menu_layout_mode "$(first_swap_layout_mode)" || status=1
        fi
    fi
    if ((status == 0)); then
        count=$(panel_menu "$direction") || status=1
    fi
    # Keep the stop marker if the shell could not be restarted. The next
    # install or uninstall can resume it using the shared shell helper.
    if [[ $direction == migrate ]]; then
        QT_PLUGIN_PATH="$global_menu_plugins${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}" shell_start || return 1
    else
        shell_start || return 1
    fi
    ((status == 0)) || return 1
    if [[ $count != 0 ]]; then
        if [[ $direction == migrate ]]; then
            say "Switched the existing panel to Platinum Global Menu"
        else
            say "Restored the stock Global Menu in the current panel layout"
        fi
    fi
}
