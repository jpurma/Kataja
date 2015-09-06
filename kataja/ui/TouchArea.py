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
from kataja.singletons import ctrl, prefs
from kataja.utils import to_tuple, tuple2_to_tuple3, sub_xy
import kataja.globals as g

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


class TouchArea(QtWidgets.QGraphicsItem):
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

    def __init__(self, host, ttype, ui_key):
        """

        :param ConstituentNode host:
        :param boolean left:
        :param boolean top:
        """

        QtWidgets.QGraphicsItem.__init__(self)
        self._dragging = False
        self.host = host
        self.ui_key = ui_key
        self._path = None
        self.start_point = None
        self.end_point = None
        self.setZValue(200)
        self.type = ttype
        # Drawing flags defaults
        self._align_left = False
        self._below_node = False
        self.shape = '+'
        # Drawing flags for each touch area type
        if self.type is g.TOUCH_ADD_CONSTITUENT:
            self.status_tip = "Add a constituent here"
        elif self.type is g.TOUCH_CONNECT_FEATURE:
            self.status_tip = "Add feature for node"
            self._below_node = True
        elif self.type is g.TOUCH_CONNECT_COMMENT:
            self.status_tip = "Add comment for node"
            self._below_node = True
        elif self.type is g.TOUCH_CONNECT_GLOSS:
            self.status_tip = "Add gloss text for node"
            self._below_node = True
        elif self.type is g.DELETE_ARROW:
            self.status_tip = "Remove this arrow"
            self._below_node = True
            self.shape = 'X'
        else:
            self.status_tip = "Unknown touch area???"
        self.selectable = False
        self.focusable = True
        self.draggable = False
        self.clickable = True
        self._visible = True
        self._hovering = False
        self._drag_hint = False
        self.key = TouchArea.create_key(host, type)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.update_end_points()
        self.setCursor(QtCore.Qt.PointingHandCursor)

        if ctrl.main.use_tooltips:
            self.setToolTip(self.status_tip)

    def is_visible(self):
        """


        :return:
        """
        return self._visible

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
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def drop_to(self, x, y, recipient=None):
        self._dragging = False

    # edge.py
    def update_end_points(self, end_point=None):
        # start
        """

        :param end_point: End point can be given or it can be calculated.
        """
        if end_point:
            self.end_point = end_point
            self.setPos(end_point[0], end_point[1])
        elif not self.host:
            return
        elif isinstance(self.host, Edge):
            x, y, z = self.host.end_point
            self.end_point = x, y
        else:
            x, y, z = self.host.current_position
            if self._below_node:
                y += self.host.height / 2 + end_spot_size
            self.end_point = x, y
        self.start_point = self.end_point
        self.setPos(self.end_point[0], self.end_point[1])
        self._path = None
        return

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
                    x, y, z = self.host.current_position
                elif hasattr(self.host, 'start_point'):
                    x, y, z = self.host.start_point
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

    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        message = ''
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return

        if self.type == g.TOUCH_CONNECT_FEATURE:
            ctrl.forest.add_feature_to_node(dropped_node, self.host)
            message = 'added feature %s to %s' % (dropped_node, self.host)
        elif self.type == g.TOUCH_CONNECT_GLOSS:
            ctrl.forest.add_gloss_to_node(dropped_node, self.host)
            message = 'added gloss %s to %s' % (dropped_node, self.host)
        elif self.type == g.TOUCH_CONNECT_COMMENT:
            ctrl.forest.add_comment_to_node(dropped_node, self.host)
            message = 'added %s to %s' % (dropped_node, self.host)
        return message

    def click(self, event=None):
        """
        :type event: QMouseEvent
         """
        self._dragging = False
        if self._drag_hint:
            return False
        replaced = self.host
        closest_parent = None
        if self.type is g.TOUCH_ADD_CONSTITUENT:
            replaced.open_embed()
        else: # hmm, could be unnecessary
            #ctrl.forest.replace_node_with_merged_node(replaced, None,
            #                                          closest_parent,
            #
            # merge_to_left=self._align_left,
            #
            # new_node_pos=self.end_point,
            #
            # merger_node_pos=self.start_point)
            ctrl.deselect_objects()
            ctrl.main.action_finished(m='add constituent')
        return True

    # self, N, R, merge_to_left, new_node_pos, merger_node_pos):

    def calculate_if_can_merge(self, dragged, root, node_list):
        """

        :param dragged:
        :param root:
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
        if not self._hovering and self.accepts_drops(dragged):
            if ctrl.latest_hover and not ctrl.latest_hover is self:
                ctrl.latest_hover.hovering = False
            ctrl.latest_hover = self
            self.hovering = True

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
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        if self._hovering:
            self.hovering = False
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    def dragEnterEvent(self, event):
        print('dragEnterEvent in TouchArea')
        self.dragged_over_by(event.mimeData().text())
        event.accept()
        QtWidgets.QGraphicsItem.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        print('dragLeaveEvent in TouchArea')
        self.hovering = False
        QtWidgets.QGraphicsItem.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        print("dropEvent")
        self.hovering = False
        event.accept()
        message = self.drop(event.mimeData().text())
        QtWidgets.QGraphicsItem.dropEvent(self, event)
        ctrl.main.action_finished(message)

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """

        if ctrl.pressed is self:
            pass

        if self._hovering:
            c = ctrl.cm.hovering(ctrl.cm.ui())
        else:
            c = ctrl.cm.ui_tr()
        painter.setPen(c)
        if self.shape == '+':
            draw_leaf(painter, 0, 0)
            if self._hovering:
                painter.setPen(c)
                draw_plus(painter, 4, 0)
        elif self.shape == 'X':
            draw_x(painter, 0, 0)


class BranchingTouchArea(TouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the tree.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key):
        super().__init__(host, ttype, ui_key)
        self._fill_path = False
        if ttype is g.LEFT_ADD_SIBLING:
            self.status_tip = "Add new sibling to left of %s" % self.host.end
            self._align_left = True
        elif ttype is g.RIGHT_ADD_SIBLING:
            self.status_tip = "Add new sibling to right of %s" % self.host.end
        if ctrl.main.use_tooltips:
            self.setToolTip(self.status_tip)
        self.update_end_points()

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

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        e = self.host
        shape_info = e.shape_info()
        shape_method = shape_info['method']
        self._fill_path = e.is_filled()
        sx, sy = to_tuple(e.get_point_at(0.5))
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            d = e.get_angle_at(0.5)
            if self._align_left:
                d -= 90 # 75
            else:
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
        sp = tuple2_to_tuple3(rel_sp)
        #ep = tuple2_to_tuple3(self.end_point)
        adjust = []
        if self._align_left:
            align = g.LEFT
        else:
            align = g.RIGHT
        self._path, true_path, control_points = shape_method(sp, (0, 0, 0),
                                                             align=align,
                                                             adjust=adjust,
                                                             **shape_info)

    def click(self, event=None):
        """
        :type event: QMouseEvent
         """
        self._dragging = False
        if self._drag_hint:
            return False
        child = self.host.end
        parent = self.host.start
        new_node = ctrl.forest.create_node(pos=child.current_position)
        new_node.copy_position(child)
        ctrl.forest.insert_node_between(new_node, parent, child,
                                        self._align_left,
                                        self.start_point)
        ctrl.deselect_objects()
        ctrl.main.action_finished(m='add constituent')
        return True

    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        message = ''
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        if self.type == g.RIGHT_ADD_SIBLING or self.type == \
            g.LEFT_ADD_SIBLING:
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

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        if self._hovering:
            c = ctrl.cm.hovering(ctrl.cm.ui())
        else:
            c = ctrl.cm.ui_tr()
        painter.setPen(c)
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            if self._align_left:
                painter.rotate(20)
                draw_leaf(painter, 0, end_spot_size / 2)
                painter.restore()
                draw_plus(painter, 4, 0)
            else:
                painter.rotate(-160)
                draw_leaf(painter, 0, end_spot_size / 2)
                painter.restore()
                draw_plus(painter, 14, 0)


class JointedTouchArea(TouchArea):
    """ TouchArea that connects to nodes and has ^-shape. Used to add nodes
    to top of the tree.
    :param host:
    :param type:
    :param ui_key:
    """

    def __init__(self, host, ttype, ui_key):
        super().__init__(host, ttype, ui_key)
        self._fill_path = False
        if ttype is g.LEFT_ADD_ROOT:
            self.status_tip = "Add new constituent to left of %s" % self.host
            self._align_left = True
        elif ttype is g.RIGHT_ADD_ROOT:
            self.status_tip = "Add new constituent to right of %s" % self.host
        if ctrl.main.use_tooltips:
            self.setToolTip(self.status_tip)
        self.update_end_points()

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
        #ex, ey = self.end_point
        #sx, sy = self.start_point
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

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.fs.shape_for_edge(g.CONSTITUENT_EDGE)
        shape_info = ctrl.fs.shape_presets(shape_name)
        shape_method = shape_info['method']
        self._fill_path = shape_info.get('fill', False)
        sx, sy, dummy = self.host.magnet(2)
        self.start_point = sx, sy
        if not end_point:
            good_width = max((prefs.edge_width * 2, self.host.width))
            if self._align_left:
                self.end_point = sx - good_width, sy
            else:
                self.end_point = sx + good_width, sy
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        sx, sy = rel_sp
        ex, ey = 0, 0

        line_middle_point = sx / 2.0, sy - 10
        mp = tuple2_to_tuple3(line_middle_point)
        adjust = []
        if self._align_left:
            sp = tuple2_to_tuple3((sx, sy))
            ep = tuple2_to_tuple3((ex, ey))
        else:
            sp = tuple2_to_tuple3((ex, ey))
            ep = tuple2_to_tuple3((sx, sy))

        self._path, true_path, control_points = shape_method(mp, sp,
                                                             align=g.RIGHT,
                                                             adjust=adjust,
                                                             **shape_info)
        self._path.moveTo(sp[0], sp[1])
        path2, true_path, control_points = shape_method(mp, ep,
                                                        align=g.LEFT,
                                                        adjust=adjust,
                                                        **shape_info)
        self._path = self._path.united(path2)

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
        if self.type == g.RIGHT_ADD_ROOT or self.type == g.LEFT_ADD_ROOT:
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

    def click(self, event=None):
        """
        :type event: QMouseEvent
         """
        self._dragging = False
        if self._drag_hint:
            return False
        root = self.host
        new_node = ctrl.forest.create_node(pos=root.current_position)
        new_node.copy_position(root)
        ctrl.forest.merge_to_top(root, new_node, self._align_left, new_node.current_position)
        ctrl.deselect_objects()
        ctrl.main.action_finished(m='add constituent')
        return True

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        if self._hovering:
            c = ctrl.cm.hovering(ctrl.cm.ui())
        elif ctrl.is_selected(self):  # wrong colors, just testing
            c = ctrl.cm.selection()
        else:
            c = ctrl.cm.ui_tr()
        painter.setPen(c)
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            if self._align_left:
                painter.rotate(20)
                draw_leaf(painter, 0, end_spot_size / 2)
                painter.restore()
                draw_plus(painter, 4, 0)
            else:
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

    def __init__(self, host, ttype, ui_key):
        super().__init__(host, ttype, ui_key)
        self._fill_path = False
        if ttype is g.LEFT_ADD_CHILD:
            self.status_tip = "Add new child for %s" % self.host
            self._align_left = True
        elif ttype is g.RIGHT_ADD_CHILD:
            self.status_tip = "Add new child for %s" % \
                              self.host
        if ctrl.main.use_tooltips:
            self.setToolTip(self.status_tip)
        self.update_end_points()

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

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        shape_name = ctrl.fs.shape_for_edge(g.CONSTITUENT_EDGE)
        shape_info = ctrl.fs.shape_presets(shape_name)
        shape_method = shape_info['method']
        self._fill_path = shape_info.get('fill', False)
        if self._align_left:
            sx, sy, dummy = self.host.magnet(7)
        else:
            sx, sy, dummy = self.host.magnet(11)
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            if self._align_left:
                ex = sx - 20 # 75
            else:
                ex = sx + 20 # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        sp = tuple2_to_tuple3(rel_sp)
        #ep = tuple2_to_tuple3(self.end_point)
        adjust = []
        if self._align_left:
            align = g.LEFT
        else:
            align = g.RIGHT
        self._path, true_path, control_points = shape_method(sp, (0, 0, 0),
                                                             align=align,
                                                             adjust=adjust,
                                                             **shape_info)

    def click(self, event=None):
        """
        :type event: QMouseEvent
         """
        self._dragging = False
        if self._drag_hint:
            return False
        ctrl.forest.add_children_for_constituentnode(self.host,
                                                     pos=tuple2_to_tuple3(self.end_point),
                                                     head_left=self._align_left)
        ctrl.deselect_objects()
        ctrl.main.action_finished(m='add constituent')
        return True

    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        message = ''
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        if self.type == g.RIGHT_ADD_SIBLING or self.type == \
            g.LEFT_ADD_SIBLING:
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

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed is self:
            pass
        if self._hovering:
            c = ctrl.cm.hovering(ctrl.cm.ui())
        else:
            c = ctrl.cm.ui_tr()
        painter.setPen(c)
        if self._fill_path:
            painter.fillPath(self._path, c)
        else:
            painter.drawPath(self._path)
        if self._hovering:
            painter.save()
            painter.setBrush(ctrl.cm.ui())
            if self._align_left:
                painter.rotate(20)
                draw_leaf(painter, 0, end_spot_size / 2)
                painter.restore()
                draw_plus(painter, 4, 0)
            else:
                painter.rotate(-160)
                draw_leaf(painter, 0, end_spot_size / 2)
                painter.restore()
                draw_plus(painter, 14, 0)


def create_touch_area(host, ttype, ui_key):
    """ Factory that saves from knowing which class to use.
    :param host:
    :param type:
    :param ui_key:
    :return:
    """
    if ttype in [g.RIGHT_ADD_ROOT, g.LEFT_ADD_ROOT]:
        return JointedTouchArea(host, ttype, ui_key)
    elif ttype in [g.LEFT_ADD_SIBLING, g.RIGHT_ADD_SIBLING]:
        return BranchingTouchArea(host, ttype, ui_key)
    elif ttype in [g.LEFT_ADD_CHILD, g.RIGHT_ADD_CHILD]:
        return ChildTouchArea(host, ttype, ui_key)
    else:
        return TouchArea(host, ttype, ui_key)
