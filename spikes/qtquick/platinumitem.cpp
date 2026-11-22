// SPDX-License-Identifier: BSD-2-Clause
#include "platinumitem.h"

#include <QApplication>
#include <QPainter>
#include <QQmlEngine>
#include <QQmlExtensionPlugin>
#include <QStyle>
#include <QStyleOption>
#include <QWidget>

// QApplication::setStyle() tells only widgets (QEvent::StyleChange), and a
// Qt Quick app has none: one hidden, never shown widget hears it for every
// item.
static QWidget *styleWatcher()
{
    static QWidget *watcher = nullptr;
    if (!watcher && qobject_cast<QApplication *>(QCoreApplication::instance())) {
        watcher = new QWidget;
        watcher->setAttribute(Qt::WA_DontShowOnScreen);
        watcher->ensurePolished();
        QObject::connect(qApp, &QCoreApplication::aboutToQuit, [] {
            delete watcher;
            watcher = nullptr;
        });
    }
    return watcher;
}

PlatinumItem::PlatinumItem(QQuickItem *parent)
    : QQuickPaintedItem(parent)
{
    setAntialiasing(false);
    connect(this, &PlatinumItem::changed, this, [this] {
        updateImplicitSize();
        update();
    });
    connect(this, &QQuickItem::enabledChanged, this, [this] { update(); });
    if (QWidget *watcher = styleWatcher()) {
        watcher->installEventFilter(this);
    }
    updateActive();
}

void PlatinumItem::updateActive()
{
    // Only a QApplication has a QStyle; a QGuiApplication-only app keeps
    // KDE's look.
    const auto *app = qobject_cast<QApplication *>(QCoreApplication::instance());
    const bool active = app && QApplication::style() && QApplication::style()->name() == QLatin1String("platinum");
    if (active != m_active) {
        m_active = active;
        Q_EMIT activeChanged();
        updateImplicitSize();
        update();
    }
}

bool PlatinumItem::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == styleWatcher() && event->type() == QEvent::StyleChange) {
        updateActive();
    }
    return false;
}

static void initMenuItem(QStyleOptionMenuItem *opt, const QString &type, const QString &text, const QString &shortcut, int shortcutColumn,
                         bool selected, bool enabled, bool checkable, bool checked, bool subMenu)
{
    opt->palette = QApplication::palette("QMenu");
    opt->font = QApplication::font("QMenu");
    opt->fontMetrics = QFontMetrics(opt->font);
    opt->state = QStyle::State_None;
    if (enabled) {
        opt->state |= QStyle::State_Enabled;
    }
    if (selected && enabled) {
        opt->state |= QStyle::State_Selected;
    }
    opt->menuItemType = type == QLatin1String("separator") ? QStyleOptionMenuItem::Separator
        : subMenu                                          ? QStyleOptionMenuItem::SubMenu
                                                           : QStyleOptionMenuItem::Normal;
    opt->checkType = checkable ? QStyleOptionMenuItem::NonExclusive : QStyleOptionMenuItem::NotCheckable;
    opt->checked = checked;
    opt->text = shortcut.isEmpty() ? text : text + QLatin1Char('\t') + shortcut;
    opt->reservedShortcutWidth = shortcutColumn;
    opt->maxIconWidth = 0;
}

void PlatinumItem::setApplicationStyle(const QString &name)
{
    QApplication::setStyle(name);
}

int PlatinumItem::shortcutWidth() const
{
    return m_shortcut.isEmpty() ? 0 : QFontMetrics(QApplication::font("QMenu")).horizontalAdvance(m_shortcut);
}

void PlatinumItem::updateImplicitSize()
{
    if (!m_active) {
        return;
    }
    QStyle *style = QApplication::style();
    if (m_type == QLatin1String("menuitem") || m_type == QLatin1String("separator")) {
        QStyleOptionMenuItem opt;
        initMenuItem(&opt, m_type, m_text, m_shortcut, m_shortcutColumn, m_selected, isEnabled(), m_checkable, m_checked, m_subMenu);
        opt.styleObject = this;
        setProperty("_platinum_shortcuts", m_shortcutColumn > 0);
        // What QMenu passes: the label's width and the font height; then it
        // adds the shortcut column to every row.
        const int label = opt.fontMetrics.boundingRect(QRect(), Qt::TextSingleLine | Qt::TextShowMnemonic, m_text).width();
        const QSize contents(m_type == QLatin1String("separator") ? 0 : label, opt.fontMetrics.height());
        const QSize size = style->sizeFromContents(QStyle::CT_MenuItem, &opt, contents, nullptr);
        setImplicitSize(size.width() + m_shortcutColumn, size.height());
    }
}

void PlatinumItem::paint(QPainter *painter)
{
    if (!m_active) {
        return;
    }
    QStyle *style = QApplication::style();
    const QRect r(0, 0, int(width()), int(height()));
    // The row's place, read by the style when there's no widget.
    setProperty("_platinum_first", m_first);
    setProperty("_platinum_last", m_last);
    setProperty("_platinum_combo", m_combo);
    setProperty("_platinum_shortcuts", m_shortcutColumn > 0);
    if (m_type == QLatin1String("menu")) {
        QStyleOption opt;
        opt.rect = r;
        opt.palette = QApplication::palette("QMenu");
        opt.state = QStyle::State_Enabled;
        opt.styleObject = this;
        style->drawPrimitive(QStyle::PE_PanelMenu, &opt, painter, nullptr);
    } else if (m_type == QLatin1String("menuitem") || m_type == QLatin1String("separator")) {
        if (!m_panel.isEmpty()) {
            QStyleOption panel;
            panel.rect = m_panel.toAlignedRect();
            panel.palette = QApplication::palette("QMenu");
            panel.state = QStyle::State_Enabled;
            style->drawPrimitive(QStyle::PE_PanelMenu, &panel, painter, nullptr);
        }
        QStyleOptionMenuItem opt;
        initMenuItem(&opt, m_type, m_text, m_shortcut, m_shortcutColumn, m_selected, isEnabled(), m_checkable, m_checked, m_subMenu);
        opt.rect = r;
        opt.styleObject = this;
        style->drawControl(QStyle::CE_MenuItem, &opt, painter, nullptr);
    } else if (m_type == QLatin1String("tooltip")) {
        QStyleOption opt;
        opt.rect = r;
        opt.palette = QApplication::palette("QTipLabel");
        opt.state = QStyle::State_Enabled;
        opt.styleObject = this;
        style->drawPrimitive(QStyle::PE_PanelTipLabel, &opt, painter, nullptr);
    }
}

class PlatinumQuickPlugin : public QQmlExtensionPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID QQmlExtensionInterface_iid)
public:
    void registerTypes(const char *uri) override
    {
        qmlRegisterType<PlatinumItem>(uri, 1, 0, "PlatinumItem");
    }
};

#include "platinumitem.moc"
