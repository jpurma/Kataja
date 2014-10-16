# coding=utf-8
# #######################################################
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QPointF as Pf
from PyQt5.QtCore import Qt

from kataja.singletons import prefs, ctrl
from kataja.utils import to_tuple


class ControlPoint(QtWidgets.QGraphicsItem):
    """

    """

    def __init__(self, edge=None, index=-1, role=''):
        if prefs.touch:
            self._wh = 16
            self._xy = -8
        else:
            self._wh = 4
            self._xy = -2
        QtWidgets.QGraphicsItem.__init__(self)
        self.setCursor(Qt.CrossCursor)
        self.role = role
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
        if self._index > -1:
            p = self.host_edge.control_points[self._index]
            a = self.host_edge.adjust[self._index]
            p = Pf(p[0] + a[0], p[1] + a[1])
        elif self.role == 'start':
            p = Pf(self.host_edge.start_point[0], self.host_edge.start_point[1])
        elif self.role == 'end':
            p = Pf(self.host_edge.end_point[0], self.host_edge.end_point[1])
        elif self.role == 'label_start':
            print('updating label start cp')
            p = Pf(self.host_edge.get_cached_label_positions()[0].x(), self.host_edge.get_cached_label_positions()[0].y())
        elif self.role == 'label_end':
            p = Pf(self.host_edge.get_cached_label_positions()[1].x(), self.host_edge.get_cached_label_positions()[1].y())
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
        if self._index == -1:
            raise hell
        p = self.host_edge.control_points[self._index]
        return int(x - p[0]), int(y - p[1])
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
        if self._index > -1:
            self.host_edge.adjust_control_point(self._index, self._compute_adjust(), cp=True)
        elif self.role == 'start':
            self.host_edge.set_start_point(event.scenePos())
            self.host_edge.make_path()
            self.host_edge.update()
        elif self.role == 'end':
            self.host_edge.set_end_point(event.scenePos())
            self.host_edge.make_path()
            self.host_edge.update()


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

    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        """
        cm = ctrl.cm
        if self.pressed:
            pen = cm.active(cm.selection())
        elif self._hovering:
            pen = cm.hovering(cm.selection())
        else:
            pen = cm.ui()
        painter.setPen(pen)
        painter.drawRect(self._xy, self._xy, self._wh, self._wh)
