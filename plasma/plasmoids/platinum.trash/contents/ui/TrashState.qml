// Whether the home trash holds anything, without Plasma imports so
// dev/check-trash.sh can test it with qml6 offscreen.
//
// FolderListModel falls back to the current directory for a folder that
// doesn't exist (AUDIT #228), so each folder is only watched once its parent
// shows it exists: ~/.local/share until "Trash" appears, Trash until "files"
// appears, then files itself. Everything is driven by the models' own file
// watchers, with no polling (AUDIT #229).
// SPDX-License-Identifier: BSD-2-Clause
import QtQuick
import QtCore
import Qt.labs.folderlistmodel

Item {
    id: state

    property string dataDir: StandardPaths.writableLocation(StandardPaths.GenericDataLocation)
    readonly property string trashDir: dataDir + "/Trash"
    readonly property string filesDir: trashDir + "/files"

    readonly property bool exists: trashAt === trashDir && filesAt === filesDir
    readonly property int count: exists ? files.count : 0
    readonly property bool full: count > 0

    // Where each model was last pointed (its folder property can't be
    // relied on to report this).
    property string trashAt: ""
    property string filesAt: ""

    FolderListModel {
        id: hasTrash
        // Idle at the root, not the current directory (often $HOME).
        folder: "file:///"
        showFiles: false
        showHidden: true
        showDotAndDotDot: false
        onCountChanged: state.follow()
        onStatusChanged: state.follow()
    }
    FolderListModel {
        id: hasFiles
        // Idle at the root, not the current directory (often $HOME).
        folder: "file:///"
        showFiles: false
        showHidden: true
        showDotAndDotDot: false
        onCountChanged: state.follow()
        onStatusChanged: state.follow()
    }
    FolderListModel {
        id: files
        folder: "file:///"
        showHidden: true
        showDirs: true
        showDotAndDotDot: false
        sortField: FolderListModel.Unsorted
    }

    // The model ignores being given the same folder again, and a folder set
    // during construction neither loads nor announces itself, so this always
    // goes through the root folder first.
    function point(model, folder) {
        model.folder = "file:///";
        model.folder = folder;
    }
    // nameFilters don't apply to folders, so look for the folder by name.
    function has(model, folder) {
        return model.status === FolderListModel.Ready && model.indexOf(folder) >= 0;
    }
    function follow() {
        if (has(hasTrash, trashDir)) {
            if (trashAt !== trashDir) {
                trashAt = trashDir;
                point(hasFiles, trashDir);
            }
        } else {
            trashAt = "";
        }
        if (trashAt === trashDir && has(hasFiles, filesDir)) {
            if (filesAt !== filesDir) {
                filesAt = filesDir;
                point(files, filesDir);
            }
        } else {
            filesAt = "";
        }
    }
    function start() {
        trashAt = "";
        filesAt = "";
        point(hasTrash, dataDir);
        Qt.callLater(follow);
    }
    Component.onCompleted: start()
    onDataDirChanged: start()
}
