# Qt Quick style spike (AUDIT.md finding 3)

Step 1 of PLAN.md "Plan: Qt Quick menus, tooltips and switches", sandbox
only. Results: docs/FINDINGS.md "Qt Quick style spike".

- `Platinum/`: a Qt Quick Controls style that overrides `ToolTip`, `Menu`,
  `MenuItem` and `MenuSeparator` and falls back to `org.kde.desktop 1.0`.
- `platinumitem.{h,cpp}`: the C++ item that paints with the application's
  QStyle (public Qt API only) and the QML plugin; `build.sh` builds it.
- `probe.qml`, `kirigami-colors.qml`, `menu.qml`, `switch.qml`: the test
  scenes (rendered with `dev/build/quickshot`); `menuref.cpp`: the widget
  QMenu they're compared with.

Run a scene from the project root (after `style/build.sh style/build` and
`spikes/qtquick/build.sh`):

```bash
QSTYLE=Platinum dev/run.sh platinum breeze env QT_QUICK_BACKEND=software QML_IMPORT_PATH=$PWD/spikes/qtquick QT_QUICK_CONTROLS_STYLE=Platinum dev/build/quickshot spikes/qtquick/probe.qml /tmp/probe.png
```

Kirigami also needs `kf6/kirigami/platform/Platinum.so` (a link to
`org.kde.desktop.so`) on `QT_PLUGIN_PATH`; the spike used one in
`dev/build/spike-kirigami-link/`.
