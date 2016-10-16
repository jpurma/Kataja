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
from PyQt5.QtCore import QPointF as Pf, Qt

from kataja.EdgeShape import EdgeShape
from kataja.singletons import ctrl, qt_prefs, prefs
import kataja.globals as g
from kataja.globals import LEFT, RIGHT
from kataja.shapes import SHAPE_PRESETS, outline_stroker
from kataja.EdgeLabel import EdgeLabel
import kataja.utils as utils
from kataja.utils import to_tuple, add_xy, sub_xy
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.uniqueness_generator import next_available_type_id


CONNECT_TO_CENTER = 0
CONNECT_TO_BOTTOM_CENTER = 1
CONNECT_TO_MAGNETS = 2
CONNECT_TO_BORDER = 3

TOP_LEFT_CORNER = 0
TOP_SIDE = 1
TOP_RIGHT_CORNER = 2
LEFT_SIDE = 3
RIGHT_SIDE = 4
BOTTOM_LEFT_CORNER = 5
BOTTOM_SIDE = 6
BOTTOM_RIGHT_CORNER = 7

angle_magnet_map = {0: 6, 1: 6, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0, 7: 5, 8: 5, 9: 5, 10: 7, 11: 8, 12: 9,
                    13: 10, 14: 11, 15: 6, 16: 6}

atan_magnet_map = {-8: 5, -7: 5, -6: 0, -5: 1, -4: 2, -3: 3, -2: 4, -1: 6, 0: 6, 1: 6, 2: 11, 3: 10,
                   4: 9, 5: 8, 6: 7, 7: 5, 8: 5}

qbytes_opacity = QtCore.QByteArray()
qbytes_opacity.append("opacity")


class SavedEdgeSetting(SavedField):
    """ Saved, but getter runs the provided after_get -method for the returned
    value. Probably bit slower than regular Saved
    """

    def __init__(self, name, before_set=None, if_changed=None):
        super().__init__(name, before_set=before_set, if_changed=if_changed)

    def __get__(self, obj, objtype=None):
        value = obj._saved[self.name]
        if value is None:
            return ctrl.fs.edge_info(obj.edge_type, self.name)
        else:
            return value


class Edge(QtWidgets.QGraphicsObject, SavedObject):
    """ Any connection between nodes: can be represented as curves, branches
    or arrows """

    __qt_type_id__ = next_available_type_id()

    def __init__(self, forest=None, start=None, end=None, edge_type='', appear=True):
        """
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param string order:
        """
        SavedObject.__init__(self)
        QtWidgets.QGraphicsItem.__init__(self)
        self.forest = forest
        self.label_item = None
        self.shape_info = EdgeShape(self)
        self._shape_method = None
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
        self.local_shape_info = {}
        self.color_id = None
        self.shape_name = None
        self.pull = None
        self._nodes_overlap = False
        self.visible_by_rule = True
        self.appearing = appear

        self._projection_thick = False
        self._projection_color = None

        self._computed_start_point = None
        self._computed_end_point = None

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
        self.setZValue(10)
        self.status_tip = ""
        self._cached_shape_info = {}
        #self.connect_end_points(start, end)
        self.arrowhead_size_at_start = 6
        self.arrowhead_size_at_end = 6
        self._arrow_cut_point_start = None
        self._arrow_cut_point_end = None
        self._arrowhead_start_path = None
        self._arrowhead_end_path = None
        self._cached_cp_rect = None
        self._use_labels = None
        self._relative_vector = None
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._fade_anim = None
        self.is_fading_in = False
        self.is_fading_out = False
        if appear:
            self.fade_in()

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
        self.update_end_points()
        self.update_visibility()
        self.announce_creation()

    def after_model_update(self, updated_fields, update_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param update_type: 0:edit, 1:CREATED, 2:DELETED
        :return: None
        """
        if update_type == 1:
            self.forest.store(self)
            self.forest.add_to_scene(self)
        self.update_visibility()
        self.connect_end_points(self.start, self.end)
        self.update_end_points()

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

    def copy(self, others=None):
        super().copy(others)

    @property
    def start_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of
        starting point of the edge
        :return: tuple (x, y, z)
        """
        if self.start:
            return self._computed_start_point or self.fixed_start_point
        else:
            return self.fixed_start_point

    @property
    def end_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of ending
        point of the edge
        :return: tuple (x, y, z)
        """
        if self.end:
            return self._computed_end_point or self.fixed_end_point
        else:
            return self.fixed_end_point

    def if_changed_visible(self, value):
        """ Edges may be filtered out of view without destroying them,
        e.g. comment edges and arrows.
        Setting edge hidden makes it invisible for many ways of manipulating
        and updating edges, so care must
         be taken.  Note that the edge can be invisible because it has shape
         'not drawn', but such edge is still visible_by_rule
         for these purposes: it will have its UI buttons, it is selectable etc.
        :param value: bool
        """
        if self.forest:
            self.update_visibility()

    def update_visibility(self):
        """ Hide or show according to model.visible_by_rule flag, which allows edge
        to exist but not be drawn.
        :return:
        """
        v = self.isVisible()
        if v and self._nodes_overlap or not self.visible_by_rule:
            self.hide()
            ctrl.ui.remove_ui_for(self)

        elif self.visible_by_rule and not (v or self._nodes_overlap):
            self.show()
            if ctrl.is_selected(self):
                ctrl.ui.add_control_points(self)

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

    def if_changed_shape_name(self, value):
        """ Set the shape name key for this edge. These keys are used to get
        the shape drawing settings, amount of
        control points, whether the shape is filled etc. Also updates the
        _shape_method according to new shape_name.
        :param value: str
        """
        if value:
            self._shape_method = SHAPE_PRESETS[value]['method']

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
        return self._cached_shape_info['fill']

    def has_outline(self) -> int:
        return self._cached_shape_info.get('thickness', 0)

    def is_visible(self) -> bool:
        return self.visible_by_rule and not self._nodes_overlap

    def set_projection_display(self, thick, color):
        """ Set both options related to displaying projections with edges.
        :param thick: bool, should the projections be drawn with thicker lines
        :param color: edge will be painted with given marker color (assumes
        that the color is transparent and will be painted on top of existing
        path)
        :return:
        """

        if thick == self._projection_thick and color == self._projection_color:
            return
        self._projection_thick = thick
        self._projection_color = color

    def make_relative_vector(self):
        """ Relative vector helps to keep the shape of a line when another,
        attached end moves.
         It applies only to lines where the other end is attached to node.
        :return:
        """
        if self.start and not self.end:
            self._relative_vector = sub_xy(self.end_point, self.start.current_scene_position)
        elif self.end and not self.start:
            self._relative_vector = sub_xy(self.end.current_scene_position, self.start_point)

    def connect_start_to(self, node):
        """

        :param node:
        """
        self.forest.set_edge_start(self, node)
        self.make_relative_vector()
        self.update_shape()

    def connect_end_to(self, node):
        """

        :param node:
        """
        self.forest.set_edge_end(self, node)
        self.make_relative_vector()
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
        self.make_relative_vector()

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
        self.make_relative_vector()

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
        elif self._projection_color:
            return ctrl.cm.get(self._projection_color)
        else:
            return self.color

    @property
    def uses_labels(self) -> bool:
        """ Some edge types, e.g. arrows inherently suggest adding labels to
        them. For others, having ui_support
         textbox for adding label would be unwanted noise.
        :return: bool
        """
        if self._use_labels is None:
            return ctrl.fs.edge_info(self.edge_type, 'labeled')
        else:
            return self._use_labels

    # ### Shape / pull / visibility
    # ###############################################################

    def drag(self, event):
        """ This is for dragging the whole edge in cases when edge is not
        connected to nodes at any point
        e.g. it is freely floating arrow or divider
        :param event: Drag event?
        """
        #self.draggable = not (self.start or self.end)

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
        if index == 0:
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
    # @utils.time_me
    def make_path(self):
        """ Draws the shape as a path """
        self.update_end_points()
        if not self._shape_method:
            self.update_shape()
        c = self._cached_shape_info
        sx, sy = self.start_point
        ex, ey = self.end_point
        if sx == ex:
            ex += 0.001 # fix disappearing vertical paths

        c['start_point'] = sx, sy
        c['end_point'] = ex, ey
        c['curve_adjustment'] = self.curve_adjustment
        c['thick'] = self._projection_thick
        c['order'], c['sister_edges_n'] = self.edge_index()
        c['start'] = self.start
        c['end'] = self.end
        c['inner_only'] = self._use_simple_path
        self._path, self._true_path, self.control_points, self.adjusted_control_points = \
            self._shape_method(**c)
        uses_pen = c.get('thickness', 0)

        if self._use_simple_path:
            self._path = self._true_path

        if self.shape_info.has_arrowhead_at_start():
            self._arrowhead_start_path = self.make_arrowhead_path('start')
            if uses_pen:
                self._path = self.sharpen_arrowhead_at_start(self._path)
        else:
            self._arrowhead_start_path = None

        if self.shape_info.has_arrowhead_at_end():
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
        if self.start and self.end:
            old = self._nodes_overlap
            self._nodes_overlap = self.start.overlap_rect().intersects(self.end.overlap_rect())
            if self._nodes_overlap != old:
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
        self.shape_info.reset_shape_info(*self.local_shape_info.keys())
        self.curve_adjustment = [(0, 0)] * len(self.control_points)
        self.update_shape()

    def has_local_style_settings(self):
        if self.local_shape_info:
            return True
        if self.curve_adjustment:
            for x, y in self.curve_adjustment:
                if x or y:
                    return True
        return False

    def get_cached_shape_info(self):
        return self._cached_shape_info


    def update_shape(self):
        """ Reload shape and shape settings """
        self._shape_method = SHAPE_PRESETS[self.shape_name]['method']
        self._cached_shape_info = self.shape_info.copy()
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
        if not self._relative_vector:
            self.make_relative_vector()
            self.update_status_tip()

        if self.start and self.end:
            sx, sy = self.start.current_scene_position
            ex, ey = self.end.current_scene_position
        elif self.start:
            sx, sy = self.start.current_scene_position
            ex = sx + self._relative_vector[0]
            ey = sy + self._relative_vector[1]
            self._computed_end_point = ex, ey
        elif self.end:
            ex, ey = self.end.current_scene_position
            sx = ex - self._relative_vector[0]
            sy = ey - self._relative_vector[1]
            self._computed_start_point = sx, sy
        else:
            return
        if self.start:
            connection_style = self.shape_info.connection_style_at_start()
            if connection_style == CONNECT_TO_CENTER:
                self._computed_start_point = self.start.current_scene_position
            elif connection_style == CONNECT_TO_BOTTOM_CENTER:
                self._computed_start_point = self.start.bottom_center_magnet()
            elif connection_style == CONNECT_TO_MAGNETS:
                e_n, e_count = self.edge_index()
                self._computed_start_point = self.start.bottom_magnet(e_n, e_count)
            elif connection_style == CONNECT_TO_BORDER:
                # Find the point in bounding rect that is on the line from center of start node to
                # center of end node / end_point. It is simple, but the point can be in any of four
                # sides of the rect.
                dx = ex - sx
                dy = ey - sy
                sbr = self.start.boundingRect()
                s_left, s_top, s_right, s_bottom = (x * .8 for x in sbr.getCoords())
                # orthogonal cases, handle separately to avoid division by zero
                if dx == 0:
                    if dy > 0:
                        self._computed_start_point = sx, sy + s_bottom
                    else:
                        self._computed_start_point = sx, sy + s_top
                elif dy == 0:
                    if dx > 0:
                        self._computed_start_point = sx + s_right, sy
                    else:
                        self._computed_start_point = sx + s_left, sy
                else:
                    ratio = dy / dx
                    if dx > 0:
                        if dy > 0:
                            if s_right * ratio < s_bottom:
                                self._computed_start_point = sx + s_right, \
                                                             sy + (s_right * ratio)
                            else:
                                self._computed_start_point = sx + (s_bottom / ratio), \
                                                             sy + s_bottom
                        else:
                            if s_right * ratio > s_top:
                                self._computed_start_point = sx + s_right, \
                                                             sy + (s_right * ratio)
                            else:
                                self._computed_start_point = sx + (s_top / ratio), \
                                                             sy + s_top
                    else:
                        if dy > 0:
                            if s_left * ratio < s_bottom:
                                self._computed_start_point = sx + s_left, \
                                                             sy + (s_left * ratio)
                            else:
                                self._computed_start_point = sx + (s_bottom / ratio), \
                                                             sy + s_bottom
                        else:
                            if s_left * ratio > s_top:
                                self._computed_start_point = sx + s_left, \
                                                             sy + (s_left * ratio)
                            else:
                                self._computed_start_point = sx + (s_top / ratio), sy + s_top

        if self.end:
            connection_style = self.shape_info.connection_style_at_end()
            if connection_style == CONNECT_TO_CENTER:
                self._computed_end_point = self.end.current_scene_position
            elif connection_style == CONNECT_TO_BOTTOM_CENTER or connection_style == CONNECT_TO_MAGNETS:
                self._computed_end_point = self.end.top_center_magnet()
            elif connection_style == CONNECT_TO_BORDER:
                # Find the point in bounding rect that is on the line from center of end node to
                # center of start node / start_point. It is simple, but the point can be in any of
                # four sides of the rect.
                dx = ex - sx
                dy = ey - sy
                ebr = self.end.boundingRect()
                e_left, e_top, e_right, e_bottom = (x * .8 for x in ebr.getCoords())
                # orthogonal cases, handle separately to avoid division by zero
                if dx == 0:
                    if dy > 0:
                        self._computed_end_point = ex, ey + e_top
                    else:
                        self._computed_end_point = ex, ey + e_bottom
                elif dy == 0:
                    if dx > 0:
                        self._computed_end_point = ex + e_left, ey
                    else:
                        self._computed_end_point = ex + e_right, ey
                else:
                    ratio = dy / dx
                    if dx > 0:
                        if dy > 0:
                            if e_left * ratio > e_top:
                                self._computed_end_point = ex + e_left, ey + (e_left * ratio)
                            else:
                                self._computed_end_point = ex + (e_top / ratio), ey + e_top

                        else:
                            if e_left * ratio < e_bottom:
                                self._computed_end_point = ex + e_left, ey + (e_left * ratio)
                            else:
                                self._computed_end_point = ex + (e_bottom / ratio), ey + e_bottom
                    else:
                        if dy > 0:
                            if e_right * ratio > e_top:
                                self._computed_end_point = ex + e_right, ey + (e_right * ratio)
                            else:
                                self._computed_end_point = ex + (e_top / ratio), ey + e_top

                        else:
                            if e_right * ratio < e_bottom:
                                self._computed_end_point = ex + e_right, ey + (e_right * ratio)
                            else:
                                self._computed_end_point = ex + (e_bottom / ratio), ey + e_bottom

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
        self.make_relative_vector()
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
            s1 = self.start
        elif self.fixed_start_point:
            s1 = '(%s, %s)' % (int(self.start_point[0]), int(self.start_point[1]))
        else:
            s1 = 'undefined'
        if self.end:
            s2 = self.end
        elif self.fixed_end_point:
            s2 = '(%s, %s)' % (int(self.end_point[0]), int(self.end_point[1]))
        else:
            s2 = 'undefined'
        return '%s from %s to %s' % (label, s1, s2)

    def __repr__(self):
        return self.description()

    def delete_on_disconnect(self):
        """ Some edges are not real edges, but can have sensible existence without being
        connected to nodes. Some are better to destroy at that point.
        :return:
        """
        if self.edge_type is g.ARROW or self.edge_type is g.DIVIDER:
            return False
        else:
            return True

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
            if self.uses_labels:
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
        return self._cached_cp_rect or QtCore.QRectF()

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
            else: # This is regular click on 'pressed' object
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
            self.update_status_tip()
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
        c = self.contextual_color
        if self._use_simple_path:
            p = QtGui.QPen()
            p.setColor(c)
            painter.setPen(p)
            painter.drawPath(self._true_path)
        else:
            width = self.has_outline()
            if width:
                p = QtGui.QPen()
                p.setColor(c)
                p.setCapStyle(QtCore.Qt.RoundCap)
                if self._projection_thick:
                    width *= 2
                p.setWidthF(width)
                painter.setPen(p)
                if self._path.length() == 0 or self._path.isEmpty():
                    print(self, self._path.length(), self._path.isEmpty())
                painter.drawPath(self._path)

            if self.is_filled():
                painter.fillPath(self._path, c)
            if self.shape_info.has_arrowhead_at_start() and self._arrowhead_start_path:
                painter.fillPath(self._arrowhead_start_path, c)
            if self.shape_info.has_arrowhead_at_end() and self._arrowhead_end_path:
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
                    painter.drawLine(self.end_point[0], self.end_point[1], self.control_points[
                        1][0], self.control_points[1][1])
                    if ca > 1 and self.curve_adjustment[1][0]:
                        p.setStyle(QtCore.Qt.DashLine)
                        painter.drawLine(self.control_points[1][0], self.control_points[1][1],
                                         self.adjusted_control_points[1][0],
                                         self.adjusted_control_points[1][1])
                        p.setStyle(QtCore.Qt.SolidLine)
                painter.drawLine(self.start_point[0], self.start_point[1],
                                 self.control_points[0][0],
                                 self.control_points[0][1])
                if ca > 0 and self.curve_adjustment[0][0]:
                    p.setStyle(QtCore.Qt.DashLine)
                    painter.drawLine(self.control_points[0][0], self.control_points[0][1],
                                     self.adjusted_control_points[0][0],
                                     self.adjusted_control_points[0][1])

    def get_point_at(self, d: float) -> Pf:
        """ Get coordinates at the percentage of the length of the path.
        :param d: int
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
        t = self._cached_shape_info.get('thickness', 0)
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
        if prefs.move_effect:
            self._use_simple_path = True

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
        if prefs.move_effect:
            self._use_simple_path = False

    def fade_in(self, s=300):
        """ Simple fade effect. The object exists already when fade starts.
        :return: None
        :param s: speed in ms
        """
        if self.is_fading_in:
            return
        self.is_fading_in = True
        self.show()
        if self.is_fading_out:
            self._fade_anim.stop()
        self._fade_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_anim.setDuration(s)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.InQuad)
        self._fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._fade_anim.finished.connect(self.fade_in_finished)

    def fade_in_finished(self):
        self.is_fading_in = False

    def fade_out(self, s=300):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if not self.is_visible():
            return
        if self.is_fading_out:
            return
        self.is_fading_out = True
        if self.is_fading_in:
            self._fade_anim.stop()
        self._fade_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_anim.setDuration(s)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._fade_anim.finished.connect(self.fade_out_finished)

    def fade_out_and_delete(self, s=300):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if self.is_fading_out:
            self._fade_anim.finished.disconnect()
            self._fade_anim.finished.connect(self.fade_out_finished_delete)
            return
        if not self.is_visible():
            self.fade_out_finished_delete()
            return
        self.is_fading_out = True
        if self.is_fading_in:
            self._fade_anim.stop()
        self._fade_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_anim.setDuration(s)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._fade_anim.finished.connect(self.fade_out_finished_delete)

    def fade_out_finished_delete(self):
        self.is_fading_out = False
        ctrl.forest.remove_from_scene(self, fade_out=False)

    def fade_out_finished(self):
        self.visible_by_rule = False
        self.is_fading_out = False
        self.update_visibility()

    def free_drawing_mode(self, *args, **kwargs):
        """ Utility method for checking conditions for editing operations
        :param args: ignored
        :param kwargs: ignored
        :return:
        """
        return ctrl.free_drawing_mode


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
    label_data = SavedField("label_data", watcher="edge_label")
    local_shape_info = SavedField("local_shape_info", watcher="edge_shape")
    visible_by_rule = SavedField("visible_by_rule", if_changed=if_changed_visible)
    forest = SavedField("forest")

    color_id = SavedEdgeSetting("color_id", if_changed=if_changed_color_id)
    shape_name = SavedEdgeSetting("shape_name", if_changed=if_changed_shape_name)
    pull = SavedEdgeSetting("pull")
