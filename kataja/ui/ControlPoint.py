# coding=utf-8
# #######################################################
from PyQt5 import QtCore, QtWidgets

from kataja.Controller import prefs, ctrl
from kataja.utils import to_tuple
from PyQt5.QtCore import QPointF as Pf
from PyQt5.QtCore import Qt


class ControlPoint(QtWidgets.QGraphicsItem):
    """

    """

    def __init__(self, edge=None, index=0, point=(0, 0), adjust=(0, 0)):
        if prefs.touch:
            self._wh = 24
            self._xy = -12
        else:
            self._wh = 6
            self._xy = -3
        QtWidgets.QGraphicsItem.__init__(self)
        self.setCursor(Qt.CrossCursor)
        self.host_edge = edge
        self._index = index
        self.focusable = True
        self.draggable = True
        self.pressed = False
        self._hovering = False
        self.setAcceptHoverEvents(True)
        self.setZValue(52)
        self._compute_position()

    def _compute_position(self):
        p = self.host_edge.control_points[self._index]
        a = self.host_edge.adjust[self._index]
        print p, a
        p = Pf(p[0] + a[0], p[1] + a[1])
        self.setPos(p)

    def boundingRect(self):
        """


        :return:
        """
        return QtCore.QRectF(self._xy, self._xy, self._wh, self._wh)

    def update_position(self):
        """


        """
        self._compute_position()
        self.update()

    def _compute_adjust(self):
        x, y = to_tuple(self.pos())
        p = self.host_edge.control_points[self._index]
        return x - p[0], y - p[1]
        # print 'computed adjust:', self.adjust

    def click(self, event=None):
        """

        :param event:
        :return:
        """
        pass
        return True  # consumes click

    def drag(self, event):
        """

        :param event:
        """
        self.setPos(event.scenePos())
        self.host_edge.adjust_control_point(self._index, self._compute_adjust())

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        self._hovering = True
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        self._hovering = False
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)


    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        cm = ctrl.cm()
        if self.pressed:
            pen = cm.ui_active()
            # pen = colors.active
            painter.setBrush(cm.ui_active())
        elif self._hovering:
            pen = cm.ui_hover()
            painter.setBrush(cm.ui_hover())
        else:
            pen = cm.ui()
        painter.setPen(pen)
        painter.drawEllipse(self._xy, self._xy, self._wh, self._wh)