# coding=utf-8
from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl


class CheckBox(QtWidgets.QGraphicsItem):
    """

    """

    def __init__(self, parent, marker='X'):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self._hover = False
        self.setAcceptHoverEvents(False)
        self.setZValue(52)
        self.marker = marker

    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        """
        QtWidgets.QGraphicsItem.paint()
        r = QtCore.QRectF(-8, -4, 15, 15)
        cm = ctrl.cm
        painter.setPen(cm.ui())
        if self._hover:
            painter.setBrush(cm.hovering(cm.ui()))
            painter.drawRect(r)
            painter.setPen(cm.ui())
            painter.drawText(r, self.marker)
        elif self.parentItem().checked:
            painter.setBrush(cm.ui_secondary())
            painter.drawRect(r)
            painter.setPen(cm.ui())
            painter.drawText(r, self.marker)
        else:
            painter.setBrush(cm.paper())
            painter.drawRect(r)

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        self._hover = True
        self.parentItem().hoverLeaveEvent(event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        self._hover = False

    def mousePressEvent(self, event):
        """

        :param event:
        """
        self.parentItem().selectOption()
        ctrl.ui_pressed = self

    def mouseReleaseEvent(self, event):
        """

        :param event:
        """
        ctrl.ui_pressed = None

    def boundingRect(self):
        """


        :return:
        """
        return QtCore.QRectF(-8, -4, 15, 15)
