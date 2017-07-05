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

import math

from PyQt5 import QtCore, QtGui, QtWidgets

import kataja.globals as g
from kataja.Shapes import draw_plus, draw_leaf, draw_x, draw_triangle, draw_tailed_leaf, \
    draw_arrow_shape_from_points, SHAPE_PRESETS
from kataja.UIItem import UIGraphicsItem
from kataja.saved.Edge import Edge
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple
from math import sqrt

symbol_radius = 10
symbol_radius_sqr = sqrt(2) * symbol_radius

LEAF_BR = QtCore.QRectF(-symbol_radius_sqr, -symbol_radius_sqr, symbol_radius_sqr * 2,
                        symbol_radius_sqr * 2)
PLUS_BR = QtCore.QRectF(-1, -1, 4, 4)


class TouchArea(UIGraphicsItem, QtWidgets.QGraphicsObject):
    """ Mouse sensitive areas connected to either nodes or edges between
    them. """
    __qt_type_id__ = next_available_type_id()
    clicked = QtCore.pyqtSignal()
    align_left = False

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

    def set_tip(self, tip):
        self.k_tooltip = tip

    def contextual_color(self):
        if self._hovering:
            return ctrl.cm.hovering(ctrl.cm.ui())
        else:
            return ctrl.cm.ui()
            # return ctrl.cm.ui_tr()

    def boundingRect(self):
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        # Just the bounding rect of end spot ellipse
        return LEAF_BR

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
        return self.drop_action #and self.calculate_if_can_merge(dragged, None, None)

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
        if (not self._hovering) and not ctrl.pressed:
            self.prepareGeometryChange()
            self.hovering = True
            ctrl.ui.show_help(self, event)
        QtWidgets.QGraphicsObject.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        if self._hovering:
            self.prepareGeometryChange()
            self.hovering = False
            ctrl.ui.show_help(self, event)
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
        if isinstance(node_or_string, str) and node_or_string.startswith('kataja:'):
            foo, command, ntype = node_or_string.split(':')
            ntype = int(ntype)
            self.drop_args['new_type'] = ntype
        else:
            self.drop_args['node_uid'] = getattr(node_or_string, 'uid')

        da = ctrl.ui.get_action(self.drop_action)
        if da:
            da.run_command(self.host, **self.drop_args)
        ctrl.deselect_objects()


class DeleteArrowTouchArea(TouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return host.has_arrow()

    @classmethod
    def drop_condition(cls, host):
        return host.dragging_my_arrow()

    def __init__(self, host):
        super().__init__(host, click_action='delete_arrow', drop_action='delete_arrow')

    def paint(self, painter, option, widget):
        """
        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        painter.setPen(self.contextual_color())
        draw_x(painter, 0, 0, symbol_radius)


class AbstractBelowTouchArea(TouchArea):
    def update_end_points(self):
        x, y = self.host.centered_scene_position
        y += self.host.height / 2 + symbol_radius
        self.end_point = x, y
        self.start_point = self.end_point
        self.setPos(self.end_point[0], self.end_point[1])

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
        if self._hovering:
            painter.setBrush(ctrl.cm.ui_tr())
        else:
            painter.setBrush(qt_prefs.no_brush)
        painter.setPen(c)
        draw_tailed_leaf(painter, 0, 0, symbol_radius)
        if self._hovering:
            painter.setPen(c)
            draw_plus(painter, 1.2 * symbol_radius, 0)


class AddBelowTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing and host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return (not ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE)) and host.can_have_as_child()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'child'
        }, drop_action='connect_node', drop_kwargs={
            'position': 'child'
        })


class AddTriangleTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return host.can_have_triangle()

    def __init__(self, host):
        super().__init__(host, click_action='add_triangle')

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
        draw_triangle(painter, 0, 0)
        if self._hovering:
            painter.setPen(c)
            draw_triangle(painter, 0, -5, 6)


class RemoveTriangleTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return host.is_triangle_host()

    def __init__(self, host):
        super().__init__(host, click_action='remove_triangle')

    def update_end_points(self):
        x, y = self.host.centered_scene_position
        lbr = self.host.label_object.boundingRect()
        y += self.host.label_object.triangle_y + lbr.top() + symbol_radius + 2
        self.end_point = x, y
        self.start_point = self.end_point
        self.setPos(x, y)

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
        # draw_triangle(painter, 0, 0)
        draw_x(painter, 0, 0, symbol_radius / 2)
        if self._hovering:
            p = QtGui.QPen(c)
            p.setWidth(2)
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


class AbstractBranchingTouchArea(TouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """

    def boundingRect(self):
        sx, sy = self.start_point
        ex, ey = self.end_point
        br = QtCore.QRectF(0, 0, sx - ex, sy - ey)
        if self._hovering:
            br = br.united(LEAF_BR).united(PLUS_BR.translated(1.2 * symbol_radius, 0))
        return br


class MergeToTop(AbstractBranchingTouchArea):
    """ TouchArea that connects to nodes and has \-shape.  """
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and not host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host):
        super().__init__(host, click_action='merge_to_top', click_kwargs={
            'left': True
        })

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """

        sx, sy = self.host.magnet(0)
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            ex = sx - 20  # 75
            ey = sy - 10
            self.end_point = ex, ey
        self.setPos(self.end_point[0], self.end_point[1])

    def boundingRect(self):
        dx = self.start_point[0] - self.end_point[0]
        dy = self.start_point[1] - self.end_point[1]
        if self._hovering:
            if len(self.host.trees) != 1:
                return QtCore.QRectF(-2, -2, dx + 4, dy + 4).united(LEAF_BR)
            else:
                top = list(self.host.trees)[0].top
                lmx, lmy = top.magnet(5)
                scene_point = QtCore.QPointF(lmx, lmy)
                end_point = self.mapFromScene(scene_point)
                path = QtGui.QPainterPath(QtCore.QPointF(dx, dy))
                path.quadTo(QtCore.QPointF(end_point.x() - 200, end_point.y()), end_point)
                return path.controlPointRect().adjusted(-4, -4, 0, 0)
        else:
            return QtCore.QRectF(0, 0, dx, dy)

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
        dx = self.start_point[0] - self.end_point[0]
        dy = self.start_point[1] - self.end_point[1]
        l = QtCore.QLineF(dx, dy, 0, 0)

        if self._hovering:
            if len(self.host.trees) != 1:
                painter.drawLine(l)
                painter.save()
                painter.setBrush(ctrl.cm.ui())
                painter.rotate(20)
                draw_leaf(painter, 0, 0, symbol_radius)
                painter.restore()
                draw_plus(painter, 1.2 * symbol_radius, 0)
                return
            else:
                top = list(self.host.trees)[0].top
                lmx, lmy = top.magnet(5)
                scene_point = QtCore.QPointF(lmx, lmy)
                end_point = self.mapFromScene(scene_point)
                path = QtGui.QPainterPath(QtCore.QPointF(dx, dy))
                path.quadTo(QtCore.QPointF(end_point.x() - 200, end_point.y()), end_point)
                painter.drawPath(path)
                l = QtCore.QLineF(QtCore.QPointF(end_point.x() - 200, end_point.y()), end_point)
        else:
            painter.drawLine(l)

        l2x = l.p2().x()
        l2 = l.p2()
        l2y = l.p2().y()
        head_size = 8.0
        back = head_size / -2
        # Draw the arrows if there's enough room.
        ll = l.length()
        if ll >= 1 and ll + back > 0:
            angle = math.acos(l.dx() / ll)  # acos has to be <= 1.0
        else:
            return
        prop = back / ll
        if l.dy() >= 0:
            angle = (math.pi * 2.0) - angle
        destArrowP1 = QtCore.QPointF((math.sin(angle - math.pi / 3) * head_size) + l2x,
                                     (math.cos(angle - math.pi / 3) * head_size) + l2y)
        destArrowP2 = QtCore.QPointF((math.sin(angle - math.pi + math.pi / 3) * head_size) + l2x,
                                     (math.cos(angle - math.pi + math.pi / 3) * head_size) + l2y)
        l2c = QtCore.QPointF(l.dx() * prop + l2x, l.dy() * prop + l2y)
        painter.setBrush(c)
        painter.drawPolygon(QtGui.QPolygonF([l2, destArrowP1, l2c, destArrowP2]))


class AbstractLeftBranching(AbstractBranchingTouchArea):
    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        e = self.host
        sx, sy = to_tuple(e.get_point_at(0.4))
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            d = e.get_angle_at(0.4)
            d -= 60  # 75
            angle = math.radians(-d)
            dx = math.cos(angle)
            dy = math.sin(angle)
            l = 12
            x = sx + dx * l
            y = sy + dy * l
            self.end_point = x, y
        self.setPos(self.end_point[0], self.end_point[1])

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
        sx, sy = self.start_point
        ex, ey = self.end_point
        painter.drawLine(sx - ex, sy - ey, 0, 0)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            painter.rotate(-20)
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class LeftAddSibling(AbstractLeftBranching):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add sibling node to left'
    align_left = True

    @classmethod
    def hosts_for_node(cls, node):
        return node.get_edges_up(similar=True, visible=True)

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode

    @classmethod
    def drop_condition(cls, host):
        return ctrl.free_drawing_mode and ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE)

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_left'
        }, drop_action='connect_node', drop_kwargs={
            'position': 'sibling_left'
        })


class LeftAddInnerSibling(AbstractLeftBranching):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def hosts_for_node(cls, node):
        return node.get_edges_up(similar=True, visible=True)

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and host.end.inner_add_sibling()

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_left',
            'new_type': g.CONSTITUENT_NODE
        })


# ############## Right branching ######################


class AbstractRightBranching(AbstractBranchingTouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """
    k_tooltip = 'Add sibling node to right'

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        e = self.host
        sx, sy = to_tuple(e.get_point_at(0.4))
        self.start_point = sx, sy
        if end_point:
            ex, ey = end_point
            self.end_point = end_point
        else:
            d = e.get_angle_at(0.4)
            d += 60  # 75
            angle = math.radians(-d)
            dx = math.cos(angle)
            dy = math.sin(angle)
            l = 12
            ex = sx + dx * l
            ey = sy + dy * l
            self.end_point = ex, ey
        self.setPos(ex, ey)

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
        sx, sy = self.start_point
        ex, ey = self.end_point

        painter.drawLine(sx - ex, sy - ey, 0, 0)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            painter.rotate(-160)
            print('painting leaf at ', 0, 0, symbol_radius)
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class RightAddSibling(AbstractRightBranching):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add sibling node to right'
    align_left = True

    @classmethod
    def hosts_for_node(cls, node):
        return node.get_edges_up(similar=True, visible=True)

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode

    @classmethod
    def drop_condition(cls, host):
        return ctrl.free_drawing_mode and ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE)

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_right'
        }, drop_action='connect_node', drop_kwargs={
            'position': 'sibling_right'
        })


class RightAddInnerSibling(AbstractRightBranching):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def hosts_for_node(cls, node):
        return node.get_edges_up(similar=True, visible=True)

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and host.end.inner_add_sibling()

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_right',
            'new_type': g.CONSTITUENT_NODE
        })


class AbstractJointedTouchArea(TouchArea):
    """ TouchArea that connects to nodes and has ^-shape. Used to add nodes
    to top of the trees. """

    def boundingRect(self):
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        return self._path.controlPointRect()\
            .united(LEAF_BR)\
            .united(PLUS_BR.translated(1.2 * symbol_radius, 0))

    def shape(self):
        """ Shape is used for collisions and it shouldn't go over the originating node. So use
        only the last half, starting from the "knee" of the shape.
        :return:
        """
        path = QtGui.QPainterPath()
        # Bounding rect that includes the tail and end spot ellipse
        sx, sy = self.start_point
        ex, ey = self.end_point

        sx -= ex
        sy -= ey
        sx /= 2.0
        ex, ey = 0, 0
        e2 = symbol_radius_sqr * 2
        if sx < ex:
            w = max((ex - sx + symbol_radius_sqr, e2))
            x = min((sx, ex - symbol_radius_sqr))
        else:
            w = max((sx - ex + symbol_radius_sqr, e2))
            x = ex - symbol_radius_sqr
        if sy < ey:
            h = max((ey - sy + symbol_radius_sqr, e2))
            y = min((sy, ey - symbol_radius_sqr))
        else:
            h = max((sy - ey + symbol_radius_sqr, e2))
            y = ey - symbol_radius_sqr
        r = QtCore.QRectF(x, y, w, h)
        path.addRect(r)
        return path

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.settings.get_edge_setting('shape_name', edge_type=g.CONSTITUENT_EDGE)
        self._fill_path = ctrl.settings.get_shape_setting('fill', edge_type=g.CONSTITUENT_EDGE)
        sx, sy = self.host.magnet(2)
        self.start_point = sx, sy
        h2 = self.host.__class__.height / 2
        cw = self.host.__class__.width
        hw_ratio = float(prefs.edge_height - h2) / (prefs.edge_width or 1)
        if not end_point:
            good_width = max((prefs.edge_width * 2, self.host.width / 2 + cw))
            if self._align_left:
                self.end_point = sx - good_width, sy
            else:
                self.end_point = sx + good_width, sy
        self.setPos(self.end_point[0], self.end_point[1])

        sx, sy = self.start_point
        ex, ey = self.end_point
        sx -= ex
        sy -= ey
        ex, ey = 0, 0
        line_middle_point = sx / 2.0, sy - hw_ratio * abs(sx)
        adjust = []
        shape = SHAPE_PRESETS[shape_name]
        if self._align_left:
            path1 = shape.path(line_middle_point, (sx, sy),
                               alignment=g.RIGHT, curve_adjustment=adjust)[0]
            path1.moveTo(sx, sy)
            path2 = shape.path(line_middle_point, (ex, ey),
                               alignment=g.LEFT, curve_adjustment=adjust)[0]
        else:
            path1 = shape.path(line_middle_point, (ex, ey),
                               alignment=g.RIGHT, curve_adjustment=adjust)[0]
            path1.moveTo(ex, ey)
            path2 = shape.path(line_middle_point, (sx, sy),
                               alignment=g.LEFT, curve_adjustment=adjust)[0]
        self._path = path1 | path2


class LeftAddTop(AbstractJointedTouchArea):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add node to left'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing and host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE) and ctrl.free_drawing and host.is_top_node()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'top_left',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'top_left'
        })

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
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            painter.rotate(20)
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class RightAddTop(AbstractJointedTouchArea):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add node to right'

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing and host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE) and ctrl.free_drawing and host.is_top_node()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'top_right',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'top_right'
        })

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
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            painter.rotate(-160)
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class AbstractChildTouchArea(TouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes. """

    def boundingRect(self):
        """


        :return:
        """
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        # Bounding rect that includes the tail and end spot ellipse
        sx, sy = self.start_point
        ex, ey = self.end_point
        w = sx - ex
        h = sy - ey
        r = QtCore.QRectF(0, 0, w, h)
        return r.united(LEAF_BR).united(PLUS_BR.translated(symbol_radius * 1.2, 0))

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))


class AbstractLeftAddChild(AbstractChildTouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes."""

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.settings.get_edge_setting('shape_name', edge_type=g.CONSTITUENT_EDGE)
        self._fill_path = ctrl.settings.get_shape_setting('fill', edge_type=g.CONSTITUENT_EDGE)
        sx, sy = self.host.magnet(7)
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
            ex, ey = end_point
        else:
            ex = sx - 20  # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(ex, ey)
        sx -= ex
        sy -= ey
        adjust = []
        self._path = SHAPE_PRESETS[shape_name].path((sx, sy), (0, 0), alignment=g.LEFT,
                                                    curve_adjustment=adjust)[0]

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        print(self)
        if ctrl.pressed is self:
            pass
        c = self.contextual_color()
        painter.setPen(c)
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            painter.rotate(20)
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class LeftAddUnaryChild(AbstractLeftAddChild):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to left'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and host.has_one_child()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.free_drawing_mode and host.has_one_child() and ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE)

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'child_left',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'child_left'
        })


class LeftAddLeafSibling(AbstractLeftAddChild):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to left'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and host.is_leaf()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.free_drawing_mode and ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE) and host.is_leaf()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_left',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'sibling_left'
        })


class AbstractRightAddChild(AbstractChildTouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes. """
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to right'

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.settings.get_edge_setting('shape_name', edge_type=g.CONSTITUENT_EDGE)
        self._fill_path = ctrl.settings.get_shape_setting('fill', edge_type=g.CONSTITUENT_EDGE)
        sx, sy = self.host.magnet(11)
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
            ex, ey = end_point
        else:
            ex = sx + 20  # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(ex, ey)
        ex, ey = self.end_point
        sx -= ex
        sy -= ey
        adjust = []
        self._path = SHAPE_PRESETS[shape_name].path((sx, sy), (0, 0), alignment=g.RIGHT,
                                                    curve_adjustment=adjust)[0]

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        print(self)
        if ctrl.pressed is self:
            pass
        c = self.contextual_color()
        painter.setPen(c)
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            painter.rotate(-160)
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class RightAddUnaryChild(AbstractRightAddChild):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to right'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and host.has_one_child()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.free_drawing_mode and host.has_one_child() and ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE)

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'child_right',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'child_right'
        })


class RightAddLeafSibling(AbstractRightAddChild):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to right'
    align_left = False

    @classmethod
    def select_condition(cls, host):
        return ctrl.free_drawing_mode and host.is_leaf()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.free_drawing_mode and ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE) and host.is_leaf()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_right',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'sibling_right'
        })
