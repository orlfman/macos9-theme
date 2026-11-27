// SPDX-FileCopyrightText: 2026 ChathurangaBW
// SPDX-License-Identifier: GPL-2.0-or-later
// Modified by the Platinum theme on 2026-11-26.

#include "desktopfallback.h"

#include <KLocalizedString>

#include <QAction>
#include <QDir>
#include <QFileInfo>
#include <QIcon>
#include <QInputDialog>
#include <QLineEdit>
#include <QMenu>
#include <QMessageBox>
#include <QProcess>
#include <QStandardPaths>
#include <QUrl>

namespace
{
class DefaultDesktopFallbackActionRunner final : public DesktopFallbackActionRunner
{
public:
    bool programAvailable(const QString &program) const override
    {
        return !QStandardPaths::findExecutable(program).isEmpty();
    }

    void startProgram(const QString &program, const QStringList &arguments) override
    {
        const QString executable = QStandardPaths::findExecutable(program);
        if (!executable.isEmpty()) {
            QProcess::startDetached(executable, arguments);
        }
    }

    void createFolder(const QString &desktopDirectory, QWidget *parent) override
    {
        bool accepted = false;
        const QString name = QInputDialog::getText(parent,
                                                   i18n("Create New Folder"),
                                                   i18n("Name:"),
                                                   QLineEdit::Normal,
                                                   i18n("New Folder"),
                                                   &accepted);
        if (accepted) {
            QString error;
            if (!createDesktopFolder(desktopDirectory, name, &error)) {
                QMessageBox::warning(parent, i18n("Create New Folder"), error);
            }
        }
    }
};

QAction *addAction(QMenu *menu, const QString &text, const QString &iconName)
{
    return menu->addAction(QIcon::fromTheme(iconName), text);
}

QUrl localLocation(const QString &path)
{
    return QDir::isAbsolutePath(path) ? QUrl::fromLocalFile(path) : QUrl();
}
}

bool isSafeDesktopItemName(const QString &name)
{
    const QString trimmed = name.trimmed();
    return !trimmed.isEmpty() && trimmed != QLatin1String(".") && trimmed != QLatin1String("..")
        && !trimmed.contains(QLatin1Char('/')) && !trimmed.contains(QLatin1Char('\\'))
        && !trimmed.contains(QLatin1Char('\n')) && !trimmed.contains(QLatin1Char('\r'))
        && !trimmed.contains(QChar::Null);
}

bool createDesktopFolder(const QString &desktopDirectory, const QString &name, QString *errorMessage)
{
    if (!isSafeDesktopItemName(name)) {
        if (errorMessage) {
            *errorMessage = i18n("Enter a name without path separators.");
        }
        return false;
    }

    QDir desktop(desktopDirectory);
    if (!QDir::isAbsolutePath(desktopDirectory) || (!desktop.exists() && !desktop.mkpath(QStringLiteral(".")))) {
        if (errorMessage) {
            *errorMessage = i18n("The Desktop folder is not available.");
        }
        return false;
    }

    const QString trimmed = name.trimmed();
    const QString path = desktop.filePath(trimmed);
    if (QFileInfo::exists(path)) {
        if (errorMessage) {
            *errorMessage = i18n("An item named %1 already exists.", trimmed);
        }
        return false;
    }

    if (desktop.mkdir(trimmed)) {
        return true;
    }
    if (errorMessage) {
        *errorMessage = i18n("The folder could not be created.");
    }
    return false;
}

DesktopFallback::DesktopFallback(QObject *parent)
    : DesktopFallback(nullptr, QStandardPaths::writableLocation(QStandardPaths::DesktopLocation), parent)
{
}

DesktopFallback::DesktopFallback(DesktopFallbackActionRunner *runner, const QString &desktopDirectory, QObject *parent)
    : QObject(parent)
    , m_ownedRunner(runner ? nullptr : std::make_unique<DefaultDesktopFallbackActionRunner>())
    , m_runner(runner ? runner : m_ownedRunner.get())
    , m_desktopDirectory(desktopDirectory)
    , m_menu(std::make_unique<QMenu>())
{
    const QString dolphin = QStringLiteral("dolphin");
    const bool dolphinAvailable = m_runner->programAvailable(dolphin);

    QMenu *fileMenu = m_menu->addMenu(i18n("&File"));
    QAction *newWindow = addAction(fileMenu, i18n("New Dolphin Window"), QStringLiteral("window-new"));
    newWindow->setEnabled(dolphinAvailable);
    connect(newWindow, &QAction::triggered, newWindow, [this, dolphin] {
        m_runner->startProgram(dolphin, {QStringLiteral("--new-window")});
    });

    QAction *newFolder = addAction(fileMenu, i18n("New Folder on Desktop…"), QStringLiteral("folder-new"));
    newFolder->setEnabled(QDir::isAbsolutePath(m_desktopDirectory));
    connect(newFolder, &QAction::triggered, newFolder, [this] {
        m_runner->createFolder(m_desktopDirectory, m_menu.get());
    });

    QMenu *goMenu = m_menu->addMenu(i18n("&Go"));
    const auto addLocation = [this, goMenu, dolphin, dolphinAvailable](const QString &label, const QUrl &url, const QString &iconName) {
        QAction *action = addAction(goMenu, label, iconName);
        action->setEnabled(dolphinAvailable && url.isValid() && !url.isEmpty());
        connect(action, &QAction::triggered, action, [this, dolphin, url] {
            m_runner->startProgram(dolphin, {url.toString(QUrl::FullyEncoded)});
        });
    };
    addLocation(i18n("Home Folder"), localLocation(QDir::homePath()), QStringLiteral("user-home"));
    addLocation(i18n("Desktop Folder"), localLocation(m_desktopDirectory), QStringLiteral("user-desktop"));
    addLocation(i18n("Documents"), localLocation(QStandardPaths::writableLocation(QStandardPaths::DocumentsLocation)), QStringLiteral("folder-documents"));
    addLocation(i18n("Downloads"), localLocation(QStandardPaths::writableLocation(QStandardPaths::DownloadLocation)), QStringLiteral("folder-download"));
    addLocation(i18n("Trash"), QUrl(QStringLiteral("trash:/")), QStringLiteral("user-trash"));
}

DesktopFallback::~DesktopFallback() = default;

QMenu *DesktopFallback::menu() const
{
    return m_menu.get();
}
