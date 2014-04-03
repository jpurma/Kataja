'''
Created on 28.8.2013

@author: purma
'''
from kataja.ui.MenuItem import MenuItem
from kataja.Controller import colors, ctrl, qt_prefs
from PyQt5.QtCore import QPointF as Pf
from PyQt5 import QtWidgets, QtCore


class ButtonMenuItem(MenuItem, QtWidgets.QGraphicsSimpleTextItem):
    def __init__(self, parent, args):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self, parent=parent)
        MenuItem.__init__(self, parent, args)
        self.setText(self._label_text)
        self.setBrush(colors.ui)
        self.setZValue(52)


    def paint(self, painter, option, widget):
        if ctrl.has_focus(self) or self.activated:
            painter.setBrush(colors.ui_active)
            painter.setPen(colors.ui)
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            r = QtCore.QRectF(self._inner_bounding_rect.topRight() + Pf(-2, 5), QtCore.QSizeF(15, 15))
            painter.drawRect(r)
            painter.drawText(r, u'\u21A9')
            self.setBrush(colors.paper)
        elif self._hovering:
            painter.setBrush(colors.ui_hover)
            painter.setPen(colors.ui)
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            self.setBrush(colors.ui)
        elif self.enabled:
            painter.setBrush(colors.ui_background)
            painter.setPen(colors.ui)
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            self.setBrush(colors.ui)
        else:
            painter.setBrush(colors.ui_background)
            painter.setPen(colors.ui)
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            self.setBrush(colors.ui)
        painter.setPen(qt_prefs.no_pen)
        QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, option, widget)

    def hoverEnterEvent(self, event):
        MenuItem.hoverEnterEvent(self, event)
        QtWidgets.QGraphicsSimpleTextItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        MenuItem.hoverLeaveEvent(self, event)
        QtWidgets.QGraphicsSimpleTextItem.hoverLeaveEvent(self, event)
