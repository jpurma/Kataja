import math
from collections import OrderedDict
from math import sin, cos, pi, acos, sqrt

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QPointF as Pf

__author__ = 'purma'

pipi = pi * 2.0

outline_stroker = QtGui.QPainterPathStroker()
outline_stroker.setWidth(4)

TOP_LEFT_CORNER = 0
TOP_SIDE = 1
TOP_RIGHT_CORNER = 2
LEFT_SIDE = 3
RIGHT_SIDE = 4
BOTTOM_LEFT_CORNER = 5
BOTTOM_SIDE = 6
BOTTOM_RIGHT_CORNER = 7


def adjusted_control_point_list(sx, sy, ex, ey, control_points, curve_adjustment) -> list:
    """ List where control points and their adjustments are added up
    :param sx: start_point x
    :param sy: start_point y
    :param ex: end_point x
    :param ey: end_point y
    :param control_points: list of x,y -tuples for points between start and end
    :param curve_adjustment: list of dist, angle -tuples, at least as long as control_points
    :return: list
    """
    l = []
    if not curve_adjustment:
        la = 0
    else:
        la = len(curve_adjustment)
    for i, (cx, cy) in enumerate(control_points):
        if la <= i:
            l.append((cx, cy))
        else:
            rdist, rrad = curve_adjustment[i]
            if i == 0:
                sx_to_cx = cx - sx
                sy_to_cy = cy - sy
            else:
                sx_to_cx = cx - ex
                sy_to_cy = cy - ey
            line_rad = math.atan2(sy_to_cy, sx_to_cx)
            line_dist = math.hypot(sx_to_cx, sy_to_cy)
            new_dist = rdist * line_dist
            new_x = cx + (new_dist * math.cos(rrad + line_rad))
            new_y = cy + (new_dist * math.sin(rrad + line_rad))
            l.append((new_x, new_y))
    return l


# Shapes

def draw_arrow_shape(self, painter):
    """

    :param self:
    :param painter:
    :return:
    """
    l = self.line()
    painter.setPen(self._pen)
    painter.setBrush(self._pen.color)
    painter.drawLine(l)
    l2x = l.p2().x()
    l2 = l.p2()
    l2y = l.p2().y()
    back = self._arrow_size / -2
    # Draw the arrows if there's enough room.
    ll = l.length()
    if ll >= 1 and ll + back > 0:
        angle = acos(l.dx() / ll)  # acos has to be <= 1.0
    else:
        return
    prop = back / ll
    if l.dy() >= 0:
        angle = pipi - angle
    destArrowP1 = Pf((sin(angle - pi / 3) * self._arrow_size) + l2x,
                     (cos(angle - pi / 3) * self._arrow_size) + l2y)
    destArrowP2 = Pf((sin(angle - pi + pi / 3) * self._arrow_size) + l2x,
                     (cos(angle - pi + pi / 3) * self._arrow_size) + l2y)
    l2c = Pf(l.dx() * prop + l2x, l.dy() * prop + l2y)
    painter.drawPolygon(QtGui.QPolygonF([l2, destArrowP1, l2c, destArrowP2]))


def draw_arrow_shape_from_points(painter, start_x, start_y, end_x, end_y, color, arrow_size=6):
    dx = end_x - start_x
    dy = end_y - start_y
    length = sqrt(dx * dx + dy * dy)
    back = arrow_size / -2
    # Draw the arrows if there's enough room.
    if length >= 1 and length + back > 0:
        angle = acos(dx / length)
    else:
        return
    prop = back / length
    if dy >= 0:
        angle = pipi - angle
    destArrowP1x = (sin(angle - pi / 3) * arrow_size) + end_x
    destArrowP1y = (cos(angle - pi / 3) * arrow_size) + end_y
    destArrowP2x = (sin(angle - pi + pi / 3) * arrow_size) + end_x
    destArrowP2y = (cos(angle - pi + pi / 3) * arrow_size) + end_y
    l2cx = dx * prop + end_x
    l2cy = dy * prop + end_y
    painter.drawLine(int(start_x), int(start_y), int(l2cx), int(l2cy))
    path2 = QtGui.QPainterPath(Pf(end_x, end_y))
    path2.lineTo(end_x, end_y)
    path2.lineTo(destArrowP1x, destArrowP1y)
    path2.lineTo(l2cx, l2cy)
    path2.lineTo(destArrowP2x, destArrowP2y)
    painter.fillPath(path2, color)


def arrow_shape_bounding_rect(self):
    """ If draw_arrow_shape is used, boundingRect should refer to this """
    l = self.line()
    p1 = l.p1()
    p2 = l.p2()
    p1x = p1.x()
    p2x = p2.x()
    p1y = p1.y()
    p2y = p2.y()

    extra = self._arrow_size / 2.0
    if p1x > p2x - extra:
        l = p2x - extra
        r = p1x + extra
    else:
        l = p1x - extra
        r = p2x + extra
    if p1y > p2y - extra:
        t = p2y - extra
        b = p1y + extra
    else:
        t = p1y - extra
        b = p2y + extra
    return QtCore.QRectF(Pf(l, t), Pf(r, b))


def to_pf(xy):
    return Pf(xy[0], xy[1])


class Shape:
    """ Baseclass for complex parametrized paths used to draw edges. Each implements path -method
    and may have their own special parameters.
    """
    shape_name = 'no_path'
    control_points_n = 0
    fillable = False
    defaults = {
        'outline': False
    }

    def __init__(self):
        pass

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        return QtGui.QPainterPath(), QtGui.QPainterPath(), [], ()

    @staticmethod
    def icon_path(painter, rect, color=None):
        pass


class ShapedCubicPath(Shape):
    """ Two point leaf-shaped curve """
    shape_name = 'shaped_cubic'
    control_points_n = 2
    fillable = True

    defaults = {
        'fill': True,
        'outline': False,
        'thickness': 0.5,
        'rel_dx': 0.2,
        'rel_dy': 0.4,
        'fixed_dx': 0,
        'fixed_dy': 0,
        'leaf_x': 0.8,
        'leaf_y': 2
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = ShapedCubicPath.defaults
        sx, sy = start_point
        ex, ey = end_point
        # edges that go to wrong direction have stronger curvature
        leaf_x = d['leaf_x']
        leaf_y = d['leaf_y']
        if thick > 1:
            leaf_x *= thick
            leaf_y *= thick
        dx = d['fixed_dx'] + abs(d['rel_dx'] * (ex - sx))
        dy = d['fixed_dy'] + abs(d['rel_dy'] * (ey - sy))
        if curve_dir_start == BOTTOM_SIDE:
            cp1 = (sx, sy + dy)
        elif curve_dir_start == TOP_SIDE:
            cp1 = (sx, sy - dy)
        elif curve_dir_start == LEFT_SIDE:
            cp1 = (sx - dx, sy)
        elif curve_dir_start == RIGHT_SIDE:
            cp1 = (sx + dx, sy)
        else:
            cp1 = (sx + dx, sy)
        if curve_dir_end == BOTTOM_SIDE:
            cp2 = (ex, ey + dy)
        elif curve_dir_end == TOP_SIDE:
            cp2 = (ex, ey - dy)
        elif curve_dir_end == LEFT_SIDE:
            cp2 = (ex - dx, ey)
        elif curve_dir_end == RIGHT_SIDE:
            cp2 = (ex + dx, ey)
        else:
            cp2 = (ex + dx, ey)

        control_points = [cp1, cp2]

        c = adjusted_control_point_list(sx, sy, ex, ey, control_points, curve_adjustment)
        (c1x, c1y), (c2x, c2y) = c
        if inner_only:
            path = None
        else:
            path = QtGui.QPainterPath(Pf(sx, sy))
            path.cubicTo(c1x - leaf_x, c1y, c2x, c2y + leaf_y, ex, ey)
            path.cubicTo(c2x, c2y - leaf_y, c1x + leaf_x, c1y, sx, sy)
        inner_path = QtGui.QPainterPath(Pf(sx, sy))
        inner_path.cubicTo(c1x, c1y, c2x, c2y, ex, ey)
        return path, inner_path, control_points, c

    @staticmethod
    def icon_path(painter, rect, color=None, rel_dx=0.4, rel_dy=0.8, leaf_x=1, leaf_y=3):
        sx, sy = 0, 4
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.cubicTo(sx + dx - leaf_x, sy + dy, ex, ey - dy + leaf_y, ex, ey)
        path.cubicTo(ex, ey - dy - leaf_y, sx + dx + leaf_x, sy + dy, sx, sy)
        painter.fillPath(path, color)


class CubicPath(Shape):
    """ Two point single stroke curve """
    shape_name = 'cubic'
    control_points_n = 2
    fillable = False

    defaults = {
        'outline': True,
        'thickness': 1.0,
        'rel_dx': 0.2,
        'rel_dy': 0.4,
        'fixed_dx': 0,
        'fixed_dy': 0,
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = CubicPath.defaults
        sx, sy = start_point
        ex, ey = end_point
        # edges that go to wrong direction have stronger curvature

        dx = d['fixed_dx'] + abs(d['rel_dx'] * (ex - sx))
        dy = d['fixed_dy'] + abs(d['rel_dy'] * (ey - sy))
        if curve_dir_start == BOTTOM_SIDE:
            cp1 = (sx, sy + dy)
        elif curve_dir_start == TOP_SIDE:
            cp1 = (sx, sy - dy)
        elif curve_dir_start == LEFT_SIDE:
            cp1 = (sx - dx, sy)
        elif curve_dir_start == RIGHT_SIDE:
            cp1 = (sx + dx, sy)
        else:
            cp1 = (sx + dx, sy)
        if curve_dir_end == BOTTOM_SIDE:
            cp2 = (ex, ey + dy)
        elif curve_dir_end == TOP_SIDE:
            cp2 = (ex, ey - dy)
        elif curve_dir_end == LEFT_SIDE:
            cp2 = (ex - dx, ey)
        elif curve_dir_end == RIGHT_SIDE:
            cp2 = (ex + dx, ey)
        else:
            cp2 = (ex - dx, ey)
        control_points = [cp1, cp2]

        path = QtGui.QPainterPath(Pf(sx, sy))
        c = adjusted_control_point_list(sx, sy, ex, ey, control_points, curve_adjustment)
        (c1x, c1y), (c2x, c2y) = c
        path.cubicTo(c1x, c1y, c2x, c2y, ex, ey)
        return path, path, control_points, c

    @staticmethod
    def icon_path(painter, rect, color=None, rel_dx=0.4, rel_dy=0.8):
        sx, sy = 0, 4
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.cubicTo(sx + dx, sy + dy, ex, ey - dy, ex, ey)
        painter.drawPath(path)


class ShapedQuadraticPath(Shape):
    """ Leaf-shaped curve with one control point """
    shape_name = 'shaped_quad'
    control_points_n = 1
    fillable = True
    defaults = {
        'fill': True,
        'outline': False,
        'thickness': 0.5,
        'rel_dx': 0.2,
        'rel_dy': 0.4,
        'fixed_dx': 0,
        'fixed_dy': 0,
        'leaf_x': 3,
        'leaf_y': 3
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = ShapedQuadraticPath.defaults
        sx, sy = start_point
        ex, ey = end_point
        leaf_x = d['leaf_x']
        leaf_y = d['leaf_y']
        if thick > 0:
            leaf_x *= thick
            leaf_y *= thick

        dx = d['fixed_dx'] + abs(d['rel_dx'] * (ex - sx))
        dy = d['fixed_dy'] + abs(d['rel_dy'] * (ey - sy))
        if curve_dir_start == BOTTOM_SIDE:
            cp1 = (sx, sy + dy)
        elif curve_dir_start == TOP_SIDE:
            cp1 = (sx, sy - dy)
        elif curve_dir_start == LEFT_SIDE:
            cp1 = (sx - dx, sy)
        elif curve_dir_start == RIGHT_SIDE:
            cp1 = (sx + dx, sy)
        else:
            cp1 = (sx + dx, sy)
        control_points = [cp1]
        c = adjusted_control_point_list(sx, sy, ex, ey, control_points, curve_adjustment)
        c1x, c1y = c[0]
        if inner_only:
            path = None
        else:
            path = QtGui.QPainterPath(Pf(sx, sy))
            path.quadTo(c1x - d['leaf_x'], c1y - d['leaf_y'], ex, ey)
            path.quadTo(c1x + d['leaf_x'], c1y + d['leaf_y'], sx, sy)
        inner_path = QtGui.QPainterPath(Pf(sx, sy))
        inner_path.quadTo(c1x, c1y, ex, ey)
        return path, inner_path, control_points, c

    @staticmethod
    def icon_path(painter, rect, color=None, rel_dx=0.4, rel_dy=0, leaf_x=1, leaf_y=3):
        sx, sy = 0, 4
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.quadTo(sx + dx - leaf_x, sy + dy - leaf_y, ex, ey)
        path.quadTo(sx + dx + leaf_x, sy + dy + leaf_y, sx, sy)
        painter.fillPath(path, color)


class QuadraticPath(Shape):
    """ Single stroke curve with one control point """
    shape_name = 'quad'
    control_points_n = 1
    fillable = False
    defaults = {
        'outline': True,
        'thickness': 1.0,
        'rel_dx': 0.4,
        'rel_dy': 0.2,
        'fixed_dx': 0,
        'fixed_dy': 0
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = QuadraticPath.defaults
        sx, sy = start_point
        ex, ey = end_point
        dx = d['fixed_dx'] + abs(d['rel_dx'] * (ex - sx))
        dy = d['fixed_dy'] + abs(d['rel_dy'] * (ey - sy))
        if curve_dir_start == BOTTOM_SIDE:
            cp1 = (sx, sy + dy)
        elif curve_dir_start == TOP_SIDE:
            cp1 = (sx, sy - dy)
        elif curve_dir_start == LEFT_SIDE:
            cp1 = (sx - dx, sy)
        elif curve_dir_start == RIGHT_SIDE:
            cp1 = (sx + dx, sy)
        else:
            cp1 = (sx + dx, sy)
        control_points = [cp1]
        path = QtGui.QPainterPath(Pf(sx, sy))
        c = adjusted_control_point_list(sx, sy, ex, ey, control_points, curve_adjustment)
        c1x, c1y = c[0]
        path.quadTo(c1x, c1y, ex, ey)
        return path, path, control_points, c

    @staticmethod
    def icon_path(painter, rect, color=None, rel_dx=0.4, rel_dy=0):
        sx, sy = 0, 4
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.quadTo(sx + dx, sy + dy, ex, ey)
        painter.drawPath(path)


class ShapedLinearPath(Shape):
    """ A straight line with a slight leaf shape """
    shape_name = 'shaped_linear'
    control_points_n = 0
    fillable = True
    defaults = {
        'fill': True,
        'outline': False,
        'thickness': 0.5,
        'leaf_x': 2,
        'leaf_y': 1.5
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = ShapedLinearPath.defaults
        sx, sy = start_point
        dx, dy = end_point
        lx = d['leaf_x']
        ly = d['leaf_y']
        if thick > 0:
            lx *= thick
            ly *= thick

        c = [(dx - lx, dy - ly), (dx + lx, dy - ly)]
        if inner_only:
            path = None
        else:
            path = QtGui.QPainterPath(Pf(sx, sy))
            path.quadTo(c[0][0], c[0][1], dx, dy)
            path.quadTo(c[1][0], c[1][1], sx, sy)
        inner_path = QtGui.QPainterPath(Pf(sx, sy))
        inner_path.lineTo(dx, dy)
        return path, inner_path, [], []

    @staticmethod
    def icon_path(painter, rect, color=None, leaf_x=4, leaf_y=4):
        sx, sy = 0, 0
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.quadTo(ex - leaf_x, ey - leaf_y, ex, ey)
        path.quadTo(ex + leaf_x, ey - leaf_y, sx, sy)
        painter.fillPath(path, color)


class LinearPath(Shape):
    """ A straight line """
    shape_name = 'linear'
    control_points_n = 0
    fillable = False
    defaults = {
        'outline': True,
        'thickness': 1.0,
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = LinearPath.defaults
        sx, sy = start_point
        dx, dy = end_point
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.lineTo(dx, dy)
        return path, path, [], []  # [] = control_points

    @staticmethod
    def icon_path(painter, rect, color=None):
        sx, sy = 0, 0
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        path = QtGui.QPainterPath(Pf(sx, sy))
        path.lineTo(ex, ey)
        painter.drawPath(path)


class BlobPath(Shape):
    """ A blob-like shape that stretches between the end points """
    shape_name = 'blob'
    control_points_n = 0
    fillable = True
    defaults = {
        'fill': True,
        'outline': False,
        'thickness': 0.5,
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = BlobPath.defaults
        if start:
            scx, scy = start.current_scene_position
        else:
            scx, scy = start_point
        if end:
            ecx, ecy = end.current_scene_position
        else:
            ecx, ecy = end_point
        thickness = d['thickness']
        if thick > 0:
            thickness *= thick
        t2 = thickness * 2

        sx, sy = start_point
        ex, ey = end_point

        inner_path = QtGui.QPainterPath(Pf(sx, sy))
        inner_path.lineTo(ex, ey)

        if inner_only:
            return None, inner_path, []

        if start:
            sx1, sy1, sw, sh = start.boundingRect().getRect()
        else:
            sx1 = -2
            sy1 = -2
            sw = 4
            sh = 4
        if end:
            ex1, ey1, ew, eh = end.boundingRect().getRect()
        else:
            ex1 = -2
            ey1 = -2
            ew = 4
            eh = 4

        sx1 += scx
        sy1 += scy
        ex1 += ecx
        ey1 += ecy
        c1x = (scx + ecx) / 2
        c1y = (scy + ecy) / 2
        path1 = QtGui.QPainterPath()
        path1.addEllipse(sx1 - thickness, sy1 - thickness, sw + t2, sh + t2)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(sx1, sy1, sw, sh)

        path2 = QtGui.QPainterPath()
        path2.addEllipse(ex1 - thickness, ey1 - thickness, ew + t2, eh + t2)
        path2neg = QtGui.QPainterPath()
        path2neg.addEllipse(ex1, ey1, ew, eh)
        path3 = QtGui.QPainterPath()
        path3.moveTo(sx1, scy)
        path3.quadTo(c1x, c1y, ex1, ecy)
        path3.lineTo(ex1 + ew, ecy)
        path3.quadTo(c1x, c1y, sx1 + sw, scy)
        path = path1 | path2 | path3
        path = path.subtracted(path1neg)
        path = path.subtracted(path2neg)
        return path.simplified(), inner_path, [], []

    @staticmethod
    def icon_path(painter, rect, color=None, thickness=3):
        sx, sy = 0, 0
        t2 = thickness * 2
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        rl = w / 8.0
        ru = h / 6.0
        rw = w / 6.0
        rh = rw / 2
        el = w - rl - rw
        eu = h - ru - rh
        c1x = (el - rl) / 2
        c1y = (eu - ru) / 2

        path1 = QtGui.QPainterPath()
        path1.addEllipse(rl - thickness, ru - thickness, rw + t2, rh + t2)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(rl, ru, rw, rh)
        path2 = QtGui.QPainterPath()
        path2.addEllipse(el - thickness, eu - thickness, rw + t2, rh + t2)
        path2neg = QtGui.QPainterPath()
        path2neg.addEllipse(el, eu, rw, rh)
        path3 = QtGui.QPainterPath()
        path3.moveTo(rl, ru)
        path3.quadTo(c1x, c1y, el, eu)
        path3.lineTo(el + rw, eu + rh)
        path3.quadTo(c1x, c1y, rl + rw, ru + rh)
        path = path1 | path2 | path3
        path = path.subtracted(path1neg)
        path = path.subtracted(path2neg)
        painter.fillPath(path, color)


class DirectionalBlobPath(Shape):
    """ A blob-like shape that stretches between the end points """
    shape_name = 'directional_blob'
    control_points_n = 0
    fillable = True
    defaults = {
        'fill': True,
        'outline': False,
        'thickness': 0.5,
    }

    @staticmethod
    def path(start_point, end_point, curve_adjustment, curve_dir_start, curve_dir_end,
             inner_only=False, thick=1, start=None, end=None, d=None):
        if not d:
            d = DirectionalBlobPath.defaults
        if start:
            scx, scy = start.current_scene_position
        else:
            scx, scy = start_point
        if end:
            ecx, ecy = end.current_scene_position
        else:
            ecx, ecy = end_point
        inner_path = QtGui.QPainterPath(Pf(scx, scy))
        inner_path.lineTo(ecx, ecy)
        if inner_only:
            return None, inner_path, [], []
        thickness = d['thickness']
        t2 = thickness * 2
        if thick > 1:
            start_ball = start  # and start.has_visible_label()
            if start_ball:
                sx1, sy1, sw, sh = start.boundingRect().getRect()
            else:
                sx1, sy1, sw, sh = 0, 0, 0, 0
            end_ball = end  # and end.has_visible_label()
            if end_ball:
                ex1, ey1, ew, eh = end.boundingRect().getRect()
            else:
                ex1, ey1, ew, eh = 0, 0, 0, 0
            sx1 += scx
            sy1 += scy
            ex1 += ecx
            ey1 += ecy
            c1x = (scx + ecx) / 2
            c1y = (scy + ecy) / 2
            path1 = QtGui.QPainterPath()
            if start_ball:
                path1.addEllipse(sx1 - thickness, sy1 - thickness, sw + t2, sh + t2)
            path2 = QtGui.QPainterPath()
            if end_ball:
                path2.addEllipse(ex1 - thickness, ey1 - thickness, ew + t2, eh + t2)
            path3 = QtGui.QPainterPath()
            path3.moveTo(sx1, scy)
            path3.quadTo(c1x, c1y, ex1, ecy)
            path3.lineTo(ex1 + ew, ecy)
            path3.quadTo(c1x, c1y, sx1 + sw, scy)
            path = path1 | path2 | path3
            if start_ball:
                path1neg = QtGui.QPainterPath()
                path1neg.addEllipse(sx1, sy1, sw, sh)
                path = path.subtracted(path1neg)
            if end_ball:
                path2neg = QtGui.QPainterPath()
                path2neg.addEllipse(ex1, ey1, ew, eh)
                path = path.subtracted(path2neg)
        else:
            sx, sy = start_point
            if end:
                balls = True
                if end.has_visible_label():
                    ex1, ey1, ew, eh = end.boundingRect().getRect()
                else:
                    ex1, ey1, ew, eh = -5, -5, 10, 10
            else:
                balls = False
                ex1 = -1
                ey1 = -1
                ew = 2
                eh = 2

            ex1 += ecx
            ey1 += ecy
            c1x = (sx + ecx) / 2
            c1y = (sy + ecy) / 2
            path = QtGui.QPainterPath()
            path.moveTo(sx, sy)
            path.quadTo(c1x, c1y, ex1, ecy)
            path.lineTo(ex1 + ew, ecy)
            path.quadTo(c1x, c1y, sx, sy)
            if balls:
                path1 = QtGui.QPainterPath()
                path1neg = QtGui.QPainterPath()
                path1.addEllipse(ex1 - thickness, ey1 - thickness, ew + t2, eh + t2)
                path1neg.addEllipse(ex1, ey1, ew, eh)
                path |= path1
                path = path.subtracted(path1neg)

        return path.simplified(), inner_path, [], []

    @staticmethod
    def icon_path(painter, rect, color=None, thickness=3):
        sx, sy = 0, 0
        t2 = thickness * 2
        w = rect.width()
        h = rect.height()
        ex, ey = w, h
        rl = w / 8.0
        ru = h / 6.0
        rw = w / 6.0
        rh = rw / 2
        el = w - rl - rw
        eu = h - ru - rh
        c1x = (el - rl) / 2
        c1y = (eu - ru) / 2

        path1 = QtGui.QPainterPath()
        path1.addEllipse(rl - thickness, ru - thickness, rw + t2, rh + t2)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(rl, ru, rw, rh)
        path2 = QtGui.QPainterPath()
        path2.addEllipse(el - thickness, eu - thickness, rw + t2, rh + t2)
        path2neg = QtGui.QPainterPath()
        path2neg.addEllipse(el, eu, rw, rh)
        path3 = QtGui.QPainterPath()
        path3.moveTo(rl, ru)
        path3.quadTo(c1x, c1y, el, eu)
        path3.lineTo(el + rw, eu + rh)
        path3.quadTo(c1x, c1y, rl + rw, ru + rh)
        path = path1 | path2 | path3
        path = path.subtracted(path1neg)
        path = path.subtracted(path2neg)
        painter.fillPath(path, color)


NoPath = Shape

available_shapes = [ShapedCubicPath, CubicPath, ShapedQuadraticPath, QuadraticPath,
                    ShapedLinearPath, LinearPath, BlobPath, DirectionalBlobPath]  # NoPath


def draw_circle(painter, x, y, end_spot_size):
    painter.drawEllipse(x - end_spot_size + 1, y - end_spot_size + 1, 2 * end_spot_size,
                        2 * end_spot_size)


def draw_plus(painter, x, y):
    x = int(x)
    y = int(y)
    painter.drawLine(x - 1, y + 1, x + 3, y + 1)
    painter.drawLine(x + 1, y - 1, x + 1, y + 3)


def draw_leaf(painter, x, y, radius):
    shift = 0.4 * radius
    minor_shift = 0.2 * radius
    path = QtGui.QPainterPath(QtCore.QPointF(x, y - radius))

    # leaf part
    path.cubicTo(x + radius + minor_shift, y - radius, x, y, x + minor_shift, y + radius)
    path.cubicTo(x - shift, y + radius, x - radius, y - radius, x, y - radius)
    painter.fillPath(path, painter.brush())
    painter.drawPath(path)
    # leaf stem
    path = QtGui.QPainterPath(QtCore.QPointF(x + shift, y - radius - shift))
    path.cubicTo(x, y - radius, x - minor_shift, y, x + minor_shift, y + radius)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    # path.addRect(x - radius, y - radius, radius * 2, radius * 2) # for debugging
    painter.drawPath(path)


def draw_tailed_leaf(painter, x, y, radius):
    leaf_top = y - radius
    shift = 0.4 * radius
    minor_shift = 0.2 * radius
    # leaf part
    path = QtGui.QPainterPath(QtCore.QPointF(x, leaf_top))

    path.cubicTo(x + radius + minor_shift, leaf_top, x, y, x + minor_shift, y + radius)
    path.cubicTo(x - shift, y + radius, x - radius, leaf_top, x, leaf_top)
    painter.fillPath(path, painter.brush())
    painter.drawPath(path)
    # stem part
    path = QtGui.QPainterPath(QtCore.QPointF(x + shift, y - radius - shift))
    path.cubicTo(x, y - radius, x - minor_shift, y + shift, x + minor_shift, y + radius)
    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    painter.drawPath(path)


def draw_x(painter, x, y, end_spot_size):
    x = int(x)
    y = int(y)
    painter.drawLine(x - end_spot_size, y - end_spot_size, x + end_spot_size, y + end_spot_size)
    painter.drawLine(x - end_spot_size, y + end_spot_size, x + end_spot_size, y - end_spot_size)


def draw_triangle(painter, x, y, r=10):
    path = QtGui.QPainterPath(QtCore.QPointF(x - r, y + r))
    path.lineTo(x, y)
    path.lineTo(x + r, y + r)
    path.lineTo(x - r, y + r)
    painter.drawPath(path)


SHAPE_PRESETS = OrderedDict([(od.shape_name, od) for od in available_shapes])

low_arc = QuadraticPath.defaults.copy()
# noinspection PyTypeChecker
low_arc['shape_name'] = 'low_arc'
low_arc['rel_dx'] = 1.0
low_arc['rel_dy'] = 0.5
low_arc['fixed_dx'] = 0
low_arc['fixed_dy'] = 40
SHAPE_PRESETS['low_arc'] = QuadraticPath
