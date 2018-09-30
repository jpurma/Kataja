# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from PyQt5 import QtCore, QtGui, QtWidgets

from kataja.Shapes import draw_plus, draw_x, draw_triangle, draw_tailed_leaf, \
    draw_arrow_shape_from_points
from kataja.UIItem import UIGraphicsItem
from kataja.saved.Edge import Edge
from kataja.singletons import ctrl, qt_prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple

symbol_radius = 10

class TouchArea(UIGraphicsItem, QtWidgets.QGraphicsObject):
    """ Mouse sensitive areas connected to either nodes or edges between
    them. """
    __qt_type_id__ = next_available_type_id()
    clicked = QtCore.pyqtSignal()
    align_left = False
    action_slot = 'clicked'

    @classmethod
    def hosts_for_node(cls, node):
        return [node]

    @classmethod
    def select_condition(cls, host):
        return False

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host, click_action='', click_kwargs=None, drop_action='', drop_kwargs=None):
        """
        :param ConstituentNode host:
        :param string click_action: str, action to call when clicking toucharea
        :param dict click_kwargs: args to add to click_action call
        :param string drop_action: str, action to call when dropping something into
        :param dict drop_kwargs: args to add to drop_action call
        """
        UIGraphicsItem.__init__(self, host=host)
        QtWidgets.QGraphicsObject.__init__(self)
        self._dragging = False
        self._path = None
        self.start_point = None
        self.end_point = None
        self.z_value = 160
        self.setZValue(self.z_value)
        # Drawing flags defaults
        self._fill_path = False
        self._align_left = self.__class__.align_left
        self._below_node = False
        self.focusable = True
        self._visible = True
        self._hovering = False
        self._drag_hint = False
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.update_end_points()
        self.click_action = click_action
        self.click_kwargs = click_kwargs or {}
        self.drop_action = drop_action
        self.drop_kwargs = drop_kwargs or {}
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        if click_action and isinstance(click_action, str):
            action_obj = ctrl.ui.get_action(click_action)
            if action_obj:
                action_obj.connect_element(self)
        self.update_end_points()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def is_visible(self):
        return self._visible

    def contextual_color(self):
        if self._hovering:
            return ctrl.cm.hovering(ctrl.cm.ui())
        else:
            return ctrl.cm.ui()
            # return ctrl.cm.ui_tr()

    def sensitive_area(self):
        return self.boundingRect()

    def update_position(self):
        # if not self in ctrl.dragged:
        self.update_end_points()

    def drag(self, event):
        self._dragging = True
        ep = to_tuple(event.scenePos())
        self.end_point = ep
        self.start_point = ep
        self.setPos(ep[0], ep[1])
        self._path = None

    def update_end_points(self):
        """ """
        if not self.host:
            return
        if isinstance(self.host, Edge):
            x, y = self.host.end_point
            self.end_point = x, y
        else:
            x, y = self.host.current_scene_position
        self.end_point = x, y
        self.start_point = self.end_point
        self.setPos(self.end_point[0], self.end_point[1])
        self._path = None

    def __repr__(self):
        return '<toucharea %s>' % self.ui_type

    def remove(self):
        """ remove item from the scene but otherwise keep it intact """
        sc = self.scene()
        if sc:
            sc.removeItem(self)

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
                self._dragging = False
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
                ctrl.main.action_finished()  # @UndefinedVariable
            else:  # This is regular click on 'pressed' object

                self.click(event)
                self.update()
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

    def click(self, event=None):
        """
        :type event: QMouseEvent
         """
        self._dragging = False
        if self._drag_hint:
            return False
        ctrl.deselect_objects()
        self.clicked.emit()
        return True

    # self, N, R, merge_to_left, new_node_pos, merger_node_pos):

    def calculate_if_can_merge(self, dragged, top, node_list):
        """

        :param dragged:
        :param top:
        :param node_list:
        :return:
        """
        host = self.host
        if host is ctrl.dragged_focus:
            return False
        elif host in ctrl.dragged_set:
            return False
        elif host is ctrl.pressed:
            return False
        return True

    def dragged_over_by(self, dragged):
        if ctrl.drag_hovering_on is self:
            self.hovering = True
            return True
        elif self.accepts_drops(dragged):
            ctrl.set_drag_hovering(self)
            return True
        else:
            return False

    def accepts_drops(self, dragged):
        return self.drop_action  # and self.calculate_if_can_merge(dragged, None, None)

    @property
    def hovering(self):
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        if value and not self._hovering:
            self._hovering = True
            self.setZValue(1000)
        elif (not value) and self._hovering:
            self._hovering = False
            self.setZValue(self.z_value)
        self.update()

    def hoverEnterEvent(self, event):
        if not (self.hovering or ctrl.pressed or ctrl.scene_moving):
            self.prepareGeometryChange()
            self.hovering = True
            ctrl.ui.show_help(self, event)
        QtWidgets.QGraphicsObject.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        if self.hovering:
            self.prepareGeometryChange()
            self.hovering = False
            ctrl.ui.hide_help(self, event)
        QtWidgets.QGraphicsObject.hoverLeaveEvent(self, event)

    def dragEnterEvent(self, event):
        self.dragged_over_by(event.mimeData().text())
        event.accept()
        QtWidgets.QGraphicsObject.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        self.hovering = False
        event.accept()
        QtWidgets.QGraphicsObject.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        self.hovering = False
        event.accept()
        message = self.drop(event.mimeData().text())
        QtWidgets.QGraphicsObject.dropEvent(self, event)
        ctrl.main.action_finished(message)

    def drop(self, node_or_string):
        """
        :param dropped_node:
        """
        drop_args = {}
        if isinstance(node_or_string, str) and node_or_string.startswith('kataja:'):
            foo, command, ntype = node_or_string.split(':')
            ntype = int(ntype)
            drop_args['new_type'] = ntype
        else:
            drop_args['node_uid'] = getattr(node_or_string, 'uid')

        da = ctrl.ui.get_action(self.drop_action)
        if da:
            da.run_command(self.host, **drop_args)
        ctrl.deselect_objects()


class AbstractBelowTouchArea(TouchArea):
    def update_end_points(self):
        x, y = self.host.centered_scene_position
        y += self.host.height / 2 + symbol_radius
        self.end_point = x, y
        self.start_point = self.end_point
        self.setPos(self.end_point[0], self.end_point[1])

    def paint(self, painter, option, widget):
        if ctrl.pressed is self:
            pass
        c = self.contextual_color()
        if self._hovering:
            painter.setBrush(ctrl.cm.ui_tr())
        else:
            painter.setBrush(qt_prefs.no_brush)
        painter.setPen(c)
        draw_tailed_leaf(painter, 0, 0, symbol_radius)
        if self._hovering:
            painter.setPen(c)
            draw_plus(painter, 1.2 * symbol_radius, 0)


class AddTriangleTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return host.can_have_triangle()

    def __init__(self, host):
        super().__init__(host, click_action='add_triangle')

    def boundingRect(self):
        return QtCore.QRectF(-symbol_radius - 2, 0, symbol_radius * 2 + 4, symbol_radius + 2)

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        c = self.contextual_color()
        p = QtGui.QPen(c)
        p.setWidth(3 if self._hovering else 1)
        painter.setPen(p)
        draw_triangle(painter, 0, 0, r=symbol_radius)


class RemoveTriangleTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return host.is_triangle_host()

    def __init__(self, host):
        super().__init__(host, click_action='remove_triangle')

    def boundingRect(self):
        return QtCore.QRectF(-symbol_radius - 2, -symbol_radius - 2, symbol_radius * 2 + 4, symbol_radius * 2 + 4)

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        c = self.contextual_color()
        p = QtGui.QPen(c)
        p.setWidth(3 if self._hovering else 1)
        painter.setPen(p)
        draw_x(painter, 0, 0, symbol_radius)


class StartArrowTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return True

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'child'
        })

    def contextual_color(self):
        if self._hovering:
            return ctrl.cm.hovering(ctrl.cm.ui())
        else:
            return ctrl.cm.ui()

    def boundingRect(self):
        """
        :return:
        """
        return QtCore.QRectF(-10, -5, 20, 15)

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        c = self.contextual_color()
        painter.setPen(c)
        draw_plus(painter, -5, 5)
        # painter.setBrush(c)
        draw_arrow_shape_from_points(painter, -2, 0, 8, 7, c)
        if self._hovering:
            painter.drawRoundedRect(self.boundingRect(), 4, 4)

