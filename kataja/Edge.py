#############################################################################
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
#############################################################################

from collections import OrderedDict
from math import sin, cos, pi, acos

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF as Pf, Qt
from kataja.Controller import ctrl, prefs, colors, qt_prefs, palette
from kataja.utils import to_tuple
from kataja.TouchArea import TouchArea
from kataja.globals import CONSTITUENT_EDGE, FEATURE_EDGE, GLOSS_EDGE, ATTRIBUTE_EDGE
from kataja.ui.TwoColorIcon import TwoColorIcon, TwoColorIconEngine


pipi = pi * 2.0
# def arrowDraw

# alignment of edges -- in some cases it is good to draw left branches differently than right branches
NO_ALIGN = 0
LEFT = 1
RIGHT = 2



# Shapes

def draw_arrow_shape(self, painter):
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

    extra = (self._arrow_size) / 2.0
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
        self.control_points = ((sx + dx, sy + dy, sz), (ex, ey - dy, ez))
    else:
        self.control_points = ((sx, sy + dy, sz), (ex, ey - dy, ez))
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0] - 1, c[1], c[2], c[3] + 3, ex, ey)
    path.cubicTo(c[2], c[3] - 3, c[0] + 1, c[1], sx, sy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


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
        self.control_points = ((sx + dx, sy + dy, sz), (ex, ey - dy, ez))
    else:
        self.control_points = ((sx, sy + dy, sz), (ex, ey - dy, ez))
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.cubicTo(c[0], c[1], c[2], c[3], ex, ey)
    self.middle_point = path.pointAtPercent(0.5)
    return path


def shaped_fixed_cubic_path(self):
    """ Two point leaf-shaped curve with fixed curvature """
    sx, sy, sz = self.start_point
    dx, dy, dz = self.end_point
    if self.align is LEFT:
        self.control_points = ((sx - 20, sy + 15, sz), (dx, dy - 15, dz))
    elif self.align is RIGHT:
        self.control_points = ((sx + 20, sy + 15, sz), (dx, dy - 15, dz))
    else:
        self.control_points = ((sx, sy + 15, sz), (dx, dy - 15, dz))
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
        self.control_points = ((sx - 20, sy + 15, sz), (dx, dy - 15, dz))
    elif self.align is RIGHT:
        self.control_points = ((sx + 20, sy + 15, sz), (dx, dy - 15, dz))
    else:
        self.control_points = ((sx, sy + 15, sz), (dx, dy - 15, dz))
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
        self.control_points = ((sx, sy, sz), None)
    else:
        self.control_points = ((sx - diff_x, sy, sz), None)
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
        self.control_points = ((sx, sy, sz), None)
    else:
        self.control_points = ((sx - diff_x, sy, sz), None)
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
        self.control_points = ((sx - 20, sy + 15, sz), None)
    elif self.align is LEFT:
        self.control_points = ((sx - 20, sy + 15, sz), None)
    elif self.align is RIGHT:
        self.control_points = ((sx + 20, sy + 15, sz), None)
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
        self.control_points = ((sx - 20, sy + 15, sz), None)
    elif self.align is LEFT:
        self.control_points = ((sx - 20, sy + 15, sz), None)
    elif self.align is RIGHT:
        self.control_points = ((sx + 20, sy + 15, sz), None)
    path = QtGui.QPainterPath(Pf(sx, sy))
    c = self.adjusted_control_point_list()
    path.quadTo(c[0], c[1], dx, dy)
    self.middle_point = path.pointAtPercent(0.25)
    return path


def shaped_fixed_linear_path(self):
    """ A straight line with a slight leaf shape """
    sx, sy, sz = self.start_point
    dx, dy, dummy = self.end_point
    self.control_points = (None, None)
    if self.align is NO_ALIGN:
        x_diff = 2
        y_diff = 2
    elif self.align is LEFT:
        x_diff = 2
        y_diff = 2
    elif self.align is RIGHT:
        x_diff = 4
        y_diff = 4
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
    self.control_points = (None, None)
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
    path1.addEllipse(sx1-4, sy1-4, sw+8, sh+8)
    path1neg = QtGui.QPainterPath()
    path1neg.addEllipse(sx1, sy1, sw, sh)

    path2 = QtGui.QPainterPath()
    path2.addEllipse(ex1-4, ey1-4, ew+8, eh+8)
    path2neg = QtGui.QPainterPath()
    path2neg.addEllipse(ex1, ey1, ew, eh)
    path3 = QtGui.QPainterPath()
    path3.moveTo(sx1, scy)
    path3.quadTo(c1x, c1y, ex1, ecy)
    path3.lineTo(ex1+ew, ecy)
    path3.quadTo(c1x, c1y, sx1+sw, scy)
    path = path1.united(path2)
    path = path.united(path3)
    path = path.subtracted(path1neg)
    path = path.subtracted(path2neg)
    self.middle_point = Pf(c1x, c1y)
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
        path1.addEllipse(ex1-4, ey1-4, ew+8, eh+8)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(ex1, ey1, ew, eh)
        path2 = QtGui.QPainterPath()
        path2.moveTo(sx, sy)
        path2.quadTo(c1x, c1y, ex1, ecy)
        path2.lineTo(ex1+ew, ecy)
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
        path1.addEllipse(sx1-4, sy1-4, sw+8, sh+8)
        path1neg = QtGui.QPainterPath()
        path1neg.addEllipse(sx1, sy1, sw, sh)
        path2 = QtGui.QPainterPath()
        path2.addEllipse(ex1-4, ey1-4, ew+8, eh+8)
        path2neg = QtGui.QPainterPath()
        path2neg.addEllipse(ex1, ey1, ew, eh)
        path3 = QtGui.QPainterPath()
        path3.moveTo(sx1, scy)
        path3.quadTo(c1x, c1y, ex1, ecy)
        path3.lineTo(ex1+ew, ecy)
        path3.quadTo(c1x, c1y, sx1+sw, scy)
        path = path1.united(path2)
        path = path.united(path3)
        path = path.subtracted(path1neg)
        path = path.subtracted(path2neg)
    self.middle_point = Pf(c1x, c1y)
    return path.simplified()



SHAPE_PRESETS = OrderedDict(
    [('shaped_relative_cubic', {'method': shaped_relative_cubic_path, 'fill': True, 'pen': 'thin'}),
     ('blob', {'method': blob_path, 'fill': True, 'pen': None}),
     ('directional_blob', {'method': directional_blob_path, 'fill': True, 'pen': None}),
     ('relative_cubic', {'method': relative_cubic_path, 'fill': False, 'pen': 'thick'}),
     ('shaped_fixed_cubic', {'method': shaped_fixed_cubic_path, 'fill': True, 'pen': 'thin'}),
     ('fixed_cubic', {'method': fixed_cubic_path, 'fill': False, 'pen': 'thick'}),
     ('shaped_relative_quadratic', {'method': shaped_relative_quadratic_path, 'fill': True, 'pen': 'thin'}),
     ('relative_quadratic', {'method': relative_quadratic_path, 'fill': False, 'pen': 'thick'}),
     ('shaped_fixed_quadratic', {'method': shaped_fixed_quadratic_path, 'fill': True, 'pen': 'thin'}),
     ('fixed_quadratic', {'method': fixed_quadratic_path, 'fill': False, 'pen': 'thick'}),
     ('shaped_fixed_linear', {'method': shaped_fixed_linear_path, 'fill': True, 'pen': 'thin'}),
     ('linear', {'method': linear_path, 'fill': False, 'pen': 'thin'}),
     ('no draw', {'method': linear_path, 'fill': False, 'pen': None})])

# ('shaped_relative_linear',{'method':shapedRelativeLinearPath,'fill':True,'pen':'thin'}),



class Edge(QtWidgets.QGraphicsItem):
    """ Any connection between nodes: can be represented as curves, branches or arrows """

    saved_fields = ['forest', 'edge_type', 'adjust', 'start', 'end', '_color', '_shape_name', '_pull','_shape_visible', '_visible', '_has_outline', '_is_filled']

    def __init__(self, forest, start=None, end=None, edge_type='', direction=''):
        """

        :param Forest forest:
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param string direction:
        :param string restoring:
        """
        QtWidgets.QGraphicsItem.__init__(self)
        self.forest = forest
        self.save_key = 'R%s' % id(self)
        intern(self.save_key)

        self.start_point = (0, 0, 0)
        self.end_point = (0, 0, 0)
        self.setZValue(-1)
        self.edge_type = edge_type
        self.control_points = (None, None)
        self.adjust = [(0, 0, 0), (0, 0, 0)]

        if isinstance(direction, str):
            if direction == 'left':
                self.align = LEFT
            elif direction == 'right':
                self.align = RIGHT
            else:
                self.align = NO_ALIGN
        elif isinstance(direction, int):
            self.align = direction
        self.start = start
        self.end = end

        ### Adjustable values, defaults to ForestSettings if None for this element
        self._color = None
        self._has_outline = None
        self._pen = None
        self._pen_width = None
        self._is_filled = None
        self._brush = None
        self._shape_name = None
        self._pull = None
        self._shape_visible = None

        # self.center_point = (0, 0, 0)

        ### Derivative elements 
        self._shape_method = None
        self._shape_supports_control_points = 0
        self._path = None
        self._visible = None
        self.selectable = True
        self.draggable = False
        self.clickable = True
        self._hovering = False
        self.touch_areas = {}
        if start and end:
            self.connect_end_points(start, end)

        # self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(False)
        if not ctrl.loading:
            forest.store(self)


    def get_touch_area(self, place):
        return self.touch_areas.get(place, None)

    def is_visible(self):
        #assert (self._visible == self.isVisible())
        return self._visible

    def add_touch_area(self, touch_area):
        if touch_area.place in self.touch_areas:
            print 'Touch area already exists. Someone is confused.'
            raise
        self.touch_areas[touch_area.place] = touch_area
        return touch_area

    def remove_touch_area(self, touch_area):
        del self.touch_areas[touch_area.place]

    #### Color ############################################################

    def color(self, value = None):
        if value is None:
            if self._color is None:
                return palette.get(self.forest.settings.edge_settings(self.edge_type, 'color'))
            else:
                return palette.get(self._color)
        else:
            self._color = value

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if ctrl.pressed == self:
            return colors.active(self.color())
        elif self._hovering:
            return colors.hovering(self.color())
        elif ctrl.is_selected(self):
            return colors.selected(self.color())
        else:
            return self.color()

    #### Pen & Brush ###############################################################

    def has_outline(self, value = None):
        if value is None:
            if self._has_outline == None:
                return self.forest.settings.edge_settings(self.edge_type, 'has_outline')
            else:
                return self._has_outline
        else:
            self._has_outline = value

    def pen(self):
        return QtGui.QPen()

    def pen_width(self, value = None):
        if value is None:
            if self._pen_width == None:
                return self.forest.settings.edge_settings(self.edge_type, 'pen_width')
            else:
                return self._pen_width
        else:
            self._pen_width = value

    def is_filled(self, value = None):
        if value is None:
            if self._is_filled is None:
                return self.forest.settings.edge_settings(self.edge_type, 'is_filled')
            else:
                return self._is_filled
        else:
            self._is_filled = value

    #### Shape / pull / visibility ###############################################################

    def shape_name(self, value = None):
        if value is None:
            if self._shape_name is None:
                return self.forest.settings.edge_settings(self.edge_type, 'shape_name')
            else:
                return self._shape_name
        else:
            self._shape_name = value
            self._shape_method = SHAPE_PRESETS[value]['method'] 

    def shape_method(self):
        return SHAPE_PRESETS[self.shape_name()]['method'] 

    def shape_control_point_support(self):
        return SHAPE_PRESETS[self.shape_name()]['control_points'] 


    def pull(self, value = None):
        if value is None:
            if self._pull is None:
                return self.forest.settings.edge_settings(self.edge_type, 'pull')
            else:
                return self._pull
        else:
            self._pull = value

    def shape_visibility(self, value = None):
        if value is None:
            if self._shape_visible == None:
                return self.forest.settings.edge_settings(self.edge_type, 'visible')
            else:
                return self._shape_visible
        else:
            self._shape_visible = value

    #### Derivative features ############################################

    def make_path(self):
        if not self._shape_method:
            self._shape_method = SHAPE_PRESETS[self.shape_name()]['method']
        self._path = self._shape_method(self)


    def is_structural(self):
        return self.edge_type == self.start.default_edge_type

    def adjust_control_point(self, index, points):
        """ Called from UI, when dragging """
        x, y = points
        z = self.adjust[index][2]
        self.adjust[index] = (x, y, z)
        self.make_path()
        self.update()


    def update_end_points(self):
        if self.align == LEFT:
            self.start_point = self.start.left_magnet()
        elif self.align == RIGHT:
            self.start_point = self.start.right_magnet()
        else:
            self.start_point = self.start.bottom_magnet()
        self.end_point = self.end.top_magnet()
        # sx, sy, sz = self.start_point
        # ex, ey, ez = self.end_point
        # self.center_point = sx + ((ex - sx) / 2), sy + ((ey - sy) / 2)


    def connect_end_points(self, start, end):
        self.start_point = start.get_current_position()
        self.end_point = end.get_current_position()
        self.start = start
        self.end = end
        # sx, sy, sz = self.start_point
        # ex, ey, ez = self.end_point
        # self.center_point = sx + ((ex - sx) / 2), sy + ((ey - sy) / 2)

    def __repr__(self):
        if self.start and self.end:
            return '<%s %s-%s %s>' % (self.edge_type, self.start, self.end, self.align)
        else:
            return '<%s stub from %s to %s>' % (self.edge_type, self.start, self.end)

    def __unicode__(self):
        if self.start and self.end:
            return u'<%s %s-%s %s>' % (self.edge_type, self.start, self.end, self.align)
        else:
            return u'<%s stub from %s to %s>' % (self.edge_type, self.start, self.end)


    def drop_to(self, x, y):
        pass

    def set_visible(self, visible):
        """ Hide or show, and also manage related UI objects. Note that the shape itself may be visible or not independent of this. It has to be visible in this level so that UI elements can be used. """
        v = self.isVisible()
        #print 'set visible called with vis %s when isVisible is %s' % (visible, v)
        if v and not visible:
            self._visible = False
            self.hide()
            ctrl.main.ui_manager.hide_control_points(self)  # @UndefinedVariable
            for touch_area in self.touch_areas.values():
                touch_area.hide()
        elif (not v) and visible:
            self._visible = True
            self.show()
            ctrl.main.ui_manager.show_control_points(self)  # @UndefinedVariable
            for touch_area in self.touch_areas.values():
                touch_area.show()

    def set_selection_status(self, selected):
        ui = ctrl.main.ui_manager  # @UndefinedVariable
        if selected:
            ui.add_control_points(self)
        else:
            ui.remove_control_points(self)
        self.update()

    def boundingRect(self):
        if self._shape_name == 'linear':
            return QtCore.QRectF(to_Pf(self.start_point), to_Pf(self.end_point))
        else:  # include curve adjustments
            if not self._path:
                self.update_end_points()
                self.make_path()
            return self._path.controlPointRect()

    def hoverEnterEvent(self, event):
        if not self._hovering:
            self._hovering = True
            self.prepareGeometryChange()
            self.update()
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        if self._hovering:
            self._hovering = False
            self.prepareGeometryChange()
            self.update()


    def click(self, event=None):
        """ Scene has decided that this node has been clicked """
        self._hovering = False
        if event and event.modifiers() == Qt.ShiftModifier:  # multiple selection
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
            return
        if ctrl.is_selected(self):
            pass
            # ctrl.deselect_objects()
        else:
            ctrl.select(self)


    def paint(self, painter, option, widget):
        if not self.start or not self.end:
            return
        c = self.contextual_color()
        if self.has_outline():
            p = self.pen()
            p.setColor(c)
            p.setWidth(self.pen_width())
            painter.setPen(p)
            painter.drawPath(self._path)
        if self.is_filled():
            painter.fillPath(self._path, c)

    def adjusted_control_point_list(self):
        l = []
        for a_point, c_point in zip(self.adjust, self.control_points):
            if not c_point:
                return l
            l.append(a_point[0] + c_point[0])
            l.append(a_point[1] + c_point[1])
        return l

    def get_path(self):
        return self._path

    def get_point_at(self, d):
        if self._filled_shape:
            d /= 2.0
        if not self._path:
            self.update_end_points()
            self.make_path()
        return self._path.pointAtPercent(d)

    def get_angle_at(self, d):
        if self._filled_shape:
            d /= 2.0
            # slopeAtPercent
        if not self._path:
            self.update_end_points()
            self.make_path()
        return self._path.angleAtPercent(d)


    #### Restoring after load / undo #########################################

    def after_restore(self, changes):
        """ Fix derived attributes """
        self.update_end_points()
        self.set_visible(self._visible)


