// The Platinum Qt Quick Controls style's one C++ piece: an item that paints
// a control part with the application's QStyle, so Qt Quick menus, menu
// bars, tooltips and switch indicators are the same pixels as the widget
// ones (PLAN.md "Plan: Qt Quick menus, tooltips and switches"; public Qt
// API only, PLAN.md decision 13).
// SPDX-License-Identifier: BSD-2-Clause
#pragma once
#include <QQuickPaintedItem>

class PlatinumItem : public QQuickPaintedItem
{
    Q_OBJECT
    // What to draw: menu, menuitem, separator, menubar, menubaritem,
    // tooltip, checkbox.
    Q_PROPERTY(QString elementType MEMBER m_type NOTIFY changed)
    Q_PROPERTY(QString text MEMBER m_text NOTIFY changed)
    Q_PROPERTY(QString shortcut MEMBER m_shortcut NOTIFY changed)
    Q_PROPERTY(bool selected MEMBER m_selected NOTIFY changed)
    Q_PROPERTY(bool pressed MEMBER m_pressed NOTIFY changed)
    Q_PROPERTY(bool checkable MEMBER m_checkable NOTIFY changed)
    Q_PROPERTY(bool checked MEMBER m_checked NOTIFY changed)
    Q_PROPERTY(bool subMenu MEMBER m_subMenu NOTIFY changed)
    // Where a menu row is, passed to the style (it can't see a QMenu here).
    Q_PROPERTY(bool first MEMBER m_first NOTIFY changed)
    Q_PROPERTY(bool last MEMBER m_last NOTIFY changed)
    Q_PROPERTY(bool combo MEMBER m_combo NOTIFY changed)
    // The menu's shortcut column (its widest shortcut), as QMenu adds it to
    // every row; and this row's own shortcut width, to find it.
    Q_PROPERTY(int shortcutColumn MEMBER m_shortcutColumn NOTIFY changed)
    Q_PROPERTY(int shortcutWidth READ shortcutWidth NOTIFY changed)
    // The whole menu panel in this row's coordinates: the row paints its
    // slice of the panel first, as QMenu paints rows over its panel (the
    // text then blends with the same pixels).
    Q_PROPERTY(QRectF panel MEMBER m_panel NOTIFY changed)
    // True while the application's QStyle is Platinum: the controls fall
    // back to KDE's own look otherwise (another style, or a Qt Quick app
    // without widgets).
    Q_PROPERTY(bool active READ active NOTIFY activeChanged)
    // Tooltips: true when the text is plain, so the item draws it as
    // QTipLabel does (rich text is left to KDE's label, inside `margin`).
    Q_PROPERTY(bool drawsText READ drawsText NOTIFY changed)
    Q_PROPERTY(int margin READ margin NOTIFY activeChanged)
public:
    explicit PlatinumItem(QQuickItem *parent = nullptr);
    void paint(QPainter *painter) override;
    bool active() const { return m_active; }
    int shortcutWidth() const;
    bool drawsText() const;
    int margin() const;
    // For dev/ test scenes only (does nothing unless M9_QUICK_TEST is set):
    // switches the application's QStyle.
    Q_INVOKABLE static void setApplicationStyle(const QString &name);

Q_SIGNALS:
    void changed();
    void activeChanged();

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    void updateActive();
    void updateImplicitSize();
    QString m_type, m_text, m_shortcut;
    bool m_selected = false, m_pressed = false, m_checkable = false, m_checked = false, m_subMenu = false;
    bool m_first = false, m_last = false, m_combo = false, m_active = false;
    int m_shortcutColumn = 0;
    QRectF m_panel;
};
