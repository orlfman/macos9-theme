// Qt style plugin: makes the Platinum style available as "Platinum".
//
// SPDX-License-Identifier: BSD-2-Clause
#include "platinumstyle.h"

#include <QStylePlugin>

class PlatinumStylePlugin : public QStylePlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QStyleFactoryInterface_iid FILE "platinum.json")

public:
    QStyle *create(const QString &key) override
    {
        if (key.compare(QLatin1String("platinum"), Qt::CaseInsensitive) == 0) {
            return new Platinum::Style;
        }
        return nullptr;
    }
};

#include "plugin.moc"
