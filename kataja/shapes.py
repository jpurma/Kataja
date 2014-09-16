from collections import OrderedDict
from math import sin, cos, pi, acos

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QPointF as Pf
from kataja.globals import LEFT, RIGHT, NO_ALIGN
from utils import time_me

__author__ = 'purma'



pipi = pi * 2.0

outline_stroker = QtGui.QPainterPathStroker()
outline_stroker.setWidth(4)


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


def shaped_cubic_path(self, relative=True, rel_dx=0.2, rel_dy=0.2, fixed_dx=20, fixed_dy=15, leaf_x=1, leaf_y=3):
    """ Two point leaf-shaped curve """
    sx, sy, sz = self.start_point
    ex, ey, ez = self.end_point
    # edges that go to wrong direction have stronger curvature

    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        if (self.align is LEFT and sx <= ex) or (self.align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if self.align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if self.align is LEFT or self.align is RIGHT:
        self.control_points = [(sx + dx, sy + dy, sz), (ex, ey - dy, ez)]
    else:
        self.control_points = [(sx, sy + dy, sz), (ex, ey - dy, ez)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0] - leaf_x, c[1], c[2], c[3] + leaf_y, ex, ey)
    path.cubicTo(c[2], c[3] - leaf_y, c[0] + leaf_x, c[1], sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


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


def cubic_path(self, relative=True, rel_dx=0.2, rel_dy=0.2, fixed_dx=20, fixed_dy=15):
    """ Two point narrow curve """
    sx, sy, sz = self.start_point
    ex, ey, ez = self.end_point
    # edges that go to wrong direction have stronger curvature

    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        if (self.align is LEFT and sx <= ex) or (self.align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if self.align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if self.align is LEFT or self.align is RIGHT:
        self.control_points = [(sx + dx, sy + dy, sz), (ex, ey - dy, ez)]
    else:
        self.control_points = [(sx, sy + dy, sz), (ex, ey - dy, ez)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0], c[1], c[2], c[3], ex, ey)
    self.middle_point = path.pointAtPercent(0.5)
    return path


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


def shaped_quadratic_path(self, relative=True, rel_dx=0.2, rel_dy=0, fixed_dx=20, fixed_dy=0, leaf_x=3, leaf_y=3): 
    """ One point leaf-shaped curve with curvature relative to line length """

    sx, sy, sz = self.start_point
    ex, ey, ez = self.end_point
    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        # edges that go to wrong direction have stronger curvature
        if (self.align is LEFT and sx <= ex) or (self.align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if self.align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if self.align is LEFT or self.align is RIGHT:
        self.control_points = [(sx + dx, sy + dy, sz)]
    else:
        self.control_points = [(sx, sy + dy, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0] - leaf_x, c[1] - leaf_y, ex, ey)
    path.quadTo(c[0] + leaf_x, c[1] + leaf_y, sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path

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

def quadratic_path(self, relative=True, rel_dx=0.2, rel_dy=0, fixed_dx=20, fixed_dy=0):  
    """ One point curve with curvature relative to line length """
    sx, sy, sz = self.start_point
    ex, ey, ez = self.end_point
    if relative:
        dx = rel_dx * (ex - sx)
        dy = rel_dy * (ey - sy)
        # edges that go to wrong direction have stronger curvature
        if (self.align is LEFT and sx <= ex) or (self.align is RIGHT and sx >= ex):
            dx *= -2
    else:
        if self.align is LEFT:
            dx = -fixed_dx
        else:
            dx = fixed_dx
        dy = fixed_dy
    if self.align is LEFT or self.align is RIGHT:
        self.control_points = [(sx + dx, sy + dy, sz)]
    else:
        self.control_points = [(sx, sy + dy, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0], c[1], ex, ey)
    self.middle_point = path.pointAtPercent(0.5)
    return path


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


def shaped_linear_path(self, leaf_x=2, leaf_y=2):
    """ A straight line with a slight leaf shape """
    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    self.control_points = []
    if self.align is RIGHT:
        leaf_x*=2
        leaf_y*=2
    c = [(dx - leaf_x, dy - leaf_y, sz), (dx + leaf_x, dy - leaf_y, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.quadTo(c[0][0], c[0][1], dx, dy)
    path.quadTo(c[1][0], c[1][1], sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path

def shaped_linear_icon(painter, rect, color=None, leaf_x=4, leaf_y=4):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.quadTo(ex - leaf_x, ey - leaf_y, ex, ey)
    path.quadTo(ex + leaf_x, ey - leaf_y, sx, sy)
    painter.fillPath(path, color)


def linear_path(self):
    """ Just a straight line """
    sx, sy, dummy = self.start_point
    dx, dy, dummy = self.end_point
    self.control_points = []
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.lineTo(dx, dy)
    self.middle_point = path.pointAtPercent(0.5)
    return path

def linear_icon(painter, rect, color=None):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.lineTo(ex, ey)
    painter.drawPath(path)



def blob_path(self, thickness=4):
    """ Surround the node with circular shape that stretches to other node """
    scx, scy, scz = self.start.get_current_position()
    ecx, ecy, ecz = self.end.get_current_position()
    t2 = thickness*2

    sx, sy, sz = self.start_point
    ex, ey, dummy = self.end_point
    sx1, sy1, sw, sh = self.start.boundingRect().getRect()
    ex1, ey1, ew, eh = self.end.boundingRect().getRect()
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
    self.middle_point = Pf(c1x, c1y)
    self.control_points = []

    return path.simplified()

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


def directional_blob_path(self, thickness=4):
    """ Surround the node with circular shape that stretches to other node """
    scx, scy, scz = self.start.get_current_position()
    ecx, ecy, ecz = self.end.get_current_position()
    t2 = thickness*2
    if self.align is LEFT:
        sx, sy, sz = self.start_point
        ex1, ey1, ew, eh = self.end.boundingRect().getRect()
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
        sx1, sy1, sw, sh = self.start.boundingRect().getRect()
        ex1, ey1, ew, eh = self.end.boundingRect().getRect()
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
    self.middle_point = Pf(c1x, c1y)
    self.control_points = []
    return path.simplified()

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

SHAPE_PRESETS = OrderedDict(
    [('shaped_cubic',
      {'method': shaped_cubic_path,
       'fill': True, 'pen': 'thin',
       'icon': shaped_cubic_icon}),
     ('cubic',
      {'method': cubic_path,
       'fill': False,
       'pen': 'thick',
       'icon': cubic_icon}),
     ('shaped_quadratic',
      {'method': shaped_quadratic_path,
       'fill': True,
       'pen': 'thin',
       'icon': shaped_quadratic_icon}),
     ('quadratic',
      {'method': quadratic_path,
       'fill': False,
       'pen': 'thick',
       'icon': quadratic_icon}),
     ('shaped_linear',
      {'method': shaped_linear_path,
       'fill': True,
       'pen': 'thin',
       'icon': shaped_linear_icon}),
     ('linear',
      {'method': linear_path,
       'fill': False,
       'pen': 'thin',
       'icon': linear_icon}),
     ('blob',
      {'method': blob_path,
       'fill': True,
       'pen': None,
       'icon': blob_icon}),
     ('directional_blob',
      {'method': directional_blob_path,
       'fill': True,
       'pen': None,
       'icon': directional_blob_icon}),
     ('no draw',
      {'method': linear_path,
       'fill': False,
       'pen': None,
       'icon': no_path_icon})])
