import math

from PyQt6 import QtCore, QtGui

import kataja.globals as g
from kataja.Shapes import SHAPE_PRESETS, outline_stroker
from kataja.globals import EDGE_PLUGGED_IN, EDGE_OPEN, EDGE_CAN_INSERT, EDGE_RECEIVING_NOW, \
    EDGE_OPEN_DOMINANT, EDGE_RECEIVING_NOW_DOMINANT
from kataja.utils import equal_synobj

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
        self.cached_shift_for_start = None

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

    def get_shift_for_start(self):
        if self.cached_shift_for_start is not None:
            return self.cached_shift_for_start
        self.cached_shift_for_start = 0
        cn = self.edge.start
        if cn and cn.node_type == g.CONSTITUENT_NODE:
            i = 0
            count = 0
            prev_edge = None
            for edge in cn.cached_sorted_feature_edges:
                if prev_edge and not equal_synobj(edge.origin, prev_edge.origin):
                    count += 1
                if edge == self.edge:
                    i = count
                prev_edge = edge
            self.cached_shift_for_start = (i - math.ceil(count / 2)) * 4
        return self.cached_shift_for_start

    def get_shift_for_end(self):

        if self.edge.end_links_to:
            return self.edge.end_links_to.path.get_shift_for_start()
        else:
            return 0

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
        i_shift = self.get_shift_for_start()
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
        i_shift = self.get_shift_for_end()
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

    def _connect_start_to_similar(self, sx, sy):
        i_shift = self.get_shift_for_start()
        upper = self.edge.start_links_to
        d = 0
        if upper and self.edge.start.can_cascade_edges():
            dx = upper.start_point[0] - upper.end_point[0]
            dy = upper.start_point[1] - upper.end_point[1]
            if dy != 0:
                d = dx / abs(dy)
                d = max(-1.4, min(1.4, d))
            elif dx > 0:
                d = 1.4
            elif dx < 0:
                d = -1.4
        self.computed_start_point = sx + i_shift, sy + (i_shift * d)
        self.curve_dir_start = BOTTOM_SIDE
        self.abstract_start_point = sx, sy

    def _connect_end_to_similar(self, ex, ey):
        i_shift = self.get_shift_for_end()
        lower = self.edge.end_links_to
        d = 0
        if lower and self.edge.end.can_cascade_edges():
            cepx, cepy = self.computed_end_point
            cspx, cspy = self.computed_start_point
            dx = cspx - cepx
            dy = cspy - cepy
            if dy != 0:
                d = dx / abs(dy)
                d = max(-1.4, min(1.4, d))
            elif dx > 0:
                d = 1.4
            elif dx < 0:
                d = -1.4
        self.computed_end_point = ex + i_shift, ey + (i_shift * d)
        self.curve_dir_end = TOP_SIDE
        self.abstract_end_point = ex, ey

    def update_end_points(self):
        osx, osy = self.computed_start_point
        oex, oey = self.computed_end_point
        start = self.edge.start
        end = self.edge.end

        sx, sy = start.current_scene_position if start else self.edge.start_point
        ex, ey = end.current_scene_position if end else self.edge.end_point
        if start:
            connection_style = self.edge.settings.get('start_connects_to')
            if connection_style == CONNECT_TO_BORDER:
                connection_style = CONNECT_TO_SIMILAR

            # if connection_style == CONNECT_TO_BORDER and start.is_empty():
            #    connection_style = CONNECT_TO_SIMILAR
            if connection_style == SPECIAL:
                csp = start.get_special_connection_point(sx, sy, ex, ey, start=True,
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
                self._connect_start_to_similar(sx, sy)
        if end:
            connection_style = self.edge.settings.get('end_connects_to')
            if connection_style == CONNECT_TO_BORDER:
                connection_style = CONNECT_TO_SIMILAR

            if connection_style == SPECIAL:
                cep = end.get_special_connection_point(sx, sy, ex, ey, start=False,
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
        elif self.edge.shape_name != self.my_shape.shape_name:
            self.my_shape = SHAPE_PRESETS[self.edge.shape_name]()
        path = self.my_shape.path(sp, (ex, ey),
                                  self.edge.curve_adjustment,
                                  self.curve_dir_start,
                                  self.curve_dir_end, thick=thick,
                                  start=self.edge.start,
                                  end=self.edge.end,
                                  inner_only=self.use_simple_path,
                                  d=self.edge.settings.flat_dict)
        self.draw_path, self.true_path, self.control_points, self.adjusted_control_points = path
        uses_pen = self.edge.has_outline()

        if self.use_simple_path:
            self.draw_path = self.true_path
        self.make_feature_edge_endings(uses_pen)
        self.make_arrowhead_at_start(uses_pen)
        self.make_arrowhead_at_end(uses_pen)

        if self.make_fat_path and not self.use_simple_path:
            # Fat path is the shape of the path with some extra margin to
            # make it easier to click/touch
            self.fat_path = outline_stroker.createStroke(self.draw_path)
        else:
            self.fat_path = self.draw_path
        self.cached_cp_rect = self.draw_path.controlPointRect().adjusted(-2, -2, 2, 2)

    def get_point_at(self, d: float) -> 'QtCore.QPointF':
        """ Get coordinates at the percentage of the length of the path. """
        if not self.true_path:
            self.make()
        return self.true_path.pointAtPercent(d)

    def get_angle_at(self, d: float) -> float:
        """ Get angle at the percentage of the length of the path."""
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

    def make_feature_edge_endings(self, uses_pen):
        if not self.edge.start_symbol:
            return
        symbol = self.edge.start_symbol
        x, y = self.computed_start_point
        path = self.draw_path  # QtGui.QPainterPath(QtCore.QPointF(x, y))
        path.moveTo(x, y)

        if symbol == 1:
            poly = QtGui.QPolygonF(
                [QtCore.QPointF(x, y - 1), QtCore.QPointF(x + 1, y), QtCore.QPointF(x, y + 1),
                 QtCore.QPointF(x - 1, y), QtCore.QPointF(x, y - 1)])
            path.addPolygon(poly)
        elif symbol == EDGE_OPEN:
            path.addEllipse(x - 2, y - 4, 4, 4)
        elif symbol == EDGE_OPEN_DOMINANT:
            path.addEllipse(x - 2, y - 4, 4, 4)
            path.addEllipse(x - 1, y - 6, 2, 2)
        elif symbol == EDGE_RECEIVING_NOW:
            path.addEllipse(x - 2, y - 4, 4, 4)
        elif symbol == EDGE_RECEIVING_NOW_DOMINANT:
            path.addEllipse(x - 2, y - 4, 4, 4)
            path.addEllipse(x - 1, y - 6, 2, 2)
        elif symbol == EDGE_PLUGGED_IN:
            checks_node = self.edge.origin.checks
            for edge in self.edge.start.edges_down:
                if equal_synobj(edge.origin, checks_node) and edge.is_visible():
                    edge.path.update_end_points()
                    cx, cy = edge.path.computed_start_point
                    cy -= 2
                    xdist = abs(x - cx)
                    if uses_pen:
                        path.cubicTo(x, y - xdist, cx, cy - xdist, cx, cy)
                    else:
                        path.cubicTo(x, y - xdist, cx, cy - xdist, cx, cy)
                        path.cubicTo(cx, cy - xdist - 3, x, y - xdist - 3, x, y)
                    break
        elif symbol == EDGE_CAN_INSERT:
            path.lineTo(x, y - 4)
        # self.draw_path += path

    def make_arrowhead_at_start(self, uses_pen):
        """ Assumes that the path exists already, creates arrowhead path to its beginning.
        """
        arrowheads = self.edge.settings.get('arrowheads')
        if not (arrowheads == g.AT_START or arrowheads == g.AT_BOTH):
            self.arrowhead_start_path = None
            return
        ad = 0.5
        t = self.edge.settings.get('thickness')
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
        arrowheads = self.edge.settings.get('arrowheads')
        if not (arrowheads == g.AT_END or arrowheads == g.AT_BOTH):
            self.arrowhead_end_path = None
            return
        ad = 0.5
        t = self.edge.settings.get('thickness')
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
                    pen.setStyle(QtCore.Qt.PenStyle.DashLine)
                    ax, ay = adjust[i]
                    painter.drawLine(cpx, cpy, ax, ay)
                    pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
                sx, sy = self.edge.end_point
