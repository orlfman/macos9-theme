# SPDX-License-Identifier: GPL-2.0-or-later
# Modified by the Platinum theme on 2026-11-26.
add_definitions(-DTRANSLATION_DOMAIN=\"plasma_applet_platinum.globalmenu\")

plasma_add_applet(platinum.globalmenu
    QML_SOURCES
        qml/configGeneral.qml
        qml/config.qml
        qml/main.qml
        qml/MenuDelegate.qml
    CPP_SOURCES
        appmenuapplet.cpp
        appmenumodel.cpp
        desktopfallback.cpp
    RESOURCES
        main.xml
    QML_ARGS DEPENDENCIES QtCore org.kde.plasma.core
)

target_compile_features(platinum.globalmenu PRIVATE cxx_std_20)

target_link_libraries(platinum.globalmenu PRIVATE
    Qt::Core
    Qt::Widgets
    Qt::Quick
    Qt::DBus
    Plasma::Plasma
    KF6::WindowSystem
    KF6::I18n
    PW::LibTaskManager
    dbusmenuqt
)
