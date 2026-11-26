// SPDX-License-Identifier: BSD-2-Clause
#include <KPackage/Package>
#include <KPackage/PackageLoader>
#include <QCoreApplication>
#include <QDebug>
#include <klookandfeel.h>

int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    if (argc != 2) {
        return 2;
    }

    auto package = KPackage::PackageLoader::self()->loadPackage(QStringLiteral("Plasma/LookAndFeel"));
    package.setPath(QStringLiteral("platinum.desktop"));
    const auto path = KLookAndFeel::colorSchemeFilePath(package);
    const auto variant = KLookAndFeel::colorSchemeVariant(package);
    qInfo() << package.path() << path << variant;
    return package.isValid() && path == QString::fromLocal8Bit(argv[1]) && variant == KLookAndFeel::Variant::Light ? 0 : 1;
}
