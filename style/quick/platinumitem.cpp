// SPDX-License-Identifier: BSD-2-Clause
#include "platinumitem.h"

#include <QApplication>
#include <QPainter>
#include <QQmlEngine>
#include <QQmlExtensionPlugin>
#include <QStyle>
#include <QStyleOption>
#include <QTextDocument>
#include <QToolTip>
#include <QWidget>

namespace
{
// QApplication::setStyle() tells only widgets (QEvent::StyleChange), and a
// Qt Quick app has none: one hidden, never shown widget hears it for every
// item.
QWidget *styleWatcher()
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

bool is(const QString &type, const char *name)
{
    return type == QLatin1String(name);
}

void initMenuItem(QStyleOptionMenuItem *opt, const QString &type, const QString &text, const QString &shortcut, int shortcutColumn, bool selected,
                  bool enabled, bool checkable, bool checked, bool subMenu)
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
    opt->menuItemType = is(type, "separator") ? QStyleOptionMenuItem::Separator
        : subMenu                              ? QStyleOptionMenuItem::SubMenu
                                               : QStyleOptionMenuItem::Normal;
    opt->checkType = checkable ? QStyleOptionMenuItem::NonExclusive : QStyleOptionMenuItem::NotCheckable;
    opt->checked = checked;
    opt->text = shortcut.isEmpty() ? text : text + QLatin1Char('\t') + shortcut;
    opt->reservedShortcutWidth = shortcutColumn;
    opt->maxIconWidth = 0;
}

void initMenuBarItem(QStyleOptionMenuItem *opt, const QString &text, bool selected, bool enabled)
{
    opt->palette = QApplication::palette("QMenuBar");
    opt->font = QApplication::font("QMenuBar");
    opt->fontMetrics = QFontMetrics(opt->font);
    opt->state = QStyle::State_None;
    if (enabled) {
        opt->state |= QStyle::State_Enabled;
    }
    // The widget menu bar marks the open title Selected | Sunken.
    if (selected && enabled) {
        opt->state |= QStyle::State_Selected | QStyle::State_Sunken;
    }
    opt->menuItemType = QStyleOptionMenuItem::Normal;
    opt->text = text;
}
} // namespace

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

void PlatinumItem::setApplicationStyle(const QString &name)
{
    if (qEnvironmentVariableIsSet("M9_QUICK_TEST")) {
        QApplication::setStyle(name);
    }
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

bool PlatinumItem::drawsText() const
{
    return is(m_type, "tooltip") && !Qt::mightBeRichText(m_text);
}

// QTipLabel's margin: 1 + the style's tooltip frame width.
int PlatinumItem::margin() const
{
    return m_active ? 1 + QApplication::style()->pixelMetric(QStyle::PM_ToolTipLabelFrameWidth) : 0;
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
    // The row's place, read by the style when there's no widget.
    setProperty("_platinum_shortcuts", m_shortcutColumn > 0);
    if (is(m_type, "menuitem") || is(m_type, "separator")) {
        QStyleOptionMenuItem opt;
        initMenuItem(&opt, m_type, m_text, m_shortcut, m_shortcutColumn, m_selected, isEnabled(), m_checkable, m_checked, m_subMenu);
        opt.styleObject = this;
        // What QMenu passes: the label's width and the font height; then it
        // adds the shortcut column to every row.
        const int label = opt.fontMetrics.boundingRect(QRect(), Qt::TextSingleLine | Qt::TextShowMnemonic, m_text).width();
        const QSize contents(is(m_type, "separator") ? 0 : label, opt.fontMetrics.height());
        const QSize size = style->sizeFromContents(QStyle::CT_MenuItem, &opt, contents, nullptr);
        setImplicitSize(size.width() + m_shortcutColumn, size.height());
    } else if (is(m_type, "menubaritem")) {
        QStyleOptionMenuItem opt;
        initMenuBarItem(&opt, m_text, m_selected, isEnabled());
        opt.styleObject = this;
        const QSize contents(opt.fontMetrics.horizontalAdvance(m_text), opt.fontMetrics.height());
        const QSize size = style->sizeFromContents(QStyle::CT_MenuBarItem, &opt, contents, nullptr);
        setImplicitSize(size.width(), size.height());
    } else if (is(m_type, "menubar")) {
        QStyleOption opt;
        const QSize size = style->sizeFromContents(QStyle::CT_MenuBar, &opt, QSize(0, 0), nullptr);
        setImplicitSize(0, size.height());
    } else if (is(m_type, "checkbox")) {
        setImplicitSize(style->pixelMetric(QStyle::PM_IndicatorWidth), style->pixelMetric(QStyle::PM_IndicatorHeight));
    } else if (drawsText()) {
        // As QTipLabel sizes itself: the text, its margin on each side, its
        // 1 px indent, and 1 px more width (1 more px height for a font
        // with a descent of 2).
        const QFontMetrics fm(QToolTip::font());
        const QRect text = fm.boundingRect(QRect(0, 0, 4096, 4096), Qt::AlignLeft | Qt::TextExpandTabs, m_text);
        const int m = margin();
        setImplicitSize(text.width() + 2 * m + 1 + 1, text.height() + 2 * m + ((fm.descent() == 2 && fm.ascent() >= 11) ? 1 : 0));
    }
}

void PlatinumItem::paint(QPainter *painter)
{
    if (!m_active) {
        return;
    }
    QStyle *style = QApplication::style();
    const QRect r(0, 0, int(width()), int(height()));
    setProperty("_platinum_first", m_first);
    setProperty("_platinum_last", m_last);
    setProperty("_platinum_combo", m_combo);
    setProperty("_platinum_shortcuts", m_shortcutColumn > 0);
    if (is(m_type, "menu")) {
        QStyleOption opt;
        opt.rect = r;
        opt.palette = QApplication::palette("QMenu");
        opt.state = QStyle::State_Enabled;
        opt.styleObject = this;
        style->drawPrimitive(QStyle::PE_PanelMenu, &opt, painter, nullptr);
    } else if (is(m_type, "menuitem") || is(m_type, "separator")) {
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
    } else if (is(m_type, "menubar")) {
        QStyleOptionMenuItem opt;
        opt.rect = r;
        opt.palette = QApplication::palette("QMenuBar");
        opt.state = QStyle::State_Enabled;
        opt.menuItemType = QStyleOptionMenuItem::EmptyArea;
        opt.styleObject = this;
        style->drawControl(QStyle::CE_MenuBarEmptyArea, &opt, painter, nullptr);
    } else if (is(m_type, "menubaritem")) {
        QStyleOptionMenuItem opt;
        initMenuBarItem(&opt, m_text, m_selected, isEnabled());
        opt.rect = r;
        opt.styleObject = this;
        style->drawControl(QStyle::CE_MenuBarItem, &opt, painter, nullptr);
    } else if (is(m_type, "tooltip")) {
        QStyleOption opt;
        opt.rect = r;
        opt.palette = QApplication::palette("QTipLabel");
        opt.state = QStyle::State_Enabled;
        opt.styleObject = this;
        style->drawPrimitive(QStyle::PE_PanelTipLabel, &opt, painter, nullptr);
        if (drawsText()) {
            // QTipLabel: its palette and font, the text left-aligned inside
            // the margin and its 1 px indent, in the tooltip text color.
            const int m = margin();
            painter->setFont(QToolTip::font());
            style->drawItemText(painter, r.adjusted(m + 1, m, -m, -m), Qt::AlignLeft | Qt::TextExpandTabs, QToolTip::palette(), true, m_text,
                                QPalette::ToolTipText);
        }
    } else if (is(m_type, "checkbox")) {
        QStyleOptionButton opt;
        opt.rect = r;
        opt.palette = QApplication::palette("QCheckBox");
        opt.state = m_checked ? QStyle::State_On : QStyle::State_Off;
        if (isEnabled()) {
            opt.state |= QStyle::State_Enabled;
        }
        if (m_pressed) {
            opt.state |= QStyle::State_Sunken;
        }
        opt.styleObject = this;
        style->drawPrimitive(QStyle::PE_IndicatorCheckBox, &opt, painter, nullptr);
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
