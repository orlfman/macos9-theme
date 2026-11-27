// SPDX-FileCopyrightText: 2026 ChathurangaBW
// SPDX-License-Identifier: GPL-2.0-or-later
// Modified by the Platinum theme on 2026-11-26.

#pragma once

#include <QObject>
#include <QStringList>

#include <memory>

class QMenu;
class QWidget;

class DesktopFallbackActionRunner
{
public:
    virtual ~DesktopFallbackActionRunner() = default;

    virtual bool programAvailable(const QString &program) const = 0;
    virtual void startProgram(const QString &program, const QStringList &arguments) = 0;
    virtual void createFolder(const QString &desktopDirectory, QWidget *parent) = 0;
};

bool isSafeDesktopItemName(const QString &name);
bool createDesktopFolder(const QString &desktopDirectory, const QString &name, QString *errorMessage = nullptr);

class DesktopFallback final : public QObject
{
public:
    explicit DesktopFallback(QObject *parent = nullptr);
    DesktopFallback(DesktopFallbackActionRunner *runner,
                    const QString &desktopDirectory,
                    QObject *parent = nullptr);
    ~DesktopFallback() override;

    QMenu *menu() const;

private:
    std::unique_ptr<DesktopFallbackActionRunner> m_ownedRunner;
    DesktopFallbackActionRunner *m_runner = nullptr;
    QString m_desktopDirectory;
    std::unique_ptr<QMenu> m_menu;
};
