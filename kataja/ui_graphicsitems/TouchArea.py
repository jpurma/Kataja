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
from kataja.UIItem import UIGraphicsItem
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.Shapes import draw_plus, draw_leaf, draw_x, draw_triangle, draw_tailed_leaf, \
    draw_arrow_shape_from_points, SHAPE_PRESETS
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, sub_xy

end_spot_size = 10


class TouchArea(UIGraphicsItem, QtWidgets.QGraphicsObject):
    """ Mouse sensitive areas connected to either nodes or edges between
    them. """
    __qt_type_id__ = next_available_type_id()
    clicked = QtCore.pyqtSignal()

    def __init__(self, host, action):
        """
        :param ConstituentNode host:
        :param string action:
        """
        UIGraphicsItem.__init__(self, host=host)
        QtWidgets.QGraphicsObject.__init__(self)
        self._dragging = False
        self._path = None
        self.start_point = None
        self.end_point = None
        self.setZValue(160)
        self.status_tip = ""
        # Drawing flags defaults
        self._fill_path = False
        self._align_left = False
        self._below_node = False
        self.focusable = True
        self._visible = True
        self._hovering = False
        self._drag_hint = False
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.update_end_points()
        self.action = action
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        if action:
            action.connect_element(self)
        if action and action.tip:
            self.set_tip(action.tip)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

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
            else: # This is regular click on 'pressed' object

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
        """

        :param dragged:
        """
        if ctrl.drag_hovering_on is self:
            self.hovering = True
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
            self.setZValue(1000)

        elif (not value) and self._hovering:
            self._hovering = False
            ctrl.remove_status(self.status_tip)
            self.setZValue(10)

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
        event.accept()
        QtWidgets.QGraphicsObject.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        self.hovering = False
        event.accept()
        message = self.drop(event.mimeData().text())
        QtWidgets.QGraphicsObject.dropEvent(self, event)
        ctrl.main.action_finished(message)


class AddConstituentTouchArea(TouchArea):

    __qt_type_id__ = next_available_type_id()

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
            self.make_node_from_string(dropped_node)


class AddBelowTouchArea(TouchArea):

    __qt_type_id__ = next_available_type_id()

    def update_end_points(self):
        x, y = self.host.centered_scene_position
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
        draw_tailed_leaf(painter, 0, 0, end_spot_size)
        if self._hovering:
            painter.setPen(c)
            draw_plus(painter, 4, 0)


class ConnectFeatureTouchArea(AddBelowTouchArea):

    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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

    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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

    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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

    __qt_type_id__ = next_available_type_id()

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
        draw_x(painter, 0, 0, end_spot_size)


class BranchingTouchArea(TouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """

    __qt_type_id__ = next_available_type_id()

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
    nodes in middle of the trees. """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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
        shape_name = ctrl.settings.get_edge_setting('shape_name', edge=e)
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
        self._path = SHAPE_PRESETS[shape_name].path(rel_sp, (0, 0),
                                  alignment=g.LEFT,
                                  curve_adjustment=adjust)[0]

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
            draw_leaf(painter, 0, end_spot_size / 2, end_spot_size)
            painter.restore()
            draw_plus(painter, 4, 0)


class LeftAddInnerSibling(LeftAddSibling):
    __qt_type_id__ = next_available_type_id()


class RightAddSibling(BranchingTouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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
        shape_name = ctrl.settings.get_edge_setting('shape_name', edge=e)
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
        self._path = SHAPE_PRESETS[shape_name].path(rel_sp, (0, 0),
                                  alignment=g.RIGHT,
                                  curve_adjustment=adjust)[0]

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
            draw_leaf(painter, 0, end_spot_size / 2, end_spot_size)
            painter.restore()
            draw_plus(painter, 14, 0)


class RightAddInnerSibling(RightAddSibling):
    __qt_type_id__ = next_available_type_id()


class JointedTouchArea(TouchArea):
    """ TouchArea that connects to nodes and has ^-shape. Used to add nodes
    to top of the trees. """
    __qt_type_id__ = next_available_type_id()

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
        shape_name = ctrl.settings.get_edge_setting('shape_name', edge_type=g.CONSTITUENT_EDGE)
        self._fill_path = ctrl.settings.get_shape_setting('fill', edge_type=g.CONSTITUENT_EDGE)
        sx, sy = self.host.magnet(2)
        self.start_point = sx, sy
        hw_ratio = float(prefs.edge_height - (ConstituentNode.height / 2)) / (prefs.edge_width or 1)
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
            self._path = SHAPE_PRESETS[shape_name].path(line_middle_point, (sx, sy),
                                                   alignment=g.RIGHT,
                                                   curve_adjustment=adjust)[0]
            self._path.moveTo(sx, sy)
            path2 = SHAPE_PRESETS[shape_name].path(line_middle_point, (ex, ey),
                                              alignment=g.LEFT,
                                              curve_adjustment=adjust)[0]
        else:
            self._path = SHAPE_PRESETS[shape_name].path(line_middle_point, (ex, ey),
                                                   alignment=g.RIGHT,
                                                   curve_adjustment=adjust)[0]
            self._path.moveTo(ex, ey)
            path2 = SHAPE_PRESETS[shape_name].path(line_middle_point, (sx, sy),
                                              alignment=g.LEFT,
                                              curve_adjustment=adjust)[0]
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
                                 pos=self.start_point)
        for node in ctrl.dragged_set:
            node.adjustment = self.host.adjustment
        return 'moved node %s to sibling of %s' % (
            dropped_node, self.host)


class LeftAddTop(JointedTouchArea):

    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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
            draw_leaf(painter, 0, end_spot_size / 2, end_spot_size)
            painter.restore()
            draw_plus(painter, 4, 0)


class RightAddTop(JointedTouchArea):

    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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
            draw_leaf(painter, 0, end_spot_size / 2, end_spot_size)
            painter.restore()
            draw_plus(painter, 14, 0)


class ChildTouchArea(TouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes. """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
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
    add nodes to leaf nodes."""
    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
        self._align_left = True

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
        else:
            ex = sx - 20 # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        adjust = []
        self._path = SHAPE_PRESETS[shape_name].path(rel_sp, (0, 0),
                                               alignment=g.LEFT,
                                               curve_adjustment=adjust)[0]

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
            draw_leaf(painter, 0, end_spot_size / 2, end_spot_size)
            painter.restore()
            draw_plus(painter, 4, 0)


class LeftAddUnaryChild(LeftAddChild):
    __qt_type_id__ = next_available_type_id()


class LeftAddLeafSibling(LeftAddChild):
    __qt_type_id__ = next_available_type_id()


class RightAddChild(ChildTouchArea):
    """ TouchArea that adds children to nodes and has /-shape. Used to
    add nodes to leaf nodes. """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, host, action):
        super().__init__(host, action)
        self._align_left = False

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
        else:
            ex = sx + 20 # 75
            ey = sy + 10
            self.end_point = ex, ey
        self.setPos(self.end_point[0], self.end_point[1])
        rel_sp = sub_xy(self.start_point, self.end_point)
        adjust = []
        self._path = SHAPE_PRESETS[shape_name].path(rel_sp, (0, 0),
                                               alignment=g.RIGHT,
                                               curve_adjustment=adjust)[0]

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
            draw_leaf(painter, 0, end_spot_size / 2, end_spot_size)
            painter.restore()
            draw_plus(painter, 14, 0)


class RightAddUnaryChild(RightAddChild):
    __qt_type_id__ = next_available_type_id()


class RightAddLeafSibling(RightAddChild):
    __qt_type_id__ = next_available_type_id()


class AddTriangleTouchArea(AddBelowTouchArea):

    __qt_type_id__ = next_available_type_id()

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

    __qt_type_id__ = next_available_type_id()

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
            draw_x(painter, 0, 0, end_spot_size)


class StartArrowTouchArea(AddBelowTouchArea):

    __qt_type_id__ = next_available_type_id()

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
        #painter.setBrush(c)
        draw_arrow_shape_from_points(painter, -2, 0, 8, 7, c)
        if self._hovering:
            painter.drawRoundedRect(self.boundingRect(), 4, 4)
