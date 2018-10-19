


import math

from PyQt5 import QtCore, QtGui

import kataja.globals as g
from kataja.Shapes import draw_plus, draw_leaf, SHAPE_PRESETS
from kataja.singletons import ctrl, prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.ui_graphicsitems.TouchArea import TouchArea, AbstractBelowTouchArea
from kataja.utils import to_tuple
from math import sqrt

symbol_radius = 10
symbol_radius_sqr = sqrt(2) * symbol_radius

LEAF_BR = QtCore.QRectF(-symbol_radius_sqr, -symbol_radius_sqr, symbol_radius_sqr * 2,
                        symbol_radius_sqr * 2)
PLUS_BR = QtCore.QRectF(-1, -1, 4, 4)


class AddBelowTouchArea(AbstractBelowTouchArea):
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return (not ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE)) and host.can_have_as_child()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'child'
        }, drop_action='connect_node', drop_kwargs={
            'position': 'child'
        })


class AbstractBranchingTouchArea(TouchArea):
    """ TouchArea that connects to edges and has /-shape. Used to add/merge
    nodes in middle of the trees. """

    def boundingRect(self):
        sx, sy = self.start_point
        ex, ey = self.end_point
        br = QtCore.QRectF(0, 0, sx - ex, sy - ey)
        if self._hovering:
            br |= LEAF_BR | PLUS_BR.translated(1.2 * symbol_radius, 0)
        return br


class AbstractLeftBranching(AbstractBranchingTouchArea):
    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def update_end_points(self, end_point=None):
        """

        :param end_point: End point can be given or it can be calculated.
        """
        e = self.host
        sx, sy = to_tuple(e.path.get_point_at(0.4))
        self.start_point = sx, sy
        if end_point:
            self.end_point = end_point
        else:
            d = e.path.get_angle_at(0.4)
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
        sx, sy = to_tuple(e.path.get_point_at(0.4))
        self.start_point = sx, sy
        if end_point:
            ex, ey = end_point
            self.end_point = end_point
        else:
            d = e.path.get_angle_at(0.4)
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
            draw_leaf(painter, 0, 0, symbol_radius)
            painter.restore()
            draw_plus(painter, 1.2 * symbol_radius, 0)


class MergeToTop(AbstractBranchingTouchArea):
    """ TouchArea that connects to nodes and has \-shape.  """
    __qt_type_id__ = next_available_type_id()

    @classmethod
    def select_condition(cls, host):
        return not host.is_top_node()

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
            tops = self.host.get_highest()
            if len(tops) != 1:
                return QtCore.QRectF(-2, -2, dx + 4, dy + 4) | LEAF_BR
            else:
                top = tops[0]
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
            tops = self.host.get_highest()
            if len(tops) != 1:
                painter.drawLine(l)
                painter.save()
                painter.setBrush(ctrl.cm.ui())
                painter.rotate(20)
                draw_leaf(painter, 0, 0, symbol_radius)
                painter.restore()
                draw_plus(painter, 1.2 * symbol_radius, 0)
                return
            else:
                top = tops[0]
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


class AbstractJointedTouchArea(TouchArea):
    """ TouchArea that connects to nodes and has ^-shape. Used to add nodes
    to top of the trees. """

    def boundingRect(self):
        if not self.end_point:
            self.update_end_points()
            assert self.end_point
        return self._path.controlPointRect() | LEAF_BR | PLUS_BR.translated(1.2 * symbol_radius, 0)


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
        shape_name = ctrl.forest.settings.get_for_edge_type('shape_name', edge_type=g.CONSTITUENT_EDGE)
        shape = SHAPE_PRESETS[shape_name]
        self._fill_path = shape.fillable and ctrl.forest.settings.get_for_edge_shape('fill', edge_shape=shape_name)
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
        if self._align_left:
            path1 = shape.path(line_middle_point, (sx, sy), adjust, g.BOTTOM, g.TOP)[0]
            path1.moveTo(sx, sy)
            path2 = shape.path(line_middle_point, (ex, ey), adjust, g.BOTTOM, g.TOP)[0]
        else:
            path1 = shape.path(line_middle_point, (ex, ey), adjust, g.BOTTOM, g.TOP)[0]
            path1.moveTo(ex, ey)
            path2 = shape.path(line_middle_point, (sx, sy), adjust, g.BOTTOM, g.TOP)[0]
        self._path = path1 | path2


class LeftAddTop(AbstractJointedTouchArea):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add node to left'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE) and host.is_top_node()

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
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE)

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
        return host.end.inner_add_sibling()

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_left',
            'new_type': g.CONSTITUENT_NODE
        })


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
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE)

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
        return host.end.inner_add_sibling()

    @classmethod
    def drop_condition(cls, host):
        return False

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_right',
            'new_type': g.CONSTITUENT_NODE
        })


class RightAddTop(AbstractJointedTouchArea):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add node to right'

    @classmethod
    def select_condition(cls, host):
        return host.is_top_node()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(
            g.CONSTITUENT_NODE) and host.is_top_node()

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
        return r | LEAF_BR | PLUS_BR.translated(symbol_radius * 1.2, 0)

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
        shape_name = ctrl.forest.settings.get_for_edge_type('shape_name', edge_type=g.CONSTITUENT_EDGE)
        shape = SHAPE_PRESETS[shape_name]
        self._fill_path = shape.fillable and ctrl.forest.settings.get_for_edge_shape('fill', edge_shape=shape_name)
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
        self._path = shape.path((sx, sy), (0, 0), adjust, g.BOTTOM, g.TOP)[0]

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


class LeftAddUnaryChild(AbstractLeftAddChild):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to left'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return host.has_one_child()

    @classmethod
    def drop_condition(cls, host):
        return host.has_one_child() and ctrl.ui.is_dragging_this_type(
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
        return host.is_leaf()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(
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
        shape_name = ctrl.forest.settings.get_for_edge_type('shape_name', edge_type=g.CONSTITUENT_EDGE)
        shape = SHAPE_PRESETS[shape_name]
        self._fill_path = shape.fillable and ctrl.forest.settings.get_for_edge_shape('fill', edge_shape=shape_name)
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
        self._path = shape.path((sx, sy), (0, 0), adjust, g.BOTTOM, g.TOP)[0]

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


class RightAddUnaryChild(AbstractRightAddChild):
    __qt_type_id__ = next_available_type_id()
    k_tooltip = 'Add child node to right'
    align_left = True

    @classmethod
    def select_condition(cls, host):
        return host.has_one_child()

    @classmethod
    def drop_condition(cls, host):
        return host.has_one_child() and ctrl.ui.is_dragging_this_type(
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
        return host.is_leaf()

    @classmethod
    def drop_condition(cls, host):
        return ctrl.ui.is_dragging_this_type(g.CONSTITUENT_NODE) and host.is_leaf()

    def __init__(self, host):
        super().__init__(host, click_action='connect_node', click_kwargs={
            'position': 'sibling_right',
            'new_type': g.CONSTITUENT_NODE
        }, drop_action='connect_node', drop_kwargs={
            'position': 'sibling_right'
        })
