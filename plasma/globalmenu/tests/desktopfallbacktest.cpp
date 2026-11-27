// SPDX-FileCopyrightText: 2026 ChathurangaBW
// SPDX-License-Identifier: GPL-2.0-or-later
// Modified by the Platinum theme on 2026-11-26.

#include "desktopfallback.h"

#include <QAction>
#include <QDir>
#include <QFileInfo>
#include <QMenu>
#include <QStandardPaths>
#include <QTemporaryDir>
#include <QUrl>
#include <QtTest>

namespace
{
QStringList labels(QMenu *menu)
{
    QStringList result;
    for (const QAction *action : menu->actions()) {
        QString label = action->text();
        result << label.remove(QLatin1Char('&'));
    }
    return result;
}

struct ProgramCall {
    QString program;
    QStringList arguments;
};

class FakeRunner final : public DesktopFallbackActionRunner
{
public:
    bool programAvailable(const QString &program) const override
    {
        return dolphinAvailable && program == QStringLiteral("dolphin");
    }

    void startProgram(const QString &program, const QStringList &arguments) override
    {
        programCalls.append({program, arguments});
    }

    void createFolder(const QString &desktopDirectory, QWidget *) override
    {
        folderDirectories << desktopDirectory;
    }

    QList<ProgramCall> programCalls;
    QStringList folderDirectories;
    bool dolphinAvailable = true;
};
}

class DesktopFallbackTest : public QObject
{
    Q_OBJECT

private Q_SLOTS:
    void fileAndGoActions();
    void unavailableTargetsAreDisabled();
    void createsFolderOnlyAtTheIntendedLocation();
};

void DesktopFallbackTest::fileAndGoActions()
{
    QTemporaryDir temp;
    QVERIFY(temp.isValid());
    const QString desktop = temp.filePath(QStringLiteral("Desktop # Test"));
    FakeRunner runner;
    DesktopFallback fallback(&runner, desktop);
    QMenu *menu = fallback.menu();
    QCOMPARE(labels(menu), QStringList({QStringLiteral("File"), QStringLiteral("Go")}));

    QMenu *file = menu->actions().at(0)->menu();
    QVERIFY(file);
    QCOMPARE(labels(file), QStringList({QStringLiteral("New Dolphin Window"), QStringLiteral("New Folder on Desktop…")}));
    file->actions().at(0)->trigger();
    file->actions().at(1)->trigger();
    QCOMPARE(runner.programCalls.size(), 1);
    QCOMPARE(runner.programCalls.first().program, QStringLiteral("dolphin"));
    QCOMPARE(runner.programCalls.first().arguments, QStringList{QStringLiteral("--new-window")});
    QCOMPARE(runner.folderDirectories, QStringList{desktop});

    QMenu *go = menu->actions().at(1)->menu();
    QVERIFY(go);
    QCOMPARE(labels(go), QStringList({QStringLiteral("Home Folder"), QStringLiteral("Desktop Folder"),
                                     QStringLiteral("Documents"), QStringLiteral("Downloads"), QStringLiteral("Trash")}));
    const QList<QUrl> destinations = {
        QUrl::fromLocalFile(QDir::homePath()),
        QUrl::fromLocalFile(desktop),
        QUrl::fromLocalFile(QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation)),
        QUrl::fromLocalFile(QStandardPaths::writableLocation(QStandardPaths::DownloadLocation)),
        QUrl(QStringLiteral("trash:/")),
    };
    for (int row = 0; row < destinations.size(); ++row) {
        QAction *action = go->actions().at(row);
        const QUrl &destination = destinations.at(row);
        if (destination.isEmpty()) {
            QVERIFY(!action->isEnabled());
            continue;
        }
        QVERIFY(action->isEnabled());
        const auto callsBefore = runner.programCalls.size();
        action->trigger();
        QCOMPARE(runner.programCalls.size(), callsBefore + 1);
        QCOMPARE(runner.programCalls.last().program, QStringLiteral("dolphin"));
        QCOMPARE(runner.programCalls.last().arguments, QStringList{destination.toString(QUrl::FullyEncoded)});
    }
}

void DesktopFallbackTest::unavailableTargetsAreDisabled()
{
    FakeRunner runner;
    runner.dolphinAvailable = false;
    DesktopFallback fallback(&runner, QStringLiteral("/some/Desktop"));
    QMenu *file = fallback.menu()->actions().at(0)->menu();
    QVERIFY(!file->actions().at(0)->isEnabled());
    QVERIFY(file->actions().at(1)->isEnabled());
    for (const QAction *action : fallback.menu()->actions().at(1)->menu()->actions()) {
        QVERIFY(!action->isEnabled());
    }

    runner.dolphinAvailable = true;
    DesktopFallback missingDesktop(&runner, QString());
    QVERIFY(!missingDesktop.menu()->actions().at(0)->menu()->actions().at(1)->isEnabled());
    QVERIFY(!missingDesktop.menu()->actions().at(1)->menu()->actions().at(1)->isEnabled());
}

void DesktopFallbackTest::createsFolderOnlyAtTheIntendedLocation()
{
    QTemporaryDir temp;
    QVERIFY(temp.isValid());
    const QString desktop = temp.filePath(QStringLiteral("Desktop"));
    QString error;
    QVERIFY(createDesktopFolder(desktop, QStringLiteral(" Project #1 "), &error));
    QVERIFY(QFileInfo(desktop + QStringLiteral("/Project #1")).isDir());
    QVERIFY(!createDesktopFolder(desktop, QStringLiteral("Project #1"), &error));
    QVERIFY(!createDesktopFolder(desktop, QStringLiteral("../escape"), &error));
    QVERIFY(!QFileInfo::exists(temp.filePath(QStringLiteral("escape"))));
    QVERIFY(!createDesktopFolder(QString(), QStringLiteral("missing-target"), &error));
    QVERIFY(!isSafeDesktopItemName(QStringLiteral("a/b")));
    QVERIFY(!isSafeDesktopItemName(QStringLiteral("a\\b")));
    QVERIFY(!isSafeDesktopItemName(QStringLiteral("a\nb")));
    QVERIFY(!isSafeDesktopItemName(QStringLiteral(".")));
    QVERIFY(!isSafeDesktopItemName(QString(QChar::Null)));
}

QTEST_MAIN(DesktopFallbackTest)
#include "desktopfallbacktest.moc"
