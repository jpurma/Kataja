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
import random

from PyQt5 import QtCore, QtGui, QtWidgets

from kataja.nodes.Node import Node
from kataja.errors import TouchAreaError
from kataja.Edge import Edge
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.utils import to_tuple, sub_xy
import kataja.globals as g
from kataja.nodes.ConstituentNode import ConstituentNode

end_spot_size = 10


def draw_circle(painter, x, y):
    painter.setBrush(ctrl.cm.paper())
    painter.drawEllipse(x - end_spot_size + 1,
                        y - end_spot_size + 1,
                        2 * end_spot_size, 2 * end_spot_size)


def draw_plus(painter, x, y):
    painter.drawLine(x - 1, y + 1,
                     x + 3, y + 1)
    painter.drawLine(x + 1, y - 1,
                     x + 1, y + 3)


def draw_leaf(painter, x, y):
    x -= 4
    path = QtGui.QPainterPath(QtCore.QPointF(x, y - end_spot_size))

    path.cubicTo(x + 1.2 * end_spot_size, y - end_spot_size,
                 x, y,
                 x + 0.2 * end_spot_size, y + end_spot_size)
    path.cubicTo(x - 4, y + end_spot_size,
                 x - end_spot_size, y - end_spot_size,
                 x, y - end_spot_size)
    painter.fillPath(path, painter.brush())
    painter.drawPath(path)
    path = QtGui.QPainterPath(QtCore.QPointF(x + 4, y - end_spot_size - 4))
    path.cubicTo(x, y - end_spot_size,
                 x - 0.2 * end_spot_size, y,
                 x + 0.2 * end_spot_size, y + end_spot_size)
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawPath(path)



def draw_x(painter, x, y):
    painter.drawLine(x - end_spot_size, y - end_spot_size,
                     x + end_spot_size, y + end_spot_size)
    painter.drawLine(x - end_spot_size, y + end_spot_size,
                     x + end_spot_size, y - end_spot_size)


def draw_triangle(painter, x, y, w=10):
    w2 = w / 2
    painter.drawLine(x - w, y + w2, x, y)
    painter.drawLine(x, y, x + w, y + w2)
    painter.drawLine(x + w, y + w2, x - w, y + w2)


class TouchArea(QtWidgets.QGraphicsObject):
    """ Mouse sensitive areas connected to either nodes or edges between
    them. """

    @staticmethod
    def create_key(host, ttype):
        """

        :param host:
        :param ttype:
        :return:
        """
        return 'touch_area_%s_%s' % (ttype, host.save_key)

    def __init__(self, host, ttype, ui_key, action=None):
        """

        :param ConstituentNode host:
        :param boolean left:
        :param boolean top:
        """

        QtWidgets.QGraphicsObject.__init__(self)
        self._dragging = False
        self.host = host
        self.ui_key = ui_key
        self._path = None
        self.start_point = None
        self.end_point = None
        self.setZValue(200)
        self.status_tip = ""
        self.type = ttype
        # Drawing flags defaults
        self._fill_path = False
        self._align_left = False
        self._below_node = False
        self.selectable = False
        self.focusable = True
        self.draggable = False
        self.clickable = True
        self._visible = True
        self._hovering = False
        self._drag_hint = False
        self.key = TouchArea.create_key(host, self.type)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.update_end_points()
        self.action = action
        if action and action.tip:
            self.set_tip(action.tip)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65656

    def is_visible(self):
        """


        :return:
        """
        return self._visible

    def set_tip(self, tip):
        self.status_tip = tip
        if ctrl.main.use_tooltips:
            self.setToolTip(self.status_tip)

    def contextual_color(self):
        if self._hovering:
            return ctrl.cm.hovering(ctrl.cm.ui())
        else:
            return ctrl.cm.ui_tr()

    def boundingRect(self):
        """


        :return:
        """
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        # Just the bounding rect of end spot ellipse
        return QtCore.QRectF(-end_spot_size, -end_spot_size,
                             end_spot_size + end_spot_size,
                             end_spot_size + end_spot_size)

    def sensitive_area(self):
        """


        :return:
        """
        return self.boundingRect()

    def update_position(self):
        """


        """
        pass
        # if not self in ctrl.dragged:
        self.update_end_points()

    def drag(self, event):
        self._dragging = True
        ep = to_tuple(event.scenePos())
        self.end_point = ep
        self.start_point = ep
        self.setPos(ep[0], ep[1])
        self._path = None

    def drop_to(self, x, y, recipient=None):
        self._dragging = False

    # edge.py
    def update_end_points(self):
        # start
        """

        :param end_point: End point can be given or it can be calculated.
        """
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
        return '<toucharea %s>' % self.key

    def remove(self):
        """ remove item from the scene but otherwise keep it intact """
        sc = self.scene()
        if sc:
            sc.removeItem(self)

    def make_node_from_string(self, string):
        """ Try to create a node from given string
        :param string: str
        :return:
        """
        command_identifier, *args = string.split(':')
        if command_identifier == 'kataja' and args:
            command, *args = args
            if command == "new_node":
                node_type = args[0]
                try:
                    node_type = int(node_type)
                except TypeError:
                    pass
                if hasattr(self.host, 'current_position'):
                    x, y = self.host.current_scene_position
                elif hasattr(self.host, 'start_point'):
                    x, y = self.host.start_point
                else:
                    return
                if hasattr(self.host, 'height'):
                    h = self.host.height
                else:
                    h = 0
                pos = QtCore.QPointF(x, y + h)
                return ctrl.forest.create_node(pos=pos, node_type=node_type)
            else:
                print('received unknown command:', command, args)
        else:
            print('received just some string: ', string)

    def click(self, event=None):
        """
        :type event: QMouseEvent
         """
        self._dragging = False
        if self._drag_hint:
            return False
        ctrl.deselect_objects()
        if self.action:
            self.action.action_triggered(sender=self)
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
        """

        :param dragged:
        """
        if ctrl.drag_hovering_on is self:
            return True
        elif self.accepts_drops(dragged):
            ctrl.set_drag_hovering(self)
            return True
        else:
            return False

    def accepts_drops(self, dragged):
        """

        :param dragged:
        :return:
        """
        return self.calculate_if_can_merge(dragged, None, None)

    @property
    def hovering(self):
        """


        :return:
        """
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """

        :param value:
        """
        if value and not self._hovering:
            self._hovering = True
            ctrl.set_status(self.status_tip)

        elif (not value) and self._hovering:
            self._hovering = False
            ctrl.remove_status(self.status_tip)
        self.update()

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        if (not self._hovering) and not ctrl.pressed:
            self.hovering = True
        QtWidgets.QGraphicsObject.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        if self._hovering:
            self.hovering = False
        QtWidgets.QGraphicsObject.hoverLeaveEvent(self, event)

    def dragEnterEvent(self, event):
        self.dragged_over_by(event.mimeData().text())
        event.accept()
        QtWidgets.QGraphicsObject.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        self.hovering = False
        QtWidgets.QGraphicsObject.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        self.hovering = False
        event.accept()
        message = self.drop(event.mimeData().text())
        QtWidgets.QGraphicsObject.dropEvent(self, event)
        ctrl.main.action_finished(message)


class AddConstituentTouchArea(TouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self.set_tip("Add a constituent here")

    def click(self, event=None):
        """
        :param event:
        """
        self._dragging = False
        if self._drag_hint:
            return False
        self.host.open_embed()
        return True

    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)


class AddBelowTouchArea(TouchArea):

    def update_end_points(self):
        # start
        """

        :param end_point: End point can be given or it can be calculated.
        """
        x, y = self.host.current_scene_position
        y += self.host.height / 2 + end_spot_size
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
        draw_leaf(painter, 0, 0)
        if self._hovering:
            painter.setPen(c)
            draw_plus(painter, 4, 0)


class ConnectFeatureTouchArea(AddBelowTouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self.set_tip("Add feature for node")

    def drop(self, dropped_node):
        """
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        ctrl.forest.add_feature_to_node(dropped_node, self.host)
        return 'added feature %s to %s' % (dropped_node, self.host)


class ConnectCommentTouchArea(AddBelowTouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self.set_tip("Add comment for node")

    def drop(self, dropped_node):
        """
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        ctrl.forest.add_comment_to_node(dropped_node, self.host)
        return 'added comment %s to %s' % (dropped_node, self.host)


class ConnectGlossTouchArea(AddBelowTouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self.set_tip("Add gloss for node")

    def drop(self, dropped_node):
        """
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        ctrl.forest.add_gloss_to_node(dropped_node, self.host)
        return 'added gloss %s to %s' % (dropped_node, self.host)


class DeleteArrowTouchArea(TouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self.set_tip("Remove this arrow")

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
        draw_x(painter, 0, 0)


class BranchingTouchArea(TouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)

    def boundingRect(self):
        """


        :return:
        """
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        # Bounding rect that includes the tail and end spot ellipse
        #ex, ey = self.end_point
        #sx, sy = self.start_point
        ex, ey = 0, 0
        sx, sy = sub_xy(self.start_point, self.end_point)
        e2 = end_spot_size * 2
        if sx < ex:
            w = max((ex - sx + end_spot_size, e2))
            x = min((sx, ex - end_spot_size))
        else:
            w = max((sx - ex + end_spot_size, e2))
            x = ex - end_spot_size
        if sy < ey:
            h = max((ey - sy + end_spot_size, e2))
            y = min((sy, ey - end_spot_size))
        else:
            h = max((sy - ey + end_spot_size, e2))
            y = ey - end_spot_size
        r = QtCore.QRectF(x, y, w, h)
        return r


    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        # host is an edge
        ctrl.forest.insert_node_between(dropped_node, self.host.start,
                                        self.host.end,
                                        self._align_left,
                                        self.start_point)
        for node in ctrl.dragged_set:
            node.adjustment = self.host.end.adjustment
        return 'moved node %s to sibling of %s' % (dropped_node, self.host)


class LeftAddSibling(BranchingTouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self._align_left = True
        self.update_end_points()

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        e = self.host
        shape_info = ctrl.fs.shape_info(e.edge_type)
        shape_method = shape_info['method']
        self._fill_path = e.is_filled()
        sx, sy = to_tuple(e.get_point_at(0.5))
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            d = e.get_angle_at(0.5)
            d -= 90 # 75
            angle = math.radians(-d)
            dx = math.cos(angle)
            dy = math.sin(angle)
            l = 12
            x = sx + dx * l
            y = sy + dy * l
            self.end_point = x, y
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        adjust = []
        self._path, true_path, control_points = shape_method(rel_sp, (0, 0),
                                                             alignment=g.LEFT,
                                                             curve_adjustment=adjust,
                                                             **shape_info)

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
            draw_leaf(painter, 0, end_spot_size / 2)
            painter.restore()
            draw_plus(painter, 4, 0)


class RightAddSibling(BranchingTouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self._align_left = False
        self.update_end_points()

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        e = self.host
        shape_info = ctrl.fs.shape_info(e.edge_type)
        shape_method = shape_info['method']
        self._fill_path = e.is_filled()
        sx, sy = to_tuple(e.get_point_at(0.5))
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            d = e.get_angle_at(0.5)
            d += 90 # 75
            angle = math.radians(-d)
            dx = math.cos(angle)
            dy = math.sin(angle)
            l = 12
            x = sx + dx * l
            y = sy + dy * l
            self.end_point = x, y
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        adjust = []
        self._path, true_path, control_points = shape_method(rel_sp, (0, 0),
                                                             alignment=g.RIGHT,
                                                             curve_adjustment=adjust,
                                                             **shape_info)

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
            draw_leaf(painter, 0, end_spot_size / 2)
            painter.restore()
            draw_plus(painter, 14, 0)


class JointedTouchArea(TouchArea):
    """ TouchArea that connects to nodes and has ^-shape. Used to add nodes
    to top of the trees.
    :param host:
    :param type:
    :param ui_key:
    """

    def boundingRect(self):
        """


        :return:
        """
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        # Bounding rect that includes the tail and end spot ellipse
        rel_sp = sub_xy(self.start_point, self.end_point)
        sx, sy = rel_sp
        ex, ey = 0, 0
        e2 = end_spot_size * 2
        if sx < ex:
            w = max((ex - sx + end_spot_size, e2))
            x = min((sx, ex - end_spot_size))
        else:
            w = max((sx - ex + end_spot_size, e2))
            x = ex - end_spot_size
        if sy < ey:
            h = max((ey - sy + end_spot_size, e2))
            y = min((sy, ey - end_spot_size))
        else:
            h = max((sy - ey + end_spot_size, e2))
            y = ey - end_spot_size
        r = QtCore.QRectF(x, y, w, h)
        return r.united(self._path.controlPointRect())

    def shape(self):
        """ Shape is used for collisions and it shouldn't go over the originating node. So use
        only the last half, starting from the "knee" of the shape.
        :return:
        """
        path = QtGui.QPainterPath()
        # Bounding rect that includes the tail and end spot ellipse
        rel_sp = sub_xy(self.start_point, self.end_point)
        sx, sy = rel_sp
        sx /= 2.0
        ex, ey = 0, 0
        e2 = end_spot_size * 2
        if sx < ex:
            w = max((ex - sx + end_spot_size, e2))
            x = min((sx, ex - end_spot_size))
        else:
            w = max((sx - ex + end_spot_size, e2))
            x = ex - end_spot_size
        if sy < ey:
            h = max((ey - sy + end_spot_size, e2))
            y = min((sy, ey - end_spot_size))
        else:
            h = max((sy - ey + end_spot_size, e2))
            y = ey - end_spot_size
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
        shape_name = ctrl.fs.shape_for_edge(g.CONSTITUENT_EDGE)
        shape_info = ctrl.fs.shape_presets(shape_name)
        shape_method = shape_info['method']
        self._fill_path = shape_info.get('fill', False)
        sx, sy = self.host.magnet(2)
        self.start_point = sx, sy
        hw_ratio = float(prefs.edge_height - (ConstituentNode.height / 2)) / prefs.edge_width
        if not end_point:
            good_width = max((prefs.edge_width * 2, self.host.width / 2 + ConstituentNode.width))
            if self._align_left:
                self.end_point = sx - good_width, sy
            else:
                self.end_point = sx + good_width, sy
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        sx, sy = rel_sp
        ex, ey = 0, 0
        line_middle_point = sx / 2.0, sy - hw_ratio * abs(sx)
        adjust = []
        if self._align_left:
            self._path, true_path, control_points = shape_method(line_middle_point, (sx, sy),
                                                                 alignment=g.RIGHT,
                                                                 curve_adjustment=adjust,
                                                                 **shape_info)
            self._path.moveTo(sx, sy)
            path2, true_path, control_points = shape_method(line_middle_point, (ex, ey),
                                                            alignment=g.LEFT,
                                                            curve_adjustment=adjust,
                                                            **shape_info)
        else:
            self._path, true_path, control_points = shape_method(line_middle_point, (ex, ey),
                                                                 alignment=g.RIGHT,
                                                                 curve_adjustment=adjust,
                                                                 **shape_info)
            self._path.moveTo(ex, ey)
            path2, true_path, control_points = shape_method(line_middle_point, (sx, sy),
                                                            alignment=g.LEFT,
                                                            curve_adjustment=adjust,
                                                            **shape_info)
        self._path |= path2

    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        # host is a node
        assert isinstance(self.host, Node)
        ctrl.forest.merge_to_top(self.host,
                                 dropped_node,
                                 merge_to_left=self._align_left,
                                 merger_pos=self.start_point)
        for node in ctrl.dragged_set:
            node.adjustment = self.host.adjustment
        return 'moved node %s to sibling of %s' % (
            dropped_node, self.host)


class LeftAddTop(JointedTouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self._align_left = True
        self.update_end_points()

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
            draw_leaf(painter, 0, end_spot_size / 2)
            painter.restore()
            draw_plus(painter, 4, 0)


class RightAddTop(JointedTouchArea):
    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self._align_left = False
        self.update_end_points()

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
            draw_leaf(painter, 0, end_spot_size / 2)
            painter.restore()
            draw_plus(painter, 14, 0)


class ChildTouchArea(TouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self.update_end_points()

    def boundingRect(self):
        """


        :return:
        """
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        # Bounding rect that includes the tail and end spot ellipse
        ex, ey = 0, 0
        sx, sy = sub_xy(self.start_point, self.end_point)
        e2 = end_spot_size * 2
        if sx < ex:
            w = max((ex - sx + end_spot_size, e2))
            x = min((sx, ex - end_spot_size))
        else:
            w = max((sx - ex + end_spot_size, e2))
            x = ex - end_spot_size
        if sy < ey:
            h = max((ey - sy + end_spot_size, e2))
            y = min((sy, ey - end_spot_size))
        else:
            h = max((sy - ey + end_spot_size, e2))
            y = ey - end_spot_size
        r = QtCore.QRectF(x, y, w, h)
        return r

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        # host is an edge
        ctrl.forest.insert_node_between(dropped_node, self.host.start,
                                        self.host.end,
                                        self._align_left,
                                        self.start_point)
        for node in ctrl.dragged_set:
            node.adjustment = self.host.end.adjustment
        message = 'moved node %s to sibling of %s' % (
            dropped_node, self.host)
        return message


class LeftAddChild(BranchingTouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self._align_left = True

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.fs.shape_for_edge(g.CONSTITUENT_EDGE)
        shape_info = ctrl.fs.shape_presets(shape_name)
        shape_method = shape_info['method']
        self._fill_path = shape_info.get('fill', False)
        sx, sy = self.host.magnet(7)
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            ex = sx - 20 # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        adjust = []
        self._path, true_path, control_points = shape_method(rel_sp, (0, 0),
                                                             alignment=g.LEFT,
                                                             curve_adjustment=adjust,
                                                             **shape_info)

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
            draw_leaf(painter, 0, end_spot_size / 2)
            painter.restore()
            draw_plus(painter, 4, 0)


class RightAddChild(ChildTouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key, action=None):
        super().__init__(host, ttype, ui_key, action=action)
        self._align_left = False

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.fs.shape_for_edge(g.CONSTITUENT_EDGE)
        shape_info = ctrl.fs.shape_presets(shape_name)
        shape_method = shape_info['method']
        self._fill_path = shape_info.get('fill', False)
        sx, sy = self.host.magnet(11)
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            ex = sx + 20 # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        adjust = []
        self._path, true_path, control_points = shape_method(rel_sp, (0, 0),
                                                             alignment=g.RIGHT,
                                                             curve_adjustment=adjust,
                                                             **shape_info)

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
            draw_leaf(painter, 0, end_spot_size / 2)
            painter.restore()
            draw_plus(painter, 14, 0)


class AddTriangleTouchArea(AddBelowTouchArea):
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


class RemoveTriangleTouchArea(AddBelowTouchArea):
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
            draw_x(painter, 0, 0)

touch_areas = {
    g.LEFT_ADD_TOP: LeftAddTop,
    g.RIGHT_ADD_TOP: RightAddTop,
    g.LEFT_ADD_CHILD: LeftAddChild,
    g.RIGHT_ADD_CHILD: RightAddChild,
    g.LEFT_ADD_SIBLING: LeftAddSibling,
    g.RIGHT_ADD_SIBLING: RightAddSibling,
    g.TOUCH_ADD_CONSTITUENT: AddConstituentTouchArea,
    g.TOUCH_CONNECT_COMMENT: ConnectCommentTouchArea,
    g.TOUCH_CONNECT_FEATURE: ConnectFeatureTouchArea,
    g.TOUCH_CONNECT_GLOSS: ConnectGlossTouchArea,
    g.ADD_TRIANGLE: AddTriangleTouchArea,
    g.REMOVE_TRIANGLE: RemoveTriangleTouchArea,
    g.DELETE_ARROW: DeleteArrowTouchArea,
    g.INNER_ADD_SIBLING_LEFT: LeftAddSibling,
    g.INNER_ADD_SIBLING_RIGHT: RightAddSibling,
    g.UNARY_ADD_CHILD_LEFT: LeftAddChild,
    g.UNARY_ADD_CHILD_RIGHT: RightAddChild,
    g.LEAF_ADD_SIBLING_LEFT: LeftAddChild,
    g.LEAF_ADD_SIBLING_RIGHT: RightAddChild
}


def create_touch_area(host, ttype, ui_key, action):
    """ Factory that saves from knowing which class to use.
    :param host:
    :param type:
    :param ui_key:
    :return:
    """
    if ttype in touch_areas:
        return touch_areas[ttype](host, ttype, ui_key, action)
    else:
        print('odd touch area type: ', ttype)
        return TouchArea(host, ttype, ui_key, action)
