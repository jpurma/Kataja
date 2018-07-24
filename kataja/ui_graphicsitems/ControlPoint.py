# coding=utf-8
# #######################################################
import math
from PyQt5 import QtCore, QtWidgets, QtGui

from PyQt5.QtCore import QPointF as Pf
from PyQt5.QtCore import Qt
from kataja.singletons import prefs, ctrl
from kataja.utils import to_tuple
from kataja.UIItem import UIGraphicsItem
import kataja.globals as g
from kataja.uniqueness_generator import next_available_type_id


class ControlPoint(UIGraphicsItem, QtWidgets.QGraphicsItem):
    """

    """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, edge, index=-1, role=''):
        UIGraphicsItem.__init__(self, host=edge, role=role)
        QtWidgets.QGraphicsItem.__init__(self)
        print('creating control_point, role is: ', role)
        if prefs.touch:
            self._wh = 12
            self._xy = -6
            self.round = True
            self.setCursor(Qt.PointingHandCursor)
        else:
            self._wh = 4
            self._xy = -2
            self.round = True
            self.setCursor(Qt.CrossCursor)
        self._index = index
        self.focusable = True
        self.pressed = False
        self._hovering = False
        self.being_dragged = False
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)

        self.setZValue(52)
        self._compute_position()
        self.k_tooltip = ""
        if self.role == g.START_POINT:
            self.k_tooltip = "Drag to move the starting point"
        elif self.role == g.END_POINT:
            self.k_tooltip = "Drag to move the ending point"
        elif self.role == g.CURVE_ADJUSTMENT:
            self.k_tooltip = "Drag to adjust the curvature of this line"
        elif self.role == g.LABEL_START:
            self.k_tooltip = "Drag along the line to adjust the anchor point of label"
            if prefs.touch:
                self._wh = 6
                self._xy = -3
        self.show()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def _compute_position(self):
        """
        :return:
        """
        if self.role == g.CURVE_ADJUSTMENT and self._index < len(
                self.host.path.adjusted_control_points):
            p = Pf(*self.host.path.adjusted_control_points[self._index])
        elif self.role == g.START_POINT:
            p = Pf(self.host.start_point[0], self.host.start_point[1])
        elif self.role == g.END_POINT:
            p = Pf(self.host.end_point[0], self.host.end_point[1])
        elif self.role == g.LABEL_START and self.host.label_item:
            c = self.host.label_item.get_label_start_pos()
            p = Pf(c.x(), c.y())
        else:
            return False
        self.setPos(p)
        return True

    def boundingRect(self):
        """
        :return:
        """
        return QtCore.QRectF(self._xy, self._xy, self._wh, self._wh)

    def update_position(self):
        ok = self._compute_position()
        self.update()
        return ok

    def _compute_adjust(self):
        x, y = to_tuple(self.pos())
        assert (self._index != -1)
        p = self.host.path.control_points[self._index]
        return int(x - p[0]), int(y - p[1])
        # print 'computed curve_adjustment:', self.curve_adjustment

    def _compute_adjust_from_pos(self, scene_pos):
        x, y = to_tuple(scene_pos)
        assert (self._index != -1)
        cx, cy = self.host.path.control_points[self._index]
        x_adjust = int(x - cx)
        y_adjust = int(y - cy)
        if self._index == 0:
            sx, sy = self.host.start_point
        else:
            sx, sy = self.host.end_point
        sx_to_cx = cx - sx
        sy_to_cy = cy - sy
        line_rad = math.atan2(sy_to_cy, sx_to_cx)
        line_dist = math.hypot(sx_to_cx, sy_to_cy)
        adj_rad = math.atan2(y_adjust, x_adjust)
        adj_dist = math.hypot(x_adjust, y_adjust)
        if line_dist != 0:
            relative_dist = adj_dist / line_dist
        else:
            relative_dist = adj_dist
        relative_rad = adj_rad - line_rad
        return relative_dist, relative_rad

    def click(self, event=None):
        """ Clicking a control point usually does nothing. These are more for dragging.
        :param event: some kind of mouse event
        :return: bool
        """
        pass
        return True  # consumes click

    def drag(self, event):
        """ Dragging a control point at least requires to update its coordinates and announcing the
        host object that things are a'changing. How this will be announced depends on control
        point's _role_.
        :param event: some kind of mouse event
        :return: None
        """
        scenepos = event.scenePos()
        if self.role == g.LABEL_START:
            d, point = self.host.path.get_closest_path_point(scenepos)
            self.host.label_item.label_start = d
        else:
            self.setPos(scenepos)
        if self.role == g.CURVE_ADJUSTMENT:
            rdist, rrad = self._compute_adjust_from_pos(scenepos)
            self.host.adjust_control_point(self._index, rdist, rrad)
        elif self.role == g.START_POINT:
            self.host.set_start_point(scenepos.x(), scenepos.y())
        elif self.role == g.END_POINT:
            self.host.set_end_point(scenepos.x(), scenepos.y())
        elif self.role == g.MIDDLE_POINT:
            self.host.set_middle_point(scenepos.x(), scenepos.y())
        self.being_dragged = True

    def drop_to(self, x, y, recipient=None, shift_down=False):
        """ Dragging ends, possibly by dropping over another object.
        :param x: scene x coordinate
        :param y: scene y coordinate
        :param recipient: object that receives the dropped _control point_
        """
        if recipient:
            # recipient.accept_drop(self)
            if self.role == g.START_POINT:
                self.host.connect_start_to(recipient)
            elif self.role == g.END_POINT:
                self.host.connect_end_to(recipient)

    def mousePressEvent(self, event):
        ctrl.press(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if ctrl.pressed is self:
            if self.being_dragged or (event.buttonDownScenePos(
                    QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
                self.drag(event)
                ctrl.graph_scene.dragging_over(event.scenePos())

    def mouseReleaseEvent(self, event):
        if ctrl.pressed is self:
            ctrl.release(self)
            if self.being_dragged:
                shift = event.modifiers() == QtCore.Qt.ShiftModifier
                x, y = to_tuple(event.scenePos())
                self.drop_to(int(x), int(y), recipient=ctrl.drag_hovering_on, shift_down=shift)
                self.being_dragged = False
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
                ctrl.main.action_finished()  # @UndefinedVariable
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        """ Trigger and update hover effects.
        :param event: somekind of qt mouse event?
        """
        self._hovering = True
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Remove hover effects for this piece.
        :param event: somekind of qt mouse event?
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
        if self.round:
            if self.pressed:
                p = QtGui.QPen(cm.active(cm.ui_tr()))
            elif self._hovering:
                p = QtGui.QPen(cm.hovering(cm.ui_tr()))
            else:
                p = QtGui.QPen(cm.ui_tr())

            if self.role == g.START_POINT or self.role == g.END_POINT:
                p.setWidth(4)
                painter.setPen(p)
                painter.drawEllipse(self._xy, self._xy, self._wh, self._wh)
            elif self.role == g.LABEL_START:
                p.setWidth(1)
                painter.setPen(p)
                painter.drawRect(self._xy, self._xy, self._wh, self._wh)
            else:
                p.setWidth(2)
                painter.setPen(p)
                painter.drawEllipse(self._xy, self._xy, self._wh, self._wh)
            #
            # if self.pressed:
            # painter.setBrush(cm.active(cm.ui_tr()))
            # elif self._hovering:
            # painter.setBrush(cm.hovering(cm.ui_tr()))
            # else:
            # painter.setBrush(cm.ui_tr())
            # painter.setPen(qt_prefs.no_pen)
            # painter.drawEllipse(self._xy, self._xy, self._wh, self._wh)
        else:
            if self.pressed:
                pen = cm.active(cm.selection())
            elif self._hovering:
                pen = cm.hovering(cm.selection())
            else:
                pen = cm.ui()
            painter.setPen(pen)
            painter.drawRect(self._xy, self._xy, self._wh, self._wh)
