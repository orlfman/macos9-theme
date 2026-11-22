// SPDX-License-Identifier: BSD-2-Clause
#include <QCoreApplication>
#include <QImageReader>

int main(int argc, char *argv[])
{
    const QCoreApplication app(argc, argv);
    const auto images = app.arguments();
    for (int i = 1; i < images.size(); ++i) {
        QImageReader reader(images.at(i));
        if (!reader.canRead())
            return 1;
    }
    return images.size() > 1 ? 0 : 1;
}
