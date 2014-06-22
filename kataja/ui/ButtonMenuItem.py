# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QPointF as Pf

from kataja.ui.MenuItem import MenuItem
from kataja.singletons import ctrl, qt_prefs


class ButtonMenuItem(MenuItem, QtWidgets.QGraphicsSimpleTextItem):
    """

    """

    def __init__(self, parent, args):
        """

        :param parent:
        :param args:
        """
        QtWidgets.QGraphicsSimpleTextItem.__init__(self)
        MenuItem.__init__(self, parent, args)
        self.setParentItem(parent)
        self.setText(self._label_text)
        self.setBrush(ctrl.cm.ui())
        self.setZValue(52)


    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        cm = ctrl.cm
        if ctrl.has_focus(self) or self.activated:
            painter.setBrush(cm.active(cm.ui()))
            painter.setPen(cm.ui())
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            r = QtCore.QRectF(self._inner_bounding_rect.topRight() + Pf(-2, 5), QtCore.QSizeF(15, 15))
            painter.drawRect(r)
            painter.drawText(r, '\u21A9')
            self.setBrush(cm.paper())
        elif self._hovering:
            painter.setBrush(cm.hover(cm.ui()))
            painter.setPen(cm.ui())
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            self.setBrush(cm.ui())
        elif self.enabled:
            painter.setBrush(cm.ui_paper())
            painter.setPen(cm.ui())
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            self.setBrush(cm.ui())
        else:
            painter.setBrush(cm.ui_paper())
            painter.setPen(cm.ui())
            painter.drawRoundedRect(self._inner_bounding_rect, 5, 5)
            self.setBrush(cm.ui())
        painter.setPen(qt_prefs.no_pen)
        QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, option, widget)

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        MenuItem.hoverEnterEvent(self, event)
        QtWidgets.QGraphicsSimpleTextItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        MenuItem.hoverLeaveEvent(self, event)
        QtWidgets.QGraphicsSimpleTextItem.hoverLeaveEvent(self, event)
