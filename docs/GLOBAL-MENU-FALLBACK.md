# Global menu fallback for the desktop and apps without menus

Research for Platinum, 2026-11-26. The local baseline was Plasma and KWin
6.8.3, Qt 6.12.1 and Dolphin 26.08.3.

## Feasibility

A replacement Plasma applet can show a small file-management menu when the
desktop is active or the focused app has no usable global menu. The same applet
can show Dolphin’s actual menu when Dolphin is focused and the native menus of
other apps whenever they export one. The fallback can open Dolphin on demand,
so it works at login and with every Dolphin window closed. A third-party
applet already demonstrates the switch between a local fallback and an
exported app menu. [KDE Global Menu source selection](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/appmenumodel.cpp#L386-L442)

Platinum’s 20 px top panel uses the stock `org.kde.plasma.appmenu` applet.
On Wayland, its model gets the active task’s menu service and object path
from Plasma’s task model. If either is missing it clears the app menu. It
also marks an empty imported menu unavailable. The standard multi-title view
hides when there are no rows to show. Its only configuration options are
compact mode and whether to follow apps on all screens. There is no fallback
setting in Plasma 6.8.3. The `widgets/menubaritem` SVG controls the appearance
of existing titles. The applet supplies the titles and their actions.
[Platinum layout](../plasma/layout.js#L35-L43) · [KDE model](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/appmenumodel.cpp#L296-L335) · [KDE panel view](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/qml/main.qml#L56-L65) · [KDE settings](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/main.xml#L8-L18) · [Platinum menu styling](FINDINGS.md#what-a-top-panel-the-global-menu-and-a-global-theme-do)

## Can the fallback use Dolphin’s actual menu?

An applet can import the menu exported by an existing Dolphin window. Early
QuickBar did this by finding a Dolphin task and caching its D-Bus menu
address for use when the active task had no menu. Its 0.2.1 change removed the
Dolphin proxy and mentions crashes when switching menu items. The current
QuickBar source reviewed for this report uses a generic local menu, even
though its Arch packaging notes still advertise a Dolphin desktop menu.
[QuickBar change removing the proxy](https://github.com/kevinbudz/quickbar/commit/978b9d00261a8d133499f98ded9981f8b7d82eb4) · [Current fallback](https://github.com/kevinbudz/quickbar/blob/213a583adfd257ed420c77ef2cf1443a709a3425/src/genericmenu.cpp#L32-L62) · [Arch packaging notes](https://github.com/kevinbudz/quickbar/blob/213a583adfd257ed420c77ef2cf1443a709a3425/packaging/arch/AUR.md#L18-L31)

An imported menu belongs to the Dolphin window that exported it. Dolphin
derives actions such as Rename, Cut and Move to Trash from that window’s
active view and selected items. A desktop command could therefore act on
files selected in a background window, in a directory unrelated to the
desktop. With multiple Dolphin windows, the applet would also have to choose
which one owns the fallback and handle its closure. Dolphin’s background
FileManager1 implementation exposes operations on explicit URIs, such as
opening a folder, revealing a file and showing properties. The interface
has no method for obtaining a window menu or reading its selection.
[Dolphin selection handling](https://github.com/KDE/dolphin/blob/v26.08.3/src/dolphinmainwindow.cpp#L2611-L2666) · [Dolphin FileManager1 implementation](https://github.com/KDE/dolphin/blob/v26.08.3/src/dbusinterface.cpp#L17-L60) · [FileManager1 specification](https://www.freedesktop.org/specifications/file-manager-interface/)

## Existing Plasma 6 applets

- **KDE Global Menu** by ChathurangaBW is the closest ready-made option to
  try. Its `org.chathuranga.globalmenu` applet uses the same local fallback
  for the desktop and for apps without an exported menu. It offers desktop
  item creation and opens Home, Documents, Downloads and Trash through URL
  handlers. Its file creation targets the configured XDG Desktop directory.
  Its menu also includes system actions such as Restart Plasma Shell and
  Lock Screen, so the unmodified applet is broader than Platinum’s proposed
  file menu. [Applet metadata](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/metadata.json) · [Desktop target and File actions](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/desktopfallback.cpp#L341-L463) · [Go actions](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/desktopfallback.cpp#L521-L529)
- **Global Menu Extended** explicitly opens Home, Documents, Downloads and
  Trash in Dolphin. Its broader fallback includes active-window commands and
  sends synthetic keystrokes for some Edit and navigation commands. Its
  Documents and Downloads entries also assume English directory names under
  Home. The Dolphin launch actions are a precedent for explicit navigation.
  [Global Menu Extended provider](https://github.com/istorie-petru/global-menu-extended/blob/42389721ba5bbf538634e568bb88107c3d630179/src/providers/fallbackmenuprovider.cpp#L57-L80) · [Folder targets](https://github.com/istorie-petru/global-menu-extended/blob/42389721ba5bbf538634e568bb88107c3d630179/src/providers/fallbackmenuprovider.cpp#L174-L192)

**Local verification.** KDE Global Menu 1.1.3 at `4a24e4d` built in an isolated
temporary directory with the system’s Plasma 6.8.3 libraries. All three
focused CTest suites passed with no skips. They covered the fallback action
model and dispatch, fallback → exported D-Bus menu → fallback, and applet
menu switching and keyboard navigation. The built applet also passed
`plasmawindowed --smoke-test` offscreen. The smoke run logged headless
portal and activity-service warnings. Nested Wayland panel interaction,
Platinum rendering and real Dolphin launches still need verification.
[Test definitions](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/tests/CMakeLists.txt#L4-L76)

## Suggested first version for Platinum

Use the existing global-menu slot and show two headings in the fallback.

| Heading | Actions |
| --- | --- |
| **File** | **New Dolphin Window** opens a new file manager window. **New Folder on Desktop…** prompts for a name and creates a folder in the configured desktop directory. |
| **Go** | **Home**, **Desktop Folder**, **Documents**, **Downloads** and **Trash** open those locations. |

Use the same commands whether the desktop or a menuless app is active.
Resolve local folders with their XDG locations. Treat **Desktop Folder** as
opening a folder window. If Folder View points at a different location, make
the target explicit or use that location when it can be determined reliably.
Use `dolphin --new-window` for the new-window action. For opening locations,
use a Dolphin launch with explicit URLs or `FileManager1.ShowFolders` if
honoring the session’s file manager is desired. The latter can reuse an
existing window. Use KDE’s `KNewFileMenu` for folder creation at a known,
writable location. Selection-dependent commands such as Rename, Move to
Trash and Get Info can stay in Dolphin’s native menu until an extension has
an explicit desktop selection to act on. [Dolphin command-line options](https://github.com/KDE/dolphin/blob/v26.08.3/src/main.cpp#L135-L145) · [Dolphin folder opening](https://github.com/KDE/dolphin/blob/v26.08.3/src/dbusinterface.cpp#L29-L38) · [KNewFileMenu API](https://api.kde.org/knewfilemenu.html)

| Session state | Titles shown |
| --- | --- |
| Focused window publishes a usable menu | That window’s own app menu, including the actual Dolphin menu when Dolphin is focused. |
| Focused window has no exporter, its menu is still loading or the export becomes empty or disappears | The File and Go fallback. A newly usable export immediately takes over. |
| Desktop is active, including at login and after the last window closes | The same File and Go fallback. |

Switch on usable menu content from the current window, since a D-Bus address
can arrive before its menu is ready. Preserve the active window’s source
when the panel acquires input focus. Close open pop-ups and discard callbacks
from the old source when it changes. Confirm the desired desktop behavior
after both a desktop click and Show Desktop, since the stock applet derives
its source from Plasma’s active task. [KDE active-task handling](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/appmenumodel.cpp#L214-L226) · [Local fallback during import](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/appmenumodel.cpp#L386-L442)

## Integration and prototype checks

1. In a disposable Plasma session, replace the stock Global Menu widget
   with the existing KDE Global Menu applet in the same panel slot. Both
   register `org.kde.kappmenuview`, which the stock `kded6` appmenu module
   watches to start the registrar. Use one menu implementation in the panel
   for the test. A distinct plugin ID can be installed alongside stock and
   selected through the layout, with no modification to Plasma or KWin.
   [Stock applet service registration](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/appmenuapplet.cpp#L24-L60) · [KDED service watcher](https://github.com/KDE/plasma-workspace/blob/v6.8.3/appmenu/appmenu.cpp#L68-L102) · [Replacement registration](https://github.com/ChathurangaBW/global-menu-KDE/blob/4a24e4dfed7eac640023e1b28d06321f65385e2b/src/appmenuapplet.cpp#L25-L53)
2. Check desktop at login, desktop with other windows open, Show Desktop,
   a test window without a menu, Dolphin, and Kate. Exercise late and
   disappearing exports, fast switches with a menu open, and keyboard and
   hover navigation. Open every proposed location at least once, including
   from a session with Dolphin closed. Use a disposable desktop directory
   when checking folder creation. Check with focus on the secondary screen
   and with the panel on the primary, matching Platinum’s single-panel
   placement and Plasma’s default all-screens menu behavior.
   [Platinum test harness](DEVELOPMENT.md#the-plasma-style-and-the-menu-bar) · [KDE all-screens setting](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/main.xml#L14-L17)
3. If the prototype passes, scope any Platinum integration to an optional
   standalone applet. Keep the upstream app-menu import and pop-up behavior
   and use the existing `menubaritem` artwork for open titles. Evaluate
   user-scope discovery and removal for the compiled plugin, including a
   missing-plugin path that leaves the stock menu usable. Update the source
   layout only after the applet can be discovered reliably. The theme builder
   generates the look-and-feel layout from it. For an already customized
   desktop, swap the menu widget in place so a layout reset is unnecessary.
   Verify the 20 px bar at 100% and at a fractional display scale.
   [KDE’s compiled applet build](https://github.com/KDE/plasma-workspace/blob/v6.8.3/applets/appmenu/CMakeLists.txt#L1-L27) · [Theme layout generator](../plasma/make-plasma.py#L617-L620)
