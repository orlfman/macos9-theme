// SPDX-License-Identifier: GPL-2.0-or-later
// Modified by the Platinum theme on 2026-11-26.
#include "desktopfallback.h"
#include <KLocalizedString>
#include <QApplication>
#include <QMenu>
#include <QtTest>

class LocaleTest : public QObject
{
    Q_OBJECT
private Q_SLOTS:
    void usesProcessLocale()
    {
        // The test harness mirrors this process LANGUAGE value into KI18n.
        const bool french = qEnvironmentVariable("LANGUAGE") == QStringLiteral("fr");
        if (french) {
            QVERIFY(KLocalizedString::languages().contains(QStringLiteral("fr")));
            QVERIFY(KLocalizedString::availableDomainTranslations("plasma_applet_platinum.globalmenu").contains(QStringLiteral("fr")));
        }
        DesktopFallback fallback;
        const auto headings = fallback.menu()->actions();
        QCOMPARE(headings.size(), 2);
        QCOMPARE(headings.first()->text(), french ? QStringLiteral("&Fichier") : QStringLiteral("&File"));
        QCOMPARE(i18n("Search…"), french ? QStringLiteral("Rechercher…") : QStringLiteral("Search…"));
        QCOMPARE(headings.last()->text(), french ? QStringLiteral("A&ller") : QStringLiteral("&Go"));
        QCOMPARE(i18n("New Dolphin Window"), french ? QStringLiteral("Nouvelle fenêtre Dolphin") : QStringLiteral("New Dolphin Window"));
        QCOMPARE(i18nc("@info:usagetip", "Open a menu"), french ? QStringLiteral("Ouvrir un menu") : QStringLiteral("Open a menu"));
    }
};

int main(int argc, char **argv)
{
    QApplication application(argc, argv);
    KLocalizedString::addDomainLocaleDir("plasma_applet_platinum.globalmenu", QStringLiteral(TEST_LOCALE_DIR));
    // Minimal CI images do not always generate locale definitions. Mirror the
    // process LANGUAGE value explicitly so the test remains deterministic while
    // production continues to follow Plasma/KI18n's configured language list.
    const QString language = qEnvironmentVariable("LANGUAGE");
    if (!language.isEmpty()) {
        KLocalizedString::setLanguages(QStringList{language});
    }
    KLocalizedString::setApplicationDomain("plasma_applet_platinum.globalmenu");
    LocaleTest test;
    return QTest::qExec(&test, argc, argv);
}

#include "localetest.moc"
