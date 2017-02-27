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

import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF as Pf, Qt

import kataja.globals as g
from kataja.EdgeLabel import EdgeLabel
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.Shapes import SHAPE_PRESETS, outline_stroker
from kataja.singletons import ctrl, prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, add_xy, sub_xy, time_me

CONNECT_TO_CENTER = 0
CONNECT_TO_BOTTOM_CENTER = 1
CONNECT_TO_MAGNETS = 2
CONNECT_TO_BORDER = 3
SPECIAL = 4

TOP_LEFT_CORNER = 0
TOP_SIDE = 1
TOP_RIGHT_CORNER = 2
LEFT_SIDE = 3
RIGHT_SIDE = 4
BOTTOM_LEFT_CORNER = 5
BOTTOM_SIDE = 6
BOTTOM_RIGHT_CORNER = 7

angle_magnet_map = {
    0: 6, 1: 6, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0, 7: 5, 8: 5, 9: 5, 10: 7, 11: 8, 12: 9, 13: 10, 14: 11,
    15: 6, 16: 6
    }

atan_magnet_map = {
    -8: 5, -7: 5, -6: 0, -5: 1, -4: 2, -3: 3, -2: 4, -1: 6, 0: 6, 1: 6, 2: 11, 3: 10, 4: 9, 5: 8,
    6: 7, 7: 5, 8: 5
    }

qbytes_opacity = QtCore.QByteArray()
qbytes_opacity.append("opacity")


class Edge(QtWidgets.QGraphicsObject, SavedObject):
    """ Any connection between nodes: can be represented as curves, branches
    or arrows """

    __qt_type_id__ = next_available_type_id()

    def __init__(self, start=None, end=None, edge_type=''):
        """
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param string order:
        """
        SavedObject.__init__(self)
        QtWidgets.QGraphicsItem.__init__(self)
        self.label_item = None
        self.edge_type = edge_type
        self.start = start
        self.end = end
        self.fixed_start_point = (0, 0)
        self.fixed_end_point = (0, 0)
        self.curve_adjustment = None  # user's adjustments. contains (dist, angle) tuples.
        self.control_points = []  # control_points are tuples of coordinates, computed by
        # shape algorithms
        self.adjusted_control_points = []  # combines those two above
        self.label_data = {}
        self._nodes_overlap = False
        self._changed = False

        self.in_projections = []

        self._computed_start_point = (0, 0)
        self._computed_end_point = (0, 0)

        self._local_drag_handle_position = None

        # ## Adjustable values, defaults to ForestSettings if None for this
        # element
        # based on the relation style

        # self.center_point = (0, 0, 0)

        # ## Derivative elements
        self._path = None
        self._true_path = None  # inner arc or line without the leaf effect
        self._fat_path = None
        self._use_simple_path = False
        self._hovering = False
        self._start_node_moving = False
        self._end_node_moving = False
        self._make_fat_path = False
        self._curve_dir_start = BOTTOM_SIDE
        self._curve_dir_end = TOP_SIDE
        self.setZValue(10)
        self.status_tip = ""
        self.arrowhead_size_at_start = 6
        self.arrowhead_size_at_end = 6
        self.crossed_out_flag = False
        self._arrow_cut_point_start = None
        self._arrow_cut_point_end = None
        self._arrowhead_start_path = None
        self._arrowhead_end_path = None
        self._cached_cp_rect = None
        self._use_labels = None
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._visible_by_logic = True
        self._fade_in_anim = None
        self._fade_out_anim = None
        self.is_fading_in = False
        self.is_fading_out = False

    def type(self) -> int:
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then
            iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can
            properly refer to each other and know their
                values.
        :return: None
        """
        self.connect_end_points(self.start, self.end)
        self.setZValue(self.cached('z_value'))
        #self.update_end_points()
        self.update_visibility()
        self.announce_creation()

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """

        print('edge after_model_update (1=CREATED, -1=DELETED), ', transition_type)
        if transition_type == g.CREATED:
            print('re-creating edge')
            ctrl.forest.store(self)
            ctrl.forest.add_to_scene(self)
            print(self.start, self.end)
        elif transition_type == g.DELETED:
            ctrl.free_drawing.delete_edge(self, fade=False)
            return
        self.connect_end_points(self.start, self.end)
        self.update_visibility()
        #self.update_end_points()

    def cut(self, others=None):
        """ If edge ends are not included, set them to None, otherwise cut the edge as it is.
        :param others:
        :return:
        """
        start = None
        end = None
        if self.start and self.start in others:
            start = self.start
        if self.end and self.end in others:
            end = self.end
        self.connect_end_points(start, end)
        ctrl.forest.remove_from_scene(self)
        return self

    @property
    def color_id(self) -> str:
        return self.cached('color_id')

    @color_id.setter
    def color_id(self, value):
        self._changed = True
        ctrl.settings.set_edge_setting('color_id', value, edge=self)

    @property
    def shape_name(self) -> str:
        return self.cached('shape_name')

    @shape_name.setter
    def shape_name(self, value):
        self._changed = True
        ctrl.settings.set_edge_setting('shape_name', value, edge=self)

    @property
    def pull(self) -> float:
        return self.cached('pull')

    @pull.setter
    def pull(self, value):
        ctrl.settings.set_edge_setting('pull', value, edge=self)

    @property
    def start_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of
        starting point of the edge
        :return: tuple (x, y, z)
        """
        if self.start:
            return self._computed_start_point
        else:
            return self.fixed_start_point

    @property
    def end_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of ending
        point of the edge
        :return: tuple (x, y, z)
        """
        if self.end:
            return self._computed_end_point
        else:
            return self.fixed_end_point

    def show(self):
        if not self.isVisible():
            super().show()
        else:
            print('unnecessary show in edge')


    def update_visibility(self, fade_in=True, fade_out=True) -> bool:
        """ Hide or show according to various factors, which allow edge
        to exist but not be drawn.
        This is called logical visibility and can be checked with is_visible().
        Qt's isVisible() checks for scene visibility. Items that are e.g. fading away
        have False for logical visibility but True for scene visibility and items that are part
        of graph in a forest that is not currently drawn may have True for logical visibility but
        false for scene visibility.
        :return:
        """
        lv = True
        if self._nodes_overlap:
            lv = False
        elif self.start and not self.start.is_visible():
            lv = False
        else:
            start = self.start
            end = self.end
            if self.edge_type == g.CONSTITUENT_EDGE:
                if end and not end.is_visible():
                    lv = False
                elif start and ctrl.forest.visualization and not \
                        ctrl.forest.visualization.show_edges_for(start):
                    lv = False
                elif not (start and end):
                    ctrl.free_drawing.delete_edge(self)
                    return False
                elif end.locked_to_node:
                    lv = False
            elif self.edge_type == g.FEATURE_EDGE or self.edge_type == g.CHECKING_EDGE:
                if end and end.locked_to_node is start:
                    lv = False
                elif not (start and end):
                    ctrl.free_drawing.delete_edge(self)
                    return False

        self._visible_by_logic = lv
        # Change visibility if necessary, with fade or instantly.
        # If forest is not drawn, only the logical visibility matters -- do nothing
        if self.scene():
            if lv:
                if self.is_fading_out:
                    if fade_in:
                        self.fade_in()
                        return True
                    else:
                        self.is_fading_out = False
                        self._fade_out_anim.stop()
                        self.show()
                        return True
                if not self.isVisible():
                    if fade_in:
                        self.fade_in()
                        return True
                    else:
                        self.show()
                        return True
            else:
                if self.isVisible():
                    if fade_out:
                        self.fade_out()
                        return True
                    else:
                        self.hide()
                        return True
        return False

    # Edge type - based settings that can be overridden

    @property
    def color(self) -> QtGui.QColor:
        """ Color for drawing the edge -- both the fill and pen color.
        Returns QColor, but what is stored is Kataja
        internal color_id.
        :return: QColor
        """
        return ctrl.cm.get(self.color_id)

    def if_changed_color_id(self, value):
        """ Set edge color, uses palette id strings as values.
        :param value: string
        """
        if self.label_item:
            self.label_item.setDefaultTextColor(ctrl.cm.get(value))

    # ## Label data and its shortcut properties

    def get_label_text(self) -> str:
        """ Label text is actually stored in model.label_data, but this is a
        shortcut for it.
        :return:
        """
        return self.label_data.get('text', '')

    def set_label_text(self, value):
        if self.label_item:
            old = self.get_label_text()
            if old != value:
                self.poke('label_data')
                self.label_data['text'] = value
                self.label_item.update_text(value)
        else:
            self.label_item = EdgeLabel(value, parent=self)
            self.poke('label_data')
            self.label_data['text'] = value

    # ## Signal handling ####

    def receive_signal(self, signal, *args):
        """

        :param signal:
        :param args:
        """
        if signal is g.EDGE_SHAPES_CHANGED:
            if (args and args[0] == self.edge_type) or not args:
                self.update_shape()

    # Helper methods for derived properties

    def is_filled(self) -> bool:
        return self.cached('fill') and self.cached('fillable')

    def has_outline(self) -> int:
        return self.cached('outline')

    def is_visible(self) -> bool:
        return self._visible_by_logic

    def connect_start_to(self, node):
        """

        :param node:
        """
        ctrl.free_drawing.set_edge_start(self, node)
        self.update_shape()

    def connect_end_to(self, node):
        """

        :param node:
        """
        ctrl.free_drawing.set_edge_end(self, node)
        self.update_shape()

    def set_start_point(self, p, y=None):
        """ Convenience method for setting start point: accepts QPoint(F)s,
        tuples and x,y coords.
        :param p: first argument, either QPoint, tuple or x coordinate if y
        is also given
        :param y: y coordinate if p was used to give x coordinate
        :return:
        """

        if y is not None:
            self.fixed_start_point = p, y
        elif isinstance(p, tuple):
            self.fixed_start_point = p
        if isinstance(p, (QtCore.QPoint, QtCore.QPointF)):
            self.fixed_start_point = p.x(), p.y()

    def set_end_point(self, p, y=None):
        """ Convenience method for setting end point: accepts QPoint(F)s,
        tuples and x,y coords.
        :param p: first argument, either QPoint, tuple or x coordinate if y
        is also given
        :param y: y coordinate if p was used to give x coordinate
        :return:
        """
        if y is not None:
            self.fixed_end_point = p, y
        elif isinstance(p, tuple):
            self.fixed_end_point = p
        if isinstance(p, (QtCore.QPoint, QtCore.QPointF)):
            self.fixed_end_point = p.x(), p.y()

    def is_broken(self) -> bool:
        """ If this edge should be a connection between two nodes and either
        node is missing, the edge
        is broken and should be displayed differently.
        :return: bool
        """
        if self.edge_type == g.ARROW:
            return False
        return not (self.start and self.end)

    def edge_index(self) -> tuple:
        """ Return tuple where first value is the order of this edge among similar type of edges
        for this parent (parent = edge.start) and the second is the total amount of siblings (
        edges of this type)
        :return:
        """
        if not self.start:
            return 0, 0
        count = 0
        found = 0
        for ed in self.start.edges_down:
            if ed.edge_type == self.edge_type:
                if ed is self:
                    found = count
                count += 1
        return found, count

    def direction(self) -> int:
        """ Coarse direction of this edge, either g.LEFT or g.RIGHT. Useful for knowing if
         to prepend or append the sibling node compared to this.
        :return:
        """
        en, ecount = self.edge_index()
        if en < ecount / 2:
            return g.LEFT
        else:
            return g.RIGHT

    # ### Color ############################################################

    @property
    def contextual_color(self) -> QtGui.QColor:
        """ Drawing color that is sensitive to edge's state
        :return: QColor
        """
        if ctrl.pressed == self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
        elif self.is_broken():
            return ctrl.cm.broken(self.color)
        elif self.in_projections:
            return ctrl.cm.get(self.in_projections[0].color_id)
        else:
            return self.color

    def uses_labels(self) -> bool:
        """ Some edge types, e.g. arrows inherently suggest adding labels to
        them. For others, having ui_support
         textbox for adding label would be unwanted noise.
        :return: bool
        """
        return self.cached('labeled')

    # ### Shape / pull / visibility
    # ###############################################################

    def drag(self, event):
        """ This is for dragging the whole edge in cases when edge is not
        connected to nodes at any point
        e.g. it is freely floating arrow or divider
        :param event: Drag event?
        """
        # self.draggable = not (self.start or self.end)

        scene_pos = to_tuple(event.scenePos())
        dist = sub_xy(self.end_point, self.start_point)
        if not self._local_drag_handle_position:
            drag = to_tuple(event.buttonDownScenePos(QtCore.Qt.LeftButton))
            self._local_drag_handle_position = sub_xy(drag, self.start_point)
        start = sub_xy(scene_pos, self._local_drag_handle_position)
        if not self.start:
            self.set_start_point(*start)
        if not self.end:
            self.set_end_point(add_xy(start, dist))

    def compute_pos_from_adjust(self, point_index) -> tuple:
        """ Works with 1 or 2 control points.
        :param point_index:
        :return:
        """
        cx, cy = self.control_points[point_index]
        rdist, rrad = self.curve_adjustment[point_index]
        if point_index == 0:
            sx, sy = self.start_point
        else:
            sx, sy = self.end_point
        sx_to_cx = cx - sx
        sy_to_cy = cy - sy
        line_rad = math.atan2(sy_to_cy, sx_to_cx)
        line_dist = math.hypot(sx_to_cx, sy_to_cy)
        new_dist = rdist * line_dist
        new_x = cx + (new_dist * math.cos(rrad + line_rad))
        new_y = cy + (new_dist * math.sin(rrad + line_rad))
        return new_x, new_y

    # ### Derivative features ############################################
    def make_path(self):
        """ Draws the shape as a path """
        self.update_end_points()
        if (self._path is not None) and not self._changed:
            return
        self._changed = False
        sx, sy = self.start_point
        ex, ey = self.end_point
        if sx == ex:
            ex += 0.001  # fix disappearing vertical paths

        en, ec = self.edge_index()
        thick = 1
        if self.in_projections and (self.in_projections[0].strong_lines and not
                                    self.in_projections[0].colorized):
            thick = len(self.in_projections)

        c = dict(start_point=self.start_point, end_point=(ex, ey),
                 curve_adjustment=self.curve_adjustment, thick=thick, edge_n=en,
                 edge_count=ec, start=self.start, end=self.end, inner_only=self._use_simple_path,
                 curve_dir_start=self._curve_dir_start, curve_dir_end=self._curve_dir_end)

        method = SHAPE_PRESETS[self.shape_name].path

        self._path, self._true_path, self.control_points, self.adjusted_control_points = method(**c)
        uses_pen = c.get('thickness', 0)

        if self._use_simple_path:
            self._path = self._true_path

        if self.cached('arrowhead_at_start'):
            self._arrowhead_start_path = self.make_arrowhead_path('start')
            if uses_pen:
                self._path = self.sharpen_arrowhead_at_start(self._path)
        else:
            self._arrowhead_start_path = None

        if self.cached('arrowhead_at_end'):
            self._arrowhead_end_path = self.make_arrowhead_path('end')
            if uses_pen:
                self._path = self.sharpen_arrowhead_at_end(self._path)
        else:
            self._arrowhead_end_path = None
        if self._make_fat_path and not self._use_simple_path:
            # Fat path is the shape of the path with some extra margin to
            # make it easier to click/touch
            self._fat_path = outline_stroker.createStroke(self._path)
        else:
            self._fat_path = self._path
        self._cached_cp_rect = self._path.controlPointRect()
        #
        if self.label_item:
            self.label_item.update_position()
        if ctrl.is_selected(self):
            ctrl.ui.update_position_for(self)
        # overlap detection is costly, so do checks for cases that make it unnecessary
        if self.edge_type == g.FEATURE_EDGE or self.edge_type == g.CHECKING_EDGE:
            self._nodes_overlap = False
        elif not ctrl.settings.get('hide_edges_if_nodes_overlap'):
            self._nodes_overlap = False
        elif self.start and self.end:
            if self.end.locked_to_node:
                self._nodes_overlap = False
            elif self.start.is_visible() and self.end.is_visible():
                self._nodes_overlap = self.start.overlap_rect().intersects(self.end.overlap_rect())
            else:
                self._nodes_overlap = False
        else:
            self._nodes_overlap = False
        self.update_visibility()

    def path_bounding_rect(self) -> QtCore.QRectF:
        if self._path:
            return self._path.boundingRect()
        else:
            return QtCore.QRectF()

    def shape(self) -> QtGui.QPainterPath:
        """ Override of the QGraphicsItem method. Should returns the real
        shape of item to
        allow exact hit detection.
        In our case we should have special '_fat_path' for those shapes that
        are just narrow lines.
        :return: QGraphicsPath
        """
        if not self._fat_path:
            self.make_path()
        return self._fat_path

    def reset_style(self):
        self.shape_name = None
        ctrl.settings.reset_edge_settings(edge=self)
        self.curve_adjustment = [(0, 0)] * len(self.control_points)
        self.update_shape()

    def update_shape(self):
        """ Reload shape and shape settings """
        cpl = len(self.control_points)
        self.make_path()
        # while len(self.curve_adjustment) < len(self.control_points):
        # self.curve_adjustment.append((0, 0, 0))
        if cpl != len(self.control_points):
            ctrl.ui.update_control_points()
        self.update()

    def update_end_points(self):
        """

        :return:
        """
        osx, osy = self._computed_start_point
        oex, oey = self._computed_end_point

        if self.start and self.end:
            sx, sy = self.start.current_scene_position
            ex, ey = self.end.current_scene_position
        elif self.start:
            ex, ey = self.end_point
            ex = int(ex)
            ey = int(ey)
            sx, sy = self.start.current_scene_position
            self._computed_end_point = ex, ey
        elif self.end:
            sx, sy = self.start_point
            sx = int(sx)
            sy = int(sy)
            ex, ey = self.end.current_scene_position
            self._computed_start_point = sx, sy
        else:
            return
        if self.start:
            connection_style = self.cached_for_type('start_connects_to')
            if connection_style == SPECIAL:
                self._computed_start_point, self._curve_dir_start = \
                    self.start.special_connection_point(sx, sy, ex, ey, start=True)
            elif connection_style == CONNECT_TO_CENTER:
                self._computed_start_point = sx, sy
                if abs(sx - ex) < abs(sy - ey):
                    if sy < ey:
                        self._curve_dir_start = BOTTOM_SIDE
                    else:
                        self._curve_dir_start = TOP_SIDE
                else:
                    if sx < ex:
                        self._curve_dir_start = RIGHT_SIDE
                    else:
                        self._curve_dir_start = LEFT_SIDE
            elif connection_style == CONNECT_TO_BOTTOM_CENTER:
                self._computed_start_point = self.start.bottom_center_magnet(scene_pos=(sx, sy))
                self._curve_dir_start = BOTTOM_SIDE
            elif connection_style == CONNECT_TO_MAGNETS:
                e_n, e_count = self.edge_index()
                if not self.start.has_ordered_children():
                    e_n = e_count - e_n - 1
                self._computed_start_point = self.start.bottom_magnet(e_n, e_count, scene_pos=(sx, sy))
                self._curve_dir_start = BOTTOM_SIDE
            elif connection_style == CONNECT_TO_BORDER:
                # Find the point in bounding rect that is on the line from center of start node to
                # center of end node / end_point. It is simple, but the point can be in any of four
                # sides of the rect.
                dx = ex - sx
                dy = ey - sy
                sbr = self.start.boundingRect()
                s_left, s_top, s_right, s_bottom = (int(x * .8) for x in sbr.getCoords())
                # orthogonal cases, handle separately to avoid division by zero
                if dx == 0:
                    if dy > 0:
                        self._computed_start_point = sx, sy + s_bottom
                        self._curve_dir_start = BOTTOM_SIDE
                    else:
                        self._computed_start_point = sx, sy + s_top
                        self._curve_dir_start = TOP_SIDE
                elif dy == 0:
                    if dx > 0:
                        self._computed_start_point = sx + s_right, sy
                        self._curve_dir_start = RIGHT_SIDE
                    else:
                        self._computed_start_point = sx + s_left, sy
                        self._curve_dir_start = LEFT_SIDE
                else:
                    ratio = dy / dx
                    if dx > 0:
                        if dy > 0:
                            if int(s_right * ratio) < s_bottom:
                                self._computed_start_point = sx + s_right, sy + int(s_right * ratio)
                                self._curve_dir_start = RIGHT_SIDE
                            else:
                                self._computed_start_point = sx + int(s_bottom / ratio), \
                                                             sy + s_bottom
                                self._curve_dir_start = BOTTOM_SIDE
                        else:
                            if int(s_right * ratio) > s_top:
                                self._computed_start_point = sx + s_right, sy + int(s_right * ratio)
                                self._curve_dir_start = RIGHT_SIDE
                            else:
                                self._computed_start_point = sx + int(s_top / ratio), sy + s_top
                                self._curve_dir_start = TOP_SIDE
                    else:
                        if dy > 0:
                            if int(s_left * ratio) < s_bottom:
                                self._computed_start_point = sx + s_left, sy + int(s_left * ratio)
                                self._curve_dir_start = LEFT_SIDE
                            else:
                                self._computed_start_point = sx + int(s_bottom / ratio), \
                                                             sy + s_bottom
                                self._curve_dir_start = BOTTOM_SIDE
                        else:
                            if int(s_left * ratio) > s_top:
                                self._computed_start_point = sx + s_left, sy + int(s_left * ratio)
                                self._curve_dir_start = LEFT_SIDE
                            else:
                                self._computed_start_point = sx + int(s_top / ratio), sy + s_top
                                self._curve_dir_start = TOP_SIDE
        if self.end:
            connection_style = self.cached_for_type('end_connects_to')
            if connection_style == SPECIAL:
                self._computed_end_point, self._curve_dir_end = self.end.special_connection_point(
                    sx, sy, ex, ey, start=False)
            elif connection_style == CONNECT_TO_CENTER:
                self._computed_end_point = ex, ey
                if abs(sx - ex) < abs(sy - ey):
                    if sy > ey:
                        self._curve_dir_end = BOTTOM_SIDE
                    else:
                        self._curve_dir_end = TOP_SIDE
                else:
                    if sx > ex:
                        self._curve_dir_end = RIGHT_SIDE
                    else:
                        self._curve_dir_end = LEFT_SIDE
            elif connection_style == CONNECT_TO_BOTTOM_CENTER or connection_style == \
                    CONNECT_TO_MAGNETS:
                self._computed_end_point = self.end.top_center_magnet(scene_pos=(ex, ey))
                self._curve_dir_end = TOP_SIDE

            elif connection_style == CONNECT_TO_BORDER:
                # Find the point in bounding rect that is on the line from center of end node to
                # center of start node / start_point. It is simple, but the point can be in any of
                # four sides of the rect.
                dx = ex - sx
                dy = ey - sy
                ebr = self.end.boundingRect()
                e_left, e_top, e_right, e_bottom = (int(x * .8) for x in ebr.getCoords())
                # orthogonal cases, handle separately to avoid division by zero
                if dx == 0:
                    if dy > 0:
                        self._computed_end_point = ex, ey + e_top
                        self._curve_dir_end = TOP_SIDE
                    else:
                        self._computed_end_point = ex, ey + e_bottom
                        self._curve_dir_end = BOTTOM_SIDE
                elif dy == 0:
                    if dx > 0:
                        self._computed_end_point = ex + e_left, ey
                        self._curve_dir_end = LEFT_SIDE
                    else:
                        self._computed_end_point = ex + e_right, ey
                        self._curve_dir_end = RIGHT_SIDE
                else:
                    ratio = dy / dx
                    if dx > 0:
                        if dy > 0:
                            if int(e_left * ratio) > e_top:
                                self._computed_end_point = ex + e_left, ey + int(e_left * ratio)
                                self._curve_dir_end = LEFT_SIDE
                            else:
                                self._computed_end_point = ex + int(e_top / ratio), ey + e_top
                                self._curve_dir_end = TOP_SIDE
                        else:
                            if int(e_left * ratio) < e_bottom:
                                self._computed_end_point = ex + e_left, ey + int(e_left * ratio)
                                self._curve_dir_end = LEFT_SIDE
                            else:
                                self._computed_end_point = ex + int(e_bottom / ratio), ey + e_bottom
                                self._curve_dir_end = BOTTOM_SIDE
                    else:
                        if dy > 0:
                            if int(e_right * ratio) > e_top:
                                self._computed_end_point = ex + e_right, ey + int(e_right * ratio)
                                self._curve_dir_end = RIGHT_SIDE
                            else:
                                self._computed_end_point = ex + int(e_top / ratio), ey + e_top
                                self._curve_dir_end = TOP_SIDE
                        else:
                            if int(e_right * ratio) < e_bottom:
                                self._computed_end_point = ex + e_right, ey + int(e_right * ratio)
                                self._curve_dir_end = RIGHT_SIDE
                            else:
                                self._computed_end_point = ex + int(e_bottom / ratio), ey + e_bottom
                                self._curve_dir_end = BOTTOM_SIDE
        nsx, nsy = self._computed_start_point
        nex, ney = self._computed_end_point
        if osx != nsx or osy != nsy or oex != nex or oey != ney:
            self._changed = True

    def connect_end_points(self, start, end):
        """

        :param start:
        :param end:
        """
        if start:
            self._computed_start_point = start.current_scene_position
            self.start = start
        else:
            self.start = None
        if end:
            self._computed_end_point = end.current_scene_position
            self.end = end
        else:
            self.end = None
        self.update_status_tip()

    def update_status_tip(self):
        """

        :return:
        """
        if self.edge_type == g.CONSTITUENT_EDGE:
            self.status_tip = 'Constituent relation: %s is part of %s' % (self.end, self.start)

    def description(self):
        """

        :return:
        """
        if self.edge_type == g.ARROW:
            label = 'Arrow'
        else:
            label = 'Edge'
        if self.start:
            s1 = f'"{self.start}"'
        elif self.fixed_start_point:
            s1 = f'({int(self.start_point[0])}, {int(self.start_point[1])})'
        else:
            s1 = 'undefined'
        if self.end:
            s2 = f'"{self.end}"'
        elif self.fixed_end_point:
            s2 = f'({int(self.end_point[0])}, {int(self.end_point[1])})'
        else:
            s2 = 'undefined'
        return f'{label} from {s1} to {s2}'

    def __repr__(self):
        return self.description()

    def delete_on_disconnect(self):
        """ Some edges are not real edges, but can have sensible existence without being
        connected to nodes. Some are better to destroy at that point.
        :return:
        """
        return self.allow_orphan_ends()

    def allow_orphan_ends(self):
        """

        :return:
        """
        return self.edge_type is g.ARROW or self.edge_type is g.DIVIDER

    def update_selection_status(self, selected):
        """ Switch

        :param selected:
        """
        if selected:
            if self.uses_labels():
                if not self.label_item:
                    self.label_item = EdgeLabel('', self, placeholder=True)
                    self.label_item.update_position()
                self.label_item.selected = True
        else:
            if self.label_item:
                if self.label_item.placeholder:
                    scene = self.scene()
                    if scene:
                        scene.removeItem(self.label_item)
                    self.label_item = None
                else:
                    self.label_item.selected = False
        self.update()

    def boundingRect(self):
        """ BoundingRect that includes the control points of the arc

        :return:
        """
        if not self._path:
            self.make_path()
        return self._cached_cp_rect

    # ### Mouse - Qt events ##################################################

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
                self._local_drag_handle_position = None
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
            else:  # This is regular click on 'pressed' object
                self.select(event)
                self.update()
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

    @property
    def hovering(self):
        """


        :return:
        """
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._hovering:
            self._hovering = True
            self.prepareGeometryChange()
            self.update()
            ctrl.set_status(self.status_tip)
        elif (not value) and self._hovering:
            self._hovering = False
            self.prepareGeometryChange()
            self.setZValue(10)
            self.update()
            ctrl.remove_status(self.status_tip)

    def hoverEnterEvent(self, event):
        """
        Overrides (and calls) QtWidgets.QGraphicsItem.hoverEnterEvent
        Toggles hovering state and necessary graphical effects.
        :param event:
        """
        self.hovering = True
        print('hover enter edge')
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        self.hovering = False
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    # ## Scene-managed call

    def select(self, event=None, multi=False):
        """ This is identical with node/movable selection, but edges don't inherit these.
        Actual selection activation stuff is in update_selection_status.
        :param event:
        :param multi: force multiple selection (append, not replace)
        """
        self.hovering = False
        if (event and event.modifiers() == Qt.ShiftModifier) or multi:  # multiple selection
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
            return
        if not ctrl.is_selected(self):
            ctrl.select(self)

    # ## Qt paint method override
    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        t = time.time()
        c = self.contextual_color
        if self._use_simple_path:
            p = QtGui.QPen()
            p.setColor(c)
            painter.setPen(p)
            painter.drawPath(self._true_path)
        else:
            if self.has_outline():
                thickness = self.cached('thickness')
                p = QtGui.QPen()
                p.setColor(c)
                p.setCapStyle(QtCore.Qt.RoundCap)
                if self.in_projections and self.in_projections[0].colorized:
                    p.setWidthF(thickness)
                    left = self.start_point[0] > self.end_point[0]
                    for i, proj in enumerate(self.in_projections):
                        cp = QtGui.QPen(p)
                        cp.setColor(ctrl.cm.get(proj.color_id))
                        painter.setPen(cp)
                        if left:
                            cpath = self._path.translated(i, i)
                        else:
                            cpath = self._path.translated(-i, i)
                        painter.drawPath(cpath)

                elif self.in_projections and self.in_projections[0].strong_lines:
                    p.setWidthF(thickness * len(self.in_projections))
                    painter.setPen(p)
                    painter.drawPath(self._path)
                else:
                    p.setWidthF(thickness)
                    painter.setPen(p)
                    painter.drawPath(self._path)

            if self.is_filled():
                if self.in_projections and self.in_projections[0].colorized:
                    left = self.start_point[0] > self.end_point[0]
                    for i, proj in enumerate(self.in_projections):
                        cp = ctrl.cm.get(proj.color_id)
                        if left:
                            cpath = self._path.translated(i, i)
                        else:
                            cpath = self._path.translated(-i, i)
                        painter.fillPath(cpath, cp)
                else:
                    painter.fillPath(self._path, c)
            if self.cached('arrowhead_at_start') and self._arrowhead_start_path:
                painter.fillPath(self._arrowhead_start_path, c)
            if self.cached('arrowhead_at_end') and self._arrowhead_end_path:
                painter.fillPath(self._arrowhead_end_path, c)

        if ctrl.is_selected(self):
            p = QtGui.QPen(ctrl.cm.ui_tr())
            painter.setPen(p)
            painter.drawPath(self._true_path)
            if self.control_points:
                if self.curve_adjustment:
                    ca = len(self.curve_adjustment)
                else:
                    ca = 0

                p.setWidthF(0.5)
                painter.setPen(p)
                if len(self.control_points) > 1:
                    painter.drawLine(self.end_point[0], self.end_point[1],
                                     self.control_points[1][0], self.control_points[1][1])
                    if ca > 1 and self.curve_adjustment[1][0]:
                        p.setStyle(QtCore.Qt.DashLine)
                        painter.drawLine(self.control_points[1][0], self.control_points[1][1],
                                         self.adjusted_control_points[1][0],
                                         self.adjusted_control_points[1][1])
                        p.setStyle(QtCore.Qt.SolidLine)
                painter.drawLine(self.start_point[0], self.start_point[1],
                                 self.control_points[0][0], self.control_points[0][1])
                if ca > 0 and self.curve_adjustment[0][0]:
                    p.setStyle(QtCore.Qt.DashLine)
                    painter.drawLine(self.control_points[0][0], self.control_points[0][1],
                                     self.adjusted_control_points[0][0],
                                     self.adjusted_control_points[0][1])
        if self.crossed_out_flag:
            cx, cy = to_tuple(self._true_path.pointAtPercent(0.5))
            p = QtGui.QPen(ctrl.cm.ui())
            p.setWidthF(1.0)
            painter.setPen(p)
            painter.drawLine(cx - 20, cy - 10, cx + 20, cy + 10)
            painter.drawLine(cx - 20, cy + 10, cx + 20, cy - 10)



    def get_point_at(self, d: float) -> Pf:
        """ Get coordinates at the percentage of the length of the path.
        :param d: float
        :return: QPoint
        """
        if not self._true_path:
            self.make_path()
        return self._true_path.pointAtPercent(d)

    def get_angle_at(self, d: float) -> float:
        """ Get angle at the percentage of the length of the path.
        :param d: int
        :return: float
        """
        if not self._true_path:
            self.make_path()
        return self._true_path.angleAtPercent(d)

    def get_closest_path_point(self, pos):
        """ When dragging object along path, gives the coordinates to closest
        point in path corresponding to
        given position. There is no exact way of doing this, what we do is to
        take 100 points along the line and
        find the closest point from there.
        :param pos: position looking for closest path position
        :return: (float:pointAtPercent, QPos:path position)
        """
        if not self._true_path:
            self.make_path()
        min_d = 1000
        min_i = -1
        min_pos = None
        for i in range(0, 100, 2):
            p2 = self._true_path.pointAtPercent(i / 100.0)
            d = (pos - p2).manhattanLength()
            if d < min_d:
                min_d = d
                min_i = i
                min_pos = p2
        return min_i / 100.0, min_pos

    def make_arrowhead_path(self, pos='end'):
        """ Assumes that the path exists already, creates arrowhead path to
        either at the end or at start,
        but doesn't yet combine these paths.
        :param pos: 'end' or 'start'
        :return: QPainterPath for arrowhead
        """
        ad = 0.5
        x = y = size = a = 0
        t = self.cached('thickness')
        if pos == 'start':
            size = self.arrowhead_size_at_start
            if t:
                size *= t
            x, y = self.start_point
            # average between last control point and general direction seems to be ok.
            if self.control_points:
                p0 = self.adjusted_control_points[0]
            else:
                p0 = self.end_point
            dx, dy = sub_xy(self.start_point, p0)
            a = math.atan2(dy, dx)
        elif pos == 'end':
            size = self.arrowhead_size_at_end
            if t:
                size *= t
            x, y = self.end_point
            # average between last control point and general direction seems to be ok.
            if self.control_points:
                plast = self.adjusted_control_points[-1]
            else:
                plast = self.start_point

            dx, dy = sub_xy(self.end_point, plast)
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
        if pos == 'start':
            self._arrow_cut_point_start = xm, ym
        elif pos == 'end':
            self._arrow_cut_point_end = xm, ym
        return p

    def sharpen_arrowhead_at_start(self, path):
        """ Move the start point of given path few pixels inwards, so when
        path is drawn with solid line it won't end with blunt end of a line
        but with the sharp end of the arrowhead shape.
        :param path: the path where sharpening occurs
        :return:
        """
        i = 0
        if self._arrow_cut_point_start:
            x, y = self._arrow_cut_point_start
        else:
            return path
        path.setElementPositionAt(i, x, y)
        return path

    def sharpen_arrowhead_at_end(self, path):
        """ Move the end point of given path few pixels inwards, so when
        path is drawn with solid line it won't end with blunt end of a line
        but with the sharp end of the arrowhead shape.
        :param path: the path where sharpening occurs
        :return:
        """
        i = path.elementCount() - 1
        if self._arrow_cut_point_end:
            x, y = self._arrow_cut_point_end
        else:
            return path
        path.setElementPositionAt(i, x, y)
        return path

    def end_node_started_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._end_node_moving = True
        self._make_fat_path = False
        if not self._start_node_moving:
            self._start_moving()

    def start_node_started_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._start_node_moving = True
        self._make_fat_path = False
        if not self._end_node_moving:
            self._start_moving()

    def _start_moving(self):
        """ Low level toggle off things that slow drawing
        :return: None
        """
        pass
        #if prefs.move_effect:
        #    self._use_simple_path = True

    def start_node_stopped_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._start_node_moving = False
        if not self._end_node_moving:
            self._stop_moving()

    def end_node_stopped_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._end_node_moving = False
        if not self._start_node_moving:
            self._stop_moving()

    def _stop_moving(self):
        """ Low level toggle back complex drawing
        :return: None
        """
        self._make_fat_path = True
        #if prefs.move_effect:
        #    self._use_simple_path = False

    def fade_in(self, s=150):
        """ Simple fade effect. The object exists already when fade starts.
        :return: None
        :param s: speed in ms
        """
        if self.is_fading_in:
            return
        self.is_fading_in = True
        self.show()
        if self.is_fading_out:
            self.is_fading_out = False
            self._fade_out_anim.stop()
        self._fade_in_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_in_anim.setDuration(s)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QtCore.QEasingCurve.InQuad)
        self._fade_in_anim.finished.connect(self.fade_in_finished)
        self._fade_in_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def fade_in_finished(self):
        self.is_fading_in = False

    def fade_out(self, s=150):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if not self.isVisible():
            return
        if self.is_fading_out:
            return
        self.is_fading_out = True
        if self.is_fading_in:
            self.is_fading_in = False
            self._fade_in_anim.stop()
        self._fade_out_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_out_anim.setDuration(s)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0)
        self._fade_out_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_out_anim.finished.connect(self.fade_out_finished)
        self._fade_out_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def fade_out_and_delete(self, s=150):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if self.is_fading_out:
            self._fade_out_anim.finished.disconnect()
            self._fade_out_anim.finished.connect(self.fade_out_finished_delete)
            if self.is_fading_in:
                self.is_fading_in = False
                self._fade_in_anim.stop()
            return
        if not self.isVisible():
            self.fade_out_finished_delete()
            return
        self.is_fading_out = True
        if self.is_fading_in:
            self.is_fading_in = False
            self._fade_in_anim.stop()
        self._fade_out_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_out_anim.setDuration(s)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0)
        self._fade_out_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_out_anim.finished.connect(self.fade_out_finished_delete)
        self._fade_out_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def fade_out_finished_delete(self):
        self.is_fading_out = False
        self.hide()
        ctrl.forest.remove_from_scene(self, fade_out=False)

    def fade_out_finished(self):
        self.is_fading_out = False
        self.hide()

    def free_drawing_mode(self, *args, **kwargs):
        """ Utility method for checking conditions for editing operations
        :param args: ignored
        :param kwargs: ignored
        :return:
        """
        return ctrl.free_drawing_mode

    # Shape helpers #############################

    def cached(self, key, missing=None):
        return ctrl.settings.cached_edge(key, self, missing)

    def cached_for_type(self, key):
        return ctrl.settings.cached_edge_type(key, self.edge_type)

    def set_arrowhead_at_start(self, value):
        ctrl.settings.set_edge_setting('arrowhead_at_start', value, edge=self)

    def set_arrowhead_at_end(self, value):
        ctrl.settings.set_edge_setting('arrowhead_at_end', value, edge=self)

    def set_leaf_width(self, value):
        ctrl.settings.set_edge_setting('leaf_x', value, edge=self)
        self.update_shape()

    def set_leaf_height(self, value):
        ctrl.settings.set_edge_setting('leaf_y', value, edge=self)
        self.update_shape()

    def reset_leaf_shape(self):
        ctrl.settings.del_shape_setting('leaf_x', edge=self)
        ctrl.settings.del_shape_setting('leaf_y', edge=self)
        self.update_shape()

    def change_edge_relative_curvature_x(self, value):
        ctrl.settings.set_edge_setting('rel_dx', value * .01, edge=self)
        self.update_shape()

    def change_edge_relative_curvature_y(self, value):
        ctrl.settings.set_edge_setting('rel_dy', value * .01, edge=self)
        self.update_shape()

    def change_edge_fixed_curvature_x(self, value):
        ctrl.settings.set_edge_setting('fixed_dx', value, edge=self)
        self.update_shape()

    def change_edge_fixed_curvature_y(self, value):
        ctrl.settings.set_edge_setting('fixed_dy', value, edge=self)
        self.update_shape()

    def set_edge_curvature_relative(self, value):
        ctrl.settings.set_edge_setting('relative', value, edge=self)
        self.update_shape()

    def reset_edge_curvature(self):
        ctrl.settings.del_shape_setting('rel_dx', edge=self)
        ctrl.settings.del_shape_setting('rel_dy', edge=self)
        ctrl.settings.del_shape_setting('fixed_dx', edge=self)
        ctrl.settings.del_shape_setting('fixed_dy', edge=self)
        ctrl.settings.del_shape_setting('relative', edge=self)
        self.update_shape()

    def reset_thickness(self):
        ctrl.settings.del_shape_setting('thickness', edge=self)
        self.update_shape()

    def set_thickness(self, value):
        ctrl.settings.set_edge_setting('thickness', value, edge=self)
        self.update_shape()

    def set_fill(self, value):
        ctrl.settings.set_edge_setting('fill', value, edge=self)
        self.update_shape()

    def set_outline(self, value):
        ctrl.settings.set_edge_setting('outline', value, edge=self)
        self.update_shape()

    def prepare_adjust_array(self, index):
        """

        :param index:
        """
        if self.curve_adjustment is None:
            self.curve_adjustment = [(0, 0)]
        while index >= len(self.curve_adjustment):
            self.curve_adjustment.append((0, 0))

    def adjust_control_point(self, index, dist=None, rad=None):
        """ Called from UI, when dragging
        :param index:
        :param dist:
        :param rad:
        """
        self.poke('curve_adjustment')
        self.prepare_adjust_array(index)
        odist, orad = self.curve_adjustment[index]
        if dist is None:
            dist = odist
        if rad is None:
            rad = orad
        self.curve_adjustment[index] = dist, rad
        self.call_watchers('edge_adjustment', 'curve_adjustment', self.curve_adjustment)
        self._changed = True
        self.make_path()
        self.update()

    def reset_control_points(self):
        """
        Set adjustments back to zero
        :return:
        """

        n = self.cached('control_points')
        self.poke('curve_adjustment')
        self.curve_adjustment = [(0, 0)] * n
        self.make_path()
        self.update()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Saved properties
    fixed_start_point = SavedField("fixed_start_point")
    fixed_end_point = SavedField("fixed_end_point")
    edge_type = SavedField("edge_type")
    curve_adjustment = SavedField("curve_adjustment", watcher="edge_adjustment")
    start = SavedField("start")
    end = SavedField("end")
    forest = SavedField("forest")
    label_data = SavedField("label_data")
