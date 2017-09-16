from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF as Pf, Qt
from kataja.Shapes import SHAPE_PRESETS, outline_stroker
from kataja.singletons import ctrl
import math
from collections import ChainMap
from kataja.utils import time_me
import kataja.globals as g

CONNECT_TO_CENTER = 0
CONNECT_TO_BOTTOM_CENTER = 1
CONNECT_TO_MAGNETS = 2
CONNECT_TO_BORDER = 3
SPECIAL = 4
CONNECT_TO_SIMILAR = 5

TOP_LEFT_CORNER = 0
TOP_SIDE = 1
TOP_RIGHT_CORNER = 2
LEFT_SIDE = 3
RIGHT_SIDE = 4
BOTTOM_LEFT_CORNER = 5
BOTTOM_SIDE = 6
BOTTOM_RIGHT_CORNER = 7


def opposite(curve_dir):
    if curve_dir == LEFT_SIDE:
        return RIGHT_SIDE
    elif curve_dir == TOP_SIDE:
        return BOTTOM_SIDE
    elif curve_dir == RIGHT_SIDE:
        return LEFT_SIDE
    elif curve_dir == BOTTOM_SIDE:
        return TOP_SIDE


class EdgePath:
    """ EdgePath takes some responsibility of the complicated path drawing operations in Edges
    """

    def __init__(self, edge):
        self.edge = edge
        self.my_shape = None
        self.computed_start_point = (0, 0)
        self.computed_end_point = (0, 0)
        self.curve_dir_start = 0
        self.curve_dir_end = 0
        self.abstract_start_point = (0, 0)
        self.abstract_end_point = (0, 0)
        self.control_points = []  # control_points are tuples of coordinates, computed by
        # shape algorithms
        self.adjusted_control_points = []  # combines those two above
        self.draw_path = None
        self.true_path = None  # inner arc or line without the leaf effect
        self.fat_path = None
        self.make_fat_path = False
        self.use_simple_path = False
        self.arrowhead_size_at_start = 6
        self.arrowhead_size_at_end = 6
        self.arrowhead_start_path = None
        self.arrowhead_end_path = None
        self.cached_cp_rect = None
        self.changed = False
        self.cached_start_index = self.edge.edge_start_index()
        self.cached_end_index = self.edge.edge_end_index()

    def shape(self) -> QtGui.QPainterPath:
        """ Use the fatter version for hit detection
        :return: QGraphicsPath
        """
        if not self.fat_path:
            self.make()
        return self.fat_path

    def boundingRect(self):
        """ BoundingRect that includes the control points of the arc
        :return: QRect
        """
        if not self.draw_path:
            self.make()
        return self.cached_cp_rect

    def _connect_start_to_center(self, sx, sy, ex, ey):
        self.computed_start_point = sx, sy
        if abs(sx - ex) < abs(sy - ey):
            if sy < ey:
                self.curve_dir_start = BOTTOM_SIDE
            else:
                self.curve_dir_start = TOP_SIDE
        else:
            if sx < ex:
                self.curve_dir_start = RIGHT_SIDE
            else:
                self.curve_dir_start = LEFT_SIDE
        self.abstract_start_point = self.computed_start_point

    def _connect_end_to_center(self, sx, sy, ex, ey):
        self.computed_end_point = ex, ey
        if abs(sx - ex) < abs(sy - ey):
            if sy > ey:
                self.curve_dir_end = BOTTOM_SIDE
            else:
                self.curve_dir_end = TOP_SIDE
        else:
            if sx > ex:
                self.curve_dir_end = RIGHT_SIDE
            else:
                self.curve_dir_end = LEFT_SIDE
        self.abstract_end_point = self.computed_end_point

    def _connect_start_to_bottom_center(self, sx, sy, start):
        self.computed_start_point = start.bottom_center_magnet(scene_pos=(sx, sy))
        self.curve_dir_start = BOTTOM_SIDE
        self.abstract_start_point = self.computed_start_point

    def _connect_end_to_bottom_center(self, ex, ey, end):
        self.computed_end_point = end.top_center_magnet(scene_pos=(ex, ey))
        self.curve_dir_end = TOP_SIDE
        self.abstract_end_point = self.computed_end_point

    def _connect_start_to_magnets(self, sx, sy, start):
        e_n, e_count = self.edge.edge_start_index()
        if not start.has_ordered_children():
            e_n = e_count - e_n - 1
        self.computed_start_point = start.bottom_magnet(e_n, e_count, scene_pos=(sx, sy))
        self.curve_dir_start = BOTTOM_SIDE
        self.abstract_start_point = self.computed_start_point

    def _connect_start_to_border(self, sx, sy, ex, ey, start):
        # Find the point in bounding rect that is on the line from center of start node to
        # center of end node / end_point. It is simple, but the point can be in any of four
        # sides of the rect.
        i, i_of = self.cached_start_index
        i_shift = (i - math.ceil(i_of / 2)) * 2
        dx = ex - sx
        dy = ey - sy
        sbr = start.boundingRect()
        self.abstract_start_point = sx, sy
        s_left, s_top, s_right, s_bottom = (int(x * .8) for x in sbr.getCoords())
        if dx > 0:
            x = s_right
            x_side = RIGHT_SIDE
        else:
            x = s_left
            x_side = LEFT_SIDE
        if dy > 0:
            y = s_bottom
            y_side = BOTTOM_SIDE
        else:
            y = s_top
            y_side = TOP_SIDE

        # orthogonal cases, handle separately to avoid division by zero
        if dx == 0:
            self.computed_start_point = sx + i_shift, sy + y
            self.curve_dir_start = y_side
        elif dy == 0:
            self.computed_start_point = sx + x, sy + i_shift
            self.curve_dir_start = x_side
        else:
            # cases where edge starts somewhere between
            ratio = dy / dx
            y_reach = int(x * ratio)
            if (y_reach < s_bottom and dy > 0) or (y_reach > s_top and dy < 0):
                self.computed_start_point = sx + x, sy + y_reach + i_shift
                self.curve_dir_start = x_side
            else:
                self.computed_start_point = sx + int(y / ratio) + i_shift, sy + y
                self.curve_dir_start = y_side

    def _connect_end_to_border(self, sx, sy, ex, ey, end):
        # Find the point in bounding rect that is on the line from center of end node to
        # center of start node / start_point. It is simple, but the point can be in any of
        # four sides of the rect.
        i, i_of = self.cached_end_index
        i_shift = (i - math.ceil(i_of / 2)) * 2
        dx = ex - sx
        dy = ey - sy
        ebr = end.boundingRect()
        self.abstract_end_point = ex, ey
        e_left, e_top, e_right, e_bottom = (int(x * .8) for x in ebr.getCoords())

        if dx > 0:
            x = e_left
            x_side = LEFT_SIDE
        else:
            x = e_right
            x_side = RIGHT_SIDE
        if dy > 0:
            y = e_top
            y_side = TOP_SIDE
        else:
            y = e_bottom
            y_side = BOTTOM_SIDE

        # orthogonal cases, handle separately to avoid division by zero
        if dx == 0:
            self.computed_end_point = ex + i_shift, ey + y
            self.curve_dir_end = y_side
        elif dy == 0:
            self.computed_end_point = ex + x, ey + i_shift
            self.curve_dir_end = x_side
        else:
            # cases where edge ends somewhere between
            ratio = dy / dx
            y_reach = int(x * ratio)
            if (dy > 0 and y_reach > e_top) or (dy < 0 and y_reach < e_bottom):
                self.computed_end_point = ex + x, ey + y_reach + i_shift
                self.curve_dir_end = x_side
            else:
                self.computed_end_point = ex + int(y / ratio) + i_shift, ey + y
                self.curve_dir_end = y_side

    def _connect_start_to_similar(self, sx, sy, start):
        i, i_of = self.cached_start_index
        i_shift = (i - math.ceil(i_of / 2)) * 2

        found = False
        for edge in start.edges_up:
            if edge.extra == self.edge.extra:
                oi, oi_of = edge.path.cached_end_index
                others_i_shift = (oi - math.ceil(oi_of / 2)) * 2
                self.computed_start_point = sx + others_i_shift, sy
                self.curve_dir_start = opposite(edge.path.curve_dir_end)
                found = True
                break
        if not found:
            if self.edge.extra and self.edge.extra.syntactic_object:
                ee = self.edge.extra.syntactic_object
                for edge in start.edges_down:
                    if edge == self.edge or edge.end is self.edge.end:
                        self.computed_start_point = sx + i_shift, sy
                        self.curve_dir_start = BOTTOM_SIDE
                        found = True
                        break
                    elif edge.extra and edge.extra.syntactic_object.name == ee.name:
                        self.computed_start_point = edge.path.computed_start_point
                        self.curve_dir_start = BOTTOM_SIDE
                        # self.curve_dir_start = opposite(edge.path.curve_dir_start)
                        found = True
                        break
        if not found:
            self.computed_start_point = sx + i_shift, sy
            self.curve_dir_start = BOTTOM_SIDE
        self.abstract_start_point = sx, sy

    def _connect_end_to_similar(self, ex, ey):
        i, i_of = self.cached_end_index
        i_shift = (i - math.ceil(i_of / 2)) * 2
        self.computed_end_point = ex + i_shift, ey
        self.curve_dir_end = TOP_SIDE
        self.abstract_end_point = ex, ey

    def update_end_points(self):
        """

        :return:
        """

        osx, osy = self.computed_start_point
        oex, oey = self.computed_end_point
        start = self.edge.start
        end = self.edge.end
        self.cached_start_index = self.edge.edge_start_index()
        self.cached_end_index = self.edge.edge_end_index()

        if start and end:
            sx, sy = start.current_scene_position
            ex, ey = end.current_scene_position
        elif start:
            ex, ey = self.edge.end_point
            sx, sy = start.current_scene_position
            self.computed_end_point = ex, ey
        elif end:
            sx, sy = self.edge.start_point
            ex, ey = end.current_scene_position
            self.computed_start_point = sx, sy
        else:
            return
        if start:
            connection_style = self.edge.flattened_settings['start_connects_to']
            if connection_style == CONNECT_TO_BORDER and start.is_empty():
                connection_style = CONNECT_TO_SIMILAR

            if connection_style == SPECIAL:
                csp = start.special_connection_point(sx, sy, ex, ey, start=True,
                                                     edge_type=self.edge.edge_type)
                self.computed_start_point, self.curve_dir_start = csp
                self.abstract_start_point = self.computed_start_point
            elif connection_style == CONNECT_TO_CENTER:
                self._connect_start_to_center(sx, sy, ex, ey)
            elif connection_style == CONNECT_TO_BOTTOM_CENTER:
                self._connect_start_to_bottom_center(sx, sy, start)
            elif connection_style == CONNECT_TO_MAGNETS:
                self._connect_start_to_magnets(sx, sy, start)
            elif connection_style == CONNECT_TO_BORDER:
                self._connect_start_to_border(sx, sy, ex, ey, start)
            elif connection_style == CONNECT_TO_SIMILAR:
                self._connect_start_to_similar(sx, sy, start)
        if end:
            connection_style = self.edge.flattened_settings['end_connects_to']
            if connection_style == CONNECT_TO_BORDER and end.is_empty():
                connection_style = CONNECT_TO_SIMILAR
            if connection_style == SPECIAL:
                cep = end.special_connection_point(sx, sy, ex, ey, start=False,
                                                  edge_type=self.edge.edge_type)
                self.computed_end_point, self.curve_dir_end = cep
                self.abstract_end_point = self.computed_end_point
            elif connection_style == CONNECT_TO_CENTER:
                self._connect_end_to_center(sx, sy, ex, ey)
            elif connection_style == CONNECT_TO_BOTTOM_CENTER or connection_style == \
                    CONNECT_TO_MAGNETS:
                self._connect_end_to_bottom_center(ex, ey, end)
            elif connection_style == CONNECT_TO_BORDER:
                self._connect_end_to_border(sx, sy, ex, ey, end)
            elif connection_style == CONNECT_TO_SIMILAR:
                self._connect_end_to_similar(ex, ey)

        nsx, nsy = self.computed_start_point
        nex, ney = self.computed_end_point
        if osx != nsx or osy != nsy or oex != nex or oey != ney:
            self.changed = True

    def make(self):
        """ Draws the shape as a path """
        self.update_end_points()
        if (self.my_shape is not None) and not self.changed:
            return
        self.changed = False
        self.edge.prepareGeometryChange()
        sp = self.edge.start_point
        ep = self.edge.end_point
        sx, sy = sp
        ex, ey = ep
        if sx == ex:
            ex += 0.001  # fix disappearing vertical paths

        thick = 1
        if not self.my_shape:
            self.my_shape = SHAPE_PRESETS[self.edge.shape_name]()
            self.edge.flatten_settings()
        elif self.edge.shape_name != self.my_shape.shape_name:
            self.my_shape = SHAPE_PRESETS[self.edge.shape_name]()
            self.edge.flatten_settings()
        (self.draw_path, self.true_path, self.control_points,
         self.adjusted_control_points) = self.my_shape.path(sp, (ex, ey),
                                                            self.edge.curve_adjustment,
                                                            self.curve_dir_start,
                                                            self.curve_dir_end, thick=thick,
                                                            start=self.edge.start,
                                                            end=self.edge.end,
                                                            inner_only=self.use_simple_path,
                                                            d=self.edge.flattened_settings)
        uses_pen = self.edge.has_outline()

        if self.use_simple_path:
            self.draw_path = self.true_path
        self.make_arrowhead_at_start(uses_pen)
        self.make_arrowhead_at_end(uses_pen)

        if self.make_fat_path and not self.use_simple_path:
            # Fat path is the shape of the path with some extra margin to
            # make it easier to click/touch
            self.fat_path = outline_stroker.createStroke(self.draw_path)
        else:
            self.fat_path = self.draw_path
        self.cached_cp_rect = self.draw_path.controlPointRect().adjusted(-2, -2, 2, 2)

    def get_point_at(self, d: float) -> 'QPointF':
        """ Get coordinates at the percentage of the length of the path.
        :param d: float
        :return: QPoint
        """
        if not self.true_path:
            self.make()
        return self.true_path.pointAtPercent(d)

    def get_angle_at(self, d: float) -> float:
        """ Get angle at the percentage of the length of the path.
        :param d: int
        :return: float
        """
        if not self.true_path:
            self.make()
        return self.true_path.angleAtPercent(d)

    def get_closest_path_point(self, pos):
        """ When dragging object along path, gives the coordinates to closest
        point in path corresponding to
        given position. There is no exact way of doing this, what we do is to
        take 100 points along the line and
        find the closest point from there.
        :param pos: position looking for closest path position
        :return: (float:pointAtPercent, QPos:path position)
        """
        if not self.true_path:
            self.make()
        min_d = 1000
        min_i = -1
        min_pos = None
        for i in range(0, 100, 2):
            p2 = self.true_path.pointAtPercent(i / 100.0)
            d = (pos - p2).manhattanLength()
            if d < min_d:
                min_d = d
                min_i = i
                min_pos = p2
        return min_i / 100.0, min_pos

    def make_arrowhead_at_start(self, uses_pen):
        """ Assumes that the path exists already, creates arrowhead path to its beginning.
        """
        arrowheads = self.edge.flattened_settings['arrowheads']
        if not (arrowheads == g.AT_START or arrowheads == g.AT_BOTH):
            self.arrowhead_start_path = None
            return
        ad = 0.5
        t = self.edge.flattened_settings['thickness']
        size = self.arrowhead_size_at_start
        if t:
            size *= t
        x, y = self.edge.start_point
        # average between last control point and general direction seems to be ok.
        if self.control_points:
            p0 = self.adjusted_control_points[0]
        else:
            p0 = self.edge.end_point
        p0x, p0y = p0
        sx, sy = self.edge.start_point
        dx, dy = sx - p0x, sy - p0y
        a = math.atan2(dy, dx)
        p = QtGui.QPainterPath()
        p.moveTo(x, y)
        x1, y1 = x - (math.cos(a + ad) * size), y - (math.sin(a + ad) * size)
        xm, ym = x - (math.cos(a) * size * 0.5), y - (math.sin(a) * size * 0.5)
        x2, y2 = x - (math.cos(a - ad) * size), y - (math.sin(a - ad) * size)
        p.lineTo(x1, y1)
        p.lineTo(xm, ym)
        p.lineTo(x2, y2)
        p.lineTo(x, y)
        self.arrowhead_start_path = p
        # sharpen line path by snipping its tip
        if uses_pen:
            self.draw_path.setElementPositionAt(0, xm, ym)

    def make_arrowhead_at_end(self, uses_pen):
        """ Assumes that the path exists already, creates arrowhead path to its end.
        """
        arrowheads = self.edge.flattened_settings['arrowheads']
        if not (arrowheads == g.AT_END or arrowheads == g.AT_BOTH):
            self.arrowhead_end_path = None
            return
        ad = 0.5
        t = self.edge.flattened_settings['thickness']
        size = self.arrowhead_size_at_end
        if t:
            size *= t
        x, y = self.edge.end_point
        # average between last control point and general direction seems to be ok.
        if self.control_points:
            last_x, last_y = self.adjusted_control_points[-1]
        else:
            last_x, last_y = self.edge.start_point

        dx, dy = x - last_x, y - last_y
        a = math.atan2(dy, dx)
        p = QtGui.QPainterPath()
        p.moveTo(x, y)
        x1, y1 = x - (math.cos(a + ad) * size), y - (math.sin(a + ad) * size)
        xm, ym = x - (math.cos(a) * size * 0.5), y - (math.sin(a) * size * 0.5)
        x2, y2 = x - (math.cos(a - ad) * size), y - (math.sin(a - ad) * size)
        p.lineTo(x1, y1)
        p.lineTo(xm, ym)
        p.lineTo(x2, y2)
        p.lineTo(x, y)
        self.arrowhead_end_path = p
        # sharpen line path by snipping its tip
        if uses_pen:
            self.draw_path.setElementPositionAt(self.draw_path.elementCount() - 1, xm, ym)

    def draw_control_point_hints(self, painter, pen, adjust):
        adjust = adjust or []
        painter.setPen(pen)
        painter.drawPath(self.true_path)
        if self.control_points:
            pen.setWidthF(0.5)
            painter.setPen(pen)
            sx, sy = self.edge.start_point
            for i, (cpx, cpy) in enumerate(self.control_points):
                painter.drawLine(sx, sy, cpx, cpy)
                if len(adjust) > i:
                    pen.setStyle(QtCore.Qt.DashLine)
                    ax, ay = adjust[i]
                    painter.drawLine(cpx, cpy, ax, ay)
                    pen.setStyle(QtCore.Qt.SolidLine)
                sx, sy = self.edge.end_point
