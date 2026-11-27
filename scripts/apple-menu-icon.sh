# Opt-in Apple logo on the Apple-menu stand-in (install.sh --apple-menu-icon).
# SPDX-License-Identifier: BSD-2-Clause
#
# The theme's own default stays the neutral start-here icon (PLAN decision 6,
# AGENTS.md legal rules). At the user's request, --apply --apple-menu-icon
# points the top bar's single Kicker at the icon theme's folder-apple, which
# WhiteSur and some other icon themes ship as the Apple logo. Nothing of
# Apple's is shipped here; only the icon name is set.
#
# The running shell does the work through Plasma's scripting API, so no
# restart is needed. The marker keeps the Kicker's previous two settings so
# an uninstall that keeps the panel can put them back.

apple_icon_name=folder-apple
apple_icon_marker=$state/apple-menu-icon

# Use KDE's active theme and inheritance. Its lookup can fall back from
# folder-apple to folder, so require a path for the exact icon name.
apple_icon_available() {
    local path
    path=$(QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME=kde kiconfinder6 "$apple_icon_name" 2> /dev/null) || return 1
    [[ ${path##*/} == "$apple_icon_name".* && -f $path && -r $path ]]
}

# JavaScript string literal for a single-line value.
apple_icon_js_string() {
    local value=${1//\\/\\\\}
    value=${value//\"/\\\"}
    printf '"%s"' "$value"
}

# The top bar's Kicker widgets, as a script prelude. Only a single one is
# changed, so a custom layout with several launchers is left to its owner.
apple_icon_prelude='var hits = [];
panels().forEach(function (p) {
    if (p.location === "top") {
        p.widgets("org.kde.plasma.kicker").forEach(function (w) { hits.push(w); });
    }
});'

set_apple_menu_icon() {
    plan "show $apple_icon_name on the Apple-menu stand-in (the top bar's Application Menu)"
    ((dry_run)) && return 0
    if ! have kiconfinder6; then
        warn "kiconfinder6 is unavailable, so the Apple-menu stand-in keeps its icon"
        return 0
    fi
    if ! apple_icon_available; then
        warn "the active KDE icon theme doesn't provide $apple_icon_name, so the Apple-menu stand-in keeps its icon"
        return 0
    fi
    # The look-and-feel switch may have changed the inherited theme while
    # the shell kept its icon cache.
    notify_icons
    local result previous
    result=$(menu_shell_script "$apple_icon_prelude
if (hits.length === 1) {
    var w = hits[0];
    w.currentConfigGroup = [\"General\"];
    var use = String(w.readConfig(\"useCustomButtonImage\", false));
    var image = String(w.readConfig(\"customButtonImage\", \"\"));
    w.writeConfig(\"customButtonImage\", $(apple_icon_js_string "$apple_icon_name"));
    w.writeConfig(\"useCustomButtonImage\", true);
    print(\"M9_APPLE_ICON_SET\t\" + use + \"\t\" + image);
} else {
    print(\"M9_APPLE_ICON_SKIP \" + hits.length);
}") || result=""
    case $result in
        *M9_APPLE_ICON_SET*)
            previous=${result#*M9_APPLE_ICON_SET$'\t'}
            previous=${previous%%$'\n'*}
            # Keep the first recorded original across repeated --apply runs.
            if [[ ! -e $apple_icon_marker ]]; then
                printf '%s\n' "$previous" > "$apple_icon_marker" ||
                    warn "couldn't record the Apple-menu stand-in's previous icon; uninstall will leave $apple_icon_name"
            fi
            say "The Apple-menu stand-in shows $apple_icon_name (Apple's logo, from your icon theme)"
            ;;
        *M9_APPLE_ICON_SKIP*)
            warn "the top bar doesn't have exactly one Application Menu (Kicker); left its icon alone"
            ;;
        *)
            warn "couldn't reach Plasma's shell to set the Apple-menu stand-in's icon; run install.sh --apply --apple-menu-icon again"
            ;;
    esac
}

# Uninstall without a full layout restore: put the Kicker's previous settings
# back, but only while it still shows the icon this option set.
restore_apple_menu_icon() {
    [[ -f $apple_icon_marker && ! -L $apple_icon_marker ]] || return 0
    local previous previous_use previous_image result
    previous=$(head -n 1 "$apple_icon_marker")
    IFS=$'\t' read -r previous_use previous_image <<< "$previous"
    [[ $previous_use == true ]] || previous_use=false
    plan "put back the Apple-menu stand-in's previous icon if it still shows $apple_icon_name"
    ((dry_run)) && return 0
    result=$(menu_shell_script "$apple_icon_prelude
if (hits.length === 1) {
    var w = hits[0];
    w.currentConfigGroup = [\"General\"];
    if (String(w.readConfig(\"customButtonImage\", \"\")) === $(apple_icon_js_string "$apple_icon_name")
            && String(w.readConfig(\"useCustomButtonImage\", false)) === \"true\") {
        w.writeConfig(\"customButtonImage\", $(apple_icon_js_string "$previous_image"));
        w.writeConfig(\"useCustomButtonImage\", $previous_use);
        print(\"M9_APPLE_ICON_RESTORED\");
    } else {
        print(\"M9_APPLE_ICON_CHANGED\");
    }
} else {
    print(\"M9_APPLE_ICON_CHANGED\");
}") || result=""
    case $result in
        *M9_APPLE_ICON_RESTORED*) say "Put back the Apple-menu stand-in's previous icon" ;;
        *M9_APPLE_ICON_CHANGED*) ;;
        *)
            return 1
            ;;
    esac
    rm -f "$apple_icon_marker"
}
