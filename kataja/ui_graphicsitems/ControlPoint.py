# coding=utf-8
# #######################################################
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
        self.setAcceptHoverEvents(True)
        self.setZValue(52)
        self._compute_position()
        self.status_tip = ""
        if self.role == g.START_POINT:
            self.status_tip = "Drag to move the starting point"
        elif self.role == g.END_POINT:
            self.status_tip = "Drag to move the ending point"
        elif self._index > -1:
            self.status_tip = "Drag to adjust the curvature of this line"
        elif self.role == g.LABEL_START:
            self.status_tip = "Drag along the line to adjust the anchor point of label"
        if ctrl.main.use_tooltips:
            self.setToolTip(self.status_tip)
        self.show()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def show(self):
        """ Assign as a watcher if necessary and make visible
        :return: None
        """
        if self.role == g.LABEL_START:
            ctrl.add_watcher('edge_label', self)

    def hide(self):
        """ Remove from watchers' list when control point is hidden
        :return: None
        """
        if self.role == g.LABEL_START:
            ctrl.remove_from_watch(self)

    def _compute_position(self):
        """
        :return:
        """
        if -1 < self._index < len(self.host.control_points):
            p = self.host.control_points[self._index]
            if self.host.curve_adjustment and len(self.host.curve_adjustment) > self._index:
                a = self.host.curve_adjustment[self._index]
                p = Pf(p[0] + a[0], p[1] + a[1])
            else:
                p = Pf(p[0], p[1])
        elif self.role == g.START_POINT:
            p = Pf(self.host.start_point[0], self.host.start_point[1])
        elif self.role == g.END_POINT:
            p = Pf(self.host.end_point[0], self.host.end_point[1])
        elif self.role == g.LABEL_START:
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
        """


        """
        ok = self._compute_position()
        self.update()
        return ok

    def _compute_adjust(self):
        x, y = to_tuple(self.pos())
        assert (self._index != -1)
        p = self.host.control_points[self._index]
        return int(x - p[0]), int(y - p[1])
        # print 'computed curve_adjustment:', self.curve_adjustment

    def click(self, event=None):
        """ Clicking a control point usually does nothing. These are more for dragging.
        :param event: some kind of mouse event
        :return: bool
        """
        pass
        return True  # consumes click

    def drag(self, event):
        """ Dragging a control point at least requires to update its coordinates and announcing the
        host object that things are a'changing. How this will be announced depends on control point's _role_.
        :param event: some kind of mouse event
        :return: None
        """
        if self.role == g.LABEL_START:
            d, point = self.host.get_closest_path_point(event.scenePos())
            self.host.label_item.label_start = d
        else:
            self.setPos(event.scenePos())
        if self._index > -1:
            self.host.shape_info.adjust_control_point(self._index, self._compute_adjust())
        elif self.role == g.START_POINT:
            self.host.set_start_point(event.scenePos())
            self.host.make_path()
            self.host.update()
        elif self.role == g.END_POINT:
            self.host.set_end_point(event.scenePos())
            self.host.make_path()
            self.host.update()

    def drop_to(self, x, y, recipient=None):
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
            if ctrl.dragged_set or (event.buttonDownScenePos(
                    QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
                self.drag(event)
                ctrl.graph_scene.dragging_over(event.scenePos())

    def mouseReleaseEvent(self, event):
        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                x, y = to_tuple(event.scenePos())
                self.drop_to(x, y, recipient=ctrl.drag_hovering_on)
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
        ctrl.set_status(self.status_tip)
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Remove hover effects for this piece.
        :param event: somekind of qt mouse event?
        """
        self._hovering = False
        ctrl.remove_status(self.status_tip)
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

    def watch_alerted(self, obj, signal, field_name, value):
        print(obj, signal, field_name, value)
