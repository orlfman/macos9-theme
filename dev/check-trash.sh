#!/bin/bash
# Tests the Platinum Trash widget's trash state (TrashState.qml) offscreen:
# a missing trash folder reads as empty (not the current directory, AUDIT
# #228), creating it and trashing a file shows full without polling (#229),
# emptying shows empty, and an existing trash reads full at login.
#   usage: check-trash.sh   (exit 1 on a failure)
set -euo pipefail
dev=$(dirname "$(readlink -f "$0")")
project=$(dirname "$dev")
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
data="$work/data#?%20"
mkdir -p "$data" "$work/cwd"
# Like a real home: other folders beside the trash, and in the current
# directory, so a wrong folder would be counted (AUDIT #228).
mkdir -p "$data/"{applications,icons,Trashcan} "$work/cwd/"{x,y}
touch "$work/cwd/"{a,b,c}
cat > "$work/test.qml" << 'QML'
import QtQuick
Item {
    property int failures: 0
    function check(name, ok) { console.log((ok ? "ok      " : "FAIL    ") + name); if (!ok) failures++ }
    TrashState { id: trash }
    Timer { id: t1; interval: 600; running: true; onTriggered: {
        check("missing trash folder reads as empty", !trash.full && trash.count === 0)
        check("missing trash folder isn't counted as the current directory", !trash.exists)
        console.log("MKDIR")
    } }
    Timer { id: t2; interval: 2000; running: true; onTriggered: {
        check("a trashed item shows the trash full", trash.full && trash.count === 1)
        check("the new trash folder is noticed without polling", trash.exists)
        console.log("EMPTY")
    } }
    Timer { interval: 3500; running: true; onTriggered: {
        check("emptying the trash shows it empty", !trash.full && trash.count === 0)
        Qt.exit(failures === 0 ? 0 : 1)
    } }
}
QML
cp "$project/plasma/plasmoids/platinum.trash/contents/ui/TrashState.qml" "$work/"
# The test asks for each step on stdout; this loop carries them out.
(cd "$work/cwd" && XDG_DATA_HOME="$data" QT_QPA_PLATFORM=offscreen QT_FORCE_STDERR_LOGGING=1 \
    QT_LOGGING_RULES='qml.debug=true;js.debug=true' timeout 20 /usr/lib/qt6/bin/qml "$work/test.qml" 2>&1) |
    while IFS= read -r line; do
        case $line in
            *MKDIR) mkdir -p "$data/Trash/files" && touch "$data/Trash/files/item" ;;
            *EMPTY) rm -f "$data/Trash/files/item" ;;
            *ok\ \ \ \ \ \ *|*FAIL\ \ \ \ *) echo "${line#qml: }" ;;
        esac
    done
status=${PIPESTATUS[0]}

# At login the trash can already hold an item. Include data directories
# whose names must survive FolderListModel's second URL parse (#278).
cat > "$work/test2.qml" << 'QML'
import QtQuick
Item {
    TrashState { id: trash }
    Timer { interval: 600; running: true; onTriggered: {
        const ok = trash.full && trash.count === 1 && trash.exists
        console.log((ok ? "ok      " : "FAIL    ") + "an existing trash with an item reads full at once")
        Qt.exit(ok ? 0 : 1)
    } }
}
QML
for name in 'data2' 'data space' 'data#hash' 'data?query' 'data%20literal' 'data#?%20 café'; do
    mkdir -p "$work/$name/Trash/files" "$work/$name/"{applications,icons}
    touch "$work/$name/Trash/files/old"
    if ! (cd "$work/cwd" && XDG_DATA_HOME="$work/$name" QT_QPA_PLATFORM=offscreen QT_FORCE_STDERR_LOGGING=1 \
        QT_LOGGING_RULES='qml.debug=true;js.debug=true' timeout 20 /usr/lib/qt6/bin/qml "$work/test2.qml" 2>&1) |
        sed -n 's/^qml: //p' | grep -E '^(ok|FAIL) ' | sed "s/\$/ ($name)/"; then
        status=1
    fi
done
((status == 0))
