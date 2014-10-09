from collections import OrderedDict
from math import sin, cos, pi, acos

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QPointF as Pf
from kataja.globals import LEFT, RIGHT, NO_ALIGN
from kataja.utils import time_me

__author__ = 'purma'



pipi = pi * 2.0

outline_stroker = QtGui.QPainterPathStroker()
outline_stroker.setWidth(4)



def adjusted_control_point_list(control_points, adjust):
    """ List where control points and their adjustments are added up, and (x,y) tuples
    are break down into one big list x1, y1, x2, y2,... to be used in path construction
    :return: list
    """
    l = []
    la = len(adjust)
    for i, cp in enumerate(control_points):
        if la <= i:
            l.append(cp[0])
            l.append(cp[1])
        else:
            l.append(cp[0] + adjust[i][0])
            l.append(cp[1] + adjust[i][1])
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
    painter.setBrush(self._pen.color())
    painter.drawLine(l)
    l2x = l.p2().x()
    l2 = l.p2()
    l2y = l.p2().y()
    back = self._arrow_size / -2
    # Draw the arrows if there's enough room.
    if l.length() + back > 0:
        angle = acos(l.dx() / l.length())
    else:
        return
    prop = back / l.length()
    if l.dy() >= 0:
        angle = pipi - angle
    destArrowP1 = Pf((sin(angle - pi / 3) * self._arrow_size) + l2x, (cos(angle - pi / 3) * self._arrow_size) + l2y)
    destArrowP2 = Pf((sin(angle - pi + pi / 3) * self._arrow_size) + l2x,
                     (cos(angle - pi + pi / 3) * self._arrow_size) + l2y)
    l2c = Pf(l.dx() * prop + l2x, l.dy() * prop + l2y)
    painter.drawPolygon(QtGui.QPolygonF([l2, destArrowP1, l2c, destArrowP2]))


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


def to_Pf(triple):
    """

    :param triple:
    :return:
    """
    return Pf(triple[0], triple[1])


def shaped_cubic_path(start_point=None, end_point=None, adjust=None, align=LEFT, relative=True, rel_dx=0.2, rel_dy=0.2,
                      fixed_dx=20, fixed_dy=15, leaf_x=1, leaf_y=3, **kwargs):
    """ Two point leaf-shaped curve
    :param kwargs: relative=True, rel_dx=0.2, rel_dy=0.2, fixed_dx=20, fixed_dy=15, leaf_x=1, leaf_y=3
    """
    sx, sy, sz = start_point
    ex, ey, ez = end_point
    # edges that go to wrong direction have stronger curvature

    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        if (align is LEFT and sx <= ex) or (align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if align is LEFT or align is RIGHT:
        control_points = [(sx + dx, sy + dy, sz), (ex, ey - dy, ez)]
    else:
        control_points = [(sx, sy + dy, sz), (ex, ey - dy, ez)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = adjusted_control_point_list(control_points, adjust)
    path.cubicTo(c[0] - leaf_x, c[1], c[2], c[3] + leaf_y, ex, ey)
    path.cubicTo(c[2], c[3] - leaf_y, c[0] + leaf_x, c[1], sx, sy)
    inner_path = QtGui.QPainterPath(Pf(sx, sy))
    inner_path.cubicTo(c[0], c[1], c[2], c[3], ex, ey)
    return path, inner_path, control_points


def shaped_cubic_icon(painter, rect, color=None, rel_dx=0.4, rel_dy=0.8, leaf_x=1, leaf_y=3):
    sx, sy = 0, 4
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    dx = rel_dx * (ex - sx)
    dy = rel_dy * (ey - sy)
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.cubicTo(sx + dx - leaf_x, sy + dy , ex, ey - dy + leaf_y, ex, ey)
    path.cubicTo(ex, ey - dy - leaf_y, sx + dx + leaf_x, sy + dy, sx, sy)
    painter.fillPath(path, color)


def cubic_path(start_point=None, end_point=None, adjust=None, align=LEFT, relative=True, rel_dx=0.2, rel_dy=0.2, fixed_dx=20, fixed_dy=15, **kwargs):
    """ Two point narrow curve
    :param kwargs:
    """
    sx, sy, sz = start_point
    ex, ey, ez = end_point
    # edges that go to wrong direction have stronger curvature

    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        if (align is LEFT and sx <= ex) or (align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if align is LEFT or align is RIGHT:
        control_points = [(sx + dx, sy + dy, sz), (ex, ey - dy, ez)]
    else:
        control_points = [(sx, sy + dy, sz), (ex, ey - dy, ez)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = adjusted_control_point_list(control_points, adjust)
    path.cubicTo(c[0], c[1], c[2], c[3], ex, ey)
    return path, path, control_points


def cubic_icon(painter, rect, color=None, rel_dx=0.2, rel_dy=0.8):
    sx, sy = 0, 4
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    dx = rel_dx * (ex - sx)
    dy = rel_dy * (ey - sy)
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.cubicTo(sx + dx, sy + dy, ex, ey - dy, ex, ey)
    painter.drawPath(path)


def shaped_quadratic_path(start_point=None, end_point=None, adjust=None, align=LEFT, relative=True, rel_dx=0.2, rel_dy=0, fixed_dx=20, fixed_dy=0, leaf_x=3, leaf_y=3, **kwargs):
    """ One point leaf-shaped curve with curvature relative to line length
    :param kwargs:
    """

    sx, sy, sz = start_point
    ex, ey, ez = end_point
    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        # edges that go to wrong direction have stronger curvature
        if (align is LEFT and sx <= ex) or (align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if align is LEFT or align is RIGHT:
        control_points = [(sx + dx, sy + dy, sz)]
    else:
        control_points = [(sx, sy + dy, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = adjusted_control_point_list(control_points, adjust)
    path.quadTo(c[0] - leaf_x, c[1] - leaf_y, ex, ey)
    path.quadTo(c[0] + leaf_x, c[1] + leaf_y, sx, sy)
    inner_path = QtGui.QPainterPath(Pf(sx, sy))
    inner_path.quadTo(c[0], c[1], ex, ey)
    return path, inner_path, control_points

def shaped_quadratic_icon(painter, rect, color=None, rel_dx=0.4, rel_dy=0, leaf_x=1, leaf_y=3):
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

def quadratic_path(start_point=None, end_point=None, adjust=None, align=LEFT, relative=True, rel_dx=0.2, rel_dy=0, fixed_dx=20, fixed_dy=0, **kwargs):
    """ One point curve with curvature relative to line length """
    sx, sy, sz = start_point
    ex, ey, ez = end_point
    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        # edges that go to wrong direction have stronger curvature
        if (align is LEFT and sx <= ex) or (align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if align is LEFT or align is RIGHT:
        control_points = [(sx + dx, sy + dy, sz)]
    else:
        control_points = [(sx, sy + dy, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = adjusted_control_point_list(control_points, adjust)
    path.quadTo(c[0], c[1], ex, ey)
    return path, path, control_points


def quadratic_icon(painter, rect, color=None, rel_dx=0.4, rel_dy=0):
    sx, sy = 0, 4
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    dx = rel_dx * (ex - sx)
    dy = rel_dy * (ey - sy)
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.quadTo(sx + dx, sy + dy, ex, ey)
    painter.drawPath(path)


def shaped_linear_path(start_point=None, end_point=None, adjust=None, align=LEFT, leaf_x=2, leaf_y=2, **kwargs):
    """ A straight line with a slight leaf shape """
    sx, sy, sz = start_point
    dx, dy, dummy = end_point
    control_points = []
    if align is RIGHT:
        leaf_x *= 2
        leaf_y *= 2
    c = [(dx - leaf_x, dy - leaf_y, sz), (dx + leaf_x, dy - leaf_y, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.quadTo(c[0][0], c[0][1], dx, dy)
    path.quadTo(c[1][0], c[1][1], sx, sy)
    inner_path = QtGui.QPainterPath(Pf(sx, sy))
    inner_path.lineTo(dx, dy)
    return path, inner_path, control_points

def shaped_linear_icon(painter, rect, color=None, leaf_x=4, leaf_y=4):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.quadTo(ex - leaf_x, ey - leaf_y, ex, ey)
    path.quadTo(ex + leaf_x, ey - leaf_y, sx, sy)
    painter.fillPath(path, color)


def linear_path(start_point=None, end_point=None, adjust=None, align=LEFT,  **kwargs):
    """ Just a straight line """
    sx, sy, dummy = start_point
    dx, dy, dummy = end_point
    control_points = []
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.lineTo(dx, dy)
    return path, path, control_points

def linear_icon(painter, rect, color=None):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.lineTo(ex, ey)
    painter.drawPath(path)



def blob_path(start_point=None, end_point=None, adjust=None, align=LEFT, thickness=4, start=None, end=None, **kwargs):
    """ Surround the node with circular shape that stretches to other node """
    if start:
        scx, scy, scz = start.get_current_position()
    else:
        scx, scy, scz = start_point
    if end:
        ecx, ecy, ecz = end.get_current_position()
    else:
        ecx, ecy, ecz = end_point
    t2 = thickness*2

    sx, sy, sz = start_point
    ex, ey, dummy = end_point
    if start:
        sx1, sy1, sw, sh = start.boundingRect().getRect()
    else:
        sx1 = -10
        sy1 = -10
        sw = 20
        sh = 20
    if end:
        ex1, ey1, ew, eh = end.boundingRect().getRect()
    else:
        ex1 = -10
        ey1 = -10
        ew = 20
        eh = 20

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
    path = path1.united(path2)
    path = path.united(path3)
    path = path.subtracted(path1neg)
    path = path.subtracted(path2neg)
    inner_path = QtGui.QPainterPath(Pf(sx, sy))
    inner_path.lineTo(ex, ey)
    return path.simplified(), inner_path, []

def blob_icon(painter, rect, color=None, thickness=3):
    sx, sy = 0, 0
    t2 = thickness * 2
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    rl = w/8.0
    ru = h/6.0
    rw = w/6.0
    rh = rw/2
    el = w - rl - rw
    eu = h - ru - rh
    c1x = (el - rl) / 2
    c1y = (eu - ru) / 2

    path1 = QtGui.QPainterPath()
    path1.addEllipse(rl - thickness, ru - thickness, rw + t2, rh + t2)
    path1neg = QtGui.QPainterPath()
    path1neg.addEllipse(rl, ru, rw, rh)
    path = path1.subtracted(path1neg)
    path2 = QtGui.QPainterPath()
    path2.addEllipse(el - thickness, eu - thickness, rw + t2, rh + t2)
    path2neg = QtGui.QPainterPath()
    path2neg.addEllipse(el, eu, rw, rh)
    path3 = QtGui.QPainterPath()
    path3.moveTo(rl, ru)
    path3.quadTo(c1x, c1y, el, eu)
    path3.lineTo(el + rw, eu+rh)
    path3.quadTo(c1x, c1y, rl + rw, ru+rh)
    path = path1.united(path2)
    path = path.united(path3)
    path = path.subtracted(path1neg)
    path = path.subtracted(path2neg)
    painter.fillPath(path, color)


def directional_blob_path(start_point=None, end_point=None, adjust=None, align=LEFT,  thickness=4, start=None, end=None, **kwargs):
    """ Surround the node with circular shape that stretches to other node """
    if start:
        scx, scy, scz = start.get_current_position()
    else:
        scx, scy, scz = start_point
    if end:
        ecx, ecy, ecz = end.get_current_position()
    else:
        ecx, ecy, ecz = end_point
    t2 = thickness*2
    if align is LEFT:
        sx, sy, sz = start_point
        if end:
            ex1, ey1, ew, eh = end.boundingRect().getRect()
        else:
            ex1 = -10
            ey1 = -10
            ew = 20
            eh = 20

        ex1 += ecx
        ey1 += ecy
        c1x = (sx + ecx) / 2
        c1y = (sy + ecy) / 2
        path1 = QtGui.QPainterPath()
        path1.addEllipse(ex1 - thickness, ey1 - thickness, ew + t2, eh + t2)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(ex1, ey1, ew, eh)
        path2 = QtGui.QPainterPath()
        path2.moveTo(sx, sy)
        path2.quadTo(c1x, c1y, ex1, ecy)
        path2.lineTo(ex1 + ew, ecy)
        path2.quadTo(c1x, c1y, sx, sy)
        path = path1.united(path2)
        path = path.subtracted(path1neg)
    else:
        if start:
            sx1, sy1, sw, sh = start.boundingRect().getRect()
        else:
            sx1 = -10
            sy1 = -10
            sw = 20
            sh = 20
        if end:
            ex1, ey1, ew, eh = end.boundingRect().getRect()
        else:
            ex1 = -10
            ey1 = -10
            ew = 20
            eh = 20
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
        path = path1.united(path2)
        path = path.united(path3)
        path = path.subtracted(path1neg)
        path = path.subtracted(path2neg)

    inner_path = QtGui.QPainterPath(Pf(sx, sy))
    inner_path.lineTo(end_point[0], end_point[1])
    return path.simplified(), inner_path, []

def directional_blob_icon(painter, rect, color=None):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.lineTo(ex, ey)
    painter.drawPath(path)

def no_path_icon(painter, rect, color=None):
    pass

SHAPE_PRESETS = OrderedDict([
    ('shaped_cubic', {
        'method': shaped_cubic_path,
        'fill': True,
        'icon': shaped_cubic_icon,
        'control_points': 2,
        'relative': True,
        'rel_dx': 0.2,
        'rel_dy': 0.2,
        'fixed_dx': 20,
        'fixed_dy': 15,
        'leaf_x': 1,
        'leaf_y': 3}),
    ('cubic', {
        'method': cubic_path,
        'fill': False,
        'icon': cubic_icon,
        'control_points': 2,
        'relative': True,
        'rel_dx': 0.2,
        'rel_dy': 0.2,
        'fixed_dx': 20,
        'fixed_dy': 15,
        'thickness': 1}),
    ('shaped_quadratic', {
        'method': shaped_quadratic_path,
        'fill': True,
        'icon': shaped_quadratic_icon,
        'control_points': 1,
        'relative': True,
        'rel_dx': 0.2,
        'rel_dy': 0,
        'fixed_dx': 20,
        'fixed_dy': 0,
        'leaf_x': 3,
        'leaf_y': 3}),
    ('quadratic', {
        'method': quadratic_path,
        'fill': False,
        'icon': quadratic_icon,
        'control_points': 1,
        'relative': True,
        'rel_dx': 0.2,
        'rel_dy': 0,
        'fixed_dx': 20,
        'fixed_dy': 0,
        'thickness': 1}),
    ('shaped_linear', {
        'method': shaped_linear_path,
        'fill': True,
        'icon': shaped_linear_icon,
        'control_points': 0,
        'leaf_x': 2,
        'leaf_y': 2}),
    ('linear', {
        'method': linear_path,
        'fill': False,
        'icon': linear_icon,
        'control_points': 0,
        'thickness': 2}),
    ('blob', {
        'method': blob_path,
        'fill': True,
        'icon': blob_icon,
        'control_points': 1,
        'thickness': 2}),
    ('directional_blob', {
        'method': directional_blob_path,
        'fill': True,
        'icon': directional_blob_icon,
        'control_points': 1,
        'thickness': 3}),
    ('no draw', {
        'method': linear_path,
        'fill': False,
        'icon': no_path_icon,
        'control_points': 0,
        'thickness': 0})])
