from collections import OrderedDict
from math import sin, cos, pi, acos

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QPointF as Pf
from kataja.globals import LEFT, RIGHT, NO_ALIGN

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


def shaped_relative_cubic_path(self):
    """ Two point leaf-shaped curve with curvature relative to line length """
    sx, sy, sz = self.start_point
    ex, ey, ez = self.end_point
    dx = 0.2 * (ex - sx)
    dy = 0.2 * (ey - sy)
    if (self.align is LEFT and sx <= ex) or (
                    self.align is RIGHT and sx >= ex):  # edges that go to wrong direction have stronger curvature
        dx *= -2
    if self.align is LEFT or self.align is RIGHT:
        self.control_points = [(sx + dx, sy + dy, sz), (ex, ey - dy, ez)]
    else:
        self.control_points = [(sx, sy + dy, sz), (ex, ey - dy, ez)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0] - 1, c[1], c[2], c[3] + 3, ex, ey)
    path.cubicTo(c[2], c[3] - 3, c[0] + 1, c[1], sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path

def shaped_relative_cubic_icon(painter, rect, pen, brush):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    dx = 0.4 * (ex - sx)
    dy = 0.8 * (ey - sy)
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.cubicTo(sx + dx - 1, sy + dy , ex, ey - dy + 3, ex, ey)
    path.cubicTo(ex, ey - dy - 3, sx + dx + 1, sy + dy, sx, sy)
    painter.setPen(pen)
    painter.setBrush(pen)
    painter.fillPath(path, pen)

def relative_cubic_path(self):
    """ Two point curve with curvature relative to line length """
    sx, sy, sz = self.start_point
    ex, ey, ez = self.end_point
    dx = 0.2 * (ex - sx)
    dy = 0.2 * (ey - sy)
    if (self.align is LEFT and sx <= ex) or (
                    self.align is RIGHT and sx >= ex):  # edges that go to wrong direction have stronger curvature
        dx *= -2
    if self.align is LEFT or self.align is RIGHT:
        self.control_points = [(sx + dx, sy + dy, sz), (ex, ey - dy, ez)]
    else:
        self.control_points = [(sx, sy + dy, sz), (ex, ey - dy, ez)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0], c[1], c[2], c[3], ex, ey)
    self.middle_point = path.pointAtPercent(0.5)
    return path

def relative_cubic_icon(painter, rect, pen, brush):
    sx, sy = 0, 0
    w = rect.width()
    h = rect.height()
    ex, ey = w, h
    dx = 0.4 * (ex - sx)
    dy = 0.8 * (ey - sy)
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.cubicTo(sx + dx, sy + dy, ex, ey - dy, ex, ey)
    painter.setPen(pen)
    painter.drawPath(path)


def shaped_fixed_cubic_path(self):
    """ Two point leaf-shaped curve with fixed curvature """
    sx, sy, sz = self.start_point
    dx, dy, dz = self.end_point
    if self.align is LEFT:
        self.control_points = [(sx - 20, sy + 15, sz), (dx, dy - 15, dz)]
    elif self.align is RIGHT:
        self.control_points = [(sx + 20, sy + 15, sz), (dx, dy - 15, dz)]
    else:
        self.control_points = [(sx, sy + 15, sz), (dx, dy - 15, dz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0] - 1, c[1], c[2], c[3] + 3, dx, dy)
    path.cubicTo(c[2], c[3] - 3, c[0] + 1, c[1], sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path



def fixed_cubic_path(self):
    """ Two point curve with fixed curvature """
    sx, sy, sz = self.start_point
    dx, dy, dz = self.end_point
    if self.align is LEFT:
        self.control_points = [(sx - 20, sy + 15, sz), (dx, dy - 15, dz)]
    elif self.align is RIGHT:
        self.control_points = [(sx + 20, sy + 15, sz), (dx, dy - 15, dz)]
    else:
        self.control_points = [(sx, sy + 15, sz), (dx, dy - 15, dz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0], c[1], c[2], c[3], dx, dy)
    self.middle_point = path.pointAtPercent(0.5)
    return path


def shaped_relative_quadratic_path(self):  # align 0=none, 1=left, 2=right
    """ One point leaf-shaped curve with curvature relative to line length """

    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    diff_x = 0.2 * (sx - dx)
    if (self.align is LEFT and sx <= dx) or (self.align is RIGHT and sx >= dx):
        diff_x *= -2
    if self.align is NO_ALIGN:
        self.control_points = [(sx, sy, sz)]
    else:
        self.control_points = [(sx - diff_x, sy, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0] - 3, c[1] - 3, dx, dy)
    path.quadTo(c[0] + 3, c[1] + 3, sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


def relative_quadratic_path(self):  # align 0=none, 1=left, 2=right
    """ One point curve with curvature relative to line length """
    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    diff_x = 0.2 * (sx - dx)
    if (self.align is LEFT and sx <= dx) or (self.align is RIGHT and sx >= dx):
        diff_x *= -2
    if self.align is NO_ALIGN:
        self.control_points = [(sx, sy, sz)]
    else:
        self.control_points = [(sx - diff_x, sy, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0], c[1], dx, dy)
    self.middle_point = path.pointAtPercent(0.5)
    return path


def shaped_fixed_quadratic_path(self):
    """ One point leaf-shaped curve with fixed curvature """
    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    if self.align is NO_ALIGN:
        self.control_points = [(sx - 20, sy + 15, sz)]
    elif self.align is LEFT:
        self.control_points = [(sx - 20, sy + 15, sz)]
    elif self.align is RIGHT:
        self.control_points = [(sx + 20, sy + 15, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0] - 3, c[1] - 3, dx, dy)
    path.quadTo(c[0] + 3, c[1] + 3, sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


def fixed_quadratic_path(self):
    """ One point curve with fixed curvature """
    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    if self.align is NO_ALIGN:
        self.control_points = [(sx - 20, sy + 15, sz)]
    elif self.align is LEFT:
        self.control_points = [(sx - 20, sy + 15, sz)]
    elif self.align is RIGHT:
        self.control_points = [(sx + 20, sy + 15, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0], c[1], dx, dy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


def shaped_fixed_linear_path(self):
    """ A straight line with a slight leaf shape """
    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    self.control_points = []
    if self.align is NO_ALIGN:
        x_diff = 2
        y_diff = 2
    elif self.align is LEFT:
        x_diff = 2
        y_diff = 2
    elif self.align is RIGHT:
        x_diff = 4
        y_diff = 4
    else:
        print("Unknown align value in Edge: ", self)
        x_diff = 2
        y_diff = 2
    c = [(dx - x_diff, dy - y_diff, sz), (dx + x_diff, dy - y_diff, sz)]
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.quadTo(c[0][0], c[0][1], dx, dy)
    path.quadTo(c[1][0], c[1][1], sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


def linear_path(self):
    """ Just a straight line """
    sx, sy, dummy = self.start_point
    dx, dy, dummy = self.end_point
    self.control_points = []
    path = QtGui.QPainterPath(Pf(sx, sy))
    path.lineTo(dx, dy)
    self.middle_point = path.pointAtPercent(0.5)
    return path


def blob_path(self):
    """ Surround the node with circular shape that stretches to other node """
    scx, scy, scz = self.start.get_current_position()
    ecx, ecy, ecz = self.end.get_current_position()

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
    path1.addEllipse(sx1 - 4, sy1 - 4, sw + 8, sh + 8)
    path1neg = QtGui.QPainterPath()
    path1neg.addEllipse(sx1, sy1, sw, sh)

    path2 = QtGui.QPainterPath()
    path2.addEllipse(ex1 - 4, ey1 - 4, ew + 8, eh + 8)
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


def directional_blob_path(self):
    """ Surround the node with circular shape that stretches to other node """
    scx, scy, scz = self.start.get_current_position()
    ecx, ecy, ecz = self.end.get_current_position()
    if self.align is LEFT:
        sx, sy, sz = self.start_point
        ex1, ey1, ew, eh = self.end.boundingRect().getRect()
        ex1 += ecx
        ey1 += ecy
        c1x = (sx + ecx) / 2
        c1y = (sy + ecy) / 2
        path1 = QtGui.QPainterPath()
        path1.addEllipse(ex1 - 4, ey1 - 4, ew + 8, eh + 8)
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
        path1.addEllipse(sx1 - 4, sy1 - 4, sw + 8, sh + 8)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(sx1, sy1, sw, sh)
        path2 = QtGui.QPainterPath()
        path2.addEllipse(ex1 - 4, ey1 - 4, ew + 8, eh + 8)
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

SHAPE_PRESETS = OrderedDict(
    [('shaped_relative_cubic',
      {'method': shaped_relative_cubic_path,
       'fill': True, 'pen': 'thin',
       'icon': shaped_relative_cubic_icon}),
     ('blob',
      {'method': blob_path,
       'fill': True,
       'pen': None,
       'icon': shaped_relative_cubic_icon}),
     ('directional_blob',
      {'method': directional_blob_path,
       'fill': True,
       'pen': None,
       'icon': shaped_relative_cubic_icon}),
     ('relative_cubic',
      {'method': relative_cubic_path,
       'fill': False,
       'pen': 'thick',
       'icon': relative_cubic_icon}),
     ('shaped_fixed_cubic',
      {'method': shaped_fixed_cubic_path,
       'fill': True,
       'pen': 'thin',
       'icon': shaped_relative_cubic_icon}),
     ('fixed_cubic',
      {'method': fixed_cubic_path,
       'fill': False,
       'pen': 'thick',
       'icon': shaped_relative_cubic_icon}),
     ('shaped_relative_quadratic',
      {'method': shaped_relative_quadratic_path,
       'fill': True,
       'pen': 'thin',
       'icon': shaped_relative_cubic_icon}),
     ('relative_quadratic',
      {'method': relative_quadratic_path,
       'fill': False,
       'pen': 'thick',
       'icon': shaped_relative_cubic_icon}),
     ('shaped_fixed_quadratic',
      {'method': shaped_fixed_quadratic_path,
       'fill': True,
       'pen': 'thin',
       'icon': shaped_relative_cubic_icon}),
     ('fixed_quadratic',
      {'method': fixed_quadratic_path,
       'fill': False,
       'pen': 'thick',
       'icon': shaped_relative_cubic_icon}),
     ('shaped_fixed_linear',
      {'method': shaped_fixed_linear_path,
       'fill': True,
       'pen': 'thin',
       'icon': shaped_relative_cubic_icon}),
     ('linear',
      {'method': linear_path,
       'fill': False,
       'pen': 'thin',
       'icon': shaped_relative_cubic_icon}),
     ('no draw',
      {'method': linear_path,
       'fill': False,
       'pen': None,
       'icon': shaped_relative_cubic_icon})])
