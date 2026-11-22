// The Platinum Qt Quick Controls style's one C++ piece: an item that paints
// a control part with the application's QStyle, so Qt Quick menus, menu
// bars, tooltips and switch indicators are the same pixels as the widget
// ones (PLAN.md "Plan: Qt Quick menus, tooltips and switches"; public Qt
// API only, PLAN.md decision 13).
// SPDX-License-Identifier: BSD-2-Clause
#pragma once
#include <QIcon>
#include <QQuickPaintedItem>
#include <QUrl>

class PlatinumItem : public QQuickPaintedItem
{
    Q_OBJECT
    // What to draw: menu, menuitem, separator, menubar, menubaritem,
    // tooltip, checkbox, dialog, drawer, slidergroove, sliderthumb.
    Q_PROPERTY(QString elementType MEMBER m_type NOTIFY changed)
    Q_PROPERTY(QString text MEMBER m_text NOTIFY changed)
    Q_PROPERTY(QString shortcut MEMBER m_shortcut NOTIFY changed)
    Q_PROPERTY(bool selected MEMBER m_selected NOTIFY changed)
    Q_PROPERTY(bool pressed MEMBER m_pressed NOTIFY changed)
    // Keyboard focus (shown only for focus moved by the keyboard).
    Q_PROPERTY(bool keyboardFocus MEMBER m_keyboardFocus NOTIFY changed)
    // A menu row's icon: a theme icon name, or a file or qrc: URL.
    Q_PROPERTY(QString iconName MEMBER m_iconName NOTIFY changed)
    Q_PROPERTY(QUrl iconSource MEMBER m_iconSource NOTIFY changed)
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
    // Sliders: the orientation, and a thumb's visual position (0..1 along
    // the groove, as Qt Quick's visualPosition).
    Q_PROPERTY(bool horizontal MEMBER m_horizontal NOTIFY changed)
    Q_PROPERTY(qreal position MEMBER m_position NOTIFY changed)
    // Drawers: the window edge it slides from (Qt::Edge); its other sides
    // lie outside the window, so only the open side's frame is drawn.
    Q_PROPERTY(int edge MEMBER m_edge NOTIFY changed)
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
    // A combo box's width hint for these item texts, as QComboBox works it
    // out (its widest text through the style's CT_ComboBox): its open list
    // is at least that wide (finding 53).
    Q_INVOKABLE int comboWidthHint(const QStringList &texts) const;

Q_SIGNALS:
    void changed();
    void activeChanged();

protected:
    bool eventFilter(QObject *watched, QEvent *event) override;

private:
    void updateActive();
    void updateImplicitSize();
    QString m_type, m_text, m_shortcut;
    QString m_iconName;
    QUrl m_iconSource;
    QIcon icon() const;
    bool m_keyboardFocus = false;
    bool m_selected = false, m_pressed = false, m_checkable = false, m_checked = false, m_subMenu = false;
    bool m_first = false, m_last = false, m_combo = false, m_active = false;
    int m_shortcutColumn = 0;
    QRectF m_panel;
    bool m_horizontal = true;
    qreal m_position = 0;
    int m_edge = Qt::LeftEdge;
};
